# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pulse (old `nabiz.py`; `mekanik pulse`): is the team working on this work now, and on what. Hooks run only in
the work's own session; from another session the team beats the pulse itself, and `mekanik step` touches it."""

import json
from datetime import datetime

from mekanik.config import state_dir
from mekanik.core import clock, yamlio

from .hook import runs

LOG_LENGTH = 30  # source: assumption — old nabiz.GUNLUK_UZUNLUGU: moves kept in the file
FRESH_MIN = 10  # source: assumption — old nabiz.TAZE_DK: a sound within this many minutes means "working"
SILENT_MIN = 30  # source: assumption — old nabiz.SESSIZ_DK: after this many minutes "may have stopped"
SESSION = {"running": "working", "waiting_permission": "waiting", "waiting_input": "waiting"}  # others: stopped


def read(work: str) -> dict | None:
    return yamlio.read(state_dir() / "pulse" / f"{work}.json")


def _write(work: str, v: dict, at: str, role: str, status: str, text: str) -> dict:
    v["log"] = ([{"at": at, "role": role, "status": status, "text": text}] + v.get("log", []))[:LOG_LENGTH]
    yamlio.write_text(state_dir() / "pulse" / f"{work}.json", json.dumps(v, ensure_ascii=False))
    return v


def beat(work: str, doing: str, role: str = "project_engineer", status: str = "working") -> dict:
    """status: working | stopped; `doing` is what is being done, or why it stopped (old nabiz.at)."""
    v, at = read(work) or {"work": work, "log": []}, clock.now()
    if status == "working" and v.get("status") != "working":
        v["started_at"] = at
    v.update(status=status, role=role, doing=doing, at=at)
    return _write(work, v, at, role, status, doing)


def touch(work: str, text: str, role: str) -> None:
    """A step was taken: a working pulse is refreshed and the move logged; a stopped one keeps its status."""
    if v := read(work):
        at = clock.now()
        v["at"] = at if v.get("status") == "working" else v["at"]
        _write(work, v, at, role, "step", text)


def liveness(work: str) -> dict:
    """working · quiet · waiting · stopped from the session's hooks and the pulse, newest wins (old nabiz.canlilik);
    `reason` (permission | input) says what a waiting session waits for."""
    n, cands = read(work) or {}, []
    for at, r in runs(work)[-1:]:
        if r["status"] not in ("finished", "failed") or clock.minutes_since(at) < FRESH_MIN:
            cands.append({"status": SESSION.get(r["status"], "stopped"), "at": at, "source": "session",
                          "role": r["role"], "doing": "", "reason": r["status"].partition("_")[2]})
    if n.get("at"):
        cands.append({"source": "pulse", **{k: n.get(k) for k in ("status", "at", "role", "doing", "started_at")}})
    if not cands:
        return {"status": "stopped", "minutes": None, "doing": "", "role": None, "source": None, "log": []}
    v = max(cands, key=lambda x: datetime.fromisoformat(x["at"]))
    v["minutes"] = max(0, clock.minutes_since(v["at"]))
    if v["status"] == "working" and v["minutes"] >= FRESH_MIN:
        v["status"], v["auto"] = ("quiet" if v["minutes"] < SILENT_MIN else "stopped"), True
    return {**v, "log": n.get("log", [])}
