# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live stream (architecture §9.1): `records/events.jsonl`, one stream-event per line, append-only (E5).

Append-only is anchored in git, as for approvals.yaml (cards.signature): on the branch's first-parent line every
committed version starts with the one before, and the working copy starts with HEAD's (byte prefix). A rewritten, cut
or deleted line is refused at the next write (`emit`, `check` before a step's commit) and by `verify` for the history.
A hash chain in the lines was not chosen: whoever rewrites the file can recompute the chain (it holds no secret), so it
would add a field to every line and no protection that the git anchor does not already give.

Decision branches append on both sides; their merge keeps both, ours first (union merge, store.works.MERGE_RULES), so
the work branch's version stays a prefix. Emit after the action's commit: a line is never taken back."""

from __future__ import annotations

import fcntl
import hashlib
import json
import secrets
import time
from pathlib import Path
from typing import Callable, Iterator

from .. import clock, yamlio
from ..errors import GitError, MekanikError
from ..i18n import t
from ..model.schema import validate
from ..store import git

FILE = "records/events.jsonl"
SCHEMA = "1.0"
LINE_MAX = 200   # source: schema stream-event `line` maxLength (architecture §9.1: two lines on a narrow screen)
LISTENERS: list[Callable[[dict], None]] = []   # in-process subscribers (the panel); they get transient events too


class Rewritten(MekanikError):
    """A version of events.jsonl is not the one before with lines added; `where` is its commit, '' the working copy."""

    def __init__(self, where: str = ""):
        super().__init__(t("report.stream.rewritten", where=where or t("report.stream.working_copy"), file=FILE))
        self.where = where


def emit(root, kind: str, **data) -> dict:
    """Append one stream event of type `kind` (step, provisional_decision, question …) to records/events.jsonl.

    `data` holds the schema's fields: line (one line, cut to 200 characters), role (default system), visuals, refs,
    check_summary, commit, run, objection_until, persistent; shorthands: `cards=[ids]` adds card refs, a visual given
    as a path (relative to the work folder) becomes a model_view ref pinned to the file's hash, a check summary may
    carry `pass`. kind, schema_version, id, work and at (system clock) are set here. A non-persistent event (agent
    detail) goes to LISTENERS only. → the event. Raises SchemaError for a bad one, Rewritten for a rewritten file."""
    if fixed := {"kind", "schema_version", "id", "work", "at", "type"} & data.keys():
        raise TypeError(f"emit() sets {sorted(fixed)} itself")
    root = Path(root)
    ev = {"kind": "stream_event", "schema_version": SCHEMA, "id": "", "work": (yamlio.read(
        root / "work.yaml", {}) or {}).get("code"), "at": clock.now(), "type": kind, "role": data.pop("role", "system"),
        "line": _line(data.pop("line", ""))}
    refs = [*(data.pop("refs", None) or []), *({"kind": "card", "id": c} for c in data.pop("cards", None) or [])]
    shown = [v if isinstance(v, dict) else _visual(root, v) for v in data.pop("visuals", None) or []]
    if (s := data.pop("check_summary", None)) is not None:
        ev["check_summary"] = {k: int(s.get(k, 0)) for k in ("block", "warn")}
    ev.update({k: v for k, v in (("visuals", shown), ("refs", refs)) if v}, **data)
    if ev.get("persistent", True):
        (path := root / FILE).parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)   # one writer at a time: CLI, agent hooks and the panel share the file
            f.seek(0)
            if not (text := f.read()).startswith(_committed(root)):
                raise Rewritten()
            ev["id"] = _id(ev["at"], text)
            validate("stream_event", ev, FILE)
            f.write(("\n" if text and not text.endswith("\n") else "") + json.dumps(ev, ensure_ascii=False) + "\n")
    else:
        ev["id"] = _id(ev["at"], "")
        validate("stream_event", ev, FILE)
    for fn in list(LISTENERS):
        fn(ev)
    return ev


def _line(text: str) -> str:
    one = " ".join(str(text).split())
    return one if len(one) <= LINE_MAX else one[:LINE_MAX - 1] + "…"


def _visual(root: Path, rel: str) -> dict:
    p = root / rel
    return {"kind": "model_view" if str(rel).startswith("records/visuals/") else "file", "id": Path(rel).name,
            "path": str(rel), **({"hash": hashlib.sha256(p.read_bytes()).hexdigest()[:16]} if p.is_file() else {})}


def _id(at: str, text: str) -> str:
    """ev-<date>-<hhmmss><4 random digits>: unique after a union merge of two branches too (no shared counter)."""
    stem = "ev-" + at[:10] + "-" + at[11:19].replace(":", "")
    while True:
        i = f"{stem}{secrets.randbelow(10 ** 4):04d}"
        if f'"id": "{i}"' not in text:
            return i


def _committed(root: Path, rev: str = "HEAD") -> str:
    try:
        return git.git("show", f"{rev}:./{FILE}", cwd=root)
    except GitError:   # not committed yet, or not a repository
        return ""


def check(root) -> None:
    """E5 before a commit: the working copy is HEAD's version with lines added; else Rewritten."""
    path = Path(root) / FILE
    if not (path.read_text(encoding="utf-8") if path.exists() else "").startswith(_committed(Path(root))):
        raise Rewritten()


def verify(root) -> None:
    """E5 over the history: every first-parent version starts with the one before, and the working copy with HEAD's."""
    prev, root = "", Path(root)
    for h in git.git("log", "--first-parent", "--reverse", "--format=%H", "--", FILE, cwd=root).split():
        if not (cur := _committed(root, h)).startswith(prev):
            raise Rewritten(h[:12])
        prev = cur
    check(root)


def since(root, offset: int = 0) -> tuple[list[dict], int]:
    """Events after byte `offset` (complete lines) and the offset after them: the panel's live feed (SSE) polls this
    and resumes from the offset it sent last. A file shorter than `offset` was cut: Rewritten."""
    path = Path(root) / FILE
    size = path.stat().st_size if path.exists() else 0
    if size < offset:
        raise Rewritten()
    if size == offset:
        return [], offset
    with path.open("rb") as f:
        f.seek(offset)
        chunk = f.read()
    end = chunk.rfind(b"\n") + 1
    out = []
    for raw in chunk[:end].splitlines():
        try:
            out.append(json.loads(raw))
        except ValueError:   # a broken line (cut write) is skipped, never repaired
            continue
    return out, offset + end


def read(root) -> list[dict]:
    """All events of the work, oldest first."""
    return since(root)[0]


def follow(root, offset: int = 0, poll: float = 0.5, stop: Callable[[], bool] | None = None
           ) -> Iterator[tuple[list[dict], int]]:
    """(new events, offset) as they are appended, until `stop()`; a blocking tail for a thread (SSE, `mekanik watch`).
    `poll` in seconds (source: assumption — screen latency, not an engineering value)."""
    while not (stop and stop()):
        events, offset = since(root, offset)
        if events:
            yield events, offset
        else:
            time.sleep(poll)
