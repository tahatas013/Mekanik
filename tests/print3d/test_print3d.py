# SPDX-License-Identifier: AGPL-3.0-or-later
"""print3d: profile type print3d.fdm, release checks BED-01/BED-02/SINGLE-01, layout, estimate, release files."""

from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from mekanik.core.errors import SchemaError
from mekanik_print3d import profile, release

CONFIG = Path(__file__).resolve().parents[1] / "fixtures" / "config"
FDM = yaml.safe_load((CONFIG / "machines" / "fdm-test.yaml").read_text(encoding="utf-8"))


def _view(bed=None):
    prof = {**FDM["profile"], **({"bed": bed} if bed else {})}
    return SimpleNamespace(code="TST-SYN-01", manufacturing={**FDM, "profile": prof})


# ------------------------------------------------------------ profile type

def test_fixture_machine_profile_is_valid(monkeypatch):
    """The test workshop machine validates through the registry (G-30); bed is optional."""
    import mekanik_mech
    import mekanik_print3d
    from mekanik.config import load_config
    from mekanik.plugins import reset_registry, set_registry

    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(CONFIG))
    set_registry([mekanik_mech.SPEC, mekanik_print3d.SPEC])
    try:
        assert load_config().machine("fdm-test@v0")["type"] == "print3d.fdm"
    finally:
        reset_registry()
    bed = {"x": {"value": 256, "unit": "mm", "source": "manufacturer:manual"}}
    profile.validate({**FDM["profile"], "bed": bed}, "machines/x")


@pytest.mark.parametrize("change,key", [
    (lambda p: p["clearance"].pop("sliding"), "missing_tasks"),
    (lambda p: p["clearance"]["centering"]["upper"].pop("source"), "required"),
    (lambda p: p["clearance"]["centering"]["upper"].update(source="tahmin"), "source"),
    (lambda p: p["screw_clearance"]["table"].update(M4="4,3"), "number"),
    (lambda p: p.pop("screw_clearance"), "required"),
    (lambda p: p.update(bed=[220]), "not_dict"),
])
def test_profile_validation_rejects(change, key):
    """Old veri._uretim_profili_dogrula cases with v1 names."""
    import re

    from mekanik.core.i18n import t

    p = copy.deepcopy(FDM["profile"])
    change(p)
    with pytest.raises(SchemaError) as e:
        profile.validate(p, "machines/fdm-test")
    assert max(re.split(r"\{[a-z_]+\}", t(f"print3d.profile.{key}")), key=len).strip() in str(e.value)


# ------------------------------------------------------------ geometry (OCCT)

@pytest.mark.occt
def test_bed_layout_turns_to_fit():
    """old: test_cekirdek::tabla_yerlesimi_dondurerek_sigdirir"""
    import cadquery as cq

    a, placed, fits = release.place({"plate": cq.Workplane().box(230, 40, 1).val()}, 220, 220, 5)
    bb = placed["plate"].BoundingBox()
    assert fits and 0 < a < 90
    assert bb.xmin >= 5 - 1e-6 and bb.ymin >= 5 - 1e-6 and bb.xmax <= 215 + 1e-6 and bb.ymax <= 215 + 1e-6
    assert not release.place({"l": cq.Workplane().box(400, 40, 1).val()}, 220, 220, 5)[2]
    bed = {k: {"value": v, "unit": "mm", "source": "manufacturer:manual"} for k, v in (("x", 220), ("y", 220),
                                                                                         ("margin", 5))}
    (r,) = release.bed_fit(_view(bed), {"plate": cq.Workplane().box(230, 40, 1).val()})
    assert (r.rule, r.status, r.extra["angle"]) == ("BED-02", "pass", a)
    assert release.bed_fit(_view(bed), {"l": cq.Workplane().box(400, 40, 1).val()})[0].status == "warn"
    assert release.bed_fit(_view(), {"l": cq.Workplane().box(4, 4, 1).val()})[0].msg == "print3d.bed02.unknown"


@pytest.mark.occt
def test_bed_contact_defect():
    """old: test_cekirdek::tabla_temasi_kusuru"""
    import cadquery as cq

    gap = 0.5
    assert release.contact_defect(cq.Workplane().box(20, 20, 5).val(), gap) is None
    plate = cq.Workplane().box(60, 40, 1, centered=(True, True, False))
    strip = cq.Workplane().box(10, 40, 1, centered=(True, True, False)).translate((35, 0, 0))
    up = strip.translate((-1, 0, 0)).rotate((30, 0, 0.5), (30, 1, 0.5), -11)   # back edge lifts, hinge corner drops
    bad = plate.union(up).val()
    d = release.contact_defect(bad, gap)
    assert d is not None and 0 < d["height"] <= gap and d["area"] > d["contact"]
    good = plate.union(up).intersect(cq.Workplane().box(500, 500, 100, centered=(True, True, False))).val()
    assert release.contact_defect(good, gap) is None
    r = {x.ref: x for x in release.bed_contact(_view(), {"bad": bad, "good": good})}
    assert (r["bad"].rule, r["bad"].status, r["good"].status) == ("BED-01", "block", "pass")


@pytest.mark.occt
def test_disjoint_solids_are_refused():
    """new: Ek B §14 madde 9 (E-28)"""
    import cadquery as cq

    two = cq.Workplane().box(10, 10, 2).union(cq.Workplane().box(3, 3, 2).translate((20, 0, 0))).val()
    r = {x.ref: x for x in release.single_solid(_view(), {"two": two, "one": cq.Workplane().box(5, 5, 5).val()})}
    assert (r["two"].rule, r["two"].status, r["two"].value) == ("SINGLE-01", "block", 2)
    assert r["one"].status == "pass"


@pytest.mark.occt
def test_print_estimate_shell_and_infill():
    """new: Ek B §14 madde 8 (E-23: a thin part is all shell)"""
    import cadquery as cq

    thin = release.estimate({"sheet": cq.Workplane().box(100, 100, 1).val()})   # 10 cm³, all shell
    assert thin["volume_cm3"] == 10.0 and thin["filament_g"] == [12, 12]
    block = release.estimate({"block": cq.Workplane().box(40, 40, 40).val()})
    lo, hi = block["filament_g"]
    assert lo < hi < 64 * release.ESTIMATE["density"]["value"] and block["hours"][0] < block["hours"][1]


@pytest.mark.occt
def test_estimate_constants_are_data_and_the_machine_profile_wins():
    """new: KF1-14 (§4.7) — no estimate number in the code: estimate.yaml gives value + source + note for each, and
    the machine profile's `estimate` overrides it"""
    import cadquery as cq

    assert {k: sorted(v) for k, v in release.ESTIMATE.items()} == dict.fromkeys(
        ("density", "shell", "infill", "flow"), ["note", "source", "unit", "value"])
    sheet = {"sheet": cq.Workplane().box(100, 100, 1).val()}
    view = _view()
    view.manufacturing["profile"]["estimate"] = {"density": {"value": 2.0, "source": "manufacturer:sınama"}}
    assert release.estimate(sheet, view)["filament_g"] == [20, 20] and release.estimate(sheet)["filament_g"] == [12, 12]


@pytest.mark.occt
def test_release_files_and_visuals(tmp_path):
    """Release files <code>.step + stl/<part>.stl with SHA-256; card figures and estimate (old akis.baski)."""
    import hashlib

    import cadquery as cq
    from mekanik_mech import HOOKS

    model = {"plate": cq.Workplane().box(230, 40, 1).val()}
    files = HOOKS.release_files(_view(), model, tmp_path / "out")
    assert sorted(files) == ["TST-SYN-01.step", "stl/plate.stl"]
    assert files["stl/plate.stl"] == hashlib.sha256((tmp_path / "out" / "stl" / "plate.stl").read_bytes()).hexdigest()
    bed = {k: {"value": v, "source": "manufacturer:manual"} for k, v in (("x", 220), ("y", 220))}
    figs, est = HOOKS.release_visuals(_view(bed), model)
    assert len(figs) == 2 and all("<svg" in s for _, s in figs) and est["volume_cm3"] == 9.2
    assert "#B3261E" not in figs[0][1]                              # turned, it fits: no red note
