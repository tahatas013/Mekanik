# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inbox of a work (§5.6): state/inbox/<code>.jsonl, append-only: the panel's and `mekanik agent send|stop`'s messages,
then their delivery (monitor, or hooks at a turn boundary) and reading; a pending one is the next session's first
notification (no session is started for it, T-09). The session lock (A8): state/locks/<code>.json, others read-only."""

import fcntl
import json
import secrets
from contextlib import contextmanager
from pathlib import Path

from mekanik.config import state_dir
from mekanik.core import clock, yamlio
from mekanik.core.i18n import t
from mekanik.core.process import refuse

from . import hook

MESSAGES = ("instruction", "stop", "resume")
STALE_MIN = 30   # source: assumption — pulse.SILENT_MIN: a lock holder silent this long has died without SessionEnd


def path(code: str) -> Path:
    return state_dir() / "inbox" / f"{code}.jsonl"


@contextmanager
def _held(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p.with_name(p.name + ".lock"), "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)   # panel, CLI, monitor and hooks are separate processes
        yield


def _add(code: str, *recs: dict) -> None:
    with path(code).open("a", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)


def _message(code: str, kind: str, by: str, via: str, text: str) -> dict:
    rec = {"id": f"in-{clock.now()[:19].replace(':', '')}-{secrets.token_hex(2)}", "kind": kind, "work": code,
           "at": clock.now(), "by": by, "via": via, "text": text.strip()}
    with _held(path(code)):
        _add(code, rec)
    return rec


def send(code: str, text: str, by: str = "chief_engineer", via: str = "panel") -> dict:
    """`mekanik agent send`: an instruction for the work's session; → the inbox record."""
    refuse(not text.strip(), "panel.inbox.empty")
    return _message(code, "instruction", by, via, text)


def stop(code: str, reason: str = "", by: str = "chief_engineer", via: str = "panel") -> dict:
    """`mekanik agent stop`: the stop flag (PreToolUse then denies every non-mekanik tool, A5) and a notification."""
    yamlio.write_text(hook.stop_flag(code), json.dumps({"at": clock.now(), "by": by, "reason": reason}))
    return _message(code, "stop", by, via, reason)


def resume(code: str, by: str = "chief_engineer", via: str = "panel") -> dict:
    """`mekanik agent stop --clear`: the flag goes; the session is told it may go on."""
    hook.stop_flag(code).unlink(missing_ok=True)
    return _message(code, "resume", by, via, "")


def items(code: str) -> list[dict]:
    """Messages, oldest first, each with state pending | delivered | read and its receipts."""
    try:
        lines, out = [json.loads(x) for x in path(code).read_text(encoding="utf-8").splitlines() if x.strip()], {}
    except (OSError, ValueError):
        return []
    for x in lines:
        if x.get("kind") in MESSAGES:
            out[x["id"]] = {**x, "state": "pending", "receipts": []}
        elif (m := out.get(x.get("ref"))) is not None:
            m["receipts"].append(x)
            m["state"] = "read" if "read" in (m["state"], x["kind"]) else "delivered"
    return list(out.values())


def take(code: str, via: str, session: str = "") -> list[dict]:
    """The pending messages, marked delivered by `via` (monitor | hook) in the same lock: each goes out once."""
    with _held(path(code)):
        got = [m for m in items(code) if m["state"] == "pending"]
        _add(code, *({"kind": "delivered", "ref": m["id"], "at": clock.now(), "via": via,
                      **({"session": session} if session else {})} for m in got))
    return got


def mark_read(code: str, ids: list[str], via: str = "mcp") -> None:
    with _held(path(code)):
        _add(code, *({"kind": "read", "ref": i, "at": clock.now(), "via": via} for i in ids))


def line(m: dict) -> str:
    return t(f"panel.inbox.{m['kind']}", work=m["work"], time=m["at"][11:16], text=" ".join(m.get("text", "").split()))


def _live(code: str, sid: str) -> bool:
    return any((r.get("adapter") or {}).get("session_id") == sid and r.get("status") not in ("finished", "failed")
               and clock.minutes_since(at) < STALE_MIN for at, r in hook.runs(code))


def holder(code: str) -> dict | None:
    """The lock record of the session that writes in the work, if it is still alive."""
    rec = yamlio.read(state_dir() / "locks" / f"{code}.json")
    return rec if isinstance(rec, dict) and _live(code, rec.get("session", "")) else None


def claim(code: str, session: str, event: str) -> dict | None:
    """The hooks' lock step: the holder or the first session keeps or takes the lock (→ None); another live holder's
    record comes back and this session is read-only. The holder's SessionEnd frees the lock."""
    with _held(lock := state_dir() / "locks" / f"{code}.json"):
        mine = isinstance(cur := yamlio.read(lock), dict) and cur.get("session") == session
        if not session or event == "SessionEnd":
            if mine:
                lock.unlink()
            return None
        if isinstance(cur, dict) and not mine and _live(code, cur.get("session", "")):
            return cur
        mine or yamlio.write_text(lock, json.dumps({"session": session, "work": code, "at": clock.now()}))
    return None
