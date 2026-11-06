# SPDX-License-Identifier: AGPL-3.0-or-later
"""Agent tests never touch the real ~/.local/state or ~/.config: both point into tmp_path."""

import shutil
from pathlib import Path

import pytest
import yaml

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "config"


@pytest.fixture(autouse=True)
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(FIXTURE))
    return tmp_path / "state" / "mekanik"


@pytest.fixture
def work(tmp_path):
    """A work folder of the allowed test organization TST."""
    d = tmp_path / "works" / "tst" / "sentetik" / "TST-SYN-01"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def forbidden(tmp_path, monkeypatch):
    """Workshop config with organization NOP, whose data may not reach the model provider. Returns its repo."""
    cfg, repo = tmp_path / "config", tmp_path / "works" / "nop"
    shutil.copytree(FIXTURE, cfg)
    (cfg / "orgs").mkdir(exist_ok=True)
    org = {"code": "NOP", "name": "Yasak", "repo": str(repo), "remote": None,
           "data_transfer": {"model_provider_allowed": False, "note": "sınama"}}
    (cfg / "orgs" / "NOP.yaml").write_text(yaml.safe_dump(org, allow_unicode=True), encoding="utf-8")
    (repo / "sentetik" / "NOP-SYN-01").mkdir(parents=True)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    return repo
