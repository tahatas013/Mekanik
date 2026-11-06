# SPDX-License-Identifier: AGPL-3.0-or-later
"""Runs the registered checks (old `kontroller.calistir`). Checks are pure functions of a read-only view."""

from __future__ import annotations

from mekanik.plugins import CheckSpec, registry

from .result import WARN, Result


def run(view, model=None, checks: list[CheckSpec] | None = None) -> list[Result]:
    """Run checks in order; `after_cards` checks run last with the cards made from the other results.

    `checks` replaces the registered list (regression uses it with fake checks)."""
    specs = sorted(checks if checks is not None else registry().checks, key=lambda c: c.order)
    out: list[Result] = [Result("schema", "SCHEMA-01", WARN, "schema.warning", {"text": w}) for w in view.warnings]
    for c in specs:
        if not c.after_cards:
            out.extend(c.run(view, model))
    late = [c for c in specs if c.after_cards]
    if late:
        from mekanik.core.cards import generate

        cards = generate(view, out)
        for c in late:
            out.extend(c.run(view, model, cards=cards))
    return out
