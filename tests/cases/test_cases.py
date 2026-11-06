# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression on the synthetic cases with every registered package (criterion 1.4).

The cases are tests/cases/{S-001,H-001} (built by tests/migrate/build_cases.py) and S-002, the v1 case of the four
phase-1 checks (KF1-17): its signed approvals cannot sit in the repo, so case.yaml is a commit sequence replayed here
in a temporary git repo with temporary GPG keys, each state run in its own worktree. A check that returns the same
status for everything (always block / always pass) must fail the regression: otherwise the case proves nothing."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.checks.regress import run_all, run_case
from mekanik.core.checks.result import BLOCK, PASS
from mekanik.plugins import registry, reset_registry

pytest.importorskip("cadquery")
pytestmark = pytest.mark.occt
ROOT = Path(__file__).resolve().parents[2]
CASE2 = yamlio.read(Path(__file__).parent / "S-002" / "case.yaml")
CHIEF, TEAM = ("Test Mühendis", "test@example.org"), ("mekanik-ekip", "ekip@mekanik.local")
NEW = {"approval_signature", "decision_effects", "card_standard", "quality_gate"}   # the phase-1 checks (KF1-17)


@pytest.fixture(autouse=True)
def _registry(monkeypatch):
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", "tests/fixtures/config")
    reset_registry()
    yield
    reset_registry()


def test_all_subcases_pass():
    """new: 1.4 — S-001 (10) + H-001 (8) subcases give the expected results with the real checks."""
    subs = run_all()
    assert len(subs) == 18
    assert all(s.passed for s in subs), [(s.case, s.id, s.errors) for s in subs if not s.passed]


def _replay(base: Path, keys: dict) -> dict[str, Path]:
    """S-002's steps in a git repo at `base`/repo (records, params, MG-01 cover, review, close; commits by chief,
    other, agent or team); → state id: worktree of that state's commit with its expected.yaml."""
    from mekanik.core import quality
    from mekanik.core.cards import approval
    from mekanik.core.errors import GitError
    from mekanik.core.model.work import load_work
    from mekanik.core.store import git
    from mekanik.migrate.convert import cover

    (root := base / "repo").mkdir()
    git.git("init", "-q", "-b", "main", cwd=root)
    shas, code = {}, CASE2["code"]
    for st in CASE2["steps"]:
        if "state" in st:
            shas[st["state"]] = git.head(root)
            continue
        for rel, doc in (st.get("files") or {}).items():
            (yamlio.write_text if isinstance(doc, str) else yamlio.write)(root / rel, doc)
        if st.get("params"):
            p = yamlio.read(root / "params.yaml")
            yamlio.write(root / "params.yaml", {n: p[n] | st["params"].get(n, {}) for n in p})
        for r in st.get("records") or []:
            v, raw = load_work(root), yamlio.read(root / "params.yaml")
            try:
                head = {"commit": git.git("rev-parse", "--verify", "-q", "HEAD", cwd=root)}
            except GitError:
                head = {}
            extra = {k: r[k] for k in ("migrated_from_hash",) if k in r}
            if n := r.get("new_value"):
                extra["new_value"] = {"name": n, "quantity": {k: raw[n][k] for k in ("value", "unit", "source",
                                                                                   "decided_by")}}
            subj = r["subject"] if r["subject"] != "card" else next(c["subject"] for c in v.cards
                                                                    if c["id"] == r["card"])
            approval.append(v, approval.record(v, r["card"], subj, r.get("action", "approve"), CHIEF, **head, **extra))
        if st.get("cover"):
            cover(root, yamlio.read(root / "work.yaml"))
        if "review" in st:
            quality.prompt(root, "S-002")
            quality.capture(code, st["review"])
            quality.record(root, "S-002", st["review"])
        if "close" in st:
            report = sorted((root / "records" / "quality").glob("*.yaml"))[-1].name
            quality.close(root, report, st["close"], "sınama", False, "S-002'nin kendisi", commit=git.head(root))
        git.git("config", "user.signingkey", keys["other" if st["by"] == "other" else "chief"], cwd=root)
        team = st["by"] == "team"
        git.commit(root, git.message(st["title"], None, "project_engineer" if team else "chief_engineer"),
                   identity=TEAM if team else CHIEF, allow_empty=True, sign=st["by"] in ("chief", "other"))
    out = {}
    for s in CASE2["states"]:
        git.git("worktree", "add", "-q", "--detach", str(d := base / s["id"]), shas[s["id"]], cwd=root)
        yamlio.write(d / "expected.yaml", {"code": code, "subcases": s["subcases"]})
        out[s["id"]] = d
    return out


@pytest.fixture(scope="module")
def s002(tmp_path_factory):
    """S-002 replayed, with the environment its checks need: GPG keys, a workshop config pinning the chief's key."""
    if not shutil.which("gpg"):
        pytest.skip("gpg not installed")
    base = tmp_path_factory.mktemp("s002")
    (home := base / "gnupg").mkdir(mode=0o700)
    (base / "gitconfig").write_text("")
    env = {"GNUPGHOME": str(home), "GIT_CONFIG_GLOBAL": str(base / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
           "XDG_STATE_HOME": str(base / "state"), "MEKANIK_CONFIG_DIR": str(cfg := base / "config")}
    keys, run = {}, lambda *a: subprocess.run(a, check=True, capture_output=True, text=True,
                                              env={**os.environ, **env}).stdout
    for who, uid in (("chief", f"{CHIEF[0]} <{CHIEF[1]}>"), ("other", "Başka <baska@example.org>")):
        run("gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key", uid, "ed25519",
            "sign", "never")
        keys[who] = next(x.split(":")[9] for x in run("gpg", "--with-colons", "--list-secret-keys", uid.split()[-1])
                         .splitlines() if x.startswith("fpr:"))
    shutil.copytree(ROOT / "tests" / "fixtures" / "config", cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["identities"]["chief_signing_key"] = keys["chief"]
    yamlio.write(cfg / "config.yaml", doc)
    with pytest.MonkeyPatch.context() as mp:
        for k, v in env.items():
            mp.setenv(k, v)
        yield _replay(base, keys), env
        run("gpgconf", "--kill", "gpg-agent")


def _all(s002, checks=None):
    return run_all(checks=checks) + [s for f in s002[0].values() for s in run_case(f, checks)]


def test_s002_subcases_pass(s002, monkeypatch):
    """new: KF1-17 — S-002's subcases (APPROVAL-02, DECISION-02, CARD-01, QUALITY-01) give the expected results"""
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", s002[1]["MEKANIK_CONFIG_DIR"])
    subs = [s for f in s002[0].values() for s in run_case(f)]
    assert len(subs) == sum(len(s["subcases"]) for s in CASE2["states"]) == 7
    assert all(s.passed for s in subs), [(s.case, s.id, s.errors) for s in subs if not s.passed]


def _uniform(spec, status):
    def run(view, model, cards=None):
        res = spec.run(view, model, cards=cards) if spec.after_cards else spec.run(view, model)
        return [replace(r, status=status) for r in res]
    return replace(spec, run=run)


def _covered() -> set[str]:
    """Check ids the expected.yaml files and S-002's states name."""
    root = Path(__file__).parent
    subs = [s for f in root.glob("*/expected.yaml") for s in yamlio.read(f)["subcases"]]
    return {e["check"] for s in subs + [x for st in CASE2["states"] for x in st["subcases"]] for e in s["expect"]}


@pytest.mark.parametrize("status", [BLOCK, PASS])
def test_uniform_check_fails_regression(status, s002, monkeypatch):
    """new: 1.4, KF1-17 — every check the cases cover, the four phase-1 ones too (S-002), made uniform (always block /
    always pass), fails at least one subcase."""
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", s002[1]["MEKANIK_CONFIG_DIR"])
    checks = registry().checks
    covered = _covered()
    survivors = []
    for i, spec in enumerate(checks):
        if spec.id not in covered:
            continue
        fake = [*checks[:i], _uniform(spec, status), *checks[i + 1:]]
        if all(s.passed for s in _all(s002, fake)):
            survivors.append(spec.id)
    assert NEW <= covered and not survivors, survivors
