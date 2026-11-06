# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decisions (old karar_ac, karar_sonucu, dayanagi_yenile; §4.4): all options on one card, each with every changed
value (E-17) and its model (E-15); branches <code>/decision/K-nn-x; a closed one keeps its approved values (E-21)."""

import re
from pathlib import Path

from mekanik.config import load_config

from .. import cards as cardmod, clock, yamlio
from ..errors import GitError
from ..evidence import calc
from ..i18n import t
from ..model.work import load_work
from ..process import Refused, refuse
from ..store import git
from ..store.works import dirty

FILE = "decisions.yaml"
# source: decision — handbook §7 madde 7 (T-06): open branched decisions; config policy.max_open_provisional wins
OPEN_BRANCHED = 5


def _basis(root, names) -> list[dict]:
    if missing := [a for a in names if calc.current_hash(root, a) is None]:
        raise Refused("process.decision.no_calc", calcs=", ".join(missing))
    return [{"calculation": a, "result_hash": calc.current_hash(root, a), "at": clock.now()} for a in names]


def _values(view, opt: dict, changed, role: str) -> list[dict]:
    vals = {a: view.params[a].value for a in changed if a in view.params and view.params[a].value is not None}
    out = []
    for a, x in {**vals, **(opt.get("values") or {})}.items():
        x = x if isinstance(x, dict) else {"value": x}
        if not (unit := x.get("unit") or (view.params[a].unit if a in view.params else None)):
            raise Refused("process.decision.no_unit", param=a)
        out.append({"name": a, "quantity": {"value": float(x["value"]), "unit": unit, "source": "decision",
                                            "decided_by": role}})
    return out


def open_decision(root, did: str, title: str, options: dict, rationale: str, *, dependents=(),
                  role: str = "project_engineer", branched: bool = True, concept: bool = False,
                  category: str | None = None, question: str = "", explain: str = "", proposal: str = "",
                  proposal_rationale: str = "", if_approved: str = "", if_rejected: str = "",
                  visual_selection: dict | None = None, criteria_weights: dict | None = None,
                  requirement_effects: list[dict] | None = None, observations: list[dict] | None = None,
                  basis: list[str] | None = None) -> dict:
    """`mekanik decide`; options {id: title | {title, summary, pros, cons, model_definition, values {param: v}}}."""
    from ..process.step import step, used_cards

    root, view, policy = Path(root), load_work(root), load_config().doc.get("policy") or {}
    effects, obs, reqs = list(requirement_effects or []), list(observations or []), {r["id"] for r in view.requirements}
    if reqs and (unknown := [str(x.get("requirement")) for x in effects if x.get("requirement") not in reqs]):
        raise Refused("process.decision.unknown_requirement", ids=", ".join(unknown))
    refuse(not re.fullmatch(r"K-\d{2}", did), "process.decision.bad_id", id=did)
    refuse(any(d.get("id") == did for d in view.decisions) or any(x == did or x.startswith(f"{did}-") for x in
                                                                   used_cards(root)), "process.decision.used", id=did)
    n, opened = policy.get("max_open_provisional", OPEN_BRANCHED), [d for d in view.decisions if d.get("status") == (
        "proposed") and any(o.get("branch") for o in d.get("options") or [])]
    refuse(branched and len(opened) >= n, "process.decision.limit", n=n)
    refuse(proposal and proposal not in options, "process.decision.bad_proposal", option=proposal)
    opts = {k: {"title": v} if isinstance(v, str) else dict(v) for k, v in options.items()}
    changed = {a for v in opts.values() for a in v.get("values") or {}}
    stop = category in policy.get("stop_categories", [])
    recs, cards = [], []
    for oid, v in opts.items():
        values, branch = _values(view, v, changed, role), f"{view.code}/decision/{did}-{oid}" if branched else None
        refuse(branch and git.branch_exists(root, branch), "process.decision.branch_exists", branch=branch)
        recs.append(_drop({"id": oid, "title": v["title"], "values": values, "model_definition": v.get(
            "model_definition"), "branch": branch}))
        cards.append(_drop({"id": oid, "title": v["title"], "values": values, **{k: v.get(k) for k in (
            "summary", "pros", "cons")}}))
    now, b, unmeasured = clock.now(), "branched" if branched else "plain", [o["text"] for o in obs
                                                                          if not o.get("measured")]
    rec = _drop({"kind": "decision", "schema_version": "1.0", "id": did, "work": view.code, "title": title,
                 "category": category, "mode": "hold" if stop else "provisional", "decided_by": role, "options": recs,
                 "rationale": rationale, "dependents": list(dependents), "requirement_effects": effects,
                 "status": "proposed", "card": did, "opened_at": now, "basis": _basis(root, basis) if basis else None,
                 "history": [{"at": now, "event": "opened", "role": role}], "concept": concept or None,
                 # Phase 1: a decision on unmeasured observations only is a card warning, not a schema block (B6)
                 "observations": obs if obs and (basis or len(unmeasured) < len(obs)) else None,
                 "criteria_weights": {"source": "assumption", "weights": dict(criteria_weights)} if criteria_weights
                 else None, **({} if stop else {"objection_until": view.profile.next_gate(
                     view.gates, view.stage) or view.stage, "visual": {"kind": "card", "id": did},
                     "provisional": {"stream_event": "", "outcome": "pending"}})})
    deps = t("process.decision.deps", ids=", ".join(dependents)) if dependents else ""
    card = _drop({"id": did, "key": f"decision:{did}", "generated": False, "level": rec["mode"], "type": "decision",
                  "stop_category": category if stop else None, "title": f"{did} · {title}", "triggers": ["decision"],
                  "subject": {"decision": did}, "status": "open", "opened_by": role, "options": cards,
                  "question": question, "explain": explain, "proposal": {"choice": proposal,
                                                                         "rationale": proposal_rationale},
                  "if_approved": if_approved or t(f"process.decision.if_approved.{b}", deps=deps),
                  "if_rejected": if_rejected or t(f"process.decision.if_rejected.{b}"),
                  "recorded_as": t("process.decision.recorded_as"), "requirement_effects": effects,   # [] if no list
                  "observations": obs or None, "basis": [{k: x[k] for k in ("calculation", "result_hash")}
                                                          for x in rec.get("basis") or []] or None,
                  "warning": t("process.decision.unmeasured", items="; ".join(unmeasured)) if unmeasured else None,
                  "visual_selection": visual_selection, "values": {"criteria_weights": criteria_weights}
                  if criteria_weights else None})
    txn, doc = yamlio.Txn(), yamlio.read(root / "work.yaml")
    txn.write(root / FILE, [*view.decisions, rec])
    txn.write(root / "cards" / f"{did}.yaml", cardmod.to_file(card))
    doc.setdefault("branches", {}).setdefault("decisions", []).extend(o["branch"] for o in recs if o.get("branch"))
    txn.write(root / "work.yaml", doc)
    out = step(root, t(f"process.decision.opened.{b}", id=did, title=title), role, t(
        "process.decision.step_text", rationale=rationale, options="; ".join(f"{o['id']}) {o['title']}" for o in recs),
        deps=", ".join(dependents) or "—"), [did], kind="decision", txn=txn)
    for o in (o for o in recs if o.get("branch")):
        git.git("branch", o["branch"], out["commit"], cwd=root)
    return {**out, "decision": rec}


def _drop(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "")}


def _edit(root, did: str, txn, event: str, **history) -> tuple[list, dict]:
    """The decision record, its history event added (in the chief's commit, txn); the caller changes the rest."""
    docs = yamlio.read(Path(root) / FILE, []) or []
    d = next(x for x in docs if x.get("id") == did)
    d.setdefault("history", []).append({"at": clock.now(), "event": event, "role": "chief_engineer", **history})
    txn.write(Path(root) / FILE, docs)
    return docs, d


def settle(root, view, did: str, action: str, option: str | None, head: str, txn) -> dict:
    """Approve one option (the others not chosen) or reject all; `affected`: branch commits not in the work branch."""
    docs, d = _edit(root, did, txn, f"{action.rstrip('e')}ed", commit=head)
    affected = {o["id"]: git.git("log", "--format=%h %s", f"HEAD..{o['branch']}", cwd=root).splitlines()
                for o in d["options"] if o.get("branch") and (action == "reject" or o["id"] == option)
                and git.branch_exists(root, o["branch"])}
    for o in d["options"]:
        o.update({"affected": affected[o["id"]]} if o["id"] in affected else {})
    d.update(status=f"{action.rstrip('e')}ed", closed_at=clock.now(), **(
        {"chosen": option, "approved_version": head} if action == "approve" else {}))
    if action == "approve" and (d.get("criteria_weights") or {}).get("source") == "assumption":
        d["criteria_weights"]["source"] = "decision"   # approved as the card showed them
    if action == "approve" and d.get("basis"):   # the basis as of the decision (B5): a change reopens it
        d["basis"] = _basis(root, [x["calculation"] for x in d["basis"]])
    txn.write(Path(root) / FILE, docs)
    view.decisions = docs
    return {"affected": affected, "dependents": d.get("dependents") or []}


def merge(root, did: str, chief: tuple[str, str]) -> str | None:
    """The chosen branch into the work branch (no-ff, chief) → merged | skipped (dirty) | conflict (aborted) | None."""
    d = next(x for x in yamlio.read(Path(root) / FILE, []) if x.get("id") == did)
    if not ((o := next(o for o in d["options"] if o["id"] == d.get("chosen"))).get("branch") and o.get("affected")):
        return None
    if dirty(root):
        return "skipped"
    title = t("process.decision.merge_title", id=did, option=o["id"])
    try:
        git.git("merge", "--no-ff", "-m", git.message(title, title, "chief_engineer", [did]), o["branch"], cwd=root,
                env=git.identity_env(*chief))
        return "merged"
    except GitError:
        git.git("merge", "--abort", cwd=root)
        return "conflict"


def reopen(root, did: str, reason: str, txn) -> None:
    """The chief's approval or rejection was undone: the decision is open again; the history keeps what it was."""
    docs, d = _edit(root, did, txn, "undone")
    d["history"][-1]["note"] = t("process.decision.undone", status=d["status"], option=d.get("chosen") or "—",
                                 reason=reason)
    for k in ("chosen", "approved_version", "closed_at"):
        d.pop(k, None)
    for o in d["options"]:
        o.pop("affected", None)
    d["status"] = "proposed"
    txn.write(Path(root) / FILE, docs)


def refresh_basis(root, did: str, card_id: str, txn) -> None:
    """The chief approved the basis-changed card: the decision holds with today's results (B5)."""
    docs, d = _edit(root, did, txn, "basis_refreshed", note=card_id)
    d["basis"] = _basis(root, [x["calculation"] for x in d.get("basis") or []])
    txn.write(Path(root) / FILE, docs)


def option_values(view, d: dict) -> dict[str, dict]:
    """{option: {param: value}}: work values minus any option's, plus its own (E-17); closed: as approved (E-21)."""
    base = {a: p.value for a, p in view.params.items()}
    try:
        if d.get("approved_version"):
            old = yamlio.load(git.git("show", f"{d['approved_version']}:./params.yaml", cwd=view.root)) or {}
            base = {a: (q or {}).get("value") for a, q in old.items()}
    except GitError:
        pass
    own = {o["id"]: {v["name"]: v["quantity"]["value"] for v in o.get("values") or []} for o in d.get("options") or []}
    changed = {a for v in own.values() for a in v}
    return {oid: {**{a: v for a, v in base.items() if a not in changed}, **vals} for oid, vals in own.items()}

