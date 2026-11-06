# SPDX-License-Identifier: AGPL-3.0-or-later
"""Safe expressions of question trees and library items (common#/$defs/expression): numbers, text, comparison,
and/or/not, + - * /, dotted names over a context (answer, answers.<id>, analysis.<id>.<name>, work.<field> …).
No call and no subscript; a missing name is None, and a comparison with None is false (except == and !=)."""

from __future__ import annotations

import ast
import operator

from ..errors import SchemaError
from ..i18n import t

_CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt,
        ast.GtE: operator.ge}
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_WORDS = {"null": None, "None": None, "true": True, "True": True, "false": False, "False": False}


def evaluate(text: str, ctx: dict):
    try:
        return _ev(ast.parse(text, mode="eval").body, ctx, text)
    except SyntaxError as e:
        raise SchemaError(t("intake.expr.invalid", expr=text, error=e.msg)) from e


def holds(text: str, ctx: dict) -> bool:
    return bool(evaluate(text, ctx))


def _ev(n, ctx: dict, text: str):
    def ev(x):
        return _ev(x, ctx, text)

    if isinstance(n, ast.Constant) and (n.value is None or isinstance(n.value, (int, float, str))):
        return n.value
    if isinstance(n, ast.Name):
        return _WORDS[n.id] if n.id in _WORDS else ctx.get(n.id)
    if isinstance(n, ast.Attribute):
        base = ev(n.value)
        return base.get(n.attr) if isinstance(base, dict) else None
    if isinstance(n, ast.BoolOp):
        return (all if isinstance(n.op, ast.And) else any)(ev(v) for v in n.values)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
        return not ev(n.operand)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        v = ev(n.operand)
        return -v if isinstance(v, (int, float)) else None
    if isinstance(n, ast.Compare) and all(type(o) in _CMP for o in n.ops):
        left = ev(n.left)
        for op, right in zip(n.ops, map(ev, n.comparators)):
            try:
                if not _CMP[type(op)](left, right):
                    return False
            except TypeError:
                return False
            left = right
        return True
    if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
        try:
            return _BIN[type(n.op)](ev(n.left), ev(n.right))
        except (TypeError, ZeroDivisionError):
            return None
    raise SchemaError(t("intake.expr.forbidden", expr=text, node=type(n).__name__))
