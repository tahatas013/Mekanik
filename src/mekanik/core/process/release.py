# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release (old baski, baski_cik, istek_geri_cek; handbook §6): the hold card B-nn with its files' SHA-256 when nothing
blocks; after the chief's signed approval the tag <code>-release-<no> on the request and the files in out/<tag>/."""

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path

from mekanik.plugins import registry

from .. import cards as cardmod, clock, quality, yamlio
from ..cards import check_items
from ..checks.builtin import assurance
from ..checks.result import BLOCK, summary
from ..evidence import calc
from ..i18n import t
from ..model.work import load_work
from ..store import git
from . import Refused, refuse
from .gates import quality_card, request_commit, stage
from .step import CARD_VISUALS, OPEN, RECORDS, commit_logged, evaluate, step, used_cards


def pending(code: str, commit: str) -> Path:
    """Files waiting for approval: in the data folder, not the cache (which may drop them)."""
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "mekanik/release" / code / commit


def _blocked(results) -> None:
    if blocks := [r for r in results if r.status == BLOCK]:
        raise Refused("process.release.blocked", n=len(blocks), items="; ".join(r.reason for r in blocks[:5]),
                      results=blocks)


def release_request(root, role: str = "project_engineer", purpose: str = "", choice: str = "",
                    rationale: str = "", basis=()) -> dict:
    """`mekanik release request`: files (the packages' release_files hook), figures and the B-nn card (hold).
    `basis`: the calcs the release rests on; they are critical (§10.2), so CALC-03 and CALC-04 judge them before the
    card opens; the card's subject.basis keeps them critical unless the request is withdrawn."""
    root, hooks, basis = Path(root), registry().model_hooks(), sorted(set(basis))
    view, model, results, cards = evaluate(root)
    refuse(not model, "process.release.no_model")
    refuse(unknown := [b for b in basis if b not in calc.recorded(root)], "policy.release.basis_unknown",
           calcs=", ".join(unknown))
    used = [int(x[2:]) for x in used_cards(root) if re.fullmatch(r"B-\d{2}", x)] + [
        int(x.rsplit("-", 1)[1]) for x in git.git("tag", "--list", f"{view.code}-release-*", cwd=root).split()]
    no = f"{1 + max(used, default=0):02d}"
    cid, tag, prof = f"B-{no}", f"{view.code}-release-{no}", (view.doc.get("profiles") or {}).get(
        "manufacturing", "—")
    if basis:   # judged as they will be once the card is open
        view.cards = [*view.cards, {"id": cid, "type": "release", "status": "open", "subject": {"basis": basis}}]
        results = [r for r in results if r.rule not in ("CALC-03", "CALC-04")] + assurance.cross(view) + \
            assurance.validity(view)
    _blocked(results + (extra := [r for h in registry().release_hooks for r in h(view, model)]))
    path, rep = quality.require_clear(root, t("process.release.review"))
    tmp, s = Path(tempfile.mkdtemp(prefix="mekanik-release-")), summary(results)
    files = hooks.release_files(view, model, tmp) if hooks.has("release_files") else {}
    figs, estimate = hooks.release_visuals(view, model) if hooks.has("release_visuals") else ([], None)
    holds, txn = [c["id"] for c in cards if c.get("level") == "hold" and c.get("status") in OPEN], yamlio.Txn()
    refs = [{"kind": "model_view", "id": title, "path": f"{CARD_VISUALS}/{cid}{f'-{i + 1}' if i else ''}.svg"}
            for i, (title, _) in enumerate(figs)]
    for ref, (_, svg) in zip(refs, figs):
        txn.write_text(root / ref["path"], svg)
    card = {"id": cid, "key": f"release:{no}", "generated": False, "level": "hold", "type": "release",
            "title": t("process.release.title", code=view.code, no=no), "triggers": ["release"],
            "subject": {"release": no, "files": files, **({"basis": basis} if basis else {})}, "status": "open",
            "opened_by": role, "visuals": refs,
            "checks": check_items(extra), **quality_card(root, path, rep, profile=prof, stage=stage(root, view),
                                                          summary=s, open_holds=holds, parts=sorted(model),
                                                          estimate=estimate),
            "question": t("process.release.question", no=no), "explain": (f"{purpose.rstrip('.')}. " if purpose else "")
            + t("process.release.explain", n=len(model), profile=prof),
            "proposal": {"choice": choice or t("process.release.approve"), "rationale": rationale or (
                t("process.release.rationale", **s) + t("process.release.holds", ids=", ".join(holds) or "—"))},
            "if_approved": t("process.release.if_approved", tag=tag), "if_rejected": t("process.release.if_rejected"),
            "recorded_as": t("process.release.recorded_as")}
    txn.write(root / "cards" / f"{cid}.yaml", cardmod.to_file(card))
    try:
        out = step(root, t("process.release.requested", no=no), role, t(
            "process.release.step_text", parts=", ".join(sorted(model)), profile=prof, stage=card["values"]["stage"],
            folder=f"out/{tag}/"), [cid], [r["path"] for r in refs[:1]], kind="release", isometric=not refs,
            trailers={"Request": cid}, txn=txn)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    (dest := pending(view.code, out["commit"])).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tmp), dest)
    return {**out, "no": no, "files": files, "folder": str(dest)}


def ready(root, view, no: str, results) -> tuple[str, Path, dict]:
    """Old _baski_hazir_mi: not released, no block but its own hold (E-24), same files → (request, folder, card)."""
    refuse(git.git("tag", "--list", tag := f"{view.code}-release-{no}", cwd=root), "process.release.tagged", tag=tag)
    _blocked([r for r in results if r.ref != f"B-{no}"])
    req, card = request_commit(root, f"B-{no}"), yamlio.read(Path(root) / "cards" / f"B-{no}.yaml")
    if not (src := pending(view.code, req)).exists() or any(not (src / f).exists() or hashlib.sha256(
            (src / f).read_bytes()).hexdigest() != h for f, h in (card["subject"].get("files") or {}).items()):
        raise Refused("process.release.files_changed", id=f"B-{no}")
    return req, src, card


def cut(root, view, no: str, chief: tuple[str, str], prepared: tuple) -> dict:
    """After the approval commit (old baski_cik): the chief's tag on the request, the files and a report in out/."""
    (req, src, card), tag = prepared, f"{view.code}-release-{no}"
    git.git("tag", "-a", tag, req, "-m", t("process.release.tag", no=no, who=chief[0]), cwd=root,
            env=git.identity_env(*chief))
    shutil.copytree(src, dest := Path(root) / "out" / tag, dirs_exist_ok=True)
    v = card["values"]
    yamlio.write_text(dest / "report.md", t("process.release.report", tag=tag, who=chief[0], commit=req, profile=v.get(
        "profile"), stage=v.get("stage"), checks=t("store.log.checks", **v["summary"])) + "".join(
        f"| {f} | `{h}` |\n" for f, h in (card["subject"].get("files") or {}).items()))
    step(root, t("process.release.cut_title", no=no), "project_engineer", t("process.release.cut_text", tag=tag),
         [f"B-{no}"], kind="release", paths=RECORDS, check_cards=False)
    return {"tag": tag, "folder": str(dest)}


def withdraw(root, card_id: str, reason: str, role: str = "project_engineer") -> dict:
    """The team withdraws its release request (old istek_geri_cek): nothing is printed, the card file stays."""
    refuse(not re.fullmatch(r"B-\d{2}", card_id), "process.withdraw.only_release", id=card_id)
    if git.git("tag", "--list", tag := f"{(view := load_work(root)).code}-release-{card_id[2:]}", cwd=root):
        raise Refused("process.withdraw.released", id=card_id, tag=tag)
    doc = yamlio.read(path := Path(root) / "cards" / f"{card_id}.yaml")
    yamlio.write(path, {**doc, "status": "withdrawn", "closed_reason": t("process.withdraw.reason", reason=reason,
                                                                          at=clock.now())})
    return {"card": card_id, "commit": commit_logged(root, view.code, role, "release", t(
        "process.withdraw.title", id=card_id), t("process.withdraw.text", reason=reason), [str(path)], [card_id])}
