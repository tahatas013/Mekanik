# SPDX-License-Identifier: AGPL-3.0-or-later
"""Plugin files: manifest, marketplace, hooks, the monitor and the MCP server point at the mekanik commands
(criterion 1.11; the monitor and the MCP server came back in phase 2, wave 2.2)."""

import json
import re

from mekanik.agent import hook
from mekanik.core import data
from mekanik.core.i18n import catalogs

ROOT = data.REPO_ROOT
PLUGIN = ROOT / "plugin"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_lists_the_plugin():
    """new: architecture §5.4 — the repo is also a marketplace; the plugin lives in plugin/"""
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    manifest = _json(PLUGIN / ".claude-plugin" / "plugin.json")
    (entry,) = market["plugins"]
    assert (ROOT / entry["source"]).resolve() == PLUGIN
    assert entry["name"] == manifest["name"] == market["name"] == "mekanik"
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", manifest["version"])
    assert _json(PLUGIN / ".mcp.json")["mcpServers"] == {"mekanik": {"command": "mekanik", "args": ["mcp"]}}


def test_hooks_call_mekanik_agent_hook():
    """new: architecture §5.4 — each hook event runs `mekanik agent hook <event>`; tools are matched with *"""
    hooks = _json(PLUGIN / "hooks" / "hooks.json")["hooks"]
    assert set(hooks) == {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Notification", "Stop",
                          "SubagentStop", "SessionEnd"}
    for event, (entry,) in hooks.items():
        commands = [h["command"] for h in entry["hooks"] if h["type"] == "command"]
        assert commands[0] == f"mekanik agent hook {event}"
        assert entry.get("matcher") == ("*" if event.endswith("ToolUse") else None)
    for event in ("SessionStart", "UserPromptSubmit"):  # old `surec bekleyenler --kanca` on the same two events
        assert [h["command"] for h in hooks[event][0]["hooks"]][1:] == ["mekanik pending --hook"]


def test_monitor_runs_mekanik_watch():
    """2.1: A12, KF1-15 — the plugin's monitor (default place monitors/monitors.json) runs `mekanik watch` at session
    start; the manifest does not move it"""
    from mekanik.cli.main import COMMANDS

    (mon,) = _json(PLUGIN / "monitors" / "monitors.json")
    assert (mon["name"], mon["command"]) == ("watch", "mekanik watch") and set(mon) <= {"name", "command",
                                                                                         "description", "when"}
    assert "monitors" not in _json(PLUGIN / ".claude-plugin" / "plugin.json")
    assert "watch" in {path for path, _, _ in COMMANDS}


def test_skill_front_matter_follows_agent_skills_standard():
    """new: architecture §5.4 — skill front matter limited to the Agent Skills fields"""
    text = (PLUGIN / "skills" / "mekanik" / "SKILL.md").read_text(encoding="utf-8")
    head = dict(line.split(": ", 1) for line in text.split("---\n")[1].splitlines())
    assert set(head) == {"name", "description"} and head["name"] == "mekanik"
    for cmd in ("mekanik check", "mekanik step", "mekanik review prompt", "mekanik review record", "mekanik approve"):
        assert cmd in text


def test_catalog_keys_exist_in_both_languages():
    """new: phase-1 guide rule 4 — every agent.* key the code uses is in tr; en carries the same keys"""
    tr = {k for k in catalogs()["tr"] if k.startswith("agent.")}
    en = {k for k in catalogs()["en"] if k.startswith("agent.")}
    used = {f"agent.deny.{k}" for k in hook.SPEC["block"]} | {"agent.deny.stop", "agent.deny.data",
                                                              "agent.block.data", "agent.context.data"}
    used |= {f"agent.watch.{k}" for k in ("started", "event")} | {f"agent.build.{k}" for k in (
        "generated", "rules", "look_for", "output")}
    assert used <= tr and tr == en
