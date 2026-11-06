# SPDX-License-Identifier: AGPL-3.0-or-later
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from mekanik.core import quality, yamlio
from mekanik.core.checks.result import BLOCK, PASS
from mekanik.core.errors import MekanikError
from mekanik.core.evidence import register
from mekanik.core.model.schema import validate

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.org", "PATH": "/usr/bin:/bin"}
FINDINGS = """İnceleme:
- [YÜKSEK] calcs/area.py:9 — birim yanlış — Kaynaksız sayı yok — mm² yerine m² — çarpan 10⁶
[DÜŞÜK] params.yaml:1 — not eksik — İzlenebilirlik — block_width açıklamasız
Genel: birim düzeltilmeden kapı istenmemeli.
"""


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    repo, w = tmp_path / "repo", tmp_path / "repo" / "tst" / "sentetik"
    w.mkdir(parents=True)
    yamlio.write(w / "work.yaml", {"code": "TST-SYN-01"})
    yamlio.write(w / "params.yaml", {"block_width": {"value": 20.0, "unit": "mm", "source": "decision"}})
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "ilk"]):
        subprocess.run(["git", *args], cwd=repo, check=True, env=ENV)
    return w


def test_prompt_format_matches_the_parser(work):
    """new: Ek B §14 madde 15"""
    text = quality.prompt(work, "kapı G1")
    copy = Path(next(p for p in text.split() if p.endswith("sentetik")))   # the frozen copy of HEAD, this work
    assert copy.is_relative_to(quality.state_dir()) and (copy / "work.yaml").exists()
    tokens, rest = re.search(r"`\[([^\]]+)\]\s*([^`]+)`", text).groups()
    parsed = [quality.parse(f"[{x}] {rest}")[0] for x in tokens.split("|")]
    assert [len(f) for f in parsed] == [1, 1, 1] and {f[0]["severity"] for f in parsed} == {"high", "medium", "low"}
    assert all(f[0]["location"] and f[0]["evidence"] for f in parsed)
    assert "TST-SYN-01" in text and "calcs/*.py" in text


def test_open_high_finding_blocks_until_closed_with_rationale(work):
    """Report on the frozen copy; an open high finding blocks the request (QUALITY-01) until closed; new inputs need
    a new review (old kalite.denetle, kapat)."""
    with pytest.raises(MekanikError):
        quality.record(work, "kapı G1", FINDINGS)           # no frozen copy: the prompt comes first
    quality.prompt(work, "kapı G1")
    path, rep = quality.record(work, "kapı G1", FINDINGS, reviewer="claude_code")
    assert path.parent == work / "records" / "quality" and path.name.endswith("-kap-g1.yaml")
    assert not list((quality.state_dir() / "review").iterdir())   # frozen copy removed
    validate("quality_review", yamlio.read(path), str(path))
    high, low = rep["findings"]
    assert (high["no"], high["severity"], high["location"], high["evidence"]) == (1, "high", "calcs/area.py:9",
                                                                                  "mm² yerine m² — çarpan 10⁶")
    assert low["severity"] == "low" and rep["summary"].startswith("Genel:") and rep["id"] == "QR-001"
    assert quality.current(work) == (path, rep) and quality.open_high(rep) == [high]
    with pytest.raises(MekanikError, match=path.name):
        quality.require_clear(work, "kapı G1")
    gate = SimpleNamespace(root=work, cards=[{"id": "O-G1", "type": "gate", "status": "open"}])
    assert [r.status for r in register.quality_gate(gate)] == [BLOCK]

    with pytest.raises(MekanikError):
        quality.close(work, path.name, 1, " ", False, "biçim")
    with pytest.raises(MekanikError):
        quality.close(work, path.name, 1, "birim düzeltildi", False, "")
    closed = quality.close(work, path.name, 1, "birim düzeltildi", True, "tests/cases/unit-mm2")
    assert closed["closure"]["regression"] == {"needed": True, "case": "tests/cases/unit-mm2"}
    validate("quality_review", yamlio.read(path), str(path))
    assert quality.require_clear(work, "kapı G1")[0] == path
    assert [r.status for r in register.quality_gate(gate)] == [PASS]

    (work / "params.yaml").write_text("block_width: {value: 22.0, unit: mm, source: decision}\n")
    assert quality.current(work) is None
    with pytest.raises(MekanikError):
        quality.require_clear(work, "kapı G1")              # inputs changed: the review runs again
