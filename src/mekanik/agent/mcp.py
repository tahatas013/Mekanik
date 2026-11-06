# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik mcp` (architecture §5.4, plugin/.mcp.json): the plugin's MCP server over stdio, read-only and team-level
tools only. None approves, signs, passes a gate or reads a secret (§4.6); the panel's login link is never given. The
descriptions are part of the plugin's context cost (A11). The work is the session folder's (CLAUDE_PROJECT_DIR)."""

import functools
import json
import os
from pathlib import Path

from mekanik.config import load_config
from mekanik.core.i18n import t

from . import inbox, pulse
from .hook import SPEC, WORK_CODE, stop_flag, work_of

def _root(work: str = "") -> tuple[Path, dict]:
    """(work folder, the cached HEAD state the panel shows: check summary and cards)."""
    from mekanik.core.store import works
    from mekanik.panel import reads

    root = works.resolve(work or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return root, reads.state(root)


def work_status(work: str = "") -> dict:
    from mekanik.core.model.work import load_work
    from mekanik.core.process import gates

    root, st = _root(work)
    view = load_work(root)
    return {"work": view.code, "title": view.title, "stage": gates.stage(root, view), "gates": view.gates,
            "passed": gates.passed(root, view.code), "checks": st["summary"], "stop": stop_flag(view.code).exists(),
            "open_cards": [c["id"] for c in st["cards"] if c.get("status") == "open"], "lock": inbox.holder(
                view.code), "liveness": pulse.liveness(view.code)["status"], "next_step": view.doc.get("next_step")}


def pending(work: str = "") -> dict:
    from mekanik.core.process import chief

    root, st = _root(work)
    return {"chief": [{"id": c["id"], "title": c.get("title")} for c in st["cards"] if c.get("status") == "open"
                      and c.get("level") == "hold"], "replies": chief.pending(root),
            "inbox": [m for m in inbox.items(work_of(root) or "") if m["state"] == "pending"]}


def read_inbox(work: str = "") -> list[dict]:
    here = work or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    code = here if WORK_CODE.fullmatch(here) else work_of(Path(here)) or ""
    got = [m for m in inbox.items(code) if m["state"] != "read"]
    inbox.mark_read(code, [m["id"] for m in got])
    return [{k: m.get(k) for k in ("id", "kind", "at", "text")} for m in got]


def note(line: str, work: str = "", role: str = "project_engineer") -> dict:
    """A notice line in the stream, committed alone (events.jsonl only): the folder stays clean for the chief."""
    from mekanik.core.process import refuse
    from mekanik.core.report import stream
    from mekanik.core.store import git

    root, _ = _root(work)
    refuse((branch := git.branch(root)).endswith("/main"), "process.step.on_main", branch=branch)
    ev = stream.emit(root, "notice", role=role if role != "chief_engineer" else "project_engineer", line=line)
    git.git("add", "--", path := str(root / stream.FILE), cwd=root)
    git.git("commit", "-q", "-m", t("panel.mcp.note_title", line=ev["line"][:60]), "--", path, cwd=root,
            env=git.identity_env(*load_config().team))
    return {"id": ev["id"], "line": ev["line"]}


def panel_url() -> str:
    p = load_config().doc.get("panel") or {}
    return f"http://{p.get('host', '127.0.0.1')}:{p.get('port', 8765)}/"


def server():
    from mcp.server.mcpserver import MCPServer

    s = MCPServer("mekanik", instructions=t("panel.mcp.instructions"))
    for name, fn in (("work_status", work_status), ("pending", pending), ("inbox", read_inbox), ("note", note),
                     ("panel_url", panel_url)):   # JSON text out; fn's own parameters are the input schema
        s.add_tool(functools.wraps(fn)(lambda *a, _f=fn, **k: json.dumps(_f(*a, **k), ensure_ascii=False,
                                                                        default=str)),
                   name=name, description=SPEC["mcp_tools"][name], structured_output=False)
    return s


def serve() -> None:
    """`mekanik mcp`: run until the client closes stdin."""
    server().run("stdio")
