# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report flow with a model (architecture §9.2): stream figures drawn from the model and cached (E2), the
before–after with the changed faces (E3). Needs OCCT (CadQuery) and the mech package."""

from __future__ import annotations

import json

import pytest

cq = pytest.importorskip("cadquery")

import mekanik_mech.views as views  # noqa: E402
from test_store import PARAMS, new, prepare  # noqa: E402

from mekanik.core import yamlio  # noqa: E402
from mekanik.core.model.work import load_work  # noqa: E402
from mekanik.core.process.step import step  # noqa: E402
from mekanik.core.report import figures, stream  # noqa: E402
from mekanik.core.store import git  # noqa: E402
from mekanik.plugins import registry  # noqa: E402

pytestmark = pytest.mark.occt
MODEL = '''import cadquery as cq


def parts(p):
    return {"blok": cq.Workplane().box(p.blok_en, p.blok_en, p.blok_kalinlik, centered=False).val()}
'''


def _label(f) -> str:
    """A plane by its outward normal (+Z …), any other face by its type."""
    if f.geomType() != "PLANE":
        return f.geomType()
    return next(s + a for a, v in zip("XYZ", f.normalAt().toTuple()) for s in "+-" if abs(v) > 0.5 and (v > 0) == (
        s == "+"))


def _plate(L=40.0, W=30.0, H=5.0, d=6.0, x=10.0, pin=None) -> dict:
    """A plate with a through hole, and optionally a separate pin of height `pin`."""
    hole = cq.Workplane().center(x, W / 2).circle(d / 2).extrude(H)
    parts = {"plate": cq.Workplane().box(L, W, H, centered=False).cut(hole).val()}
    return parts | ({"pin": cq.Workplane().center(30, 15).circle(2).extrude(pin).val()} if pin else {})


CHANGES = [   # (before, after, changed faces by part)
    ({}, {"H": 8.0}, {"plate": {"+Z", "+X", "-X", "+Y", "-Y", "CYLINDER"}}),   # thicker: the bottom stays
    ({}, {"d": 8.0}, {"plate": {"+Z", "-Z", "CYLINDER"}}),                     # larger hole
    ({}, {"L": 50.0}, {"plate": {"+X", "+Y", "-Y", "+Z", "-Z"}}),              # longer: the -X end and hole stay
    ({}, {"pin": 12.0}, {"pin": {"+Z", "-Z", "CYLINDER"}}),                    # a part added: all its faces
    ({"pin": 12.0}, {"pin": 20.0}, {"pin": {"+Z", "CYLINDER"}}),               # only the other part changes
]


def test_before_after_shows_the_changed_faces_of_five_synthetic_changes():
    """2.4: E3 — in 5 synthetic changes the before–after's changed face set equals the expected one (5/5); the old
    model's signatures go through JSON as in the cache; no change, no changed face"""
    hooks = registry().model_hooks()
    for before, after, want in CHANGES:
        old, cur = _plate(**before), _plate(**after)
        svg, changed = hooks.diff_svg(cur, json.loads(json.dumps(hooks.face_signatures(old))), "t")
        got = {n: [_label(cur[n].Faces()[i]) for i in ix] for n, ix in changed.items()}
        assert {n: set(v) for n, v in got.items()} == want and all(len(v) == len(set(v)) for v in got.values())
        assert svg.count("<svg") == 1
    assert hooks.diff_svg(_plate(), hooks.face_signatures(_plate()))[1] == {}


def test_stream_figures_come_from_the_model_and_are_drawn_once_per_model(shop, monkeypatch):
    """2.4: E2 — the step's figure is drawn from the model; the second drawing of the same model (the next step, or
    the same commit again) comes from the cache: hit rate 100 %; a changed model is drawn anew"""
    code, d = new()
    prepare(d, model=MODEL)
    calls, real = [], views.isometric_svg
    monkeypatch.setattr(views, "isometric_svg", lambda parts: calls.append(1) or real(parts))
    a = step(d, "bir", "project_engineer")
    b = step(d, "iki", "design_engineer")
    hooks = registry().model_hooks()
    again = figures.step_figures(d, hooks.build(load_work(d)), hooks)          # the same commit, drawn again
    assert len(calls) == 1
    svg = (d / a["visuals"][0]).read_text(encoding="utf-8")
    assert "<svg" in svg and (d / b["visuals"][0]).read_text(encoding="utf-8") == svg == again["isometric"]
    assert [e["event"]["visuals"][0]["path"] for e in (a, b)] == [a["visuals"][0], b["visuals"][0]]
    keys = [r["hash"] for e in (a, b) for r in e["event"]["refs"] if r["kind"] == "model"]
    assert keys == [again["key"]] * 2 and again["before_after"] is None
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_en": {**PARAMS["blok_en"], "value": 30.0}})
    c = step(d, "üç", "design_engineer")
    assert len(calls) == 2 and (d / c["visuals"][0]).read_text(encoding="utf-8") != svg


def test_a_model_change_step_puts_the_before_after_on_its_stream_line(shop):
    """2.4: E3 — a step that changes the model carries the before–after (changed faces in colour) as its stream
    visual, committed; a step without a change shows the model view"""
    code, d = new()
    prepare(d, model=MODEL)
    step(d, "bir", "project_engineer")
    yamlio.write(d / "params.yaml", {**PARAMS, "blok_kalinlik": {**PARAMS["blok_kalinlik"], "value": 8.0}})
    hooks = registry().model_hooks()
    pre = figures.step_figures(d, model := hooks.build(load_work(d)), hooks)
    assert {_label(model["blok"].Faces()[i]) for i in pre["changed"]["blok"]} == {"+Z", "+X", "-X", "+Y", "-Y"}
    s = step(d, "kalınlık 8", "design_engineer")
    ba = s["event"]["visuals"][0]["path"]
    assert ba.endswith("-before-after.svg") and ba in s["visuals"] and (d / ba).read_text(encoding="utf-8") == pre[
        "before_after"]
    assert ba.rsplit("/", 1)[-1] in git.git("show", "--name-only", "--format=", s["commit"], cwd=d)
    same = step(d, "değişiklik yok", "design_engineer")
    assert same["event"]["visuals"][0]["path"] == same["visuals"][0] and not same["visuals"][0].endswith(
        "-before-after.svg")
    assert stream.read(d)[-1] == same["event"] and git.is_clean(d)
    stream.verify(d)
