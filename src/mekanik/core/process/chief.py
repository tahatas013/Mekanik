# SPDX-License-Identifier: AGPL-3.0-or-later
"""The chief's actions (old onay_ver, deger_gir, onay_geri_al, model_notu) and the team's reply: a clean folder at the
version seen (Ö-07), records in a commit signed with his key (APPROVAL-02), gate and release never undone (Ö-15)."""

import re
from pathlib import Path

from mekanik.config import load_config

from .. import cards as cardmod, clock, decisions, yamlio
from ..cards import DECISION_TYPES, approval, signature
from ..checks.builtin.approval import signature as signatures
from ..i18n import num, t
from ..model.work import load_work
from ..store import git
from ..store.works import dirty
from . import Refused, gates, refuse, release
from .step import OPEN, commit_logged, evaluate, log_commit, step, used_cards

NOTES = "records/visuals/notes"
NOTE_MAX = 8 * 2**20   # source: assumption — old model_notu: one screenshot (the panel's are a few hundred KB)


def ready(root, viewed: str | None = None) -> str:
    """Ö-07: no unsaved change of the agent in the work folder, and the version seen is the last one; → HEAD."""
    refuse(d := dirty(root), "process.ready.dirty", files="; ".join(d.splitlines()[:3]))
    if viewed and not ((head := git.head(root)).startswith(viewed) or viewed.startswith(head)):
        raise Refused("process.ready.stale", seen=viewed[:7], head=head[:7])
    return git.head(root)


def _sealed(root, view, card_id: str, paths, sha: str) -> str:
    """Only what was written rides in the chief's signed commit (no hook or staged file, §4.6); else it is undone."""
    pre, top = git.git("rev-parse", "--show-prefix", cwd=root), Path(root).resolve()
    want = {pre + str(Path(p).resolve().relative_to(top)) for p in paths}
    got = set(git.git("diff-tree", "-z", "--no-commit-id", "--name-only", "-r", sha, cwd=root).split("\0")) - {""}
    if got <= want and yamlio.load(git.git("show", f"{sha}:./{approval.FILE}", cwd=root)) == view.approvals:
        return sha
    git.git("reset", "-q", "--keep", f"{sha}~1", cwd=root)
    raise Refused("process.approve.tampered", id=card_id, commit=sha[:7],
                  files=", ".join(sorted(got - want)) or approval.FILE)


def _signed(root, view, results, txn, title: str, text: str, card_id: str) -> str:
    """Cards regenerated with the new records; the chief's signed commit and its log. A failure undoes the writes."""
    try:
        cardmod.sync(new := load_work(root), cardmod.generate(new, results, used_cards(root)), txn)
        return _sealed(root, view, card_id, txn.paths, commit_logged(root, view.code, "chief_engineer", "approval",
                       title, text, [str(p) for p in txn.paths], [card_id], chief=True, sign=True))
    except BaseException:
        txn.rollback()
        raise


def approve(root, card_id: str, action: str = "approve", reason: str = "", option: str | None = None,
            rows: list[str] | None = None, viewed: str | None = None, channel: str = "cli_tty") -> dict:
    """`mekanik approve` / `gate pass` (TTY; chief): approve | reject | comment; a gate passes, a release is cut."""
    root, head, chief = Path(root), ready(root, viewed), load_config().chief
    refuse(action not in ("approve", "reject", "comment"), "process.approve.action", action=action)
    view, model, results, cards = evaluate(root)
    refuse((card := {c["id"]: c for c in cards}.get(card_id)) is None, "process.approve.no_card", id=card_id)
    if card.get("status") in ("closed", "withdrawn", "superseded"):
        raise Refused("process.approve.closed", id=card_id, status=card["status"])
    typ, subj, yes, deciding = card["type"], card.get("subject") or {}, action == "approve", action != "comment"
    if yes and (bad := (card.get("values") or {}).get("bad_results")) and not reason.strip():
        raise Refused("process.approve.reason", id=card_id, n=len(bad))
    if yes and typ in ("gate", "release") and (bad := [r for r in signatures(view) if r.failed]):   # §4.6, KF1-05
        raise Refused("process.approve.signature", id=card_id, n=len(bad), items="; ".join(r.reason for r in bad[:5]))
    if yes and typ == "gate":
        gates.ready_to_pass(root, view, subj["gate"], results, cards)
    prepared = release.ready(root, view, subj["release"], results) if yes and typ == "release" else None
    kw, out, txn = {"commit": head, "reason": reason, "channel": channel, **(
        {"viewed_version": viewed} if viewed else {})}, {"card": card_id, "action": action}, yamlio.Txn()
    try:
        if typ in DECISION_TYPES and deciding:
            refuse(card["status"] not in OPEN, "process.approve.decided", id=card_id, status=card["status"])
            if yes and option not in (ids := [o["id"] for o in card.get("options") or []]):
                raise Refused("process.approve.option", id=card_id, options=", ".join(ids))
            pick = {"option": option} if yes else {}
            recs = [approval.record(view, card_id, {**subj, **pick}, action, chief, **kw, **pick)]
            out["decision"] = decisions.settle(root, view, subj["decision"], action, option, head, txn)
        elif typ == "assumption_list" and deciding:
            if not rows or not set(rows) <= set(subj["params"]):
                raise Refused("process.approve.rows", id=card_id, rows=", ".join(subj["params"]))
            recs = [approval.record(view, f"{card_id}/{r}", {"params": [r]}, action, chief, **kw) for r in rows]
        else:
            recs = [approval.record(view, card_id, subj, action, chief, **kw)]
            if yes and typ == "basis_changed":   # the decision holds with the new results (B5)
                decisions.refresh_basis(root, subj["decision"], card_id, txn)
        for r in recs:
            approval.append(view, r, txn)
        if yes and typ == "gate":
            gates.record_pass(root, view, subj["gate"], recs[0], txn)
    except BaseException:
        txn.rollback()
        raise
    title = t(f"process.approve.title.{action}", id=card_id) + (t("process.approve.with_option", option=option) if (
        yes and option) else "") + (t("process.approve.with_rows", rows=", ".join(rows)) if rows and deciding else "")
    out["commit"] = _signed(root, view, results, txn, title, reason, card_id)
    if yes and typ == "gate":
        try:
            out["gate"] = gates.merge_main(root, view, subj["gate"], chief)
        except BaseException:   # the pass is not left half done: the approval commits go too
            git.git("reset", "-q", "--keep", head, cwd=root)
            raise
    if prepared:
        out["release"] = release.cut(root, view, subj["release"], chief, prepared)
    if yes and typ in DECISION_TYPES and (m := decisions.merge(root, subj["decision"], chief)):
        out["merge"] = m
        log_commit(root, view.code, "chief_engineer", "decision", t(f"process.decision.merge.{m}", id=card_id,
                                                                     option=option), cards=[card_id], chief=True)
    return out


def undo(root, card_id: str, reason: str, row: str | None = None, viewed: str | None = None,
         channel: str = "cli_tty") -> dict:
    """`mekanik approve --action undo`: an `undo` record for the last approval or rejection; a decision reopens."""
    root, head = Path(root), ready(root, viewed)
    refuse(card_id.startswith(("O-", "B-")), "process.undo.gate_release", id=card_id)
    view, _, results, _ = evaluate(root)
    if (last := approval.last(view, rid := f"{card_id}/{row}" if row else card_id)) is None:
        raise Refused("process.undo.nothing", id=rid)
    d = next((x for x in view.decisions if x.get("card", x.get("id")) == card_id), None)
    if (o := next((o for o in (d or {}).get("options") or [] if o["id"] == d.get("chosen")), {})).get("affected"):
        raise Refused("process.undo.merged", id=card_id, option=o["id"])
    undoes = signature.record_commits(root, view.approvals)[view.approvals.index(last)] or last.get("commit") or head
    txn = yamlio.Txn()
    try:
        approval.append(view, approval.record(view, rid, {}, "undo", load_config().chief, commit=head, reason=reason,
                                              channel=channel, undoes=undoes), txn)
        if d:
            decisions.reopen(root, d["id"], reason, txn)
    except BaseException:
        txn.rollback()
        raise
    return {"card": card_id, "undone": last, "commit": _signed(root, view, results, txn, t(
        f"process.undo.title.{last['action']}", id=rid), reason, card_id)}


def value(root, name: str, new: float, reason: str = "", card_id: str | None = None, viewed: str | None = None) -> dict:
    """`mekanik approve --value` (old deger_gir): the chief's own value, source decision, decided by the chief."""
    ready(root := Path(root), viewed)
    refuse(name not in (doc := yamlio.read(root / "params.yaml", {}) or {}), "process.value.unknown", name=name)
    refuse(isinstance(new, bool) or not isinstance(new, (int, float)), "process.value.not_number", name=name)
    p, txn = doc[name], yamlio.Txn()
    p.pop("formula", None)
    p.update(value=float(new), source="decision", decided_by="chief_engineer", note=t(
        "process.value.note", at=clock.now(), old=p.get("value"), reason=reason))
    txn.write(root / "params.yaml", doc)   # a broken record stops the step before its commit; the write is undone
    return step(root, t("process.value.title", name=name, value=num(new)), "chief_engineer", t(
        "process.value.text", card=card_id or "—", reason=reason), [card_id] if card_id else [], kind="intervention",
                paths=["params.yaml", "cards", "records"], chief=True, check_cards=False, txn=txn)


def model_note(root, text: str, png: bytes, subject: dict, channel: str = "cli_tty") -> dict:
    """Old model_notu: screenshot, part, point, camera → card N-nn; its first comment waits for the team's reply."""
    refuse(not text.strip(), "process.note.empty")
    refuse(not png.startswith(b"\x89PNG") or len(png) > NOTE_MAX, "process.note.bad_image", mb=NOTE_MAX // 2**20)
    head, view = ready(root := Path(root)), load_work(root)
    n = [int(x[2:]) for x in {*used_cards(root), *(c["id"] for c in view.cards)} if re.fullmatch(r"N-\d{2}", x)]
    cid, part = f"N-{1 + max(n, default=0):02d}", subject.get("part") or t("process.note.model")
    img, txn = root / NOTES / f"{cid}.png", yamlio.Txn()
    card = {"id": cid, "key": f"note:{cid}", "generated": False, "level": "hold", "type": "model_note",
            "title": t("process.note.title", id=cid, part=part), "triggers": ["model_note"], "status": "open",
            "subject": {k: subject[k] for k in ("commit", "part", "point", "camera", "box") if k in subject},
            "opened_by": "chief_engineer", "question": text.strip(), "explain": t("process.note.explain"),
            "proposal": {"choice": t("process.note.choice"), "rationale": t("process.note.rationale")},
            "if_approved": "—", "if_rejected": "—", "recorded_as": t("process.note.recorded_as"), "visuals": [
                {"kind": "model_view", "id": t("process.note.visual", part=part), "path": f"{NOTES}/{cid}.png"}]}
    try:
        img.parent.mkdir(parents=True, exist_ok=True)
        img.write_bytes(png)
        txn.write(root / "cards" / f"{cid}.yaml", cardmod.to_file(card))
        approval.append(view, approval.record(view, cid, card["subject"], "comment", load_config().chief, commit=head,
                                              reason=text.strip(), channel=channel), txn)
        sha = _sealed(root, view, cid, paths := [str(p) for p in txn.paths] + [str(img)], commit_logged(
            root, view.code, "chief_engineer", "approval", card["title"], text.strip(), paths, [cid], chief=True,
            sign=True))
    except BaseException:
        txn.rollback()
        img.unlink(missing_ok=True)
        raise
    return {"card": cid, "visual": f"{NOTES}/{cid}.png", "commit": sha}


def pending(root) -> list[dict]:
    """`mekanik pending` (old bekleyen_yorumlar): the chief's notes without a team reply, oldest first."""
    view = load_work(root)
    done = {(y["card"], y["comment_at"]) for y in view.replies}
    return sorted(({"card": r["card"], "at": r["at"], "text": r["reason"], "action": r["action"], "row": r.get("row")}
                   for r in view.approvals if r.get("action") in ("comment", "approve", "reject")
                   and (r.get("reason") or "").strip() and (r["card"], r["at"]) not in done), key=lambda x: x["at"])


def reply(root, card_id: str, text: str, comment_at: str | None = None, role: str = "project_engineer",
          commit: str | None = None) -> dict:
    """`mekanik reply`: the team answers the oldest (or given) note (replies.yaml append-only) with the step that did
    it (`commit`, default HEAD; old yanitla --commit); a note closes."""
    refuse(not text.strip(), "process.reply.empty")
    refuse(role == "chief_engineer", "process.reply.team_only")
    root = Path(root)
    refuse(not (waiting := [p for p in pending(root) if p["card"] == card_id]), "process.reply.none", id=card_id)
    if (target := next((p for p in waiting if p["at"] == comment_at), None) if comment_at else waiting[0]) is None:
        raise Refused("process.reply.no_comment", id=card_id, at=comment_at)
    rec, txn = {"card": card_id, "comment_at": target["at"], "text": text.strip(), "role": role, "at": clock.now(),
                "commit": git.git("rev-parse", "--verify", f"{commit or 'HEAD'}^{{commit}}", cwd=root)}, yamlio.Txn()
    txn.write(root / "replies.yaml", [*load_work(root).replies, rec])
    if note := (doc := yamlio.read(path := root / "cards" / f"{card_id}.yaml", {}) or {}).get("type") == "model_note":
        txn.write(path, {**doc, "status": "superseded", "closed_reason": t("process.reply.applied", text=text.strip(),
                                                                           commit=rec["commit"][:7])})
    try:
        commit_logged(root, load_work(root).code, role, "reply", t("process.reply.title." + (
            "note" if note else "comment"), id=card_id), t("process.reply.text", comment=target["text"],
                                                           text=text.strip()), [str(p) for p in txn.paths], [card_id])
    except BaseException:
        txn.rollback()
        raise
    return rec
