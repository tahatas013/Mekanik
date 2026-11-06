# SPDX-License-Identifier: AGPL-3.0-or-later
"""PreToolUse: block list (criterion 1.11: negative tests; a convenience layer, the guarantee is the signature),
stop flag (A5) and data gate (KM2-2 layer 3). The reason is checked by catalog key, not by text."""

import pytest

from mekanik.agent import hook
from mekanik.core.i18n import t


def pre(cwd, tool, **inp):
    return hook.handle("PreToolUse", {"session_id": "s", "cwd": str(cwd), "tool_name": tool, "tool_input": inp})


def denied(out, key, **kw):
    return out == {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                          "permissionDecisionReason": t(f"agent.deny.{key}", **kw)}}


BLOCKED = [  # (tool, input, catalog key)
    ("Bash", {"command": "mekanik approve O-G0 --action approve"}, "approve"),
    ("Bash", {"command": "uv run mekanik approve K-01 --option a"}, "approve"),
    ("Write", {"file_path": "/w/TST-SYN-01/approvals.yaml", "content": "- {}"}, "approvals_file"),
    ("Edit", {"file_path": "approvals.yaml", "old_string": "a", "new_string": "b"}, "approvals_file"),
    ("Bash", {"command": "printf -- '- action: approve\\n' >> approvals.yaml"}, "approvals_file"),
    ("Bash", {"command": 'git -c user.name="Test Mühendis" -c user.email=t@example.org commit -m onay'}, "identity"),
    ("Bash", {"command": "GIT_AUTHOR_NAME=x GIT_AUTHOR_EMAIL=x@example.org git commit -m onay"}, "identity"),
    ("Bash", {"command": "GIT_COMMITTER_EMAIL=test@example.org git commit --amend --no-edit"}, "identity"),
    ("Bash", {"command": 'git commit --author="Test Mühendis <test@example.org>" -m onay'}, "identity"),
    ("Bash", {"command": "git config user.email test@example.org"}, "identity"),
    ("Bash", {"command": "git commit -S -m onay"}, "signing"),
    ("Bash", {"command": "git commit --gpg-sign=ABC -m onay"}, "signing"),
    ("Bash", {"command": "git -c gpg.format=ssh -c user.signingkey=~/.ssh/k commit -m x"}, "signing"),
    ("Bash", {"command": "HOME=/tmp/sahte git commit -m onay"}, "identity"),
    ("Bash", {"command": "git config --global include.path /tmp/kimlik.inc"}, "identity"),
    ("Bash", {"command": "printf '[user]\\n name = x\\n' >> .git/config"}, "identity"),
    ("Edit", {"file_path": "/w/.git/config", "old_string": "a", "new_string": "b"}, "identity"),
    ("Write", {"file_path": "/home/x/.gitconfig", "content": "[user]"}, "identity"),
    ("Bash", {"command": "git tag TST-SYN-01-G1"}, "signing"),
    ("Bash", {"command": "ssh-add -c ~/.ssh/id_ed25519"}, "signing"),
    ("Bash", {"command": "ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n git msg"}, "signing"),
    ("Bash", {"command": "cat ~/.ssh/id_ed25519"}, "signing"),
    ("Read", {"file_path": "/home/x/.ssh/id_ed25519"}, "signing"),
    ("Edit", {"file_path": "/home/x/.config/git/allowed_signers", "old_string": "a", "new_string": "b"}, "signing"),
    ("Grep", {"pattern": "PRIVATE", "path": "/home/x/.gnupg"}, "signing"),
]


@pytest.mark.parametrize("tool, inp, key", BLOCKED, ids=[f"{k}:{i.get('command') or i.get('file_path') or i['path']}"
                                                         for _, i, k in BLOCKED])
def test_block_list_denies(work, tool, inp, key):
    """new: criterion 1.11 — PreToolUse block list, negative test"""
    assert denied(pre(work, tool, **inp), key)


ALLOWED = [
    ("Bash", {"command": "mekanik step 'G1 hazırlığı'"}),
    ("Bash", {"command": "mekanik pending"}),
    ("Bash", {"command": "git commit -m 'adım'"}),
    ("Bash", {"command": "git log -S nominal --oneline"}),
    ("Bash", {"command": "git describe --tags"}),
    ("Bash", {"command": "git status --porcelain"}),
    ("Read", {"file_path": "/w/TST-SYN-01/params.yaml"}),
    ("Read", {"file_path": "/w/TST-SYN-01/approvals.yaml"}),
    ("Read", {"file_path": "/w/.git/config"}),
    ("Edit", {"file_path": "/w/TST-SYN-01/fits.yaml", "old_string": "a", "new_string": "b"}),
]


@pytest.mark.parametrize("tool, inp", ALLOWED, ids=[i.get("command") or i["file_path"] for _, i in ALLOWED])
def test_ordinary_tools_pass_without_allow(work, tool, inp):
    """new: criterion 1.11 — the list does not catch ordinary work; the hook never answers 'allow'"""
    assert pre(work, tool, **inp) == {}


def test_stop_flag_denies_every_non_mekanik_tool(work):
    """new: A5 — with the stop flag every non-mekanik tool is denied, whatever the model; mekanik commands run"""
    flag = hook.stop_flag("TST-SYN-01")
    flag.parent.mkdir(parents=True)
    flag.touch()
    for tool, inp in (("Bash", {"command": "ls"}), ("Edit", {"file_path": str(work / "params.yaml")}),
                      ("Read", {"file_path": str(work / "work.yaml")}), ("Task", {"prompt": "çiz"}),
                      ("Bash", {"command": "mekanik step x && rm -rf model"}), ("Bash", {"command": "mekanik $(id)"})):
        assert denied(pre(work, tool, **inp), "stop", work="TST-SYN-01"), (tool, inp)
    assert pre(work, "Bash", command="mekanik step 'durduruldu, bekliyorum'") == {}
    assert pre(work, "mcp__plugin_mekanik_mekanik__work_status") == {}
    assert denied(pre(work, "Bash", command="mekanik approve O-G1"), "approve")
    flag.unlink()
    assert pre(work, "Bash", command="ls") == {}


def test_data_gate_denies_tools_on_forbidden_organization(forbidden, work):
    """new: architecture §5.4 KM2-2 layer 3 — tools touching a forbidden organization's work or repo are denied"""
    nop = forbidden / "sentetik" / "NOP-SYN-01"
    assert denied(pre(nop, "Read", file_path=str(nop / "params.yaml")), "data", org="NOP")
    assert denied(pre(nop, "Bash", command="mekanik step x"), "data", org="NOP")
    assert denied(pre(work, "Read", file_path=str(nop / "params.yaml")), "data", org="NOP")
    assert denied(pre(work, "Bash", command=f"cat {forbidden}/works.yaml"), "data", org="NOP")
    assert denied(pre(work, "Grep", pattern="nominal", path=str(forbidden)), "data", org="NOP")
    assert denied(pre(work, "Bash", command="ls ../../NOP-SYN-02"), "data", org="NOP")
    assert pre(work, "Read", file_path=f"{forbidden}2/params.yaml") == {}, "a sibling folder is not the repo"
    assert pre(work, "Read", file_path=str(work / "params.yaml")) == {}
