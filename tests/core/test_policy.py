# SPDX-License-Identifier: AGPL-3.0-or-later
"""Question policy and the phase-2 assurance checks without git (OCCT-free): the stop classifier (D1), the threshold
suggestion (D6), the stage measures (D5), SOURCE-02 (F3), CALC-03, CALC-04 and REQ-01 (F5), each check with a passing
and a failing subcase that its "always block" and "always pass" fakes cannot pass (F2 for the new checks)."""

from __future__ import annotations

import copy
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from mekanik.core import policy, yamlio
from mekanik.core.builtin import SPEC
from mekanik.core.cards import generate, sync
from mekanik.core.checks import regress, runner
from mekanik.core.checks.builtin import assurance, source_code
from mekanik.core.model.schema import errors
from mekanik.core.model.work import load_work
from mekanik.core.policy import metrics
from mekanik.plugins import reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
EIGHT = ["manufacturing_method", "material", "main_dimensions", "deviation_from_standard", "cost_impact",
         "release_production", "requirement_change", "chief_only_info"]
TEN = EIGHT + ["frozen_version_change", "process_document_change"]
EX = {n: json.loads((ROOT / "schemas/v1/examples" / f"{n}.json").read_text(encoding="utf-8"))
      for n in ("decision", "provisional-decision", "card", "config")}
AT = "2026-11-06T10:00:00+03:00"
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": AT,
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G1",
                    "gate_status": {"G1": {"status": "in_progress", "started_at": AT}}}}
PARAMS = {"w": {"value": 20.0, "unit": "mm", "source": "decision"},
          "edge": {"value": 30.0, "unit": "mm", "source": "decision", "main_dimension": True},
          "price": {"value": 3.0, "unit": "count", "source": "decision", "critical": "cost"},
          "wall": {"value": 2.0, "unit": "mm", "source": "assumption", "critical": "safety", "rationale": "r"}}
REQ = {"id": "R-01", "text": "Kenar sığar", "kind": "mandatory", "origin": {"type": "chief_engineer"},
       "criterion": {"measure": "edge_len", "operator": "<=", "target": {"value": 256.0, "unit": "mm",
                                                                       "source": "decision",
                                                                       "decided_by": "chief_engineer"}},
       "verification": {"method": "calculation"}, "status": "approved"}


@pytest.fixture(autouse=True)
def _registry():
    set_registry([SPEC])
    yield
    reset_registry()


def _work(tmp, stage="G1", params=None, reqs=(), decisions=(), calcs=None, files=None):
    yamlio.write(tmp / "work.yaml", {**WORK, "process": {**WORK["process"], "stage": stage}})
    yamlio.write(tmp / "params.yaml", PARAMS if params is None else params)
    if reqs:
        yamlio.write(tmp / "requirements.yaml", {"kind": "requirement_list", "schema_version": "1.0",
                                                 "work": WORK["code"], "items": list(reqs)})
    yamlio.write(tmp / "decisions.yaml", list(decisions))
    for cid, rec in (calcs or {}).items():
        yamlio.write_text(tmp / "records" / "calcs" / f"{cid}.json", json.dumps({"id": cid, **rec}))
    for rel, text in (files or {}).items():
        yamlio.write_text(tmp / rel, text)
    return load_work(tmp)


def _prov(did, category="design_detail", status="provisional_active", opened=AT, values=("w",)):
    """A schema-valid provisional decision record."""
    d = {**copy.deepcopy(EX["provisional-decision"]), "id": did, "work": WORK["code"], "category": category,
         "status": status, "opened_at": opened, "objection_until": "G1", "card": did, "dependents": [],
         "options": [{"id": o, "title": o, "values": [{"name": n, "quantity": {
             "value": v, "unit": "mm", "source": "decision", "decided_by": "project_engineer"}} for n in values]}
                     for o, v in (("a", 1.0), ("b", 2.0))], "requirement_effects": []}
    if status == "reverted":
        d["provisional"] = {"stream_event": "", "outcome": "objected_reverted",
                            "objection": {"at": AT, "text": "hayır"}}
        d["history"] = [{"at": opened, "event": "reverted", "role": "project_engineer"}]
    return d


def test_stop_category_decision_or_card_cannot_be_provisional_in_the_schema():
    """2.3: D1 — schema: a decision of any of the 8 + 2 stop categories is not provisional (decision and
    provisional-decision schemas), nor a card that carries a stop category (10/10)"""
    for cat in TEN:
        dec = {**copy.deepcopy(EX["provisional-decision"]), "category": cat}
        assert errors("decision", dec) and errors("provisional_decision", dec), cat
        assert not errors("decision", {**copy.deepcopy(EX["decision"]), "category": cat}), cat   # hold is fine
        card = {**copy.deepcopy(EX["card"]), "stop_category": cat}
        assert not errors("card", {**card, "level": "hold"}), cat
        assert errors("card", {**card, "level": "provisional"}) and errors("card", {**card, "level": "witness"}), cat
    assert not errors("provisional_decision", EX["provisional-decision"])


def test_classifier_holds_every_stop_category_and_the_config_only_extends(tmp_path, monkeypatch):
    """2.3: D1 — classifier: each of the 8 + 2 categories is hold whatever the config says; the config adds
    categories but cannot drop one of the eight (config schema); the two of T-23 hold even if the config omits them"""
    v = _work(tmp_path)
    opts = [{"id": "a", "values": [{"name": "w"}]}, {"id": "b", "values": []}]
    assert set(policy.fixed_stops()) == set(TEN) and policy.decision_category(v, "design_detail", opts) is None
    for cat in TEN:
        assert policy.decision_category(v, cat, opts) == cat
        assert policy.classify_card(v, {"type": "question", "stop_category": cat, "generated": True})[0] == "hold"
    cfg = copy.deepcopy(EX["config"])
    for cat in EIGHT:
        narrow = {**cfg, "policy": {**cfg["policy"], "stop_categories": [c for c in EIGHT if c != cat]}}
        assert errors("config", narrow), cat
    monkeypatch.setattr(policy, "_config", lambda: {"stop_categories": EIGHT + ["design_detail"]})
    assert policy.decision_category(v, "design_detail", opts) == "design_detail"
    assert set(TEN) <= set(policy.stop_categories())


def test_rules_make_a_decision_or_card_stricter_than_the_role(tmp_path):
    """2.3: D1 — the stricter of the role's category and the rules: a main dimension (marked or in a requirement
    criterion), a cost-critical value, a material or manufacturing profile, a deviation, an assumed safety value"""
    v = _work(tmp_path, reqs=[REQ], params={**PARAMS, "edge_len": {"value": 1.0, "unit": "mm", "source": "decision"}})
    one = lambda name: [{"id": "a", "values": [{"name": name}]}, {"id": "b", "values": []}]  # noqa: E731
    assert policy.main_dimensions(v) == {"edge", "edge_len"}
    assert [policy.decision_category(v, "design_detail", one(n)) for n in ("edge", "edge_len", "price", "w")] == [
        "main_dimensions", "main_dimensions", "cost_impact", None]
    mat = [{"id": "a", "values": [], "model_definition": {"material": "PETG"}}, {"id": "b", "values": []}]
    assert policy.decision_category(v, "other", mat) == "material"
    card = {"type": "assumption", "generated": True, "subject": {"params": ["w"]}, "triggers": ["assumption"]}
    assert policy.classify_card(v, card) == ("provisional", None)
    assert policy.classify_card(v, {**card, "checks": [{"rule": "X", "result": "warn"}]}) == (
        "hold", "deviation_from_standard")
    assert policy.level(v, {**card, "subject": {"params": ["wall"]}}) == "hold"           # assumed safety value
    assert policy.level(v, {**card, "subject": {"params": ["edge"]}}) == "hold"
    assert policy.level(v, {"type": "gate", "generated": False, "level": "hold"}) == "hold"
    assert policy.level(v, {"type": "question", "generated": False, "level": "hold"}) == "hold"   # kept by hand
    assert policy.level(v, {"type": "policy_suggestion", "generated": True}) == "witness"


def test_cards_take_their_level_from_the_policy(tmp_path):
    """2.3: D1 — G-31 lifted: generated cards get the policy level, a stop card its category (card schema valid)"""
    v = _work(tmp_path, params={**PARAMS, "free": {"value": 1.0, "unit": "mm", "source": "assumption",
                                                   "critical": "interface", "rationale": "r"},
                                "loose": {"value": 1.0, "unit": "mm"}})
    cards = {c["key"]: c for c in generate(v, runner.run(v))}
    assert cards["assumption:free"]["level"] == "provisional" and cards["assumption:wall"]["level"] == "hold"
    assert (cards["unsourced:loose"]["level"], cards["unsourced:loose"]["stop_category"]) == (
        "hold", "deviation_from_standard")
    sync(v, list(cards.values()))
    assert {c["id"] for c in load_work(tmp_path).cards} == {c["id"] for c in cards.values()}   # files valid


def test_revert_rate_above_the_threshold_opens_a_suggestion_card_and_leaves_the_config(tmp_path):
    """2.3: D6 — 2 of 3 provisional decisions of a category reverted (67 % > 20 %, T-06) → a witness card
    `policy:design_detail`; the workshop config is not changed, neither by the card nor by its sync"""
    cfg = Path(os.environ["MEKANIK_CONFIG_DIR"]) / "config.yaml"
    before = cfg.read_bytes()
    decs = [_prov("K-01", status="reverted"), _prov("K-02", status="reverted"), _prov("K-03")]
    v = _work(tmp_path, decisions=decs)
    assert metrics.revert_rates(v)["design_detail"] == {"n": 3, "reverted": ["K-01", "K-02"], "rate": 2 / 3}
    cards = generate(v, runner.run(v))
    (s,) = [c for c in cards if c["type"] == "policy_suggestion"]
    assert s["key"] == "policy:design_detail" and s["level"] == "witness" and s["subject"]["policy"] == "design_detail"
    assert s["triggers"] == ["policy.revert_rate"] and s["subject"]["reverted"] == ["K-01", "K-02"]
    sync(v, cards)
    assert cfg.read_bytes() == before and "design_detail" not in policy.stop_categories()


def test_no_suggestion_at_the_threshold_or_for_a_stop_category(tmp_path, monkeypatch):
    """2.3: D6 — 1 of 5 reverted (20 %, not above) gives no card; a category already on the stop list neither"""
    decs = [_prov("K-01", status="reverted")] + [_prov(f"K-0{i}") for i in range(2, 6)]
    v = _work(tmp_path, decisions=decs)
    assert metrics.revert_rates(v)["design_detail"]["rate"] == 0.2 and metrics.suggestions(v) == []
    monkeypatch.setattr(metrics, "number", lambda name: {"revert_rate_threshold": 0.1, "revert_window": 10}[name])
    assert [c["key"] for c in metrics.suggestions(v)] == ["policy:design_detail"]
    monkeypatch.setattr(metrics, "stop_categories", lambda: (*TEN, "design_detail"))
    assert metrics.suggestions(v) == []


def test_revert_window_counts_only_the_last_decisions(tmp_path, monkeypatch):
    """2.3: D6 — the rate is over the last `revert_window` provisional decisions of the category (by opening)"""
    decs = [_prov("K-01", status="reverted", opened="2026-11-06T09:00:00+03:00")] + [
        _prov(f"K-0{i}", opened=f"2026-11-06T1{i}:00:00+03:00") for i in range(2, 5)]
    monkeypatch.setattr(metrics, "number", lambda name: {"revert_window": 3}[name])
    assert metrics.revert_rates(_work(tmp_path, decisions=decs))["design_detail"]["rate"] == 0.0


def test_stage_measures(tmp_path):
    """2.3: D5 — the measures of §8.2 from the records: hold questions of the stage and their answer time,
    provisional decisions made and reverted in the stage, the revert rate per category, the question limit (T-06)"""
    decs = [_prov("K-01", status="reverted", opened="2026-11-06T11:00:00+03:00"), _prov("K-02"),
            _prov("K-03", opened="2026-11-05T10:00:00+03:00")]
    decs[0]["history"][0]["at"] = "2026-11-06T12:00:00+03:00"
    v = _work(tmp_path, decisions=decs)
    v.approvals = [{"card": "S-01", "action": "approve", "at": "2026-11-06T10:30:00+03:00"}]
    cards = [{"id": "S-01", "level": "hold", "type": "assumption", "opened_at": "2026-11-06T10:10:00+03:00"},
             {"id": "S-02", "level": "provisional", "type": "assumption", "opened_at": "2026-11-06T10:10:00+03:00"},
             {"id": "O-G1", "level": "hold", "type": "gate", "opened_at": "2026-11-06T10:10:00+03:00"}]
    m = metrics.stage(v, "G1", cards)
    assert [m[k] for k in ("questions_asked", "questions_limit", "provisional_made", "provisional_reverted")] == [
        1, 5, 2, 1]
    assert m["time_to_answer"] == {"S-01": 20} and m["revert_rate"] == {"design_detail": round(1 / 3, 3)}
    assert "G1" in metrics.line(m)


# --- SOURCE-02, CALC-03, CALC-04, REQ-01: passing and failing subcases; the fakes must not pass -------------------

def _rec(magnitudes=(), zone="validation", reads=(), note="none_available", inputs=()):
    return {"magnitudes": [{"name": n, "value": x, "unit": "N", "level": lv, "method": m}
                           for n, x, lv, m in magnitudes],
            "results": [{"name": "r", "value": 1.0, "unit": "N", "status": "ok", **(
                {"uncertainty_note": note} if note else {})}], "inputs": list(inputs), "read_calculations": list(reads),
            "validity": {"zone": zone, "in_domain": {"outside": False, "undefined": None}.get(zone, True)}}


CALCS = {"h_ok": _rec([("f", 10.0, 1, "el")]), "h_ok2": _rec([("f", 10.5, 2, "FEA")]),
         "h_out": _rec([("g", 5.0, 1, "el")], zone="outside"), "h_dis": _rec([("k", 1.0, 1, "el")]),
         "h_dis2": _rec([("k", 2.0, 3, "ölçüm")]), "h_same": _rec([("k", 1.01, 1, "el")], reads=["h_dis"]),
         "h_quiet": _rec([], note=None)}
REQS = [{**REQ, "evaluation": {"status": "met", "at": "G5", "evidence": [{"kind": "calculation", "id": "h_ok"}]}},
        {**REQ, "id": "R-02", "evaluation": {"status": "met", "at": "G5", "evidence": [
            {"kind": "calculation", "id": "h_out"}]}},
        {**REQ, "id": "R-03", "evaluation": {"status": "met", "at": "G5", "evidence": [
            {"kind": "calculation", "id": "h_dis"}]}},
        {**REQ, "id": "R-04", "kind": "wish", "evaluation": {"status": "met", "at": "G5", "evidence": [
            {"kind": "calculation", "id": "h_quiet"}]}}]
CODE = {"model/model.py": "def parts(p):\n    return {'a': p.w * 3.7, 'b': p.w / 2, 'c': p.edge[0]}\n",
        "calcs/clean.py": 'ID = "clean"\n\n\ndef calculate(c, m):\n    g = c.const("g", 9.81, "m/s", "standard:x")\n'
                          '    c.magnitude("f", g * 2, "N", 3, "el")\n    c.result("r", 0.5 * g, "N")\n'}
EXPECTED = {"subcases": [
    {"id": "source02", "expect": [{"check": "source_code", "ref": "model/model.py", "result": "block"},
                                  {"check": "source_code", "ref": "calcs/clean.py", "result": "pass"}]},
    {"id": "calc03", "expect": [{"check": "calc_cross_check", "ref": "h_ok", "result": "pass"},
                                {"check": "calc_cross_check", "ref": "h_out", "result": "block"},
                                {"check": "calc_cross_check", "ref": "h_dis", "result": "block"}]},
    {"id": "calc04", "expect": [{"check": "calc_validity", "ref": "h_ok", "result": "pass"},
                                {"check": "calc_validity", "ref": "h_out", "result": "block"},
                                {"check": "calc_validity", "ref": "h_quiet", "result": "block"}]},
    {"id": "req01", "expect": [{"check": "requirements_met", "ref": "R-01", "result": "pass"},
                               {"check": "requirements_met", "ref": "R-02", "result": "block"}]}]}
SPECS = [*source_code.CHECKS, *assurance.CHECKS]


@pytest.fixture
def case(tmp_path):
    _work(tmp_path, stage="G5", reqs=REQS, calcs=CALCS, files=CODE)
    yamlio.write(tmp_path / "expected.yaml", EXPECTED)
    return tmp_path


def _always(spec, status):
    return replace(spec, run=lambda *a, **kw: [replace(r, status=status) for r in spec.run(*a, **kw)])


def test_new_checks_pass_and_fail_their_subcases(case):
    """2.5: F3, F5 — SOURCE-02 blocks an unsourced constant at finalizing (const() argument, method level and
    index are not counted), CALC-03 passes an agreeing independent pair and blocks a missing or disagreeing second
    method, CALC-04 blocks a result outside its domain or without an uncertainty statement, REQ-01 blocks at G5 a
    mandatory requirement whose only evidence is refused"""
    out = regress.run_case(case, SPECS)
    assert [s.id for s in out] == ["source02", "calc03", "calc04", "req01"]
    assert all(s.passed for s in out), [(s.id, s.errors) for s in out if not s.passed]
    v = load_work(case)
    by = {(r.check, r.ref): r for r in runner.run(v, None, SPECS)}
    assert by[("calc_cross_check", "h_ok")].extra["with"] == "h_ok2" and by[("calc_cross_check", "h_dis")].extra[
        "status"] == "disagree" and by[("calc_cross_check", "h_out")].msg == "policy.calc03.missing"
    assert [r.value for r in runner.run(v, None, source_code.CHECKS) if r.failed] == [3.7]
    assert [x["status"] for x in assurance.requirement_table(v)] == ["met"] + ["awaiting_evidence"] * 3


@pytest.mark.parametrize("spec", SPECS, ids=lambda c: c.id)
@pytest.mark.parametrize("status", ["block", "pass"])
def test_uniform_new_check_fails_its_subcases(case, spec, status):
    """2.5: F2 for the new checks — an "always block" or "always pass" fake of each new check fails a subcase"""
    out = regress.run_case(case, [_always(c, status) if c is spec else c for c in SPECS])
    assert any(not s.passed for s in out), f"{spec.id} always {status}: still passed"


def test_source02_warns_before_finalizing_and_counts_nothing_allowed(tmp_path):
    """2.5: F3 — exploration and development warn (G1), finalizing blocks; allowed numbers and the exempt places
    give a pass; release (finalizing) needs 0 constants"""
    files = {"model/model.py": "def parts(p):\n    return p.w * 25.4\n"}
    assert [r.status for r in source_code.run(_work(tmp_path, files=files)) if r.failed] == ["warn"]
    assert [r.status for r in source_code.run(_work(tmp_path, stage="G3", files=files)) if r.failed] == ["block"]
    ok = {"model/model.py": "def parts(p):\n    return p.w * 2 + p.edge / 0.5 - 1 + 90 + p.l[3] + p.l[-4]\n"}
    assert [r.status for r in source_code.run(_work(tmp_path, stage="G5", files=ok))] == ["pass"]


def test_req01_applies_only_at_g4_and_g5(tmp_path):
    """2.5: F5 — REQ-01 is not applied before G4; at G4 and G5 an unmet mandatory requirement blocks"""
    reqs = [{**REQ, "evaluation": {"status": "not_met", "at": "G3"}}]
    assert assurance.requirements(_work(tmp_path, stage="G3", reqs=reqs)) == []
    assert [r.status for r in assurance.requirements(_work(tmp_path, stage="G5", reqs=reqs))] == ["block"]
    yamlio.write(tmp_path / "work.yaml", {**WORK, "risk_class": "A", "process": {
        **WORK["process"], "gates": ["G0", "G1", "G2", "G3", "G4", "G5"], "stage": "G4"}})
    assert [r.status for r in assurance.requirements(load_work(tmp_path))] == ["block"]


def test_critical_by_hold_basis_or_safety_input_and_extrapolation_needs_the_placard(tmp_path):
    """2.5: CALC-03 critical from a hold decision's basis and a safety-critical input; CALC-04 limits zone blocks
    without the chief's approved placard, warns with it; verification and an undefined domain warn"""
    hold = {**copy.deepcopy(EX["decision"]), "id": "K-05", "work": WORK["code"],
            "basis": [{"calculation": "h_lim", "result_hash": "a" * 16, "at": AT}]}
    calcs = {"h_lim": _rec([("f", 1.0, 1, "el")], zone="limits"), "h_ver": _rec(zone="verification"),
             "h_undef": _rec(zone="undefined"), "h_safe": _rec([("s", 1.0, 1, "el")], inputs=[
                 {"name": "wall", "quantity": {"value": 2.0, "unit": "mm", "source": "assumption"}}])}
    reqs = [{**REQ, "kind": "wish", "evaluation": {"status": "met", "at": "G1", "evidence": [
        {"kind": "calculation", "id": c}]}, "id": f"R-0{i}"} for i, c in enumerate(("h_ver", "h_undef"), 1)]
    v = _work(tmp_path, reqs=reqs, decisions=[hold], calcs=calcs)
    assert assurance.critical(v, assurance.calc.recorded(tmp_path)) == {"h_lim": "K-05", "h_safe": "safety"}
    st = {r.ref: (r.status, r.msg.rsplit(".", 1)[1]) for r in assurance.validity(v)}
    assert st == {"h_lim": ("block", "limits"), "h_ver": ("warn", "verification"), "h_undef": ("warn", "undefined")}
    calcs["h_lim"]["validity"]["placard"] = {"limit_type": "x", "extent": "y", "consequence": "z",
                                             "approved": {"kind": "card", "id": "S-01"}}
    v = _work(tmp_path, reqs=reqs, decisions=[hold], calcs=calcs)
    assert {r.ref: r.status for r in assurance.validity(v)}["h_lim"] == "warn"
