# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pulse (old nabiz.py) and watcher (old gozcu.py)."""

import json
import os
import subprocess
from datetime import datetime, timedelta
from types import SimpleNamespace

from mekanik.agent import hook, pulse, watch
from mekanik.config import load_config
from mekanik.core.i18n import t


def _age(path, key, minutes):
    """Move a stamp `minutes` into the past (the file's `key` field, or its mtime when key is None)."""
    past = datetime.now().astimezone() - timedelta(minutes=minutes)
    if key:
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc[key] = past.isoformat(timespec="seconds")
        path.write_text(json.dumps(doc), encoding="utf-8")
    else:
        os.utime(path, (past.timestamp(), past.timestamp()))


def test_pulse_beat_touch_and_log(state):
    """new: Ek B §14 madde 3 — beat starts and stops, a step refreshes only a working pulse, the log is capped"""
    v = pulse.beat("TST-SYN-01", "G1 kapısı hazırlanıyor")
    assert v["status"] == "working" and v["started_at"] == v["at"] and v["role"] == "project_engineer"
    pulse.touch("TST-SYN-01", "adım", "design_engineer")
    assert pulse.read("TST-SYN-01")["log"][0] | {"at": None} == {"at": None, "role": "design_engineer",
                                                                  "status": "step", "text": "adım"}
    stopped = pulse.beat("TST-SYN-01", "K-02 kararını bekliyor", status="stopped")
    _age(state / "pulse" / "TST-SYN-01.json", "at", 5)
    pulse.touch("TST-SYN-01", "adım", "technician")
    after = pulse.read("TST-SYN-01")
    assert after["status"] == "stopped" and after["at"] < stopped["at"] and after["doing"] == "K-02 kararını bekliyor"
    for i in range(pulse.LOG_LENGTH + 5):
        pulse.touch("TST-SYN-01", f"adım {i}", "technician")
    assert len(pulse.read("TST-SYN-01")["log"]) == pulse.LOG_LENGTH
    pulse.touch("TST-SYN-02", "adım", "technician")
    assert pulse.read("TST-SYN-02") is None, "touch does not start a pulse"


def test_liveness_thresholds(state, work):
    """new: Ek B §14 madde 3 — working → quiet after FRESH_MIN → stopped after SILENT_MIN; newest source wins"""
    path = state / "pulse" / "TST-SYN-01.json"
    assert pulse.liveness("TST-SYN-01")["status"] == "stopped"
    pulse.beat("TST-SYN-01", "çiziyor")
    assert pulse.liveness("TST-SYN-01")["status"] == "working"
    _age(path, "at", pulse.FRESH_MIN)
    v = pulse.liveness("TST-SYN-01")
    assert (v["status"], v["auto"], v["minutes"]) == ("quiet", True, pulse.FRESH_MIN)
    _age(path, "at", pulse.SILENT_MIN)
    assert pulse.liveness("TST-SYN-01")["status"] == "stopped"
    hook.handle("Notification", {"session_id": "s", "cwd": str(work), "notification_type": "permission_prompt"})
    v = pulse.liveness("TST-SYN-01")
    assert (v["status"], v["reason"], v["source"]) == ("waiting", "permission", "session")
    hook.handle("SessionEnd", {"session_id": "s", "cwd": str(work)})
    (run,) = (state / "runs").glob("*.json")
    _age(run, None, pulse.FRESH_MIN + 1)
    assert pulse.liveness("TST-SYN-01")["source"] == "pulse", "a long-closed session is not a candidate"


def _git(repo, *args, who=("mekanik-ekip", "ekip@mekanik.local")):
    env = {**os.environ, "GIT_AUTHOR_NAME": who[0], "GIT_AUTHOR_EMAIL": who[1], "GIT_COMMITTER_NAME": who[0],
           "GIT_COMMITTER_EMAIL": who[1]}
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def _commit(repo, path, title, who):
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(title, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", title, who=who)


def test_watch_reports_chief_commits_only(tmp_path):
    """new: Ek B §14 madde 2 — a chief-identity commit gives one line; log commits and team commits do not;
    archive repos and organizations that forbid data transfer are not watched"""
    cfg = load_config()
    chief, team = cfg.chief, cfg.team
    repo, archived = tmp_path / "tst", tmp_path / "archive" / "old"
    for r in (repo, archived):
        r.mkdir(parents=True)
        _git(r, "init", "-q")
        _commit(r, "works.yaml", "başlangıç", team)
    orgs = SimpleNamespace(lists={"organizations": [  # a stand-in: the cached workshop config is not touched
        {"code": "TST", "repo": str(repo), "data_transfer": {"model_provider_allowed": True}},
        {"code": "OLD", "repo": str(archived), "data_transfer": {"model_provider_allowed": True}},
        {"code": "NOP", "repo": str(repo), "data_transfer": {"model_provider_allowed": False}}]})
    assert watch.org_repos(orgs) == [repo]
    seen, author = set(), "{} <{}>".format(*chief)
    watch.new_events([repo], seen, author)
    _commit(repo, "sentetik/TST-SYN-01/approvals.yaml", "O-G1 onaylandı", chief)
    _commit(repo, "sentetik/TST-SYN-01/records/log/2026-11-06.md", "Günlük: O-G1 onaylandı", chief)
    _commit(repo, "sentetik/TST-SYN-01/params.yaml", "adım", team)
    _commit(repo, "sentetik/TST-SYN-01/approvals.yaml.bak", "yorum", (chief[0], "baska@example.org"))
    (line,) = watch.new_events([repo], seen, author)
    sha, at = subprocess.run(["git", "log", "-1", "--format=%H %ad", "--date=format:%H:%M", "--", "sentetik/TST-SYN-01/"
                              "approvals.yaml"], cwd=repo, capture_output=True, text=True, check=True).stdout.split()
    assert line == t("agent.watch.event", work="TST-SYN-01", time=at, title="O-G1 onaylandı", sha=sha[:7])
    assert watch.new_events([repo], seen, author) == [], "a commit is reported once"


def test_watch_exits_silently_outside_works(tmp_path, capsys):
    """new: architecture §5.4 — the user-scope monitor starts in every session; outside the works it says nothing"""
    assert watch.watch(cwd=tmp_path, interval=0, rounds=1) == 0
    assert capsys.readouterr().out == ""


def test_watch_announces_itself_in_a_work(work, capsys):
    """new: old gozcu.calistir — the first line names the repo count and the chief engineer"""
    assert watch.watch(cwd=work, interval=0, rounds=1) == 0
    cfg = load_config()
    assert capsys.readouterr().out.splitlines() == [t("agent.watch.started", repos=len(watch.org_repos(cfg)),
                                                      who=cfg.chief[0])]
