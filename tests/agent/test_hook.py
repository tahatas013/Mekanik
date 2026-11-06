# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hook handler: agent-run records (old durum.py), SessionStart/UserPromptSubmit answers, the hook command."""

import io
import json

from mekanik.agent import hook
from mekanik.core.i18n import t
from mekanik.core.model.schema import validate


def _send(event, payload, work=None):
    out = io.StringIO()
    assert hook.run(event, work, stdin=io.StringIO(json.dumps(payload)), stdout=out) == 0
    return json.loads(out.getvalue()) if out.getvalue() else {}


def test_status_hook(work):
    """old: test_akis::test_durum_kancasi"""
    for event, expected in (("UserPromptSubmit", "running"), ("Notification", "waiting_permission"),
                            ("Stop", "waiting_input")):
        payload = {"hook_event_name": event, "session_id": "x", "cwd": "/tmp",
                   "message": "Claude needs your permission to use Bash" if event == "Notification" else ""}
        _send(event, payload, "TST-SYN-09")
        assert hook.runs("TST-SYN-09")[-1][1]["status"] == expected
    _send("Notification", {"hook_event_name": "Notification", "message": "Claude needs your permission"}, "TST-SYN-09")
    assert hook.runs("TST-SYN-09")[-1][1]["status"] == "waiting_permission"


def test_work_code_from_cwd(work, tmp_path):
    """new: architecture §5.4 — the plugin's hooks are global, the work comes from the session folder"""
    (work / "model").mkdir()
    assert hook.work_of(work / "model") == "TST-SYN-01"
    assert hook.work_of(tmp_path) is None
    assert hook.handle("Stop", {"session_id": "s", "cwd": str(tmp_path)}) == {}
    assert hook.runs() == []


def test_run_record_is_schema_valid_and_holds_no_credentials(work, monkeypatch, state):
    """new: architecture §5.7 and A7 — agent-run validates; no environment value or stray payload field is written"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sekret-anahtar-1")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sekret-anahtar-2")
    base = {"session_id": "6f1c2a9e", "cwd": str(work), "transcript_path": "/x/sekret-anahtar-3.jsonl",
            "token": "sekret-anahtar-4", "permission_mode": "default"}
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        hook.handle(event, {**base, "hook_event_name": event, "tool_name": "Read",
                            "tool_input": {"file_path": str(work / "params.yaml")}})
    files = list((state / "runs").glob("*.json"))
    assert len(files) == 1, "one record per session"
    rec = json.loads(files[0].read_text(encoding="utf-8"))
    assert validate("agent_run", rec, files[0].name) == []
    assert rec["status"] == "finished" and rec["end_reason"] == "completed" and rec["ended_at"] >= rec["started_at"]
    assert rec["adapter"]["session_id"] == "6f1c2a9e" and "--resume 6f1c2a9e" in rec["terminal_command"]
    assert "sekret" not in files[0].read_text(encoding="utf-8")


def test_sessions_get_separate_records(work):
    """new: architecture §4.10 — active work is counted from agent runs, one per session"""
    for sid in ("a", "b", "a"):
        hook.handle("UserPromptSubmit", {"session_id": sid, "cwd": str(work)})
    assert sorted(r["adapter"]["session_id"] for _, r in hook.runs("TST-SYN-01")) == ["a", "b"]


def test_hook_never_breaks_the_session(work, monkeypatch):
    """new: old durum.kancadan rule — unreadable input or an internal error gives exit 0 and no output"""
    out = io.StringIO()
    assert hook.run("PreToolUse", stdin=io.StringIO("{bozuk"), stdout=out) == 0 and out.getvalue() == ""
    monkeypatch.setattr(hook, "record", lambda *a: 1 / 0)
    assert _send("Stop", {"session_id": "s", "cwd": str(work)}) == {}


def test_allowed_organization_is_silent(work):
    """new: architecture §5.4 — in a work whose organization allows data transfer the prompt hooks say nothing"""
    for event in ("SessionStart", "UserPromptSubmit", "Stop"):
        assert _send(event, {"session_id": "s", "cwd": str(work), "prompt": "devam"}) == {}


def test_data_gate_blocks_prompt_and_warns_at_session_start(forbidden):
    """new: architecture §5.4 KM2-2 layers 2 — UserPromptSubmit blocks, SessionStart (cannot block) warns"""
    cwd = str(forbidden / "sentetik" / "NOP-SYN-01")
    assert _send("UserPromptSubmit", {"session_id": "s", "cwd": cwd, "prompt": "çiz"}) == {
        "decision": "block", "reason": t("agent.block.data", org="NOP")}
    ctx = _send("SessionStart", {"session_id": "s", "cwd": cwd})["hookSpecificOutput"]
    assert ctx == {"hookEventName": "SessionStart", "additionalContext": t("agent.context.data", org="NOP")}


def test_unknown_organization_is_held(tmp_path):
    """new: architecture §5.5 KM-50 — a work whose organization has no data_transfer declaration is a Hold"""
    cwd = tmp_path / "ZZZ-SYN-01"
    cwd.mkdir()
    assert _send("UserPromptSubmit", {"session_id": "s", "cwd": str(cwd)})["decision"] == "block"


def test_resumed_session_is_open_again(work):
    """new: architecture §5.4 — `claude --resume` continues the same record; the end fields go away"""
    for event in ("SessionStart", "SessionEnd", "SessionStart"):
        rec = hook.handle(event, {"session_id": "r", "cwd": str(work)}) or hook.runs("TST-SYN-01")[-1][1]
    assert rec["status"] == "waiting_input" and "ended_at" not in rec and "end_reason" not in rec
    assert len(hook.runs("TST-SYN-01")) == 1
