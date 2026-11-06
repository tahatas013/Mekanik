# SPDX-License-Identifier: AGPL-3.0-or-later
"""Plain-language text of the core card types (old `kartlar.metinler`). Every card is written for an engineer who
does not follow the work. The words live in the catalog (`cards.<type>.<field>`); package cards bring their own."""

from __future__ import annotations

from ..i18n import num, t

FIELDS = ("title", "question", "explain", "if_approved", "if_rejected")


def _messages(card: dict) -> str:
    return "; ".join(c["message"] if isinstance(c, dict) else str(c) for c in card.get("checks") or [])


def _vars(card: dict) -> dict:
    v = dict(card.get("values") or {})
    if "unit" in v:
        v["value_text"] = f"{num(v['value'])} {v['unit']}" if v.get("value") is not None else t("cards.no_value")
    if v.get("uses"):
        v["why"] = t("cards.critical.uses", refs=", ".join(v["uses"]))
    elif v.get("critical"):
        v["why"] = t(f"cards.critical.{v['critical']}")
    v["desc"] = f"{v['description']} " if v.get("description") else ""
    if "uncertainty" in v:
        v["u"] = num(v["uncertainty"])
    return {**v, "checks": _messages(card), "count": len((card.get("subject") or {}).get("params") or [])}


def rationale(card: dict, kw: dict) -> str:
    typ = card["type"]
    if typ == "assumption":
        return kw.get("rationale") or ""
    if typ == "unsourced":
        return kw.get("rationale") or t("cards.unsourced.rationale")
    if typ in ("uncertainty", "remeasure"):
        return kw["checks"]
    return t(f"cards.{typ}.rationale", **kw)


def fill(card: dict) -> dict:
    """Fill the empty text fields of a core card from its type and values."""
    kw = _vars(card)
    base = f"cards.{card['type']}"
    for f in FIELDS:
        card.setdefault(f, t(f"{base}.{f}", **kw))
    card.setdefault("proposal", {"choice": t(f"{base}.choice", **kw), "rationale": rationale(card, kw)})
    return card
