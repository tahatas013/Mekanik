# SPDX-License-Identifier: AGPL-3.0-or-later
"""Question policy (architecture §8, handbook §7): what stops (hold), what goes on as a provisional decision, what is
only reported (witness). Rules decide, not the model's opinion: the category the role writes and the rule-based
classifier both run, and the stricter one holds. The stop list is the schema's ten categories (common#stop_category:
the eight of the fixed decision and the two of T-23) plus what the workshop config adds; it never shrinks.

The classifier (§8.1) looks at the values a decision or card is about: a main dimension (marked `main_dimension` in
params.yaml or named by a requirement criterion), a cost-critical value, an option whose model definition names a
`material` or `manufacturing` profile; on a card also a deviation (its `deviation` trigger, or a check result that is
not a pass: accepting a value outside a rule limit is a deviation, KM-27). An assumed safety-critical value on a card
stops too (stricter than the eight; the phase-1 level of those cards is kept). The numbers come from stdlib/policy
(T-06) unless the workshop config's `policy` gives them."""

from __future__ import annotations

import json
from functools import cache

from mekanik.config import load_config

from .. import data, yamlio

HOLD, PROVISIONAL, WITNESS = "hold", "provisional", "witness"
ORDER = (WITNESS, PROVISIONAL, HOLD)
DECISION_TYPES = ("decision", "provisional_decision")
PROFILE_KEYS = {"material": "material", "manufacturing": "manufacturing_method"}


@cache
def _stdlib() -> dict:
    return yamlio.read(data.stdlib("policy", "default.yaml"), {})


@cache
def fixed_stops() -> tuple[str, ...]:
    """The schema's stop categories: always hold, whatever the config says."""
    doc = json.loads(data.schemas("common.schema.json").read_text(encoding="utf-8"))
    return tuple(doc["$defs"]["stop_category"]["enum"])


def _config() -> dict:
    return load_config().doc.get("policy") or {}


def stop_categories() -> tuple[str, ...]:
    """The schema's ten and the config's additions: the config can extend the list, never narrow it."""
    return (*fixed_stops(), *(c for c in _config().get("stop_categories") or [] if c not in fixed_stops()))


def number(name: str) -> float:
    """A policy number (revert_window, revert_rate_threshold, max_open_provisional, max_questions_per_stage): the
    workshop config's, else the stdlib's (T-06, source decision)."""
    v = _config().get(name)
    v = _stdlib()["numbers"][name] if v is None else v
    return v["value"] if isinstance(v, dict) else v


def main_dimensions(view) -> set[str]:
    """Params marked by the chief (params.yaml main_dimension) and the measures of requirement criteria (§8.1)."""
    raw = yamlio.read(view.root / "params.yaml", {}) or {}
    marked = {n for n, q in raw.items() if isinstance(q, dict) and q.get("main_dimension")}
    return marked | {m for r in view.requirements if (m := (r.get("criterion") or {}).get("measure"))}


def _param_category(view, names) -> str | None:
    if set(names) & main_dimensions(view):
        return "main_dimensions"
    return "cost_impact" if any((p := view.params.get(n)) and p.critical == "cost" for n in names) else None


def decision_category(view, category: str | None, options: list[dict]) -> str | None:
    """The stop category of a decision (options in record form), or None: it may go on as a provisional one."""
    if category in stop_categories():
        return category
    if found := _param_category(view, {v["name"] for o in options for v in o.get("values") or []}):
        return found
    keys = {k for o in options for k in (o.get("model_definition") or {})}
    return next((c for k, c in PROFILE_KEYS.items() if k in keys), None)


def _failed(card: dict) -> bool:
    return "deviation" in (card.get("triggers") or []) or any(
        isinstance(c, dict) and c.get("result") in ("warn", "block") for c in card.get("checks") or [])


def classify_card(view, card: dict) -> tuple[str, str | None]:
    """(level, stop category) of a card. A card opened by hand keeps its own level when that is stricter."""
    typ, subj = card.get("type"), card.get("subject") or {}
    if typ in _stdlib()["hold_types"]:
        return HOLD, card.get("stop_category")
    if typ in _stdlib()["witness_types"]:
        return WITNESS, None
    if typ in DECISION_TYPES and (d := next((x for x in view.decisions if x.get("id") == subj.get("decision")),
                                            None)):
        cat = decision_category(view, d.get("category"), d.get("options") or [])
        return (HOLD if cat or d.get("mode") == HOLD else PROVISIONAL), cat or card.get("stop_category")
    names = subj.get("params") or []
    cat = card.get("stop_category") or ("deviation_from_standard" if _failed(card) else _param_category(view, names))
    safety = any((p := view.params.get(n)) and p.critical == "safety" for n in names)
    got = HOLD if cat or safety else PROVISIONAL
    if not card.get("generated") and card.get("level") in ORDER:
        got = max(got, card["level"], key=ORDER.index)
    return got, cat


def level(view, card: dict) -> str:
    """`hold` | `provisional` | `witness` of a card (contract of plan §4)."""
    return classify_card(view, card)[0]
