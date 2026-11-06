# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wave 2.2 remainders with git and the chief's signed records: an open objection waits in `pending` (D3), the
chosen branch of a decision accepted at the gate merges into the work branch (D4), the main-dimension mark is the
chief's (KM-19) and a release request rests on critical calcs (§10.2; needs OCCT). The figures of the decision cards
come from the stand-in package of tests/core/test_policy_flow.py (no mech)."""

from __future__ import annotations

import pytest
from test_policy_flow import TEXT, Figures, _dec, _opts, _ready
from test_store import PARAMS, new, prepare, review

from dataclasses import replace

from mekanik.core import yamlio
from mekanik.core.builtin import SPEC
from mekanik.core.checks import regress
from mekanik.core.checks.builtin import MAIN_DIMENSION
from mekanik.core.decisions import open_decision
from mekanik.core.policy import lifecycle
from mekanik.core.process import Refused, chief, gates, release
from mekanik.core.process.step import evaluate, step
from mekanik.core.store import git
from mekanik.plugins import PackageSpec, set_registry

MODEL = '''import cadquery as cq


def parts(p):
    return {"blok": cq.Workplane().box(p.blok_en, p.blok_en, p.blok_kalinlik).val()}
'''
FORCE = 'ID = "{id}"\n\n\ndef calculate(c, model):\n    c.magnitude("f", {expr}, "N", {level}, "{method}")\n' \
        '    c.result("f", c.input("blok_en"), "N")\n'


@pytest.fixture
def figures():
    set_registry([SPEC, PackageSpec(id="fig", version="0.1.0", model=Figures())])


def test_open_objection_waits_in_pending_until_answered(shop, figures):
    """2.3: D3 — the chief's objection is a note the team owes an answer to: `pending` lists it, `reply` sends the
    team to `respond` (the answer moves the decision), and after the answer it is no longer pending"""
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "g", branched=False, **TEXT)
    lifecycle.object_decision(d, "K-01", "neden a?")
    (p,) = [x for x in chief.pending(d) if x["card"] == "K-01"]
    assert (p["action"], p["text"]) == ("objection", "neden a?")
    with pytest.raises(Refused) as e:
        chief.reply(d, "K-01", "a daha hafif")
    assert e.value.key == "process.reply.objection"
    lifecycle.respond(d, "K-01", "b'ye döndük")
    assert not [x for x in chief.pending(d) if x["card"] == "K-01"] and _dec(d)["status"] == "reverted"


def test_gate_pass_merges_the_chosen_branch_of_an_accepted_decision(shop, figures, tmp_path):
    """2.3: D4 — a branched provisional decision accepted at the gate (no objection) has its chosen branch merged
    into the work branch, as an approved decision's is: the branch's value is in params.yaml after the pass"""
    code, d = _ready()
    open_decision(d, "K-01", "en", _opts(a="x", b="y"), "g", **TEXT)
    git.git("worktree", "add", "-q", str(wt := tmp_path / "wt"), f"{code}/decision/K-01-a", cwd=d)
    yamlio.write(wt / "sentetik" / code / "params.yaml", {**PARAMS, "blok_en": {**PARAMS["blok_en"], "value": 26.0}})
    step(wt / "sentetik" / code, "seçenek a", "design_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    out = chief.approve(d, "O-G0")
    k = _dec(d)
    assert out["gate"]["accepted"] == ["K-01"] and out["gate"]["merged"] == {"K-01": "merged"}
    assert k["status"] == "accepted_at_gate" and next(o for o in k["options"] if o["id"] == "a")["affected"]
    assert yamlio.read(d / "params.yaml")["blok_en"]["value"] == 26.0 and git.is_clean(d)
    git.git("merge-base", "--is-ancestor", f"{code}/decision/K-01-a", "HEAD", cwd=d)   # raises when not merged


def test_team_cannot_set_the_main_dimension_mark(shop, figures):
    """2.3: KM-19 — a mark the team sets in its own commit blocks (MAINDIM-01); the chief's signed value entry with
    the mark makes it his, and the check passes"""
    code, d = _ready()
    raw = yamlio.read(d / "params.yaml")
    raw["blok_en"]["main_dimension"] = True
    yamlio.write(d / "params.yaml", raw)
    step(d, "ana ölçü", "project_engineer")
    (r,) = [r for r in evaluate(d)[2] if r.rule == "MAINDIM-01"]
    assert (r.status, r.msg, r.ref) == ("block", "policy.maindim.set", "blok_en")
    chief.value(d, "blok_en", 20.0, "ana ölçü", "S-01", main=True)
    assert [r.status for r in evaluate(d)[2] if r.rule == "MAINDIM-01"] == ["pass"]


def test_main_dimension_check_fails_its_subcases_when_uniform(shop, figures):
    """2.3: KM-19, F2 for MAINDIM-01 — on a work with history the chief's signed mark passes and the team's blocks;
    an "always block" or "always pass" fake of the check fails the subcase"""
    code, d = _ready()
    chief.value(d, "blok_en", 20.0, "ana ölçü", "S-01", main=True)
    raw = yamlio.read(d / "params.yaml")
    raw["blok_kalinlik"]["main_dimension"] = True
    yamlio.write(d / "params.yaml", raw)
    step(d, "ekip işareti", "project_engineer")
    yamlio.write(d / "expected.yaml", {"subcases": [{"id": "maindim", "expect": [
        {"check": "main_dimension", "ref": "blok_kalinlik", "result": "block"},
        {"check": "main_dimension", "ref": "blok_en", "result": "pass"}]}]})
    real = [s.passed for s in regress.run_case(d, [MAIN_DIMENSION])]
    fakes = [[s.passed for s in regress.run_case(d, [replace(MAIN_DIMENSION, run=lambda *a, st=st, **kw: [
        replace(r, status=st) for r in MAIN_DIMENSION.run(*a, **kw)])])] for st in ("block", "pass")]
    assert real == [True] and fakes == [[False], [False]]


def test_release_request_rests_on_critical_calcs(shop):
    """2.5: §10.2 — the calcs a release request names as its basis are critical: an unknown one is refused, a
    second method that disagrees (CALC-03) refuses the request; agreeing, the card keeps the basis and CALC-03
    counts the calc critical because of it"""
    pytest.importorskip("cadquery")
    code, d = new()
    prepare(d, model=MODEL)
    yamlio.write_text(d / "calcs" / "h1.py", FORCE.format(id="h1", expr='c.input("blok_en")', level=1, method="el"))
    yamlio.write_text(d / "calcs" / "h2.py", FORCE.format(id="h2", expr='c.input("blok_en") * 2', level=2,
                                                          method="FEA"))
    step(d, "hesaplar", "project_engineer")
    review(d)
    with pytest.raises(Refused) as e:
        release.release_request(d, basis=["yok"])
    assert e.value.key == "policy.release.basis_unknown"
    with pytest.raises(Refused) as e:
        release.release_request(d, basis=["h1"])
    assert e.value.key == "process.release.blocked" and [(r.ref, r.extra["status"]) for r in e.value.data[
        "results"] if r.rule == "CALC-03"] == [("h1", "disagree")]
    yamlio.write_text(d / "calcs" / "h2.py", FORCE.format(id="h2", expr='c.input("blok_en") + 1', level=2,
                                                          method="FEA"))
    step(d, "ikinci yöntem", "project_engineer")
    review(d)
    s = release.release_request(d, basis=["h1"])
    assert yamlio.read(d / "cards" / f"B-{s['no']}.yaml")["subject"]["basis"] == ["h1"]
    (r,) = [r for r in evaluate(d)[2] if r.rule == "CALC-03"]
    assert (r.ref, r.status, r.args["why"]) == ("h1", "pass", f"B-{s['no']}")
