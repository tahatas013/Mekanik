# SPDX-License-Identifier: AGPL-3.0-or-later
"""CLI tests never touch the real ~/.config, ~/.local/state, ~/.cache or the works folder: HOME, the XDG folders and
MEKANIK_CONFIG_DIR point into tmp_path. `shop` adds a temporary organization repo and GPG keys for the chief's signed
approvals (no ssh-keygen in this container); the core runs with its own checks only (OCCT-free)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mekanik.cli.main import main
from mekanik.core import yamlio
from mekanik.core.store import git
from mekanik.plugins import reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "config"
CHIEF = ("Test Mühendis", "test@example.org")
TEAM = ("mekanik-ekip", "ekip@mekanik.local")


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    from mekanik.core.builtin import SPEC

    for k in ("HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME"):
        monkeypatch.setenv(k, str(tmp_path / k.lower()))
    (tmp_path / "home").mkdir()
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(FIXTURE))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("MEKANIK_TMUX_SOCKET", f"mekanik-cli-{os.getpid()}-{tmp_path.name}")
    (tmp_path / "gitconfig").write_text("")
    set_registry([SPEC])
    yield tmp_path
    reset_registry()
    subprocess.run(["tmux", "-L", os.environ["MEKANIK_TMUX_SOCKET"], "kill-server"], capture_output=True)


@pytest.fixture
def cli(capsys):
    """Run `mekanik <args>` in process → (exit code, stdout, stderr)."""
    def run(*args: str):
        capsys.readouterr()
        rc = main(list(args))
        out, err = capsys.readouterr()
        return rc, out, err
    return run


@pytest.fixture(scope="session")
def gpg_home(tmp_path_factory):
    if not shutil.which("gpg"):
        pytest.skip("gpg not installed")
    home = tmp_path_factory.mktemp("gnupg")
    home.chmod(0o700)
    env = {**os.environ, "GNUPGHOME": str(home)}
    uid = f"{CHIEF[0]} <{CHIEF[1]}>"
    subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key", uid,
                    "ed25519", "sign", "never"], check=True, capture_output=True, env=env)
    out = subprocess.run(["gpg", "--with-colons", "--list-secret-keys", CHIEF[1]], check=True, capture_output=True,
                         text=True, env=env).stdout
    yield home, next(x.split(":")[9] for x in out.splitlines() if x.startswith("fpr:"))
    subprocess.run(["gpgconf", "--kill", "gpg-agent"], capture_output=True, env=env)


@pytest.fixture
def shop(env, monkeypatch, gpg_home):
    """Organization TST (project SYN) with its repo in tmp_path/works/tst; config copy pinning the chief's GPG key."""
    home, key = gpg_home
    monkeypatch.setenv("GNUPGHOME", str(home))
    cfg, repo = env / "config", env / "works" / "tst"
    shutil.copytree(FIXTURE, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["paths"]["works_root"] = str(env / "works")
    doc["organizations"][0]["repo"] = str(repo)
    doc["identities"]["chief_signing_key"] = key
    yamlio.write(cfg / "config.yaml", doc)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    repo.mkdir(parents=True)
    git.git("init", "-q", "-b", "main", cwd=repo)
    git.git("config", "user.signingkey", key, cwd=repo)
    git.commit(repo, git.message("ilk", None, "project_engineer"), identity=TEAM, allow_empty=True)
    return SimpleNamespace(root=env, repo=repo, config=cfg, key=key)


@pytest.fixture
def work(shop, cli):
    """`mekanik work new` → (code, work folder)."""
    from mekanik.core.store import works

    rc, out, _ = cli("work", "new", "--org", "TST", "--project", "SYN", "--title", "CLI", "--class", "C",
                     "--purpose", "sınama", "--done", "testler geçer")
    assert rc == 0
    code = out.split()[0]
    return code, works.find(code)


@pytest.fixture
def tty():
    """`with tty("O-G0"):` an interactive terminal for `mekanik approve` whose user types the given answer."""
    import builtins
    import contextlib

    import mekanik.cli.main as m

    class Sys:
        stdin = stdout = SimpleNamespace(isatty=lambda: True)
        stderr = property(lambda self: sys.stderr)

    @contextlib.contextmanager
    def term(answer: str):
        real, ask = m.sys, builtins.input
        m.sys, builtins.input = Sys(), lambda prompt="": answer
        try:
            yield
        finally:
            m.sys, builtins.input = real, ask
    return term
