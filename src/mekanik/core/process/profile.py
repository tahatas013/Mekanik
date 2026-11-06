# SPDX-License-Identifier: AGPL-3.0-or-later
"""Process profile: stages, gates and class→gate map as data (architecture §4.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache

from .. import data, yamlio
from ..errors import SchemaError
from ..i18n import t


@dataclass(frozen=True)
class ProcessProfile:
    ref: str
    stages: tuple[str, ...]
    finalizing_from: str
    classes: dict[str, tuple[str, ...]]
    risk_questions: tuple[dict, ...]
    gate_items: dict[str, tuple[str, ...]] = field(default_factory=dict)
    doc: dict = field(default_factory=dict)

    def finalizing(self, stage: str) -> bool:
        """Finalizing phase (old `kesinlestirme`): warnings become blocks from this gate on."""
        return self.stages.index(stage) >= self.stages.index(self.finalizing_from)

    def next_gate(self, gates: list[str], gate: str) -> str | None:
        i = gates.index(gate)
        return gates[i + 1] if i + 1 < len(gates) else None


@cache
def load_profile(ref: str = "default@1") -> ProcessProfile:
    path = data.stdlib("process", f"{ref}.yaml")
    if not path.exists():
        raise SchemaError(t("profile.missing", ref=ref))
    d = yamlio.read(path)
    return ProcessProfile(ref=ref, stages=tuple(d["stages"]), finalizing_from=d["finalizing_from"],
                          classes={k: tuple(v) for k, v in d["classes"].items()},
                          risk_questions=tuple(d.get("risk_questions") or ()),
                          gate_items={k: tuple(v) for k, v in (d.get("gate_items") or {}).items()}, doc=d)
