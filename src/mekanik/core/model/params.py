# SPDX-License-Identifier: AGPL-3.0-or-later
"""Work parameters (params.yaml): sourced values, safe formulas (old `veri.py` params part).

A missing source is not a schema error; SOURCE-01 reports it as a block (guide G-25).
"""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from pathlib import Path

from .. import yamlio
from ..errors import SchemaError
from ..i18n import t
from .schema import validate

# Accepted units; anything else is a typo (old BIRIMLER, renamed per guide §2.2).
UNITS = {"mm", "m", "deg", "count", "ratio", "g", "N", "MPa", "%", "g/cm3", "m/s", "-"}
SOURCE_RE = re.compile(r"^(measured:[a-z0-9][a-z0-9_-]*|standard:.+|regulation:.+|customer:.+|manufacturer:.+"
                       r"|literature:.+|decision|derived|assumption)$")


@dataclass
class Param:
    name: str
    value: float | None
    unit: str
    source: str | None
    formula: str | None = None
    note: str = ""
    critical: str | None = None      # safety | cost | interface: an assumption opens a card on its own
    description: str = ""            # what the value is for (card text)
    rationale: str = ""              # why the team chose it (needed for an assumption card)

    @property
    def measured(self) -> bool:
        return bool(self.source and self.source.startswith("measured:"))

    @property
    def instrument(self) -> str | None:
        return self.source.split(":", 1)[1] if self.measured else None


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _parse(formula: str) -> ast.Expression:
    try:
        return ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise SchemaError(t("formula.syntax", formula=formula)) from e


def formula_names(formula: str) -> set[str]:
    return {n.id for n in ast.walk(_parse(formula)) if isinstance(n, ast.Name)}


def formula_eval(formula: str, values: dict[str, float | None]) -> float:
    """Only + − × ÷, numbers, parentheses and parameter names."""

    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return float(n.value)
        if isinstance(n, ast.Name):
            if values.get(n.id) is None:
                raise SchemaError(t("formula.unknown", formula=formula, name=n.id))
            return values[n.id]
        raise SchemaError(t("formula.forbidden", formula=formula))

    return ev(_parse(formula))


def parse_params(doc: dict, where: str = "params.yaml") -> dict[str, Param]:
    validate("params", doc, where)
    out: dict[str, Param] = {}
    for name, k in doc.items():
        here = f"{where}:{name}"
        if k["unit"] not in UNITS:
            raise SchemaError(t("params.unit", where=here, unit=k["unit"], accepted=", ".join(sorted(UNITS))))
        p = Param(name=name, value=None if k.get("value") is None else float(k["value"]), unit=k["unit"],
                  source=k.get("source"), formula=k.get("formula"), note=k.get("note") or "",
                  critical=k.get("critical"), description=k.get("description") or "", rationale=k.get("rationale") or "")
        if p.source == "derived" and not formula_names(p.formula):
            raise SchemaError(t("params.derived_constant", where=here))
        out[name] = p
    # Resolve derived values in any order: loop until nothing changes.
    pending = [p for p in out.values() if p.source == "derived"]
    for _ in range(len(pending) + 1):
        left = []
        for p in pending:
            try:
                p.value = formula_eval(p.formula, {a: q.value for a, q in out.items()})
            except SchemaError:
                left.append(p)
        pending = left
    if pending:
        raise SchemaError(t("params.unresolved", where=where, names=", ".join(p.name for p in pending)))
    return out


def load_params(path: Path) -> dict[str, Param]:
    return parse_params(yamlio.read(path, {}), Path(path).name)
