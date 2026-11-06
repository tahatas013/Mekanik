# SPDX-License-Identifier: AGPL-3.0-or-later
"""Panel cockpit (architecture §5): FastAPI back end (REST + SSE) on 127.0.0.1 only. `mekanik panel` calls `serve`."""

from __future__ import annotations

from mekanik.core.i18n import t

LOOPBACK = ("127.0.0.1", "::1", "localhost")


def login_url(host: str, port: int) -> str:
    """The link that opens the panel with its session (printed once to the chief's terminal; the agent may not run
    `mekanik panel`, claude_code.yaml block `panel`)."""
    from .auth import secret

    return f"http://{'[::1]' if host == '::1' else host}:{port}/login?token={secret()}"


def serve(host: str | None = None, port: int | None = None, rotate: bool = False) -> None:
    """Run the panel until stopped; host and port default to the workshop config's `panel`. Only a loopback host is
    served: reaching it from elsewhere is the platform adapter's job (e.g. a Tailscale serve, §5.6)."""
    import uvicorn

    from mekanik.config import load_config
    from mekanik.core.process import Refused

    from .app import create_app
    from .auth import secret

    cfg = load_config().doc.get("panel") or {}
    host, port = host or cfg.get("host", "127.0.0.1"), port or cfg.get("port", 8765)
    if host not in LOOPBACK:
        raise Refused("panel.serve.loopback", host=host)
    secret(rotate)
    print(t("panel.serve.open", url=login_url(host, port)), flush=True)
    uvicorn.run(create_app(), host=host, port=port, log_level="warning", timeout_graceful_shutdown=2)
