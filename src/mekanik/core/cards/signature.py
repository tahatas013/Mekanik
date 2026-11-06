# SPDX-License-Identifier: AGPL-3.0-or-later
"""Commit signature of each approval record (APPROVAL-02, architecture §4.6).

approvals.yaml is append-only; a record belongs to the last commit that changed its entry, and that commit must be
signed by the chief's key (`identities.chief_signing_key`). Signatures are read with git's %G? (status) and %GF/%GP
(signing key and primary key fingerprint); SSH keys give `SHA256:…` fingerprints, GPG keys hexadecimal ones.
A migrated record (`migrated_from_hash`) is unsigned; it counts when its `migration_approval` commit is (V5)."""

from __future__ import annotations

from pathlib import Path

from .. import yamlio
from ..errors import GitError
from ..store.git import git

FILE = "approvals.yaml"
GOOD = ("G", "U")   # good signature; U = validity unknown to gpg/ssh — the key is pinned by its fingerprint below
_FMT = "--format=%G?%x1f%GF%x1f%GP"
# An empty allowed-signers file makes git verify an SSH signature without a principal ('U' + fingerprint); without it
# git refuses SSH verification. Trust comes from the fingerprint match, not from this file.
_SSH = ("-c", "gpg.ssh.allowedSignersFile=/dev/null")


def _norm(key: str) -> str:
    key = (key or "").strip()
    return key if key.startswith("SHA256:") else key.replace(" ", "").upper()


def matches(key: str, *fingerprints: str) -> bool:
    """Same key: equal fingerprint, or a GPG long key id (≥ 16 hex) that ends the fingerprint."""
    k = _norm(key)
    for f in map(_norm, filter(None, fingerprints)):
        if f == k or (len(k) >= 16 and not k.startswith("SHA256:") and f.endswith(k)):
            return True
    return False


def signer(root: Path, rev: str) -> tuple[str, str, str]:
    """(status, signing key fingerprint, primary key fingerprint) of one commit."""
    st, fpr, prim = (git(*_SSH, "log", "-1", _FMT, rev, cwd=root) + "\x1f\x1f").split("\x1f")[:3]
    return st or "N", fpr, prim


def record_commits(root: Path, records: list[dict]) -> list[str | None]:
    """Commit that last changed each record's entry; None if the working copy differs from every commit."""
    last: dict[int, str] = {}
    prev: list = []
    for h in git("log", "--reverse", "--format=%H", "--", FILE, cwd=root).split():
        try:
            cur = yamlio.load(git("show", f"{h}:./{FILE}", cwd=root)) or []
        except GitError:          # file removed in that commit
            cur = []
        for i, r in enumerate(cur):
            if i >= len(prev) or prev[i] != r:
                last[i] = h
        prev = cur
    return [last.get(i) if i < len(prev) and prev[i] == r else None for i, r in enumerate(records)]


def verify(root: Path, records: list[dict], key: str) -> list[tuple[str, dict] | None]:
    """Per record: None when valid, else (problem key, message args)."""
    try:
        commits = record_commits(Path(root), records)
    except GitError:
        return [("no_repo", {})] * len(records)
    out: list[tuple[str, dict] | None] = []
    seen: dict[str, tuple[str, str, str]] = {}
    for rec, h in zip(records, commits):
        if rec.get("migrated_from_hash"):
            h = rec.get("migration_approval")
            if not h:
                out.append(("migrated", {}))
                continue
        if h is None:
            out.append(("uncommitted", {}))
            continue
        if h not in seen:
            try:
                seen[h] = signer(Path(root), h)
            except GitError:
                seen[h] = ("N", "", "")
        st, fpr, prim = seen[h]
        args = {"commit": h[:12], "status": st, "fingerprint": fpr or "—"}
        if st == "N":
            out.append(("unsigned", args))
        elif st not in GOOD:
            out.append(("bad", args))
        elif not matches(key, fpr, prim):
            out.append(("other_key", args))
        else:
            out.append(None)
    return out
