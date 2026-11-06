# SPDX-License-Identifier: AGPL-3.0-or-later
"""Card makers of mech (old kartlar.uret: fit, flex and deviation cards; kartlar.metinler for their texts).
Cards are dicts as in guide §8.2; the core numbers, files and syncs them. Level: hold (G-31)."""

from __future__ import annotations

from mekanik.core.cards import check_items
from mekanik.core.i18n import num, t

from .fits import fits, flexes, profile, side_names


def _card(key: str, typ: str, title: str, triggers: list, subject: dict, text: str, choice: str, rationale: str,
          **kw) -> dict:
    return {"key": key, "type": typ, "level": "hold", "title": title, "triggers": triggers, "subject": subject,
            "question": t(f"mech.card.{text}.question", **kw), "explain": t(f"mech.card.{text}.explain", **kw),
            "proposal": {"choice": choice, "rationale": rationale},
            "if_approved": t(f"mech.card.{text}.if_approved"), "if_rejected": t(f"mech.card.{text}.if_rejected"),
            "recorded_as": t("mech.card.recorded_as"), "generated": True, "opened_by": "system"}


def fit_cards(view, results: list) -> list[dict]:
    """A fit is asked when its profile is provisional, its task undefined, its limit or a side an assumption, or a
    check failed it."""
    failed = [r for r in results if r.failed]
    prof, out = profile(view), []
    provisional = (view.manufacturing or {}).get("status") != "calibrated"
    for f in fits(view):
        trig = ["provisional_profile"] if provisional else []
        if f["task"] is None:
            trig.append("task_undefined")
        elif f["task"] != "screw_clearance":
            lim = (prof.get("clearance") or {}).get(f["task"]) or {}
            if "assumption" in ((lim.get("lower") or {}).get("source"), (lim.get("upper") or {}).get("source")):
                trig.append("assumption_limit")
        names = side_names(f)
        if any(view.params[a].source in (None, "assumption") for a in names):
            trig.append("assumption_value")
        rel = [r for r in failed if r.ref == f["id"]]
        if rel:
            trig.append("deviation")
        if not trig:
            continue
        task, a, b = t(f"mech.task.{f['task']}") if f["task"] else t("mech.task.none"), *f["parts"]
        why = "; ".join(t(f"mech.card.fit.why.{x}") for x in trig)
        card = _card(f"fit:{f['id']}", "mech:fit", t("mech.card.fit.title", fit=f["id"], task=task, a=a, b=b), trig,
                     {"params": sorted(set(names)), "fit": f["id"]}, "fit",
                     t("mech.card.fit.choice_fix" if rel else "mech.card.fit.choice_ok"),
                     "; ".join(r.reason for r in rel) if rel else t("mech.card.fit.rationale_ok"),
                     fit=f["id"], a=a, b=b, task=task, why=why)
        out.append({**card, "checks": check_items(rel)})
    return out


def flex_cards(view, results: list) -> list[dict]:
    return [_card(f"flex:{e['id']}", "mech:flex", t("mech.card.flex.title", flex=e["id"], part=e.get("part"),
                                                    value=num(e.get("value"))),
                  ["assembly_flex"], {"flex": e["id"]}, "flex", t("mech.card.flex.choice"),
                  t("mech.card.flex.rationale"), part=e.get("part"), value=num(e.get("value")))
            for e in flexes(view)]


def deviation_cards(view, results: list) -> list[dict]:
    """A failed interference or unregistered-fit result with a ref (no ref: the model was not loaded)."""
    out = []
    for r in results:
        if r.failed and r.ref and r.check in ("mech.unregistered_fit", "mech.interference"):
            out.append({**_card(f"{r.check.removeprefix('mech.')}:{r.ref}", "deviation", r.reason, ["deviation"], {},
                                "deviation", t("mech.card.deviation.choice"), t("mech.card.deviation.rationale"),
                                checks=r.reason), "checks": check_items([r])})
    return out


MAKERS = [fit_cards, flex_cards, deviation_cards]
