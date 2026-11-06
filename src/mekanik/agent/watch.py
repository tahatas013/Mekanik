# SPDX-License-Identifier: AGPL-3.0-or-later
"""Watcher (old `gozcu.py`, E-14; `mekanik watch`, the plugin's monitor): a line per chief-identity commit in the org
repos (`TST-SYN-01 · 23:20 · O-G1 approved · 9d6afd4`) and per inbox message (what waited first, A12). Skipped:
log-only commits, archive repos, organizations that forbid data transfer. It only reads and prints (§5.4)."""

import os
import time
from pathlib import Path

from mekanik.config import load_config
from mekanik.core.errors import GitError
from mekanik.core.i18n import t
from mekanik.core.store.git import git

from . import inbox
from .hook import WORK_CODE, org_allowed, work_of

INTERVAL = 3.0  # source: assumption — old gozcu.calistir: poll interval in seconds (local git, cheap)
TICK = 0.5  # source: assumption — inbox poll in seconds (A12: an instruction reaches the session in p95 ≤ 5 s)
SINCE = "2.hours"  # source: assumption — old gozcu.yeni_olaylar: look-back window of git log
ARCHIVE = {"archive", "arsiv"}  # old gozcu.kurum_repolari: a repo under an archive folder is not watched


def org_repos(cfg) -> list[Path]:
    repos = [(o, Path(os.path.expanduser(o["repo"]))) for o in cfg.lists["organizations"]]
    return [r for o, r in repos if o["data_transfer"]["model_provider_allowed"] is True and (r / ".git").exists()
            and not ARCHIVE & set(r.parts)]


def new_events(repos: list[Path], seen: set[str], author: str) -> list[str]:
    """Lines for commits by `author` ("Name <email>", fixed string) not yet `seen`, oldest first."""
    out = []
    for repo in repos:
        try:
            log = git("log", "--all", f"--since={SINCE}", "-F", f"--author={author}", "--date=format:%H:%M",
                      "--format=%x1e%H%x1f%ad%x1f%s", "--name-only", cwd=repo)
        except GitError:
            continue
        for entry in reversed(log.split("\x1e")[1:]):
            head, _, rest = entry.partition("\n")
            (sha, at, title), files = head.split("\x1f", 2), [f for f in rest.splitlines() if f]
            if sha not in seen and not (files and all("records/log/" in f for f in files)):
                code = next((m.group(0) for f in files if (m := WORK_CODE.search(f))), "?")
                out.append(t("agent.watch.event", work=code, time=at, title=title, sha=sha[:7]))
            seen.add(sha)
    return out


def deliver(work: str) -> list[str]:
    """The inbox's pending messages as lines, marked delivered by the monitor (none in a forbidden organization)."""
    return [inbox.line(m) for m in inbox.take(work, "monitor")] if org_allowed(work[:3]) else []


def watch(cwd: Path | None = None, interval: float = INTERVAL, rounds: int | None = None, tick: float = TICK) -> int:
    """Print the events until stopped; outside a work folder exit at once (a monitor starts it anywhere). `rounds`
    counts the git polls (every `interval` s); the inbox is read every `tick` s."""
    if not (work := work_of(Path(cwd or os.getcwd()))):
        return 0
    cfg = load_config()
    repos, seen, author = org_repos(cfg), set(), "{} <{}>".format(*cfg.chief)
    new_events(repos, seen, author)  # what is already there is not an event
    for line in deliver(work):   # what waited for the session is its first notification
        print(line, flush=True)
    print(t("agent.watch.started", repos=len(repos), who=cfg.chief[0]), flush=True)
    while rounds is None or (rounds := rounds - 1) >= 0:
        for line in new_events(repos, seen, author):
            print(line, flush=True)
        for _ in range(max(1, round(interval / tick)) if tick else 1):
            for line in deliver(work):
                print(line, flush=True)
            time.sleep(min(tick, interval))
    return 0
