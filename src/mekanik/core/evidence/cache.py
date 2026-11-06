# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model cache `<cache>/<commit>/` (old `onbellek.py`): generated outputs of one commit (tessellation, STEP, sections).

Over the size limit the least recently *used* entry goes (LRU); use time is the mtime of the entry's `.last-used`
file, not the atime. Root and limit come from the workshop config (paths.cache, paths.cache_limit).
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from ..errors import MekanikError

# source: decision — chief engineer, 2026-10-26 (pre-K1 addition 3); paths.cache_limit in the workshop config wins
DEFAULT_LIMIT = 5 * 1024**3
# source: assumption — binary prefixes, as the old 5 GB limit was 5 · 1024³ bytes
_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
MARK = ".last-used"


def _paths() -> dict:
    from mekanik.config import load_config

    try:
        return load_config().doc.get("paths") or {}
    except MekanikError:
        return {}


def root() -> Path:
    if p := _paths().get("cache"):
        return Path(os.path.expanduser(p))
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "mekanik"


def limit() -> int:
    return int(q["value"] * _UNITS[q["unit"]]) if (q := _paths().get("cache_limit")) else DEFAULT_LIMIT


def _size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file() and not f.is_symlink())


def entry(commit: str, base: Path | None = None) -> Path:
    """The entry's folder, created when missing and marked as used."""
    path = (base or root()) / commit
    path.mkdir(parents=True, exist_ok=True)
    (path / MARK).touch()
    return path


def status(base: Path | None = None) -> tuple[int, int]:
    """(entry count, total bytes)"""
    entries = [p for p in k.iterdir() if p.is_dir()] if (k := base or root()).is_dir() else []
    return len(entries), sum(_size(p) for p in entries)


def prune(limit_bytes: int | None = None, base: Path | None = None, keep: str | None = None) -> list[str]:
    """Delete least recently used entries until the total is under the limit; returns the deleted commits. `keep`
    (the entry made now) stays; only commit-named (40 hex) children are touched (helper worktrees, previews stay)."""
    k = (base or root()).resolve()
    entries = sorted((p for p in (k.iterdir() if k.is_dir() else ()) if p.is_dir() and not p.is_symlink()
                      and re.fullmatch(r"[0-9a-f]{40}", p.name)),
                     key=lambda p: (p / MARK if (p / MARK).exists() else p).stat().st_mtime)
    sizes = {p: _size(p) for p in entries}
    total, cap, deleted = sum(sizes.values()), limit() if limit_bytes is None else limit_bytes, []
    for p in entries:
        if total <= cap:
            break
        if p.name != keep:
            shutil.rmtree(p)
            total -= sizes[p]
            deleted.append(p.name)
    return deleted
