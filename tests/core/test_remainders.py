# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wave 2.2 remainders of the core, without git (OCCT-free): the policy suggestion card's figure (D6), the calc API's
validity domain and critical flag (architecture §4.5, §10.2, §10.3) as CALC-03 and CALC-04 read them, the release
request's basis counted critical, and the main-dimension check outside a repository. The flows with git are in
tests/flow/test_remainders_flow.py."""

from __future__ import annotations

from test_policy import PARAMS, REQ, _prov, _registry, _work  # noqa: F401  (fixture)

from mekanik.core import yamlio
from mekanik.core.cards import generate, missing_fields
from mekanik.core.checks import runner
from mekanik.core.checks.builtin import approval as approval_checks, assurance, cards as card_checks
from mekanik.core.evidence import calc
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.core.process.step import _attach, core_figures

HEAD = 'ID = "{id}"\n{extra}\n\ndef calculate(c, model):\n    w = c.input("w")\n'
FORCE = HEAD + '    c.magnitude("f", {x}, "N", {level}, "{method}")\n    c.result("f", {x}, "N")\n'
DOMAIN = '    c.validity([{{"name": "w", "min": {lo}, "max": {hi}, "source": "manufacturer:x", ' \
         '"region": "validation"}},' \
         ' {{"name": "w", "min": 0, "max": 100, "source": "manufacturer:x", "region": "limits"}}]{more})\n'


def _calcs(tmp, **scripts) -> dict:
    for name, text in scripts.items():
        yamlio.write_text(tmp / "calcs" / f"{name}.py", text)
    view = load_work(tmp)
    calc.write(view, recs := calc.run(view))
    return {r["id"]: r for r in recs}


def test_policy_suggestion_card_gets_a_text_figure_without_a_model(tmp_path):
    """2.3: D6 — the threshold suggestion (a config matter) is drawn from its numbers, so it meets the card standard
    (CARD-01) in a work without a model"""
    decs = [_prov("K-01", status="reverted"), _prov("K-02", status="reverted"), _prov("K-03")]
    v = _work(tmp_path, decisions=decs)
    cards = generate(v, results := runner.run(v))
    (s,) = [c for c in cards if c["type"] == "policy_suggestion"]
    ((title, svg),) = core_figures(s, None, results)
    assert title == t("process.visual.policy") and "design_detail" in svg and "K-01, K-02" in svg
    _attach(v, None, cards, results, yamlio.Txn())
    assert s["visuals"] and "visuals" not in missing_fields(s)
    assert not [r for r in card_checks.standard(v, None, [s], opened_only=False) if r.status == "block"]


def test_validity_domain_sets_the_zone_and_the_placard(tmp_path):
    """2.5: §10.3 — `validity(domain=…)`: inside the validation range → validation; only inside the limits →
    limits with the placard (limit type, extent, consequence); outside every range → outside and every result
    unreliable; no domain → undefined; a domain name the calc does not know is the calc's error"""
    _work(tmp_path)   # w = 20 mm
    recs = _calcs(tmp_path, a_in=HEAD.format(id="a_in", extra="") + DOMAIN.format(lo=10, hi=30, more="") +
                  '    c.result("r", w, "mm")\n',
                  b_lim=HEAD.format(id="b_lim", extra="") + DOMAIN.format(lo=1, hi=5, more=', consequence="büyük"') +
                  '    c.result("r", w, "mm", status="ok")\n',
                  c_out=HEAD.format(id="c_out", extra="") + '    c.validity([{"name": "w", "max": 4, "source": '
                  '"manufacturer:x"}])\n    c.result("r", w, "mm", status="ok")\n',
                  d_none=HEAD.format(id="d_none", extra="") + '    c.result("r", w, "mm")\n',
                  e_bad=HEAD.format(id="e_bad", extra="") + '    c.validity([{"name": "x", '
                  '"source": "manufacturer:y"}])\n')
    v = {k: r["validity"] for k, r in recs.items()}
    assert (v["a_in"]["zone"], v["a_in"]["in_domain"]) == ("validation", True) and "placard" not in v["a_in"]
    assert v["b_lim"]["zone"] == "limits" and v["b_lim"]["placard"] == {
        "limit_type": "verification", "extent": "w = 20.0 (verification)", "consequence": "büyük"}
    assert (v["c_out"]["zone"], v["c_out"]["in_domain"], v["c_out"]["out_of_domain"]) == ("outside", False, ["w"])
    assert [r["status"] for r in recs["c_out"]["results"]] == ["unreliable"]
    assert (v["d_none"]["zone"], v["d_none"]["in_domain"]) == ("undefined", None)
    assert recs["e_bad"]["error"].startswith("SchemaError") and recs["e_bad"]["validity"]["zone"] == "undefined"


def test_calc04_reads_the_recorded_zone(tmp_path):
    """2.5: CALC-04 — a calc used as evidence is judged by the zone its run recorded (validity domain)"""
    reqs = [{**REQ, "kind": "wish", "id": f"R-0{i}", "evaluation": {"status": "met", "at": "G1", "evidence": [
        {"kind": "calculation", "id": c}]}} for i, c in enumerate(("a_in", "c_out"), 1)]
    _work(tmp_path, reqs=reqs)
    _calcs(tmp_path, a_in=HEAD.format(id="a_in", extra="") + DOMAIN.format(lo=10, hi=30, more="") +
           '    c.result("r", w, "mm")\n',
           c_out=HEAD.format(id="c_out", extra="") + DOMAIN.format(lo=1, hi=2, more="").replace("100", "3") +
           '    c.result("r", w, "mm")\n')
    got = {r.ref: (r.status, r.msg) for r in assurance.validity(load_work(tmp_path))}
    assert got == {"a_in": ("pass", "policy.calc04.validation"), "c_out": ("block", "policy.calc04.outside")}


def test_critical_calc_records_its_second_method(tmp_path):
    """2.5: §10.2 — `CRITICAL = True` makes the calc critical (record `critical`, CALC-03 'declared'); its record
    names the second method (cross_check with the catalog's tolerance): agreeing, disagreeing or missing"""
    _work(tmp_path)
    recs = _calcs(tmp_path, h1=FORCE.format(id="h1", extra="CRITICAL = True", x=10.0, level=1, method="el"),
                  h2=FORCE.format(id="h2", extra="", x=10.5, level=2, method="FEA"),
                  k1=FORCE.format(id="k1", extra="CRITICAL = True", x=1.0, level=1, method="el").replace('"f"', '"k"'),
                  k2=FORCE.format(id="k2", extra="", x=2.0, level=3, method="ölçüm").replace('"f"', '"k"'),
                  m1=FORCE.format(id="m1", extra="CRITICAL = True", x=1.0, level=1, method="el").replace('"f"', '"m"'))
    assert recs["h1"]["critical"] and "critical" not in recs["h2"]
    x = recs["h1"]["cross_check"]
    assert (x["with"], x["magnitude"], x["status"], x["tolerance"]["value"]) == ("h2", "f", "agree", 0.10)
    assert recs["k1"]["cross_check"]["status"] == "disagree" and recs["m1"]["cross_check"] == {
        "with": "none", "tolerance": {"value": 0.10, "unit": "-", "source": "decision", "decided_by": "chief_engineer"},
        "status": "missing"}
    v = load_work(tmp_path)
    assert {k: w for k, w in assurance.critical(v, calc.recorded(tmp_path)).items()} == {
        "h1": "declared", "k1": "declared", "m1": "declared"}
    assert {r.ref: r.status for r in assurance.cross(v)} == {"h1": "pass", "k1": "block", "m1": "block"}


def test_release_basis_is_critical(tmp_path):
    """2.5: §10.2 — a calc a release request rests on (its card's subject.basis) is critical: CALC-03 asks for its
    second method and CALC-04 judges its domain; a withdrawn request no longer counts"""
    _work(tmp_path)
    _calcs(tmp_path, h1=FORCE.format(id="h1", extra="", x=1.0, level=1, method="el"))
    card = {"id": "B-01", "type": "release", "status": "open", "subject": {"release": "01", "basis": ["h1"]}}
    v = load_work(tmp_path)
    assert assurance.critical(v, calc.recorded(tmp_path)) == {}
    v.cards = [card]
    assert assurance.critical(v, calc.recorded(tmp_path)) == {"h1": "B-01"}
    assert [(r.ref, r.status) for r in assurance.cross(v)] == [("h1", "block")]
    assert [(r.ref, r.status) for r in assurance.validity(v)] == [("h1", "warn")]   # domain undefined
    v.cards = [{**card, "status": "withdrawn"}]
    assert assurance.critical(v, calc.recorded(tmp_path)) == {}


def test_main_dimension_check_needs_the_history(tmp_path):
    """2.3: KM-19 — MAINDIM-01 judges the commits that changed a mark; outside a repository it gives no result (the
    flow with the chief's signed commit is in tests/cli/test_phase2_commands.py)"""
    assert approval_checks.main_dimension(_work(tmp_path, params=PARAMS)) == []


def test_new_rule_is_in_the_catalog_with_its_basis():
    """2.3: KM-19 — the rule is in stdlib/rules/core.yaml with its basis and its check"""
    from mekanik.core.checks import rules

    r = rules.rule("MAINDIM-01")
    assert r["check"] == "main_dimension" and "KM-19" in r["basis"] and r["file"] == "core.yaml"
