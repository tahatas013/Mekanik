# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik mcp` (plugin/.mcp.json): read-only and team-level tools, none that approves or signs (§4.6); short
descriptions (A11, measured with `claude plugin details`); the stream line is committed alone so the folder stays
clean for the chief (Ö-07); the panel's address carries no secret."""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

from test_store import gpg_keys, new, prepare, shop  # noqa: E402,F401

from mekanik.agent import inbox, mcp  # noqa: E402
from mekanik.core.report import stream  # noqa: E402
from mekanik.core.store import git, works  # noqa: E402
from mekanik.plugins import reset_registry, set_registry  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[2] / "plugin"


@pytest.fixture(autouse=True)
def _core_only():
    from mekanik.core.builtin import SPEC

    set_registry([SPEC])
    yield
    reset_registry()


def test_tools_are_read_only_or_team_level():
    """2.1: A11, §4.6 — five tools; no approve, sign, gate or secret tool; the tool definitions (name, description,
    input schema) stay under 2 000 characters (≈ 570 tokens at 3.5 characters a token): with the always-on ~345
    tokens `claude plugin details` reports (it does not count MCP schemas) the plugin stays under 1 500 per turn"""
    s = mcp.server()
    tools = asyncio.run(s.list_tools())
    assert {x.name for x in tools} == {"work_status", "pending", "inbox", "note", "panel_url"}
    assert not any(w in x.name for x in tools for w in ("approve", "sign", "gate", "secret", "login"))
    defs = [{"name": x.name, "description": x.description, "input_schema": x.input_schema} for x in tools]
    assert len(json.dumps(defs, ensure_ascii=False)) + len(s.instructions or "") <= 2000
    assert json.loads((PLUGIN / ".mcp.json").read_text())["mcpServers"]["mekanik"] == {"command": "mekanik",
                                                                                      "args": ["mcp"]}


def test_status_pending_note_and_url(shop, monkeypatch):
    """2.1: A1 (agent side) — the tools read the session folder's work; `note` adds a stream line in a commit of
    events.jsonl only, the rest of a dirty tree untouched; the panel URL has no login token"""
    code, d = new()
    prepare(d)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(d))
    st = mcp.work_status()
    assert (st["work"], st["stage"], st["stop"]) == (code, "G0", False)
    inbox.send(code, "önce G0")
    assert [m["text"] for m in mcp.pending()["inbox"]] == ["önce G0"]
    (d / "notlar.md").write_text("taslak")
    head = git.head(d)
    out = mcp.note("Sehim hesabı başladı")
    assert stream.read(d)[-1]["id"] == out["id"] and git.git("rev-list", "--count", f"{head}..HEAD", cwd=d) == "1"
    assert git.git("show", "--name-only", "--format=", "HEAD", cwd=d).splitlines() == [
        f"sentetik/{code}/{stream.FILE}"] and f"?? sentetik/{code}/notlar.md" in works.dirty(d).splitlines()
    assert f"sentetik/{code}/params.yaml" in works.dirty(d)
    assert "token" not in mcp.panel_url() and mcp.panel_url().startswith("http://127.0.0.1:")
    reply = asyncio.run(mcp.server().call_tool("work_status", {"work": code}))
    assert json.loads(reply.content[0].text)["work"] == code
