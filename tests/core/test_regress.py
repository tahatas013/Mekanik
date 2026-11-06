# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression of frozen cases, and the regression's own test: a fake version of a check that blocks everything or
passes everything must not pass the regression (old test_regresyon; PROMPT §3.5, handbook §10).

tests/core runs without packages, so the cases here are small hand-written v1 cases of the core checks; the
migrated cases in tests/cases (with fits) run with the mech package."""

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.cards import makers
from mekanik.core.checks import regress
from mekanik.core.checks.builtin import CHECKS
from mekanik.plugins import CriticalDim, PackageSpec, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CORE = PackageSpec(id="core", version="0", checks=CHECKS, card_makers=[makers.make])
# The package side of UNCERT-01: critical dimensions read from the case's dims.yaml.
DIMS = PackageSpec(id="dims", version="0", loaders={"dims": lambda root, view: yamlio.read(root / "dims.yaml", [])},
                   critical_dims=lambda view: [CriticalDim(**d) for d in view.ext["dims"]])
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "profiles": {"instruments": ["caliper", "scanner-lidar"]},
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G3", "gate_status": {}}}
DECISION = {"kind": "decision", "schema_version": "1.0", "work": "TST-SYN-09", "title": "Malzeme",
            "category": "material", "mode": "hold", "decided_by": "chief_engineer", "rationale": "r",
            "opened_at": "2026-11-06T10:00:00+03:00",
            "options": [{"id": "a", "title": "A", "values": []}, {"id": "b", "title": "B", "values": []}],
            "requirement_effects": []}


def _card(cid, effects, visuals):
    return {"kind": "card", "schema_version": "1.0", "id": cid, "work": "TST-SYN-09", "key": f"decision:{cid}",
            "type": "decision", "level": "hold", "stop_category": "material", "title": "Malzeme hangisi?",
            "question": "A mı B mi?", "explain": {"tr": "Malzeme DUR kategorisidir."},
            "triggers": ["policy.stop:material"],
            "subject": {"decision": cid}, "proposal": {"text": "A dayanımı karşılıyor.", "option": "a"},
            "options": [{"id": x, "title": x, "visual": {"kind": "model_view", "id": f"{cid}-{x}.svg"}} for x in "ab"],
            "if_approved": "A kayda geçer.", "if_rejected": "Yeni seçenek.", "recorded_as": "decisions.yaml",
            "requirement_effects": effects, "status": "open", "opened_by": "project_engineer",
            "opened_at": "2026-11-06T10:00:00+03:00",
            **({"visuals": [{"kind": "model_view", "id": "v.svg"}]} if visuals else {})}


CASE_A = {
    "params": {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
               "slot_w": {"value": 5.0, "unit": "mm", "source": "measured:scanner-lidar"},
               "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
               "boss": {"value": 14.0, "unit": "mm"}},
    "dims": [{"ref": "X-01", "param": "hole_dia", "band": 0.2, "task": "centering"},
             {"ref": "X-02", "param": "slot_w", "band": 0.2, "task": "centering"}],
    "decisions": [{**DECISION, "id": "K-01", "status": "proposed"},
                  {**DECISION, "id": "K-02", "status": "approved", "chosen": "a", "approved_version": "abc1234"},
                  {**DECISION, "id": "K-03", "status": "proposed"}],
    "cards/K-01": _card("K-01", [], visuals=False),
    "cards/K-03": _card("K-03", [{"requirement": "R-01", "effect": "A: 2,4 ≥ 2,0"}], visuals=True),
    "approvals": [{"kind": "approval", "schema_version": "1.0", "work": "TST-SYN-09", "card": "S-01",
                   "action": "comment", "role": "chief_engineer",
                   "identity": {"name": "Test Mühendis", "email": "test@example.org"},
                   "at": "2026-11-06T11:00:00+03:00", "approved_hash": "0" * 64, "reason": "kaynak?"}],
    "expected": {"subcases": [
        {"id": "source", "description": "kaynaksız boss kalır, kumpas ölçüsü geçer",
         "expect": [{"check": "source", "ref": "boss", "result": "block"},
                    {"check": "source", "ref": "hole_dia", "result": "pass"}],
         "cards": [{"key": "unsourced:boss", "trigger": "unsourced"}]},
        {"id": "uncertainty", "description": "kumpas sınırda geçer, LiDAR kritik ölçüde kalır",
         "expect": [{"check": "uncertainty", "ref": "X-01", "param": "hole_dia", "result": "pass", "value": 0.05},
                    {"check": "uncertainty", "ref": "X-02", "param": "slot_w", "result": "fail"}],
         "cards": [{"key": "uncertainty:caliper", "trigger": "borderline"},
                   {"key": "measured:slot_w", "trigger": "uncertainty"}]},
        {"id": "approval_state", "description": "incelenmiş K-02 geçer, incelenmemiş K-01 kalır (G3)",
         "expect": [{"check": "approval_state", "ref": "K-02", "result": "pass"},
                    {"check": "approval_state", "ref": "K-01", "result": "block"}]},
        {"id": "decision_effects", "description": "isteklere etkisi yazılı K-03 geçer, boş K-01 kalır",
         "expect": [{"check": "decision_effects", "ref": "K-03", "result": "pass"},
                    {"check": "decision_effects", "ref": "K-01", "result": "block"}]},
        {"id": "card_standard", "description": "görselli K-03 geçer, görselsiz K-01 kalır",
         "expect": [{"check": "card_standard", "ref": "K-03", "result": "pass"},
                    {"check": "card_standard", "ref": "K-01", "result": "block"}]},
        {"id": "approval_signature", "description": "imzalı commit'i olmayan onay kaydı kalır",
         "expect": [{"check": "approval_signature", "ref": "S-01", "result": "block"}]}]},
}
CASE_B = {
    "params": {"gap": {"value": 0.3, "unit": "mm", "source": "decision"}},
    "expected": {"subcases": [
        {"id": "approval_signature", "description": "onay kaydı yoksa geçer",
         "expect": [{"check": "approval_signature", "ref": None, "result": "pass"}]}]},
}


@pytest.fixture(scope="module")
def cases(tmp_path_factory):
    root = tmp_path_factory.mktemp("cases")
    req = json.loads((ROOT / "schemas/v1/examples/requirement.json").read_text(encoding="utf-8"))
    for name, files, stage in (("core-a", CASE_A, "G3"), ("core-b", CASE_B, "G2")):
        (root / name / "cards").mkdir(parents=True)
        yamlio.write(root / name / "work.yaml", {**WORK, "process": {**WORK["process"], "stage": stage}})
        if name == "core-a":
            yamlio.write(root / name / "requirements.yaml", {**req, "work": "TST-SYN-09"})
        for f, data in files.items():
            yamlio.write(root / name / f"{f}.yaml", data)
    return root


@pytest.fixture(autouse=True)
def _registry():
    set_registry([CORE, DIMS])
    yield
    reset_registry()


def _always(spec, status):
    """The real check's results, every status replaced (refs kept)."""
    return replace(spec, run=lambda *a, **kw: [replace(r, status=status) for r in spec.run(*a, **kw)])


def test_all_cases_pass(cases):
    """old: test_regresyon::vakalarin_hepsi_gecer"""
    out = regress.run_all(cases)
    assert {s.case for s in out} == {"core-a", "core-b"}
    assert [s.id for s in out if s.case == "core-a"] == ["source", "uncertainty", "approval_state", "decision_effects",
                                                          "card_standard", "approval_signature"]
    assert all(s.passed for s in out), [(s.case, s.id, s.errors) for s in out if not s.passed]


@pytest.mark.parametrize("spec", CHECKS, ids=lambda c: c.id)
@pytest.mark.parametrize("status", ["block", "pass"])
def test_uniform_check_fails_regression(cases, spec, status):
    """old: test_regresyon::tek_duze_kontrol_regresyondan_gecmez"""
    checks = [_always(c, status) if c is spec else c for c in CHECKS]
    out = regress.run_all(cases, checks)
    assert any(not s.passed for s in out), f"{spec.id} always {status}: the regression still passed"
