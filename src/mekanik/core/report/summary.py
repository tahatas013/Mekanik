# SPDX-License-Identifier: AGPL-3.0-or-later
"""Day-end summary (architecture §9.3): records/summaries/YYYY-MM-DD.md in four sections — decisions made, pending,
risks, agent use; an empty section says "none" (E4). Made from the day's stream events and the work's state now
(cards, check results, calc records, the last quality review, requirements, standard items, agent runs). Its stream
line (daily_summary) goes into the same team commit. The panel calls `build` for the draft and `write` at the set
time (config daily_summary.time) or when asked."""

from __future__ import annotations

from pathlib import Path

from mekanik.config import load_config, state_dir

from .. import clock, quality, yamlio
from ..cards import OPEN
from ..checks.result import BLOCK, WARN
from ..evidence import calc
from ..i18n import num, t
from ..store import git
from . import stream

FOLDER = "records/summaries"
SECTIONS = ("decisions", "pending", "risks", "agents")
DECIDED = ("decision", "provisional_decision")   # the chief's approvals come as `decision` lines (process.step)
RISK_CARDS = ("consistency", "basis_changed")


def _wait(stamp: str | None) -> str:
    m = clock.minutes_since(stamp) if stamp else None
    return "—" if m is None else t("report.summary.wait", h=m // 60, m=m % 60)


def build(root, day: str | None = None, state: tuple | None = None) -> dict[str, list[str]]:
    """{section: [lines]} of `day` (default today). `state` is process.step.evaluate's (view, model, results, cards),
    passed when the caller has it (it builds the model)."""
    from ..process.step import evaluate   # process imports this package

    root, day = Path(root), day or clock.today()
    view, _, results, cards = state or evaluate(root)
    out: dict[str, list[str]] = {k: [] for k in SECTIONS}
    for e in (e for e in stream.read(root) if str(e.get("at", ""))[:10] == day):
        args = {"time": e["at"][11:16], "role": t(f"store.log.role.{e.get('role', 'system')}"), "line": e["line"]}
        if e["type"] == "provisional_decision":
            out["decisions"].append(t("report.summary.provisional", until=e.get("objection_until", "—"), **args))
        elif e["type"] in DECIDED:
            out["decisions"].append(t("report.summary.decision", **args))
        elif e["type"] == "question_batch":
            out["pending"].append(t("report.summary.batch", **args))
    for c in cards:
        if c.get("status") == "open" and c.get("level") == "hold":
            out["pending"].append(t("report.summary.hold", id=c["id"], title=c.get("title", ""),
                                    wait=_wait(c.get("opened_at"))))
        elif c.get("status") == "awaiting_reply":
            out["pending"].append(t("report.summary.reply", id=c["id"], title=c.get("title", "")))
    out["risks"] = _risks(root, view, results, cards)
    out["agents"] = _agents(view.code, day)
    return out


def _risks(root: Path, view, results, cards) -> list[str]:
    label = {BLOCK: t("status.block"), WARN: t("status.warn")}
    out = [t("report.summary.result", status=label[r.status], rule=r.rule, ref=r.ref or "—", reason=r.reason)
           for r in results if r.status in label]
    for cid, rec in calc.recorded(root).items():
        if bad := [r["name"] for r in rec.get("results") or [] if r.get("status") == "unreliable"]:
            out.append(t("report.summary.calc", id=cid, name=", ".join(bad), why=t("report.summary.unreliable")))
        if (v := rec.get("validity") or {}).get("in_domain") is False:
            out.append(t("report.summary.calc", id=cid, name=rec.get("title", cid), why=t(
                "report.summary.out_of_domain", names=", ".join(v.get("out_of_domain") or []) or "—")))
    out += [t("report.summary.card", id=c["id"], title=c.get("title", "")) for c in cards
            if c.get("type") in RISK_CARDS and c.get("status") in OPEN]
    for path, rep in quality.reports(root)[-1:]:   # the last review
        for f in (f for f in rep.get("findings") or [] if f.get("status") == "open"):
            out.append(t("report.summary.finding", report=path.name, no=f["no"], location=f["location"],
                         problem=f["problem"], severity=t(f"report.summary.severity.{f['severity']}")))
    out += [t("report.summary.requirement", id=r["id"], text=r.get("text", "")) for r in view.requirements
            if r.get("kind") == "mandatory" and (r.get("evaluation") or {}).get("status") == "awaiting_evidence"]
    items = yamlio.read(root / "stdmap.yaml", []) or []
    out += [t("report.summary.standard", id=i.get("id", "—"), title=i.get("title", ""))
            for i in (items.get("items") or [] if isinstance(items, dict) else items)
            if isinstance(i, dict) and i.get("verification_status") == "unverified"]
    return out


def _agents(code: str, day: str) -> list[str]:
    runs = [r for r in (yamlio.read(p, {}) for p in sorted((state_dir() / "runs").glob("run-*.json")))
            if isinstance(r, dict) and r.get("work") == code and str(r.get("started_at", ""))[:10] == day]
    if not runs:
        return []
    use = [r.get("usage") or {} for r in runs]
    cost = sum(u.get("estimated_cost_usd") or 0 for u in use)
    return [t("report.summary.agents", n=len(runs), turns=sum(u.get("turns") or 0 for u in use)) + (
        " · " + t("report.summary.cost", cost=num(cost, 2)) if cost else "")]


def render(code: str, day: str, sections: dict[str, list[str]], events: int) -> str:
    lines = [t("report.summary.title", code=code, day=day), "", t("report.summary.made_at", at=clock.now(),
                                                                    events=events)]
    for k in SECTIONS:
        lines += ["", f"## {t('report.summary.section.' + k)}", ""]
        lines += [f"- {x}" for x in sections[k]] or [t("report.summary.none")]
    return "\n".join(lines) + "\n"


def write(root, day: str | None = None, state: tuple | None = None, commit: bool = True) -> dict:
    """records/summaries/<day>.md and its stream line, in one team commit when `commit` (not on the main line);
    → {path, sections, event, commit}."""
    from ..process import refuse
    from ..process.step import evaluate

    root, day = Path(root), day or clock.today()
    branch = git.branch(root) if commit else ""
    refuse(branch.endswith("/main"), "process.step.on_main", branch=branch)
    sections = build(root, day, state := state or evaluate(root))
    n = sum(str(e.get("at", ""))[:10] == day for e in stream.read(root))
    yamlio.write_text(path := root / FOLDER / f"{day}.md", render(state[0].code, day, sections, n))
    ev = stream.emit(root, "daily_summary", line=t("report.summary.line", day=day, decisions=len(sections[
        "decisions"]), pending=len(sections["pending"]), risks=len(sections["risks"])), refs=[{
            "kind": "document", "id": path.name, "path": f"{FOLDER}/{path.name}"}])
    sha = git.commit(root, git.message(t("report.summary.commit", day=day), None, "system"), [
        str(path), str(root / stream.FILE)], load_config().team) if commit else None
    return {"path": path, "sections": sections, "event": ev, "commit": sha}
