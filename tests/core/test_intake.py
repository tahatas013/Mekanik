# SPDX-License-Identifier: AGPL-3.0-or-later
"""Intake (architecture §7, criteria 2.2 C1–C6) on the three synthetic cases of tests/intake/cases: the questions that
must be asked and those the data answers are written beforehand in each case's expected.yaml. OCCT-free."""

from __future__ import annotations

import copy

import pytest
from intake_data import NAMES, case, events, expected, review, specs
from test_store import gpg_keys, new, shop  # noqa: F401  (fixtures)

from mekanik.config import load_config
from mekanik.core import yamlio
from mekanik.core.cards import approval
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.checks.result import BLOCK, PASS
from mekanik.core.errors import SchemaError
from mekanik.core.intake import engine, expr, summary, trees
from mekanik.core.model.schema import validate
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, chief
from mekanik.core.store import git, works
from mekanik.plugins import reset_registry, set_registry


@pytest.fixture(autouse=True)
def _registry():
    set_registry(specs())
    yield
    reset_registry()


def _plan(d, **kw):
    return engine.plan(load_work(d), **kw)


def _states(p) -> dict[str, set]:
    out: dict[str, set] = {}
    for x in p["nodes"]:
        out.setdefault(x["state"], set()).add(x["key"])
    return out


def _answer_all(d, name):
    for key, value in expected(name)["answers"].items():
        engine.answer(d, key, value)


def _intake(d):
    return summary.check(load_work(d))


@pytest.mark.parametrize("name", NAMES)
def test_cases_ask_only_what_the_data_does_not_give(name, tmp_path):
    """2.2: C1 — veriden çıkarılabilen soru sorulmaz: her vakada önceden yazılı sorular sorulur, veriden çıkanlar
    sorulmaz (0)"""
    p, exp = _plan(d := case(name, tmp_path)), expected(name)
    st = _states(p)
    assert st.get("derived", set()) == set(exp["derived"]) and st.get("answered", set()) == set(exp["answered"])
    assert set(p["now"]) == set(exp["now"]) and set(p["stage_end"]) == set(exp["stage_end"])
    assert not (set(p["now"]) | set(p["stage_end"])) & st.get("derived", set())
    assert set(engine.ask(d)["now"]) == set(exp["now"]) and len(events(d, "question")) == len(exp["now"])


def test_derived_answer_is_recorded_as_derived_and_streamed_once(tmp_path):
    """2.2: C1 — veriden çıkan cevap `derived` kaynağıyla yazılır ve akışa bir kez düşer"""
    d = case("I-01", tmp_path)
    engine.ask(d)
    engine.ask(d)
    rec, notes = engine.records(d), events(d, "notice")
    assert rec["print3d.basics/printer"] == {"asked": "derived", "value": "fdm-test@v0", "at": rec[
        "print3d.basics/printer"]["at"]}
    assert len(notes) == len(expected("I-01")["derived"])
    q = next(x for x in _plan(d)["nodes"] if x["key"] == "print3d.basics/copies")
    assert (q["state"], q["answer"], q["source"]) == ("derived", 20, "derived")   # from the core tree's answer


def test_every_question_has_why_default_and_visual():
    """2.2: C2 — her soruda neden önemli, cevapsızsa ne varsayılacağı ve görsel var (%100; çekirdek ve print3d)"""
    all_trees = trees.load("questions", "question_tree")
    assert {"core.basics", "core.product", "print3d.basics"} <= set(all_trees)
    nodes = [n for tr in all_trees.values() for n in trees.walk(tr["nodes"])]
    assert len(nodes) >= 15
    for n in nodes:
        assert engine.text(n["why"]).strip() and n["visual"]["generator"] and "value" in n["default_if_unanswered"]
        assert n["default_if_unanswered"]["source"] and n["urgency"] in ("now", "stage_end"), n["id"]


@pytest.mark.parametrize("field", ["why", "default_if_unanswered", "visual", "urgency"])
def test_schema_refuses_a_question_without_why_default_or_visual(field):
    """2.2: C2 — negatif şema testi: neden, varsayılan, görsel ya da aciliyeti olmayan soru şemadan geçmez"""
    tree = copy.deepcopy(trees.load("questions", "question_tree")["core.basics"])
    validate("question_tree", tree, "core.basics")
    del tree["nodes"][1][field]
    with pytest.raises(SchemaError):
        validate("question_tree", tree, "core.basics")


def test_asked_questions_reach_the_stream_with_their_figure(tmp_path):
    """2.2: C2 — akışa giden her soru görselini taşır (gerçek dosya)"""
    d = case("I-01", tmp_path)
    engine.ask(d)
    qs = events(d, "question")
    assert len(qs) == 5 and all(e["visuals"] and (d / e["visuals"][0]["path"]).is_file() for e in qs)


@pytest.mark.parametrize("name", NAMES)
def test_now_questions_per_case_are_within_the_limit(name, tmp_path):
    """2.2: C3 — vaka başına "şimdi" sorusu ≤ 5 (T-06; sınır katalogdan)"""
    p = _plan(case(name, tmp_path))
    assert p["limit"] == 5 and len(p["now"]) <= 5


def _bare(tmp_path):
    """I-01 with nothing given: no brief answers, no analysis, no machine profile, no risk answers."""
    d = case("I-01", tmp_path)
    (d / engine.ANSWERS).unlink()
    (d / engine.ANALYSIS).unlink()
    doc = yamlio.read(d / "work.yaml")
    yamlio.write(d / "work.yaml", {k: v for k, v in doc.items() if k not in ("profiles", "risk_answers")})
    return d


def test_now_limit_sends_the_rest_to_the_stage_end_batch(tmp_path):
    """2.2: C3 — sınırı aşan "şimdi" soruları aşama sonu paketine geçer; DUR soruları önce sorulur"""
    p = _plan(d := _bare(tmp_path))
    nodes = {x["key"]: x for x in p["nodes"]}
    wanted = [k for k, x in nodes.items() if x["node"]["urgency"] == "now" and x["state"] == "pending"]
    assert len(wanted) > 5 and len(p["now"]) == 5 and set(wanted) - set(p["now"]) <= set(p["stage_end"])
    holds = [k for k in wanted if nodes[k]["hold"]]
    assert set(holds) <= set(p["now"])
    engine.ask(d)
    for k in p["now"]:                       # answering the five does not open five more "now" questions
        x = nodes[k]["node"]["answer"]
        engine.answer(d, k, {"boolean": True, "number": 3, "text": "PLA", "choice": "tr"}[x["type"]])
    assert _plan(d)["now"] == [] and _plan(d)["asked_now"] == 5


def test_now_limit_comes_from_the_workshop_config(tmp_path, monkeypatch):
    """2.2: C3 — sınır atölye ayarından (policy.max_questions_per_stage) gelir; yoksa INTAKE-02 max_now"""
    import shutil

    shutil.copytree(load_config().root, cfg := tmp_path / "config")
    doc = yamlio.read(cfg / "config.yaml")
    yamlio.write(cfg / "config.yaml", {**doc, "policy": {**doc["policy"], "max_questions_per_stage": 2}})
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    p = _plan(_bare(tmp_path))
    assert p["limit"] == 2 and len(p["now"]) == 2 and all(x["hold"] for x in p["nodes"] if x["key"] in p["now"])


def test_planted_findings_are_caught(tmp_path):
    """2.2: C4 — bilerek konmuş çelişki, sayısız istek ve gözden kaçan şey yakalanır: 9/9 (vaka başına 3)"""
    caught = 0
    for name in NAMES:
        got = {(f["kind"], f["ref"]) for f in _plan(case(name, tmp_path))["findings"]}
        planted = {(x["kind"], x["ref"]) for x in expected(name)["planted"]}
        assert {k for k, _ in planted} == {"contradiction", "missing_number", "overlooked"}
        caught += len(planted & got)
    assert caught == 9


def test_findings_enter_the_summary(tmp_path):
    """2.2: C4 — bulgular metniyle ve dayanağıyla anlama özetine girer"""
    d = case("I-02", tmp_path)
    _answer_all(d, "I-02")
    doc = summary.build(view := load_work(d), engine.plan(view, defaults=True))
    validate("intake_summary", doc, "summary")
    assert sorted(f["kind"] for f in doc["findings"]) == ["contradiction", "missing_number", "overlooked"]
    assert all(f["text"] and f["resolved"] is False for f in doc["findings"])


def _submitted(d, name):
    """A summary as `submit` leaves it, without git: the reviewed content with status submitted."""
    _answer_all(d, name)
    doc = summary.build(view := load_work(d), engine.plan(view, defaults=True))
    yamlio.write(d / summary.SUMMARY, {**doc, "status": "submitted"})
    return doc


def _stage(d, stage):
    doc = yamlio.read(d / "work.yaml")
    doc["process"].update(stage=stage, gate_status={"G0": {"status": "done"}, stage: {"status": "in_progress"}})
    yamlio.write(d / "work.yaml", doc)


def _approve(d, doc):
    view = load_work(d)
    approval.append(view, approval.record(view, summary.CARD, summary.subject(doc), "approve", load_config().chief))


def test_unapproved_summary_blocks_design(tmp_path):
    """2.2: C5 — onaysız anlama özetiyle tasarım engellenir: G0'da ön koşul kalır, G0'dan sonra ENGEL; onayla geçer,
    özet değişince onay düşer"""
    d = case("I-01", tmp_path)
    r = _intake(d)[0]
    assert (r.rule, r.status, r.extra["precondition"], r.msg) == ("INTAKE-01", "warn", "G0", "intake.check.none")
    doc = _submitted(d, "I-01")
    assert summary.status(load_work(d)) == "submitted" and _intake(d)[0].failed
    _stage(d, "G1")
    assert [(x.rule, x.status) for x in _intake(d)][0] == ("INTAKE-01", BLOCK)
    _approve(d, doc)
    assert summary.status(load_work(d)) == "approved" and _intake(d)[0].status == PASS
    yamlio.write(d / summary.SUMMARY, {**doc, "method": {**doc["method"], "manufacturing": "SLA"}})
    assert summary.status(load_work(d)) == "dropped" and _intake(d)[0].status == BLOCK


def test_work_past_g0_without_any_summary_has_no_intake_result(tmp_path):
    """2.2: C5 — G0'ı tanımlamadan önce geçmiş (taşınmış) çalışma için sonuç yok: taşıma eşitliği (V4) bozulmaz"""
    d = case("I-01", tmp_path)
    _stage(d, "G1")
    assert _intake(d) == []


def test_summary_round_trip_with_the_chiefs_signed_approval(shop):
    """2.2: C5 — özet kalite incelemesinden sonra T-01 DUR kartı olur; baş mühendisin imzalı onayıyla ön koşul
    sağlanır"""
    code = works.new_work("TST", "SYN", "Braket", "C", "sınama", "testler geçer",
                          profiles={"manufacturing": "fdm-test@v0"}, work_type="new_part")
    d, src = works.find(code), case("I-01", shop.root / "cases")
    doc = yamlio.read(d / "work.yaml")
    yamlio.write(d / "work.yaml", {**doc, "risk_answers": yamlio.read(src / "work.yaml")["risk_answers"]})
    for f in ("requirements.yaml", "decisions.yaml", engine.ANSWERS, engine.ANALYSIS):
        yamlio.write_text(d / f, (src / f).read_text(encoding="utf-8").replace("TST-SYN-11", code))
    git.commit(d, git.message("hazırlık", None, "project_engineer"), [str(d)], load_config().team)   # team's step
    engine.ask(d)
    _answer_all(d, "I-01")
    with pytest.raises(Refused) as e:
        summary.submit(d)
    assert e.value.key == "intake.submit.none"
    summary.summarize(d)
    review(d)
    out = summary.submit(d)
    card = yamlio.read(d / "cards" / "T-01.yaml")
    assert out["card"] == "T-01" and (card["level"], card["type"], card["status"]) == ("hold", "intake_summary", "open")
    assert (d / summary.FIGURE).is_file() and summary.status(load_work(d)) == "submitted"
    assert _intake(d)[0].failed
    chief.approve(d, "T-01")
    assert summary.status(load_work(d)) == "approved" and _intake(d)[0].status == PASS
    assert all(r.status == PASS for r in approval_checks.signature(load_work(d)))   # APPROVAL-02: signed


def test_submit_needs_a_review_of_this_summary(shop):
    """2.2: C5 — kalite incelemesi bu özetin sürümünde yapılmadıysa özet baş mühendise gitmez (G-11)"""
    code = works.new_work("TST", "SYN", "Analiz", "C", "sınama", "testler geçer", work_type="analysis")
    d, src = works.find(code), case("I-03", shop.root / "cases")
    for f in ("requirements.yaml", engine.ANSWERS):
        yamlio.write_text(d / f, (src / f).read_text(encoding="utf-8").replace("TST-SYN-13", code))
    git.commit(d, git.message("hazırlık", None, "project_engineer"), [str(d)], load_config().team)
    review(d)                                    # reviewed before the summary was written
    summary.summarize(d)
    with pytest.raises(Refused) as e:
        summary.submit(d)
    assert e.value.key == "intake.submit.not_reviewed"


def test_schema_keeps_a_hold_question_without_a_default():
    """2.2: C6 — şema: DUR kategorisindeki sorunun varsayılan değeri yoktur (null) ve kart açar"""
    tree = copy.deepcopy(trees.load("questions", "question_tree")["core.product"])
    node = next(n for n in tree["nodes"] if n.get("stop_category"))
    for bad in ({"value": 100}, {"opens_card": False}):
        t2 = copy.deepcopy(tree)
        next(n for n in t2["nodes"] if n["id"] == node["id"])["default_if_unanswered"].update(bad)
        with pytest.raises(SchemaError):
            validate("question_tree", t2, "core.product")


def test_stage_end_defaults_skip_hold_questions(tmp_path):
    """2.2: C6 — aşama sonu varsayılanı DUR sorusuna uygulanmaz: soru açık kalır, iş o konuda durur"""
    p = _plan(case("I-02", tmp_path), defaults=True)
    for x in p["nodes"]:
        assert x["state"] != "defaulted" or not x["hold"], x["key"]
        assert x["state"] != "pending" or x["hold"], x["key"]
    assert {x["key"] for x in p["nodes"] if x["state"] == "pending"} == {
        "core.basics/safety_part", "core.product/quantity", "core.product/manufacturing_method",
        "core.product/cost_target"}


def test_summary_is_refused_while_a_hold_question_is_open(tmp_path):
    """2.2: C6 — DUR sorusu cevapsızken özet yazılmaz; DUR sorusu varsayılmış bir özet INTAKE-02 ENGEL alır"""
    d = case("I-02", tmp_path)
    with pytest.raises(Refused) as e:
        summary.summarize(d)
    assert e.value.key == "intake.summary.pending" and "core.product/quantity" in e.value.data["ids"]
    doc = _submitted(d, "I-02")
    for q in doc["questions"]:
        if (q["tree"], q["node"]) == ("core.product", "quantity"):
            q.update(state="defaulted", answer=None, source="assumption")
    yamlio.write(d / summary.SUMMARY, doc)
    r = [x for x in _intake(d) if x.rule == "INTAKE-02"]
    assert r[0].status == BLOCK and "core.product/quantity" in r[0].args["ids"]


def test_expressions_are_safe():
    """2.2: C1 — derive_from ifadesi güvenlidir: çağrı, indeks ve dunder yok; eksik ad None"""
    ctx = {"answers": {"n": 3}, "analysis": {"a": {"b": {"count": 1}}}}
    assert expr.evaluate("answers.n * 2 + 1", ctx) == 7 and expr.holds("analysis.a.b.count == 1", ctx)
    assert expr.evaluate("answers.none", ctx) is None and not expr.holds("answers.none > 0", ctx)
    assert expr.holds("answers.none == null and not false", ctx)
    for bad in ("__import__('os')", "answers['n']", "(lambda: 1)()", "answers.n if true else 0"):
        with pytest.raises(SchemaError):
            expr.evaluate(bad, ctx)


def test_work_types_are_data_and_need_their_package(tmp_path):
    """new: architecture §7.1 adım 1 — türler veridir; sağlayan paketi kurulu olmayan tür sunulmaz; öneri girdiden"""
    assert set(trees.work_types(available=False)) == {"new_part", "mold_for_part", "modify_model", "analysis",
                                                      "scan_to_model"}
    assert "mold_for_part" not in trees.work_types()                       # molding is not installed
    assert trees.suggest(["tarama.stl"])[0] == "scan_to_model"
    assert trees.suggest(["parca.step"], "delik düzelt")[0] == "modify_model"
    d = case("I-02", tmp_path)
    with pytest.raises(Refused) as e:
        engine.choose(d, "mold_for_part")
    assert e.value.key == "intake.type.unavailable"
    engine.choose(d, "new_part")
    assert load_work(d).doc["work_type"] == "new_part" and events(d, "notice")


def test_answer_must_fit_the_question(tmp_path):
    """new: architecture §7.1 adım 3 — cevap sorunun biçimine uyar; açık olmayan soru cevaplanmaz"""
    d = case("I-01", tmp_path)
    for key, value, why in (("core.product/market", "mars", "intake.answer.invalid"),
                            ("core.basics/customer_spec", "evet", "intake.answer.invalid"),
                            ("print3d.basics/split", True, "intake.answer.unknown")):
        with pytest.raises(Refused) as e:
            engine.answer(d, key, value)
        assert e.value.key == why
    with pytest.raises(SchemaError):
        engine.answer(d, "core.product/market", "tr", source="tahmin")
    rec = engine.answer(d, "core.product/market", "tr")
    assert rec["asked"] == "brief" and rec["source"] == "decision"


def test_team_step_keeps_the_open_summary_card(shop):
    """2.2: C5 — T-01 açıkken ekip adım atabilir (kartın görseli açılışta çizilir, adımda silinmez)"""
    from mekanik.core.process.step import step

    code = works.new_work("TST", "SYN", "Analiz", "C", "sınama", "testler geçer", work_type="analysis")
    d, src = works.find(code), case("I-03", shop.root / "cases")
    for f in ("requirements.yaml", engine.ANSWERS):
        yamlio.write_text(d / f, (src / f).read_text(encoding="utf-8").replace("TST-SYN-13", code))
    git.commit(d, git.message("hazırlık", None, "project_engineer"), [str(d)], load_config().team)
    summary.summarize(d)
    review(d)
    summary.submit(d)
    step(d, "bağımsız iş", "project_engineer")
