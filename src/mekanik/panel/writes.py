# SPDX-License-Identifier: AGPL-3.0-or-later
"""The panel's writes: the chief's channel (old uygulama yazma uçları). Approvals, rejections, undo, values, model
notes, objections and gate returns go through the process module (signed commit, Ö-07 readiness, APPROVAL-02) with
`channel: panel_confirmed`; a hold, decision, gate or release card and every undo need the confirmation dialog's
`confirmed: true` (Ö-14) — the server refuses them without it. One write per work at a time."""

from __future__ import annotations

import base64
import hashlib
import re
import shlex
import threading
from pathlib import Path
from urllib.parse import quote

from mekanik.agent import hook, inbox
from mekanik.config import load_config
from mekanik.core import clock, yamlio
from mekanik.core.i18n import t
from mekanik.core.process import Refused, chief, gates, refuse
from mekanik.core.process.step import commit_logged
from mekanik.core.store import git, works

from . import events, reads

CHANNEL = "panel_confirmed"
CONFIRM_TYPES = ("gate", "release", "decision", "provisional_decision")
UPLOAD_LIMIT = 512 * 2**20   # source: assumption — default when the config gives no panel.upload_limit (a large STEP)
NAME = re.compile(r"^[\w.() -]{1,120}$")
_locks: dict[str, threading.Lock] = {}


def _one(code: str) -> threading.Lock:
    return _locks.setdefault(code, threading.Lock())


def needs_confirm(card: dict) -> bool:
    """Ö-14: no one-click approval of a hold (DUR), decision, gate or release card (old _teyit_gerekir)."""
    return card.get("level") == "hold" or card.get("type") in CONFIRM_TYPES


def _card(root: Path, card_id: str) -> dict:
    if (card := next((c for c in reads.state(root)["cards"] if c["id"] == card_id), None)) is None:
        raise Refused("process.approve.no_card", id=card_id)
    return card


def _signing(code: str, card: str, fn, *a, **kw):
    """The chief's signed commit: the page is told first (the signing key's per-use dialog may pop up, §4.6 m.5)."""
    events.publish({"type": "signing", "work": code, "card": card})
    try:
        with _one(code):
            return fn(*a, channel=CHANNEL, **kw)
    finally:
        events.publish({"type": "signed", "work": code, "card": card})


def decide(code: str, card_id: str, action: str, reason: str = "", option: str | None = None,
           rows: list[str] | None = None, viewed: str | None = None, branch: str | None = None,
           confirmed: bool = False) -> dict:
    root = reads.root_of(code, branch)
    refuse(action == "comment" and not reason.strip(), "panel.confirm.comment_empty")
    if action != "comment" and needs_confirm(_card(root, card_id)) and not confirmed:
        raise Refused("panel.confirm.required", id=card_id)
    return _signing(code, card_id, chief.approve, root, card_id, action, reason, option=option, rows=rows,
                    viewed=viewed)


def undo(code: str, card_id: str, reason: str, row: str | None = None, viewed: str | None = None,
         branch: str | None = None, confirmed: bool = False) -> dict:
    """Ö-15: the chief takes back his own last approval or rejection; nothing is deleted."""
    refuse(not reason.strip(), "panel.confirm.undo_reason")
    refuse(not confirmed, "panel.confirm.required", id=card_id)
    return _signing(code, card_id, chief.undo, reads.root_of(code, branch), card_id, reason, row=row, viewed=viewed)


def value(code: str, name: str, new: float, reason: str = "", card: str | None = None, viewed: str | None = None,
          branch: str | None = None) -> dict:
    return _signing(code, card or name, chief.value, reads.root_of(code, branch), name, new, reason, card_id=card,
                    viewed=viewed)


def model_note(code: str, text: str, png: str, subject: dict) -> dict:
    """The chief marks a place on the model and writes a note: card N-nn, the team replies and applies it."""
    try:
        raw = base64.b64decode(png.split(",", 1)[-1], validate=True)
    except ValueError as e:
        raise Refused("process.note.bad_image", mb=chief.NOTE_MAX // 2**20) from e
    rnd = {k: [round(x, n) for x in subject[k]] for k, n in (("point", 2), ("box", 4)) if subject.get(k)}
    return _signing(code, "N", chief.model_note, reads.root_of(code), text, raw, {
        k: v for k, v in {**subject, **rnd}.items() if v is not None})


def objection(code: str, decision: str, reason: str, viewed: str | None = None) -> dict:
    """An objection to a provisional decision (§8.1): it reopens before its gate, the team answers."""
    from mekanik.core.policy import lifecycle

    return _signing(code, decision, lifecycle.object_decision, reads.root_of(code), decision, reason, viewed)


def gate_back(code: str, gate: str, reason: str, viewed: str | None = None, confirmed: bool = False) -> dict:
    refuse(not confirmed, "panel.confirm.required", id=f"O-{gate}")
    return _signing(code, f"O-{gate}", gates.gate_back, reads.root_of(code), gate, reason, viewed)


def open_branch(code: str, commit: str, name: str) -> str:
    """A new work branch from a past commit (old dal_ac): nothing is deleted or moved (e2e 5)."""
    refuse(not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", name), "panel.branch.bad_name", name=name)
    root, new = reads.root_of(code), f"{code}/work/{name}"
    refuse(git.branch_exists(root, new), "panel.branch.exists", branch=new)
    git.git("cat-file", "-e", f"{commit}^{{commit}}", cwd=root)
    git.git("branch", new, commit, cwd=root)
    return new


def new_work(org: str, project: str, title: str, risk_class: str, purpose: str = "", done_criterion: str = "",
             work_type: str | None = None) -> dict:
    """The project screen: `mekanik work new` with the same arguments (the CLI equivalent is shown on the page)."""
    code = works.new_work(org, project, title, risk_class, purpose, done_criterion, work_type=work_type)
    cli = ["mekanik", "work", "new", "--org", org, "--project", project, "--title", title, "--class", risk_class]
    return {"code": code, "path": str(works.find(code)), "branch": f"{code}/work/general", "cli": shlex.join(
        cli + [x for k, v in (("--purpose", purpose), ("--done", done_criterion)) if v for x in (k, v)])}


def open_session(code: str) -> dict:
    """"Open the session": the user's own Claude Code opens in the work folder (deep link, or the command to paste).
    Nothing is started here (T-09); a work whose organization forbids data transfer gets no link (KM2-2 layer 1)."""
    refuse(not hook.org_allowed(code[:3]), "panel.session.data_forbidden", org=code[:3])
    w = works.open_work(code)
    path, prompt = str(w["path"]), f"/mekanik:resume {code}"
    return {"code": code, "path": path, "prompt": prompt, "command": w["command"],
            "link": f"claude-cli://open?cwd={quote(path, safe='')}&q={quote(prompt, safe='')}"}


def upload_limit() -> int:
    q = (load_config().doc.get("panel") or {}).get("upload_limit")
    return int(q["value"] * {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30}[q["unit"]]) if q else UPLOAD_LIMIT


def add_input(code: str, name: str, body: bytes) -> dict:
    """A dropped file (STEP, STL, PDF, image) into inputs/, its SHA-256 into work.yaml `inputs`, one commit; an
    existing input is never overwritten (originals do not change). The folder must be clean (Ö-07)."""
    refuse(not NAME.fullmatch(name) or name.startswith("."), "panel.upload.bad_name", name=name)
    refuse(len(body) > upload_limit(), "panel.upload.too_large", mb=upload_limit() // 2**20)
    root = reads.root_of(code)
    with _one(code):
        chief.ready(root)
        refuse((path := root / "inputs" / name).exists(), "panel.upload.exists", name=name)
        doc, rec = yamlio.read(root / "work.yaml"), {"path": f"inputs/{name}", "sha256": hashlib.sha256(
            body).hexdigest(), "added_at": clock.now()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        yamlio.write(root / "work.yaml", {**doc, "inputs": [*(doc.get("inputs") or []), rec]})
        try:
            sha = commit_logged(root, code, "chief_engineer", "step", t("panel.upload.title", name=name), t(
                "panel.upload.text", sha=rec["sha256"][:12]), [str(path), str(root / "work.yaml")])
        except BaseException:
            path.unlink(missing_ok=True)
            yamlio.write(root / "work.yaml", doc)
            raise
    return {**rec, "commit": sha}


def instruct(code: str, text: str) -> dict:
    reads.root_of(code)
    return inbox.send(code, text, via="panel")


def stop(code: str, reason: str = "") -> dict:
    reads.root_of(code)
    return inbox.stop(code, reason, via="panel")


def resume(code: str) -> dict:
    reads.root_of(code)
    return inbox.resume(code, via="panel")


def intake_answer(code: str, key: str, value) -> dict:
    from mekanik.core.intake import engine

    return engine.answer(reads.root_of(code), key, value, by="chief_engineer", via="panel")
