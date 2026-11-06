# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cleanliness (architecture §3.1): the core knows no domain, person, organization or machine, and imports no
package. Identifiers and string constants of src/mekanik/core are compared word by word (`print(` or `drawing` do
not count); the real names are read from the workshop config at test time."""

import ast
import importlib.util
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from mekanik.config import load_config

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CORE = ROOT / "src" / "mekanik" / "core"
DOMAIN = {"fit", "fdm", "printer", "mold", "molding", "wing", "lidar"}
PACKAGES = ("mekanik_mech", "mekanik_print3d", "mekanik_analysis")


def _texts(tree: ast.AST):
    """(line, text) of every identifier and string constant."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.lineno, n.value
        elif isinstance(n, ast.Name):
            yield n.lineno, n.id
        elif isinstance(n, ast.Attribute):
            yield n.lineno, n.attr
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield n.lineno, n.name
        elif isinstance(n, ast.arg):
            yield n.lineno, n.arg
        elif isinstance(n, ast.keyword) and n.arg:
            yield n.value.lineno, n.arg
        elif isinstance(n, ast.alias):
            yield getattr(n, "lineno", 0), n.asname or n.name


def _names() -> list[str]:
    """Person, organization and machine names of the workshop config (phrases, compared case-insensitively)."""
    cfg = load_config()
    out = [cfg.doc["person"]["name"], cfg.chief[0]]
    out += [x for o in cfg.lists["organizations"] for x in (o["code"], o["name"])]
    out += [x for m in cfg.lists["machines"] for x in (m["id"], m.get("name", ""))]
    return [x for x in out if x]


def test_core_has_no_domain_person_org_or_machine_names():
    """new: architecture §3.1 temizlik testi — 0 matches"""
    phrases = [re.compile(rf"(?<![\w-]){re.escape(x)}(?![\w-])", re.I) for x in _names()]
    found = []
    for f in sorted(CORE.rglob("*.py")):
        for line, text in _texts(ast.parse(f.read_text(encoding="utf-8"))):
            words = {w.lower() for w in re.split(r"[^A-Za-z0-9]+", text) if w}
            hits = sorted(words & DOMAIN) + [p.pattern for p in phrases if p.search(text)]
            found += [f"{f.relative_to(ROOT)}:{line}: {h}" for h in hits]
    assert found == []


def test_core_imports_no_package():
    """new: architecture §3.1 — the core (and the rest of src/mekanik) never imports a package"""
    found = []
    for f in sorted((ROOT / "src" / "mekanik").rglob("*.py")):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            found += [f"{f.relative_to(ROOT)}:{n.lineno}: {m}" for m in mods if m.split(".")[0] in PACKAGES]
    assert found == []


def test_import_linter_contracts():
    """new: architecture §3.1 — `uv run lint-imports`: 0 violations"""
    exe = shutil.which("lint-imports")
    if exe is None or not all(importlib.util.find_spec(p) for p in PACKAGES):
        pytest.skip("lint-imports or a package is not installed in this environment (OCCT-free run)")
    p = subprocess.run([exe], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout[-2000:]


def test_catalog_messages_do_not_use_the_key_placeholder():
    """new: t(key, **args) cannot take an argument named `key`; core catalog messages must not use {key}"""
    for f in sorted((CORE / "i18n").glob("*.yaml")):
        assert "{key}" not in f.read_text(encoding="utf-8"), f.name
        yaml.safe_load(f.read_text(encoding="utf-8"))
