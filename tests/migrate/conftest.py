# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared fixtures of the migration tests: the test workshop config, migrated cases and stand-ins for the v1 side."""

from __future__ import annotations

from pathlib import Path

import pytest

from build_cases import OLD, ROOT, snapshot
from fakes import RULES, Hooks, old_cards, old_results
from mekanik.config import load_config
from mekanik.migrate import surec_work
from mekanik.plugins import CheckSpec, PackageSpec, reset_registry, set_registry


@pytest.fixture(autouse=True)
def _registry():
    yield
    reset_registry()


@pytest.fixture
def cfg():
    return load_config(ROOT / "tests" / "fixtures" / "config")


@pytest.fixture
def migrated(tmp_path, cfg):
    """case → (old folder, new folder, log): a dry run into tmp_path with the old-side snapshot."""
    def run(case: str, old: Path | None = None):
        old = old or OLD / case
        out = tmp_path / case
        return old, out, surec_work(old, out, cfg, old=snapshot(case))
    return run


@pytest.fixture
def v1_side(monkeypatch):
    """Stand-ins for the wave-2 modules, so V4–V8 logic is tested on its own: checks that return `results`, card
    generation that returns `cards`, print3d.fdm profile type, model hooks."""
    import mekanik.core.cards as cards_mod

    def install(case: str, out: Path, results=None, cards=None, metrics=None, hooks=True, checks=True):
        res = old_results(case) if results is None else results
        specs = [PackageSpec(id="core", version="0", checks=[CheckSpec("fake", lambda v, m, cards=None: res, RULES)]
                             if checks else []),
                 PackageSpec(id="print3d", version="0", profile_types={"print3d.fdm": lambda d, w: None},
                             model=(Hooks(snapshot(case)["model"] if metrics is None else metrics) if hooks else None))]
        set_registry(specs)
        monkeypatch.setattr(cards_mod, "generate", lambda view, results: old_cards(case) if cards is None else cards)
    return install
