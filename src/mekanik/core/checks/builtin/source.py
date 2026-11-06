# SPDX-License-Identifier: AGPL-3.0-or-later
"""SOURCE-01: unsourced value, a structural rule; block at every stage (old `kontroller/kaynaksiz.py`).

One result per parameter in params.yaml and per value a package reports through `sourced_values`."""

from __future__ import annotations

from mekanik.plugins import registry

from ...i18n import num
from ..result import BLOCK, PASS, Result

RULE = "SOURCE-01"


def run(view, model=None) -> list[Result]:
    out = []
    for p in view.params.values():
        args = {"name": p.name, "value": num(p.value), "unit": p.unit, "source": p.source}
        if not p.source:
            out.append(Result("source", RULE, BLOCK, "checks.source.missing", args, p.name, p.value))
        elif p.value is None and p.source != "assumption":
            out.append(Result("source", RULE, BLOCK, "checks.source.no_value", args, p.name))
        else:
            out.append(Result("source", RULE, PASS, "checks.source.ok", args, p.name, p.value))
    for v in registry().collect("sourced_values", view):
        args = {"name": v.ref, "value": num(v.value), "unit": v.unit, "source": v.source}
        status, msg = (PASS, "checks.source.ok") if v.source else (BLOCK, "checks.source.missing")
        out.append(Result("source", RULE, status, msg, args, v.ref, v.value))
    return out or [Result("source", RULE, PASS, "checks.source.none")]
