# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixtures of the mech tests: a v1 work folder in tmp_path (the counterpart of old test_cekirdek.kur), the test
workshop config, and a registry of the domain packages only (the core's own checks are written in parallel)."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest
import yaml
from mech_data import FITS, PARAMS, WORK

CONFIG = Path(__file__).resolve().parents[1] / "fixtures" / "config"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    import mekanik_analysis
    import mekanik_mech
    import mekanik_print3d
    from mekanik.plugins import reset_registry, set_registry

    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(CONFIG))
    set_registry([mekanik_mech.SPEC, mekanik_print3d.SPEC, mekanik_analysis.SPEC])
    yield
    reset_registry()


@pytest.fixture
def work(tmp_path):
    """work(params=…, fits=…, flexes=…, stage=…, model=…) → WorkView of a fresh v1 work folder."""
    def make(params=None, fits=None, flexes=None, stage="G2", model: str | None = None, root: Path = tmp_path):
        from mekanik.core.model.work import load_work

        doc = {**WORK, "process": {**WORK["process"], "stage": stage}}
        for name, data in (("work.yaml", doc), ("params.yaml", PARAMS if params is None else params),
                           ("fits.yaml", {"fits": FITS if fits is None else fits, "flexes": flexes or []})):
            (root / name).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if model is not None:
            (root / "model").mkdir(exist_ok=True)
            (root / "model" / "model.py").write_text(model, encoding="utf-8")
        return load_work(root)
    return make


@pytest.fixture
def approval_states(monkeypatch):
    """ASSY-01 asks `mekanik.core.cards.approval.state` (wave 2 · A). The states are set per card id here; when A's
    module is not there yet a stand-in module takes its place. Returns (states, calls)."""
    try:
        mod = importlib.import_module("mekanik.core.cards.approval")
    except ImportError:
        import mekanik.core.cards as pkg

        mod = types.ModuleType("mekanik.core.cards.approval")
        monkeypatch.setitem(sys.modules, mod.__name__, mod)
        monkeypatch.setattr(pkg, "approval", mod, raising=False)
    states, calls = {}, []

    def state(view, card_id, subject):
        calls.append((card_id, subject))
        return states.get(card_id, "none")

    monkeypatch.setattr(mod, "state", state, raising=False)
    return states, calls


@pytest.fixture
def shaft_hole():
    """Old test_cekirdek._mil_delik: shaft_hole(shaft_d, hole_d=10) → block A with a hole, pin B through it."""
    def make(shaft_d: float, hole_d: float = 10.0) -> dict:
        import cadquery as cq

        a = cq.Workplane().box(30, 30, 10).faces(">Z").workplane().hole(hole_d).val()
        b = cq.Workplane().circle(shaft_d / 2).extrude(20).translate((0, 0, -10)).val()
        return {"A": a, "B": b}
    return make
