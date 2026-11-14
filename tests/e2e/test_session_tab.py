# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.1: A13 — the session tab (T-18a): the user's interactive agent in a terminal inside the panel. No real agent
runs: MEKANIK_CLAUDE is a fake (fake_claude.py) that prints its arguments, echoes each typed line and logs to
FAKE_CLAUDE_LOG. Four tests: open, type, continue after a panel restart (--resume), refused without the secret."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from conftest import go, new, prepare

from mekanik.agent import inbox
from mekanik.core.process.step import step

pytestmark = pytest.mark.e2e
TERM = "[data-terminal] .xterm-rows"


def log() -> list[dict]:
    p = Path(os.environ["FAKE_CLAUDE_LOG"])
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


@pytest.fixture(scope="module")
def w(shop_e2e):
    code, d = new(title="Oturum sınaması")
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    return code, d


def test_1_session_opens_in_the_panel(page, panel_e2e, w):
    """2.1: A13 (open) — the session tab starts the agent in a terminal in the work folder: a new session with a
    chosen id (--session-id) and the resume prompt, on a real terminal (PTY)"""
    code, d = w
    go(page, panel_e2e, f"/{code}/session", "session")
    page.click("[data-pty='new']")
    page.wait(f"{TERM}:has-text('FAKE-CLAUDE')", 20000)
    start = [e for e in log() if e["event"] == "start"][-1]
    assert start["args"][0] == "--session-id" and start["args"][2] == f"/mekanik:resume {code}"
    assert start["cwd"] == str(d) and start["tty"] is True
    assert page.attr("[data-terminal]", "data-session") == start["args"][1]


def test_2_typing_reaches_the_terminal_and_the_instruction_box_does_not(page, panel_e2e, w):
    """2.1: A13 (type) — what the chief types in the tab reaches the agent; an instruction from the instruction box goes
    to the inbox and never into this terminal (§5.4 T-18a)"""
    code, d = w
    go(page, panel_e2e, f"/{code}/session", "session")
    page.wait(f"{TERM}:has-text('FAKE-CLAUDE')", 20000)   # the running terminal is attached again, with its output
    page.click("[data-terminal]")
    page.keyboard("type", "merhaba")
    page.keyboard("press", "Enter")
    page.wait(f"{TERM}:has-text('echo: merhaba')", 20000)
    assert {"event": "line", "text": "merhaba"} in log()
    go(page, panel_e2e, f"/{code}/flow")
    page.fill("[data-instruction]", "terminale yazılmamalı")
    with page.response("/instructions"):
        page.click("[data-send]")
    page.wait("[data-inbox-list] [data-inbox='pending']")
    assert inbox.items(code)[-1]["text"] == "terminale yazılmamalı"
    assert not [e for e in log() if "terminale" in e.get("text", "")]


def test_3_session_continues_after_a_panel_restart(page, panel_e2e, w):
    """2.1: A13 (resume) — the panel stops (its terminal ends with it) and starts again: the tab offers to continue and
    the agent starts with --resume and the same session id"""
    code, d = w
    sid = next(e["args"][1] for e in reversed(log()) if e["event"] == "start" and e["args"][0] == "--session-id")
    panel_e2e.stop()
    panel_e2e.start()
    go(page, panel_e2e, f"/{code}/session", "session")
    page.click("[data-pty='resume']")
    page.wait(f"{TERM}:has-text('FAKE-CLAUDE --resume')", 20000)
    assert [e for e in log() if e["event"] == "start"][-1]["args"] == ["--resume", sid]


def test_4_no_terminal_without_the_session_secret(browser, panel_e2e, w):
    """2.1: A13 (secret) — without the session cookie the page gets no panel and its socket is refused before it is
    accepted; a foreign Origin is refused too; no agent starts"""
    import websockets.sync.client as wsc
    from websockets.exceptions import InvalidStatus

    from mekanik.panel import auth

    code, d = w
    before = len(log())
    anon = browser.page("anon")
    anon.goto(panel_e2e.url + "/")
    anon.wait("[data-login-needed]")
    closed = anon.eval("""(url) => new Promise((done) => { const s = new WebSocket(url); s.onopen = () => done('open');
      s.onclose = (e) => done(e.code); })""", f"ws://127.0.0.1:{panel_e2e.port}/api/works/{code}/pty")
    assert closed != "open"
    url = f"ws://127.0.0.1:{panel_e2e.port}/api/works/{code}/pty"
    for headers in ({"Origin": panel_e2e.url}, {"Origin": "http://kotu.example", "Cookie": f"{auth.COOKIE}={auth.session_value()}"}):
        with pytest.raises(InvalidStatus) as e:
            wsc.connect(url, additional_headers=headers, open_timeout=5)
        assert e.value.response.status_code == 403
    assert len(log()) == before
