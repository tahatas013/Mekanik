# SPDX-License-Identifier: AGPL-3.0-or-later
"""Flows with a model (old test_akis, K2 acceptance): G0 to G3 with tags, decisions and their branches, the release
hold, the card standard, undo, quality review before a release. Needs OCCT (CadQuery) and the mech package."""

from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("cadquery")

from test_store import CHIEF, PARAMS, REQUIREMENTS, log_entries, new, prepare, review  # noqa: E402

from mekanik.core import quality, yamlio  # noqa: E402
from mekanik.core.checks import runner  # noqa: E402
from mekanik.core.checks.result import BLOCK, Result  # noqa: E402
from mekanik.core.decisions import open_decision, option_values  # noqa: E402
from mekanik.core.errors import MekanikError  # noqa: E402
from mekanik.core.i18n import t  # noqa: E402
from mekanik.core.evidence import cache  # noqa: E402
from mekanik.core.model.work import load_work  # noqa: E402
from mekanik.core.process import Refused, chief, gates, release  # noqa: E402
from mekanik.core.process.step import RECORDS, evaluate, step  # noqa: E402
from mekanik.core.store import git  # noqa: E402
from mekanik.plugins import registry  # noqa: E402

pytestmark = pytest.mark.occt
MODEL = '''import cadquery as cq


def parts(p):
    return {"blok": cq.Workplane().box(p.blok_en, p.blok_en, p.blok_kalinlik).val()}
'''
TEXT = {"question": "Hangisi?", "explain": "sınama kararı", "proposal": "a", "proposal_rationale": "sınama",
        "requirement_effects": [{"requirement": "R-01", "effect": "blok yazıcıya sığar (değişmez)"}]}
CALC = 'ID = "{id}"\nX = {x}\n\n\ndef calculate(h, model):\n    h.magnitude("x", X, "-", {level}, "{method}")\n' \
       '    h.result("x", X, "-")\n'


def option_status(d: dict, oid: str) -> str:
    """Derived from the decision record (old seçenek durumu): open | approved | not_chosen | rejected."""
    if d.get("chosen"):
        return "approved" if d["chosen"] == oid else "not_chosen"
    return "rejected" if d.get("status") == "rejected" else "open"


def _sec(**names):
    """Options, each different in the model (blok_en), so that their drawings differ (card standard)."""
    return {k: {"title": v, "values": {"blok_en": 20.0 + 4 * i}} for i, (k, v) in enumerate(names.items())}


def _card(d, cid):
    return next(c for c in evaluate(d)[3] if c["id"] == cid)


def _decision(d, did="K-01"):
    return next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == did)


def _tags(d):
    return set(git.git("tag", "--list", cwd=d).split())


def _n(d):
    return len(yamlio.read(d / "approvals.yaml", []) or [])


def _g0(cls="C", **kw):
    code, d = new(cls, **kw)
    prepare(d, model=MODEL)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    return code, d


def _option_work(d, tmp_path, code, opt, thickness):
    """A step on the option's own branch, in its own worktree."""
    wt = tmp_path / f"wt-{opt}"
    git.git("worktree", "add", "-q", str(wt), f"{code}/decision/K-01-{opt}", cwd=d)
    wd = wt / "sentetik" / code
    yamlio.write(wd / "params.yaml", {**PARAMS, "blok_kalinlik": {**PARAMS["blok_kalinlik"], "value": thickness}})
    step(wd, f"seçenek {opt}", "design_engineer")
    return git.git("rev-parse", f"{code}/decision/K-01-{opt}", cwd=d)


def test_g0_to_g3_with_tags_and_log(shop):
    """old: test_akis::g0_dan_g3_e_ilerler_ve_gunlukte_gorunur"""
    code, d = new()
    prepare(d, model=MODEL)
    s = step(d, "G0: istek listesi ve model iskeleti", "project_engineer", "ilk adım")
    body = log_entries(d)[0]["body"]
    assert "![" in body and s["visuals"] and (d / s["visuals"][0]).read_text().count("<svg")
    assert git.trailers(git.git("log", "-1", "--format=%B", s["commit"], cwd=d))["Step"].startswith("G0")
    review(d)
    assert all(x["ok"] for x in gates.stage_finish(d, "G0")["items"])
    chief.approve(d, "O-G0")
    assert f"{code}-G0" in _tags(d) and load_work(d).stage == "G1"
    open_decision(d, "K-01", "Kavram", _sec(a="tek blok", b="iki blok", c="çerçeve"), "sınama", concept=True,
                  branched=False, **TEXT)
    chief.approve(d, "K-01", option="a")
    review(d)
    lst = gates.stage_finish(d, "G1")["items"]
    assert {x["id"]: x["ok"] for x in lst} == {"three_options": True, "weights_by_chief": False,
                                               "choice_recorded": True}
    chief.approve(d, "O-G1")
    assert load_work(d).stage == "G3"                               # no G2 in class C
    for c in evaluate(d)[3]:
        if c["status"] == "open" and not c["id"].startswith("O-"):
            chief.approve(d, c["id"])
    review(d)
    gates.stage_finish(d, "G3")
    chief.approve(d, "O-G3")
    assert {f"{code}-G0", f"{code}-G1", f"{code}-G3"} <= _tags(d)
    v = load_work(d)
    assert v.stage == "G5" and v.doc["process"]["gate_status"]["G3"]["status"] == "done"
    main = git.git("log", "--first-parent", "--format=%B%x1e", f"{code}/main", cwd=d).split("\x1e")
    steps = [git.trailers(b).get("Step") for b in main[:3]]
    assert steps == [t("process.gate.done", gate=g) for g in ("G3", "G1", "G0")]
    assert len(main) == 6                       # three gate merges, the opening, the code, the repo's first commit


def test_g3_block_no_tag(shop):
    """old: test_akis::g3_engel_varken_etiket_konmaz"""
    code, d = new()
    prepare(d, model=MODEL, params={**PARAMS, "blok_en": {"value": 20.0, "unit": "mm"}})   # unsourced → block
    doc = yamlio.read(d / "work.yaml")
    doc["process"]["stage"] = "G3"
    yamlio.write(d / "work.yaml", doc)
    step(d, "kaynaksız değer", "design_engineer")
    review(d)
    gates.stage_finish(d, "G3")
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G3")
    assert e.value.key == "process.gate.required_failed" and f"{code}-G3" not in _tags(d)


def test_rejected_decision_touches_only_its_own_branches(shop, tmp_path):
    """old: test_akis::reddedilen_karar_yalniz_kendi_dalini_etkiler"""
    code, d = new("B")
    prepare(d, model=MODEL)
    step(d, "taban", "project_engineer")
    open_decision(d, "K-01", "Blok kalınlığı", _sec(a="5 mm", b="8 mm"), "dayanım", dependents=["blok"], **TEXT)
    heads = {o: _option_work(d, tmp_path, code, o, x) for o, x in (("a", 5.5), ("b", 8.0))}
    params, main = (d / "params.yaml").read_text(), git.git("rev-parse", f"{code}/main", cwd=d)
    out = chief.approve(d, "K-01", "reject", "kalınlık yetmez")    # one card: rejection rejects every option
    aff = out["decision"]["affected"]
    assert any("seçenek b" in x for x in aff["b"]) and not any("seçenek a" in x for x in aff["b"])
    assert {o: git.git("rev-parse", f"{code}/decision/K-01-{o}", cwd=d) for o in "ab"} == heads   # nothing deleted
    assert git.git("rev-parse", f"{code}/main", cwd=d) == main and (d / "params.yaml").read_text() == params
    k = _decision(d)
    assert [option_status(k, o["id"]) for o in k["options"]] == ["rejected", "rejected"] and k["status"] == "rejected"


def test_release_is_a_hold_tag_and_out_after_approval(shop):
    """old: test_akis::baski_hold_onaydan_sonra_etiket_ve_cikti"""
    code, d = new()
    prepare(d, model=MODEL)
    review(d)
    s = release.release_request(d)
    assert s["no"] == "01" and f"{code}-release-01" not in _tags(d) and not (d / "out" / f"{code}-release-01").exists()
    chief.approve(d, "B-01")
    out = d / "out" / f"{code}-release-01"
    assert f"{code}-release-01" in _tags(d) and (out / f"{code}.step").exists() and (out / "report.md").exists()


def test_card_number_is_not_reused_across_branches(shop):
    """old: test_akis::kart_numarasi_dallar_arasinda_tekrar_kullanilmaz"""
    code, d = _g0()
    open_decision(d, "K-01", "ilk", _sec(a="x", b="y"), "g", **TEXT)
    git.git("checkout", "-q", "-b", f"{code}/work/baska", f"{code}/main", cwd=d)
    with pytest.raises(Refused) as e:
        open_decision(d, "K-01", "ikinci", _sec(a="x", b="y"), "g", **TEXT)
    assert e.value.key == "process.decision.used"


def test_every_team_step_has_a_figure(shop):
    """old: test_akis::ekip_adimlarinin_hepsi_gorselli"""
    code, d = _g0()
    open_decision(d, "K-01", "karar", _sec(a="x", b="y"), "g", **TEXT)
    team = [e for e in log_entries(d) if e["role"] != "Baş mühendis"]
    assert team and all("![" in e["body"] and "sınır kutusu" in e["body"] for e in team), [e["title"] for e in team]


def test_approved_option_branch_merges_into_the_work_branch(shop, tmp_path):
    """old: test_akis::onaylanan_karar_dali_is_dalina_birlesir"""
    code, d = _g0()
    open_decision(d, "K-01", "kalınlık", _sec(a="5", b="7"), "g", **TEXT)
    _option_work(d, tmp_path, code, "b", 7.0)
    with pytest.raises(Refused) as e:
        chief.approve(d, "K-01")                                   # no approval without an option
    assert e.value.key == "process.approve.option"
    assert chief.approve(d, "K-01", option="b")["merge"] == "merged"
    assert yamlio.read(d / "params.yaml")["blok_kalinlik"]["value"] == 7.0
    k = _decision(d)
    assert _card(d, "K-01")["status"] == "approved" and [option_status(k, o["id"]) for o in k["options"]] == [
        "not_chosen", "approved"]


def test_no_release_while_a_block(shop):
    """old: test_akis::engel_varken_baski_istenmez"""
    code, d = _g0()
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_en": {"value": 20.0, "unit": "mm"}})
    with pytest.raises(Refused) as e:
        release.release_request(d)
    assert e.value.key == "process.release.blocked" and any(r.rule == "SOURCE-01" for r in e.value.data["results"])


def test_partial_step_on_a_dirty_tree_writes_no_wrong_model_to_the_cache(shop):
    """old: test_akis::kirli_agacta_kismi_adim_onbellege_yanlis_model_yazmaz"""
    code, d = new()
    prepare(d, model=MODEL)
    first, hooks = step(d, "ilk model", "project_engineer"), registry().model_hooks()
    tess = cache.root() / hooks.signature(d, first["commit"]) / "tessellation.json"
    before = tess.read_bytes()
    (d / "model" / "model.py").write_text(MODEL.replace("p.blok_en, p.blok_en", "p.blok_en * 2, p.blok_en"))
    s = step(d, "yalnız kayıt", "project_engineer", paths=RECORDS)
    assert hooks.signature(d, s["commit"]) == hooks.signature(d, first["commit"])   # the commit's model is the same
    assert tess.read_bytes() == before and not (cache.root() / s["commit"] / "check.json").exists()


def test_card_standard_stops_a_step_without_text_or_figure(shop):
    """old: test_akis::kart_standardi_metinsiz_karar_ve_izsiz_varsayim_adimi_durdurur"""
    code, d = _g0()
    head = git.head(d)
    with pytest.raises(Refused) as e:
        open_decision(d, "K-01", "metinsiz", _sec(a="x", b="y"), "g", branched=False)
    miss = next(r for r in e.value.data["results"] if r.ref == "K-01").extra["missing"]
    assert {"question", "explain", "proposal"} <= set(miss)
    assert git.head(d) == head and not git.git("status", "--porcelain", "--", str(d), cwd=d)   # nothing left behind
    with pytest.raises(Refused) as e:                                # options that do not differ in the model
        open_decision(d, "K-01", "ayrışmayan", {"a": "x", "b": "y"}, "g", branched=False, **TEXT)
    assert "visuals" in next(r for r in e.value.data["results"] if r.ref == "K-01").extra["missing"]
    open_decision(d, "K-01", "metinli", _sec(a="x", b="y"), "g", branched=False, **TEXT)   # the number was not spent
    doc = yamlio.read(path := d / "cards" / "K-01.yaml")
    yamlio.write(path, {**doc, "status": "closed"})                  # a card file cannot close an open decision
    assert _card(d, "K-01")["status"] == "open"
    git.git("checkout", "-q", "--", str(path), cwd=d)
    yamlio.write(d / "params.yaml", {**PARAMS, "bos": {"value": 3.0, "unit": "mm", "source": "assumption",
                                                       "rationale": "g"}})
    with pytest.raises(Refused) as e:                                # no trace in the model → V-01 cannot open
        step(d, "kullanılmayan ölçü", "project_engineer")
    assert "untraced:bos" in next(r for r in e.value.data["results"] if r.ref == "V-01").extra["missing"]
    params = {**PARAMS, "blok_en": {**PARAMS["blok_en"], "source": "assumption"}}
    yamlio.write(d / "params.yaml", params)
    with pytest.raises(Refused) as e:                                # an assumption without a rationale
        step(d, "gerekçesiz varsayım", "project_engineer")
    assert "rows:blok_en:rationale" in next(r for r in e.value.data["results"] if r.ref == "V-01").extra["missing"]
    params["blok_en"]["rationale"] = "yazıcıya rahat sığar"
    yamlio.write(d / "params.yaml", params)
    step(d, "gerekçeli varsayım", "project_engineer")
    v = yamlio.read(d / "cards" / "V-01.yaml")
    assert (d / v["visuals"][0]["path"]).read_text().count("<svg")
    assert v["rows"][0]["param"] == "blok_en" and v["rows"][0]["rationale"] == "yazıcıya rahat sığar"
    chief.approve(d, "V-01", rows=["blok_en"])
    assert _card(d, "V-01")["status"] == "approved"


def test_withdrawn_request_and_undone_decision(shop):
    """old: test_akis::istek_geri_cekilir_onay_geri_alinir"""
    code, d = _g0()
    review(d)
    b = release.release_request(d, purpose="sınama")
    with pytest.raises(Refused) as e:
        release.withdraw(d, "O-G0", "x")
    assert e.value.key == "process.withdraw.only_release"
    release.withdraw(d, f"B-{b['no']}", "eski model")
    k = _card(d, f"B-{b['no']}")
    assert k["status"] == "withdrawn" and "eski model" in k["closed_reason"]
    with pytest.raises(Refused) as e:
        chief.approve(d, f"B-{b['no']}")
    assert e.value.key == "process.approve.closed"
    open_decision(d, "K-01", "biçim", _sec(a="x", b="y"), "g", branched=False, **TEXT)
    chief.approve(d, "K-01", option="b")
    n = _n(d)
    chief.undo(d, "K-01", "yanlış tıklama")
    recs = yamlio.read(d / "approvals.yaml")
    assert len(recs) == n + 1 and recs[-1]["action"] == "undo" and recs[-2]["action"] == "approve"
    k = _decision(d)
    assert "chosen" not in k and k["status"] == "proposed" and k["history"][-1]["event"] == "undone"
    assert _card(d, "K-01")["status"] == "open"


def test_merged_option_cannot_be_undone_a_row_can(shop, tmp_path):
    """old: test_akis::birlesmis_secenegin_onayi_geri_alinmaz_satir_geri_alinir"""
    code, d = _g0()
    open_decision(d, "K-01", "kalınlık", _sec(a="5", b="7"), "g", **TEXT)
    _option_work(d, tmp_path, code, "b", 7.0)
    assert chief.approve(d, "K-01", option="b")["merge"] == "merged"
    with pytest.raises(Refused) as e:
        chief.undo(d, "K-01", "yanlış tıklama")
    assert e.value.key == "process.undo.merged"
    p = yamlio.read(d / "params.yaml")
    p["blok_en"].update(source="assumption", rationale="yazıcıya sığar")
    yamlio.write(d / "params.yaml", p)
    step(d, "varsayım", "project_engineer")
    chief.approve(d, "V-01", rows=["blok_en"])
    chief.undo(d, "V-01", "yanlış tıklama", row="blok_en")
    assert _card(d, "V-01")["rows"][0]["status"] == "open"


def test_option_definition_is_kept_in_the_record(shop):
    """old: test_akis::karar_secenek_tanimi_kayitta_durur"""
    code, d = _g0()
    open_decision(d, "K-01", "biçim", _sec(a="x", b="y"), "g", branched=False, **TEXT)
    k = _decision(d)
    assert [{v["name"]: v["quantity"]["value"] for v in o["values"]} for o in k["options"]] == [
        {"blok_en": 20.0}, {"blok_en": 24.0}]


def test_chosen_options_value_does_not_leak_into_the_other(shop):
    """old: test_akis::secilen_secenegin_olcusu_obur_secenege_sizmaz"""
    code, d = _g0()
    opts = {"a": {"title": "x", "summary": "p", "pros": ["+"], "cons": ["-"]},
            "c": {"title": "y", "values": {"blok_en": 24.0, "yeni_olcu": {"value": 5.0, "unit": "mm"}}}}
    open_decision(d, "K-01", "biçim", opts, "g", branched=False, **TEXT)
    k = _decision(d)
    assert [(v["name"], v["quantity"]["value"]) for v in k["options"][0]["values"]] == [("blok_en", 20.0)]
    v = load_work(d)
    v.params["blok_en"].value = 24.0                                # c chosen, its value went to params.yaml
    a = option_values(v, k)["a"]
    assert a["blok_en"] == 20.0 and "yeni_olcu" not in a


def test_closed_decision_is_compared_as_approved(shop):
    """old: test_akis::kapanmis_kararin_karsilastirmasi_donar"""
    code, d = _g0()
    open_decision(d, "K-01", "biçim", _sec(a="x", b="y"), "g", branched=False, **TEXT)
    step(d, "karar açıldı", "project_engineer")
    chief.approve(d, "K-01", option="a")
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_kalinlik": {**PARAMS["blok_kalinlik"], "value": 9.0}})
    v = load_work(d)
    assert v.params["blok_kalinlik"].value == 9.0
    assert option_values(v, _decision(d))["a"]["blok_kalinlik"] == 5.0


def test_release_does_not_stop_on_its_own_hold_card(shop, monkeypatch):
    """old: test_akis::kesinlestirmede_baski_kendi_hold_kartina_takilmaz"""
    code, d = new()
    prepare(d, model=MODEL)
    review(d)
    release.release_request(d)
    real = runner.run

    def blocked(refs):
        return lambda v, m=None, checks=None: [*real(v, m, checks), *[Result(
            "approval_state", "APPROVAL-01", BLOCK, "checks.approval_state.hold", {"id": r, "status": "open"}, r)
            for r in refs]]

    monkeypatch.setattr(runner, "run", blocked(["B-01", "K-09"]))
    with pytest.raises(Refused) as e:
        chief.approve(d, "B-01")
    assert [r.ref for r in e.value.data["results"]] == ["K-09"]
    monkeypatch.setattr(runner, "run", blocked(["B-01"]))
    chief.approve(d, "B-01")
    assert f"{code}-release-01" in _tags(d)


def test_open_high_quality_finding_blocks_the_release_until_closed(shop):
    """old: test_akis::kalite_yuksek_bulgu_kapanmadan_baski_istenmez"""
    code, d = new()
    prepare(d, model=MODEL)
    step(d, "hazır", "project_engineer")
    review(d, "[YÜKSEK] calcs/x.py:3 — birim hatası — §9 — mm/m\n[DÜŞÜK] a — b — c — d")
    with pytest.raises(MekanikError):
        release.release_request(d)
    (path, rep), = quality.reports(d)
    assert [f["severity"] for f in rep["findings"]] == ["high", "low"]
    quality.close(d, path.name, 1, "birim düzeltildi", False, "tek seferlik yazım hatası")
    s = release.release_request(d)                                 # inputs unchanged: no new review
    q = yamlio.read(d / "cards" / f"B-{s['no']}.yaml")["values"]["quality"]
    assert q["high"] == 1 and q["open"] == 1 and q["report"].endswith(path.name) and q["closed_high"]


def test_consistency_and_basis_cards_when_approved(shop):
    """old: test_akis::tutarlilik_ve_dayanak_karti_onaylaninca"""
    code, d = new()
    prepare(d, model=MODEL)
    (d / "calcs").mkdir()
    (d / "calcs" / "h1.py").write_text(CALC.format(id="h1", x=1.0, level=1, method="elle"))
    (d / "calcs" / "h2.py").write_text(CALC.format(id="h2", x=1.3, level=2, method="VLM"))
    step(d, "hesaplar", "project_engineer")
    open_decision(d, "K-01", "biçim", _sec(a="x", b="y"), "g", branched=False, basis=["h2"], **TEXT)
    chief.approve(d, "K-01", option="a")
    t = next(c for c in evaluate(d)[3] if c.get("key") == "consistency:x")
    assert t["status"] == "open"
    chief.approve(d, t["id"])
    assert [r.status for r in evaluate(d)[2] if r.check == "calc_consistency" and r.ref == "x"] == ["pass"]
    (d / "calcs" / "h2.py").write_text(CALC.format(id="h2", x=1.35, level=2, method="VLM"))
    step(d, "h2 değişti", "project_engineer")
    cards = {c.get("key"): c for c in evaluate(d)[3]}
    assert cards["basis:K-01"]["status"] == "open" and cards["consistency:x"]["status"] == "open"
    assert (d / cards["basis:K-01"]["visuals"][0]["path"]).read_text().startswith("<svg")
    chief.approve(d, cards["basis:K-01"]["id"])
    assert _decision(d)["history"][-1] == {**_decision(d)["history"][-1], "event": "basis_refreshed",
                                           "note": cards["basis:K-01"]["id"]}
    assert not [r for r in evaluate(d)[2] if r.check == "decision_basis" and r.status != "pass"]


def test_decision_without_requirement_effects_cannot_open(shop):
    """new: Ek B §14 (yeniden yazılan) — hedef_etkisi eksikse kart açılmaz (B8, DECISION-02)"""
    code, d = _g0()
    head = git.head(d)
    with pytest.raises(Refused) as e:
        open_decision(d, "K-01", "etkisiz", _sec(a="x", b="y"), "g", branched=False,
                      **{**TEXT, "requirement_effects": []})
    assert [r.rule for r in e.value.data["results"]] == ["DECISION-02"] and git.head(d) == head
    with pytest.raises(Refused) as e:
        open_decision(d, "K-01", "bilinmeyen", _sec(a="x", b="y"), "g", **{**TEXT, "requirement_effects": [
            {"requirement": "R-99", "effect": "x"}]})
    assert e.value.key == "process.decision.unknown_requirement"


def test_unmeasured_observation_warns_on_the_card(shop):
    """new: Ek B §14 (yeniden yazılan) — ölçümsüz gözlem uyarısı (B6); Faz 1'de UYARI, şema ENGEL'i değil"""
    code, d = _g0()
    open_decision(d, "K-01", "gözlem", _sec(a="x", b="y"), "g", branched=False,
                  observations=[{"text": "parça esniyor gibi", "measured": False}], **TEXT)
    k = yamlio.read(d / "cards" / "K-01.yaml")
    assert "parça esniyor gibi" in k["warning"] and k["observations"][0]["measured"] is False
    assert "observations" not in _decision(d)            # only an unmeasured one and no basis: not in the record


def test_open_branched_decision_limit_from_the_config(shop):
    """new: el kitabı §7 madde 7 — open branched decisions are limited (config policy.max_open_provisional)"""
    doc = yamlio.read(shop.config / "config.yaml")
    doc["policy"]["max_open_provisional"] = 1
    yamlio.write(shop.config / "config.yaml", doc)
    code, d = _g0()
    open_decision(d, "K-01", "dallı", _sec(a="x", b="y"), "g", **TEXT)
    open_decision(d, "K-02", "dalsız", _sec(a="x", b="y"), "g", branched=False, **TEXT)   # does not use the limit
    with pytest.raises(Refused) as e:
        open_decision(d, "K-03", "ikinci dallı", _sec(a="x", b="y"), "g", **TEXT)
    assert e.value.key == "process.decision.limit" and e.value.data["n"] == 1
    assert subprocess.run(["git", "rev-parse", "--verify", f"{code}/decision/K-01-a"], cwd=d).returncode == 0
    assert git.git("log", "-1", "--format=%an", cwd=d) != CHIEF[0] and REQUIREMENTS

def test_decision_card_opens_with_empty_effects_when_there_is_no_requirement(shop):
    """new: Ek B §14 (yeniden yazılan) — the card schema needs requirement_effects; without a requirement list the
    decision card opens with [] (DECISION-02 asks only when there is a list)"""
    code, d = new()
    prepare(d, model=MODEL)
    yamlio.write(d / "requirements.yaml", {**yamlio.read(d / "requirements.yaml"), "items": []})
    step(d, "istek listesi boş", "project_engineer")
    open_decision(d, "K-01", "biçim", _sec(a="x", b="y"), "g", branched=False,
                  **{k: v for k, v in TEXT.items() if k != "requirement_effects"})
    assert yamlio.read(d / "cards" / "K-01.yaml")["requirement_effects"] == [] and _card(d, "K-01")["status"] == "open"
    assert _decision(d)["requirement_effects"] == []
