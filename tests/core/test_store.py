# SPDX-License-Identifier: AGPL-3.0-or-later
"""Store: works.yaml, new/open/close/archive, the log (old test_akis and new). Also the shop fixture of the process
tests (tests/core/test_process*.py, tests/flow): a temporary organization repo, a copy of the test workshop config
pointing into tmp_path, GPG keys for the chief's signed approvals (no ssh-keygen in this container)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from mekanik.core import clock, quality, yamlio
from mekanik.core.process import Refused
from mekanik.core.store import git, log, works
from mekanik.plugins import reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONFIG = ROOT / "tests" / "fixtures" / "config"
CHIEF = ("Test Mühendis", "test@example.org")
TEAM = ("mekanik-ekip", "ekip@mekanik.local")
REQUIREMENTS = [{"id": "R-01", "text": "Blok yazıcıya sığar", "kind": "mandatory", "origin": {"type": "chief_engineer"},
                 "criterion": {"measure": "block_edge", "operator": "<=", "target": {
                     "value": 256.0, "unit": "mm", "source": "decision", "decided_by": "chief_engineer"}},
                 "verification": {"method": "check"}, "status": "approved"}]
PARAMS = {"blok_en": {"value": 20.0, "unit": "mm", "source": "decision"},
          "blok_kalinlik": {"value": 5.0, "unit": "mm", "source": "decision"}}
RISK_C = [{"question_id": q, "answer": a} for q, a in (("harm", False), ("cost", False), ("regulation", False),
                                                       ("variant", True))]


@pytest.fixture(autouse=True)
def _core_only():
    """tests/core run with the core's own checks only (no package, no model; OCCT-free)."""
    from mekanik.core.builtin import SPEC

    set_registry([SPEC])
    yield
    reset_registry()


def _run(*args, **kw):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kw).stdout


@pytest.fixture(scope="session")
def gpg_keys(tmp_path_factory):
    if not shutil.which("gpg"):
        pytest.skip("gpg not installed")
    home = tmp_path_factory.mktemp("gnupg")
    home.chmod(0o700)
    env, keys = {**os.environ, "GNUPGHOME": str(home)}, {}
    for who, uid in (("chief", f"{CHIEF[0]} <{CHIEF[1]}>"), ("other", "Başka <baska@example.org>")):
        _run("gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key", uid, "ed25519",
             "sign", "never", env=env)
        out = _run("gpg", "--with-colons", "--list-secret-keys", uid.split()[-1], env=env)
        keys[who] = next(x.split(":")[9] for x in out.splitlines() if x.startswith("fpr:"))
    yield home, keys
    subprocess.run(["gpgconf", "--kill", "gpg-agent"], capture_output=True, env=env)


@pytest.fixture
def shop(tmp_path, monkeypatch, gpg_keys):
    """Organization repo TST (project SYN) in tmp_path/works/tst; config copy with works_root and the chief's key."""
    home, keys = gpg_keys
    for k, v in {"GNUPGHOME": home, "GIT_CONFIG_GLOBAL": tmp_path / "gitconfig", "GIT_CONFIG_NOSYSTEM": "1",
                 "XDG_STATE_HOME": tmp_path / "state", "XDG_DATA_HOME": tmp_path / "data",
                 "XDG_CACHE_HOME": tmp_path / "cache", "MEKANIK_TMUX_SOCKET": f"mekanik-test-{tmp_path.name}"}.items():
        monkeypatch.setenv(k, str(v))
    (tmp_path / "gitconfig").write_text("")
    cfg, repo = tmp_path / "config", tmp_path / "works" / "tst"
    shutil.copytree(FIXTURE_CONFIG, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["paths"]["works_root"] = str(tmp_path / "works")
    doc["organizations"][0]["repo"] = str(repo)
    doc["identities"]["chief_signing_key"] = keys["chief"]
    yamlio.write(cfg / "config.yaml", doc)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    repo.mkdir(parents=True)
    git.git("init", "-q", "-b", "main", cwd=repo)
    git.git("config", "user.signingkey", keys["chief"], cwd=repo)
    git.commit(repo, git.message("ilk", None, "project_engineer"), identity=TEAM, allow_empty=True)
    yield SimpleNamespace(root=tmp_path, repo=repo, keys=keys, config=cfg)
    subprocess.run(works._tmux("kill-server"), capture_output=True)


def prepare(d: Path, risk=RISK_C, params=PARAMS, model: str | None = None) -> None:
    """Old _hazirla: risk answers, one requirement, sourced params, optional model."""
    doc = yamlio.read(d / "work.yaml")
    doc["risk_answers"] = risk
    yamlio.write(d / "work.yaml", doc)
    yamlio.write(d / "requirements.yaml", {**yamlio.read(d / "requirements.yaml"), "items": REQUIREMENTS})
    yamlio.write(d / "params.yaml", params)
    if model is not None:
        (d / "model" / "model.py").write_text(model)


def review(d: Path, text: str = "Bulgu yok.") -> None:
    """The quality engineer's report on HEAD: its output caught as the plugin's SubagentStop hook does (KF1-16)."""
    quality.prompt(d, "sınama")
    quality.capture(yamlio.read(d / "work.yaml")["code"], text)
    quality.record(d, "sınama", text)


def new(cls: str = "C", title: str = "Akış sınaması") -> tuple[str, Path]:
    code = works.new_work("TST", "SYN", title, cls, "sınama", "testler geçer")
    return code, works.find(code)


def log_entries(root) -> list[dict]:
    """The log's entries: {date, time, role, kind, title, body} (old gunluk.kayitlari_oku, the panel's reader)."""
    out = []
    for path in sorted((Path(root) / log.FOLDER).glob("*.md")):
        for block in path.read_text(encoding="utf-8").split("\n### ")[1:]:
            head, _, rest = block.partition("\n")
            parts, (title, _, body) = [x.strip() for x in head.split("·")], rest.strip().partition("\n")
            out.append({"date": path.stem, "time": parts[0], "role": " · ".join(parts[1:-1]), "kind": parts[-1],
                        "title": title.strip("*"), "body": body.strip()})
    return out


def run_record(state: Path, work: str, status: str = "running") -> Path:
    path = state / "mekanik" / "runs" / f"run-20261106-120000-{work[-2:]}00.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"kind": "agent_run", "work": work, "status": status, "role": "project_engineer"}))
    return path


def test_new_work_branches_skeleton_and_registry(shop):
    """old: test_akis::g0_dan_g3_e_ilerler_ve_gunlukte_gorunur (açılış kısmı)"""
    code, d = new()
    assert code == "TST-SYN-01" and git.branch(d) == f"{code}/work/general"
    assert git.branch_exists(shop.repo, f"{code}/main") and d.parent.name == "sentetik"
    from mekanik.core.model.work import load_work

    v = load_work(d)
    assert v.stage == "G0" and v.gates == ["G0", "G1", "G3", "G5"] and v.doc["branches"]["main"] == f"{code}/main"
    assert v.doc["process"]["gate_status"]["G0"]["status"] == "in_progress" and not git.git("status", "--porcelain",
                                                                                            cwd=d)
    assert [x["code"] for x in yamlio.read(shop.repo / "works.yaml")] == [code]


def test_work_numbers_are_never_reused(shop):
    """new: architecture §3.4 — works.yaml is append-only; a number is never given twice"""
    codes = [new(title=f"P{i}")[0] for i in range(2)]
    reg = yamlio.read(shop.repo / "works.yaml")
    assert codes == ["TST-SYN-01", "TST-SYN-02"] and [x["code"] for x in reg] == codes
    with pytest.raises(Refused) as e:
        works.new_work("TST", "SYN", "x", "Z")
    assert e.value.key == "store.class.bad" and len(yamlio.read(shop.repo / "works.yaml")) == 2


def test_two_works_open_at_most_three_active(shop):
    """old: test_akis::iki_calisma_acilir_gecilir_en_cok_uc (v1: active = open agent runs, not tmux sessions)"""
    codes = [new(title=f"Paralel {i}")[0] for i in range(4)]
    state = shop.root / "state"
    shutil.rmtree(works.tree(codes[0]))
    git.git("worktree", "prune", cwd=shop.repo)
    o = works.open_work(codes[0])                      # worktree made again from the work branch
    assert o["path"].name == codes[0] and o["path"].exists() and o["command"].startswith("cd ")
    for c in codes[:3]:
        run_record(state, c)
    assert works.active() == codes[:3]
    with pytest.raises(Refused) as e:
        works.open_work(codes[3])
    assert e.value.key == "store.open.limit" and e.value.data["n"] == 3
    assert works.open_work(codes[1])["code"] == codes[1]   # an active one opens again
    assert works.close_work(codes[0])
    assert works.open_work(codes[3])["path"].exists() and works.tree(codes[0]).exists()   # nothing deleted
    assert codes[0] not in works.active()


def test_attach_starts_a_tmux_session_in_the_work_folder(shop, monkeypatch):
    """new: Ek B §14 madde 12 (work attach); the tmux adapter is optional"""
    if not shutil.which("tmux"):
        pytest.skip("tmux not installed")
    code, d = new()
    monkeypatch.delenv("TMUX", raising=False)
    calls = []
    monkeypatch.setattr(works.os, "execvp", lambda p, a: calls.append(a))
    works.attach_work(code)
    assert calls[0][-2:] == ["-t", code]
    path = subprocess.run(works._tmux("display-message", "-p", "-t", code, "#{session_path}"), capture_output=True,
                          text=True).stdout.strip()
    assert Path(path) == d


def test_archive_deletes_nothing(shop):
    """old: test_akis::arsivle_hicbir_sey_silmez_panelden_gizler"""
    code, d = new()
    head = git.head(d)
    before = git.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", cwd=shop.repo)
    rec = works.archive_work(code, "sınama")
    assert git.git("rev-parse", f"{code}-archive^{{commit}}", cwd=shop.repo) == head
    after = git.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", cwd=shop.repo)
    assert all(x in after for x in before.splitlines() if not x.startswith("refs/heads/main "))
    assert not works.tree(code).exists() and (shop.root / "works" / "archive" / code).exists()
    assert code in works.archived(shop.repo) and rec["last_commit"] == head
    with pytest.raises(Refused) as e:
        works.archive_work(code, "yine")
    assert e.value.key == "store.archive.already"


def test_log_is_append_only_and_uses_the_system_clock(tmp_path, monkeypatch):
    """new: Ek B §14 madde 4 — gunluk.py: entries are only appended; date and time come from clock.now()"""
    times = iter(["2026-11-06T09:05:00+03:00", "2026-11-06T17:45:00+03:00", "2026-11-07T08:00:00+03:00"])
    monkeypatch.setattr(clock, "now", lambda: next(times))
    log.write(tmp_path, "TST-SYN-09", "project_engineer", "step", "ilk", "gövde", ["records/visuals/a.svg"],
              {"block": 0, "warn": 1, "pass": 2}, ["S-01"], "abcdef1234", "TST-SYN-09/work/general")
    first = (tmp_path / log.FOLDER / "2026-11-06.md").read_text()
    log.write(tmp_path, "TST-SYN-09", "chief_engineer", "approval", "ikinci")
    log.write(tmp_path, "TST-SYN-09", "design_engineer", "step", "ertesi gün")
    assert (tmp_path / log.FOLDER / "2026-11-06.md").read_text().startswith(first)
    entries = log_entries(tmp_path)
    assert [(e["date"], e["time"], e["title"]) for e in entries] == [
        ("2026-11-06", "09:05", "ilk"), ("2026-11-06", "17:45", "ikinci"), ("2026-11-07", "08:00", "ertesi gün")]
    assert "](../visuals/a.svg)" in entries[0]["body"] and "abcdef1" in entries[0]["body"]
