# SPDX-License-Identifier: AGPL-3.0-or-later
"""The session tab's terminal (A13, T-18a; architecture §5.4): the user's own interactive Claude Code, unchanged, in
a PTY under the panel and in the work folder, shown by xterm.js over the WebSocket W/pty. The socket is accepted only
after auth.refusal (loopback client, allowed Host, same-origin Origin, the session cookie). One terminal per work: a
page that reconnects attaches to it and sees the recent output again. It ends with the panel or on "close"; the
next start continues the conversation with `claude --resume <id>` (the id is chosen at the first start with
`--session-id` and kept in the state folder, which the agent may not read). Only this socket's keystrokes reach the
terminal: the instruction box writes to the inbox, never here (§5.3, §5.4).

Protocol: server → {"type": "ready", "running", "session"}; page → {"type": "start", "mode": "resume"|"new", "cols",
"rows"}; server → {"type": "started", "session", "resumed"}, then the output as binary frames; page → {"type":
"input", "data"} | {"type": "resize", "cols", "rows"} | {"type": "close"}; server → {"type": "exit", "code"}."""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import json
import os
import pty
import shlex
import shutil
import signal
import struct
import termios
import uuid

from mekanik.config import state_dir

COMMAND = "claude"   # MEKANIK_CLAUDE replaces it (shell words; the tests' fake agent)
BACKLOG = 256 * 1024   # source: assumption — bytes of recent output shown again to a page that reconnects
READ = 65536   # source: assumption — bytes read from the terminal at a time
TERMS: dict[str, "Term"] = {}


def record(code: str):
    return state_dir() / "terminals" / f"{code}.json"


def saved(code: str) -> str | None:
    try:
        return json.loads(record(code).read_text())["session"]
    except (OSError, ValueError, KeyError):
        return None


class Term:
    def __init__(self, code: str, pid: int, fd: int, session: str, resumed: bool):
        self.code, self.pid, self.fd, self.session, self.resumed = code, pid, fd, session, resumed
        self.clients: set[asyncio.Queue] = set()
        self.backlog, self.loop, self.code_ = bytearray(), asyncio.get_running_loop(), None
        self.loop.add_reader(fd, self._read)

    def _send(self, item) -> None:
        for q in list(self.clients):
            q.put_nowait(item)

    def _read(self) -> None:
        try:
            data = os.read(self.fd, READ)
        except OSError:   # EIO: the program closed the terminal (it ended)
            data = b""
        if not data:
            return self._ended()
        self.backlog += data
        del self.backlog[:-BACKLOG]
        self._send(data)

    def _ended(self) -> None:
        self.loop.remove_reader(self.fd)
        with contextlib.suppress(OSError):
            os.close(self.fd)
        TERMS.pop(self.code, None)
        self._reap(20)

    def _reap(self, tries: int) -> None:
        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
        except ChildProcessError:
            pid, status = self.pid, 0
        if pid or not tries:
            self.code_ = os.waitstatus_to_exitcode(status) if pid else None
            return self._send({"type": "exit", "code": self.code_})
        self.loop.call_later(0.1, self._reap, tries - 1)

    def write(self, text: str) -> None:
        os.write(self.fd, text.encode())

    def resize(self, cols: int, rows: int) -> None:
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", max(rows, 2), max(cols, 10), 0, 0))

    def close(self) -> None:
        """Hang up the program's session (as closing a terminal window does); it may save and end."""
        with contextlib.suppress(OSError):
            os.killpg(self.pid, signal.SIGHUP)


def spawn(code: str, root, mode: str, cols: int, rows: int) -> Term:
    """Start the agent in the work folder: `--resume <id>` when a session is known and `mode` is not "new", else a
    new session with a chosen id and the resume prompt as its first message (as the deep link gives it)."""
    known = saved(code) if mode != "new" else None
    session = known or str(uuid.uuid4())
    words = shlex.split(os.environ.get("MEKANIK_CLAUDE", COMMAND))
    args = [*words, "--resume", session] if known else [*words, "--session-id", session, f"/mekanik:resume {code}"]
    exe = shutil.which(args[0]) or args[0]
    env = {**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor"}
    pid, fd = pty.fork()
    if pid == 0:   # the child only changes folder and executes (the panel has threads: nothing else after fork)
        try:
            os.chdir(root)
            os.execve(exe, args, env)
        finally:
            os._exit(127)
    record(code).parent.mkdir(parents=True, exist_ok=True)
    record(code).write_text(json.dumps({"session": session, "resumed": bool(known)}))
    term = TERMS[code] = Term(code, pid, fd, session, bool(known))
    term.resize(cols, rows)
    return term


async def serve(ws, code: str, root) -> None:
    """One page's connection: ready → start → output and keystrokes until the page leaves (the terminal stays)."""
    await ws.send_json({"type": "ready", "running": code in TERMS, "session": saved(code)})
    q: asyncio.Queue = asyncio.Queue()
    term = None

    async def pump():
        while True:
            item = await q.get()
            await (ws.send_bytes(bytes(item)) if isinstance(item, (bytes, bytearray)) else ws.send_json(item))

    task = None
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            m = json.loads(msg.get("text") or "{}")
            if m.get("type") == "start" and term is None:
                term = TERMS.get(code) or spawn(code, root, m.get("mode", "resume"), int(m.get("cols", 80)),
                                                int(m.get("rows", 24)))
                await ws.send_json({"type": "started", "session": term.session, "resumed": term.resumed})
                term.clients.add(q)
                q.put_nowait(bytes(term.backlog))
                task = asyncio.create_task(pump())
            elif term is not None and m.get("type") == "input":
                term.write(str(m.get("data", "")))
            elif term is not None and m.get("type") == "resize":
                term.resize(int(m.get("cols", 80)), int(m.get("rows", 24)))
            elif term is not None and m.get("type") == "close":
                term.close()
    finally:
        if term is not None:
            term.clients.discard(q)
        if task:
            task.cancel()


def close_all(grace: float = 2.0) -> None:
    """The panel stops: every terminal ends with it (hang-up, then kill after `grace` s; the conversation continues
    with --resume at the next start)."""
    import time

    terms = list(TERMS.values())
    TERMS.clear()
    for term in terms:
        term.close()
        term.loop.remove_reader(term.fd)
        with contextlib.suppress(OSError):
            os.close(term.fd)
    end = time.monotonic() + grace
    for term in terms:
        while time.monotonic() < end and _alive(term.pid):
            time.sleep(0.05)
        if _alive(term.pid):
            with contextlib.suppress(OSError):
                os.killpg(term.pid, signal.SIGKILL)
                os.waitpid(term.pid, 0)


def _alive(pid: int) -> bool:
    try:
        return os.waitpid(pid, os.WNOHANG)[0] == 0
    except ChildProcessError:
        return False
