# SPDX-License-Identifier: AGPL-3.0-or-later
"""Agent compiler (architecture §4.9, §5.4): stdlib/roles/<role>.yaml (runs_as: subagent) → plugin/agents/*.md.
Models: the mapping given (config `agent.roles` on a rebuild), else claude_code.yaml's (the committed plugin)."""

import json
from pathlib import Path

from mekanik.core import data, yamlio
from mekanik.core.i18n import t

from .hook import SPEC


def render(role: dict, model: dict | None = None) -> str:
    """Agent file text: front matter (name, description, tools, model alias) and the role's prompt and rules."""
    model, desc = model or {}, json.dumps(role["description"].strip(), ensure_ascii=False)
    head = ["---", "# " + t("agent.build.generated", source=f"stdlib/roles/{role['id']}.yaml"),
            f"name: {role['id'].replace('_', '-')}", f"description: {desc}",
            "tools: " + ", ".join(model.get("tools") or SPEC["tools"][role["tool_class"]])]
    head += [f"model: {model['model']}"] if model.get("model") else []
    body = [role["prompt"].strip(), "", f"{t('agent.build.rules')} ({', '.join(role['basis'])}):",
            *(f"- {r}" for r in role["locked_rules"])]
    body += ["", f"{t('agent.build.look_for')}: {role['look_for'].strip()}"] if role.get("look_for") else []
    return "\n".join([*head, "---", "", *body, "", f"{t('agent.build.output')}: {role['output'].strip()}"]) + "\n"


def build(out: Path, models: dict | None = None) -> list[Path]:
    """Write the agent files into `out`; `models` is role → {model, tools?} (config agent.roles' shape)."""
    written = []
    for f in sorted(data.stdlib("roles").glob("*.yaml")):
        if (role := yamlio.read(f))["runs_as"] == "subagent":
            written.append(Path(out) / f"{role['id'].replace('_', '-')}.md")
            yamlio.write_text(written[-1], render(role, (SPEC["models"] if models is None else models).get(role["id"])))
    return written
