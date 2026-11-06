# SPDX-License-Identifier: AGPL-3.0-or-later
"""Panel access (architecture §4.6 m.3, §5.6; old uygulama.koruma): loopback clients only; Host on the allowed list
(DNS rebinding); every /api call carries the session cookie, made from a secret the agent cannot read (a mode-600 file
in the state folder, on the agent's block list); every write also the CSRF token, a same-origin Origin and JSON.

`mekanik panel` prints a login link with the secret once; /login turns it into an HttpOnly, SameSite=Strict cookie
(an HMAC of the secret, never the secret) and the page reads the CSRF token from /api/session."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from mekanik.config import state_dir

LOOPBACK = {"127.0.0.1", "::1", "localhost"}
COOKIE, CSRF_HEADER = "mekanik_session", "x-csrf-token"
READS = ("GET", "HEAD", "OPTIONS")
RAW_UPLOAD = "/inputs/"   # PUT …/inputs/<name> carries the file itself, not JSON (CSRF token and Origin still apply)


def secret_file() -> Path:
    """The session secret; its name is on the PreToolUse block list (claude_code.yaml `panel`)."""
    return state_dir() / "panel.secret"


def secret(rotate: bool = False) -> str:
    """The secret, made on first use (32 random bytes, mode 600); kept across restarts so an open page stays in."""
    path = secret_file()
    if rotate or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(32))
        os.replace(tmp, path)
    path.chmod(0o600)
    return path.read_text().strip()


def _mac(purpose: str) -> str:
    return hmac.new(secret().encode(), purpose.encode(), hashlib.sha256).hexdigest()


def session_value() -> str:
    return _mac("session")


def csrf_token() -> str:
    return _mac("csrf")


def same(a: str | None, b: str) -> bool:
    return bool(a) and hmac.compare_digest(str(a), b)


def hosts() -> set[str]:
    """Loopback names and what the platform adapter adds (MEKANIK_PANEL_HOSTS, comma list; e.g. a Tailscale name)."""
    return LOOPBACK | {x.strip().lower() for x in os.environ.get("MEKANIK_PANEL_HOSTS", "").split(",") if x.strip()}


def host_name(netloc: str) -> str:
    try:
        return (urlsplit("//" + netloc).hostname or "").lower()
    except ValueError:
        return ""


def refusal(method: str, path: str, client: str | None, headers, socket: bool = False) -> tuple[int, str] | None:
    """(HTTP status, catalog key) when a request may not pass; None when it may. A WebSocket (`socket`) is checked
    as a write without the CSRF token and JSON: a browser sends its Origin, which must be this host."""
    if client not in ("127.0.0.1", "::1"):
        return 403, "panel.auth.client"
    if host_name(host := headers.get("host", "")) not in hosts():
        return 403, "panel.auth.host"
    if not path.startswith("/api/"):
        return None
    if not same(_cookie(headers.get("cookie", "")), session_value()):
        return 401, "panel.auth.session"
    if method in READS and not socket:
        return None
    origin = headers.get("origin") or headers.get("referer") or ""
    if not origin or urlsplit(origin).netloc.lower() != host.lower():
        return 403, "panel.auth.origin"
    if socket:
        return None
    if not same(headers.get(CSRF_HEADER), csrf_token()):
        return 403, "panel.auth.csrf"
    if RAW_UPLOAD not in path and not headers.get("content-type", "").startswith("application/json"):
        return 415, "panel.auth.json"
    return None


def _cookie(header: str) -> str | None:
    for part in header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == COOKIE:
            return v
    return None
