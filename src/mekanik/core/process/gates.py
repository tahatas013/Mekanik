# SPDX-License-Identifier: AGPL-3.0-or-later
"""Gates (§4.2; old akis kapı kısmı): checklist, requirement table (B2), gate plan (B7), stage finish with the gate
card and, after the chief's signed approval, a signed merge of the request into <code>/main tagged <code>-G<n>.
Phase 2 (§4.2, §8.1, §10.6): the gate card lists the provisional decisions its pass accepts (D4; a chosen branch then
merges into the work branch) and the stage measures (D5); open objections stop the pass; G4/G5 need every mandatory
requirement met (REQ-01, F5); the return G3 → G2 (`gate_back`, Ö-17, E-26) keeps the G2 tag, adds
<code>-G2-back-<n> and asks the gate again (<code>-G2-2)."""

import tempfile
from collections import Counter
from pathlib import Path

from mekanik.config import load_config

from .. import cards as cardmod, clock, quality, yamlio
from ..cards import approval
from ..checks.builtin import assurance
from ..checks.result import BLOCK, PASS, WARN
from ..errors import GitError
from ..evidence import calc
from ..i18n import t
from ..model.schema import validate
from ..model.work import load_work
from ..policy import lifecycle, metrics
from ..store import git
from . import Refused, refuse
from .step import OPEN, RECORDS, evaluate, log_commit, step

VALIDATION_GATE = "G4"   # handbook §6: a mandatory requirement verified by experiment needs it in every class (Ö-26)


def _rounds(root, code: str) -> tuple[Counter, Counter]:
    """(pass tags, return tags) per gate: <code>-G2, <code>-G2-2 … and <code>-G2-back-1 …"""
    passes, backs = Counter(), Counter()
    for x in git.git("tag", "--list", f"{code}-G*", cwd=root).split():
        g, _, rest = x[len(code) + 1:].partition("-")
        (backs if rest.startswith("back") else passes)[g] += 1
    return passes, backs


def passed(root, code: str) -> list[str]:
    """Gates passed: more pass tags than returns to the gate."""
    passes, backs = _rounds(root, code)
    return [g for g in passes if passes[g] > backs[g]]


def tag_name(root, code: str, gate: str) -> str:
    """The tag of the gate's next pass: <code>-<G> the first time, <code>-<G>-<n> after a return."""
    return f"{code}-{gate}" + (f"-{n + 1}" if (n := _rounds(root, code)[0][gate]) else "")


def stage(root, view) -> str:
    """The real stage: the gate after the last tagged one (work.yaml may lag behind on another branch)."""
    done = [g for g in view.gates if g in passed(root, view.code)]
    return (view.profile.next_gate(view.gates, done[-1]) or done[-1]) if done else view.stage


def precheck(root, view, gate: str) -> None:
    refuse(gate not in view.gates, "process.gate.not_planned", gate=gate, cls=view.risk_class)
    refuse(gate in passed(root, view.code), "process.gate.passed", gate=gate, tag=f"{view.code}-{gate}")
    refuse((now := stage(root, view)) != gate, "process.gate.wrong_stage", code=view.code, stage=now, gate=gate)


def requirement_table(view) -> list[dict]:
    """Per requirement: met | not_met | awaiting_evidence and the evidence (B2); 'met' needs evidence that CALC-03 and
    CALC-04 accept (§10.6), else it is awaiting evidence."""
    return assurance.requirement_table(view)


def risk_rule(view) -> str | None:
    """Handbook §5: a yes to one of the first questions → the strictest class; all no but the last → the loosest."""
    q, order = [x["id"] for x in view.profile.risk_questions], list(view.profile.classes)
    if any(k not in (a := {x["question_id"]: x["answer"] for x in view.doc.get("risk_answers") or []}) for k in q):
        return None
    return order[0] if any(a[k] for k in q[:-1]) else order[-1] if a[q[-1]] else order[1]


def items(view, gate: str, results, cards) -> list[dict]:
    """The profile's checklist of the gate: [{id, ok, required, text}]; an id ending in '!' is required to pass."""
    own, req, order, rule = f"O-{gate}", view.requirements, list(view.profile.classes), risk_rule(view)
    blocks = [r for r in results if r.status == BLOCK and r.ref != own]
    concept, ids = [d for d in view.decisions if d.get("concept")], lambda xs: ", ".join(xs)
    holds = [c["id"] for c in cards if c.get("level") == "hold" and c.get("status") in OPEN and c["id"] != own]
    vague = [r["id"] for r in req if not (r.get("criterion") and r.get("origin"))]
    blind = [r["id"] for r in req if r.get("kind") == "mandatory" and not r.get("verification")]
    undefined = sorted({r.ref for r in results if r.extra.get("undefined") and r.ref})
    # INTAKE-01, STDMAP-01 (§7, §10.8); a work without a work type predates intake (schema 1.1 makes it required)
    pre = [r.reason for r in results if r.extra.get("precondition") == gate and r.failed and view.doc.get("work_type")]
    unmet = [x["requirement"] for x in requirement_table(view) if x["status"] != "met" and x["requirement"] in {
        r["id"] for r in req if r.get("kind") == "mandatory" and r.get("status") != "withdrawn"}]
    tests = {
        "requirements_listed": (bool(req), {"n": len(req)}),
        "requirement_ids": (len({r["id"] for r in req}) == len(req), {}),
        "requirements_measurable": (not vague, {"ids": ids(vague)}),
        "risk_answered": (rule is not None, {"cls": rule}),
        "risk_class_rule": (bool(rule) and order.index(view.risk_class) <= order.index(rule),
                            {"cls": view.risk_class, "rule": rule}),
        "three_options": (any(len(d["options"]) >= 3 for d in concept), {}),
        "weights_by_chief": (any((d.get("criteria_weights") or {}).get("source") == "decision" for d in concept), {}),
        "choice_recorded": (any(d.get("chosen") for d in concept), {}),
        "no_unsourced": (not any(r.check == "source" and r.failed for r in results), {}),
        "records_defined": (not undefined, {"ids": ids(undefined)}),
        "manufacturing_profile": (view.manufacturing is not None,
                                  {"ref": (view.doc.get("profiles") or {}).get("manufacturing")}),
        "no_block": (not blocks, {"items": "; ".join(r.reason for r in blocks[:5])}),
        "mandatory_verified": (not blind, {"ids": ids(blind)}),
        "validation_written": (any(yamlio.read(p, {}).get("conditions") for p in (view.root / "experiments").glob(
            "*.yaml")), {}),
        "decisions_reviewed": (all(d.get("status") not in (None, "proposed") for d in view.decisions), {}),
        "approvals_current": (not [c for c in cards if c.get("approval_state") == "dropped"
                                   and c.get("status") in OPEN], {}),
        "no_open_hold": (not holds, {"ids": ids(holds)}),
        "requirements_met": (not unmet, {"ids": ids(unmet)}),   # REQ-01 (F5)
        "preconditions_met": (not pre, {"items": "; ".join(pre[:5])})}   # the first gate's (§7, §10.8)
    out = []
    for item in view.profile.gate_items.get(gate, ()):
        ok, args = tests[key := item.rstrip("!")]
        part = "policy.gate" if key in ("requirements_met", "preconditions_met") else "process.gate"
        detail = f" ({t(f'{part}.detail.{key}', **args)})" if any(args.values()) else ""
        out.append({"id": key, "ok": ok, "required": item.endswith("!"), "text": t(f"{part}.item.{key}") + detail})
    return out


def plan_update(root, role: str = "project_engineer") -> list[str]:
    """The validation gate when a mandatory requirement is verified by experiment (B7); → the added gates."""
    view, root = load_work(root), Path(root)
    need = [r["id"] for r in view.requirements if r.get("kind") == "mandatory" and (r.get("verification") or {}).get(
        "method") == "experiment"]
    if not need or VALIDATION_GATE in view.gates:
        return []
    doc, why, txn = yamlio.read(root / "work.yaml"), t("process.gate.g4_reason", ids=", ".join(need)), yamlio.Txn()
    doc["process"]["gates"] = sorted({*view.gates, VALIDATION_GATE}, key=view.profile.stages.index)
    doc["process"]["gate_status"][VALIDATION_GATE] = {"status": "pending", "added_reason": why}
    txn.write(root / "work.yaml", doc)
    step(root, t("process.gate.g4_title"), role, why, paths=["work.yaml"], check_cards=False, txn=txn)
    return [VALIDATION_GATE]


def quality_card(root, path: Path, rep: dict, **values) -> dict:
    """Quality fields of a gate or release card (old _kalite_ozeti): the review, its counts, closed high findings."""
    f, rel = rep.get("findings") or [], str(Path(path).relative_to(root))
    return {"quality": {"review": {"kind": "quality_review", "id": rep["id"], "path": rel}, "open_high": 0},
            "values": {**values, "bad_results": calc.bad_results(calc.recorded(root)), "quality": {
                "report": rel, "commit": rep.get("commit"), "open": sum(x.get("status") == "open" for x in f),
                **{k: sum(x["severity"] == k for x in f) for k in ("high", "medium", "low")},
                "closed_high": [f"{x['no']} {x['location']} — {x['problem']}" for x in f
                                if x["severity"] == "high" and x.get("status") == "closed"]}}}


def stage_finish(root, gate: str, role: str = "project_engineer") -> dict:
    """`mekanik stage finish <G>` (old asama_bitir): plan, checklist, checks, review (QUALITY-01), gate card O-<G>."""
    plan_update(root := Path(root), role)
    precheck(root, view := load_work(root), gate)
    path, rep = quality.require_clear(root, t("process.gate.review", gate=gate))
    view, model, results, cards = evaluate(root, view)
    if bad := [r for r in results if r.rule == "CALC-03" and r.extra.get("status") == "disagree"]:   # §10.2
        raise Refused("policy.gate.calc03", gate=gate, items="; ".join(r.reason for r in bad))
    lst, nxt, cid, subject = items(view, gate, results, cards), view.profile.next_gate(view.gates, gate), f"O-{gate}", {
        "gate": gate, "design": True}
    accepts, measures = [d["id"] for d in lifecycle.due(view, gate)], metrics.stage(view, gate, cards)
    objected = [d["id"] for d in view.decisions if d.get("status") == lifecycle.OBJECTED]
    failed, others = [x["text"] for x in lst if not x["ok"]], [c["id"] for c in cards if c.get("status") in OPEN
                                                               and c["id"] != cid]
    card = {"id": cid, "key": f"gate:{gate}", "generated": False, "level": "hold", "type": "gate", "triggers": ["gate"],
            "title": t("process.gate.title", code=view.code, gate=gate), "subject": subject, "status": "open",
            "opened_by": role, "approval_hash": approval.digest(approval.subject_values(view, subject)),
            "checks": [{"rule": f"{gate}.{x['id']}", "result": PASS if x["ok"] else BLOCK if x["required"] else WARN,
                        "message": x["text"]} for x in lst], "requirement_table": requirement_table(view),
            **quality_card(root, path, rep, gate=gate, next=nxt, open_cards=others, policy=measures, objected=objected,
                           provisional=[{k: d.get(k) for k in ("id", "title", "chosen", "category", "objection_until")}
                                        for d in lifecycle.due(view, gate)], summary={
                "title": view.title, "purpose": view.doc.get("purpose", ""), "risk_class": view.risk_class,
                "requirements": [f"{r['id']}: {r['text']}" for r in view.requirements],
                **({"risk_answers": view.doc.get("risk_answers") or []} if gate == view.gates[0] else {})}),
            "question": t("process.gate.question", code=view.code, gate=gate),
            "explain": t("process.gate.explain", meaning=t(f"process.stage.{gate}")),
            "proposal": {"choice": t("process.gate.reject" if failed else "process.gate.approve"), "rationale": (t(
                "process.gate.failed", items="; ".join(failed)) if failed else t("process.gate.all_passed", n=len(lst)))
                + (t("process.gate.others", ids=", ".join(others)) if others else "")},
            "if_approved": t(f"process.gate.if_approved.{'next' if nxt else 'last'}", tag=tag_name(
                root, view.code, gate), next=nxt) + (t("policy.gate.accepts", ids=", ".join(accepts)) if accepts
                                                      else "")
            + (t("policy.gate.objected", gate=gate, ids=", ".join(objected)) if objected else ""),
            "if_rejected": t("process.gate.if_rejected", gate=gate),
            "recorded_as": t("process.gate.recorded_as")}
    validate("card", doc := cardmod.to_file(card), f"cards/{cid}.yaml")
    (txn := yamlio.Txn()).write(root / "cards" / f"{cid}.yaml", doc)
    title = t("process.gate.requested", gate=gate) + (t("process.gate.requested_failed", n=len(failed))
                                                      if failed else "")
    text = "\n".join([t("process.gate.list")] + [f"- {'✓' if x['ok'] else '✗'} {x['text']}" for x in lst] + [
        "", metrics.line(measures)])   # D5: in the log entry; the gate's stream line refs the card (values.policy)
    return {**step(root, title, role, text, [cid], kind="gate", paths=RECORDS, trailers={"Request": cid}, txn=txn),
            "items": lst}


def request_commit(root, card_id: str) -> str:
    """The newest commit that requested the card (trailer `Request: <card>`)."""
    if not (sha := git.git("log", "-1", "--format=%H", "-E", f"--grep=^Request: {card_id}$", cwd=root)):
        raise Refused("process.request.missing", id=card_id)
    return sha


def ready_to_pass(root, view, gate: str, results, cards) -> None:
    """Before the approval is recorded (old _kapi_hazir_mi): order, required items, request, design unchanged."""
    precheck(root, view, gate)
    if must := [x["text"] for x in items(view, gate, results, cards) if x["required"] and not x["ok"]]:
        raise Refused("process.gate.required_failed", gate=gate, items="; ".join(must))
    if objected := [d["id"] for d in view.decisions if d.get("status") == lifecycle.OBJECTED]:   # §8.1
        raise Refused("policy.gate.open_objection", gate=gate, ids=", ".join(objected))
    request_commit(root, card := f"O-{gate}")
    if next(c for c in cards if c["id"] == card).get("approval_hash") != approval.digest(approval.subject_values(
            view, {"gate": gate, "design": True})):
        raise Refused("process.gate.changed", id=card)


def record_pass(root, view, gate: str, rec: dict, txn) -> None:
    """work.yaml in the chief's commit: the gate done with its tag and approval, the next stage started."""
    p, now = (doc := yamlio.read(Path(root) / "work.yaml"))["process"], clock.now()
    p["gate_status"][gate] = {**p["gate_status"].get(gate, {}), "status": "done", "finished_at": now, "tag": tag_name(
        root, view.code, gate), "approval": {"kind": "card", "id": f"O-{gate}", "hash": rec["approved_hash"]}}
    lifecycle.accept(root, view, gate, rec.get("commit") or git.head(root), txn, p["gate_status"][gate]["tag"])  # D4
    if nxt := view.profile.next_gate(p["gates"], gate):
        p["stage"], p["gate_status"][nxt] = nxt, {**p["gate_status"].get(nxt, {}), "status": "in_progress",
                                                  "started_at": now}
    else:
        doc["closed_at"] = now
    txn.write(Path(root) / "work.yaml", doc)


def merge_main(root, view, gate: str, chief: tuple[str, str]) -> dict:
    """Old kapi_gec: the request's tree with HEAD's records, a signed merge on <code>/main and the chief's tag."""
    card, main, tag, env = f"O-{gate}", f"{view.code}/main", tag_name(root, view.code, gate), git.identity_env(*chief)
    req, prefix = request_commit(root, card), git.git("rev-parse", "--show-prefix", cwd=root)
    with tempfile.TemporaryDirectory() as d:
        git.git("read-tree", req, cwd=root, env=(idx := {"GIT_INDEX_FILE": str(Path(d) / "index")}))
        for f in ("approvals.yaml", "work.yaml", f"cards/{card}.yaml", *(["decisions.yaml"] if (
                Path(root) / "decisions.yaml").exists() else [])):   # decisions: those accepted at the gate (D4)
            blob = git.git("rev-parse", f"HEAD:{prefix}{f}", cwd=root)
            git.git("update-index", "--add", "--cacheinfo", f"100644,{blob},{prefix}{f}", cwd=root, env=idx)
        tree = git.git("write-tree", cwd=root, env=idx)
    msg = git.message(t("process.gate.merge_title", gate=gate, branch=git.branch(root)), t(
        "process.gate.done", gate=gate), "chief_engineer", [card], extra={"Request-commit": req[:12]})
    old = git.git("rev-parse", f"refs/heads/{main}", cwd=root)
    merge = git.git("commit-tree", "-S", "-p", old, "-p", req, tree, cwd=root, stdin=msg, env=env)
    git.git("tag", "-a", tag, merge, "-m", t("process.gate.tag", gate=gate, who=chief[0]), cwd=root, env=env)
    try:
        git.git("update-ref", f"refs/heads/{main}", merge, old, cwd=root)
    except GitError:
        git.git("tag", "-d", tag, cwd=root)
        raise
    accepted = [e["refs"][0]["id"] for e in lifecycle.announce_accepted(root, tag, chief)]   # D4, stream
    return {"tag": tag, "merge": merge, "next": view.profile.next_gate(view.gates, gate), "accepted": accepted,
            "merged": merge_accepted(root, view, accepted, chief)}


def merge_accepted(root, view, ids: list[str], chief: tuple[str, str]) -> dict[str, str]:
    """The chosen branch of each decision accepted at the gate goes into the work branch, as an approved one's does
    (decisions.merge: merged | skipped | conflict), with its log entry."""
    from ..decisions import merge

    out = {}
    for did in ids:
        if m := merge(root, did, chief):
            option = next(x for x in yamlio.read(Path(root) / "decisions.yaml") if x["id"] == did).get("chosen")
            out[did] = m
            log_commit(root, view.code, "chief_engineer", "decision", t(f"process.decision.merge.{m}", id=did,
                                                                         option=option), cards=[did], chief=True)
    return out


def gate_back(root, gate: str, reason: str, viewed: str | None = None, channel: str = "cli_tty") -> dict:
    """`mekanik gate back <G>` (the chief; TTY): from the stage in progress back to the passed gate `gate` the profile
    allows (`returns`, default@1: G3 → G2; Ö-17, E-26). The chief's reason is his signed comment on O-<G> (the team
    replies), work.yaml goes back to <G> in progress (the stage left is `returned`), the G tag stays and the return
    tag <code>-<G>-back-<n> is added: the gate is asked again and passes as <code>-<G>-<n+1>."""
    from .chief import _signed, ready

    root, head, chief = Path(root), ready(root, viewed), load_config().chief
    refuse(not reason.strip(), "policy.back.reason")
    view, _, results, _ = evaluate(root)
    here = stage(root, view)
    refuse((view.profile.doc.get("returns") or {}).get(here) != gate, "policy.back.not_allowed", stage=here, gate=gate)
    refuse(gate not in passed(root, view.code), "policy.back.not_passed", gate=gate)
    tag, at, txn = f"{view.code}-{gate}-back-{_rounds(root, view.code)[1][gate] + 1}", clock.now(), yamlio.Txn()
    try:
        approval.append(view, approval.record(view, f"O-{gate}", {"gate": gate, "back_from": here}, "comment", chief,
                                              commit=head, reason=reason.strip(), channel=channel), txn)
        p = (doc := yamlio.read(root / "work.yaml"))["process"]
        old = p["gate_status"].get(gate, {})
        p["stage"], p["gate_status"][here] = gate, {**p["gate_status"].get(here, {}), "status": "returned"}
        p["gate_status"][gate] = {**old, "status": "in_progress", "started_at": at, "returns": [
            *old.get("returns", []), {"at": at, "from": here, "reason": reason.strip(), "tag": tag}]}
        txn.write(root / "work.yaml", doc)
    except BaseException:
        txn.rollback()
        raise
    sha = _signed(root, view, results, txn, t("policy.back.title", gate=gate, stage=here), reason.strip(), f"O-{gate}")
    git.git("tag", "-a", tag, sha, "-m", t("policy.back.tag", gate=gate, stage=here, who=chief[0]), cwd=root,
            env=git.identity_env(*chief))
    return {"gate": gate, "from": here, "tag": tag, "commit": sha}
