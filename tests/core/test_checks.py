# SPDX-License-Identifier: AGPL-3.0-or-later
"""Core checks: SOURCE-01, UNCERT-01, APPROVAL-01, DECISION-02, CARD-01 (old test_cekirdek and new)."""

import json
import os
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.cards import makers
from mekanik.core.checks import runner
from mekanik.core.checks.builtin import CHECKS, approval, cards, source, uncertainty
from mekanik.core.model.work import load_work
from mekanik.plugins import CriticalDim, PackageSpec, SourcedValue, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CORE = PackageSpec(id="core", version="0", checks=CHECKS, card_makers=[makers.make])
# The package side of UNCERT-01 is faked: one critical dimension on hole_dia, band 0.2 (centering 0.2 … 0.4).
DIMS = PackageSpec(id="fake", version="0", critical_dims=lambda v: [CriticalDim("X-01", "hole_dia", 0.2, "centering")])
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "profiles": {"instruments": ["caliper", "scanner-lidar"]},
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G2", "gate_status": {}}}
PARAMS = {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
          "shaft_dia": {"value": None, "unit": "mm", "source": "derived", "formula": "hole_dia - gap"}}
BOSS = {"boss": {"value": 14.0, "unit": "mm"}}


def work(tmp, params=None, stage="G2", **files):
    yamlio.write(tmp / "work.yaml", {**WORK, "process": {**WORK["process"], "stage": stage}})
    yamlio.write(tmp / "params.yaml", PARAMS if params is None else params)
    for name, data in files.items():
        yamlio.write(tmp / (f"cards/{name[5:]}.yaml" if name.startswith("card_") else f"{name}.yaml"), data)
    return load_work(tmp)


@pytest.fixture(autouse=True)
def _registry():
    set_registry([CORE, DIMS])
    yield
    reset_registry()


def test_unsourced_param_blocks(tmp_path):
    """old: test_cekirdek::kaynaksiz_param_engel_verir"""
    s = source.run(work(tmp_path, params={**PARAMS, **BOSS}))
    assert [(x.status, x.ref, x.msg) for x in s if x.failed] == [("block", "boss", "checks.source.missing")]
    assert {x.ref for x in s if x.status == "pass"} == {"hole_dia", "gap", "shaft_dia"}


def test_unsourced_blocks_at_every_stage(tmp_path):
    """old: test_cekirdek::kaynaksiz_her_asamada_engel"""
    for stage in ("G0", "G2", "G5"):
        v = work(tmp_path, params={**PARAMS, **BOSS}, stage=stage)
        assert next(x for x in source.run(v) if x.ref == "boss").status == "block"


def test_sourced_params_pass(tmp_path):
    """old: test_cekirdek::kaynakli_params_gecer"""
    assert all(x.status == "pass" for x in source.run(work(tmp_path)))


def test_package_value_without_source_blocks(tmp_path):
    """new: SOURCE-01 covers the values a package reports (sourced_values), e.g. an assembly flex"""
    flex = PackageSpec(id="flexes", version="0", sourced_values=lambda v: [SourcedValue("E-01", 3.2, "mm", None),
                                                                           SourcedValue("E-02", 1.0, "mm", "decision")])
    set_registry([CORE, flex])
    s = {x.ref: x.status for x in source.run(work(tmp_path))}
    assert s["E-01"] == "block" and s["E-02"] == "pass"


def test_caliper_centering_borderline_passes(tmp_path):
    """old: test_cekirdek::kumpas_ortalama_gecmede_sinirda_gecer"""
    s = uncertainty.run(work(tmp_path))   # caliper ±0.05; band 0.2 / 4 = 0.05
    assert s[0].status == "pass" and s[0].msg == "checks.uncertainty.ok"
    assert s[0].extra["borderline"] and s[0].extra["assumed"] and s[0].args["notes"]


def test_lidar_fails_on_critical_dimension(tmp_path):
    """old: test_cekirdek::lidar_kritik_gecmede_kalir"""
    p = {**PARAMS, "hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:scanner-lidar"}}
    s = uncertainty.run(work(tmp_path, params=p))
    assert s[0].failed and s[0].ref == "X-01" and s[0].extra["param"] == "hole_dia"
    assert set(s[0].extra["cases"]) == {"form_only", "ratio"}      # old OLCU-02 and OLCU-01
    assert s[0].status == "warn"                                     # before finalizing
    assert uncertainty.run(work(tmp_path, params=p, stage="G3"))[0].status == "block"


def test_uncertainty_without_band_fails(tmp_path):
    """new: an undefined tolerance band cannot pass the 1/4 rule (old olcme_belirsizligi, untested branch)"""
    nob = PackageSpec(id="f", version="0", critical_dims=lambda v: [CriticalDim("X-02", "hole_dia", None)])
    set_registry([CORE, nob])
    s = uncertainty.run(work(tmp_path))
    assert s[0].failed and s[0].extra["cases"] == ["no_band"]


def test_open_card_blocks_when_finalizing(tmp_path):
    """old: test_cekirdek::kesinlestirmede_acik_kart_engel"""
    p = {**PARAMS, "wall": {"value": 2.0, "unit": "mm", "source": "assumption", "critical": "safety"}}
    s = [x for x in runner.run(work(tmp_path, params=p, stage="G3")) if x.check == "approval_state"]
    assert any(x.status == "block" and x.msg == "checks.approval_state.hold" for x in s)
    assert approval.state(work(tmp_path, params=p, stage="G2")) == []   # not applied before finalizing


DECISION = {"kind": "decision", "schema_version": "1.0", "work": "TST-SYN-09", "title": "Malzeme",
            "category": "material", "mode": "hold", "decided_by": "chief_engineer", "rationale": "r",
            "opened_at": "2026-11-06T10:00:00+03:00",
            "options": [{"id": "a", "title": "A", "values": []}, {"id": "b", "title": "B", "values": []}],
            "requirement_effects": []}


def _decision_card(cid, effects, visuals=True):
    return {"kind": "card", "schema_version": "1.0", "id": cid, "work": "TST-SYN-09", "key": f"decision:{cid}",
            "type": "decision", "level": "hold", "stop_category": "material", "title": "Malzeme hangisi?",
            "question": "Malzeme A mı B mi?", "explain": {"tr": "Malzeme DUR kategorisidir."},
            "triggers": ["policy.stop:material"], "subject": {"decision": cid},
            "proposal": {"text": "A dayanımı karşılıyor.", "option": "a", "choice": "a", "rationale": "dayanım"},
            "options": [{"id": x, "title": x.upper(), "visual": {"kind": "model_view", "id": f"{cid}-{x}.svg"}}
                        for x in "ab"],
            "if_approved": "A kayda geçer.", "if_rejected": "Ekip yeni seçenek önerir.",
            "recorded_as": "decisions.yaml",
            "requirement_effects": effects, "status": "open", "opened_by": "project_engineer",
            "opened_at": "2026-11-06T10:00:00+03:00",
            **({"visuals": [{"kind": "model_view", "id": f"{cid}.svg"}]} if visuals else {})}


def _with_decisions(tmp_path, stage="G3"):
    req = json.loads((ROOT / "schemas/v1/examples/requirement.json").read_text(encoding="utf-8"))
    effect = [{"requirement": "R-01", "effect": "A: 2,4 ≥ 2,0", "direction": "improves"}]
    dec = [{**DECISION, "id": "K-01", "status": "proposed"},
           {**DECISION, "id": "K-02", "status": "approved", "chosen": "a", "approved_version": "abc1234"},
           {**DECISION, "id": "K-03", "status": "proposed"}]
    return work(tmp_path, stage=stage, requirements={**req, "work": "TST-SYN-09"}, decisions=dec,
                **{"card_K-01": _decision_card("K-01", [], visuals=False), "card_K-03": _decision_card("K-03", effect)})


def test_decision_not_reviewed_blocks_when_finalizing(tmp_path):
    """new: APPROVAL-01 decision part (old onay_durumu: 'karar incelenmedi')"""
    s = [(x.ref, x.msg) for x in runner.run(_with_decisions(tmp_path)) if x.check == "approval_state"]
    assert {("K-01", "checks.approval_state.decision_open"), ("K-03", "checks.approval_state.decision_open"),
            ("K-02", "checks.approval_state.decision_ok"), ("K-01", "checks.approval_state.hold")} <= set(s)


def test_decision_card_needs_requirement_effects(tmp_path):
    """new: Ek B §14 — `hedef_etkisi` eksikse kartın açılmaması (B8), DECISION-02"""
    s = {x.ref: x.status for x in runner.run(_with_decisions(tmp_path, stage="G2")) if x.check == "decision_effects"}
    assert s == {"K-01": "block", "K-03": "pass"}


def test_card_standard_blocks_opened_card_without_visual(tmp_path):
    """new: CARD-01, card standard (Ö-10, old kartlar.eksikler: kimliksiz kural)"""
    v = _with_decisions(tmp_path, stage="G2")
    s = {x.ref: x for x in runner.run(v) if x.check == "card_standard"}
    assert s["K-01"].status == "block" and s["K-01"].extra["missing"] == ["visuals"]
    assert s["K-03"].status == "pass"
    new = {"id": "S-09", "status": "open", "type": "assumption"}          # not opened yet: the step checks it
    assert cards.standard(v, cards=[new]) == cards.standard(v, cards=[])
    assert cards.standard(v, cards=[new], opened_only=False)[0].status == "block"
