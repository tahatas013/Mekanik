# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rule catalog and its link to the code (architecture §4.7; Ek B finding 1)."""

import os
from pathlib import Path

import pytest

from mekanik.core import builtin, yamlio
from mekanik.core.checks import rules, runner
from mekanik.core.errors import SchemaError
from mekanik.core.model.work import load_work
from mekanik.plugins import CheckSpec, PackageSpec, registry, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "profiles": {"instruments": ["caliper"]},
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G3", "gate_status": {}}}
PARAMS = {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "wall": {"value": 2.0, "unit": "mm", "source": "assumption", "critical": "safety"},
          "boss": {"value": 14.0, "unit": "mm"}}
FIELDS = ("id", "text", "limit", "limit_source", "level", "basis", "check")


@pytest.fixture(autouse=True)
def _registry():
    set_registry([builtin.SPEC])          # the real core registration, with the evidence module's checks
    yield
    reset_registry()


def test_every_rule_has_its_fields_and_a_basis():
    """new: catalog format of guide §8.1; a rule without a basis does not enter the catalog (handbook §9)"""
    for rid, r in rules.catalog().items():
        assert all(f in r for f in FIELDS), rid
        assert r["basis"], f"{rid}: no basis"


def test_core_rules_are_in_the_catalog():
    """new: the core's rule ids (guide §2.3) are in stdlib/rules/core.yaml"""
    core = {i for i, r in rules.catalog().items() if r["file"] == "core.yaml"}
    assert core == {"SOURCE-01", "UNCERT-01", "APPROVAL-01", "APPROVAL-02", "DECISION-02", "CARD-01", "SCHEMA-01",
                    "SOURCE-02", "CALC-03", "CALC-04", "REQ-01"}   # phase 2 (plan §3, P)


def test_catalog_and_code_are_linked(tmp_path):
    """new: Ek B §14 madde 11 — every result's rule is in the catalog, every catalog rule's check is registered"""
    yamlio.write(tmp_path / "work.yaml", WORK)
    yamlio.write(tmp_path / "params.yaml", PARAMS)
    results = runner.run(load_work(tmp_path))
    assert rules.link_errors(registry(), results) == []
    assert {r.rule for r in results} <= set(rules.catalog())


def test_link_errors_find_unknown_and_unclaimed_rules():
    """new: the link check itself fails what is wrong"""
    fake = PackageSpec(id="core", version="0", checks=[CheckSpec("source", lambda v, m=None: [], ("NOPE-01",))])
    errors = rules.link_errors(set_registry([fake]))
    assert any("NOPE-01" in e for e in errors) and any("UNCERT-01" in e for e in errors)


def test_limit_comes_from_the_catalog():
    """new: thresholds are read from the catalog (guide §1.2, §8.1)"""
    assert rules.limit("UNCERT-01", "ratio") == 4
    with pytest.raises(SchemaError):
        rules.limit("UNCERT-01", "nope")
    with pytest.raises(SchemaError):
        rules.limit("NOPE-01", "ratio")
    assert rules.package_of("mech.fit_clearance") == "mech" and rules.package_of("source") == "core"
