# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage measures (architecture §8.2, D5) and the threshold suggestion (D6). Sources: decisions.yaml, the cards and
approvals.yaml; no record of their own. When a category's revert rate over the last `revert_window` provisional
decisions is above `revert_rate_threshold`, the core suggests (a witness card) putting it on the stop list. The
system never changes the config itself: the chief does (§8.2), and the eight fixed categories never leave it."""

from __future__ import annotations

from datetime import datetime

from ..i18n import t
from . import WITNESS, number, stop_categories


def _at(stamp: str | None) -> datetime | None:
    return datetime.fromisoformat(stamp) if stamp else None


def revert_rates(view) -> dict[str, dict]:
    """Category → {n, reverted [ids], rate} over its last `revert_window` provisional decisions (by opening)."""
    window, by = int(number("revert_window")), {}
    prov = (d for d in view.decisions if d.get("mode") == "provisional")
    for d in sorted(prov, key=lambda d: d.get("opened_at") or ""):
        by.setdefault(d.get("category") or "other", []).append(d)
    out = {}
    for cat, ds in by.items():
        rev = [d["id"] for d in ds[-window:] if d.get("status") == "reverted"]
        out[cat] = {"n": len(ds[-window:]), "reverted": rev, "rate": len(rev) / len(ds[-window:])}
    return out


def stage(view, gate: str, cards: list[dict]) -> dict:
    """D5: the measures of the stage that ends at `gate` (since the gate was started; table of §8.2)."""
    since = _at((view.doc["process"]["gate_status"].get(gate) or {}).get("started_at") or view.doc.get("opened_at"))

    def inside(stamp) -> bool:
        return (x := _at(stamp)) is not None and (since is None or x >= since)

    asked = [c for c in cards if c.get("level") == "hold" and c.get("type") != "gate" and inside(c.get("opened_at"))]
    answers = {}
    for c in asked:
        if first := next((r["at"] for r in view.approvals if r.get("card") == c["id"] and r.get("action") in (
                "approve", "reject")), None):
            answers[c["id"]] = round((_at(first) - _at(c["opened_at"])).total_seconds() / 60)
    return {"gate": gate, "questions_asked": len(asked), "questions_limit": int(number("max_questions_per_stage")),
            "provisional_made": sum(d.get("mode") == "provisional" and inside(d.get("opened_at"))
                                    for d in view.decisions),
            "provisional_reverted": sum(any(h.get("event") == "reverted" and inside(h.get("at"))
                                            for h in d.get("history") or []) for d in view.decisions),
            "revert_rate": {k: round(v["rate"], 3) for k, v in sorted(revert_rates(view).items())},
            "time_to_answer": answers}


def line(m: dict) -> str:
    rates = ", ".join(f"{k} {v:.0%}" for k, v in m["revert_rate"].items()) or "—"
    return t("policy.metrics.line", **{**m, "rates": rates, "over": t("policy.metrics.over") if m[
        "questions_asked"] > m["questions_limit"] else ""})


def suggestions(view, results=None) -> list[dict]:
    """D6 (card maker): a category above the threshold and not yet on the stop list → `policy:<category>`."""
    limit, stops, out = number("revert_rate_threshold"), stop_categories(), []
    for cat, r in sorted(revert_rates(view).items()):
        if cat in stops or r["rate"] <= limit:
            continue
        names = sorted({v["name"] for d in view.decisions if d["id"] in r["reverted"] for o in d.get("options") or []
                        for v in o.get("values") or []})
        kw = {"category": cat, "rate": f"{r['rate']:.0%}", "n": r["n"], "limit": f"{limit:.0%}",
              "ids": ", ".join(r["reverted"]), "window": int(number("revert_window"))}
        out.append({"key": f"policy:{cat}", "type": "policy_suggestion", "level": WITNESS, "generated": True,
                    "opened_by": "system", "triggers": ["policy.revert_rate"], "values": kw,
                    "subject": {"policy": cat, "reverted": r["reverted"], **({"params": names} if names else {})},
                    **{f: t(f"policy.suggest.{f}", **kw) for f in ("title", "question", "explain", "if_approved",
                                                                  "if_rejected", "recorded_as")},
                    "proposal": {"choice": t("policy.suggest.choice", **kw),
                                 "rationale": t("policy.suggest.rationale", **kw)}})
    return out
