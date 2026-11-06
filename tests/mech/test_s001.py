# SPDX-License-Identifier: AGPL-3.0-or-later
"""The mech sub-cases of the synthetic case S-001 (tests/fixtures/surec/S-001/beklenen.yaml), written by hand in v1
form and run through the whole registry (core + mech + print3d): checks, then cards. Not the migration output
(wave 2 · F produces that); it checks that mech meets the core's interfaces with the old expectations."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mech_data import WORK


PARAMS = {
    "a_delik_cap": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
    "g01_bosluk": {"value": 0.3, "unit": "mm", "source": "decision"},
    "b_mil_cap": {"unit": "mm", "source": "derived", "formula": "a_delik_cap - g01_bosluk"},
    "c_delik_cap": {"value": 8.0, "unit": "mm", "source": "decision"},
    "d_mil_cap": {"value": 8.5, "unit": "mm", "source": "decision"},
    "e_delik_cap": {"value": 12.0, "unit": "mm", "source": "measured:scanner-lidar"},
    "g03_bosluk": {"value": 0.3, "unit": "mm", "source": "decision"},
    "g_mil_cap": {"value": 11.0, "unit": "mm", "source": "decision"},
    "x_et": {"value": 2.0, "unit": "mm"},
    **{n: {"value": v, "unit": "mm", "source": "decision"}
       for n, v in (("blok_en", 30.0), ("blok_kalinlik", 10.0), ("pim_boy", 20.0), ("aralik", 50.0))},
}
FITS = {"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "nominal": "a_delik_cap",
                  "clearance": "g01_bosluk", "critical": True},
                 {"id": "G-02", "parts": ["C", "D"], "task": "sliding", "sides": {"hole": "c_delik_cap",
                                                                                   "shaft": "d_mil_cap"}},
                 {"id": "G-03", "parts": ["E", "F"], "task": "centering", "nominal": "e_delik_cap",
                  "clearance": "g03_bosluk", "critical": True}],
        "flexes": [{"id": "E-01", "part": "A", "location": "kulak", "value": 2.0, "unit": "mm", "source": "decision"},
                   {"id": "E-02", "part": "C", "location": "kulak", "value": 3.0, "unit": "mm",
                    "source": "assumption"}],
        "tool_access": []}
MODEL = (Path(__file__).resolve().parents[1] / "fixtures" / "surec" / "S-001" / "model"
         / "model.py").read_text(encoding="utf-8")


@pytest.mark.occt
def test_s001_mech_subcases(tmp_path):
    builtin = pytest.importorskip("mekanik.core.builtin")
    approval = pytest.importorskip("mekanik.core.cards.approval")
    import mekanik_mech
    import mekanik_print3d
    from mekanik.core.checks import runner
    from mekanik.core.model.work import load_work
    from mekanik.plugins import set_registry

    set_registry([builtin.SPEC, mekanik_mech.SPEC, mekanik_print3d.SPEC])
    for name, data in (("work.yaml", {**WORK, "process": {**WORK["process"], "stage": "G3"}}),
                       ("params.yaml", PARAMS), ("fits.yaml", FITS)):
        (tmp_path / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "model.py").write_text(MODEL, encoding="utf-8")
    v = load_work(tmp_path)
    approval.append(v, approval.record(v, "E-01", {"flex": "E-01"}, "approve", ("Test Mühendis", "test@example.org")))
    v = load_work(tmp_path)
    model = mekanik_mech.HOOKS.build(v)
    results = runner.run(v, model)

    def status(check, ref, **extra):
        rs = [r for r in results if r.check == check and r.ref == ref
              and all(r.extra.get(k) == x for k, x in extra.items())]
        assert rs, (check, ref)
        return "pass" if all(r.status == "pass" for r in rs) else "fail"

    expected = [("source", "x_et", "fail"), ("source", "a_delik_cap", "pass"),
                ("mech.independent_number", "G-01", "pass"), ("mech.independent_number", "G-02", "fail"),
                ("mech.fit_clearance", "G-01", "pass"), ("mech.fit_clearance", "G-02", "fail"),
                ("mech.interference", "A-B", "pass"), ("mech.interference", "C-D", "fail"),
                ("mech.interference", "A", "pass"),
                ("mech.assembly", "E-01", "pass"), ("mech.assembly", "E-02", "fail"),
                ("mech.unregistered_fit", "G-01", "pass"), ("mech.unregistered_fit", "E-G", "fail")]
    assert [(c, r, status(c, r)) for c, r, _ in expected] == expected
    assert status("uncertainty", "G-01", param="a_delik_cap") == "pass"
    assert status("uncertainty", "G-03", param="e_delik_cap") == "fail"
    clear = {r.ref: r.value for r in results if r.check == "mech.fit_clearance"}
    assert clear["G-01"] == pytest.approx(0.3) and clear["G-02"] == pytest.approx(-0.5)

    from mekanik.core.cards import generate

    cards = {c["key"]: c for c in generate(v, results)}
    assert cards["fit:G-02"]["id"] == "G-02" and "deviation" in cards["fit:G-02"]["triggers"]
    assert cards["flex:E-01"]["status"] == "approved" and cards["flex:E-02"]["status"] == "open"
    assert cards["interference:C-D"]["type"] == "deviation" and cards["interference:C-D"]["id"].startswith("S-")
    assert "unregistered_fit:E-G" in cards


H001_PARAMS = {
    "p1_mentese_delik_cap": {"value": 17.0, "unit": "mm", "source": "measured:scanner-lidar"},
    "p2_pivot_kabarti_cap": {"value": 14.0, "unit": "mm"},
    "p2_pivot_delik_cap": {"value": 7.0, "unit": "mm", "source": "measured:scanner-lidar"},
    "m6_civata_cap": {"value": 6.0, "unit": "mm", "source": "standard:ISO 261 M6 anma çapı"},
    "p4_kilit_yarik_gen": {"value": 5.0, "unit": "mm", "source": "assumption"},
    "p3_pim_boyun_cap": {"value": 4.0, "unit": "mm", "source": "assumption"},
    "p1_stop_kanal_gen": {"value": 5.0, "unit": "mm", "source": "measured:scanner-lidar"},
    "p2_stop_pim_cap": {"value": 4.5, "unit": "mm", "source": "measured:scanner-lidar"},
    "p5_m4_delik_cap": {"value": 4.3, "unit": "mm"},
    "p5_et_kalinligi": {"value": 2.2, "unit": "mm", "source": "assumption"},
    "p5_bindirme_bosluk": {"value": 0.2, "unit": "mm"},
}
H001_FITS = {"fits": [
    {"id": "G-01", "parts": ["P1", "P2"], "task": "centering", "critical": True,
     "sides": {"hole": "p1_mentese_delik_cap", "shaft": "p2_pivot_kabarti_cap"}},
    {"id": "G-02", "parts": ["P2", "civata"], "task": "rotation",
     "sides": {"hole": "p2_pivot_delik_cap", "shaft": "m6_civata_cap"}},
    {"id": "G-03", "parts": ["P4", "P3"], "task": "sliding", "sides": {"hole": "p4_kilit_yarik_gen",
                                                                        "shaft": "p3_pim_boyun_cap"}},
    {"id": "G-04", "parts": ["P1", "P2"], "task": "sliding", "sides": {"hole": "p1_stop_kanal_gen",
                                                                        "shaft": "p2_stop_pim_cap"}},
    {"id": "G-05", "parts": ["P5", "P6"], "task": "screw_clearance", "screw": "M4",
     "sides": {"hole": "p5_m4_delik_cap"}},
    {"id": "G-06", "parts": ["P5", "P6"], "nominal": "p5_et_kalinligi", "clearance": "p5_bindirme_bosluk"}],
    "flexes": [{"id": "E-01", "part": "P1", "location": "kulak, her yanda", "value": 3.2, "unit": "mm"}]}


def test_h001_mech_subcases(tmp_path):
    """H-001 (tests/fixtures/surec/H-001/beklenen.yaml) mech sub-cases 1–4, 6, 7a, 7b without a model."""
    builtin = pytest.importorskip("mekanik.core.builtin")
    import mekanik_mech
    import mekanik_print3d
    from mekanik.core.cards import generate
    from mekanik.core.checks import runner
    from mekanik.core.model.work import load_work
    from mekanik.plugins import set_registry

    set_registry([builtin.SPEC, mekanik_mech.SPEC, mekanik_print3d.SPEC])
    work = {**WORK, "code": "TST-SYN-02", "risk_class": "A", "process": {**WORK["process"], "stage": "G2",
                                                                         "gates": ["G0", "G1", "G2", "G3", "G4", "G5"]}}
    for name, data in (("work.yaml", work), ("params.yaml", H001_PARAMS), ("fits.yaml", H001_FITS)):
        (tmp_path / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    v = load_work(tmp_path)
    results = runner.run(v, None)
    got = {(r.check, r.ref): (r.status, r.value) for r in results if r.check.startswith("mech.") and r.ref}
    assert got[("mech.independent_number", "G-01")][0] == "warn"
    assert {f: got[("mech.fit_clearance", f)] for f in ("G-01", "G-02", "G-03", "G-04", "G-05")} == {
        "G-01": ("warn", 3.0), "G-02": ("warn", 1.0), "G-03": ("warn", 1.0), "G-04": ("pass", 0.5),
        "G-05": ("pass", 4.3)}
    assert got[("mech.fit_clearance", "G-06")][0] == "warn" and got[("mech.assembly", "E-01")][0] == "warn"
    assert next(r for r in results if r.check == "source" and r.ref == "E-01").status == "block"
    cards = {c["key"]: c for c in generate(v, results)}
    assert "provisional_profile" in cards["fit:G-04"]["triggers"]
    assert "task_undefined" in cards["fit:G-06"]["triggers"]
    assert cards["flex:E-01"]["triggers"] == ["assembly_flex"]
