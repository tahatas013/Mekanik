# SPDX-License-Identifier: AGPL-3.0-or-later
"""The quality review bound to the quality-engineer subagent's own output (architecture §4.8, KF1-16): the plugin's
SubagentStop hook catches it, `mekanik review record` writes only that. The payload fields used are
`agent_type`, `last_assistant_message` and, when that is missing, `agent_transcript_path` (JSONL)."""

import hashlib
import json
import subprocess

import pytest

from mekanik.agent import hook
from mekanik.core import quality, yamlio
from mekanik.core.errors import MekanikError

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.org", "PATH": "/usr/bin:/bin"}
FINDINGS = "[YÜKSEK] calcs/a.py:3 — birim hatası — Kaynaksız sayı yok — mm yerine m\nGenel: düzeltilmeden kapı yok."
AGENT = "mekanik:quality-engineer"


@pytest.fixture
def repo(work):
    yamlio.write(work / "work.yaml", {"code": "TST-SYN-01"})
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "ilk"]):
        subprocess.run(["git", *args], cwd=work.parents[1], check=True, env=ENV)
    return work


def _stop(work, **payload) -> dict:
    return hook.handle("SubagentStop", {"session_id": "s", "cwd": str(work), "hook_event_name": "SubagentStop",
                                        "stop_hook_active": False, **payload})


def test_made_up_no_findings_is_refused(repo):
    """Faz 2: KF1-16 — "Bulgu yok." from the main session is not recorded when the subagent did not run, when only
    another or a same-named non-plugin agent ran, or when it says other than the caught output (phase 1: recorded)"""
    quality.prompt(repo, "kapı G1")
    with pytest.raises(MekanikError):
        quality.record(repo, "kapı G1", "Bulgu yok.")
    assert _stop(repo, agent_type="general-purpose", last_assistant_message="Bulgu yok.") == {}
    assert _stop(repo, agent_type="quality-engineer", last_assistant_message="Bulgu yok.") == {}
    with pytest.raises(MekanikError):
        quality.record(repo, "kapı G1", "Bulgu yok.")
    _stop(repo, agent_type=AGENT, agent_id="a1", last_assistant_message=FINDINGS)
    with pytest.raises(MekanikError):
        quality.record(repo, "kapı G1", "Bulgu yok.")
    path, rep = quality.record(repo, "kapı G1", "  " + FINDINGS.replace("\n", "\n\n") + "\n")   # same findings
    assert [f["severity"] for f in rep["findings"]] == ["high"] and rep["summary"].startswith("Genel")
    assert rep["reviewer"]["output_hash"] == hashlib.sha256(FINDINGS.encode()).hexdigest()
    assert not list((quality.state_dir() / "review").iterdir())                 # copy and caught output consumed


def test_output_from_the_transcript_and_no_stale_capture(repo, tmp_path):
    """Faz 2: KF1-16 — without `last_assistant_message` the last assistant text of the subagent's transcript is
    caught; an output caught before the prompt made the frozen copy does not count; empty stdin takes the caught text"""
    rows = [{"type": "user", "message": {"role": "user", "content": "istem"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Bulgu yok.\nGenel: temiz."}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}}]
    (log := tmp_path / "agent-a1.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
    _stop(repo, agent_type=AGENT, agent_transcript_path=str(log))
    quality.prompt(repo, "kapı G1")                                               # after the capture: stale
    with pytest.raises(MekanikError):
        quality.record(repo, "kapı G1", "")
    _stop(repo, agent_type=AGENT, agent_transcript_path=str(log))
    _, rep = quality.record(repo, "kapı G1", "")
    assert rep["findings"] == [] and rep["summary"] == "Genel: temiz."


def test_report_delivered_by_subagent_handback_is_the_one_kept(repo):
    """2.1: KF1-16 — in auto mode the subagent hands its report back with SubagentHandback (PostToolUse
    tool_input.message, Claude Code hooks reference); the later SubagentStop closing text does not replace it."""
    hook.handle("PostToolUse", {"session_id": "s", "cwd": str(repo), "hook_event_name": "PostToolUse",
                                "agent_id": "a1", "agent_type": AGENT, "tool_name": "SubagentHandback",
                                "tool_input": {"message": FINDINGS}})
    _stop(repo, agent_id="a1", agent_type=AGENT, last_assistant_message="Rapor teslim edildi.")
    got = json.loads(quality._caught("TST-SYN-01").read_text(encoding="utf-8"))
    assert got["text"] == FINDINGS and got["via"] == "handback"
    assert got["sha256"] == hashlib.sha256(FINDINGS.encode()).hexdigest()
    other = {"session_id": "s", "cwd": str(repo), "hook_event_name": "PostToolUse", "agent_id": "a2",
             "agent_type": "Explore", "tool_name": "SubagentHandback", "tool_input": {"message": "Bulgu yok."}}
    hook.handle("PostToolUse", other)
    assert json.loads(quality._caught("TST-SYN-01").read_text(encoding="utf-8"))["text"] == FINDINGS
