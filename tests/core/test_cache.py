# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import shutil
import time
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.evidence import cache

FIXTURE_CONFIG = Path(__file__).resolve().parents[1] / "fixtures" / "config"


def _entry(base, commit, size, at):
    path = cache.entry(commit, base)
    (path / "model.bin").write_bytes(b"\0" * size)
    os.utime(path / cache.MARK, (at, at))


def test_over_limit_least_recently_used_is_deleted(tmp_path):
    """old: test_onbellek::sinir_asilinca_en_eski_kullanilan_silinir"""
    now = time.time()
    _entry(tmp_path, "a" * 40, 400, now - 300)
    _entry(tmp_path, "b" * 40, 400, now - 200)
    _entry(tmp_path, "c" * 40, 400, now - 100)
    cache.entry("a" * 40, tmp_path)   # a is used again → now the newest

    assert cache.prune(900, tmp_path) == ["b" * 40]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a" * 40, "c" * 40]


def test_nothing_deleted_under_limit(tmp_path):
    """old: test_onbellek::sinirin_altinda_hicbir_sey_silinmez"""
    _entry(tmp_path, "a" * 40, 100, time.time())
    assert cache.prune(1000, tmp_path) == []


def test_kept_entry_is_not_deleted(tmp_path):
    """old: test_onbellek::korunan_giris_silinmez"""
    now = time.time()
    _entry(tmp_path, "e" * 40, 500, now - 100)
    _entry(tmp_path, "f" * 40, 500, now)
    assert cache.prune(600, tmp_path, keep="e" * 40) == ["f" * 40]


def test_upper_limit_5_gb(tmp_path, monkeypatch):
    """old: test_onbellek::ust_sinir_5_gb"""
    # v1: the workshop config's paths.cache_limit overrides the default
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(FIXTURE_CONFIG))
    assert cache.DEFAULT_LIMIT == 5 * 1024**3 and cache.limit() == cache.DEFAULT_LIMIT
    cfg = tmp_path / "config"
    shutil.copytree(FIXTURE_CONFIG, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["paths"]["cache_limit"] = {"value": 2, "unit": "GB", "source": "decision", "decided_by": "chief_engineer"}
    yamlio.write(cfg / "config.yaml", doc)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    assert cache.limit() == 2 * 1024**3


def test_folder_not_named_as_commit_is_not_deleted(tmp_path):
    """old: test_onbellek::commit_adi_olmayan_klasor_silinmez"""
    (tmp_path / "branches").mkdir()
    (tmp_path / "branches" / "x.bin").write_bytes(b"\0" * 900)
    _entry(tmp_path, "d" * 40, 400, time.time())
    cache.prune(100, tmp_path)
    assert (tmp_path / "branches").exists()
