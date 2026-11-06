# SPDX-License-Identifier: AGPL-3.0-or-later
"""Record model: YAML loader, params schema, instrument and machine pins, broken input (old test_cekirdek)."""

import importlib.util
import os
import re
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.cards import makers
from mekanik.core.checks.builtin import CHECKS
from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.plugins import PackageSpec, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CORE = PackageSpec(id="core", version="0", checks=CHECKS, card_makers=[makers.make])
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G2", "gate_status": {}}}
PARAMS = {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
          "shaft_dia": {"value": None, "unit": "mm", "source": "derived", "formula": "hole_dia - gap"}}


def work(tmp, params=None, stage="G2", profiles=None, **files):
    doc = {**WORK, "process": {**WORK["process"], "stage": stage},
           "profiles": profiles or {"instruments": ["caliper", "scanner-lidar"]}}
    yamlio.write(tmp / "work.yaml", doc)
    yamlio.write(tmp / "params.yaml", PARAMS if params is None else params)
    for name, data in files.items():
        yamlio.write(tmp / f"{name}.yaml", data)
    return load_work(tmp)


def key_re(key: str) -> str:
    """Regex of a catalog message (placeholders → anything): tests check the key, not the Turkish text."""
    return "(?s)^" + ".*".join(map(re.escape, re.split(r"\{[a-z_]+\}", t(key)))) + "$"


@pytest.fixture(autouse=True)
def _registry():
    set_registry([CORE])
    yield
    reset_registry()


def test_yaml_no_key_is_not_bool():
    """old: test_cekirdek::yaml_no_anahtari_bool_olmaz"""
    assert yamlio.load("- no: G-01\n  critical: true\n  x: yes") == [{"no": "G-01", "critical": True, "x": "yes"}]


@pytest.mark.parametrize("bad,key", [
    ({"x": {"value": 1, "unit": "mm", "source": "guess"}}, "schema.invalid"),                  # unknown source
    ({"x": {"value": 1, "unit": "mm", "source": "measured:micrometer"}}, "work.instrument_not_pinned"),
    ({"x": {"value": 1, "unit": "mm", "source": "derived"}}, "schema.invalid"),                # formula required
    ({"X-1": {"value": 1, "unit": "mm", "source": "decision"}}, "schema.invalid"),             # ASCII name
])
def test_schema_violation_stops_with_clear_message(tmp_path, bad, key):
    """old: test_cekirdek::sema_ihlali_acik_mesajla_durur"""
    with pytest.raises(SchemaError, match=key_re(key)):
        work(tmp_path, params={**PARAMS, **bad})


def test_constant_formula_is_not_derived(tmp_path):
    """old: test_cekirdek::sabit_formul_turetilir_sayilmaz"""
    with pytest.raises(SchemaError, match=key_re("params.derived_constant")):
        work(tmp_path, params={"boss": {"unit": "mm", "source": "derived", "formula": "14.0"}})


def test_scan_label_cannot_use_caliper_profile(tmp_path):
    """old: test_cekirdek::tarama_etiketi_kumpas_profiliyle_yazilamaz

    v1: the instrument is in the source tag itself; a scanner value cannot ride on the pinned caliper."""
    p = {**PARAMS, "hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:scanner-lidar"}}
    with pytest.raises(SchemaError, match=key_re("work.instrument_not_pinned")):
        work(tmp_path, params=p, profiles={"instruments": ["caliper"]})


def test_measuring_profile_version_is_pinned(tmp_path):
    """old: test_cekirdek::olcum_profili_surumu_sabitlenir

    v1: instruments are pinned by id (a versioned id is not the config's); machine profiles by <id>@<version>."""
    with pytest.raises(SchemaError, match=key_re("config.missing_instruments")):
        work(tmp_path, profiles={"instruments": ["caliper@v9"]})
    with pytest.raises(SchemaError, match=key_re("config.machine_version")):
        work(tmp_path, profiles={"manufacturing": "fdm-test@v9", "instruments": ["caliper"]})


@pytest.mark.parametrize("name,content,key", [
    ("decisions", {"id": "K-01"}, "schema.not_list"),
    ("params", ["hole"], "schema.invalid"),
    ("params", {"x": {"value": True, "unit": "mm", "source": "decision"}}, "schema.invalid"),
    ("params", {"x": {"value": 1, "unit": "inch", "source": "decision"}}, "params.unit"),
    ("decisions", ["x"], "schema.invalid"),
    ("approvals", [{"card": "G-01"}], "schema.invalid"),
    ("replies", [{"card": "S-01", "text": "tamam"}], "schema.invalid"),
])
def test_broken_input_stops_with_clear_message(tmp_path, name, content, key):
    """old: test_cekirdek::bozuk_girdi_acik_mesajla_durur (core files; the fit-file cases are in tests/mech)"""
    work(tmp_path)
    yamlio.write(tmp_path / f"{name}.yaml", content)
    with pytest.raises(SchemaError, match=key_re(key)):
        load_work(tmp_path)


def test_schema_examples_clean():
    """new: schemas/v1 and their examples (old docs/design/schemas/check_examples.py), also run as a pytest test"""
    spec = importlib.util.spec_from_file_location("schema_examples", Path(__file__).with_name("schema_examples.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
