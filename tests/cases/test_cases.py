# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression on the migrated synthetic cases with every registered package (criterion 1.4).

The cases are tests/cases/{S-001,H-001} (built by tests/migrate/build_cases.py). A check that returns the same
status for everything (always block / always pass) must fail the regression: otherwise the case proves nothing."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.checks.regress import run_all
from mekanik.core.checks.result import BLOCK, PASS
from mekanik.plugins import registry, reset_registry

pytest.importorskip("cadquery")
pytestmark = pytest.mark.occt


@pytest.fixture(autouse=True)
def _registry(monkeypatch):
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", "tests/fixtures/config")
    reset_registry()
    yield
    reset_registry()


def test_all_subcases_pass():
    """new: 1.4 — S-001 (10) + H-001 (8) subcases give the expected results with the real checks."""
    subs = run_all()
    assert len(subs) == 18
    assert all(s.passed for s in subs), [(s.case, s.id, s.errors) for s in subs if not s.passed]


def _uniform(spec, status):
    def run(view, model, cards=None):
        res = spec.run(view, model, cards=cards) if spec.after_cards else spec.run(view, model)
        return [replace(r, status=status) for r in res]
    return replace(spec, run=run)


def _covered() -> set[str]:
    """Check ids the expected.yaml files name."""
    root = Path(__file__).parent
    return {e["check"] for f in root.glob("*/expected.yaml") for s in yamlio.read(f)["subcases"] for e in s["expect"]}


@pytest.mark.parametrize("status", [BLOCK, PASS])
def test_uniform_check_fails_regression(status):
    """new: 1.4 — every check the cases cover, made uniform (always block / always pass), fails at least one subcase."""
    checks = registry().checks
    covered = _covered()
    survivors = []
    for i, spec in enumerate(checks):
        if spec.id not in covered:
            continue
        fake = [*checks[:i], _uniform(spec, status), *checks[i + 1:]]
        if all(s.passed for s in run_all(checks=fake)):
            survivors.append(spec.id)
    assert covered and not survivors, survivors
