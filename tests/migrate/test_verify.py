# SPDX-License-Identifier: AGPL-3.0-or-later
"""V4–V8 (architecture §14.3): each with a passing and a failing case on stand-ins for the v1 side, then the real
modules of wave 2 (A checks and cards, B calcs, C mech/print3d) on S-001 and H-001."""

from __future__ import annotations

import shutil

import pytest

from build_cases import OLD, ROOT, build, known, snapshot
from fakes import old_cards, old_results
from mekanik.core.i18n import t
from mekanik.core import yamlio
from mekanik.core.checks.result import BLOCK, PASS, Result
from mekanik.migrate import surec_work, verify

STATUS = lambda res: {k: v["status"] for k, v in res.items()}  # noqa: E731


def _run(v1_side, migrated, tmp_path, cfg, case="S-001", old=None, **kw):
    v1_side(case, tmp_path / case, **kw)
    old, out, _ = migrated(case, old)
    return out, verify(old, out, cfg, old=snapshot(case), known=known())


@pytest.mark.parametrize("case", ["S-001", "H-001"])
def test_all_pass_when_the_v1_side_equals_the_old(v1_side, migrated, tmp_path, cfg, case):
    """new: V1–V8 pass and the report is written (records/migration-report.md)."""
    out, res = _run(v1_side, migrated, tmp_path, cfg, case)
    assert set(STATUS(res).values()) == {"pass"}, res
    report = (out / "records" / "migration-report.md").read_text(encoding="utf-8")
    assert report.count(f"| {t('status.pass')} |") == 8 and t('migrate.report.gaps') in report


def test_v4_fails_on_a_changed_level(v1_side, migrated, tmp_path, cfg):
    """new: x_et no longer blocked → the (SOURCE-01, x_et, block) pair differs."""
    flip = lambda r: Result(r.check, r.rule, PASS, r.msg, ref=r.ref) if r.ref == "x_et" else r  # noqa: E731
    _, res = _run(v1_side, migrated, tmp_path, cfg, results=old_results("S-001", flip))
    assert res["V4"]["status"] == "fail"
    assert res["V4"]["details"] == ["- ('SOURCE-01', 'x_et', 'block')", "+ ('SOURCE-01', 'x_et', 'pass')"]


def test_v4_known_changes_pass_and_unknown_new_results_fail(v1_side, migrated, tmp_path, cfg):
    """new: listed intentional changes (APPROVAL-02, the MG-01 card) are accepted; anything else is a difference."""
    extra = [Result("approval_state", "APPROVAL-01", BLOCK, "x", ref="MG-01"),
             Result("approval_signature", "APPROVAL-02", BLOCK, "x", ref="E-01")]
    _, res = _run(v1_side, migrated, tmp_path, cfg, results=old_results("S-001") + extra)
    assert res["V4"]["status"] == "pass"
    _, res = _run(v1_side, migrated, tmp_path, cfg,
                  results=old_results("S-001") + [Result("mech.fit_clearance", "FIT-02", BLOCK, "x", ref="G-09")])
    assert res["V4"]["details"] == ["+ ('FIT-02', 'G-09', 'block')"]


def test_v4_is_pending_without_new_checks(v1_side, migrated, tmp_path, cfg):
    """new: a rule no registered check declares is not a difference but a missing dependency."""
    _, res = _run(v1_side, migrated, tmp_path, cfg, results=[], checks=False)
    assert res["V4"]["status"] == "pending" and "SOURCE-01" in res["V4"]["details"][0]


def test_v5_rehash_keeps_a_valid_approval_and_fails_when_lost(v1_side, migrated, tmp_path, cfg):
    """new: E-01 was valid in surec → gets the v1 hash; written back as the old hash it would drop (V5 fails)."""
    out, res = _run(v1_side, migrated, tmp_path, cfg)
    a = yamlio.read(out / "approvals.yaml")
    assert res["V5"]["status"] == "pass" and a[0]["approved_hash"] != a[0]["migrated_from_hash"]
    yamlio.write(out / "approvals.yaml", [a[0] | {"approved_hash": a[0]["migrated_from_hash"]}])
    res = verify(OLD / "S-001", out, cfg, old=snapshot("S-001"), known=known())
    assert res["V5"]["status"] == "fail" and "E-01" in res["V5"]["details"][0]


def test_v5_an_approval_dropped_in_surec_stays_dropped(v1_side, tmp_path, cfg):
    """new: the subject changed after the old approval → the old hash is kept and the approval stays invalid."""
    snap, out = snapshot("S-001"), tmp_path / "S-001"
    next(c for c in snap["cards"] if c["id"] == "E-01")["subject_hash"] = "0" * 64
    v1_side("S-001", out)
    surec_work(OLD / "S-001", out, cfg, old=snap)
    a = yamlio.read(out / "approvals.yaml")[0]
    assert a["approved_hash"] == a["migrated_from_hash"]
    assert verify(OLD / "S-001", out, cfg, old=snap, known=known())["V5"]["status"] == "pass"


def test_v6_model_equality(v1_side, migrated, tmp_path, cfg):
    """new: volume, bounding box and face count per part; a 1e-3 relative volume change fails; no hooks → pending."""
    good = snapshot("S-001")["model"]
    bad = {p: m | {"volume": m["volume"] * (1 + 1e-3)} if p == "A" else m for p, m in good.items()}
    _, res = _run(v1_side, migrated, tmp_path, cfg, metrics=bad)
    assert res["V6"]["status"] == "fail" and res["V6"]["details"][0].startswith("A:")
    _, res = _run(v1_side, migrated, tmp_path, cfg, hooks=False)
    assert res["V6"]["status"] == "pending"


def test_v7_card_equality(v1_side, migrated, tmp_path, cfg):
    """new: open card keys equal; a card the old system opened and v1 does not is a difference."""
    _, res = _run(v1_side, migrated, tmp_path, cfg, cards=old_cards("S-001", drop=("flex:E-02",)))
    assert res["V7"]["details"] == ["- flex:E-02"]


def _with_calc(tmp_path, numbers):
    src = tmp_path / "old-S"
    shutil.copytree(OLD / "S-001", src, dirs_exist_ok=True)
    (src / "hesaplar").mkdir(exist_ok=True)
    (src / "hesaplar" / "h_vlm.py").write_text(
        'AD = "h_vlm"\nBASLIK = "h_vlm"\n\n\ndef hesapla(h, model):\n'
        f'    h.sonuc("denge", {numbers[0]}, "")\n    h.buyukluk("sm", {numbers[1]}, "-", 2, "VLM")\n'
        f'    h.buyukluk("denge_cl", {numbers[2]}, "-", 2, "VLM")\n')
    return src


@pytest.mark.parametrize("numbers, status", [((0.52, 0.101, 0.52), "pass"), ((0.52, 0.2, 0.52), "fail")])
def test_v8_calcs_rerun_with_the_same_results(v1_side, migrated, tmp_path, cfg, numbers, status):
    """new: calcs/*.py re-run by the evidence runner (wave 2 · B) give the old recorded results."""
    _, res = _run(v1_side, migrated, tmp_path, cfg, old=_with_calc(tmp_path, numbers))
    assert res["V8"]["status"] == status, res["V8"]
    assert status == "pass" or res["V8"]["details"] == ["h_vlm.sm: 0.101 ≠ 0.2"]


@pytest.mark.parametrize("case", ["H-001", "S-001"])
def test_real_v1_modules(tmp_path, cfg, case):
    """new: architecture §14.4 Faz 1 (CI) — with the registered packages, S-001 and H-001 pass V1–V8 and the old
    regression expectations."""
    if case == "S-001":
        pytest.importorskip("cadquery")
    from mekanik.core.checks import regress

    res = build(case, tmp_path / case, cfg)
    assert set(STATUS(res).values()) == {"pass"}, {k: v for k, v in res.items() if v["status"] != "pass"}
    subs = regress.run_case(tmp_path / case)
    assert subs and all(s.passed for s in subs), [s.errors for s in subs if not s.passed]
    assert (ROOT / "tests" / "cases" / case / "expected.yaml").exists()
