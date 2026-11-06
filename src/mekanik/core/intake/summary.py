# SPDX-License-Identifier: AGPL-3.0-or-later
"""Understanding summary (architecture §7.1 step 5; C5): intake/summary.yaml goes to the quality engineer, then to
the chief as the hold card T-01. Its approval is the chief's signed record in approvals.yaml (chief.approve), bound to
the summary's content; the file's own `status` is never trusted for that. INTAKE-01: without a current approval the
G0 gate's precondition fails (warn at G0, the gate item refuses) and design after G0 is blocked; INTAKE-02: no
question with a stop category was defaulted, and no more "now" questions than the limit."""

from __future__ import annotations

from pathlib import Path

from .. import cards as cardmod, quality, yamlio
from ..cards import approval
from ..checks.result import BLOCK, PASS, WARN, Result
from ..errors import GitError
from ..i18n import t
from ..model.schema import validate
from ..model.work import load_work
from ..process import refuse
from ..report import stream
from ..store import git
from . import engine, trees

SUMMARY, CARD = "intake/summary.yaml", "T-01"
FIGURE = f"records/visuals/cards/{CARD}.svg"
METHOD = {"target": "intake", "path": "method"}


def read(root) -> dict | None:
    return yamlio.read(Path(root) / SUMMARY, None)


def content(doc: dict) -> dict:
    """What the approval is bound to: everything but the workflow fields."""
    return {k: v for k, v in doc.items() if k not in ("status", "approval")}


def subject(doc: dict) -> dict:
    return {"intake": approval.digest(content(doc))}


def status(view) -> str:
    """none | draft | submitted | approved | rejected | dropped (approved, then the summary changed)."""
    if (doc := read(view.root)) is None:
        return "none"
    st = approval.state(view, CARD, subject(doc))
    return st if st in ("approved", "rejected", "dropped") else doc.get("status", "draft")


def build(view, p: dict) -> dict:
    """The summary record of a plan (in memory; schema `intake-summary`, status draft)."""
    from .. import stdmap

    m = next((x for x in p["nodes"] if METHOD in (x["node"].get("sets") or ())), None)
    dec = next((d["id"] for d in reversed(view.decisions) if d.get("category") == "manufacturing_method"), None)
    return {"kind": "intake_summary", "schema_version": "1.0", "work": view.code,
            "work_type": view.doc.get("work_type"),
            "analyses": engine.analyses(view.root),
            "questions": [{"tree": x["tree"], "node": x["node"]["id"], "state": x["state"], **(
                {"answer": x["answer"], "source": x["source"]} if x["state"] != "pending" else {})}
                          for x in p["nodes"]],
            "findings": [{"kind": f["kind"], "text": f["text"], **({"basis": f["basis"]} if f.get("basis") else {}),
                          "resolved": False} for f in p["findings"]],
            "requirements": "requirements.yaml",
            "method": {"not_applicable": True} if m is None else {"manufacturing": str(m["answer"]), **(
                {"decision": dec} if dec else {})},
            "packages": view.doc.get("packages") or [], "stdmap": stdmap.counts(stdmap.load(view.root) or []),
            "status": "draft"}


def _current(view) -> dict:
    """The summary of today's answers and data; refused while a question with a stop category is open (C6)."""
    p = engine.plan(view, defaults=True)
    refuse(hold := [x["key"] for x in p["nodes"] if x["state"] == "pending"], "intake.summary.pending",
           ids=", ".join(hold))
    doc = build(view, p)
    refuse("decision" not in doc["method"] and "not_applicable" not in doc["method"], "intake.summary.no_method")
    validate("intake_summary", doc, SUMMARY)
    return doc


def summarize(root, role: str = "project_engineer") -> dict:
    """`mekanik intake summary`: write the draft (stage-end questions take their defaults) and commit it, so the
    quality engineer reviews this version; the commit's log line is its stream line (core.report)."""
    from ..process.step import commit_logged

    root = Path(root)
    view = load_work(root)
    yamlio.write(root / SUMMARY, doc := _current(view))
    files = (SUMMARY, engine.ANSWERS, engine.ANALYSIS, engine.MAP, engine.VISUALS, stream.FILE)
    paths = [str(root / p) for p in files if (root / p).exists()]
    return {"summary": doc, "commit": commit_logged(root, view.code, role, "step", t("intake.summary.title"), t(
        "intake.summary.text", **counts(doc)), paths)}


def counts(doc: dict) -> dict:
    st = [q["state"] for q in doc["questions"]]
    return {**{k: st.count(k) for k in ("answered", "derived", "defaulted")}, "findings": len(doc["findings"]),
            "items": doc["stdmap"]["items"], "paid": doc["stdmap"]["paid_items"],
            "unverified": doc["stdmap"].get("unverified", 0)}


def _reviewed(root: Path, rep: dict, doc: dict) -> bool:
    try:
        old = yamlio.load(git.git("show", f"{rep['commit']}:./{SUMMARY}", cwd=root))
    except GitError:
        return False
    return content(old or {}) == content(doc)


def submit(root, role: str = "project_engineer") -> dict:
    """`mekanik intake submit`: the reviewed, current summary becomes the hold card T-01 for the chief (G-11)."""
    from ..process.gates import quality_card
    from ..process.step import commit_logged, text_svg

    root = Path(root)
    view, doc = load_work(root), read(root)
    refuse(doc is None, "intake.submit.none")
    refuse(content(doc) != content(now := _current(view)), "intake.submit.stale")
    path, rep = quality.require_clear(root, t("intake.review"))
    refuse(not _reviewed(root, rep, doc), "intake.submit.not_reviewed", report=rep["id"])
    c, txn = counts(now), yamlio.Txn()
    card = {"id": CARD, "key": "intake:summary", "work": view.code, "generated": False, "level": "hold",
            "type": "intake_summary", "triggers": ["intake"], "title": t("intake.card.title", code=view.code),
            "subject": subject(now), "status": "open", "opened_by": role,
            "question": t("intake.card.question", code=view.code), "explain": t("intake.card.explain"),
            "proposal": {"choice": t("intake.card.approve"), "rationale": t("intake.card.rationale", **c)},
            "if_approved": t("intake.card.if_approved", gate=view.gates[0]),
            "if_rejected": t("intake.card.if_rejected"),
            "recorded_as": t("intake.card.recorded_as"),
            "visuals": [{"kind": "model_view", "id": t("intake.figure.title"), "path": FIGURE}],
            **quality_card(root, path, rep, summary=c)}
    rows = [(t(f"intake.figure.{k}"), str(v)) for k, v in c.items()] + [
        (t("intake.figure.method"), now["method"].get("manufacturing") or "—"), (t("intake.figure.review"), rep["id"])]
    try:
        txn.write(root / SUMMARY, {**now, "status": "submitted"})
        txn.write_text(root / FIGURE, text_svg(t("intake.figure.title"), rows))
        validate("card", cdoc := cardmod.to_file(card), f"cards/{CARD}.yaml")
        txn.write(root / "cards" / f"{CARD}.yaml", cdoc)
        sha = commit_logged(root, view.code, role, "step", t("intake.stream.submitted", id=CARD, code=view.code), t(
            "intake.summary.text", **c), [*map(str, txn.paths), str(root / quality.FOLDER)], [CARD])
    except BaseException:
        txn.rollback()
        raise
    return {"card": CARD, "commit": sha}


def check(view, model=None) -> list[Result]:
    """INTAKE-01 and INTAKE-02. A work past G0 without any summary predates intake (migrated): no result."""
    first, doc = view.gates[0], read(view.root)
    pre, at_first = {"precondition": first}, view.stage == first
    if doc is None:
        return [Result("intake", "INTAKE-01", WARN, "intake.check.none", {"gate": first}, "summary", extra=pre)
                ] if at_first else []
    st = status(view)
    out = [Result("intake", "INTAKE-01", PASS if st == "approved" else WARN if at_first else BLOCK,
                  f"intake.check.{st}", {"gate": first, "id": CARD}, "summary", extra=pre)]
    holds = {(tr["id"], n["id"]) for tr in trees.active(view) for n in trees.walk(tr["nodes"])
             if n.get("stop_category")}
    bad = [f"{q['tree']}/{q['node']}" for q in doc.get("questions") or () if (q["tree"], q["node"]) in holds
           and q["state"] in ("defaulted", "skipped")]
    out.append(Result("intake", "INTAKE-02", BLOCK if bad else PASS, "intake.check.hold_defaulted" if bad else
                      "intake.check.hold_ok", {"ids": ", ".join(bad)}, "questions"))
    if (n := sum(e.get("asked") == "now" for e in engine.records(view.root).values())) > (lim := engine.max_now()):
        out.append(Result("intake", "INTAKE-02", WARN, "intake.check.too_many", {"n": n, "limit": lim}, "now"))
    return out

