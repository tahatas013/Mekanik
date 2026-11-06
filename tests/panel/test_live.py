# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live panel on a real port: A2 (stream latency, 100 events: emit → SSE line; and hook → status line), A6 (the
session's state seen again after 10 panel restarts), the old e2e 6 (new version) and 7 (the session waits for a
permission) on the back end."""

from __future__ import annotations

import json
import statistics
import threading
import time

import httpx
from panel_util import client_for

from mekanik.agent import hook
from mekanik.core.process.step import step
from mekanik.core.report import stream


def p95(xs: list[float]) -> float:
    return statistics.quantiles(xs, n=20)[-1] if len(xs) >= 20 else max(xs)


class Feed(threading.Thread):
    """Reads /api/events into (arrival time, event) pairs."""

    def __init__(self, base, cookies):
        super().__init__(daemon=True)
        self.base, self.cookies, self.got, self.ready = base, cookies, [], threading.Event()

    def run(self):
        with httpx.Client(base_url=self.base, cookies=self.cookies, timeout=None) as c:
            with c.stream("GET", "/api/events") as r:
                for line in r.iter_lines():
                    if line.startswith("event: ready"):
                        self.ready.set()
                    elif line.startswith("data: ") and (e := json.loads(line[6:])):
                        self.got.append((time.monotonic(), e))

    def wait(self, test, timeout=15.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if found := [x for x in list(self.got) if test(x[1])]:
                return found
            time.sleep(0.02)
        return []


def _feed(served):
    base, cookies, _ = served
    f = Feed(base, cookies)
    f.start()
    assert f.ready.wait(10)
    time.sleep(0.5)   # the watcher's first look at the works
    return f


def test_stream_latency_from_emit_and_hook(g0, served):
    """2.1: A2 — 100 stream events emitted as another process does (records/events.jsonl) reach the page's event
    stream with p95 ≤ 1.0 s; 100 hook events (session records) reach it as `status` lines with p95 ≤ 1.0 s"""
    code, d = g0
    feed = _feed(served)
    sent = {}
    for i in range(100):
        t0 = time.monotonic()
        sent[stream.emit(d, "notice", line=f"olay {i}")["id"]] = t0
        time.sleep(0.01)
    assert len(feed.wait(lambda e: e["type"] == "stream" and e["event"]["line"] == "olay 99")) == 1
    arrived = {e["event"]["id"]: at for at, e in feed.got if e["type"] == "stream"}
    lat = [arrived[i] - t0 for i, t0 in sent.items()]
    assert len(lat) == 100 and p95(lat) <= 1.0, (p95(lat), max(lat))
    hooks = {}
    for i in range(100):
        hooks[f"s{i:03d}"] = time.monotonic()
        hook.handle("PostToolUse", {"session_id": f"s{i:03d}", "cwd": str(d), "tool_name": "Read"})
        time.sleep(0.03)
    feed.wait(lambda e: e["type"] == "status" and any(
        (r.get("adapter") or {}).get("session_id") == "s099" for r in e["runs"]))
    first = {}
    for at, e in feed.got:
        for r in e.get("runs") or [] if e["type"] == "status" else []:
            first.setdefault((r.get("adapter") or {}).get("session_id"), at)
    lat2 = [first[s] - t0 for s, t0 in hooks.items()]
    assert len(lat2) == 100 and p95(lat2) <= 1.0, (p95(lat2), max(lat2))
    print(f"A2 emit→SSE p95 {p95(lat):.3f} s max {max(lat):.3f} s; hook→SSE p95 {p95(lat2):.3f} s")


def test_new_version_and_waiting_session(g0, served):
    """2.1: old e2e 6 and 7 — a new step gives a `new_version` line with its commit and title (the open model is not
    reloaded by itself); a permission notification of the session gives a `status` line and the liveness says the
    session waits for a permission, the ball is the chief's"""
    code, d = g0
    feed = _feed(served)
    s = step(d, "ajan adımı: sınama", "design_engineer")
    (at, ev), *_ = feed.wait(lambda e: e["type"] == "new_version" and e["commit"] == s["commit"])
    assert ev["work"] == code and ev["line"] == "ajan adımı: sınama" and ev["role"] == "design_engineer"
    hook.handle("Notification", {"session_id": "s", "cwd": str(d), "message": "Claude needs your permission to use "
                                 "Bash", "notification_type": "permission_prompt"})
    assert feed.wait(lambda e: e["type"] == "status" and any(r.get("status") == "waiting_permission"
                                                             for r in e["runs"]))
    base, cookies, _ = served
    live = httpx.get(f"{base}/api/works/{code}/liveness", cookies=cookies).json()
    assert (live["liveness"]["status"], live["liveness"]["reason"]) == ("waiting", "permission")
    assert live["ball"]["key"] == "panel.ball.waiting_permission" and live["ball"]["who"] == "chief_engineer"


def test_session_state_survives_panel_restarts(g0):
    """2.1: A6 — the panel keeps no session state of its own: after each of 10 restarts it shows the open session
    (tab, run record, liveness) again, from the hooks' records (10/10)"""
    from mekanik.panel.app import create_app

    code, d = g0
    for event in ("SessionStart", "PostToolUse"):
        hook.handle(event, {"session_id": "oturum-1", "cwd": str(d), "tool_name": "Edit"})
    seen = 0
    for _ in range(10):
        with client_for(create_app()) as c:
            tabs, live = c.get("/api/tabs").json(), c.get(f"/api/works/{code}/liveness").json()
            run = c.get(f"/api/works/{code}/status").json()["run"]
            seen += ([t["code"] for t in tabs["tabs"]] == [code] and live["liveness"]["status"] == "working"
                     and run["adapter"]["session_id"] == "oturum-1" and run["status"] == "running")
    assert seen == 10
