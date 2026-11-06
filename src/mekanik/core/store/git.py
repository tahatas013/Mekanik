# SPDX-License-Identifier: AGPL-3.0-or-later
"""Git helpers and commit trailers (old `git.py`).

Team commits use the team identity from the workshop config; chief-engineer commits (approvals) use the chief
identity and are signed (APPROVAL-02). Trailers: Step, Role, Card, Visual, Log; values keep the record language.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from ..errors import GitError

ROLES = {"project_engineer", "design_engineer", "technician", "quality_engineer", "chief_engineer", "system"}
TRAILERS = ("Step", "Role", "Card", "Visual", "Log")
# Signing-related variables are removed so a child process cannot borrow an identity (architecture §4.6).
_IDENTITY_ENV = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")
_BIN = "/usr/local/bin:/usr/bin:/bin"   # source: assumption — the usual system folders, not PATH or a repo's config
# Every call: no repo hooks; only an explicit -S signs (a user's commit.gpgsign never signs a team commit); the signing
# programs from _BIN (§4.6), and a missing one fails: its signature counts as unsigned.
_PROGRAMS = {"gpg": "gpg", "gpg.ssh": "ssh-keygen", "gpg.x509": "gpgsm"}
_CFG = {"core.hooksPath": "/dev/null", "core.fsmonitor": "false", "commit.gpgSign": "false", "tag.gpgSign": "false",
        "gpg.ssh.allowedSignersFile": "/dev/null",   # SSH: verified without a principal; the fingerprint is the trust
        **{f"{k}.program": shutil.which(n, path=_BIN) or "/nonexistent/" for k, n in _PROGRAMS.items()}}
SAFE = [x for k, v in _CFG.items() for x in ("-c", f"{k}={v}")]


def git(*args: str, cwd: Path, stdin: str | None = None, env: dict | None = None) -> str:
    env = {k: v for k, v in os.environ.items() if k not in _IDENTITY_ENV} | (env or {})
    p = subprocess.run(["git", *SAFE, *args], cwd=cwd, capture_output=True, text=True, input=stdin, env=env)
    if p.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def identity_env(name: str, email: str) -> dict:
    return {f"GIT_{w}_{k}": v for w in ("AUTHOR", "COMMITTER") for k, v in (("NAME", name), ("EMAIL", email))}


def message(title: str, step: str | None, role: str, cards: list[str] = (), visuals: list[str] = (),
            extra: dict | None = None) -> str:
    if role not in ROLES:
        raise ValueError(f"role must be one of {sorted(ROLES)}")
    lines = [title, ""]
    if step:
        lines.append(f"Step: {step}")
    lines.append(f"Role: {role}")
    if cards:
        lines.append(f"Card: {', '.join(cards)}")
    lines += [f"Visual: {v}" for v in visuals]
    lines += [f"{k}: {v}" for k, v in (extra or {}).items()]
    return "\n".join(lines) + "\n"


_TRAILER = re.compile(r"^([A-Za-z-]+): (.+)$")


def trailers(msg: str) -> dict:
    """`Key: value` lines of the last paragraph. Visual may repeat (list); Card is a comma list."""
    para = msg.strip().split("\n\n")[-1].splitlines()
    out: dict = {}
    if not all(_TRAILER.match(s) for s in para):
        return out
    for s in para:
        k, v = _TRAILER.match(s).groups()
        if k == "Visual":
            out.setdefault(k, []).append(v)
        elif k == "Card":
            out[k] = [x.strip() for x in v.split(",") if x.strip()]
        else:
            out[k] = v
    return out


def commit(cwd: Path, msg: str, paths: list[str] | None = None, identity: tuple[str, str] | None = None,
           allow_empty: bool = False, sign: bool = False) -> str:
    """Stage `paths` (all when None) and commit with `identity`; `sign=True` adds -S (chief approvals)."""
    git("add", "-A", *(["--", *paths] if paths else []), cwd=cwd)
    args = ["commit", "-q", "-F", "-"] + (["--allow-empty"] if allow_empty else []) + (["-S", "--no-verify"] * sign)
    git(*args, cwd=cwd, stdin=msg, env=identity_env(*identity) if identity else None)
    return git("rev-parse", "HEAD", cwd=cwd)


def toplevel(cwd: Path) -> Path:
    return Path(git("rev-parse", "--show-toplevel", cwd=cwd))


def branch(cwd: Path) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)


def head(cwd: Path) -> str:
    return git("rev-parse", "HEAD", cwd=cwd)


def branch_exists(repo: Path, name: str) -> bool:
    try:
        git("rev-parse", "--verify", "--quiet", f"refs/heads/{name}", cwd=repo)
        return True
    except GitError:
        return False


def is_clean(cwd: Path) -> bool:
    return not git("--no-optional-locks", "status", "--porcelain", cwd=cwd)
