# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check result and stage-dependent level (old `kontroller/sonuc.py`)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..i18n import t

BLOCK, WARN, PASS = "block", "warn", "pass"


@dataclass
class Result:
    check: str              # check id (guide §2.3)
    rule: str               # catalog rule id
    status: str             # block | warn | pass
    msg: str                # i18n key of the reason
    args: dict = field(default_factory=dict)
    ref: str | None = None  # param name, fit/flex id, decision id …
    value: float | None = None
    extra: dict = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return self.status != PASS

    @property
    def reason(self) -> str:
        return t(self.msg, **self.args)

    def as_dict(self) -> dict:
        return {**asdict(self), "reason": self.reason}


def level(view) -> str:
    """Exploration and development: warn; finalizing (G3–G5): block (handbook §10)."""
    return BLOCK if view.finalizing else WARN


def summary(results: list[Result]) -> dict:
    return {s: sum(r.status == s for r in results) for s in (BLOCK, WARN, PASS)}
