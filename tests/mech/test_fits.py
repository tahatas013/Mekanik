# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fit record and fit checks without OCCT (FIT-01, FIT-02, BOLT-01, ASSY-01; SOURCE-01 and UNCERT-01 inputs)."""

from __future__ import annotations

import subprocess
import sys

import pytest
import yaml

from mech_data import FITS, PARAMS
from mekanik.core.errors import SchemaError
from mekanik_mech import cards, checks, fits


def _params(**changes):
    out = {k: dict(v) for k, v in PARAMS.items()}
    for name, fields in changes.items():
        out[name] = {**out.get(name, {}), **fields}
    return out


# ------------------------------------------------------------ SOURCE-01 input: a flex without a source

def test_unsourced_flex_blocks(work):
    """old: test_cekirdek::kaynaksiz_esneme_engel"""
    v = work(flexes=[{"id": "E-01", "part": "K", "value": 3.2, "unit": "mm"}])
    sv = {x.ref: x for x in fits.sourced_values(v)}
    assert sv["E-01"].source is None and sv["E-01"].value == 3.2 and sv["E-01"].unit == "mm"
    try:   # the core check (wave 2 · A) sees the same value as a block
        from mekanik.core.builtin import SPEC as CORE
    except ImportError:
        return
    source = next((c for c in CORE.checks if c.id == "source"), None)
    if source is not None:
        from mekanik.plugins import set_registry

        import mekanik_mech

        set_registry([CORE, mekanik_mech.SPEC])
        assert next(r for r in source.run(v, None) if r.ref == "E-01").status == "block"


# ------------------------------------------------------------ FIT-01: independent number

def test_fit_defined_by_independent_numbers_is_caught(work):
    """old: test_cekirdek::bagimsiz_sayiyla_tanimli_gecme_yakalanir"""
    p = {"hole": {"value": 17.0, "unit": "mm", "source": "decision"},
         "boss": {"value": 14.0, "unit": "mm", "source": "decision"}}
    f = [{"id": "G-01", "parts": ["K", "D"], "task": "centering", "sides": {"hole": "hole", "shaft": "boss"}}]
    r = checks.independent_number(work(params=p, fits=f))
    assert r[0].failed and r[0].ref == "G-01" and r[0].msg == "mech.fit01.independent" and r[0].rule == "FIT-01"


def test_nominal_clearance_fit_is_not_independent_number(work):
    """old: test_cekirdek::nominal_bosluk_gecmesi_bagimsiz_sayi_degil"""
    assert checks.independent_number(work())[0].status == "pass"


def test_derived_side_is_not_independent_number(work):
    """old: test_cekirdek::turetilen_taraf_bagimsiz_sayi_degil"""
    f = [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "sides": {"hole": "hole_d", "shaft": "shaft_d"}}]
    assert checks.independent_number(work(fits=f))[0].status == "pass"


@pytest.mark.parametrize("params,fit", [
    # a formula that does not rest on the other side
    ({"hole": {"value": 17.0, "unit": "mm", "source": "decision"},
      "other": {"value": 1.0, "unit": "mm", "source": "decision"},
      "boss": {"unit": "mm", "source": "derived", "formula": "other * 14"}},
     {"sides": {"hole": "hole", "shaft": "boss"}}),
    ({"boss": {"value": 14.0, "unit": "mm", "source": "decision"}}, {"sides": {"shaft": "boss"}}),
    ({"hole": {"value": 17.0, "unit": "mm", "source": "decision"}}, {"nominal": "hole"}),
])
def test_independent_number_cannot_be_bypassed(work, params, fit):
    """old: test_cekirdek::bagimsiz_sayi_atlatilamaz"""
    f = [{"id": "G-01", "parts": ["K", "D"], "task": "centering", **fit}]
    assert checks.independent_number(work(params=params, fits=f))[0].failed


# ------------------------------------------------------------ FIT-02 and BOLT-01: clearance bands

@pytest.mark.parametrize("task,gap,expected", [
    ("centering", 0.3, "pass"), ("centering", 0.4, "pass"), ("centering", 0.41, "warn"), ("centering", 0.1, "warn"),
    ("sliding", 0.6, "pass"), ("rotation", 1.0, "warn"), ("press", 0.1, "warn"),
])
def test_fit_clearance_bands(work, task, gap, expected):
    """old: test_cekirdek::gecme_boslugu_bantlari"""
    v = work(params=_params(gap={"value": gap}), fits=[{**FITS[0], "task": task}])
    r = checks.fit_clearance(v)[0]
    assert (r.rule, r.status) == ("FIT-02", expected)
    if task == "press":   # profile has no limit for press fits
        assert r.extra == {"undefined": "limit"}


def test_failing_fit_blocks_when_finalizing(work):
    """old: test_cekirdek::kesinlestirmede_kalan_gecme_engel"""
    r = checks.fit_clearance(work(params=_params(gap={"value": 3.0}), stage="G3"))[0]
    assert r.status == "block" and r.value == pytest.approx(3.0)


def test_screw_clearance_and_undefined_task(work):
    """BOLT-01 reads the profile screw table; a fit without a task has no limit (H-001 sub-cases 7a, 7b)."""
    p = {"m4_hole": {"value": 4.3, "unit": "mm"}, "wall": {"value": 2.2, "unit": "mm", "source": "assumption"},
         "lap": {"value": 0.2, "unit": "mm"}, "m5_hole": {"value": 5.3, "unit": "mm", "source": "decision"}}
    f = [{"id": "G-05", "parts": ["P5", "P6"], "task": "screw_clearance", "screw": "M4", "sides": {"hole": "m4_hole"}},
         {"id": "G-06", "parts": ["P5", "P6"], "nominal": "wall", "clearance": "lap"},
         {"id": "G-07", "parts": ["P5", "P6"], "task": "screw_clearance", "screw": "M5", "sides": {"hole": "m5_hole"}}]
    r = {x.ref: x for x in checks.fit_clearance(work(params=p, fits=f))}
    assert (r["G-05"].rule, r["G-05"].status, r["G-05"].value) == ("BOLT-01", "pass", 4.3)
    assert (r["G-06"].status, r["G-06"].extra) == ("warn", {"undefined": "task"})
    assert (r["G-07"].status, r["G-07"].extra) == ("warn", {"undefined": "screw"})
    assert checks.independent_number(work(params=p, fits=f))[0].status == "pass"


# ------------------------------------------------------------ ASSY-01 and subject values, with the core's approvals

CHIEF = ("Test Mühendis", "test@example.org")   # tests/fixtures/config identities.chief


def test_unapproved_flex_fails_approved_passes(work):
    """old: test_cekirdek::onaysiz_esneme_kalir_onayli_gecer"""
    approval = pytest.importorskip("mekanik.core.cards.approval")
    from mekanik.core.model.work import load_work

    v = work(flexes=[{"id": "E-01", "part": "K", "location": "ear", "value": 3.2, "unit": "mm", "source": "decision"}])
    r = checks.assembly(v)[0]
    assert r.failed and r.ref == "E-01" and r.extra == {"state": "none"} and r.msg == "mech.assy01.fail"
    approval.append(v, approval.record(v, "E-01", {"flex": "E-01"}, "approve", CHIEF))
    assert checks.assembly(load_work(v.root))[0].status == "pass"


def test_assembly_maps_approval_states(work, approval_states):
    """ASSY-01 asks the approval state of the flex card (its id from cards/ when filed, else the flex id)."""
    states, calls = approval_states
    v = work(flexes=[{"id": "E-01", "part": "K", "value": 3.2, "source": "decision"}], stage="G3")
    for st, expected in (("approved", "pass"), ("dropped", "block"), ("rejected", "block"), ("none", "block")):
        states["E-01"] = st
        r = checks.assembly(v)[0]
        assert r.status == expected and calls[-1] == ("E-01", {"flex": "E-01"})
    v.cards.append({"id": "E-07", "key": "flex:E-01"})
    checks.assembly(v)
    assert calls[-1][0] == "E-07"
    assert checks.assembly(work(flexes=[]))[0].msg == "mech.assy01.none"


def test_profile_limit_change_drops_approval(work):
    """old: test_cekirdek::profil_siniri_degisince_onay_duser"""
    approval = pytest.importorskip("mekanik.core.cards.approval")
    v = work()
    subject = {"params": ["gap", "hole_d", "shaft_d"], "fit": "G-01"}
    v.approvals.append(approval.record(v, "G-01", subject, "approve", CHIEF))
    assert approval.state(v, "G-01", subject) == "approved"
    prof = v.manufacturing["profile"]
    v.manufacturing = {**v.manufacturing, "profile": {**prof, "clearance": {
        **prof["clearance"], "centering": {"lower": {"value": 0.2, "source": "assumption"},
                                           "upper": {"value": 3.5, "source": "decision"}}}}}
    assert approval.state(v, "G-01", subject) == "dropped"


def test_fit_subject_values(work):
    """The fit snapshot carries the fit record and the profile limit of its task; params are the core's part."""
    v = work()
    sv = fits.subject_values(v, {"params": ["gap"], "fit": "G-01"})
    assert sv["profile"] == {"id": "fdm-test", "version": "v0", "status": "provisional",
                             "limit": v.manufacturing["profile"]["clearance"]["centering"]}
    assert sv["fit:G-01"]["task"] == "centering" and set(sv) == {"fit:G-01", "profile"}
    assert fits.subject_values(v, {"params": ["gap"]}) is None
    assert fits.subject_values(v, {"flex": "E-09"}) == {"flex:E-09": None}


# ------------------------------------------------------------ new tests: loader, interface, cards

@pytest.mark.parametrize("doc,key", [
    ([{"id": "G-01"}], "not_dict"),
    ({"fits": {"id": "G-01"}}, "not_list"),
    ({"fits": [{"id": "G-1", "parts": ["A", "B"], "nominal": "hole_d"}]}, "fit_id"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "sides": ["a"]}]}, "sides"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "nominal": "hole_d", "critical": "no"}]}, "critical"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "nominal": "hole_d", "clearance": "gap",
                "sides": {"hole": "hole_d"}}]}, "sides_or_nominal"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "screw_clearance", "sides": {"hole": "hole_d"}}]}, "screw"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "nominal": "nope"}]}, "unknown_param"),
    ({"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "ortalama", "nominal": "hole_d"}]}, "task"),
    ({"flexes": [{"value": 3.2}]}, "required"),
    ({"flexes": [{"id": "E-01", "value": True}]}, "number"),
])
def test_fits_loader_rejects_broken_record(work, tmp_path, doc, key):
    """Loader errors of fits.yaml (old gecmeler_yukle/_montaj_dogrula cases of test_cekirdek::bozuk_girdi…)."""
    import re

    from mekanik.core.i18n import t
    from mekanik.core.model.work import load_work

    work()
    (tmp_path / "fits.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(SchemaError) as e:
        load_work(tmp_path)
    fixed = max(re.split(r"\{[a-z_]+\}", t(f"mech.fits.{key}")), key=len).replace("{{", "{").replace("}}", "}")
    assert fixed.strip() in str(e.value)


def test_param_uses_follow_formulas_and_critical_dims(work):
    """Param → fits (old gecmeye_girenler) and the measured values of critical fits with their band (UNCERT-01)."""
    f = [{**FITS[0]}, {"id": "G-02", "parts": ["C", "D"], "task": "rotation", "sides": {"hole": "hole_d",
                                                                                       "shaft": "shaft_d"}}]
    v = work(fits=f)
    uses = fits.param_uses(v)
    assert uses == {"gap": ["G-01", "G-02"], "hole_d": ["G-01", "G-02"], "shaft_d": ["G-02"]}
    (cd,) = fits.critical_dims(v)
    assert (cd.ref, cd.param, cd.task) == ("G-01", "hole_d", "centering") and cd.band == pytest.approx(0.2)


def test_fit_and_flex_cards(work):
    """Fit card triggers (provisional profile, assumption limit, deviation) and flex card; texts from the catalog."""
    flex = {"id": "E-01", "part": "K", "value": 3.2, "source": "decision"}
    v = work(params=_params(gap={"value": 3.0}), flexes=[flex])
    rs = checks.independent_number(v) + checks.fit_clearance(v)
    (fc,) = cards.fit_cards(v, rs)
    assert fc["key"] == "fit:G-01" and fc["type"] == "mech:fit" and fc["level"] == "hold"
    assert fc["triggers"] == ["provisional_profile", "assumption_limit", "deviation"]
    assert fc["subject"] == {"params": ["gap", "hole_d"], "fit": "G-01"} and fc["checks"]
    assert all(fc[k] for k in ("question", "explain", "if_approved", "if_rejected", "recorded_as"))
    assert fc["proposal"]["rationale"] == fc["checks"][0]["message"] and fc["checks"][0]["rule"] == "FIT-02"
    (ec,) = cards.flex_cards(v, rs)
    assert (ec["key"], ec["type"], ec["triggers"], ec["subject"]) == ("flex:E-01", "mech:flex", ["assembly_flex"],
                                                                       {"flex": "E-01"})


def test_mech_imports_no_occt():
    """Criterion 1.10: the package, its loader and fit checks run without OCCT."""
    code = ("import sys, mekanik_mech, mekanik_print3d, mekanik_analysis; from mekanik_mech import checks, fits, cards;"
            "assert not {'cadquery', 'OCP', 'trimesh', 'manifold3d'} & set(sys.modules), sorted(sys.modules)")
    subprocess.run([sys.executable, "-c", code], check=True)


def test_model_signature_follows_design_files_only(work):
    """Model cache key (old modelci.imza): model/, params.yaml and fits.yaml at a commit; a log commit keeps it."""
    from mekanik.core.store.git import commit, git
    from mekanik_mech.model import signature

    v = work(model="def parts(p):\n    return {}\n")
    git("init", "-q", cwd=v.root)
    me = ("Test Ekip", "ekip@example.org")
    first = commit(v.root, "a\n", identity=me)
    (v.root / "records").mkdir()
    (v.root / "records" / "log.md").write_text("x\n", encoding="utf-8")
    log = commit(v.root, "log\n", identity=me)
    assert signature(v.root, first) == signature(v.root, log) and len(signature(v.root, first)) == 40
    (v.root / "fits.yaml").write_text("fits: []\n", encoding="utf-8")
    assert signature(v.root, commit(v.root, "fits\n", identity=me)) != signature(v.root, first)
