# SPDX-License-Identifier: AGPL-3.0-or-later
"""Commit signature of each approval record (APPROVAL-02, architecture §4.6).

approvals.yaml is append-only, against its history too: every committed version, and the working copy, is the one
before with records added; otherwise every record is invalid (`rewritten`). A record belongs to the commit that added
it, and that commit must be signed by the chief's key (`identities.chief_signing_key`). Signatures are read with git's
%G? (status) and %GF/%GP (signing key and primary key fingerprint) through the trusted programs (store.git.SAFE); SSH
keys give `SHA256:…` fingerprints, GPG keys hexadecimal ones. A migrated record (`migrated_from_hash`) is unsigned; it
counts when its `migration_approval` is the chief's signed approval of the migration card MG-01 (V5)."""

from __future__ import annotations

from pathlib import Path

from .. import yamlio
from ..errors import GitError
from ..store.git import git, trailers

FILE, GAP_CARD = "approvals.yaml", "MG-01"
GOOD = ("G", "U")   # good signature; U = validity unknown to gpg/ssh — the key is pinned by its fingerprint below
_FMT = "--format=%G?%x1f%GF%x1f%GP"


class Rewritten(GitError):
    """A version of approvals.yaml is not the one before with records added (its commit, or '' for the working copy)."""


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
    st, fpr, prim = (git("log", "-1", _FMT, rev, cwd=root) + "\x1f\x1f").split("\x1f")[:3]
    return st or "N", fpr, prim


def record_commits(root: Path, records: list[dict]) -> list[str | None]:
    """Commit that added each record (None: not committed yet); raises Rewritten when the history is not append-only."""
    prev, out = [], []
    for h in git("log", "--reverse", "--format=%H", "--", FILE, cwd=root).split():
        try:
            cur = yamlio.load(git("show", f"{h}:./{FILE}", cwd=root)) or []
        except GitError:          # file removed in that commit
            cur = []
        if cur[:len(prev)] != prev:
            raise Rewritten(h)
        out, prev = out + [h] * (len(cur) - len(prev)), cur
    if records[:len(prev)] != prev:
        raise Rewritten("")
    return out + [None] * (len(records) - len(out))


def _migration(root: Path, ref, records: list[dict], commits: list) -> str | None:
    """Commit `ref` if it adds the chief's approve record of the migration card and carries `Card: MG-01`."""
    h = next((c for r, c in zip(records, commits) if c and ref and c.startswith(str(ref)) and r.get("card") == GAP_CARD
              and r.get("action") == "approve"), None)
    return h if h and GAP_CARD in trailers(git("log", "-1", "--format=%B", h, cwd=root)).get("Card", []) else None


def verify(root: Path, records: list[dict], key: str) -> list[tuple[str, dict] | None]:
    """Per record: None when valid, else (problem key, message args)."""
    try:
        commits = record_commits(Path(root), records)
    except Rewritten as e:
        return [("rewritten", {"commit": str(e)[:12] or "—"})] * len(records)
    except GitError:
        return [("no_repo", {})] * len(records)
    out: list[tuple[str, dict] | None] = []
    seen: dict[str, tuple[str, str, str]] = {}
    for rec, h in zip(records, commits):
        if migrated := rec.get("migrated_from_hash"):   # its signature is that of the migration approval
            h = _migration(Path(root), rec.get("migration_approval"), records, commits)
        if h is None:
            out.append(("migrated" if migrated else "uncommitted", {}))
            continue
        if h not in seen:
            try:
                seen[h] = signer(Path(root), h)
            except GitError:
                seen[h] = ("N", "", "")
        st, fpr, prim = seen[h]
        args = {"commit": h[:12], "status": st, "fingerprint": fpr or "—"}
        problem = "unsigned" if st == "N" else "bad" if st not in GOOD else not matches(key, fpr, prim) and "other_key"
        out.append((problem, args) if problem else None)
    return out
