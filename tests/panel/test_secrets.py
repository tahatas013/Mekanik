# SPDX-License-Identifier: AGPL-3.0-or-later
"""A7: no credential leaks. With credentials in the environment and in the agent's tool inputs, a session's hooks,
steps, the inbox and every panel answer are scanned: agent-run records, records/events.jsonl, the log, the state
folder and the panel's responses hold none of them, nor the panel's session secret or cookie (0 findings)."""

from __future__ import annotations

import re

from panel_util import client_for

from mekanik.agent import hook, inbox
from mekanik.config import state_dir
from mekanik.core.process.step import step
from mekanik.panel import auth

FAKE = {"ANTHROPIC_API_KEY": "sk-ant-api03-" + "A" * 40, "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-" + "B" * 40,
        "GITHUB_TOKEN": "ghp_" + "C" * 36, "SSH_AUTH_SOCK": "/tmp/ssh-XYZsecret/agent.4242"}
PATTERNS = [re.compile(p) for p in (r"sk-ant-[A-Za-z0-9_-]{10,}", r"ghp_[A-Za-z0-9]{20,}", r"ssh-XYZsecret",
                                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----")]


def _findings(text: str, own: list[str]) -> list[str]:
    return [p.pattern for p in PATTERNS if p.search(text)] + [s[:6] + "…" for s in own if s in text]


def test_no_credential_in_records_logs_state_or_answers(g0, monkeypatch):
    """2.1: A7 — 0 findings in agent-run, events.jsonl, the log, the state folder (but the secret file itself) and
    the panel's answers (the CSRF token only in /api/session, where the page reads it)"""
    from mekanik.panel.app import create_app

    code, d = g0
    for k, v in FAKE.items():
        monkeypatch.setenv(k, v)
    payload = {"session_id": "s1", "cwd": str(d), "permission_mode": "default", "transcript_path": "/tmp/t.jsonl"}
    for event, extra in (("SessionStart", {}), ("PreToolUse", {"tool_name": "Bash", "tool_input": {
            "command": f"curl -H 'x-api-key: {FAKE['ANTHROPIC_API_KEY']}' https://api.example"}}),
                         ("PostToolUse", {"tool_name": "Bash", "tool_response": {"stdout": FAKE["GITHUB_TOKEN"]}}),
                         ("Notification", {"message": f"token {FAKE['CLAUDE_CODE_OAUTH_TOKEN']}"}), ("Stop", {})):
        hook.handle(event, {**payload, **extra})
    step(d, "adım", "design_engineer", "anahtar yok")
    inbox.send(code, "devam et")
    with client_for(create_app(watch=False)) as c:
        own = [auth.secret(), auth.session_value()]
        bodies = {p: c.get(p).text for p in ["/api/tree", "/api/tabs", "/api/cards", "/api/new-work", "/api/catalog",
                                             *(f"/api/works/{code}{s}" for s in (
                                                 "", "/stages", "/status", "/liveness", "/cards", "/files",
                                                 "/branches", "/design-file", "/stream", "/inbox", "/summary"))]}
        session = c.get("/api/session").text
    found = {p: f for p, b in bodies.items() if (f := _findings(b, own + [auth.csrf_token()]))}
    found |= {"/api/session": f} if (f := _findings(session, own)) else {}
    for f in [*(d / "records").rglob("*"), *state_dir().rglob("*")]:
        if f.is_file() and f != auth.secret_file() and (got := _findings(f.read_text(errors="replace"), own)):
            found[str(f)] = got
    assert found == {}
    assert hook.runs(code) and all("tool_input" not in r and "env" not in r for _, r in hook.runs(code))
