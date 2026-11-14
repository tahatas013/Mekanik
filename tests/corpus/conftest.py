# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixtures of the seeded-error corpus (tests/corpus/F1): the workshop config of the cases (the test config with a
calibrated machine profile and a micrometer whose uncertainty is sourced, tests/corpus/F1/config), the shop of
tests/core/test_store.py (organization repo, GPG keys of the chief) for the cases that run the process, and the F1
summary printed at the end of the run (caught / fixed twin passes, per case)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "core"))

from test_store import gpg_keys, shop  # noqa: E402,F401

EXTRA = Path(__file__).resolve().parent / "F1" / "config"
OUTCOMES = pytest.StashKey[dict]()


def _overlay(cfg: Path) -> Path:
    """The corpus's machine and instrument files added to a copy of the test workshop config."""
    for f in EXTRA.rglob("*.yaml"):
        (dest := cfg / f.relative_to(EXTRA)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)
    return cfg


@pytest.fixture(scope="session")
def corpus_config(tmp_path_factory) -> Path:
    cfg = tmp_path_factory.mktemp("f1") / "config"
    shutil.copytree(ROOT / "tests" / "fixtures" / "config", cfg)
    return _overlay(cfg)


@pytest.fixture
def corpus_shop(shop):
    """The shop with the corpus's machine and instrument files in its workshop config."""
    _overlay(shop.config)
    return shop


@pytest.fixture
def f1_outcomes(request) -> dict:
    return request.config.stash.setdefault(OUTCOMES, {})


@pytest.fixture(autouse=True)
def _registry():
    from mekanik.plugins import reset_registry

    reset_registry()
    yield
    reset_registry()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not (done := config.stash.get(OUTCOMES, None)):
        return
    caught, clean = sum(bool(x["caught"]) for x in done.values()), sum(x["clean"] for x in done.values())
    terminalreporter.section("F1 seeded-error corpus")
    for cid, x in sorted(done.items()):
        mark = "caught" if x["caught"] else "NOT CAUGHT"
        terminalreporter.line(f"{cid} {x['kind']:<24} {mark:<10} {'; '.join(x['caught'])[:90]}"
                              + ("" if x["clean"] else "  [fixed twin flagged]"))
    terminalreporter.line(f"F1: {caught}/{len(done)} caught before a gate or decision; {clean}/{len(done)} fixed "
                          f"twins pass")
