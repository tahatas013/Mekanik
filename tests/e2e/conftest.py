# SPDX-License-Identifier: AGPL-3.0-or-later
"""The panel's end-to-end tests (criteria 2.6, A1, A3, A4, A13, 2.8): the built front end (panel-ui/dist) against
the real back end on a port in this process, in a temporary workshop (organization repo, config copy, GPG keys for
the chief's signed approvals, XDG folders) with the real packages (mech builds the models), driven by Chromium
through Node Playwright (browser.py). Marked `e2e`: `pytest -m e2e` runs them; the default run skips them unless
MEKANIK_E2E=1. They need `npm ci && npm run build` in panel-ui and a Chromium for Playwright."""

from __future__ import annotations

import os
import shlex
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[0] / "core")]

from test_store import FIXTURE_CONFIG, TEAM, gpg_keys, new, prepare, review  # noqa: E402,F401

from mekanik.core import yamlio  # noqa: E402
from mekanik.core.store import git  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: panel end-to-end tests in a browser (pytest -m e2e)")


def pytest_collection_modifyitems(config, items):
    if "e2e" in (config.getoption("-m") or "") or os.environ.get("MEKANIK_E2E") == "1":
        return
    skip = pytest.mark.skip(reason="panel e2e: run with -m e2e (or MEKANIK_E2E=1)")
    for it in items:
        if "e2e" in it.keywords:
            it.add_marker(skip)


def workshop(tmp: Path, setenv, fingerprint: str, gnupg: Path) -> SimpleNamespace:
    """The shop of tests/core/test_store.py for a whole module: env, config copy, organization repo TST."""
    for k, v in {"GNUPGHOME": gnupg, "GIT_CONFIG_GLOBAL": tmp / "gitconfig", "GIT_CONFIG_NOSYSTEM": "1",
                 "XDG_STATE_HOME": tmp / "state", "XDG_DATA_HOME": tmp / "data", "XDG_CACHE_HOME": tmp / "cache",
                 "MEKANIK_TMUX_SOCKET": f"mekanik-e2e-{tmp.name}", "MEKANIK_CONFIG_DIR": tmp / "config"}.items():
        setenv(k, str(v))
    (tmp / "gitconfig").write_text("")
    cfg, repo = tmp / "config", tmp / "works" / "tst"
    shutil.copytree(FIXTURE_CONFIG, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["paths"]["works_root"] = str(tmp / "works")
    doc["organizations"][0]["repo"] = str(repo)
    doc["identities"]["chief_signing_key"] = fingerprint
    yamlio.write(cfg / "config.yaml", doc)
    repo.mkdir(parents=True)
    git.git("init", "-q", "-b", "main", cwd=repo)
    git.git("config", "user.signingkey", fingerprint, cwd=repo)
    git.commit(repo, git.message("ilk", None, "project_engineer"), identity=TEAM, allow_empty=True)
    return SimpleNamespace(root=tmp, repo=repo, config=cfg)


@pytest.fixture(scope="module")
def shop_e2e(tmp_path_factory, gpg_keys):
    from mekanik.plugins import reset_registry

    if not (HERE.parents[1] / "panel-ui" / "dist" / "index.html").exists():
        pytest.skip("panel-ui is not built: cd panel-ui && npm ci && npm run build")
    home, keys = gpg_keys
    with pytest.MonkeyPatch.context() as mp:
        reset_registry()
        mp.setenv("MEKANIK_CLAUDE", shlex.join([sys.executable, str(HERE / "fake_claude.py")]))
        shop = workshop(tmp_path_factory.mktemp("e2e"), mp.setenv, keys["chief"], home)
        mp.setenv("FAKE_CLAUDE_LOG", str(shop.root / "fake-claude.log"))
        yield shop
        from mekanik.core.store import works

        import subprocess

        subprocess.run(works._tmux("kill-server"), capture_output=True)
        reset_registry()


@pytest.fixture(scope="module")
def panel_e2e(shop_e2e):
    from stage import Panel

    p = Panel().start()
    yield p
    p.stop()


@pytest.fixture(scope="module")
def browser():
    from browser import Browser

    try:
        b = Browser()
    except (FileNotFoundError, AssertionError) as e:
        pytest.skip(f"no Node Playwright: {e}")
    yield b
    b.close()


@pytest.fixture(scope="module")
def page(browser, panel_e2e):
    """One logged-in page at 1440×900 (the wireframes' size)."""
    pg = browser.page("main")
    pg.goto(panel_e2e.login())
    yield pg


def go(page, panel, route: str, screen: str | None = None):
    """Open #<route> in a freshly loaded page and wait until its screen is drawn."""
    url = f"{panel.url}/#{route}"
    if page.url() != url:
        page.goto(url)
    page.reload()   # a fresh page: no state of the previous test, works made since are in the tree
    page.shown(screen or route.split("?")[0].split("/")[-1])


@pytest.fixture(autouse=True)
def _keep_failure_logs(request, tmp_path_factory):
    yield
    rep = getattr(request.node, "rep_call", None)
    pg = request.node.funcargs.get("page") if hasattr(request.node, "funcargs") else None
    if rep is not None and rep.failed and pg is not None:
        out = tmp_path_factory.getbasetemp() / f"e2e-{request.node.name}"
        out.mkdir(exist_ok=True)
        pg.screenshot(out / "page.png")
        (out / "console.txt").write_text("\n".join(pg.logs()))
        print(f"e2e failure artefacts: {out}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    rep = (yield).get_result()
    if rep.when == "call":
        item.rep_call = rep
