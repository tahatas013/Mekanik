# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inbox, monitor delivery and the session lock (architecture §5.1, §5.6): A5 through `inbox.stop`, A8 (3 tests), A12
(3 tests, the latency one is tests/panel/test_live.py). Text is compared through the catalog, never literally."""

import json
import os
import threading
import time

from mekanik.agent import hook, inbox, watch
from mekanik.config import load_config
from mekanik.core.i18n import t

CODE = "TST-SYN-01"


def STARTED():
    cfg = load_config()
    return t("agent.watch.started", repos=len(watch.org_repos(cfg)), who=cfg.chief[0])


def ev(work, event, sid, **kw):
    return hook.handle(event, {"session_id": sid, "cwd": str(work), "hook_event_name": event, **kw})


def pre(work, sid, tool, **inp):
    return ev(work, "PreToolUse", sid, tool_name=tool, tool_input=inp)


def reason(out):
    return out.get("hookSpecificOutput", {}).get("permissionDecisionReason")


def test_stop_flag_from_the_inbox(work):
    """2.1: A5 — `inbox.stop` (`mekanik agent stop`) sets the flag the PreToolUse hook reads; every non-mekanik tool
    is denied, whatever the model asks; `resume` lifts it; both are inbox messages"""
    inbox.stop(CODE, "bekle")
    assert hook.stop_flag(CODE).exists() and json.loads(hook.stop_flag(CODE).read_text())["reason"] == "bekle"
    assert reason(pre(work, "s1", "Bash", command="ls")) == t("agent.deny.stop", work=CODE)
    assert reason(pre(work, "s1", "mcp__plugin_mekanik_mekanik__work_status")) is None
    inbox.resume(CODE)
    assert pre(work, "s1", "Bash", command="ls") == {} and [m["kind"] for m in inbox.items(CODE)] == ["stop", "resume"]


def test_second_session_is_warned_and_read_only(work):
    """2.1: A8 (1/3) — the first session holds the lock; a second one gets a warning at SessionStart"""
    assert ev(work, "SessionStart", "s1") == {}
    out = ev(work, "SessionStart", "s2")["hookSpecificOutput"]["additionalContext"]
    assert out == t("agent.context.locked", work=CODE, at=inbox.holder(CODE)["at"][11:16])
    assert inbox.holder(CODE)["session"] == "s1"


def test_read_only_session_cannot_write(work):
    """2.1: A8 (2/3) — the second session's writes are denied (edit, write, a shell command, a mekanik step, the
    stream-note tool); its reads pass; the holder writes"""
    ev(work, "SessionStart", "s1")
    ev(work, "SessionStart", "s2")
    locked = t("agent.deny.locked", work=CODE, at=inbox.holder(CODE)["at"][11:16])
    for tool, inp in (("Edit", {"file_path": str(work / "params.yaml")}), ("Write", {"file_path": str(work / "a")}),
                      ("Bash", {"command": "rm -rf model"}), ("Bash", {"command": "mekanik step x"}),
                      ("mcp__plugin_mekanik_mekanik__note", {"line": "x"})):
        assert reason(pre(work, "s2", tool, **inp)) == locked, tool
    for tool, inp in (("Read", {"file_path": str(work / "params.yaml")}), ("Bash", {"command": "git log --oneline"}),
                      ("Bash", {"command": "mekanik check"}), ("mcp__plugin_mekanik_mekanik__work_status", {})):
        assert pre(work, "s2", tool, **inp) == {}, tool
    assert pre(work, "s1", "Edit", file_path=str(work / "params.yaml")) == {}


def test_lock_passes_when_the_holder_ends(work):
    """2.1: A8 (3/3) — the holder's SessionEnd frees the lock; the waiting session takes it at its next event and
    writes; a holder that died without SessionEnd stops counting once its record is stale"""
    ev(work, "SessionStart", "s1")
    ev(work, "SessionStart", "s2")
    ev(work, "SessionEnd", "s1")
    assert pre(work, "s2", "Edit", file_path=str(work / "params.yaml")) == {}
    assert inbox.holder(CODE)["session"] == "s2"
    old = time.time() - 60 * (inbox.STALE_MIN + 1)
    for p in (inbox.state_dir() / "runs").glob("run-*.json"):
        os.utime(p, (old, old))
    assert inbox.holder(CODE) is None and pre(work, "s3", "Edit", file_path=str(work / "a")) == {}


def test_waiting_instruction_is_the_first_notification(work, capsys):
    """2.1: A12 (1/3) — with no session open an instruction is pending (the panel shows it); when the session opens
    its monitor prints it before anything else, and it is then delivered"""
    m = inbox.send(CODE, "Kapak kalınlığını 3 mm yap")
    assert [x["state"] for x in inbox.items(CODE)] == ["pending"]
    watch.watch(cwd=work, interval=0, rounds=1)
    lines = capsys.readouterr().out.splitlines()
    assert lines == [inbox.line(m), STARTED()]
    (x,) = inbox.items(CODE)
    assert x["state"] == "delivered" and x["receipts"][0]["via"] == "monitor"


def test_each_message_goes_out_once(work, capsys):
    """2.1: A12 (2/3) — a delivered message is not delivered again by a later monitor or by the hooks; the MCP inbox
    read marks it read"""
    from mekanik.agent import mcp

    inbox.send(CODE, "bir")
    watch.watch(cwd=work, interval=0, rounds=1)
    capsys.readouterr()
    watch.watch(cwd=work, interval=0, rounds=1)
    assert capsys.readouterr().out.splitlines() == [STARTED()]
    assert ev(work, "UserPromptSubmit", "s1", prompt="devam") == {}
    got = mcp.read_inbox(CODE)
    assert [g["text"] for g in got] == ["bir"] and inbox.items(CODE)[0]["state"] == "read"


def test_turn_boundary_route_without_a_monitor(work):
    """2.1: A12 (3/3) — where the monitor does not run (desktop, VS Code; §5.4) the hooks pass the message at the
    turn boundary: UserPromptSubmit adds it to the context, Stop refuses to stop and says it; a read-only session
    does not take the holder's messages"""
    ev(work, "SessionStart", "s1")
    a = inbox.send(CODE, "önce testleri koş")
    out = ev(work, "UserPromptSubmit", "s1", prompt="devam")
    assert out["hookSpecificOutput"]["additionalContext"] == inbox.line(a)
    b = inbox.stop(CODE, "bekle")
    ev(work, "SessionStart", "s2")
    assert ev(work, "Stop", "s2") == {}
    assert ev(work, "Stop", "s1") == {"decision": "block", "reason": inbox.line(b)}
    assert ev(work, "Stop", "s1", stop_hook_active=True) == {}
    assert {x["state"] for x in inbox.items(CODE)} == {"delivered"}


def test_monitor_is_quick(work, capsys):
    """2.1: A12 — the monitor reads the inbox every TICK seconds: a message sent while it runs is printed well within
    the 5 s bound (here one tick)"""
    th = threading.Thread(target=watch.watch, kwargs={"cwd": work, "interval": 0.2, "rounds": 10, "tick": 0.05})
    th.start()
    time.sleep(0.1)
    m = inbox.send(CODE, "hızlı")
    th.join(5)
    assert inbox.line(m) in capsys.readouterr().out.splitlines()
