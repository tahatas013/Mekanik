# SPDX-License-Identifier: AGPL-3.0-or-later
"""Provisional decision life with git and the chief's signed records (OCCT-free; a stand-in package draws the card
figures instead of mech): the stream line with a figure (D2), objection and the dependent work (D3), acceptance at
the gate (D4), the stage measures at every stage finish (D5), REQ-01 at G4/G5 (F5), the return G3 → G2."""

from __future__ import annotations

import pytest
from test_store import PARAMS, TEAM, gpg_keys, log_entries, new, prepare, review, shop  # noqa: F401

from mekanik.core import yamlio
from mekanik.core.builtin import SPEC
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.decisions import open_decision
from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.core.policy import lifecycle, metrics
from mekanik.core.process import Refused, chief, gates
from mekanik.core.process.step import evaluate, step
from mekanik.core.report import stream
from mekanik.core.store import git, works
from mekanik.plugins import PackageSpec, reset_registry, set_registry

TEXT = {"question": "Hangisi?", "explain": "sınama kararı", "proposal": "a", "proposal_rationale": "sınama",
        "requirement_effects": [{"requirement": "R-01", "effect": "blok yazıcıya sığar (değişmez)"}]}
CALC = 'ID = "alan"\n\n\ndef calculate(h, model):\n    h.result("alan", h.input("blok_en") * 2, "mm")\n'


class Figures:
    """Model hooks with no model: one figure per card, one per option of a decision card (the option id)."""

    def build(self, view):
        return None

    def producer_version(self):
        return "0"

    def has(self, name):
        return False

    def card_visuals(self, view, card, model, option_values=None, base=None):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><text>{}</text></svg>'.format
        if card.get("options"):
            return [(o["id"], svg(f"{card['id']} {o['id']}")) for o in card["options"]], []
        return [("fig", svg(card["id"]))], []


@pytest.fixture(autouse=True)
def _figures():
    set_registry([SPEC, PackageSpec(id="fig", version="0.1.0", model=Figures())])
    yield
    reset_registry()


def _opts(**names):
    return {k: {"title": v, "values": {"blok_en": 20.0 + 4 * i}} for i, (k, v) in enumerate(names.items())}


def _dec(d, did="K-01"):
    return next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == did)


def _card(d, cid):
    return next(c for c in evaluate(d)[3] if c["id"] == cid)


def _ready(cls="C", params=None):
    code, d = new(cls)
    prepare(d, params=params or PARAMS)
    step(d, "hazırlık", "project_engineer")
    return code, d


def _pass(d, gate):
    review(d)
    gates.stage_finish(d, gate)
    return chief.approve(d, f"O-{gate}")


def test_provisional_decision_goes_to_the_stream_with_its_figure(shop):
    """2.3: D2 — a provisional decision gets a `provisional_decision` line with the card's figure, the decision
    and the gate its objection window ends at; the decision keeps the line's id; a line without a figure is refused
    by the schema; the tree stays clean (the line is committed right after the decision's commit)"""
    code, d = _ready()
    out = open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "sınama", branched=False, **TEXT)
    ev, rec = out["event"], _dec(d)
    assert ev["type"] == "provisional_decision" and ev["objection_until"] == "G0" == rec["objection_until"]
    assert ev["visuals"][0]["path"] == "records/visuals/cards/K-01-a.svg" and (d / ev["visuals"][0]["path"]).exists()
    assert {"kind": "decision", "id": "K-01"} in ev["refs"] and rec["provisional"]["stream_event"] == ev["id"]
    assert (rec["mode"], rec["status"], rec["chosen"], rec["visual"]) == ("provisional", "provisional_active", "a",
                                                                         ev["visuals"][0])
    assert stream.read(d)[-1] == ev and git.is_clean(d)
    assert _card(d, "K-01")["level"] == "provisional" and _card(d, "K-01")["status"] == "open"
    with pytest.raises(SchemaError):
        stream.emit(d, "provisional_decision", line="görselsiz", refs=[{"kind": "decision", "id": "K-01"}],
                    objection_until="G0")


def test_stop_category_decision_opens_as_hold(shop):
    """2.3: D1 — opening: a stop category (and a category the rules make stricter) gives a hold decision with no
    objection window and no stream line of its own"""
    code, d = _ready()
    out = open_decision(d, "K-01", "malzeme", _opts(a="x", b="y"), "g", branched=False, category="material", **TEXT)
    rec = _dec(d)
    assert (rec["mode"], rec["status"]) == ("hold", "proposed") and "objection_until" not in rec
    assert out["event"]["type"] == "decision" and stream.read(d)[-1] == out["event"]   # the step's own line only
    assert _card(d, "K-01")["level"] == "hold" and _card(d, "K-01")["stop_category"] == "material"
    # the main-dimension mark is the chief's (MAINDIM-01): set with his signed value, not by a team step
    chief.value(d, "blok_en", yamlio.read(d / "params.yaml")["blok_en"]["value"], "ana ölçü", "S-01", main=True)
    open_decision(d, "K-02", "en", _opts(a="x", b="y"), "g", branched=False, category="design_detail", **TEXT)
    k2 = _dec(d, "K-02")
    assert (k2["mode"], k2["category"]) == ("hold", "main_dimensions") and "design_detail" in k2["history"][0]["note"]


def test_objection_lists_the_dependent_work(shop, tmp_path):
    """2.3: D3 — scenario 1: the objection is the chief's signed record; the decision's declared dependents and
    changed values are listed; scenario 2: the calcs reading a changed value and the cards about it; scenario 3:
    the commits of its chosen branch not in the work branch (3/3)"""
    p = {**PARAMS, "blok_en": {**PARAMS["blok_en"], "source": "assumption", "rationale": "sığar"}}
    code, d = _ready(params=p)
    (d / "calcs").mkdir(exist_ok=True)
    (d / "calcs" / "alan.py").write_text(CALC)
    step(d, "hesap", "project_engineer")
    open_decision(d, "K-01", "en", _opts(a="x", b="y"), "g", dependents=["parça:blok"], **TEXT)
    wt = tmp_path / "wt"
    git.git("worktree", "add", "-q", str(wt), f"{code}/decision/K-01-a", cwd=d)
    yamlio.write(wt / "sentetik" / code / "params.yaml", {**p, "blok_en": {**p["blok_en"], "value": 26.0}})
    step(wt / "sentetik" / code, "seçenek a", "design_engineer")
    out = lifecycle.object_decision(d, "K-01", "en büyük olmalı")
    deps = out["dependents"]
    assert deps[:2] == ["parça:blok", "param:blok_en"]                                   # scenario 1
    assert "calc:alan" in deps and "card:V-01" in deps                                  # scenario 2
    assert any(x.startswith("commit:") and x.endswith("seçenek a") for x in deps)        # scenario 3
    rec, last = _dec(d), yamlio.read(d / "approvals.yaml")[-1]
    assert rec["status"] == "objected" and rec["provisional"]["objection"]["text"] == "en büyük olmalı"
    assert (last["action"], last["card"], last["reason"]) == ("objection", "K-01", "en büyük olmalı")
    assert not [r for r in approval_checks.signature(load_work(d)) if r.failed]         # signed (APPROVAL-02)
    assert stream.read(d)[-1]["type"] == "objection" and git.is_clean(d)
    assert _card(d, "K-01")["status"] == "awaiting_reply"                               # the team owes an answer
    with pytest.raises(Refused) as e:
        lifecycle.object_decision(d, "K-01", "yine")
    assert e.value.key == "policy.object.state"
    r = lifecycle.respond(d, "K-01", "b'ye dönüyoruz")
    assert r["dependents"] == deps and _dec(d)["status"] == "reverted" and _dec(d)["chosen"] == "b"
    assert _dec(d)["provisional"]["reverted_work"] == deps and _card(d, "K-01")["status"] == "closed"


def test_kept_after_objection_needs_the_chief(shop):
    """2.3: D3 — keeping an objected decision is the team's reasoned reply and the chief's approval
    (objected_kept); until then the gate does not pass"""
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    lifecycle.object_decision(d, "K-01", "neden a?")
    lifecycle.respond(d, "K-01", "a daha hafif; ölçüm ekte", keep=True)
    assert _dec(d)["status"] == "objected" and _card(d, "K-01")["status"] == "open"
    review(d)
    gates.stage_finish(d, "G0")
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "policy.gate.open_objection" and e.value.data["ids"] == "K-01"
    chief.approve(d, "K-01", option="a")
    assert (_dec(d)["status"], _dec(d)["provisional"]["outcome"]) == ("approved", "objected_kept")


def test_gate_pass_accepts_provisional_decisions_and_lists_them(shop):
    """2.3: D4 — scenario 1: the gate card lists the provisional decisions its pass accepts and says approving it
    approves them; the pass makes them accepted_at_gate with their option and a `decision` stream line;
    scenario 2: a decision the chief approved before the gate is not listed nor changed; scenario 3: a hold
    decision is not listed and stays open"""
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    open_decision(d, "K-02", "renk", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    open_decision(d, "K-03", "malzeme", _opts(a="x", b="y"), "g", branched=False, category="material", **TEXT)
    chief.approve(d, "K-02", option="b")
    review(d)
    gates.stage_finish(d, "G0")
    card = yamlio.read(d / "cards" / "O-G0.yaml")
    assert [x["id"] for x in card["values"]["provisional"]] == ["K-01"]
    assert t("policy.gate.accepts", ids="K-01") in card["if_approved"]
    out = chief.approve(d, "O-G0")
    k1, k2, k3 = (_dec(d, x) for x in ("K-01", "K-02", "K-03"))
    assert (k1["status"], k1["chosen"], k1["provisional"]["outcome"]) == ("accepted_at_gate", "a",
                                                                          "accepted_no_objection")
    assert k1["approved_version"] and k1["history"][-1]["note"] == f"{code}-G0" and out["gate"]["accepted"] == ["K-01"]
    assert (k2["status"], k2["chosen"]) == ("approved", "b") and k3["status"] == "proposed"
    assert _card(d, "K-01")["status"] == "approved" and _card(d, "K-03")["status"] == "open"
    line = stream.read(d)[-1]
    assert line["type"] == "decision" and {"kind": "decision", "id": "K-01"} in line["refs"] and git.is_clean(d)
    with pytest.raises(Refused) as e:
        lifecycle.object_decision(d, "K-01", "geç kaldım")
    assert e.value.key == "policy.object.state"


def test_objected_decision_blocks_the_gate_until_reverted(shop):
    """2.3: D4 — an objected decision is not accepted: the gate does not pass while it is open; after the team goes
    back to the alternative the gate passes and the reverted decision stays reverted (not accepted)"""
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    lifecycle.object_decision(d, "K-01", "a olmaz")
    review(d)
    gates.stage_finish(d, "G0")
    assert yamlio.read(d / "cards" / "O-G0.yaml")["values"]["objected"] == ["K-01"]
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "policy.gate.open_objection"
    lifecycle.respond(d, "K-01", "b'ye döndük")
    _pass(d, "G0")
    assert _dec(d)["status"] == "reverted" and f"{code}-G0" in git.git("tag", "--list", cwd=d).split()


def test_every_stage_finish_measures_the_stage(shop, monkeypatch):
    """2.3: D5 — each stage finish computes the measures (§8.2): they are on the gate card (values.policy), in the
    request's log entry, and the gate's stream line refers to that card (2/2 stage finishes)"""
    from datetime import datetime, timedelta
    from itertools import count

    from mekanik.core import clock

    start, n = datetime.now().astimezone(), count()   # one second per stamp: a fast test still has stages
    monkeypatch.setattr(clock, "now", lambda: (start + timedelta(seconds=next(n))).isoformat(timespec="seconds"))
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    for gate, made in (("G0", 1), ("G1", 0)):
        _pass(d, gate)
        m = yamlio.read(d / "cards" / f"O-{gate}.yaml")["values"]["policy"]
        assert m["gate"] == gate and m["provisional_made"] == made and m["questions_limit"] == 5
        assert set(m) >= {"questions_asked", "provisional_reverted", "revert_rate", "time_to_answer"}
        entry = next(e for e in log_entries(d) if e["title"].startswith(t("process.gate.requested", gate=gate)))
        assert metrics.line(m) in entry["body"]
        line = next(e for e in stream.read(d) if e["type"] == "gate" and {"kind": "card", "id": f"O-{gate}"} in e[
            "refs"])
        assert line["commit"]


@pytest.mark.parametrize("cls, gate", [("A", "G4"), ("C", "G5")])
def test_unmet_mandatory_requirement_stops_g4_and_g5(shop, cls, gate):
    """2.5: F5 — at G4 and G5 a mandatory requirement not met (or only awaiting evidence) stops the gate pass
    (required checklist item, REQ-01 block); met with evidence it passes the item"""
    code, d = _ready(cls)
    doc = yamlio.read(d / "work.yaml")
    doc["process"]["stage"] = gate
    yamlio.write(d / "work.yaml", doc)
    view, _, results, cards = evaluate(d)
    assert [r.status for r in results if r.rule == "REQ-01"] == ["block"]
    with pytest.raises(Refused) as e:
        gates.ready_to_pass(d, view, gate, results, cards)
    assert e.value.key == "process.gate.required_failed"
    assert not next(x for x in gates.items(view, gate, results, cards) if x["id"] == "requirements_met")["ok"]
    req = yamlio.read(d / "requirements.yaml")
    req["items"][0]["evaluation"] = {"status": "met", "at": gate, "evidence": [{"kind": "check", "id": "BED-02"}]}
    yamlio.write(d / "requirements.yaml", req)
    view, _, results, cards = evaluate(d)
    assert [r.status for r in results if r.rule == "REQ-01"] == ["pass"]
    assert next(x for x in gates.items(view, gate, results, cards) if x["id"] == "requirements_met")["ok"]


def test_return_g3_to_g2_keeps_the_tag_and_asks_the_gate_again(shop):
    """new: Ö-17, E-26 — `gate back G2` from stage G3: the chief's signed reason, the G2 tag stays, a return tag,
    G2 in progress again; its new pass is tagged <code>-G2-2; only the profile's return path is allowed"""
    code, d = _ready("B")
    for gate in ("G0", "G1", "G2"):
        _pass(d, gate)
    assert load_work(d).stage == "G3"
    with pytest.raises(Refused) as e:
        gates.gate_back(d, "G1", "kavram yanlış")
    assert e.value.key == "policy.back.not_allowed"
    with pytest.raises(Refused) as e:
        gates.gate_back(d, "G2", " ")
    assert e.value.key == "policy.back.reason"
    out = gates.gate_back(d, "G2", "ölçüler yeniden açılmalı")
    tags = set(git.git("tag", "--list", cwd=d).split())
    assert out["tag"] == f"{code}-G2-back-1" and {f"{code}-G2", out["tag"]} <= tags
    v = load_work(d)
    assert v.stage == "G2" == gates.stage(d, v) and "G2" not in gates.passed(d, code)
    gs = v.doc["process"]["gate_status"]
    assert gs["G2"]["status"] == "in_progress" and gs["G3"]["status"] == "returned"
    assert gs["G2"]["returns"][0]["reason"] == "ölçüler yeniden açılmalı"
    rec = yamlio.read(d / "approvals.yaml")[-1]
    assert (rec["action"], rec["card"]) == ("comment", "O-G2") and not [
        r for r in approval_checks.signature(v) if r.failed]
    chief.reply(d, "O-G2", "ölçüler yeniden bakıldı")
    res = _pass(d, "G2")
    assert res["gate"]["tag"] == f"{code}-G2-2" and "G2" in gates.passed(d, code) and load_work(d).stage == "G3"


def test_policy_numbers_come_from_t06_unless_the_config_says(monkeypatch):
    """2.3: D6 — the numbers of T-06 (window 10, threshold 20 %, 5 branched provisional, 5 questions per stage) from
    stdlib/policy; the workshop config's policy wins"""
    from mekanik.core import policy

    assert [policy.number(n) for n in ("revert_window", "revert_rate_threshold", "max_open_provisional",
                                       "max_questions_per_stage")] == [10, 0.2, 5, 5]
    monkeypatch.setattr(policy, "_config", lambda: {"revert_rate_threshold": {"value": 0.3}, "revert_window": 4})
    assert (policy.number("revert_rate_threshold"), policy.number("revert_window")) == (0.3, 4)



def _preconditions(d) -> None:
    """G0's preconditions (I's INTAKE-01, STDMAP-01): a standard map and the understanding summary reviewed,
    submitted and approved (signed) by the chief."""
    from mekanik.core.intake import summary

    yamlio.write(d / "stdmap.yaml", [])
    git.commit(d, git.message("standart haritası", None, "project_engineer"), [str(d / "stdmap.yaml")], TEAM)
    summary.summarize(d)
    review(d)
    summary.submit(d)
    chief.approve(d, "T-01")


def test_g0_does_not_pass_without_its_preconditions(shop):
    """2.2/2.5: C6, F8 (gate side) — the required G0 item `preconditions_met`: without an approved understanding
    summary and a standard map (I's precondition results) the G0 pass is refused; with them it passes. A work
    without a work type predates intake and is not held (schema 1.1 makes the work type required)"""
    code = works.new_work("TST", "SYN", "Ön koşul", "C", "sınama", "testler geçer", work_type="analysis")
    d = works.find(code)
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    item = next(x for x in yamlio.read(d / "cards" / "O-G0.yaml")["checks"] if x["rule"] == "G0.preconditions_met")
    assert item["result"] == "block"
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "process.gate.required_failed" and f"{code}-G0" not in git.git("tag", "--list", cwd=d)
    _preconditions(d)
    res = _pass(d, "G0")
    assert res["gate"]["tag"] == f"{code}-G0" and load_work(d).stage == "G1"
