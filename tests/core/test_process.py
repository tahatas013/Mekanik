# SPDX-License-Identifier: AGPL-3.0-or-later
"""Process flow without a model (OCCT-free): step, gate request and pass, the chief's signed approval, comment and
reply, model note, undo refusals (old test_akis and new). The model-bound flows are in tests/flow."""

from __future__ import annotations

import pytest
from test_store import (CHIEF, PARAMS, REQUIREMENTS, _core_only, gpg_keys, log_entries, new, prepare,  # noqa: F401
                        review, shop)

from mekanik.core import yamlio
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, chief, gates
from mekanik.core.process.step import evaluate, step
from mekanik.core.store import git

CALC = '''ID = "{id}"
TITLE = "{id}"


def calculate(h, model):
    w = h.input("blok_en")
    h.magnitude("alan", w * {k}, "mm", {level}, "{method}")
    h.result("alan", w * {k}, "mm", status="{status}")
'''


def _card(d, cid):
    return next(c for c in evaluate(d)[3] if c["id"] == cid)


def _approvals(d):
    return yamlio.read(d / "approvals.yaml", []) or []


def _g0(shop, **kw):
    code, d = new(**kw)
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    return code, d


def test_step_commits_with_trailers_and_a_separate_log_commit(shop):
    """old: test_akis::g0_dan_g3_e_ilerler_ve_gunlukte_gorunur (adım ve günlük kısmı)"""
    code, d = new()
    prepare(d)
    s = step(d, "G0: istek listesi", "project_engineer", "ilk adım")
    tr = git.trailers(git.git("log", "-1", "--format=%B", s["commit"], cwd=d))
    assert tr["Step"] == "G0: istek listesi" and tr["Role"] == "project_engineer"
    last = git.trailers(git.git("log", "-1", "--format=%B", cwd=d))
    assert last["Log"].startswith("records/log/") and git.git("diff", "--name-only", "HEAD~1", cwd=d).startswith(
        "sentetik/") and "records/log/" in git.git("diff", "--name-only", "HEAD~1", cwd=d)
    assert [e["title"] for e in log_entries(d)] == ["G0: istek listesi"] and "ilk adım" in log_entries(d)[0]["body"]
    assert not git.git("status", "--porcelain", cwd=d)


def test_no_step_on_the_main_line(shop):
    """old: test_akis::ana_hatta_adim_atilamaz"""
    code, d = new()
    git.git("checkout", "-q", f"{code}/main", cwd=d)
    with pytest.raises(Refused) as e:
        step(d, "yasak", "project_engineer")
    assert e.value.key == "process.step.on_main"


def test_team_cannot_use_the_chief_role(shop):
    """old: test_akis::ekip_bas_muhendis_rolu_kullanamaz"""
    code, d = _g0(shop)
    with pytest.raises(PermissionError):
        step(d, "taklit", "chief_engineer")


def test_gate_passes_with_signed_approval_merge_and_tag(shop):
    """old: test_akis::kapi_etiketi_onay_kaydini_icerir_ve_bas_muhendis_imzalar"""
    code, d = _g0(shop)
    assert all(x["ok"] for x in _card(d, "O-G0")["checks"] and gates.items(load_work(d), "G0", [], []))
    out = chief.approve(d, "O-G0")
    tag = f"{code}-G0"
    assert out["gate"]["tag"] == tag and out["gate"]["next"] == "G1" and tag in git.git("tag", cwd=d).split()
    recs = yamlio.load(git.git("show", f"{tag}:sentetik/{code}/approvals.yaml", cwd=d))
    assert any(r["card"] == "O-G0" and r["action"] == "approve" for r in recs)
    assert git.git("log", "-1", "--format=%an", tag, cwd=d) == CHIEF[0]
    assert CHIEF[0] in git.git("for-each-ref", f"refs/tags/{tag}", "--format=%(taggername)", cwd=d)
    assert git.git("log", "-1", "--format=%G?", f"{code}/main", cwd=d) in ("G", "U")      # signed merge on main
    v = load_work(d)
    assert v.stage == "G1" and v.doc["process"]["gate_status"]["G0"]["status"] == "done"
    assert _card(d, "O-G0")["status"] == "closed"
    assert [r.status for r in approval_checks.signature(v)] == ["pass"]                  # APPROVAL-02
    main = git.git("log", "--first-parent", "--format=%s", f"{code}/main", cwd=d).splitlines()
    assert main[0] == t("process.gate.merge_title", gate="G0", branch=f"{code}/work/general") and len(main) == 4
    assert not git.git("status", "--porcelain", cwd=d)


def test_design_change_after_request_refuses_gate_approval(shop):
    """old: test_akis::istekten_sonra_tasarim_degisirse_kapi_onayi_yazilmaz"""
    code, d = _g0(shop)
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_en": {**PARAMS["blok_en"], "value": 25.0}})
    step(d, "istekten sonra değişiklik", "design_engineer")
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "process.gate.changed" and not _approvals(d) and f"{code}-G0" not in git.git("tag", cwd=d)


def test_passed_gate_cannot_be_approved_again_nothing_half_done(shop):
    """old: test_akis::gecilmis_kapi_yeniden_onaylanamaz_yarim_kalmaz"""
    code, d = _g0(shop)
    chief.approve(d, "O-G0")
    main, n = git.git("rev-parse", f"{code}/main", cwd=d), len(_approvals(d))
    with pytest.raises(Refused):
        chief.approve(d, "O-G0")
    assert len(_approvals(d)) == n and git.git("rev-parse", f"{code}/main", cwd=d) == main


def test_main_line_failure_undoes_the_approval_commit(shop, monkeypatch):
    """new: Ek B §14 kapı geçişi — the pass is not left half done when the main line cannot move"""
    code, d = _g0(shop)
    head = git.head(d)
    monkeypatch.setattr(gates, "merge_main", lambda *a: (_ for _ in ()).throw(RuntimeError("ana hat")))
    with pytest.raises(RuntimeError):
        chief.approve(d, "O-G0")
    assert git.head(d) == head and not _approvals(d) and load_work(d).stage == "G0"


def test_closing_field_written_in_a_card_file_does_not_close_a_hold(shop):
    """old: test_akis::kapanis_alani_hold_kapatmaz (v1: on the gate card)"""
    code, d = _g0(shop)
    doc = yamlio.read(d / "cards" / "O-G0.yaml")
    yamlio.write(d / "cards" / "O-G0.yaml", {**doc, "status": "closed", "closed_reason": "ekip kapattı"})
    assert _card(d, "O-G0")["status"] == "open"


def test_stage_is_read_from_the_gate_tags(shop):
    """old: test_akis::asama_etiketlerden_okunur"""
    code, d = _g0(shop)
    git.git("checkout", "-q", "-b", f"{code}/work/hazirlik", cwd=d)
    git.git("checkout", "-q", f"{code}/work/general", cwd=d)
    chief.approve(d, "O-G0")
    git.git("checkout", "-q", f"{code}/work/hazirlik", cwd=d)
    v = load_work(d)
    assert v.stage == "G0" and gates.stage(d, v) == "G1"
    with pytest.raises(Refused) as e:
        gates.stage_finish(d, "G0")
    assert e.value.key == "process.gate.passed"
    with pytest.raises(Refused) as e:
        gates.stage_finish(d, "G3")
    assert e.value.key == "process.gate.wrong_stage" and e.value.data["stage"] == "G1"


def test_chief_does_not_write_into_a_dirty_folder(shop):
    """old: test_akis::kirli_klasorde_bas_muhendis_yazmaz"""
    code, d = _g0(shop)
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_en": {**PARAMS["blok_en"], "value": 31.0}})   # agent at work
    n = len(git.git("log", "--format=%H", cwd=d).split())
    for call in (lambda: chief.approve(d, "O-G0"), lambda: chief.value(d, "blok_kalinlik", 6.0)):
        with pytest.raises(Refused) as e:
            call()
        assert e.value.key == "process.ready.dirty"
    assert len(git.git("log", "--format=%H", cwd=d).split()) == n and not _approvals(d)


def test_who_saw_an_old_version_cannot_approve(shop):
    """old: test_akis::eski_surumu_goren_onay_veremez"""
    code, d = _g0(shop)
    seen = git.head(d)
    step(d, "ara adım", "project_engineer")                     # the agent took a step meanwhile
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0", viewed=seen[:7])
    assert e.value.key == "process.ready.stale" and not _approvals(d)


def test_comment_waits_for_a_reply_and_closes_with_it(shop):
    """old: test_akis::yorum_yanit_bekler_yanitlaninca_kapanir"""
    code, d = _g0(shop)
    chief.approve(d, "O-G0", "comment", "R-01'i değiştir")
    k = _card(d, "O-G0")
    assert k["status"] == "awaiting_reply" and k["thread"][0]["text"] == "R-01'i değiştir"
    assert [p["card"] for p in chief.pending(d)] == ["O-G0"]
    with pytest.raises(Refused) as e:
        chief.reply(d, "O-G0", "x", role="chief_engineer")
    assert e.value.key == "process.reply.team_only"
    chief.reply(d, "O-G0", "R-01 değişti")
    k = _card(d, "O-G0")
    assert k["status"] == "open" and k["thread"][1]["text"] == "R-01 değişti" and chief.pending(d) == []
    with pytest.raises(Refused) as e:
        chief.reply(d, "O-G0", "yine")
    assert e.value.key == "process.reply.none" and not git.git("status", "--porcelain", "--", str(d), cwd=d)


def test_model_note_opens_falls_to_the_team_and_closes_with_the_reply(shop):
    """old: test_akis::model_notu_acilir_ekibe_duser_yanitla_kapanir"""
    code, d = _g0(shop)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    s = chief.model_note(d, "Burun ucunu yuvarlat", png, {"part": "blok", "point": [1.0, 2.0, 3.0],
                                                           "box": [0.1, 0.1, 0.3, 0.3]})
    assert s["card"] == "N-01" and (d / s["visual"]).read_bytes() == png
    assert [p["card"] for p in chief.pending(d)] == ["N-01"]
    k = yamlio.read(d / "cards" / "N-01.yaml")
    assert k["type"] == "model_note" and k["visuals"][0]["path"] == s["visual"] and k["subject"]["part"] == "blok"
    assert git.git("log", "-1", "--format=%an", "--", "cards/N-01.yaml", cwd=d) == CHIEF[0]
    step(d, "başka bir adım", "project_engineer")             # a step keeps the screenshot
    assert yamlio.read(d / "cards" / "N-01.yaml")["visuals"][0]["path"] == s["visual"]
    chief.reply(d, "N-01", "Burun ucu 2 mm yuvarlatıldı")
    assert _card(d, "N-01")["status"] == "superseded" and "Burun ucu" in _card(d, "N-01")["closed_reason"]
    assert not chief.pending(d) and chief.model_note(d, "ikinci", png, {})["card"] == "N-02"
    assert [r.status for r in approval_checks.signature(load_work(d))] == ["pass", "pass"]


def test_experiment_verified_mandatory_requirement_adds_g4(shop):
    """old: test_akis::deneyle_dogrulanan_zorunlu_istek_g4_ekler"""
    code, d = _g0(shop)
    assert "G4" not in load_work(d).gates
    req = yamlio.read(d / "requirements.yaml")
    req["items"].append({**REQUIREMENTS[0], "id": "R-09", "text": "uçar", "verification": {"method": "experiment"}})
    yamlio.write(d / "requirements.yaml", req)
    step(d, "istek eklendi", "project_engineer")
    assert gates.plan_update(d) == ["G4"]
    v = load_work(d)
    assert v.gates == ["G0", "G1", "G3", "G4", "G5"] and v.doc["process"]["gate_status"]["G4"]["added_reason"]
    assert gates.plan_update(d) == []


def test_bad_result_on_the_gate_card_needs_a_reason(shop):
    """new: Ek B §14 madde 10 — CALC-02: a card listing a bad or unreliable result is approved only with a reason"""
    code, d = new()
    prepare(d)
    (d / "calcs").mkdir()
    (d / "calcs" / "alan.py").write_text(CALC.format(id="alan", k=2, level=1, method="elle", status="bad"))
    step(d, "hesap", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    assert _card(d, "O-G0")["values"]["bad_results"][0]["status"] == "bad"
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "process.approve.reason" and not _approvals(d)
    chief.approve(d, "O-G0", reason="kötü sonuç bilerek kabul: sınama")
    assert _approvals(d)[0]["reason"].startswith("kötü sonuç")


def test_consistency_card_has_a_core_figure_and_its_approval_lifts_the_warning(shop):
    """old: test_akis::tutarlilik_ve_dayanak_karti_onaylaninca (tutarlılık kısmı; dayanak kısmı tests/flow'da)"""
    code, d = new()
    prepare(d)
    (d / "calcs").mkdir()
    (d / "calcs" / "h1.py").write_text(CALC.format(id="h1", k=1.0, level=1, method="elle", status="ok"))
    (d / "calcs" / "h2.py").write_text(CALC.format(id="h2", k=1.3, level=2, method="VLM", status="ok"))
    step(d, "hesaplar", "project_engineer")
    t = next(c for c in evaluate(d)[3] if c.get("key") == "consistency:alan")
    assert t["status"] == "open" and (d / t["visuals"][0]["path"]).read_text().startswith("<svg")
    chief.approve(d, t["id"])
    _, _, results, _ = evaluate(d)
    assert [r.status for r in results if r.check == "calc_consistency" and r.ref == "alan"] == ["pass"]


def test_requirement_table_states_and_evidence(shop):
    """new: Ek B §14 (yeniden yazılan) — istek–kanıt durumu (B2): met needs evidence, else awaiting evidence"""
    code, d = new()
    prepare(d)
    req = yamlio.read(d / "requirements.yaml")
    ev = [{"kind": "calculation", "id": "alan"}]
    req["items"] += [{**REQUIREMENTS[0], "id": "R-02", "evaluation": {"status": "met", "at": "G0", "evidence": ev}},
                     {**REQUIREMENTS[0], "id": "R-03", "evaluation": {"status": "not_met", "at": "G0"}}]
    yamlio.write(d / "requirements.yaml", req)
    assert gates.requirement_table(load_work(d)) == [
        {"requirement": "R-01", "status": "awaiting_evidence"},
        {"requirement": "R-02", "status": "met", "evidence": ev}, {"requirement": "R-03", "status": "not_met"}]


def test_gate_and_release_approvals_are_never_undone(shop):
    """old: test_akis::istek_geri_cekilir_onay_geri_alinir (kapı kısmı; Ö-15)"""
    code, d = _g0(shop)
    chief.approve(d, "O-G0")
    for cid in ("O-G0", "B-01"):
        with pytest.raises(Refused) as e:
            chief.undo(d, cid, "x")
        assert e.value.key == "process.undo.gate_release"
    with pytest.raises(Refused) as e:
        chief.undo(d, "S-01", "x")
    assert e.value.key == "process.undo.nothing"
