# SPDX-License-Identifier: AGPL-3.0-or-later
"""Panel back-end tests (wave 2.2): the shop fixture of tests/core/test_store.py (a temporary organization repo, GPG
keys for the chief's signed approvals, XDG folders in tmp_path), the core's own checks only (OCCT-free) unless a test
installs the packages; the FastAPI app in process (TestClient from 127.0.0.1) or on a real port (`served`)."""

from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

from test_store import gpg_keys, new, prepare, review, shop  # noqa: E402,F401

from mekanik.core.process import gates  # noqa: E402
from mekanik.core.process.step import step  # noqa: E402
from mekanik.plugins import reset_registry, set_registry  # noqa: E402
from panel_util import client_for  # noqa: E402


@pytest.fixture(autouse=True)
def _core_only():
    from mekanik.core.builtin import SPEC

    set_registry([SPEC])
    yield
    reset_registry()


@pytest.fixture
def panel(shop):
    from mekanik.panel.app import create_app

    with client_for(create_app(watch=False)) as c:
        yield c


@pytest.fixture
def g0(shop):
    """A work at G0 with its gate requested (risk answers, a requirement, sourced params, a quality review)."""
    code, d = new()
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    return code, d


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def served(shop):
    """The panel on a real port with its watcher (SSE latency tests): → (base URL, session cookie, server)."""
    import uvicorn

    from mekanik.panel import auth
    from mekanik.panel.app import create_app

    port = free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="warning",
                                          timeout_graceful_shutdown=1))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.02)
    yield f"http://127.0.0.1:{port}", {auth.COOKIE: auth.session_value()}, server
    server.should_exit = server.force_exit = True   # an open event stream does not hold the shutdown
    th.join(5)
