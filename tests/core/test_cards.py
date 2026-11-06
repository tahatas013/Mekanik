# SPDX-License-Identifier: AGPL-3.0-or-later
"""Card generation, numbering, status, thread and sync (old test_cekirdek and new)."""

import os
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.cards import approval, awaiting, generate, makers, missing_fields, sync
from mekanik.core.checks import runner
from mekanik.core.checks.builtin import CHECKS
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.plugins import CriticalDim, PackageSpec, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CHIEF = ("Test Mühendis", "test@example.org")
CORE = PackageSpec(id="core", version="0", checks=CHECKS, card_makers=[makers.make])
DIMS = PackageSpec(id="fake", version="0", critical_dims=lambda v: [CriticalDim("X-01", "hole_dia", 0.2, "centering")])
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "profiles": {"instruments": ["caliper", "scanner-lidar"]},
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G2", "gate_status": {}}}
PARAMS = {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
          "shaft_dia": {"value": None, "unit": "mm", "source": "derived", "formula": "hole_dia - gap"}}


def work(tmp, params=None, gate_status=None, **files):
    yamlio.write(tmp / "work.yaml", {**WORK, "process": {**WORK["process"], "gate_status": gate_status or {}}})
    yamlio.write(tmp / "params.yaml", PARAMS if params is None else params)
    for name, data in files.items():
        yamlio.write(tmp / f"{name}.yaml", data)
    return load_work(tmp)


def wall(**kw):
    return {**PARAMS, "wall": {"value": 2.0, "unit": "mm", "source": "assumption", **kw}}


def cards_of(view):
    return generate(view, runner.run(view))


@pytest.fixture(autouse=True)
def _registry():
    set_registry([CORE, DIMS])
    yield
    reset_registry()


def test_card_ids_are_stable(tmp_path):
    """old: test_cekirdek::kart_numaralari_kararli"""
    v = work(tmp_path, params=wall())
    k1 = cards_of(v)
    sync(v, k1)
    k2 = cards_of(load_work(tmp_path))          # the written cards load back (schema-valid records)
    assert [k["id"] for k in k1] == [k["id"] for k in k2]
    # a non-critical assumption opens no card of its own; it goes to the V-01 list (card standard)
    assert not any(k["key"] == "assumption:wall" for k in k2)
    v01 = next(k for k in k2 if k["id"] == "V-01")
    assert v01["subject"]["params"] == ["wall"] and v01["status"] == "open"


def test_critical_assumption_own_card_manufacturer_source_no_card(tmp_path):
    """old: test_cekirdek::kritik_varsayim_tek_kart_uretici_kaynagi_kart_acmaz"""
    p = {**wall(critical="safety", rationale="g"),
         "bed": {"value": 256.0, "unit": "mm", "source": "manufacturer:test-maker"}}
    k = cards_of(work(tmp_path, params=p))
    own = next(x for x in k if x["key"] == "assumption:wall")
    assert own["id"].startswith("S-") and own["values"]["critical"] == "safety"
    assert own["question"] and own["proposal"]["rationale"] == "g" and own["level"] == "hold"
    assert not any("bed" in (x.get("subject") or {}).get("params", []) for x in k)
    assert not any(x["id"] == "V-01" for x in k)


def test_caliper_assumed_uncertainty_opens_card(tmp_path):
    """old: test_cekirdek::kumpas_varsayim_belirsizligi_kart_acar"""
    k = next(k for k in cards_of(work(tmp_path)) if k["key"] == "uncertainty:caliper")
    assert {"assumption", "borderline"} <= set(k["triggers"])
    assert k["subject"]["params"] == ["hole_dia"] and k["checks"][0]["rule"] == "UNCERT-01"


def test_removed_trigger_closes_card(tmp_path):
    """old: test_cekirdek::tetikleyici_kalkan_kart_kapanir"""
    v = work(tmp_path, params=wall(critical="cost"))
    sync(v, cards_of(v))
    cid = next(k["id"] for k in v.cards if k["key"] == "assumption:wall")
    v2 = work(tmp_path, params={**PARAMS, "wall": {"value": 2.0, "unit": "mm", "source": "decision"}})
    sync(v2, cards_of(v2))
    doc = yamlio.read(tmp_path / "cards" / f"{cid}.yaml")
    assert doc["status"] == "closed" and doc["note"] == t("cards.note.trigger_gone")


def test_approved_value_change_drops_approval_and_reopens_card(tmp_path):
    """old: test_cekirdek::onaylanan_deger_degisince_onay_duser_ve_kart_yeniden_acilir"""
    v = work(tmp_path, params=wall(critical="safety", rationale="g"))
    card = next(k for k in cards_of(v) if k["key"] == "assumption:wall")
    approval.append(v, approval.record(v, card["id"], card["subject"], "approve", CHIEF, commit="abc1234"))
    assert approval.state(v, card["id"], card["subject"]) == "approved"
    assert next(k for k in cards_of(v) if k["id"] == card["id"])["status"] == "approved"

    v2 = work(tmp_path, params=wall(critical="safety", rationale="g", value=2.5))     # value 2.0 → 2.5
    assert len(v2.approvals) == 1                                                  # approvals.yaml kept
    assert approval.state(v2, card["id"], card["subject"]) == "dropped"
    k2 = next(k for k in cards_of(v2) if k["id"] == card["id"])
    assert k2["status"] == "open" and k2["approval_state"] == "dropped" and k2["note"] == t("cards.note.dropped")


def test_assumption_list_rows_are_approved_one_by_one(tmp_path):
    """new: V-01 rows (old _liste_durumu, `V-01/<param>`); manufacturer values are information rows"""
    p = {**wall(rationale="r"), "rib": {"value": 1.0, "unit": "mm", "source": "assumption", "rationale": "r"},
         "bed": {"value": 256.0, "unit": "mm", "source": "manufacturer:test-maker"}}
    v = work(tmp_path, params=p)
    approval.append(v, approval.record(v, "V-01/wall", {"params": ["wall"]}, "approve", CHIEF))
    v01 = next(k for k in cards_of(v) if k["id"] == "V-01")
    assert {r["param"]: r["status"] for r in v01["rows"]} == {"wall": "approved", "rib": "open"}
    assert v01["status"] == "open" and [r["param"] for r in v01["info_rows"]] == ["bed"]
    assert v.approvals[0]["card"] == "V-01" and v.approvals[0]["row"] == "wall"
    approval.append(v, approval.record(v, "V-01/rib", {"params": ["rib"]}, "approve", CHIEF))
    assert next(k for k in cards_of(v) if k["id"] == "V-01")["status"] == "approved"


def test_comment_without_reply_awaits_reply(tmp_path):
    """new: card thread from approvals.yaml comments and replies.yaml (G-29)"""
    v = work(tmp_path, params=wall(critical="safety", rationale="g"))
    cid = next(k["id"] for k in cards_of(v) if k["key"] == "assumption:wall")
    rec = approval.append(v, approval.record(v, cid, {}, "comment", CHIEF, reason="Neden 2 mm?"))
    k = next(k for k in cards_of(v) if k["id"] == cid)
    assert k["status"] == "awaiting_reply" and awaiting(k) and k["thread"][0]["text"] == "Neden 2 mm?"
    yamlio.write(tmp_path / "replies.yaml", [{"card": cid, "comment_at": rec["at"], "text": "Benzer parçada yeterli.",
                                             "role": "design_engineer", "at": rec["at"]}])
    k = next(k for k in cards_of(load_work(tmp_path)) if k["id"] == cid)
    assert k["status"] == "open" and not awaiting(k) and k["thread"][1]["kind"] == "reply"


def test_manual_card_kept_and_closed_when_gate_passed(tmp_path):
    """new: cards opened by hand are kept; a gate card closes when its gate is done (old: git tag)"""
    gate = {"kind": "card", "schema_version": "1.0", "id": "O-G2", "work": "TST-SYN-09", "type": "question",
            "level": "hold", "title": "G2 kapısı", "subject": {"gate": "G2", "design": True}, "status": "open",
            "opened_by": "project_engineer", "opened_at": "2026-11-06T10:00:00+03:00"}
    (tmp_path / "cards").mkdir()
    yamlio.write(tmp_path / "cards" / "O-G2.yaml", gate)
    assert next(k for k in cards_of(work(tmp_path)) if k["id"] == "O-G2")["status"] == "open"
    v = work(tmp_path, gate_status={"G2": {"status": "done", "tag": "TST-SYN-09-G2"}})
    k = next(k for k in cards_of(v) if k["id"] == "O-G2")
    assert k["status"] == "closed" and "TST-SYN-09-G2" in k["closed_reason"]


def test_missing_fields_card_standard(tmp_path):
    """old behaviour of kartlar.eksikler, tested directly: an open generated card lacks only its visual"""
    k = next(k for k in cards_of(work(tmp_path, params=wall(critical="safety", rationale="g")))
             if k["key"] == "assumption:wall")
    assert missing_fields(k) == ["visuals"]
    assert missing_fields({**k, "visuals": [{"kind": "model_view", "id": "a.svg"}]}) == []
    assert missing_fields({**k, "status": "approved"}) == []
    k["proposal"]["rationale"] = ""
    assert "proposal" in missing_fields(k)


def test_package_card_takes_its_record_id(tmp_path):
    """new: a card about a record whose id is a card id keeps it (old G-nn, E-nn cards); others get S-nn"""
    def maker(view, results):
        base = {"type": "pkg:thing", "level": "hold", "title": "x", "triggers": ["t"], "generated": True}
        return [{**base, "key": "rec:E-01", "subject": {"rec": "E-01"}},
                {**base, "key": "basis:K-04", "subject": {"decision": "K-04"}}]
    set_registry([CORE, PackageSpec(id="pkg", version="0", card_makers=[maker])])
    ids = {k["key"]: k["id"] for k in cards_of(work(tmp_path))}
    assert ids["rec:E-01"] == "E-01" and ids["basis:K-04"].startswith("S-")
