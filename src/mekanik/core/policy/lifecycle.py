# SPDX-License-Identifier: AGPL-3.0-or-later
"""Life of a provisional decision (architecture §8.1, handbook §7): provisional_active → objected (the chief's
signed `objection` record, `mekanik object`) → reverted (the team goes back to an alternative; the work resting on
the decision is listed from the dependency record, D3) or kept (the team's reasoned reply; keeping needs the chief's
approval → objected_kept). Without an objection the gate the window ends at accepts it (accepted_at_gate, D4).
Stream lines (S's `report.stream.emit`) follow the action's commit and are committed right after it: the opening as
`provisional_decision` (D2), the objection as `objection`, the acceptance at a gate as `decision`."""

from __future__ import annotations

from pathlib import Path

from mekanik.config import load_config

from .. import clock, yamlio
from ..cards import approval
from ..evidence import calc
from ..i18n import t
from ..model.work import load_work
from ..process import refuse
from ..report import stream
from ..store import git

FILE, ACTIVE, OBJECTED = "decisions.yaml", "provisional_active", "objected"


def _line(root: Path, kind: str, role: str, who, title: str, cards: list[str], **data) -> dict:
    """A stream line after the action's commit (never taken back), committed right away."""
    ev = stream.emit(root, kind, role=role, cards=cards, **data)
    git.commit(root, git.message(title, None, role, cards), [str(root / stream.FILE)], who)
    return ev


def announce(root, did: str, role: str) -> dict:
    """D2: the provisional decision's stream line with the first figure of its card (made in the decision's step)
    and the gate its objection window ends at; the decision keeps the line's id and the figure as its visual."""
    root = Path(root)
    docs, card = yamlio.read(root / FILE, []), yamlio.read(root / "cards" / f"{did}.yaml", {}) or {}
    d = next(x for x in docs if x["id"] == did)
    ev = stream.emit(root, "provisional_decision", role=role, line=t(
        "policy.provisional.line", id=did, title=d["title"], gate=d["objection_until"]), cards=[did], visuals=[
        v.get("path") or v for v in card.get("visuals") or []][:1], refs=[{"kind": "decision", "id": did}],
        objection_until=d["objection_until"])
    d["provisional"]["stream_event"], d["visual"] = ev["id"], ev["visuals"][0]
    yamlio.write(root / FILE, docs)
    git.commit(root, git.message(t("policy.provisional.title", id=did), None, role, [did]),
               [str(root / FILE), str(root / stream.FILE)], load_config().team)
    return ev


def dependents(view, d: dict) -> list[str]:
    """D3: what rests on the decision — its dependency record, the values its options change, the calcs reading them,
    the cards about them, the decisions naming it, the commits of its chosen branch not in the work branch."""
    names = sorted({v["name"] for o in d.get("options") or [] for v in o.get("values") or []})
    readers = {}
    for cid, rec in calc.recorded(view.root).items():
        for i in rec.get("inputs") or []:
            readers.setdefault(i["name"], []).append(cid)
    out = [*(d.get("dependents") or []), *(f"param:{n}" for n in names)]
    out += [f"calc:{c}" for n in names for c in readers.get(n, [])]
    out += [f"card:{c['id']}" for c in view.cards if c.get("id") != d.get("card", d["id"])
            and set((c.get("subject") or {}).get("params") or []) & set(names)]
    out += [f"decision:{x['id']}" for x in view.decisions if d["id"] in (x.get("dependents") or [])]
    for o in d.get("options") or []:
        if o.get("branch") and o["id"] == d.get("chosen") and git.branch_exists(view.root, o["branch"]):
            out += [f"commit:{x}" for x in git.git("log", "--format=%h %s", f"HEAD..{o['branch']}",
                                                     cwd=view.root).splitlines()]
    return list(dict.fromkeys(out))


def due(view, gate: str) -> list[dict]:
    """Provisional decisions without an objection whose window ends at `gate` (or before): accepted by its pass."""
    at = view.profile.stages.index
    return [d for d in view.decisions if d.get("mode") == "provisional" and d.get("status") == ACTIVE
            and at(d.get("objection_until") or gate) <= at(gate)]


def accept(root, view, gate: str, commit: str, txn, tag: str) -> list[str]:
    """D4: in the chief's gate commit the due decisions become accepted_at_gate with their chosen option (the history
    note is the pass's tag); a chosen branch's commits not in the work branch are its `affected` (merged after the
    pass, as an approved decision's are: gates.merge_main)."""
    docs, now = yamlio.read(Path(root) / FILE, []) or [], clock.now()
    ids = {d["id"] for d in due(view, gate)}
    for d in (d for d in docs if d.get("id") in ids):
        for o in (o for o in d["options"] if o["id"] == d.get("chosen") and o.get("branch")):
            if git.branch_exists(root, o["branch"]):
                o["affected"] = git.git("log", "--format=%h %s", f"HEAD..{o['branch']}", cwd=root).splitlines()
        d.update(status="accepted_at_gate", approved_version=commit, closed_at=now)
        d["provisional"]["outcome"] = "accepted_no_objection"
        d.setdefault("history", []).append({"at": now, "event": "accepted_at_gate", "role": "chief_engineer",
                                            "note": tag, "commit": commit})
    if ids:
        txn.write(Path(root) / FILE, docs)
    return sorted(ids)


def announce_accepted(root, tag: str, chief) -> list[dict]:
    """After the gate's merge and tag: one `decision` line per decision accepted with the pass `tag` (day-end summary
    §1 lists them), committed in one commit."""
    root, events = Path(root), []
    for d in yamlio.read(root / FILE, []) or []:
        if any(h.get("event") == "accepted_at_gate" and h.get("note") == tag for h in d.get("history") or []):
            events.append(stream.emit(root, "decision", role="chief_engineer", line=t(
                "policy.accepted.line", id=d["id"], title=d["title"], option=d.get("chosen"), tag=tag),
                cards=[d.get("card") or d["id"]], refs=[{"kind": "decision", "id": d["id"]}]))
    if events:
        git.commit(root, git.message(t("policy.accepted.title", tag=tag, n=len(events)), None, "chief_engineer", [
            e["refs"][0]["id"] for e in events]), [str(root / stream.FILE)], chief)
    return events


def _provisional(view, did: str) -> dict:
    d = next((x for x in view.decisions if x.get("id") == did), None)
    refuse(d is None or d.get("mode") != "provisional", "policy.object.not_provisional", id=did)
    return d


def object_decision(root, did: str, reason: str, viewed: str | None = None, channel: str = "cli_tty") -> dict:
    """`mekanik object <K-nn>` (the chief; TTY): an objection to a provisional decision before its window's gate is
    passed — a signed `objection` record, the decision objected, its dependent work listed (D3), a stream line."""
    from ..process import chief, gates
    from ..process.step import evaluate

    root, head = Path(root), chief.ready(root, viewed)
    refuse(not reason.strip(), "policy.object.reason")
    view, _, results, _ = evaluate(root)
    d = _provisional(view, did)
    refuse(d.get("status") != ACTIVE, "policy.object.state", id=did, status=d.get("status"))
    gate, cid = d.get("objection_until"), d.get("card") or did
    refuse(gate in gates.passed(root, view.code), "policy.object.window", id=did, gate=gate)
    txn = yamlio.Txn()
    try:
        rec = approval.append(view, approval.record(view, cid, {"decision": did}, "objection", load_config().chief,
                                                    commit=head, reason=reason.strip(), channel=channel, **(
                                                        {"viewed_version": viewed} if viewed else {})), txn)
        docs = yamlio.read(root / FILE)
        x = next(x for x in docs if x["id"] == did)
        x["status"], x["provisional"]["objection"] = OBJECTED, {"at": rec["at"], "text": rec["reason"], "commit": head}
        x.setdefault("history", []).append({"at": rec["at"], "event": "objected", "role": "chief_engineer",
                                            "note": rec["reason"], "commit": head})
        txn.write(root / FILE, docs)
        deps = dependents(view, x)
    except BaseException:
        txn.rollback()
        raise
    sha = chief._signed(root, view, results, txn, t("policy.object.title", id=did), rec["reason"], cid)
    ev = _line(root, "objection", "chief_engineer", load_config().chief, t("policy.object.title", id=did), [cid],
               line=t("policy.object.line", id=did, reason=rec["reason"], n=len(deps)),
               refs=[{"kind": "decision", "id": did}])
    return {"decision": did, "card": cid, "commit": sha, "dependents": deps, "event": ev}


def respond(root, did: str, text: str, keep: bool = False, option: str | None = None,
            role: str = "project_engineer") -> dict:
    """The team's answer to an objection (a reply to it): back to an alternative (`option`, default the first other
    one) → reverted with the dependent work listed (D3); or `keep` with a reason → objected until the chief approves
    keeping it (`mekanik approve <K-nn>` → objected_kept) or rejects it."""
    from ..process.step import RECORDS, step

    refuse(not text.strip(), "policy.respond.empty")
    refuse(role == "chief_engineer", "policy.respond.team_only")
    root, view = Path(root), load_work(root)
    d = _provisional(view, did)
    refuse(d.get("status") != OBJECTED, "policy.respond.state", id=did, status=d.get("status"))
    docs, now, cid, txn = yamlio.read(root / FILE), clock.now(), d.get("card") or did, yamlio.Txn()
    x, deps = next(x for x in docs if x["id"] == did), []
    txn.write(root / "replies.yaml", [*view.replies, {"card": cid, "comment_at": d["provisional"]["objection"]["at"],
                                                      "text": text.strip(), "role": role, "at": now,
                                                      "commit": git.head(root)}])
    if not keep:
        alt = option or next(o["id"] for o in x["options"] if o["id"] != x.get("chosen"))
        refuse(alt == x.get("chosen") or alt not in [o["id"] for o in x["options"]], "policy.respond.option",
               id=did, option=alt)
        deps = dependents(view, x)
        x.update(status="reverted", chosen=alt, closed_at=now)
        x["provisional"].update(outcome="objected_reverted", reverted_work=deps)
        x.setdefault("history", []).append({"at": now, "event": "reverted", "role": role, "note": text.strip()})
        txn.write(root / FILE, docs)
    out = step(root, t(f"policy.respond.title.{'kept' if keep else 'reverted'}", id=did), role, text.strip(), [cid],
               kind="decision", paths=RECORDS, txn=txn)
    return {**out, "decision": x, "dependents": deps}
