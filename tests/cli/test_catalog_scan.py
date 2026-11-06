# SPDX-License-Identifier: AGPL-3.0-or-later
"""Criterion 1.5: no Turkish text outside the catalog in the CLI. Every string constant of src/mekanik/cli other than
a docstring is checked for Turkish letters (f-string parts included); the CLI's catalog keys must exist."""

import ast
import re
from pathlib import Path

from mekanik.core.i18n import has

CLI = Path(__file__).resolve().parents[2] / "src" / "mekanik" / "cli"
TURKISH = re.compile("[çğıöşüÇĞİÖŞÜ]")


def _docstrings(tree: ast.AST) -> set[int]:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and isinstance(
                first := n.body[0], ast.Expr) and isinstance(first.value, ast.Constant):
            out.add(id(first.value))
    return out


def _strings():
    for f in sorted(CLI.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        docs = _docstrings(tree)
        yield from ((f, n) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and id(n) not in docs)


def test_cli_has_no_turkish_string_outside_the_catalog():
    """new: architecture §17 criterion 1.5 — 0 strings"""
    found = [f"{f.name}:{n.lineno}: {n.value!r}" for f, n in _strings() if TURKISH.search(n.value)]
    assert found == []


def test_cli_catalog_keys_exist():
    """new: architecture §4.12 — every literal cli.* key the CLI asks for is in the Turkish catalog"""
    keys = {n.value for _, n in _strings() if re.fullmatch(r"cli(\.[\w-]+)+", n.value)
            and not (CLI / f"{n.value[4:]}.py").exists()}           # not a module name (_m("cli.doctor"))
    assert keys and sorted(k for k in keys if not has(k)) == []
