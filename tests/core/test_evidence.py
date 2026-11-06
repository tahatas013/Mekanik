# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import sys
from types import SimpleNamespace

from mekanik.core import data, yamlio
from mekanik.core.checks.result import PASS, WARN
from mekanik.core.evidence import calc, register
from mekanik.core.i18n import t
from mekanik.core.model.params import Param

CODE = "TST-SYN-01"


def _view(root, params=(), decisions=(), cards=()):
    return SimpleNamespace(root=root, code=CODE, params={p.name: p for p in params}, decisions=list(decisions),
                           cards=list(cards))


def _calcs(root, **scripts):
    (root / "calcs").mkdir(exist_ok=True)
    for name, text in scripts.items():
        (root / "calcs" / f"{name}.py").write_text(text, encoding="utf-8")


def test_analysis_needs_a_link_and_unchanged_calcs_do_not_rerun(tmp_path):
    """old: test_cekirdek::analiz_baglantisiz_olmaz_ve_onbellek"""
    ran = tmp_path / "ran.txt"
    _calcs(tmp_path,
           a='ID = "a"\nTYPE = "analysis"\nLINKS = []\ndef calculate(c, m):\n    c.result("x", 1, "")\n',
           b=f'ID = "b"\ndef calculate(c, m):\n    open({str(ran)!r}, "a").write("b")\n    c.result("y", 2, "")\n',
           c='ID = "c"\ndef calculate(c, m):\n    c.result("z", c.other("b")["results"][0]["value"] + 1, "")\n')
    view = _view(tmp_path)
    s = {r["id"]: r for r in calc.run(view)}
    assert s["a"]["error"] == "SchemaError: " + t("evidence.calc.unlinked", calc="a")
    assert s["c"]["results"][0]["value"] == 3 and s["c"]["read_calculations"] == ["b"]
    assert sorted(calc.write(view, list(s.values()))) == [f"records/calcs/{x}.json" for x in "abc"]
    again = {r["id"]: r for r in calc.run(view)}
    assert ran.read_text() == "b" and again["b"] == s["b"]          # from the cache: b did not run again
    assert calc.write(view, list(again.values())) == []
    (tmp_path / "calcs" / "b.py").write_text('ID = "b"\ndef calculate(c, m):\n    c.result("y", 5, "")\n')
    assert {r["id"]: r for r in calc.run(view)}["c"]["results"][0]["value"] == 6   # input changed: rerun


AREA = '''
ID = "area"
TITLE = "Blok alanı"
PURPOSE = "sınama"


def calculate(c, model):
    w = c.input("block_width")
    k = c.const("k", 2.0, "-", "decision")
    a = c.step("Alan", "A = w² × k", w * w * k, "mm2")
    c.result("area", a, "mm2")
    c.chart("g", [1, 2], [3, 4], "x", "y")
'''


def test_calcs_are_recorded_unsourced_constant_rejected(tmp_path):
    """old: test_akis::hesaplar_kayda_gecer_kaynaksiz_sabit_reddedilir"""
    _calcs(tmp_path, area=AREA, bad=AREA.replace('"decision")', '"assumption")').replace('"area"', '"bad"', 1)
           .replace("Blok alanı", "Bozuk"))
    view = _view(tmp_path, [Param("block_width", 20.0, "mm", "decision")])
    calc.write(view, calc.run(view))
    v = json.loads((tmp_path / "records" / "calcs" / "area.json").read_text())
    assert v["error"] is None and v["results"][0]["value"] == 800.0
    assert v["inputs"][0]["quantity"]["source"] == "decision"
    assert v["kind"] == "calculation" and v["work"] == CODE and v["result_hash"] == calc.current_hash(tmp_path, "area")
    b = json.loads((tmp_path / "records" / "calcs" / "bad.json").read_text())
    assert t("evidence.calc.bad_const", calc="bad", name="k", source="assumption") in b["error"]
    assert calc.param_users(tmp_path)["block_width"] == ["Blok alanı", "Bozuk"]   # bad read the input, then failed
    unsourced = _view(tmp_path, [Param("block_width", 20.0, "mm", None)])
    assert t("evidence.calc.no_source", calc="area", name="block_width") in calc.run(unsourced, cache=False)[0]["error"]


def test_calc_scripts_write_no_bytecode(tmp_path, monkeypatch):
    """new: Ek B §14 madde 5"""
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    _calcs(tmp_path, _helper="X = 1\n", area=AREA)
    view = _view(tmp_path, [Param("block_width", 20.0, "mm", "decision")])
    assert calc.run(view)[0]["error"] is None
    assert not list(tmp_path.rglob("__pycache__")) and not list(tmp_path.rglob("*.pyc"))
    assert sys.dont_write_bytecode is False


def _magnitudes(name, level, method, sm, cl, status):
    return (f'ID = "{name}"\ndef calculate(c, m):\n    c.magnitude("sm", {sm}, "-", {level}, "{method}")\n'
            f'    c.magnitude("balance_cl", {cl}, "-", {level}, "{method}")\n'
            f'    c.result("balance", {cl}, "", status="{status}")\n')


def _s001(tmp_path, cards=()):
    """The S-001 numbers: sm 26 % apart, balance_cl 4 % apart, a bad result; K-03 unchanged, K-04 changed."""
    _calcs(tmp_path, h_hand=_magnitudes("h_hand", 1, "hand", 0.127, 0.5, "bad"),
           h_vlm=_magnitudes("h_vlm", 2, "VLM", 0.101, 0.52, "ok"))
    calc.write(_view(tmp_path), calc.run(_view(tmp_path)))
    at = "2026-11-06T10:00:00+03:00"
    decisions = [{"id": "K-03", "status": "approved", "basis": [{"calculation": "h_vlm", "result_hash":
                                                                  calc.current_hash(tmp_path, "h_vlm"), "at": at}]},
                 {"id": "K-04", "status": "approved", "basis": [{"calculation": "h_hand", "result_hash": "0" * 16,
                                                                 "at": at}]},
                 {"id": "K-05", "status": "proposed", "basis": [{"calculation": "h_hand", "result_hash": "0" * 16,
                                                                 "at": at}]}]
    view = _view(tmp_path, decisions=decisions, cards=cards)
    return view, register.run(view)


def test_consistency_bad_result_and_decision_basis(tmp_path):
    """CALC-01, CALC-02 and DECISION-01 on the S-001 numbers (S-001 subcases hesap_tutarliligi, karar_dayanagi)."""
    view, results = _s001(tmp_path)
    by = {(r.check, r.ref): r for r in results if r.check != "schema"}
    assert by[("calc_consistency", "sm")].status == WARN and by[("calc_consistency", "balance_cl")].status == PASS
    assert by[("calc_result", "h_hand")].status == WARN and ("calc_result", "h_vlm") not in by
    assert by[("decision_basis", "K-03")].status == PASS
    k04 = by[("decision_basis", "K-04")]
    assert k04.status == WARN and k04.extra["changed"] == ["h_hand"] and k04.extra["superseded"] == ["h_hand"]
    assert ("decision_basis", "K-05") not in by   # a proposed decision has no basis to lose yet
    assert {r.msg for r in results if r.check == "schema"} == {"schema.warning"}   # phase-1 fields (G-27)
    cards = {c["key"]: c for c in register.make_cards(view, results)}
    assert set(cards) == {"consistency:sm", "basis:K-04"}
    c = cards["consistency:sm"]
    assert c["type"] == "consistency" and c["triggers"] == ["consistency"] and c["level"] == "hold"
    assert c["subject"] == {"magnitude": "sm", "results": {"h_vlm": 0.101, "h_hand": 0.127}}
    assert all(c[f] for f in ("question", "explain", "if_approved", "if_rejected", "recorded_as", "title"))
    assert c["proposal"]["choice"] and c["proposal"]["rationale"] and c["checks"][0]["rule"] == "CALC-01"
    b = cards["basis:K-04"]
    assert b["type"] == "basis_changed" and b["triggers"] == ["decision_basis"] and b["subject"]["decision"] == "K-04"


def test_accepted_consistency_passes_while_values_hold(tmp_path, monkeypatch):
    """The chief engineer's approval of the consistency card turns CALC-01 into a pass; the card stays."""
    seen = []
    monkeypatch.setattr(register.approval, "state", lambda view, cid, subj: seen.append((cid, subj)) or "approved")
    view, results = _s001(tmp_path, cards=[{"id": "S-01", "key": "consistency:sm"}])
    sm = next(r for r in results if r.check == "calc_consistency" and r.ref == "sm")
    assert sm.status == PASS and sm.extra["accepted"] == "S-01"
    assert seen == [("S-01", {"magnitude": "sm", "results": {"h_vlm": 0.101, "h_hand": 0.127}})]
    card = next(c for c in register.make_cards(view, results) if c["key"] == "consistency:sm")
    assert card["title"] == t("evidence.card.consistency.accepted_title", name="sm")


def test_evidence_rules_are_bound_to_code(tmp_path):
    """new: Ek B §14 madde 11"""
    catalog = {r["id"]: r for r in yamlio.read(data.stdlib("rules", "evidence.yaml"))["rules"]}
    assert set(catalog) == {r for c in register.CHECKS for r in c.rules}
    view, results = _s001(tmp_path, cards=[{"id": "O-G1", "type": "gate", "status": "open"}])
    results += register.quality_gate(view)
    assert {r.rule for r in results} - {"SCHEMA-01"} == set(catalog)
    assert {r["check"] for r in catalog.values()} == {r.check for r in results} - {"schema"}
    assert all(r.get("basis") and r.get("text") for r in catalog.values())
    assert catalog["CALC-01"]["limit"]["relative"] == 0.10 and catalog["CALC-01"]["limit_source"]
