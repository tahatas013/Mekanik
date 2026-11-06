# SPDX-License-Identifier: AGPL-3.0-or-later
"""Core card maker (old `kartlar.uret`, domain-free part). The triggers decide what is asked, not the team:
- an assumption that enters an interface record or is marked critical: its own card (`assumption:<param>`);
- an unsourced value: its own card (`unsourced:<param>`);
- the other assumptions: one list per work (V-01, approved row by row);
- an instrument uncertainty that is itself an assumption, used on a critical dimension (`uncertainty:<instrument>`);
- a measured value whose uncertainty does not pass UNCERT-01: re-measure (`measured:<param>`)."""

from __future__ import annotations

from mekanik.plugins import registry

from .texts import fill

LIST_ID = "V-01"


def check_items(results) -> list[dict]:
    """Card `checks` entries from results (rule, result, message)."""
    return [{"rule": r.rule, "result": r.status, "message": r.reason} for r in results]


def _card(key: str, type_: str, subject: dict, triggers: list[str], **kw) -> dict:
    return fill({"key": key, "type": type_, "level": "hold", "subject": subject, "triggers": triggers,
                 "generated": True, "opened_by": "system", **kw})


def criticality(view, name: str, uses: dict | None = None) -> dict | None:
    """Why an assumption is asked on its own: it enters interface records (packages report them), or the team
    marked it safety, cost or interface. None: it goes to the assumption list."""
    uses = registry().param_uses(view) if uses is None else uses
    if uses.get(name):
        return {"uses": sorted(set(uses[name]))}
    p = view.params[name]
    return {"critical": p.critical} if p.critical else None


def make(view, results) -> list[dict]:
    cards, listed = [], []
    uses = registry().param_uses(view)
    for p in view.params.values():
        values = {"name": p.name, "value": p.value, "unit": p.unit, "source": p.source,
                  "description": p.description, "rationale": p.rationale}
        if p.source == "assumption":
            why = criticality(view, p.name, uses)
            if why:
                cards.append(_card(f"assumption:{p.name}", "assumption", {"params": [p.name]},
                                   ["assumption", "critical"], values={**values, **why}))
            else:
                listed.append(p.name)
        elif not p.source:
            cards.append(_card(f"unsourced:{p.name}", "unsourced", {"params": [p.name]}, ["unsourced", "deviation"],
                               values=values))
    if listed:
        cards.append(_card("assumption_list", "assumption_list", {"params": listed, "list": True}, ["assumption"],
                           id=LIST_ID))

    unc = [r for r in results if r.check == "uncertainty" and r.extra.get("param")]
    for inst_id in sorted({r.extra["instrument"] for r in unc}):
        u = view.instruments[inst_id]["uncertainty"]
        if u.get("source") != "assumption":
            continue
        rel = [r for r in unc if r.extra["instrument"] == inst_id]
        triggers = ["assumption"] + (["borderline"] if any(r.extra.get("borderline") for r in rel) else [])
        cards.append(_card(f"uncertainty:{inst_id}", "uncertainty", {"params": sorted({r.extra["param"] for r in rel})},
                           triggers, values={"instrument": inst_id, "uncertainty": u["value"],
                                             "unit": u.get("unit", "-"), "value": u["value"]},
                           checks=check_items(rel)))
    for r in unc:
        if r.failed:
            name = r.extra["param"]
            cards.append(_card(f"measured:{name}", "remeasure", {"params": [name]}, ["uncertainty"],
                               values={"name": name}, checks=check_items([r])))
    return cards
