# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standard map (architecture §10.8; F8): stdmap.yaml is a list of `standard-item` records (SM-nn), proposed from the
library (stdlib/items/** and packages' items/, schema standard-item with library: true) by their `applies_to`
expressions over the intake answers, or added by hand (customer specification). A tick needs evidence and an
existing quality review (schema + STDMAP-01). A paid standard whose text is not in hand shows as unverified (or as
its open equivalent's secondary source) whatever its record says, and no number is taken from it."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mekanik.plugins import CheckSpec

from .. import clock, quality, yamlio
from ..checks import rules
from ..checks.result import BLOCK, PASS, WARN, Result
from ..errors import SchemaError
from ..i18n import t
from ..model.schema import validate
from ..process import refuse
from ..report.stream import emit

FILE = "stdmap.yaml"
LEVELS = ("unverified", "secondary_source", "text_in_hand")


def library() -> dict[str, dict]:
    from ..intake import trees

    items = trees.load("items", "standard_item")
    bad = [k for k, v in items.items() if not v.get("library")]
    refuse(bad, "stdmap.library.not_template", ids=", ".join(bad))
    return items


def load(root) -> list[dict] | None:
    """The work's map; None when there is none. A record against the schema raises SchemaError (F8)."""
    items = yamlio.read(Path(root) / FILE, None)
    if items is not None and not isinstance(items, list):
        raise SchemaError(t("schema.not_list", where=FILE))
    for i, x in enumerate(items or ()):
        validate("standard_item", x, f"{FILE}[{i}]")
    return items


def save(root, items: list[dict]) -> None:
    for i, x in enumerate(items):
        validate("standard_item", x, f"{FILE}[{i}]")
    yamlio.write(Path(root) / FILE, items)


def priority(item: dict) -> int:
    """Source priority (§10.8): 1 regulation, 2 customer spec, 3 open technical source, 4 guideline, 5 paid."""
    return {"regulation": 1, "customer_spec": 2}.get(item["type"]) or (5 if item["access"] == "paid" else 4 if item[
        "type"] == "guideline" else 3)


def mandatory(item: dict) -> bool:
    return item.get("mandatory", item["type"] in ("regulation", "customer_spec"))


def effective(item: dict) -> str:
    """The verification status shown: a paid text not bought is at most its open equivalent's secondary source."""
    st = item["verification_status"]
    if item["access"] != "paid" or (item.get("procurement") or {}).get("approved"):
        return st
    cap = "secondary_source" if (item.get("open_equivalent") or {}).get("found") else "unverified"
    return min(st, cap, key=LEVELS.index)


def counts(items: list[dict]) -> dict:
    return {"items": len(items), "paid_items": sum(i["access"] == "paid" for i in items),
            "unverified": sum(effective(i) == "unverified" for i in items)}


def rows(root) -> list[dict]:
    """The panel's table: each item with its shown status, priority and whether it is mandatory."""
    return [{**i, "shown_status": effective(i), "priority": priority(i), "mandatory": mandatory(i)}
            for i in sorted(load(root) or [], key=priority)]


def _next(items: list[dict]) -> int:
    return 1 + max((int(i["id"][3:]) for i in items), default=0)


def propose(view) -> list[dict]:
    """Library items whose `applies_to` holds for the work (answers with stage-end defaults) and not yet mapped."""
    from ..intake import engine, expr

    nodes = engine.plan(view, defaults=True)["nodes"]
    answers: dict = {}
    for x in nodes:
        if x["state"] != "pending":
            answers.setdefault(x["node"]["id"], x["answer"])
    ctx, have = engine.context(view, answers), {i.get("from_library") for i in load(view.root) or ()}
    return [x for k, x in library().items() if k not in have and any(expr.holds(e, ctx) for e in x.get("applies_to")
                                                                    or ())]


def _from_library(lib: dict, code: str, n: int) -> dict:
    keep = {k: v for k, v in lib.items() if k not in ("id", "library", "applies_to")}
    return {**keep, "id": f"SM-{n:02d}", "work": code, "from_library": lib["id"], "priority": priority(lib),
            "mandatory": mandatory(lib), "status": "awaiting_evidence", "evidence": [], "tick": {"checked": False}}


def build(root, role: str = "project_engineer") -> list[str]:
    """`mekanik stdmap build`: add the proposed library items; an empty map is written too (G0 needs a map)."""
    from ..model.work import load_work

    root = Path(root)
    view, items = load_work(root), load(root) or []
    new = [_from_library(x, view.code, _next(items) + i) for i, x in enumerate(propose(view))]
    save(root, items := items + new)
    emit(root, "notice", role=role, line=t("stdmap.stream.built", n=len(new), total=len(items), **counts(items)))
    return [i["id"] for i in new]


def add(root, item: dict, role: str = "project_engineer") -> dict:
    """`mekanik stdmap add`: an item written by hand (e.g. a customer specification clause)."""
    root = Path(root)
    items, code = load(root) or [], yamlio.read(root / "work.yaml")["code"]
    item = {"kind": "standard_item", "schema_version": "1.0", "status": "awaiting_evidence", **item,
            "id": f"SM-{_next(items):02d}", "work": code}
    save(root, [*items, item])
    emit(root, "notice", role=role, line=t("stdmap.stream.added", id=item["id"], title=item["title"]))
    return item


def tick(root, item_id: str, evidence: list[dict], review: str, role: str = "project_engineer") -> dict:
    """`mekanik stdmap tick`: only with evidence and an existing quality review; the item becomes `met`."""
    root, items = Path(root), load(Path(root)) or []
    refuse((item := next((i for i in items if i["id"] == item_id), None)) is None, "stdmap.tick.unknown", id=item_id)
    refuse(not evidence, "stdmap.tick.no_evidence", id=item_id)
    refuse(review not in {r.get("id") for _, r in quality.reports(root)}, "stdmap.tick.no_review", id=item_id,
           review=review)
    item.update(evidence=[*(item.get("evidence") or ()), *evidence], status="met", tick={
        "checked": True, "quality_review": {"kind": "quality_review", "id": review}, "at": clock.now()})
    save(root, items)
    emit(root, "notice", role=role, line=t("stdmap.stream.ticked", id=item_id, title=item["title"]))
    return item


def _problem(item: dict, reviews: set, release: bool) -> str | None:
    tick, crit = item.get("tick") or {}, (item.get("acceptance") or {}).get("criterion") or {}
    if tick.get("checked") and (tick.get("quality_review") or {}).get("id") not in reviews:
        return "unreviewed"
    if effective(item) != item["verification_status"]:
        return "not_in_hand"
    if item["access"] == "paid" and effective(item) == "unverified" and str(crit.get("source", "")).startswith(
            "standard:"):
        return "number_without_text"
    return "unticked" if release and mandatory(item) and not tick.get("checked") else None


def check(view, model=None) -> list[Result]:
    """STDMAP-01: the map exists at the first gate (precondition), ticks are backed, paid texts are not claimed, no
    mandatory item is unticked at the last gate; a regulation read too long ago warns."""
    first, last = view.gates[0], view.gates[-1]
    pre = {"precondition": first}
    try:
        items = load(view.root)
    except SchemaError as e:
        return [Result("stdmap", "STDMAP-01", BLOCK, "stdmap.check.schema", {"error": str(e)}, "stdmap", extra=pre)]
    if items is None:
        return [Result("stdmap", "STDMAP-01", WARN, "stdmap.check.none", {"gate": first}, "stdmap", extra=pre)] if \
            view.stage == first else [Result("stdmap", "STDMAP-01", BLOCK, "stdmap.check.none_release", {
                "gate": last}, "stdmap")] if view.stage == last else []
    out = [Result("stdmap", "STDMAP-01", PASS, "stdmap.check.present", {"n": len(items)}, "stdmap", extra=pre)]
    reviews, days = {r.get("id") for _, r in quality.reports(view.root)}, rules.limit("STDMAP-01", "reading_age_days")
    today = date.fromisoformat(clock.today())
    for i in items:
        why = _problem(i, reviews, view.stage == last)
        out.append(Result("stdmap", "STDMAP-01", BLOCK if why else PASS, f"stdmap.check.{why or 'ok'}", {
            "id": i["id"], "title": i["title"], "shown": effective(i)}, i["id"]))
        if i["type"] == "regulation" and (on := i["citation"].get("read_on")) and (
                today - date.fromisoformat(on)).days > days:
            out.append(Result("stdmap", "STDMAP-01", WARN, "stdmap.check.reading_old", {"id": i["id"], "on": on,
                                                                                         "days": days}, i["id"]))
    return out


CHECKS = [CheckSpec("stdmap", check, ("STDMAP-01",), order=9)]
