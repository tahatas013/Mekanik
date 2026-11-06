# SPDX-License-Identifier: AGPL-3.0-or-later
"""The panel's reads (old veriler.py): the repository is the truth (tags, trailers, records, events.jsonl); git reads
run without optional locks (E-20, `GIT_OPTIONAL_LOCKS=0` in the panel process). Check results and cards are of the
committed HEAD, cached by HEAD and the process signature: a dirty folder (the agent at work) is shown as committed and
not re-evaluated on every request. Another branch of the work is read in a helper worktree under the cache
(`<cache>/branches/<code>/<branch>`); the agent's worktree is never touched."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime
from functools import cache as once
from pathlib import Path

from mekanik.agent import hook, inbox, pulse
from mekanik.config import config_dir, load_config, state_dir
from mekanik.core import data, i18n, yamlio
from mekanik.core.checks.result import Result
from mekanik.core.errors import GitError, MekanikError
from mekanik.core.evidence import cache, calc
from mekanik.core.i18n import t
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, gates
from mekanik.core.process.step import evaluate
from mekanik.core.report import stream
from mekanik.core.store import git, works
from mekanik.plugins import registry

from . import model

DOWNLOADS = ("out", "records", "inputs")   # architecture §5.6: downloads only from these folders of the work
IMAGES = {".svg", ".png", ".jpg", ".jpeg", ".md", ".step", ".stl"}
OPEN, RECENT = ("open", "awaiting_reply"), 12   # source: assumption — old veriler: steps shown on the status screen
_lock = threading.RLock()


class Unknown(LookupError):
    """No such work, file or commit here (404)."""


def root_of(code: str, branch: str | None = None) -> Path:
    """The work folder; `branch` only a work or decision branch of this work (old calisma_dizini; e2e 8)."""
    if not works.CODE.match(code or ""):
        raise Unknown(code)
    try:
        d = works.find(code)
    except MekanikError as e:
        raise Unknown(code) from e
    if not branch or git.branch(d) == branch:
        return d
    if not re.fullmatch(rf"{re.escape(code)}/(work|decision)/[A-Za-z0-9._-]+", branch) or not git.branch_exists(
            d, branch):
        raise Refused("panel.branch.not_work", branch=branch)
    with _lock:
        if not (wt := cache.root() / "branches" / code / branch.replace("/", "__")).exists():
            wt.parent.mkdir(parents=True, exist_ok=True)
            git.git("worktree", "add", "-q", str(wt), branch, cwd=d)
    return wt / d.relative_to(works.tree(code))


@once
def _code_signature() -> str:
    h = hashlib.sha1()
    for top in (Path(data.__file__).parent, data.stdlib()):
        for f in sorted(p for p in top.rglob("*") if p.suffix in (".py", ".yaml") and "__pycache__" not in p.parts):
            h.update(f.read_bytes())
    h.update(" ".join(f"{p.id}={p.version}" for p in registry().packages).encode())
    return h.hexdigest()[:16]


def signature() -> str:
    """What check results depend on besides the commit: core code, stdlib, packages, workshop config, language."""
    stamp = max((f.stat().st_mtime for f in config_dir().rglob("*.yaml")), default=0)
    return f"{_code_signature()}-{int(stamp * 1000):x}-{i18n.lang()}"


def state(root: Path) -> dict:
    """{head, summary, results, cards} of the committed HEAD (old _ozet_kontrol_onbellekli)."""
    head = git.head(root)
    if (path := cache.root() / head / f"panel-{signature()}.json").exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    with model.at_commit(root, head) as d:
        _, _, results, cards = evaluate(d)
    st = {"head": head, "summary": {s: sum(r.status == s for r in results) for s in ("block", "warn", "pass")},
          "results": [r.as_dict() for r in results], "cards": cards}
    yamlio.write_text(cache.entry(head) / path.name, json.dumps(st, ensure_ascii=False, default=str))
    return st


def results_of(st: dict) -> list[Result]:
    return [Result(**{k: v for k, v in r.items() if k != "reason"}) for r in st["results"]]


def color(st: dict) -> str:
    """red: a block; yellow: an open hold or a warning; green (old _renk)."""
    if st["summary"]["block"]:
        return "red"
    return "yellow" if st["summary"]["warn"] or any(c.get("status") == "open" and c.get("level") == "hold"
                                                    for c in st["cards"]) else "green"


def _counts(root: Path, st: dict) -> dict:
    kinds = [r.get("type", "calculation") for r in calc.recorded(root).values()]
    op = [c for c in st["cards"] if c.get("status") == "open"]
    return {"color": color(st), "open_cards": len(op), "hold": sum(c.get("level") == "hold" for c in op),
            "calcs": kinds.count("calculation"), "analyses": kinds.count("analysis")}


def tree() -> list[dict]:
    """Organization → project → work (old agac); archived works and projects are left out, nothing is deleted."""
    out = []
    for o in load_config().lists["organizations"]:
        repo = Path(o["repo"]).expanduser()
        reg, gone = yamlio.read(repo / "works.yaml", []) or [], works.archived(repo) if (repo / ".git").exists() else {}
        projects = {p["code"]: {"code": p["code"], "name": p.get("name", p["code"]), "works": []}
                    for p in o.get("projects") or [] if not p.get("archived")}
        for w in (w for w in reg if w["code"] not in gone and w["project"] in projects):
            item = {k: w.get(k) for k in ("code", "title", "risk_class", "opened_at")}
            try:
                root = works.find(w["code"])
                view, st = load_work(root), state(root)
                item.update(stage=gates.stage(root, view), work_type=view.doc.get("work_type"), **_counts(root, st))
            except (MekanikError, GitError) as e:
                item["error"] = str(e)[:200]
            projects[w["project"]]["works"].append(item)
        out.append({"code": o["code"], "name": o["name"], "data_allowed": hook.org_allowed(o["code"]),
                    "projects": list(projects.values())})
    return out


def tabs() -> dict:
    """Open works (an agent session that has not ended; at most works.MAX_ACTIVE) and the session records."""
    runs = [{**r, "updated_at": at} for at, r in hook.runs()]
    tabs = []
    for code in works.active():
        try:
            view = load_work(works.find(code))
            tabs.append({"code": code, "title": view.title, "liveness": pulse.liveness(code)})
        except MekanikError:
            continue
    return {"tabs": tabs, "max": works.MAX_ACTIVE, "chief": load_config().chief[0], "runs": runs[-20:]}


def work(code: str, branch: str | None = None) -> dict:
    root = root_of(code, branch)
    view, st = load_work(root), state(root)
    return {"code": code, "title": view.title, "org": code[:3], "data_allowed": hook.org_allowed(code[:3]),
            **{k: view.doc.get(k) for k in ("purpose", "done_criterion", "work_type", "profiles", "next_step",
                                            "inputs", "risk_class", "opened_at")},
            "stage": gates.stage(root, view), "gates": view.gates, "passed": gates.passed(root, code),
            "branch": git.branch(root), "commit": st["head"], "summary": st["summary"], **_counts(root, st),
            "dirty": bool(works.dirty(root)), "branches": _branches(root, code)}


def _branches(root: Path, code: str) -> list[str]:
    return git.git("for-each-ref", "--format=%(refname:short)", f"refs/heads/{code}/", cwd=root).split()


def _tags(root: Path, code: str) -> dict[str, dict]:
    """Gate tag → {commit, tagger, at} (annotated tags of <code>-G*)."""
    out = {}
    for line in git.git("for-each-ref", "--format=%(refname:short)\x1f%(*objectname)\x1f%(taggername)\x1f"
                        "%(taggerdate:iso-strict)", f"refs/tags/{code}-G*", cwd=root).splitlines():
        name, sha, who, at = line.split("\x1f")
        out[name] = {"commit": sha, "by": who, "at": at}
    return out


def stages(code: str) -> dict:
    """Gates with their state, time, approver, tag, model commit, steps and decisions in range (old asamalar)."""
    root = root_of(code)
    view, st = load_work(root), state(root)
    passed, here, tags = gates.passed(root, code), gates.stage(root, view), _tags(root, code)
    steps = [e for e in stream.read(root) if e.get("type") == "step"]
    out = []
    for g in view.profile.stages:
        s = (view.doc["process"]["gate_status"] or {}).get(g) or {}
        tag = tags.get(s.get("tag") or "")
        state_ = "done" if g in passed else "in_progress" if g == here else "pending" if g in view.gates \
            else "not_applicable"
        start, end = s.get("started_at"), s.get("finished_at") if state_ == "done" else None
        made = git.git("rev-parse", f"{tag['commit']}^2", cwd=root) if tag else st["head"] if state_ == \
            "in_progress" else None
        check = yamlio.read(cache.root() / made / "check.json") if made and made != st["head"] else None
        inside = (lambda at: bool(at) and (not start or at >= start) and (not end or at <= end)) \
            if state_ in ("done", "in_progress") else (lambda at: False)
        out.append({"gate": g, "status": state_, "planned": g in view.gates, "started_at": start, "finished_at": end,
                    "tag": s.get("tag") if tag else None, "approver": tag and tag["by"],
                    "commit": tag and tag["commit"],
                    "model_commit": made, "summary": (check or {}).get("summary") or (
                        st["summary"] if state_ == "in_progress" else None),
                    "steps": [{k: e.get(k) for k in ("at", "role", "line", "commit")} for e in steps
                              if inside(e["at"])],
                    "decisions": [{k: d.get(k) for k in ("id", "title", "status", "chosen", "mode")} | {
                        "options": [{k: o.get(k) for k in ("id", "title", "status")} for o in d.get("options") or []]}
                                  for d in view.decisions if inside(d.get("opened_at"))]})
    return {"code": code, "stage": here, "stages": out, "activity": [
        {k: e.get(k) for k in ("at", "role", "line", "commit")} for e in steps[::-1][:RECENT]]}


def _waiting(st: dict) -> tuple[list[dict], list[dict]]:
    """(cards waiting for the chief, cards whose chief note waits for the team); model notes are the team's."""
    chief = [{"id": c["id"], "question": c.get("question") or c.get("title"), "type": c.get("type"),
              "level": c.get("level")} for c in st["cards"] if c.get("status") == "open"
             and c.get("type") != "model_note"]
    team = [{"id": c["id"], "question": c.get("question") or c.get("title"), "comment": next(
        (x["text"] for x in c.get("thread") or [] if x.get("kind") != "reply"), "")} for c in st["cards"]
            if c.get("status") == "awaiting_reply" or (c.get("type") == "model_note" and c.get("status") == "open")]
    return chief, team


def _say(key: str, kind: str, **data) -> dict:
    return {"kind": kind, "key": key, "data": data, "text": t(key, **data)}


def ball(live: dict, chief: list, team: list) -> dict:
    """Who has the ball (old top_kimde): the session waiting in the terminal, the team at work, the chief, nobody."""
    if live["status"] == "waiting":
        return {"who": "chief_engineer", **_say(f"panel.ball.waiting_{live.get('reason') or 'input'}", "chief")}
    if live["status"] in ("working", "quiet"):
        return {"who": live.get("role") or "project_engineer", **_say("panel.ball.working", "team",
                                                                       doing=live.get("doing") or "—")}
    if chief:
        return {"who": "chief_engineer", **_say("panel.ball.cards", "chief", n=len(chief))}
    return {"who": None, **_say("panel.ball.replies" if team else "panel.ball.idle", "idle", n=len(team))}


def liveness(code: str) -> dict:
    """The top bar's light reading (asked every few seconds; old canlilik_ozeti)."""
    st, live = state(root_of(code)), pulse.liveness(code)
    chief, team = _waiting(st)
    return {"code": code, "liveness": live, "ball": ball(live, chief, team), "chief": len(chief), "team": len(team),
            "stop": hook.stop_flag(code).exists(), "lock": inbox.holder(code),
            "inbox": sum(x["state"] == "pending" for x in inbox.items(code))}


def status(code: str) -> dict:
    """The status screen (old durum_ekrani): who waits for whom, the session, the last move, the next job."""
    root = root_of(code)
    view, st, light = load_work(root), state(root), liveness(code)
    chief, team = _waiting(st)
    live, rows, changed = light["liveness"], [], works.dirty(root).splitlines()
    if live["status"] == "waiting":
        rows.append(_say(f"panel.status.waiting_{live.get('reason') or 'input'}", "chief"))
    elif live["status"] in ("working", "quiet"):
        rows.append(_say("panel.status.working", "team", doing=live.get("doing") or "—", minutes=live["minutes"]))
    if changed and live["status"] not in ("working", "quiet"):
        rows.append(_say("panel.status.dirty", "team", files="; ".join(x.strip() for x in changed[:3])))
    if chief:
        rows.append(_say("panel.status.chief", "chief", n=len(chief), ids=", ".join(c["id"] for c in chief)))
    if team:
        rows.append(_say("panel.status.team", "team", n=len(team), ids=", ".join(c["id"] for c in team)))
    if live["status"] == "stopped" and not changed:
        rows.append(_say("panel.status.stopped", "idle", minutes="—" if live["minutes"] is None else live["minutes"]))
    last = git.git("log", "-1", "--format=%aI%x1f%an%x1f%s", cwd=root).split("\x1f")
    run = next((r for _, r in reversed(hook.runs(code))), None)
    return {**light, "title": view.title, "purpose": view.doc.get("purpose"), "stage": gates.stage(root, view),
            "gates": [{"gate": g, "status": "done" if g in gates.passed(root, code) else "in_progress" if g ==
                       gates.stage(root, view) else "pending"} for g in view.gates],
            "summary": st["summary"], "rows": rows, "chief_cards": chief, "team_cards": team, "run": run,
            "last": {"at": last[0], "who": last[1], "title": last[2]} if last[0] else None,
            "steps": stages(code)["activity"], "next": view.doc.get("next_step"), "dirty": changed[:3]}


def cards(code: str, branch: str | None = None, commit: str | None = None) -> dict:
    """Cards, check results, params, package records, approvals and decisions (old kartlar); `commit` shows a past
    version, read in a temporary worktree."""
    root = root_of(code, branch)
    sha = model.resolve(root, commit)
    if sha != git.head(root):
        with model.at_commit(root, sha) as d:
            _, _, res, made = evaluate(d)
            view, st = load_work(d), {"head": sha, "results": [r.as_dict() for r in res], "cards": made}
            st["summary"] = {s: sum(r.status == s for r in res) for s in ("block", "warn", "pass")}
    else:
        view, st = load_work(root), state(root)
    return {"code": code, "branch": git.branch(root), "commit": sha, "past": sha != git.head(root), **st,
            "params": yamlio.read(view.root / "params.yaml", {}) or {}, "records": json.loads(json.dumps(
                view.ext, default=str)), "approvals": view.approvals[::-1], "decisions": view.decisions,
            "requirements": gates.requirement_table(view)}


def all_cards() -> list[dict]:
    """Open cards of every work (the cards screen's "all works" filter)."""
    out = []
    for o in tree():
        for p in o["projects"]:
            for w in (w for w in p["works"] if "error" not in w):
                out += [{**c, "work_title": w["title"]} for c in state(works.find(w["code"]))["cards"]
                        if c.get("status") == "open"]
    return out


def calcs(code: str, branch: str | None = None) -> dict:
    """Recorded calculation results (records/calcs/*.json, made at a step) and calc files without a record."""
    root = root_of(code, branch)
    rec = calc.recorded(root)
    return {"code": code, "commit": git.head(root), "calcs": list(rec.values()),
            "unrecorded": sorted({p.stem for p in calc.files(root)} - set(rec))}


def files(code: str) -> dict:
    """Downloadable folders out/<subfolder>, records/, inputs/: size and SHA-256 of every file; a release folder's
    report.md hashes are compared (changed files are marked; old dosyalar)."""
    root, folders = root_of(code), []
    for top in DOWNLOADS:
        if not (base := root / top).is_dir():
            continue
        for k in sorted((x for x in base.iterdir() if x.is_dir()), reverse=True) if top == "out" else [base]:
            report = (k / "report.md").read_text(encoding="utf-8") if (k / "report.md").is_file() else ""
            want = dict(re.findall(r"\| (\S+) \| `([0-9a-f]{64})` \|", report))
            rows = []
            for f in sorted(x for x in k.rglob("*") if x.is_file() and not x.name.startswith(".")):
                h, rel = hashlib.sha256(f.read_bytes()).hexdigest(), str(f.relative_to(k))
                rows.append({"path": str(f.relative_to(root)), "name": rel, "size": f.stat().st_size, "sha256": h,
                             "matches": want[rel] == h if rel in want else None})
            folders.append({"path": str(k.relative_to(root)), "kind": "release" if top == "out" else top,
                            "files": rows})
    return {"code": code, "folders": folders}


def _inside(root: Path, rel: str, tops: tuple[str, ...] | None) -> Path:
    """`rel` under the work folder (and under one of `tops`), an existing file or folder; else Unknown (e2e 16)."""
    base, target = root.resolve(), (root / rel).resolve()
    ok = (base in target.parents) if tops is None else any(
        target == (base / u) or (base / u) in target.parents for u in tops)
    if not ok or not target.exists():
        raise Unknown(rel)
    return target


def download(code: str, rel: str) -> Path:
    return _inside(root_of(code), rel, DOWNLOADS)


def image(code: str, rel: str, branch: str | None = None) -> Path:
    if not (p := _inside(root_of(code, branch), rel, None)).is_file() or p.suffix.lower() not in IMAGES:
        raise Unknown(rel)
    return p


def step_detail(code: str, sha: str) -> dict:
    """What one step did (old adim_ayrintisi): text, changed params (before → after, source), files, code diff,
    calc results before → after, check summary."""
    root = root_of(code)
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        raise Unknown(sha)
    try:
        sha = model.resolve(root, sha)
    except GitError as e:
        raise Unknown(sha) from e
    parents, who, at, msg = git.git("log", "-1", "--format=%P%x1f%an%x1f%aI%x1f%B", sha, cwd=root).split("\x1f", 3)
    files_ = [dict(zip(("added", "removed", "path"), x.split("\t", 2))) for x in git.git(
        "show", "--numstat", "--format=", "--relative", sha, "--", ".", cwd=root).splitlines()]
    prev = parents.split()[0] if parents.split() else None

    def show(ref, rel, default):
        try:
            return yamlio.load(git.git("show", f"{ref}:./{rel}", cwd=root)) if ref else default
        except (GitError, MekanikError):
            return default

    before, after = show(prev, "params.yaml", {}) or {}, show(sha, "params.yaml", {}) or {}
    params = [{"name": n, "before": before.get(n), "after": after.get(n)} for n in dict.fromkeys([*after, *before])
              if before.get(n) != after.get(n)]
    diffs = [{"path": f["path"], "lines": git.git("show", "--format=", "--relative", "-U2", sha, "--", f["path"],
                                                  cwd=root).splitlines()[4:404]}
             for f in files_ if f["path"].endswith(".py") and f["added"] != "-"]
    calcs_ = []
    for f in (f for f in files_ if f["path"].startswith(calc.FOLDER + "/")):
        old, new = ({r["name"]: r for r in (show(ref, f["path"], {}) or {}).get("results") or []}
                    for ref in (prev, sha))
        if changed := [{"name": n, "unit": r.get("unit"), "before": (old.get(n) or {}).get("value"),
                        "after": r.get("value"), "status": r.get("status")} for n, r in new.items()
                       if (old.get(n) or {}).get("value") != r.get("value")]:
            calcs_.append({"path": f["path"], "results": changed})
    ev = next((e for e in stream.read(root) if (e.get("commit") or "x") in sha), None)
    return {"commit": sha, "parents": parents.split(), "author": who, "at": at, "title": msg.strip().splitlines()[0],
            "text": msg.strip(), "trailers": git.trailers(msg), "files": files_, "params": params, "code_diff": diffs,
            "calcs": calcs_, "summary": (yamlio.read(cache.root() / sha / "check.json") or {}).get("summary") or (
                ev or {}).get("check_summary"), "first": not parents.split()}


def branches(code: str) -> dict:
    """Branch map (old dal_haritasi): main, work and decision branches, each visible commit (with a Step trailer)
    owned by one branch (main first, then work, then decision branches), its visible parents for the curves."""
    root = root_of(code)
    names, view, main = _branches(root, code), load_work(root), f"{code}/main"
    state_of = {o.get("branch"): o.get("status") for d in view.decisions for o in d.get("options") or [] if
                o.get("branch")}
    owner: dict[str, str] = {}
    for b in sorted(names, key=lambda x: (x != main, "/decision/" in x, x)):
        for s in git.git("rev-list", "--first-parent", b, cwd=root).split():
            owner.setdefault(s, b)
    log, tags = git.git("log", "--format=%H%x1f%P%x1f%an%x1f%aI%x1f%B%x1e", *names, cwd=root), {}
    for line in git.git("for-each-ref", "--format=%(refname:short) %(*objectname) %(objectname)",
                        f"refs/tags/{code}-*", cwd=root).splitlines():
        name, *sha = line.split()
        tags.setdefault(sha[0] if len(sha) == 2 else sha[-1], []).append(name)
    every = {}
    for rec in (r.strip("\n") for r in log.split("\x1e") if r.strip()):
        sha, parents, who, at, body = rec.split("\x1f", 4)
        tr = git.trailers(body)
        every[sha] = {"sha": sha, "parents": parents.split(), "author": who, "at": at, "title": body.strip(
            ).splitlines()[0], "step": tr.get("Step"), "role": tr.get("Role"), "cards": tr.get("Card", []),
            "branch": owner.get(sha), "tags": tags.get(sha, [])}

    def seen(s):
        while s and s in every and not every[s]["step"]:
            s = (every[s]["parents"] or [None])[0]
        return s if s in every else None

    shown = [c | {"visible_parents": [seen(p) for p in c["parents"]]} for c in every.values() if c["step"]]
    here, info = git.branch(root), []
    for b in names:
        kind = "main" if b == main else "decision" if "/decision/" in b else "work"
        try:
            merged = kind == "work" and not git.git("merge-base", "--is-ancestor", b, main, cwd=root)
        except GitError:
            merged = False
        info.append({"name": b, "short": b[len(code) + 1:], "kind": kind, "head": git.git("rev-parse", b, cwd=root),
                     "status": kind if kind == "main" else state_of.get(b, "open") if kind == "decision" else
                     "merged" if merged else "open", "current": b == here,
                     "steps": sum(c["branch"] == b for c in shown)})
    return {"branches": info, "folded": len(every) - len(shown), "commits": shown}


def _read_marks() -> Path:
    return state_dir() / "panel-read.json"


def design_file(code: str, branch: str | None = None) -> dict:
    """Design file (old tasarim_dosyasi): what came since the chief last read it (stream lines), what was found, what
    waits for him, the checks by group; the log itself (records/log/*.md) is listed for reading."""
    root = root_of(code, branch)
    st, last = state(root), (yamlio.read(_read_marks(), {}) or {}).get(code)
    new = [e for e in stream.read(root) if not last or e["at"] > last]
    groups: dict[str, dict] = {}
    for r in st["results"]:
        g = groups.setdefault(r["check"], {"check": r["check"], "status": "pass", "open": 0, "total": 0})
        g["total"], g["open"] = g["total"] + 1, g["open"] + (r["status"] != "pass")
        g["status"] = min(g["status"], r["status"], key=("block", "warn", "pass").index)
    return {"code": code, "last_read": last, "new": len(new), "events": new[::-1][:50],
            "done": [e["line"] for e in new if e.get("role") != "chief_engineer"][-6:],
            "found": [r["reason"] for r in st["results"] if r["status"] != "pass"][:6],
            "waiting": [f"{c['id']} · {c.get('title', '')}" for c in st["cards"] if c.get("status") == "open"][:8],
            "checks": sorted(groups.values(), key=lambda g: ("block", "warn", "pass").index(g["status"])),
            "log": sorted(p.name for p in (root / "records" / "log").glob("*.md"))[::-1], "summary": st["summary"]}


def read_mark(code: str) -> str:
    root_of(code)
    marks, at = yamlio.read(_read_marks(), {}) or {}, datetime.now().astimezone().isoformat(timespec="seconds")
    yamlio.write_text(_read_marks(), json.dumps(marks | {code: at}))
    return at


def day_summary(code: str, day: str | None = None) -> dict:
    """The day-end summary draft (report.summary.build) from the cached state (no model is built)."""
    from mekanik.core.report import summary

    root = root_of(code)
    st = state(root)
    return {"code": code, "day": day, "sections": summary.build(root, day, (load_work(root), None, results_of(st),
                                                                             st["cards"]))}


def intake(code: str) -> dict:
    """Intake screen: work type, the question plan (now / stage end), findings, the understanding summary."""
    from mekanik.core.intake import engine, summary, trees

    root = root_of(code)
    view = load_work(root)
    return {"code": code, "work_type": view.doc.get("work_type"), "types": json.loads(json.dumps(
        trees.work_types(), default=str)), "plan": json.loads(json.dumps(engine.plan(view), default=str)),
        "answers": engine.records(root), "summary": summary.read(root), "summary_status": summary.status(view)}


def stdmap(code: str) -> dict:
    from mekanik.core import stdmap as sm

    rows = sm.rows(root_of(code))
    return {"code": code, "items": rows, "counts": sm.counts(rows)}


def policy(code: str) -> dict:
    """The stage's measures (questions asked, provisional decisions made and reverted, time to answer; §8.2)."""
    from mekanik.core.policy import metrics

    root = root_of(code)
    view, st = load_work(root), state(root)
    m = metrics.stage(view, gates.stage(root, view), st["cards"])
    return {"code": code, "metrics": m, "line": metrics.line(m)}


def new_work_options() -> dict:
    """What the project screen offers: organizations and projects, risk classes, installed work types."""
    from mekanik.core.intake import trees
    from mekanik.core.process.profile import load_profile

    return {"organizations": [{"code": o["code"], "name": o["name"], "data_allowed": hook.org_allowed(o["code"]),
                               "projects": [{"code": p["code"], "name": p.get("name")} for p in o.get("projects") or []
                                            if not p.get("archived")]} for o in load_config().lists["organizations"]],
            "classes": list(load_profile().classes), "work_types": json.loads(json.dumps(
                trees.work_types(), default=str)), "packages": [p.id for p in registry().packages]}
