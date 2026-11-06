# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live events for the page over SSE (old izleyici.py). One thread polls what other processes write: each work's
records/events.jsonl from the last offset (report.stream.since; every line → `stream`, a line with a commit also →
`new_version`: an open model never changes by itself, the user loads it), the session records, pulses, stop flags
and locks (→ `status`), the inboxes (→ `inbox`). Events emitted in this process and not kept in the file (transient
agent detail) come through report.stream.LISTENERS. The panel also sends `signing`/`signed` around a signed commit."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from mekanik.agent import hook, inbox
from mekanik.config import load_config, state_dir
from mekanik.core import yamlio
from mekanik.core.errors import MekanikError
from mekanik.core.report import stream
from mekanik.core.store import works

POLL = 0.2   # source: assumption — screen latency (A2: p95 ≤ 1 s from a hook or emit to the page), not engineering
REFRESH = 25   # source: assumption — polls between two readings of the works registries (5 s)
QUEUE = 200   # source: assumption — old Yayin: events waiting per page; a page that does not read loses the rest


class Hub:
    def __init__(self) -> None:
        self.queues: set[asyncio.Queue] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    def add(self) -> asyncio.Queue:
        self.loop = asyncio.get_running_loop()
        self.queues.add(q := asyncio.Queue(maxsize=QUEUE))
        return q

    def remove(self, q: asyncio.Queue) -> None:
        self.queues.discard(q)

    def publish(self, ev: dict) -> None:
        if self.loop and self.queues:
            text = json.dumps(ev, ensure_ascii=False, default=str)
            for q in list(self.queues):
                self.loop.call_soon_threadsafe(lambda q=q: q.full() or q.put_nowait(text))


hub = Hub()
publish = hub.publish


def _transient(ev: dict) -> None:
    if ev.get("persistent") is False:
        publish({"type": "stream", "work": ev.get("work"), "event": ev})


def known_works() -> dict[str, Path]:
    """Code → work folder of every registered work with a worktree."""
    out = {}
    for o in load_config().lists["organizations"]:
        for w in yamlio.read(Path(o["repo"]).expanduser() / "works.yaml", []) or []:
            try:
                out[w["code"]] = works.find(w["code"])
            except MekanikError:
                continue
    return out


def _stamp(*folders: str) -> dict[str, tuple]:
    out = {}
    for p in (p for f in folders for p in (state_dir() / f).glob("*") if not p.name.startswith(".")):
        try:
            out[str(p)] = ((st := p.stat()).st_mtime_ns, st.st_size)
        except OSError:   # removed meanwhile
            continue
    return out


class Watcher(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True, name="mekanik-panel-watch")
        self.stopped, self.offsets, self.works = threading.Event(), {}, {}
        self.status, self.boxes, self.n = {}, {}, 0

    def run(self) -> None:
        if _transient not in stream.LISTENERS:
            stream.LISTENERS.append(_transient)
        self.status, self.boxes = _stamp("runs", "pulse", "stop", "locks"), _stamp("inbox")
        while not self.stopped.wait(POLL):
            try:
                self.tick()
            except Exception as e:   # noqa: BLE001 — the watcher thread must not die silently
                publish({"type": "error", "text": f"{type(e).__name__}: {e}"[:200]})

    def tick(self) -> None:
        self.n += 1
        if self.n % REFRESH == 1:   # a failing registry read is retried at the next refresh, not on every poll
            for code, root in known_works().items():
                if code not in self.offsets:   # what is already there is not an event
                    self.offsets[code] = (root / stream.FILE).stat().st_size if (root / stream.FILE).exists() else 0
                self.works[code] = root
        for code, root in self.works.items():
            try:
                got, self.offsets[code] = stream.since(root, self.offsets[code])
            except stream.Rewritten:
                got, self.offsets[code] = [], 0
            for e in got:
                publish({"type": "stream", "work": code, "event": e})
                if e.get("commit"):
                    publish({"type": "new_version", "work": code, "kind": e.get("type"), **{k: e.get(k) for k in (
                        "commit", "line", "role", "at")}})
        if (now := _stamp("runs", "pulse", "stop", "locks")) != self.status:
            self.status = now
            publish({"type": "status", "runs": [{**r, "updated_at": at} for at, r in hook.runs()][-20:]})
        if (now := _stamp("inbox")) != self.boxes:
            for code in {Path(p).name.split(".")[0] for p, _ in set(now.items()) ^ set(self.boxes.items())}:
                publish({"type": "inbox", "work": code, "items": inbox.items(code)})
            self.boxes = now
