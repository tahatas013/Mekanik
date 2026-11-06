# SPDX-License-Identifier: AGPL-3.0-or-later
"""CARD-01 (card standard, Ö-10) and DECISION-02 (decision card names its effect on requirements, B8): both were
parts of the old `kartlar.eksikler`; they run with the cards made from the other results."""

from __future__ import annotations

from ..result import BLOCK, PASS, Result

EFFECTS = "requirement_effects"


def standard(view, model=None, cards: list[dict] | None = None, opened_only: bool = True) -> list[Result]:
    """Open cards with missing text or visual. The check run covers cards already opened (on disk); a step calls it
    with `opened_only=False` after the visuals are attached, before it opens new cards (old akis.adim)."""
    from ...cards import missing_fields

    out = []
    for k in cards if cards is not None else view.cards:
        if opened_only and not k.get("opened_at"):
            continue
        miss = [f for f in missing_fields(k) if f != EFFECTS]
        out.append(Result("card_standard", "CARD-01", BLOCK if miss else PASS,
                          "checks.card_standard.missing" if miss else "checks.card_standard.ok",
                          {"id": k["id"], "fields": ", ".join(miss)}, k["id"], extra={"missing": miss}))
    return out or [Result("card_standard", "CARD-01", PASS, "checks.card_standard.none")]


def effects(view, model=None, cards: list[dict] | None = None) -> list[Result]:
    out = []
    if view.requirements:
        for k in cards if cards is not None else view.cards:
            if k.get("type") in ("decision", "provisional_decision") and k.get("status") in ("open", "awaiting_reply"):
                ok = bool(k.get(EFFECTS))
                out.append(Result("decision_effects", "DECISION-02", PASS if ok else BLOCK,
                                  "checks.decision_effects.ok" if ok else "checks.decision_effects.missing",
                                  {"id": k["id"]}, k["id"]))
    return out or [Result("decision_effects", "DECISION-02", PASS, "checks.decision_effects.none")]
