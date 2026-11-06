# SPDX-License-Identifier: AGPL-3.0-or-later
"""SOURCE-02 (architecture §10.1, F3): a number in the work's model or calc code (model/*.py, calcs/*.py) outside the
catalog's allow list must come from params.yaml or a sourced `const()`. Exploration and development warn, finalizing
blocks (F3: zero at release). Not engineering numbers, so not counted: the arguments of `const()` (sourced in the
call), the method level of `magnitude()` and integer subscripts (positions)."""

from __future__ import annotations

import ast
from pathlib import Path

from mekanik.plugins import CheckSpec

from ...evidence import calc
from ..result import BLOCK, PASS, Result, level
from ..rules import limit

RULE = "SOURCE-02"


def numbers(tree: ast.AST) -> list[tuple[int, float]]:
    """(line, value) of the numeric constants of the code that count."""
    skip: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "const":
            skip |= {id(x) for a in [*n.args, *(k.value for k in n.keywords)] for x in ast.walk(a)}
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "magnitude":
            lv = n.args[3] if len(n.args) > 3 else next((k.value for k in n.keywords if k.arg == "level"), None)
            skip |= {id(lv)} if lv is not None else set()
        elif isinstance(n, ast.Subscript):
            skip |= {id(x) for x in ast.walk(n.slice) if isinstance(x, ast.Constant) and type(x.value) is int}
    return [(n.lineno, n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and type(n.value) in (int, float) and id(n) not in skip]


def files(root: Path) -> list[Path]:
    return sorted((root / "model").glob("*.py")) + calc.files(root)


def run(view, model=None) -> list[Result]:
    root, allowed, out = Path(view.root), {float(x) for x in limit(RULE, "allowed")}, []
    for f in files(root):
        rel = str(f.relative_to(root))
        try:
            found = [(n, v) for n, v in numbers(ast.parse(f.read_text(encoding="utf-8"))) if float(v) not in allowed]
        except SyntaxError as e:
            out.append(Result("source_code", RULE, BLOCK, "policy.source02.unreadable", {"file": rel, "line": e.lineno},
                              rel))
            continue
        out += [Result("source_code", RULE, level(view), "policy.source02.number", {"file": rel, "line": n, "value": v},
                       rel, float(v), extra={"line": n}) for n, v in found]
        if not found:
            out.append(Result("source_code", RULE, PASS, "policy.source02.clean", {"file": rel}, rel))
    return out or [Result("source_code", RULE, PASS, "policy.source02.none")]


CHECKS = [CheckSpec("source_code", run, (RULE,), order=12)]
