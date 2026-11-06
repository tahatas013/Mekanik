# SPDX-License-Identifier: AGPL-3.0-or-later
"""Role definitions (stdlib/roles) and the agent compiler: the committed plugin/agents equal the compiler output."""

import re

import pytest

from mekanik.agent import build
from mekanik.config import load_config
from mekanik.core import data, yamlio
from mekanik.core.i18n import lang, set_lang

ROOT = data.REPO_ROOT
ROLES = {f.stem: yamlio.read(f) for f in sorted(data.stdlib("roles").glob("*.yaml"))}


@pytest.fixture
def turkish():
    old = lang()
    set_lang("tr")  # the committed files are built with the role files' language
    yield
    set_lang(old)


def test_committed_agents_equal_compiler_output(tmp_path, turkish):
    """new: Ek B §14 madde 15 — agent files come from the role definitions; nobody edits them by hand"""
    written = build.build(tmp_path)
    committed = sorted((ROOT / "plugin" / "agents").glob("*.md"))
    assert [p.name for p in written] == [p.name for p in committed] == [
        "design-engineer.md", "quality-engineer.md", "technician.md"]
    for new, old in zip(written, committed):
        assert new.read_text(encoding="utf-8") == old.read_text(encoding="utf-8"), (
            f"{old.name} is stale: uv run python -m mekanik.agent build")


def test_front_matter_carries_name_model_and_tools(tmp_path, turkish):
    """new: Ek B §14 madde 15 — front matter (name, model, tools) parses; the quality engineer is read-only"""
    for p in build.build(tmp_path):
        head = yamlio.load(p.read_text(encoding="utf-8").split("---\n")[1])
        role = ROLES[head["name"].replace("-", "_")]
        assert head["tools"].split(", ") == build.SPEC["tools"][role["tool_class"]]
        assert head["model"] == build.SPEC["models"][role["id"]]["model"]
        assert head["description"] == role["description"].strip()
    qe = (tmp_path / "quality-engineer.md").read_text(encoding="utf-8")
    assert "tools: Read, Grep, Glob\n" in qe and "mekanik review prompt" in qe and "mekanik review record" in qe
    assert "[YÜKSEK|ORTA|DÜŞÜK] dosya:satır — sorun — ilke — kanıt" in qe, "old kalite.SATIR finding format"


def test_rebuild_uses_workshop_agent_roles(tmp_path, turkish):
    """new: architecture §5.4 — on a rebuild the model and tools come from the config's agent.roles"""
    roles = load_config().doc["agent"]["roles"]
    build.build(tmp_path, roles)
    qe, de = ((tmp_path / f).read_text(encoding="utf-8") for f in ("quality-engineer.md", "design-engineer.md"))
    assert f"model: {roles['quality_engineer']['model']}\n" in qe and "tools: Read, Grep, Glob\n" in qe
    assert "\nmodel:" not in de, "a role without a mapping inherits the session's model"


def test_role_definitions_are_complete_and_hold_no_model_name():
    """new: architecture §4.9 — authority, tool class and locked rules per role; the model lives in the config"""
    assert set(ROLES) == {"chief_engineer", "project_engineer", "design_engineer", "technician", "quality_engineer"}
    for rid, role in ROLES.items():
        assert role["id"] == rid and role["lang"] == "tr" and role["locked_rules"] and role["basis"]
        assert role["runs_as"] in ("person", "main_session", "subagent")
        assert role["authority"] in ("approve", "decide", "draw_within_brief", "findings_only", "none")
        assert role["tool_class"] in ("none", *build.SPEC["tools"])
        assert "model" not in role
        assert not re.search(r"\b(opus|sonnet|haiku)\b", (data.stdlib("roles") / f"{rid}.yaml").read_text(
            encoding="utf-8"), re.I)
        if role["runs_as"] == "subagent":
            assert role["prompt"] and role["output"] and role["tool_class"] != "none"
    assert ROLES["chief_engineer"]["authority"] == "approve" and ROLES["technician"]["authority"] == "none"
    assert [r for r, x in ROLES.items() if x["authority"] == "approve"] == ["chief_engineer"]


def test_skill_carries_the_project_engineer_rules():
    """new: architecture §4.9 — the main session's locked rules (divan) reach it through the mekanik skill"""
    skill = (ROOT / "plugin" / "skills" / "mekanik" / "SKILL.md").read_text(encoding="utf-8")
    for rule in ROLES["project_engineer"]["locked_rules"]:
        assert rule in skill, rule
