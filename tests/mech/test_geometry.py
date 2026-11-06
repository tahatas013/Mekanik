# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model, geometric checks, export and drawings (OCCT)."""

from __future__ import annotations

import pytest

from mech_data import FITS, PARAMS
from mekanik.core.i18n import num, t
from mekanik_mech import checks

pytestmark = pytest.mark.occt

MODEL = '''
import cadquery as cq


def parts(p):
    a = cq.Workplane().box(30, 30, 10).faces(">Z").workplane().hole(p.hole_d).val()
    b = cq.Workplane().circle(p.shaft_d / 2).extrude(20).translate((0, 0, -10))
    return {"A": a, "B": b}
'''


# ------------------------------------------------------------ SOLID-01, INTERF-01, UNREG-01

def test_interference_caught_clearance_passes(work, shaft_hole):
    """old: test_cekirdek::girisim_yakalanir_ve_bosluklu_gecer"""
    v = work()
    bad = checks.interference(v, shaft_hole(11.0))
    assert any(r.rule == "INTERF-01" and r.failed and r.ref == "A-B" for r in bad)
    good = checks.interference(v, shaft_hole(9.7))
    assert all(r.status == "pass" for r in good) and {r.rule for r in good} == {"SOLID-01", "INTERF-01"}


def test_unregistered_fit_warns_registered_passes(work, shaft_hole):
    """old: test_cekirdek::kayitsiz_gecme_uyari_kayitli_gecer"""
    assert all(r.status == "pass" for r in checks.unregistered_fit(work(), shaft_hole(9.7)))   # G-01: Ø10,0 ↔ Ø9,7
    r = checks.unregistered_fit(work(fits=[]), shaft_hole(9.7))
    assert [(x.status, x.ref) for x in r] == [("warn", "A-B")]


def test_distant_diameters_are_not_unregistered(work, shaft_hole):
    """old: test_cekirdek::uzak_caplar_kayitsiz_sayilmaz"""
    assert checks.unregistered_fit(work(fits=[]), shaft_hole(6.0))[0].status == "pass"   # 4 mm ≥ 3 mm


def test_no_model_is_reported(work):
    v = work()
    assert checks.interference(v, None)[0].msg == "mech.solid01.no_model"
    assert checks.unregistered_fit(v, None)[0].status == "warn"


def test_filleted_block_mesh_is_closed(tmp_path):
    """old: test_cekirdek::yuvarlatilmis_kose_agi_kapali"""
    import cadquery as cq
    import trimesh

    from mekanik_mech import export, geom

    s = cq.Workplane().box(10, 51, 6.7).edges().fillet(2).val()
    m = geom.mesh(s)
    assert m.is_watertight and m.is_volume and abs(m.volume - s.Volume()) < 0.01 * s.Volume()
    assert trimesh.load(export.stl({"block": s}, tmp_path)[0]).is_watertight


# ------------------------------------------------------------ export and drawings

def test_step_stl_tessellation(tmp_path, shaft_hole):
    """old: test_cekirdek::step_stl_tessellation"""
    from mekanik_mech import export

    p = shaft_hole(9.7)
    assert export.step(p, tmp_path / "m.step").stat().st_size > 0
    assert [y.name for y in export.stl(p, tmp_path / "stl")] == ["A.stl", "B.stl"]
    assert export.write_tessellation(p, tmp_path / "m.json").stat().st_size > 0
    assert sorted(x.name for x in tmp_path.iterdir()) == ["m.json", "m.step", "stl"]   # no temp file left


def test_dimensioned_section_in_drawing_style(shaft_hole):
    """old: test_cekirdek::olculu_kesit_teknik_resim_dilinde"""
    from mekanik_mech.views import dia_dim, section

    svg = section(shaft_hole(9.7), dims=[dia_dim((0, 0, 6), (1, 0, 0), 10.0)])
    assert t("mech.view.section", name="A–A", scale="\0").split("\0")[0] in svg and 'fill="#fff"' in svg
    assert "hatch0" in svg and "hatch1" in svg                    # two parts, opposite hatching
    assert 'marker-start="url(#arrow)"' in svg and f"Ø{num(10.0)}" in svg


# ------------------------------------------------------------ model (E-19) and migration metrics

def test_model_load_writes_no_bytecode(work, monkeypatch):
    """new: Ek B §14 madde 5 (KF1-23: with bytecode writing on, as in a plain interpreter, whatever pytest's own
    setting; the interpreter's setting comes back after the load)"""
    import importlib.util
    import sys

    v = work(model=MODEL)
    from mekanik_mech import HOOKS

    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    model = HOOKS.build(v)
    assert sorted(model) == ["A", "B"] and not hasattr(model["B"], "val")   # Workplane unwrapped
    assert not list((v.root / "model").rglob("__pycache__")) and not list(v.root.rglob("*.pyc"))
    assert sys.dont_write_bytecode is False
    spec = importlib.util.spec_from_file_location("probe", v.root / "model" / "model.py")
    spec.loader.exec_module(importlib.util.module_from_spec(spec))           # the same load without the guard …
    assert list((v.root / "model").rglob("*.pyc"))                            # … writes bytecode: the check bites
    (v.root / "other").mkdir()
    assert HOOKS.build(work(root=v.root / "other")) is None        # no model/model.py


def test_metrics_and_build_path(work):
    """Migration V6 compares volume, bounding box and face count of a model built from explicit values."""
    from mekanik_mech import model as m

    v = work(model=MODEL)
    a = m.metrics(m.build(v))
    b = m.metrics(m.build_path(v.root / "model" / "model.py", {"hole_d": 10.0, "shaft_d": 9.7}))
    assert a == b and a["A"]["solids"] == 1 and a["B"]["faces"] == 3
    assert a["A"]["bbox"] == pytest.approx((30, 30, 10)) and a["B"]["volume"] == pytest.approx(3.14159 * 4.85 ** 2 * 20,
                                                                                               rel=1e-3)
    assert m.summary(m.build(v)).startswith(t("mech.model.summary", n=2, x="\0", y="", z="").split("\0")[0])


# ------------------------------------------------------------ card figures (Ek B §14 madde 6, 7)

def _plates():
    import cadquery as cq

    def make(v: dict) -> dict:
        plate = cq.Workplane().box(40, 30, v["thick"], centered=(True, True, False)).faces(">Z").workplane() \
            .hole(v["hole"]).val()
        pin = cq.Workplane().box(10, 10, 5, centered=(True, False, False)).translate((0, 15 + v["gap"], 0)).val()
        return {"plate": plate, "pin": pin}
    return make, {"thick": 4.0, "hole": 8.0, "gap": 6.0}


@pytest.mark.parametrize("name,kind,text", [("hole", "diameter", "Ø"), ("thick", "plane", ""),
                                            ("gap", "placement", "")])
def test_param_effect_finds_dimension(name, kind, text):
    """new: Ek B §14 madde 6 (diameter, moved plane, moved part)"""
    from mekanik_mech.card_views import param_effect

    make, vals = _plates()
    e = param_effect(make, vals, name, "mm")
    assert e.dim is not None and e.dim.text == f"{text}{num(vals[name])}"
    a, b = e.dim.a, e.dim.b
    assert sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5 == pytest.approx(vals[name], abs=1e-6)
    assert e.parts == {"diameter": ["plate"], "plane": ["plate"], "placement": ["plate", "pin"]}[kind]


def test_fit_section_and_isometric(work, shaft_hole):
    """new: Ek B §14 madde 7"""
    from mekanik_mech.card_views import card_visuals, fit_axes

    v, model = work(), shaft_hole(9.7)
    e = fit_axes(v, model)["G-01"]
    assert (e["hole"], e["parts"]) == (10.0, ["A", "B"]) and e["shaft"] == pytest.approx(9.7)
    figs, untraced = card_visuals(v, {"type": "mech:fit", "subject": {"fit": "G-01"}}, model)
    (title, svg), = figs
    assert title == t("mech.view.fit_section", fit="G-01") and f"Ø{num(10.0)}" in svg and f"Ø{num(9.7)}" in svg
    assert untraced == [] and "hatch1" in svg
    (_, iso), = card_visuals(v, {"type": "deviation", "subject": {}}, model)[0]
    assert iso.lstrip().startswith("<?xml") and "<svg" in iso
    assert card_visuals(v, {"type": "consistency", "subject": {}}, model) is None
    assert fit_axes(v, shaft_hole(9.0)) == {}                     # diameters do not match the record


def test_param_figure_and_untraced_value(work):
    """A parameter card shows its dimension in the model; a value with no trace is reported, not drawn."""
    from mekanik_mech.card_views import card_visuals

    p = {**PARAMS, "spare": {"value": 2.0, "unit": "mm", "source": "assumption"}}
    v = work(params=p, model=MODEL)
    figs, untraced = card_visuals(v, {"type": "assumption", "subject": {"params": ["hole_d"]}}, None)
    assert len(figs) == 1 and f"Ø{num(10.0)}" in figs[0][1] and untraced == []
    figs, untraced = card_visuals(v, {"type": "assumption_list", "subject": {"params": ["hole_d", "spare"]}}, None)
    assert len(figs) == 1 and figs[0][0].startswith(f"1 · hole_d = {num(10.0)} mm")
    assert untraced == ["spare"]
    card = {"type": "assumption", "subject": {"params": ["spare"]}}
    figs, _ = card_visuals(v, card, None, calc_uses={"spare": ["c1"]})
    assert t("mech.view.calc_input") in figs[0][0] and "c1" in figs[0][1]


def test_fit_cards_follow_geometric_deviation(work, shaft_hole):
    """Interference results become deviation cards keyed by check and ref."""
    from mekanik_mech import cards

    v = work(fits=FITS)
    rs = checks.interference(v, shaft_hole(11.0))
    (c,) = cards.deviation_cards(v, rs)
    assert c["key"] == "interference:A-B" and c["type"] == "deviation" and c["triggers"] == ["deviation"]


def test_decision_options_drawn_at_one_scale(work):
    """Decision options side by side (E-17: an option's values do not leak into another); identical drawings mean
    the options do not differ in the model, so no figure is given."""
    from mekanik_mech.card_views import card_visuals

    v = work(model=MODEL)
    q = lambda n, x: {"name": n, "quantity": {"value": x, "unit": "mm", "source": "decision"}}   # noqa: E731
    v.decisions.append({"id": "K-01", "options": [{"id": "a", "title": "a", "values": [q("hole_d", 8.0)]},
                                                  {"id": "b", "title": "b", "values": [q("hole_d", 12.0)]}]})
    card = {"type": "decision", "subject": {"decision": "K-01"}, "visual_selection": {"view": "top"}}
    figs, _ = card_visuals(v, card, {"A": None})
    assert [f[0] for f in figs] == ["a", "b"] and f"{num(12.0)}" in figs[1][1] and f"{num(8.0)}" in figs[0][1]
    assert t("mech.view.option", id="A", where=t("mech.view.dir.top")) in figs[0][1]
    v.decisions[0]["options"][1]["values"] = [q("hole_d", 8.0)]
    assert card_visuals(v, card, {"A": None}) == ([], [])
    v.decisions[0]["options"][1]["values"] = [q("hole_d", 12.0)]
    sliced = card_visuals(v, {**card, "visual_selection": {"section": {"z": 0}}}, {"A": None})[0]
    assert len(sliced) == 2 and all(t("mech.view.slice", axis="Z", pos=num(0)) in s for _, s in sliced)
