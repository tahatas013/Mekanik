# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standard map (architecture §10.8, criterion 2.5 F8) and STDMAP-01: no G0 without a map, no tick without evidence
or quality review (schema + check), no unticked mandatory item at G5, a paid text not in hand is never "in hand" and
gives no number. OCCT-free."""

from __future__ import annotations

import copy

import pytest
from intake_data import case, events, specs

from mekanik.core import stdmap, yamlio
from mekanik.core.checks.result import BLOCK, PASS, WARN
from mekanik.core.errors import SchemaError
from mekanik.core.intake import engine
from mekanik.core.model.schema import validate
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused
from mekanik.plugins import reset_registry, set_registry

EVIDENCE = [{"kind": "calculation", "id": "h_load"}]


@pytest.fixture(autouse=True)
def _registry():
    set_registry(specs())
    yield
    reset_registry()


def _stage(d, stage):
    doc = yamlio.read(d / "work.yaml")
    doc["process"]["stage"] = stage
    yamlio.write(d / "work.yaml", doc)


def _check(d):
    return stdmap.check(load_work(d))


def _item(**kw) -> dict:
    base = {"kind": "standard_item", "schema_version": "1.0", "title": "Şartname md. 4.2: yanal yük",
            "type": "customer_spec", "access": "customer_provided", "citation": {"document": "ŞRT-TST-01",
                                                                                  "clause": "4.2"},
            "purpose": "Yanal yükte dayanım", "why_here": "R-01 bu maddeden", "test_method": "hesap",
            "acceptance": {"text": "20 N'da kalıcı şekil değişimi yok", "requirement": "R-01"},
            "verification_status": "text_in_hand"}
    return {**base, **kw}


def test_g0_does_not_pass_without_a_map(tmp_path):
    """2.5: F8 — G0 kapısı haritasız geçmez: haritasız G0 ön koşulu kalır, G5'te ENGEL; harita varsa ön koşul geçer"""
    d = case("I-01", tmp_path)
    r = _check(d)
    assert [(x.rule, x.status, x.msg, x.extra.get("precondition")) for x in r] == [
        ("STDMAP-01", WARN, "stdmap.check.none", "G0")]
    _stage(d, "G5")
    assert [(x.status, x.msg) for x in _check(d)] == [(BLOCK, "stdmap.check.none_release")]
    _stage(d, "G1")
    assert _check(d) == []                       # migrated past G0 before the map existed
    _stage(d, "G0")
    stdmap.save(d, [])
    assert [(x.status, x.msg, x.extra["precondition"]) for x in _check(d)] == [(PASS, "stdmap.check.present", "G0")]


def test_build_proposes_regulations_from_the_intake_answers(tmp_path):
    """2.5: F8 — harita G0'da kütüphaneden önerilir: pazar ve tüketici cevaplarına göre mevzuat (applies_to)"""
    d = case("I-01", tmp_path)
    engine.answer(d, "core.product/market", "tr")
    engine.answer(d, "core.product/consumer_product", False)
    ids = stdmap.build(d)
    got = {i["from_library"] for i in stdmap.load(d)}
    assert ids == [f"SM-{n:02d}" for n in range(1, len(ids) + 1)]
    assert {"tr.7223.law", "tr.pgd.2021", "tr.kkdik.2023"} <= got and not got & {"eu.2023-988.art5", "tr.gugy.2021"}
    engine.answer(d, "core.product/market", "eu_tr")
    engine.answer(d, "core.product/consumer_product", True)
    stdmap.build(d)
    got2 = {i["from_library"] for i in stdmap.load(d)}
    assert {"eu.2023-988.art5", "tr.gugy.2021", "eu.1907-2006.art33"} <= got2 and len(got2) == len(stdmap.load(d))
    assert events(d, "notice") and all(i["status"] == "awaiting_evidence" for i in stdmap.load(d))


def test_library_items_are_templates_and_paid_texts_are_not_in_hand():
    """2.5: F8 — kütüphane maddeleri şablondur; paralı standart metni elde değil (kopyalanmaz, uydurulmaz)"""
    lib = stdmap.library()
    assert len(lib) >= 13 and all(x["library"] for x in lib.values())
    paid = [x for x in lib.values() if x["access"] == "paid"]
    assert paid and all(x["verification_status"] != "text_in_hand" and x["open_equivalent"]["searched"] for x in paid)
    assert all(x["citation"].get("read_on") for x in lib.values() if x["type"] == "regulation")


@pytest.mark.parametrize("bad", ["no_evidence", "no_review", "not_met", "no_time"])
def test_schema_refuses_a_tick_without_evidence_or_review(bad):
    """2.5: F8 — şema: kanıtsız, kalite incelemesiz ya da karşılanmamış tik geçmez"""
    item = _item(id="SM-01", work="TST-SYN-11", status="met", evidence=EVIDENCE, tick={
        "checked": True, "quality_review": {"kind": "quality_review", "id": "QR-001"},
        "at": "2026-11-06T12:00:00+03:00"})
    validate("standard_item", item, "stdmap.yaml")
    broken = copy.deepcopy(item)
    {"no_evidence": lambda: broken.update(evidence=[]), "no_review": lambda: broken["tick"].pop("quality_review"),
     "not_met": lambda: broken.update(status="awaiting_evidence"), "no_time": lambda: broken["tick"].pop("at")}[bad]()
    with pytest.raises(SchemaError):
        validate("standard_item", broken, "stdmap.yaml")


def test_tick_needs_evidence_and_an_existing_quality_review(tmp_path):
    """2.5: F8 — tik yalnız kanıtla ve var olan kalite incelemesiyle konur; dayanaksız tik STDMAP-01 ENGEL"""
    d = case("I-01", tmp_path)
    sm = stdmap.add(d, _item())
    with pytest.raises(Refused) as e:
        stdmap.tick(d, sm["id"], [], "QR-001")
    assert e.value.key == "stdmap.tick.no_evidence"
    with pytest.raises(Refused) as e:
        stdmap.tick(d, sm["id"], EVIDENCE, "QR-001")
    assert e.value.key == "stdmap.tick.no_review"
    (d / "records/quality").mkdir(parents=True)
    (d / "records/quality/x.yaml").write_text("id: QR-001\n")
    done = stdmap.tick(d, sm["id"], EVIDENCE, "QR-001")
    assert (done["status"], done["tick"]["checked"]) == ("met", True)
    assert [x.status for x in _check(d) if x.ref == sm["id"]] == [PASS]
    (d / "records/quality/x.yaml").unlink()                    # the review it rests on is gone
    assert [(x.status, x.msg) for x in _check(d) if x.ref == sm["id"]] == [(BLOCK, "stdmap.check.unreviewed")]
    items = stdmap.load(d)
    items[0]["evidence"] = []
    yamlio.write(d / stdmap.FILE, items)                       # a tick written by hand without evidence
    assert [(x.status, x.msg) for x in _check(d)] == [(BLOCK, "stdmap.check.schema")]


def test_g5_blocks_an_unticked_mandatory_item(tmp_path):
    """2.5: F8 — G5'te tiksiz zorunlu madde ENGEL; zorunlu olmayan madde ve öncesindeki aşamalar geçer"""
    d = case("I-01", tmp_path)
    req = stdmap.add(d, _item())
    opt = stdmap.add(d, _item(type="guideline", access="open", mandatory=False, title="Tasarım kılavuzu"))
    assert {x.ref: x.status for x in _check(d) if x.ref.startswith("SM-")} == {req["id"]: PASS, opt["id"]: PASS}
    _stage(d, "G5")
    assert {x.ref: (x.status, x.msg) for x in _check(d) if x.ref.startswith("SM-")} == {
        req["id"]: (BLOCK, "stdmap.check.unticked"), opt["id"]: (PASS, "stdmap.check.ok")}
    assert stdmap.mandatory(req) and not stdmap.mandatory(opt) and stdmap.priority(req) == 2


def test_paid_text_not_in_hand_shows_unverified(tmp_path):
    """2.5: F8 — paralı standart: metin elde değilse "doğrulanmadı" görünür; "metin elde" yazmak ya da ondan sayı almak
    STDMAP-01 ENGEL"""
    d = case("I-01", tmp_path)
    paid = {"type": "standard", "access": "paid", "citation": {"document": "ISO 99999"},
            "open_equivalent": {"searched": True}, "procurement": {"needed": True, "justification": "metin gerekli"}}
    claimed = stdmap.add(d, _item(**paid, title="iddia"))
    number = stdmap.add(d, _item(**paid, title="sayı", verification_status="unverified", acceptance={
        "text": "x", "criterion": {"value": 0.2, "unit": "mm", "source": "standard:ISO 99999 Tablo 1"}}))
    honest = stdmap.add(d, _item(**paid, title="dürüst", verification_status="unverified", acceptance={
        "text": "tolerans grubu", "criterion": {"value": 0.3, "unit": "mm", "source": "assumption"}}))
    got = {x.ref: x.msg for x in _check(d) if x.ref.startswith("SM-")}
    assert got == {claimed["id"]: "stdmap.check.not_in_hand", number["id"]: "stdmap.check.number_without_text",
                   honest["id"]: "stdmap.check.ok"}
    rows = {r["id"]: r["shown_status"] for r in stdmap.rows(d)}
    assert rows[claimed["id"]] == rows[honest["id"]] == "unverified" and stdmap.counts(stdmap.load(d)) == {
        "items": 3, "paid_items": 3, "unverified": 3}
    bought = _item(**{**paid, "procurement": {"needed": True, "justification": "x", "approved": {"kind": "card",
                                                                                               "id": "K-09"}}})
    found = _item(**{**paid, "open_equivalent": {"searched": True, "found": "jcgm.106-2012"}})
    assert stdmap.effective(bought) == "text_in_hand" and stdmap.effective(found) == "secondary_source"


def test_old_regulation_reading_warns(tmp_path):
    """2.5: F8 — mevzuat atfının okuması 365 günden eskiyse yeniden doğrulama uyarısı (STDMAP-01 limit)"""
    d = case("I-01", tmp_path)
    old = stdmap.add(d, _item(type="regulation", access="open", title="eski", citation={
        "document": "7223", "read_on": "2024-01-02"}))
    new = stdmap.add(d, _item(type="regulation", access="open", title="yeni", citation={
        "document": "7223", "read_on": "2026-11-06"}))
    warns = [x.ref for x in _check(d) if x.status == WARN]
    assert warns == [old["id"]] and new["id"] not in warns


def test_summary_carries_the_map_counts(tmp_path):
    """2.5: F8 — anlama özeti standart haritası özetini taşır (madde, paralı, doğrulanmamış)"""
    from mekanik.core.intake import summary

    d = case("I-01", tmp_path)
    stdmap.add(d, _item(type="standard", access="paid", citation={"document": "ISO 99999"}, verification_status=
                        "unverified", open_equivalent={"searched": True}, procurement={"needed": True,
                                                                                         "justification": "x"}))
    stdmap.add(d, _item())
    doc = summary.build(view := load_work(d), engine.plan(view, defaults=True))
    assert doc["stdmap"] == {"items": 2, "paid_items": 1, "unverified": 1}
