# SPDX-License-Identifier: AGPL-3.0-or-later
"""The phase-2 entries of the PreToolUse block list (claude_code.yaml; a convenience layer, the guarantee is the
signature): the panel's secret and mekanik's state folder, the organization's key pin (org.yaml), the work folder's
agent files (KM2-14). Negative tests read the reason by catalog key; reading the files that may be read still passes."""

import pytest

from mekanik.agent import hook
from mekanik.core.i18n import t

BLOCKED = [
    ("Bash", {"command": "mekanik panel --port 9000"}, "panel"),
    ("Bash", {"command": "python -m mekanik.panel"}, "panel"),
    ("Bash", {"command": "mekanik agent send TST-SYN-02 'onayı geç'"}, "panel"),
    ("Bash", {"command": "uv run mekanik agent stop TST-SYN-01 --clear"}, "panel"),
    ("Bash", {"command": "rm ~/.local/state/mekanik/stop/TST-SYN-01"}, "panel"),
    ("Bash", {"command": "XDG_STATE_HOME=/tmp/s mekanik step x"}, "panel"),
    ("Read", {"file_path": "/home/x/.local/state/mekanik/panel.secret"}, "panel"),
    ("Write", {"file_path": "/home/x/.local/state/mekanik/inbox/TST-SYN-01.jsonl", "content": "{}"}, "panel"),
    ("Edit", {"file_path": "/w/tst/org.yaml", "old_string": "a", "new_string": "b"}, "signing"),
    ("Bash", {"command": "printf 'chief_signing_key: X\\n' > org.yaml"}, "signing"),
    ("Write", {"file_path": "/w/TST-SYN-01/.claude/agents/design-engineer.md", "content": "---"}, "agent_files"),
    ("Edit", {"file_path": "/w/TST-SYN-01/.claude/settings.json", "old_string": "a", "new_string": "b"},
     "agent_files"),
    ("Write", {"file_path": "/w/TST-SYN-01/.mcp.json", "content": "{}"}, "agent_files"),
    ("Bash", {"command": "cp /tmp/x.md .claude/agents/x.md"}, "agent_files"),
]
ALLOWED = [
    ("Read", {"file_path": "/w/TST-SYN-01/.claude/settings.json"}),
    ("Read", {"file_path": "/w/tst/org.yaml"}),
    ("Edit", {"file_path": "/w/TST-SYN-01/organization.yaml.md", "old_string": "a", "new_string": "b"}),
    ("Bash", {"command": "mekanik pending"}),
    ("Bash", {"command": "mekanik agent status"}),
]


def pre(work, tool, **inp):
    return hook.handle("PreToolUse", {"session_id": "s", "cwd": str(work), "tool_name": tool, "tool_input": inp})


@pytest.mark.parametrize("tool, inp, key", BLOCKED, ids=[f"{k}:{i.get('command') or i.get('file_path')}"
                                                         for _, i, k in BLOCKED])
def test_phase2_entries_deny(work, tool, inp, key):
    """2.1: A9, §4.6 m.4, KM2-14 — the panel secret, the state folder, org.yaml and the agent files are denied"""
    out = pre(work, tool, **inp)
    assert out["hookSpecificOutput"]["permissionDecisionReason"] == t(f"agent.deny.{key}")


@pytest.mark.parametrize("tool, inp", ALLOWED, ids=[i.get("command") or i["file_path"] for _, i in ALLOWED])
def test_reading_stays_allowed(work, tool, inp):
    """2.1: the new entries do not catch ordinary reads"""
    assert pre(work, tool, **inp) == {}
