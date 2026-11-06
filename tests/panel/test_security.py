# SPDX-License-Identifier: AGPL-3.0-or-later
"""A9 and the panel's access rules: the old security e2e tests (testler/test_panel_e2e.py 8 and 16) on the back end —
Host and Origin, a branch that is not a work or decision branch, path escapes — and the new session secret, CSRF
token, loopback-only clients and the PTY socket's checks (A13's authorization part). Reasons are read by key."""

from __future__ import annotations

import os
import stat

import pytest
from panel_util import BASE, client_for
from starlette.websockets import WebSocketDisconnect

from mekanik.agent import hook
from mekanik.core.store import git
from mekanik.panel import auth


def key(r):
    return r.json()["error"]["key"]


def test_host_and_origin_are_checked(panel, g0):
    """2.1: A9 (old e2e 8) — a foreign Host is refused (DNS rebinding); a write needs a same-origin Origin (missing or
    foreign: refused), the CSRF token and JSON"""
    code, _ = g0
    r = panel.get("/api/tree", headers={"Host": "kotu.example"})
    assert r.status_code == 403 and key(r) == "panel.auth.host"
    url = f"/api/works/{code}/read-mark"
    assert key(panel.post(url, json={}, headers={"Origin": "http://kotu.example"})) == "panel.auth.origin"
    bare = {k: v for k, v in panel.headers.items() if k.lower() != "origin"}
    r = panel.post(url, json={}, headers={"Origin": ""}) if "origin" not in bare else None
    assert r is not None and r.status_code == 403 and key(r) == "panel.auth.origin"
    assert key(panel.post(url, json={}, headers={auth.CSRF_HEADER: "x" * 64})) == "panel.auth.csrf"
    r = panel.post(url, content=b"a=1", headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 415 and key(r) == "panel.auth.json"
    assert panel.post(url, json={}).status_code == 200


def test_session_secret_cookie_and_client(shop, g0):
    """2.1: A9 — /api without the session cookie is refused, the login link sets an HttpOnly SameSite cookie that is
    not the secret; a wrong token sets nothing; a client that is not loopback is refused; the secret file is mode
    600 and on the agent's block list (Read and Bash)"""
    from fastapi.testclient import TestClient

    from mekanik.panel.app import create_app

    app = create_app(watch=False)
    anon = client_for(app, login=False)
    assert anon.get("/api/tree").status_code == 401 and key(anon.get("/api/session")) == "panel.auth.session"
    assert anon.get("/login?token=yanlis").status_code == 401 and not anon.cookies
    r = anon.get(f"/login?token={auth.secret()}")
    head = r.headers["set-cookie"]
    assert r.status_code == 303 and "HttpOnly" in head and "SameSite=strict" in head and auth.secret() not in head
    assert anon.get("/api/tree").status_code == 200
    far = TestClient(app, base_url=BASE, client=("192.168.1.20", 4000), cookies=dict(anon.cookies))
    assert far.get("/api/tree").status_code == 403 and key(far.get("/api/tree")) == "panel.auth.client"
    assert stat.S_IMODE(os.stat(auth.secret_file()).st_mode) == 0o600
    work = g0[1]
    for tool, inp in (("Read", {"file_path": str(auth.secret_file())}), ("Bash", {"command": "cat ~/.local/state/"
                      "mekanik/panel.secret"}), ("Bash", {"command": "mekanik panel"}), ("Grep", {
                          "pattern": "x", "path": "/home/x/.local/state/mekanik"})):
        out = hook.handle("PreToolUse", {"session_id": "s", "cwd": str(work), "tool_name": tool, "tool_input": inp})
        assert out["hookSpecificOutput"]["permissionDecisionReason"] == hook.t("agent.deny.panel"), (tool, inp)


@pytest.mark.parametrize("branch", ["sha", "HEAD", "main", "../x"])
def test_only_work_and_decision_branches(panel, g0, branch):
    """2.1: A9 (old e2e 8) — `branch` is only a work or decision branch of this work: a commit, HEAD, the main line or
    a made-up name is refused, for reads and for writes"""
    code, d = g0
    b = {"sha": git.head(d), "HEAD": "HEAD", "main": f"{code}/main", "../x": f"{code}/work/../x"}[branch]
    r = panel.post(f"/api/works/{code}/cards/O-G0/decision", json={"action": "comment", "reason": "x", "branch": b})
    assert r.status_code == 409 and key(r) == "panel.branch.not_work" and r.json()["error"]["data"]["branch"] == b
    assert key(panel.get(f"/api/works/{code}/cards", params={"branch": b})) == "panel.branch.not_work"


@pytest.mark.parametrize("path", ["params.yaml", "out/../params.yaml", "../../../etc/passwd", "records/../work.yaml",
                                  "%2e%2e/%2e%2e/etc/passwd", "inputs/../../../../../etc/hostname", "/etc/passwd"])
def test_no_path_escape(panel, g0, path):
    """2.1: A9 (old e2e 16) — downloads only from out/, records/ and inputs/, images only inside the work folder;
    nothing outside them answers (404), however the path is written"""
    from mekanik.panel import reads

    code, _ = g0
    for screen in ("download", "images"):   # a URL the client folds out of /api/works/… never reaches the handler
        assert panel.get(f"/api/works/{code}/{screen}/{path}").status_code in (404, 503), (screen, path)
    for fn in (reads.download, reads.image):   # the raw path, as an unfolding client would send it
        with pytest.raises(reads.Unknown):
            fn(code, path.replace("%2e", "."))


def test_upload_names_and_unknown_works(panel, g0):
    """2.1: A9 — an upload name with a folder, '..' or a leading dot is refused; an unknown work code is 404"""
    from mekanik.core.process import Refused
    from mekanik.panel import writes

    code, d = g0
    for name in ("..%2Fwork.yaml", ".hidden", "a%2Fb.step"):
        r = panel.put(f"/api/works/{code}/inputs/{name}", content=b"x")
        assert r.status_code in (404, 405, 409), name
        assert r.status_code != 409 or key(r) == "panel.upload.bad_name"
    for name in ("../work.yaml", "a/b.step", ".hidden", ""):
        with pytest.raises(Refused) as e:
            writes.add_input(code, name, b"x")
        assert e.value.key == "panel.upload.bad_name"
    assert not (d / "inputs").exists()
    assert panel.get("/api/works/XXX-YYY-99").status_code == 404 and panel.get("/api/works/nope").status_code == 404


def test_pty_socket_needs_the_session(panel, g0):
    """2.1: A13 (authorization, wave 2.2) — the session tab's socket: without the cookie or with a foreign Origin it
    is closed unaccepted; with them it is accepted (the terminal itself is wave 2.3); the instruction box never
    writes into it"""
    from fastapi.testclient import TestClient

    code, _ = g0
    url = f"ws://127.0.0.1:8765/api/works/{code}/pty"
    anon = TestClient(panel.app, base_url=BASE, client=("127.0.0.1", 5))
    for c, headers in ((anon, {"Origin": BASE}), (panel, {"Origin": "http://kotu.example"})):
        with pytest.raises(WebSocketDisconnect) as e:
            with c.websocket_connect(url, headers=headers) as ws:
                ws.receive_json()
        assert e.value.code == 4401
    with panel.websocket_connect(url, headers={"Origin": BASE}) as ws:
        assert ws.receive_json()["error"]["key"] == "panel.pty.later"


def test_serve_refuses_a_public_address(shop):
    """2.1: A9 — the panel listens on loopback only; opening it to others is the platform adapter's job (§5.6)"""
    from mekanik.core.process import Refused
    from mekanik.panel import serve

    with pytest.raises(Refused) as e:
        serve("0.0.0.0", 8765)
    assert e.value.key == "panel.serve.loopback"
