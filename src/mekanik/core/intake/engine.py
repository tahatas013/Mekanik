# SPDX-License-Identifier: AGPL-3.0-or-later
"""Question tree engine (architecture §7.1 step 3; C1–C3, C6). A node is answered (intake/answers.yaml), derived
from the data (derive_from: analysis results, work.yaml, inputs, risk answers, other answers; source `derived`),
defaulted (stage end; never a node with a stop category) or pending. Pending "now" questions are capped per stage
(policy.max_questions_per_stage, else INTAKE-02 max_now; T-06), stop categories first; the rest wait for the stage
end batch. Questions and derivations go to the stream (core.report.stream.emit)."""

from __future__ import annotations

from pathlib import Path

from mekanik.config import load_config

from .. import clock, yamlio
from ..checks import rules
from ..i18n import lang, t
from ..model.schema import validate
from ..model.work import load_work
from ..process import refuse
from ..report.stream import emit
from . import expr, trees

ANSWERS, ANALYSIS, MAP = "intake/answers.yaml", "intake/analysis.yaml", "stdmap.yaml"
VISUALS = "records/visuals/intake"
TYPES = ("regulation", "customer_spec", "standard", "guideline", "literature")
PASSES = 4   # source: assumption — passes until answers that refer to other trees settle; not an engineering value


def text(d: dict | None) -> str:
    """A text_i18n field in the UI language (Turkish when missing)."""
    return (d or {}).get(lang()) or (d or {}).get("tr", "")


def records(root) -> dict:
    return yamlio.read(Path(root) / ANSWERS, {}) or {}


def analyses(root) -> list[dict]:
    """Analyzer results written before the questions (Phase 3 packages write them; cases give them as data)."""
    items = yamlio.read(Path(root) / ANALYSIS, []) or []
    for i, a in enumerate(items):
        validate("intake_summary#/properties/analyses/items", a, f"{ANALYSIS}[{i}]")
    return items


def _analysis(items: list[dict]) -> dict:
    """analysis.<a_b>.<name> and analysis.<a>.<b>.<name> for analyzer `a.b`: the quantity values."""
    out: dict = {}
    for a in items:
        vals, (*head, last) = {r["name"]: r["quantity"]["value"] for r in a["results"]}, a["analyzer"].split(".")
        out[a["analyzer"].replace(".", "_")] = vals
        node = out
        for h in head:
            node = node.setdefault(h, {})
        node[last] = vals
    return out


def context(view, answers: dict | None = None) -> dict:
    exts: dict[str, int] = {}
    for i in view.doc.get("inputs") or ():
        exts[e] = exts.get(e := Path(i["path"]).suffix.lower().lstrip("."), 0) + 1
    smap = yamlio.read(view.root / MAP, None)
    return {"work": view.doc, "work_type": trees.work_types(False).get(view.doc.get("work_type"), {}),
            "analysis": _analysis(analyses(view.root)), "inputs": exts, "answers": answers or {},
            "risk": {r["question_id"]: r["answer"] for r in view.doc.get("risk_answers") or ()},
            "stdmap": {k: sum(x.get("type") == k for x in smap) for k in TYPES} if isinstance(smap, list) else {}}


def max_now() -> int:
    return (load_config().doc.get("policy") or {}).get("max_questions_per_stage") or rules.limit("INTAKE-02", "max_now")


def _visit(tid: str, n: dict, ctx: dict, rec: dict, defaults: bool, out: list) -> None:
    key, e, d = f"{tid}/{n['id']}", rec.get(f"{tid}/{n['id']}") or {}, n.get("derive_from")
    ok = bool(d) and expr.holds(d["expression"], ctx)
    got = (expr.evaluate(d["value"], ctx) if d.get("value") else True) if ok else None
    if "answer" in e:
        state, ans, src = "answered", e["answer"], e.get("source")
    elif ok:
        state, ans, src = "derived", got, "derived"
    elif defaults and not n.get("stop_category"):
        state, ans, src = "defaulted", n["default_if_unanswered"]["value"], n["default_if_unanswered"]["source"]
    else:
        state, ans, src = "pending", None, None
    out.append({"key": key, "tree": tid, "node": n, "state": state, "answer": ans, "source": src, "asked": e.get(
        "asked"), "hold": n.get("stop_category"), "derivable": ok, "derived": got, "bucket": None})
    if state != "pending":
        for c in n.get("children") or ():
            if expr.holds(c["when"], {**ctx, "answer": ans}):
                _visit(tid, c["node"], ctx, rec, defaults, out)


def plan(view, defaults: bool = False) -> dict:
    """Every active node with its state and bucket (now | stage_end), and the findings; nothing is written.
    `defaults`: unanswered nodes take their default (stage end), except those with a stop category (C6)."""
    rec, answers, nodes, ctx = records(view.root), {}, [], {}
    for _ in range(PASSES):
        ctx, nodes = context(view, answers), []
        for tree in trees.active(view):
            for n in tree["nodes"]:
                _visit(tree["id"], n, ctx, rec, defaults, nodes)
        new: dict = {}
        for x in nodes:
            if x["state"] != "pending":
                new.setdefault(x["node"]["id"], x["answer"])
        if new == answers:
            break
        answers = new
    limit, asked = max_now(), [x for x in nodes if x["asked"] == "now"]
    fresh = sorted((x for x in nodes if x["state"] == "pending" and x["asked"] != "now" and x["node"]["urgency"] ==
                    "now"), key=lambda x: not x["hold"])
    for x in nodes:
        x["bucket"] = "stage_end" if x["state"] == "pending" else None
    for x in [*asked, *fresh[:max(0, limit - len(asked))]]:
        x["bucket"] = "now" if x["state"] == "pending" else None
    from .findings import find

    return {"nodes": nodes, "limit": limit, "asked_now": len(asked), "findings": find(view, nodes, ctx),
            "now": [x["key"] for x in nodes if x["bucket"] == "now"],
            "stage_end": [x["key"] for x in nodes if x["bucket"] == "stage_end"]}


def _figure(root: Path, x: dict) -> dict:
    """The question's figure (the tree's generator draws it from the model in Phase 3; here its text and default)."""
    from ..process.step import text_svg

    n, d = x["node"], x["node"]["default_if_unanswered"]
    rows = [(t("intake.figure.question"), text(n["text"])), (t("intake.figure.why"), text(n["why"])),
            (t("intake.figure.default"), t("intake.figure.hold", cat=x["hold"]) if x["hold"] else f"{d['value']} "
             f"({d['source']})"), (t("intake.figure.generator"), n["visual"]["generator"])]
    yamlio.write_text(root / (rel := f"{VISUALS}/{x['key'].replace('/', '-')}.svg"), text_svg(x["key"], rows))
    return {"kind": "file", "id": n["visual"]["generator"], "path": rel}


def ask(root, role: str = "project_engineer") -> dict:
    """Mark the "now" questions asked and send each to the stream with its why, default and figure; derivations go
    to the stream once per value. → the plan after marking."""
    root, at = Path(root), clock.now()
    view, rec = load_work(root), records(root)
    for x in plan(view)["nodes"]:
        e = rec.get(x["key"]) or {}
        if x["bucket"] == "now" and not e.get("asked"):
            rec[x["key"]] = {**e, "asked": "now", "at": at}
            emit(root, "question", role=role, line=t("intake.stream.question", q=x["key"], text=text(x["node"][
                "text"]), hold=t("intake.stream.hold") if x["hold"] else ""), visuals=[_figure(root, x)])
        elif x["state"] == "derived" and (e.get("asked") != "derived" or e.get("value") != x["answer"]):
            rec[x["key"]] = {"asked": "derived", "value": x["answer"], "at": at}
            emit(root, "notice", role="system", line=t("intake.stream.derived", q=x["key"], value=x["answer"],
                                                        evidence=x["node"]["derive_from"]["evidence"]))
    yamlio.write(root / ANSWERS, rec)
    return plan(view)


def fits(spec: dict, v) -> bool:
    """The answer matches the node's answer spec (choice value, number in range, boolean, non-empty text)."""
    if spec["type"] == "choice":
        return v in [c["value"] for c in spec["choices"]]
    if spec["type"] == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool) and spec.get("min", v) <= v <= spec.get("max", v)
    if spec["type"] == "boolean":
        return isinstance(v, bool)
    return isinstance(v, str) and bool(v.strip())


def answer(root, key: str, value, source: str = "decision", by: str = "chief_engineer", via: str | None = None) -> dict:
    """`mekanik intake answer <tree/node> <value>`: record an answer of an active node. `via="brief"` marks an answer
    given before the question was asked (it does not count as a "now" question)."""
    root = Path(root)
    x = next((x for x in plan(load_work(root))["nodes"] if x["key"] == key), None)
    refuse(x is None, "intake.answer.unknown", q=key)
    refuse(not fits(x["node"]["answer"], value), "intake.answer.invalid", q=key, value=value)
    validate("common#/$defs/source_tag", source, key)
    rec = records(root)
    e = rec.get(key) or {}
    rec[key] = {**{k: v for k, v in e.items() if k != "value"}, "answer": value, "source": source, "by": by,
                "at": clock.now(), "asked": e["asked"] if e.get("asked") in ("now", "stage_end") else via or "brief"}
    yamlio.write(root / ANSWERS, rec)
    emit(root, "notice", role=by, line=t("intake.stream.answered", q=key, value=value, source=source))
    return rec[key]


def choose(root, type_id: str, role: str = "project_engineer") -> str:
    """The work type (step 1); the chief confirms it with the summary. Unknown or uninstalled types are refused."""
    root = Path(root)
    refuse(type_id not in (ok := trees.work_types()), "intake.type.unavailable", id=type_id, ids=", ".join(sorted(ok)))
    yamlio.write(root / "work.yaml", yamlio.read(root / "work.yaml") | {"work_type": type_id})
    emit(root, "notice", role=role, line=t("intake.stream.type", id=type_id, title=text(ok[type_id]["title"])))
    return type_id
