# SPDX-License-Identifier: AGPL-3.0-or-later
"""Works (old `isler.py`, handbook §8): works.yaml (append-only, no number reused), worktrees <works_root>/work/<code>,
at most MAX_ACTIVE active ones counted from the agent-run records (state/runs/*.json); nothing is deleted."""

import json
import os
import re
import shlex
import subprocess
from pathlib import Path

from mekanik.config import load_config, state_dir
from mekanik.plugins import registry

from .. import clock, yamlio
from ..errors import GitError
from ..i18n import t
from ..process import Refused, refuse
from ..process.profile import load_profile
from . import git

CODE = re.compile(r"^([A-Z]{3})-([A-Z]{3})-(\d{2})$")
MAX_ACTIVE = 3   # source: decision — handbook §8 "aynı anda en çok 3 aktif çalışma"
ENDED = ("finished", "failed", "interrupted")
# append-only records keep both sides of a merge; card files are regenerated, ours is kept
MERGE_RULES = "".join(f"**/{p} merge={d}\n" for p, d in (("records/log/*.md", "union"), ("approvals.yaml", "union"),
                                                         ("replies.yaml", "union"), ("cards/*.yaml", "mekanik-card")))
SKELETON = {"params.yaml": {}, "decisions.yaml": [], "approvals.yaml": [], "replies.yaml": []}
KEEP = ("cards", "model", "out", "records/log", "records/visuals")


def _where(code: str, project: str | None = None) -> tuple[dict, Path, dict]:
    """(organization, its repo, project) of a work code, or of an organization and project code."""
    if project is None:
        refuse(not (m := CODE.match(code or "")), "store.code.bad", code=code)
        code, project = m.group(1), m.group(2)
    org = load_config().org(code)
    if (p := next((x for x in org.get("projects") or [] if x["code"] == project), None)) is None:
        raise Refused("store.project.missing", org=code, project=project)
    return org, Path(os.path.expanduser(org["repo"])), p


def dirty(path: Path) -> str:
    """`git status --porcelain` of a folder (git.is_clean gives status --no-optional-locks, which git refuses)."""
    return git.git("status", "--porcelain", "--", str(path), cwd=path)


def tree(code: str) -> Path:
    return load_config().path("works_root") / "work" / code


def find(code: str) -> Path:
    """The work folder in the work's worktree."""
    p = _where(code)[2]
    refuse(not tree(code).exists(), "store.tree.missing", code=code, path=str(tree(code)))
    return tree(code) / p.get("folder", p["code"].lower()) / code


def resolve(arg: str | None) -> Path:
    """A work code, or a folder at or below a work folder."""
    if arg and CODE.match(arg):
        return find(arg)
    here = Path(arg or ".").resolve()
    if (found := next((d for d in (here, *here.parents) if (d / "work.yaml").exists()), None)) is None:
        raise Refused("store.not_in_work", path=str(here))
    return found


def setup_repo(repo: Path) -> None:
    """Local merge rules of the organization repo (info/attributes and config; nothing to commit)."""
    common = Path(git.git("rev-parse", "--git-common-dir", cwd=repo))
    yamlio.write_text((common if common.is_absolute() else repo / common) / "info" / "attributes", MERGE_RULES)
    git.git("config", "merge.mekanik-card.name", "mekanik card file: keep ours", cwd=repo)
    git.git("config", "merge.mekanik-card.driver", "true", cwd=repo)


def new_work(org: str, project: str, title: str, risk_class: str, purpose: str = "", done_criterion: str = "",
             profiles: dict | None = None, work_type: str | None = None, topic: str = "general") -> str:
    """`mekanik work new`: the next code, <code>/main and the work branch in a worktree, the skeleton; → the code."""
    prof, team = load_profile(), load_config().team
    refuse(risk_class not in prof.classes, "store.class.bad", cls=risk_class, classes=", ".join(prof.classes))
    if (p := _where(org, project)[2]).get("archived"):
        raise Refused("store.project.archived", org=org, project=project, at=p["archived"])
    setup_repo(repo := _where(org, project)[1])
    base, reg = git.git("symbolic-ref", "--short", "HEAD", cwd=repo), yamlio.read(repo / "works.yaml", []) or []
    n = 1 + max((int(x["code"][-2:]) for x in reg if x["code"].startswith(f"{org}-{project}-")), default=0)
    code, now, gates = f"{org}-{project}-{n:02d}", clock.now(), list(prof.classes[risk_class])
    yamlio.write(repo / "works.yaml", [*reg, {"code": code, "title": title, "project": project,
                                              "risk_class": risk_class, "opened_at": now}])
    git.commit(repo, git.message(t("store.new.code_title", code=code), None, "project_engineer"), ["works.yaml"], team)
    git.git("worktree", "add", "-q", "-b", f"{code}/main", str(tree(code)), base, cwd=repo)
    d = tree(code) / p.get("folder", project.lower()) / code
    doc = {"kind": "work", "schema_version": "1.0", "code": code, "title": title, "org": org, "project": project,
           "work_type": work_type, "risk_class": risk_class, "purpose": purpose, "done_criterion": done_criterion,
           "process": {"profile": prof.ref, "gates": gates, "stage": gates[0], "gate_status": {
               g: {"status": "in_progress", "started_at": now} if g == gates[0] else {"status": "pending"}
               for g in gates}},
           "packages": [{"id": s.id, "version": s.version} for s in registry().packages if s.id != "core"],
           "profiles": profiles, "branches": {"main": f"{code}/main", "work": [f"{code}/work/{topic}"]},
           "opened_at": now}
    yamlio.write(d / "work.yaml", {k: v for k, v in doc.items() if v not in ("", None)})
    for name, data in {**SKELETON, "requirements.yaml": {"kind": "requirement_list", "schema_version": "1.0",
                                                         "work": code, "items": []}}.items():
        yamlio.write(d / name, data)
    for sub in KEEP:
        yamlio.write_text(d / sub / ".gitkeep", "")
    yamlio.write_text(d / ".gitignore", "__pycache__/\n")   # model and calc code leave no bytecode (E-19)
    git.commit(tree(code), git.message(t("store.new.opened_title", code=code, title=title), t(
        "store.new.opened_step", title=title, cls=risk_class), "project_engineer"), [str(d)], team)
    git.git("checkout", "-q", "-b", f"{code}/work/{topic}", cwd=tree(code))
    return code


def _runs():
    return [(p, yamlio.read(p, {})) for p in sorted((state_dir() / "runs").glob("run-*.json"))]


def active() -> list[str]:
    """Works with an agent session that has not ended (old: tmux sessions)."""
    return sorted({r.get("work") for _, r in _runs() if r.get("status") not in ENDED} - {None})


def open_work(code: str) -> dict:
    """`mekanik work open`: the worktree (made when missing) and the terminal command that opens the session."""
    repo = _where(code)[1]
    if code not in (now := active()) and len(now) >= MAX_ACTIVE:
        raise Refused("store.open.limit", n=MAX_ACTIVE, codes=", ".join(now))
    setup_repo(repo)
    if not tree(code).exists():
        b = git.git("for-each-ref", "--format=%(refname:short)", f"refs/heads/{code}/work/", cwd=repo).split()
        refuse(not b, "store.open.no_branch", code=code)
        git.git("worktree", "add", "-q", str(tree(code)), b[0], cwd=repo)
    path, last = find(code), [r for _, r in _runs() if r.get("work") == code and r.get("terminal_command")]
    # the launcher of the agent adapter (agent.adapter: claude_code, the only one in v1); a known session resumes
    return {"code": code, "path": path,
            "command": last[-1]["terminal_command"] if last else f"cd {shlex.quote(str(path))} && claude"}


def _tmux(*args: str) -> list[str]:
    sock = os.environ.get("MEKANIK_TMUX_SOCKET")   # tests use their own tmux server
    return ["tmux", *(["-L", sock] if sock else []), *args]


def close_work(code: str) -> list[str]:
    """`mekanik work close`: the work's open agent runs end, its tmux session (if any) closes; nothing is deleted."""
    _where(code)
    for p, r in (ended := [x for x in _runs() if x[1].get("work") == code and x[1].get("status") not in ENDED]):
        r.update(status="finished", end_reason="user_stop", ended_at=clock.now())
        yamlio.write_text(p, json.dumps(r, ensure_ascii=False))
    subprocess.run(_tmux("kill-session", "-t", code), capture_output=True)
    return [r.get("id") for _, r in ended]


def attach_work(code: str) -> None:
    """`mekanik work attach`: the work's tmux session (made in the work folder when missing); optional adapter."""
    if subprocess.run(_tmux("has-session", "-t", code), capture_output=True).returncode != 0:
        subprocess.run(_tmux("new-session", "-d", "-s", code, "-c", str(find(code))), check=True)
    if os.environ.get("TMUX"):
        subprocess.run(_tmux("switch-client", "-t", code), check=True)
    else:
        os.execvp("tmux", _tmux("attach-session", "-t", code))


def archived(repo: Path) -> dict[str, dict]:
    """archive.yaml on the organization repo's own branch: code → record."""
    try:
        return {x["code"]: x for x in yamlio.load(git.git("show", "HEAD:archive.yaml", cwd=repo)) or []}
    except GitError:
        return {}


def archive_work(code: str, reason: str) -> dict:
    """`mekanik work archive`: tag <code>-archive, archive.yaml, close, the worktree to <works_root>/archive/."""
    repo, wt = _where(code)[1], tree(code)
    refuse(code in archived(repo), "store.archive.already", code=code)
    refuse(dirty(repo) or (wt.exists() and dirty(wt)), "store.archive.dirty", code=code)
    head = git.head(wt) if wt.exists() else git.git("rev-parse", f"{code}/main", cwd=repo)
    team, tag, dest = load_config().team, f"{code}-archive", load_config().path("works_root") / "archive" / code
    git.git("tag", "-a", tag, head, "-m", t("store.archive.tag", reason=reason), cwd=repo, env=git.identity_env(*team))
    rec = {"code": code, "at": clock.now(), "reason": reason, "last_commit": head, "tag": tag,
           "branch": git.branch(wt) if wt.exists() else f"{code}/main", "folder": str(dest) if wt.exists() else None}
    yamlio.write(repo / "archive.yaml", [*(yamlio.read(repo / "archive.yaml", []) or []), rec])
    git.commit(repo, git.message(t("store.archive.title", code=code), None, "project_engineer"), ["archive.yaml"], team)
    close_work(code)
    if wt.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        git.git("worktree", "move", str(wt), str(dest), cwd=repo)
    return rec
