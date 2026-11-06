# SPDX-License-Identifier: AGPL-3.0-or-later
"""Helpers of the panel tests (a unique module name: `conftest` is ambiguous when several test folders run)."""

from __future__ import annotations

BASE = "http://127.0.0.1:8765"


def client_for(app, login: bool = True, base: str = BASE):
    """A TestClient from 127.0.0.1; logged in with the session secret and sending Origin and the CSRF token."""
    from fastapi.testclient import TestClient

    from mekanik.panel import auth

    c = TestClient(app, base_url=base, client=("127.0.0.1", 50000), follow_redirects=False)
    if login:
        assert c.get(f"/login?token={auth.secret()}").status_code == 303
        c.headers.update({"Origin": base, auth.CSRF_HEADER: auth.csrf_token()})
    return c
