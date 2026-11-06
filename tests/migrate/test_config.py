# SPDX-License-Identifier: AGPL-3.0-or-later
"""surec-config: kurumlar and profiller/{uretim,olcum} → orgs/, machines/, instruments/ (architecture §14.2)."""

from __future__ import annotations

import shutil

import pytest

from build_cases import OLD, ROOT
from mekanik.core import yamlio
from mekanik.migrate import Phase2Error, surec_config, surec_work, verify_config
from mekanik.plugins import registry

TARGET = ROOT / "tests" / "fixtures" / "config"


def _strip(x, drop=("note",)):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in drop}
    return x


def test_config_records_pass_v1_with_one_gap(tmp_path):
    """new: architecture §14.3 V1 for the workshop records; data_transfer has no old counterpart (KM-37)."""
    log = surec_config(OLD, tmp_path)
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.yaml") if p.name != "migration.yaml") \
        == ["instruments/caliper.yaml", "instruments/scanner-lidar.yaml", "machines/fdm-test.yaml", "orgs/TST.yaml"]
    assert log.gaps == [{"file": "orgs/TST.yaml", "path": "data_transfer"}]
    assert log.unmapped == []
    assert log.dropped == ["orgs/TST.yaml.aciklama", "orgs/TST.yaml.onay_yetkilisi"] + [   # no v1 place; in the report
        f"{d}.yaml.{k}" for d in ("machines/fdm-test", "instruments/caliper", "instruments/scanner-lidar")
        for k in ("tarih", "onaylayan", "not") if not (d.startswith("machines") and k == "not")]
    res = verify_config(tmp_path)
    assert {k: v["status"] for k, v in res.items()} == {"V1": "pass", "V3": "pass"}
    assert "data_transfer" not in yamlio.read(tmp_path / "orgs" / "TST.yaml")
    assert (tmp_path / "migration-report.md").read_text(encoding="utf-8").count("data_transfer") == 1


def test_config_values_equal_the_target_fixture(tmp_path):
    """new: the old-format test profiles give the values of tests/fixtures/config (G-28, G-30)."""
    surec_config(OLD, tmp_path)
    m, want = yamlio.read(tmp_path / "machines" / "fdm-test.yaml"), yamlio.read(TARGET / "machines" / "fdm-test.yaml")
    assert {k: m[k] for k in ("id", "version", "type", "status")} == {k: want[k] for k in ("id", "version", "type",
                                                                                          "status")}
    assert _strip(m["profile"]) == want["profile"]
    assert m["profile"]["clearance"]["centering"]["upper"]["note"]           # old `not` kept as note
    for inst in ("caliper", "scanner-lidar"):
        got = yamlio.read(tmp_path / "instruments" / f"{inst}.yaml")
        want = yamlio.read(TARGET / "instruments" / f"{inst}.yaml")
        assert {k: got[k] for k in ("id", "kind", "uncertainty", "valid_for")} == {
            k: want[k] for k in ("id", "kind", "uncertainty", "valid_for")}
    org = yamlio.read(tmp_path / "orgs" / "TST.yaml")
    assert org["projects"] == [{"code": "SYN", "name": "Sentetik", "folder": "sentetik"}]
    assert org["remote"] is None and org["cost_threshold"] == {"value": None, "unit": "TL", "source": "assumption",
                                                                "note": "sınama"}


def test_machine_passes_the_print3d_profile_type(tmp_path):
    """new: the migrated machine profile passes the print3d.fdm validator (wave 2 · C) when it is installed."""
    check = registry().profile_types.get("print3d.fdm")
    if check is None:
        pytest.skip("print3d.fdm profile type not registered")
    surec_config(OLD, tmp_path)
    check(yamlio.read(tmp_path / "machines" / "fdm-test.yaml")["profile"], "machines/fdm-test")


def test_old_layout_and_unknown_tag(tmp_path):
    """new: kurumlar/<kod>/kurum.yaml (the real old layout) and an instrument tag without a v1 kind (a gap)."""
    old = tmp_path / "old"
    shutil.copytree(OLD / "profiller", old / "profiller")
    (old / "kurumlar" / "tst").mkdir(parents=True)
    shutil.copy(OLD / "kurumlar" / "TST.yaml", old / "kurumlar" / "tst" / "kurum.yaml")
    p = yamlio.read(old / "profiller" / "olcum" / "caliper.yaml") | {"etiket": "olcu:baska"}
    yamlio.write(old / "profiller" / "olcum" / "caliper.yaml", p)
    log = surec_config(old, tmp_path / "new")
    assert (tmp_path / "new" / "orgs" / "TST.yaml").exists()
    assert {"file": "instruments/caliper.yaml", "path": "kind"} in log.gaps
    assert "kind" not in yamlio.read(tmp_path / "new" / "instruments" / "caliper.yaml")


def test_apply_is_phase_two(tmp_path, cfg):
    """new: --apply (dry_run=False) is phase 2 (architecture §14.1); nothing is written."""
    with pytest.raises(Phase2Error) as e:
        surec_config(OLD, tmp_path / "a", dry_run=False)
    assert "Faz 2" in str(e.value) or "phase 2" in str(e.value)
    with pytest.raises(Phase2Error):
        surec_work(OLD / "S-001", tmp_path / "b", cfg, dry_run=False)
    assert not (tmp_path / "a").exists() and not (tmp_path / "b").exists()
