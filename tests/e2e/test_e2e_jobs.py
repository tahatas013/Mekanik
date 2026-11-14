# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.1: A1 — the seven jobs from the panel with no terminal step, each in the browser: open a project/work, open the
session, stop the agent, instruct it, approve a card, add a file, download files. The agent's side is played by the
plugin's own handlers (hook events, the monitor `mekanik watch`), as a session would."""

from __future__ import annotations

import hashlib
import json
from urllib.parse import unquote

import pytest
from conftest import go, new, prepare, review

from mekanik.agent import hook, inbox, watch
from mekanik.core import yamlio
from mekanik.core.process import gates
from mekanik.core.process.step import step
from mekanik.core.store import git, works

pytestmark = pytest.mark.e2e
CLEAR = "() => document.querySelectorAll('.bildirim').forEach((b) => b.remove())"
SHA = """async (url) => { const b = await (await fetch(url)).arrayBuffer();
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', b))].map((x) => x.toString(16).padStart(2, '0')).join(''); }"""
HEAD4 = "async (url) => [...new Uint8Array(await (await fetch(url)).arrayBuffer())].slice(0, 2)"


@pytest.fixture(scope="module")
def w(shop_e2e):
    """A work at G0 with its gate requested (core checks; no model needed for these jobs)."""
    code, d = new(title="İş sınaması")
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    return code, d


def test_1_project_and_work_open_from_the_panel(page, panel_e2e, shop_e2e, tmp_path):
    """2.1: A1 job 1 — the new-work screen: organization, project, title, purpose, "done", class, work type and an
    input file; the work opens (worktree, branches), the file is in inputs/ with its SHA-256; the CLI equivalent"""
    go(page, panel_e2e, "/new", "new")
    page.fill("[data-in=title]", "Panelden açılan")
    page.fill("[data-in=purpose]", "sınama")
    page.fill("[data-in=done]", "testler geçer")
    page.click("[data-type='new_part'] input")
    f = tmp_path / "braket v1.step"
    f.write_bytes(b"ISO-10303-21;\nHEADER;\nENDSEC;\n")
    page._c("setInputFiles", "[data-file-input]", [str(f)])
    page.wait("[data-queued='braket v1.step']")
    assert page.text("[data-cli]").startswith("mekanik work new --org TST --project SYN")
    with page.response("/api/works") as got:
        page.click("[data-create]")
    assert got["status"] == 200, got["body"]
    code = json.loads(got["body"])["code"]
    page.shown("flow")
    d = works.find(code)
    assert git.branch(d) == f"{code}/work/general" and page.count(f"[data-work='{code}']") == 1
    page.wait(f"[data-work='{code}']")
    rec = next(i for i in (yamlio.read(d / "work.yaml").get("inputs") or []) if i["path"] == "inputs/braket v1.step")
    assert rec["sha256"] == hashlib.sha256(f.read_bytes()).hexdigest() and yamlio.read(d / "work.yaml")["work_type"] == "new_part"


def test_2_session_opens_from_the_panel(page, panel_e2e, w):
    """2.1: A1 job 2 — "open the session": the deep link into the user's own Claude Code in the work folder with the
    resume prompt, the command and folder to paste; the panel starts nothing; the session, once open, is a tab"""
    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    with page.response("/session") as got:
        page.click("header [data-open-session]")
    assert got["status"] == 200, got["body"]
    page.wait("dialog[data-session][open]")
    link = page.attr("[data-deep-link]", "href")
    assert link.startswith("claude-cli://open?cwd=") and unquote(link.split("cwd=")[1].split("&")[0]) == str(d)
    assert unquote(link.split("&q=")[1]) == f"/mekanik:resume {code}" and str(d) in page.text("[data-command]")
    assert hook.runs(code) == []   # nothing started by the panel (T-09)
    page.click("dialog[data-session] [data-close]")
    for event in ("SessionStart", "PostToolUse"):   # the user's own session opens (its hooks report it)
        hook.handle(event, {"session_id": "e2e-a1", "cwd": str(d), "tool_name": "Read"})
    try:
        page.wait(f"[data-tab='{code}']:not(.soluk-sekme)", 20000)
    finally:
        hook.handle("SessionEnd", {"session_id": "e2e-a1", "cwd": str(d)})


def test_3_stop_from_the_panel_and_resume(page, panel_e2e, w):
    """2.1: A1 job 3, A5 — "Stop": the confirmation window, the stop flag, the session's tools denied by the hook,
    the notice in the inbox; "Resume" lifts it"""
    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    page.click("header [data-stop]")
    page.wait("dialog[data-confirm][open]")
    page.fill("dialog[data-confirm] [data-field]", "bekle")
    with page.response("/stop") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200 and hook.stop_flag(code).exists()
    page.wait("header [data-resume]")
    deny = hook.handle("PreToolUse", {"session_id": "s", "cwd": str(d), "tool_name": "Bash", "tool_input": {"command": "ls"}})
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert [m["kind"] for m in inbox.items(code)][-1] == "stop"
    page.eval(CLEAR)
    with page.response("/resume") as got:
        page.click("header [data-resume]")
    assert got["status"] == 200 and not hook.stop_flag(code).exists()
    page.wait("header [data-stop]")


def test_4_instruction_reaches_the_session(page, panel_e2e, w):
    """2.1: A1 job 4, A12 — the instruction box writes to the inbox ("waiting"); the monitor prints it to the session
    and the page shows it delivered (live, without reloading)"""
    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    page.fill("[data-instruction]", "G1 için üç seçenek hazırla")
    with page.response("/instructions") as got:
        page.click("[data-send]")
    assert got["status"] == 200
    page.wait("[data-inbox-list] [data-inbox='pending']", 20000)
    watch.watch(cwd=d, interval=0, rounds=1)
    page.wait("[data-inbox-list] [data-inbox='delivered']", 20000)
    assert inbox.items(code)[-1]["text"] == "G1 için üç seçenek hazırla"


def test_5_card_approval_from_the_panel(page, panel_e2e, w):
    """2.1: A1 job 5 — the gate card approved from the cards screen through the confirmation window: the chief's signed
    commit with the panel channel, the tag (old e2e 1 does the same on the model work)"""
    code, d = w
    go(page, panel_e2e, f"/{code}/cards?card=O-G0", "cards")
    page.click("#card-area [data-act=approve]")
    page.wait("dialog[data-confirm][open]")
    with page.response("/cards/O-G0/decision") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    assert f"{code}-G0" in git.git("tag", "--list", cwd=d).split()
    assert [x for x in yamlio.read(d / "approvals.yaml") if x["card"] == "O-G0"][-1]["channel"] == "panel_confirmed"


def test_6_file_added_from_the_panel(page, panel_e2e, w, tmp_path):
    """2.1: A1 job 6 — dropping (choosing) a file on the files screen: inputs/<name>, its SHA-256 in work.yaml, one
    commit, the folder clean; it is listed"""
    code, d = w
    go(page, panel_e2e, f"/{code}/files", "files")
    f = tmp_path / "not.pdf"
    f.write_bytes(b"%PDF-1.4 sinama")
    head = git.head(d)
    with page.response("/inputs/not.pdf") as got:
        page._c("setInputFiles", "[data-file-input]", [str(f)])
    assert got["status"] == 200, got["body"]
    page.wait("[data-file='inputs/not.pdf']", 20000)
    rec = next(i for i in yamlio.read(d / "work.yaml")["inputs"] if i["path"] == "inputs/not.pdf")
    assert rec["sha256"] == hashlib.sha256(b"%PDF-1.4 sinama").hexdigest() and git.head(d) != head and works.dirty(d) == ""


def test_7_files_downloaded_from_the_panel(page, panel_e2e, w):
    """2.1: A1 job 7 — the files screen's links: a file comes as it is (same SHA-256 as listed), a folder as a zip"""
    from mekanik.panel import writes

    code, d = w
    if not (d / "inputs" / "not.pdf").exists():   # job 6 adds it; alone, this test adds it itself
        writes.add_input(code, "not.pdf", b"%PDF-1.4 sinama")
    go(page, panel_e2e, f"/{code}/files", "files")
    page.wait("[data-file='inputs/not.pdf'] a[download]")
    href = page.attr("[data-file='inputs/not.pdf'] a[download]", "href")
    assert page.eval(SHA, href) == hashlib.sha256((d / "inputs" / "not.pdf").read_bytes()).hexdigest()
    assert page.eval(HEAD4, page.attr("[data-folder='records'] [data-zip]", "href")) == [0x50, 0x4B]   # "PK": a zip
