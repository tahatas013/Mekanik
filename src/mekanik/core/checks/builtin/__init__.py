# SPDX-License-Identifier: AGPL-3.0-or-later
"""Core checks (architecture §4.7). Order: SOURCE-01 first, UNCERT-01 after the package interface checks,
the card-based checks last (they run with the cards made from the other results)."""

from mekanik.plugins import CheckSpec

from . import approval, cards, source, uncertainty

CHECKS = [
    CheckSpec("source", source.run, ("SOURCE-01",), order=10),
    CheckSpec("uncertainty", uncertainty.run, ("UNCERT-01",), order=40),
    CheckSpec("approval_signature", approval.signature, ("APPROVAL-02",), order=95),
    CheckSpec("approval_state", approval.state, ("APPROVAL-01",), after_cards=True, order=90),
    CheckSpec("decision_effects", cards.effects, ("DECISION-02",), after_cards=True, order=96),
    CheckSpec("card_standard", cards.standard, ("CARD-01",), after_cards=True, order=97),
]
# KM-19 (wave 2.2): judged from the history, so its regression case is a git work (tests/flow); core.builtin adds it
MAIN_DIMENSION = CheckSpec("main_dimension", approval.main_dimension, ("MAINDIM-01",), order=94)
