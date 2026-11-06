# SPDX-License-Identifier: AGPL-3.0-or-later
"""Commit signature of each approval record (APPROVAL-02, architecture §4.6).

approvals.yaml is append-only, against its history too: every committed version, and the working copy, is the one
before with records added; otherwise every record is invalid (`rewritten`). A record belongs to the commit that added
it, and that commit must be signed by the chief's key (`identities.chief_signing_key`). Signatures are read with git's
%G? (status) and %GF/%GP (signing key and primary key fingerprint) through the trusted programs (store.git.SAFE); SSH
keys give `SHA256:…` fingerprints, GPG keys hexadecimal ones. A migrated record (`migrated_from_hash`) is unsigned; it
counts when the chief's valid signed approval of the migration card MG-01 covers it (V5, KF1-18; `migration_cover`).
The key is pinned in the organization repo (org.yaml `chief_signing_key`, in commits signed by that key; §4.6 m.4,
KF1-07): when a pin exists, a configured key other than the pinned one, or a pin that changed, voids every record."""

from __future__ import annotations

from pathlib import Path

from .. import yamlio
from ..errors import GitError
from ..i18n import t
from ..store.git import commit, git, message, toplevel
from . import approval

FILE, GAP_CARD, PIN = "approvals.yaml", "MG-01", "org.yaml"
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


def pin(root: Path, key: str, chief: tuple[str, str]) -> str:
    """The chief pins his key: org.yaml `chief_signing_key` at the organization repo root, in a commit he signs."""
    top = toplevel(Path(root))
    yamlio.write(top / PIN, (yamlio.read(top / PIN, {}) or {}) | {"chief_signing_key": key})
    return commit(top, message(t("checks.signature.pin_title", fingerprint=key), None, "chief_engineer"), [str(top / PIN)],
                  chief, sign=True)


def pinned(root: Path, key: str) -> tuple[str, dict] | None:
    """None when nothing is pinned or `key` is the pinned key; else the problem. Every version of org.yaml on every
    branch holds one key, in a commit signed by that key (a changed, removed or unsigned pin is `pin_changed`)."""
    top, seen = toplevel(Path(root)), set()
    for h in (hs := git("log", "--all", "--format=%H", "--", PIN, cwd=top).split()):
        try:
            k = str((yamlio.load(git("show", f"{h}:{PIN}", cwd=top)) or {}).get("chief_signing_key") or "")
        except GitError:          # removed in that commit
            k = ""
        st, fpr, prim = signer(top, h)
        seen.add(k if k and st in GOOD and matches(k, fpr, prim) else None)
    if not hs:
        return None
    if None in seen or len(seen) > 1:
        return "pin_changed", {"commit": hs[0][:12]}
    k = seen.pop()
    return None if matches(key, k) or matches(k, key) else ("key_pin", {"configured": key or "—", "pinned": k})


def migration_cover(view, found: list) -> tuple[set, set]:
    """(record hashes, gates) the chief took over by approving MG-01: its subject lists them (`approvals`, `gates`),
    his last decision on it is a valid signed approval, and that approval's hash is the subject's as it is now, so a
    record or gate added later is not covered."""
    last = approval.last(view, GAP_CARD)
    i = next((i for i, r in enumerate(view.approvals) if r is last), None)
    subj = next((c.get("subject") or {} for c in view.cards if c.get("id") == GAP_CARD), {})
    if i is None or last["action"] != "approve" or found[i] is not None or last.get(
            "approved_hash") != approval.digest(approval.subject_values(view, subj)):
        return set(), set()
    return set(subj.get("approvals") or []), set(subj.get("gates") or [])


def verify(root: Path, records: list[dict], key: str) -> list[tuple[str, dict] | None]:
    """Per record: None when valid, else (problem key, message args)."""
    try:
        commits, bad = record_commits(Path(root), records), pinned(Path(root), key)
    except Rewritten as e:
        return [("rewritten", {"commit": str(e)[:12] or "—"})] * len(records)
    except GitError:
        return [("no_repo", {})] * len(records)
    if bad:
        return [bad] * len(records)
    out: list[tuple[str, dict] | None] = []
    seen: dict[str, tuple[str, str, str]] = {}
    for rec, h in zip(records, commits):
        if h is None or rec.get("migrated_from_hash"):   # a migrated record: migration_cover decides
            out.append(("migrated" if rec.get("migrated_from_hash") else "uncommitted", {}))
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
