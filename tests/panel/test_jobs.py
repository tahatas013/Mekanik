# SPDX-License-Identifier: AGPL-3.0-or-later
"""A1: the seven jobs from the panel with no terminal step (back-end side; the Playwright tests are wave 2.3). The
agent's side is played by the plugin's hook handler and the monitor (`mekanik watch`), as a fake session would."""

from __future__ import annotations

import hashlib
import io
import zipfile
from urllib.parse import unquote

from mekanik.agent import hook, inbox, watch
from mekanik.core import yamlio
from mekanik.core.store import git, works


def pre(work, tool, **inp):
    return hook.handle("PreToolUse", {"session_id": "s1", "cwd": str(work), "tool_name": tool, "tool_input": inp})


def test_1_project_opens_from_the_panel(panel):
    """2.1: A1 — project / work opening: POST /api/works makes the work (worktree, branches, skeleton) as
    `mekanik work new` does; the tree shows it; the reply carries the CLI equivalent"""
    opts = panel.get("/api/new-work").json()
    assert opts["organizations"][0]["projects"][0]["code"] == "SYN" and "C" in opts["classes"]
    r = panel.post("/api/works", json={"org": "TST", "project": "SYN", "title": "Panelden", "risk_class": "C",
                                       "purpose": "sınama", "done_criterion": "testler geçer"})
    assert r.status_code == 200, r.text
    code = r.json()["code"]
    assert works.find(code).exists() and git.branch(works.find(code)) == f"{code}/work/general"
    assert r.json()["cli"].startswith("mekanik work new --org TST --project SYN")
    assert [w["code"] for w in panel.get("/api/tree").json()[0]["projects"][0]["works"]] == [code]


def test_2_session_opens_from_the_panel(panel, g0):
    """2.1: A1 — opening the session: a deep link into the user's own Claude Code in the work folder with the resume
    prompt and the command to paste; nothing is started by the panel (T-09)"""
    code, d = g0
    out = panel.post(f"/api/works/{code}/session", json={}).json()
    assert out["link"].startswith("claude-cli://open?cwd=") and unquote(out["link"].split("cwd=")[1].split("&")[0]) \
        == str(d) and unquote(out["link"].split("&q=")[1]) == f"/mekanik:resume {code}"
    assert out["command"] == f"cd {d} && claude" and hook.runs(code) == []


def test_3_stop_from_the_panel_and_back(panel, g0):
    """2.1: A1, A5 — the stop button: the flag is set, the session's non-mekanik tools are denied whatever the model
    (3 kinds), a mekanik command still runs; the session is told; resume lifts it"""
    code, d = g0
    assert panel.post(f"/api/works/{code}/stop", json={"text": "bekle"}).status_code == 200
    assert hook.stop_flag(code).exists() and panel.get(f"/api/works/{code}/liveness").json()["stop"] is True
    for tool, inp in (("Bash", {"command": "ls"}), ("Edit", {"file_path": str(d / "params.yaml")}),
                      ("Write", {"file_path": str(d / "x.md")})):
        assert pre(d, tool, **inp)["hookSpecificOutput"]["permissionDecisionReason"] == hook.t(
            "agent.deny.stop", work=code)
    assert pre(d, "Bash", command="mekanik step 'durdum, bekliyorum' --role project_engineer") == {}
    assert [m["kind"] for m in inbox.items(code)] == ["stop"]
    panel.post(f"/api/works/{code}/resume", json={})
    assert not hook.stop_flag(code).exists() and pre(d, "Bash", command="ls") == {}


def test_4_instruction_reaches_the_session(panel, g0, capsys):
    """2.1: A1, A12 — the instruction box: the text goes to the work's inbox and the monitor prints it to the session;
    the panel then shows it delivered"""
    code, d = g0
    panel.post(f"/api/works/{code}/instructions", json={"text": "G1 için üç seçenek hazırla"})
    assert [m["state"] for m in panel.get(f"/api/works/{code}/inbox").json()["items"]] == ["pending"]
    capsys.readouterr()
    watch.watch(cwd=d, interval=0, rounds=1)
    first = capsys.readouterr().out.splitlines()[0]
    assert first == inbox.line(inbox.items(code)[0]) and "G1 için üç seçenek hazırla" in first
    item = panel.get(f"/api/works/{code}/inbox").json()["items"][0]
    assert item["state"] == "delivered" and item["receipts"][0]["via"] == "monitor"


def test_5_card_approval_from_the_panel(panel, g0):
    """2.1: A1 (old e2e 1) — the gate card: an unconfirmed approval is refused and writes nothing (Ö-14); confirmed,
    the chief's signed commit, the tag and the merge on main; the record's channel is panel_confirmed (§4.6)"""
    code, d = g0
    head = git.head(d)
    r = panel.post(f"/api/works/{code}/cards/O-G0/decision", json={"action": "approve"})
    assert r.status_code == 409 and r.json()["error"]["key"] == "panel.confirm.required" and git.head(d) == head
    r = panel.post(f"/api/works/{code}/cards/O-G0/decision", json={"action": "approve", "confirmed": True,
                                                                  "viewed": head[:7]})
    assert r.status_code == 200, r.text
    assert r.json()["gate"]["tag"] == f"{code}-G0" and f"{code}-G0" in git.git("tag", cwd=d).split()
    rec = [x for x in yamlio.read(d / "approvals.yaml") if x["card"] == "O-G0"][-1]
    assert rec["channel"] == "panel_confirmed" and rec["action"] == "approve"
    assert git.git("log", "-1", "--format=%an", f"{code}-G0", cwd=d) == "Test Mühendis"
    st = panel.get(f"/api/works/{code}/stages").json()["stages"]
    assert (st[0]["status"], st[0]["tag"], st[0]["approver"]) == ("done", f"{code}-G0", "Test Mühendis")
    assert next(s for s in st if s["status"] == "in_progress")["gate"] == "G1"


def test_6_file_added_from_the_panel(panel, g0):
    """2.1: A1 — dropping a file: inputs/<name>, its SHA-256 in work.yaml `inputs`, one commit, the folder clean; an
    existing input is never overwritten"""
    code, d = g0
    body = b"ISO-10303-21;\nHEADER;\nENDSEC;\n"
    r = panel.put(f"/api/works/{code}/inputs/braket v1.step", content=body,
                  headers={"Content-Type": "application/octet-stream"})
    assert r.status_code == 200, r.text
    assert (d / "inputs" / "braket v1.step").read_bytes() == body and works.dirty(d) == ""
    rec = yamlio.read(d / "work.yaml")["inputs"][0]
    assert rec["path"] == "inputs/braket v1.step" and rec["sha256"] == hashlib.sha256(body).hexdigest()
    again = panel.put(f"/api/works/{code}/inputs/braket v1.step", content=b"x")
    assert again.status_code == 409 and again.json()["error"]["key"] == "panel.upload.exists"


def test_7_files_downloaded_from_the_panel(panel, g0):
    """2.1: A1 — downloading: a file as it is, a folder as a zip, only from out/, records/ and inputs/; the files
    screen lists each with its SHA-256"""
    code, d = g0
    panel.put(f"/api/works/{code}/inputs/not.pdf", content=b"%PDF-1.4 sinama")
    assert panel.get(f"/api/works/{code}/download/inputs/not.pdf").content == b"%PDF-1.4 sinama"
    z = zipfile.ZipFile(io.BytesIO(panel.get(f"/api/works/{code}/download/records").content))
    assert "records/events.jsonl" in z.namelist()
    folders = panel.get(f"/api/works/{code}/files").json()["folders"]
    listed = {f["path"]: f["sha256"] for k in folders for f in k["files"]}
    assert listed["inputs/not.pdf"] == hashlib.sha256(b"%PDF-1.4 sinama").hexdigest()
