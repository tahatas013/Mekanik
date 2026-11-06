# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only view of a work folder (old `veri.calisma_yukle`). Packages add their data through loaders (view.ext)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import yamlio
from ..errors import SchemaError
from ..i18n import t
from ..process.profile import ProcessProfile, load_profile
from .params import Param, parse_params
from .schema import validate


@dataclass
class WorkView:
    root: Path
    code: str
    title: str
    stage: str
    risk_class: str
    gates: list[str]
    doc: dict
    profile: ProcessProfile
    params: dict[str, Param]
    requirements: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    cards: list[dict] = field(default_factory=list)
    approvals: list[dict] = field(default_factory=list)
    replies: list[dict] = field(default_factory=list)
    manufacturing: dict | None = None
    instruments: dict[str, dict] = field(default_factory=dict)
    ext: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def finalizing(self) -> bool:
        return self.profile.finalizing(self.stage)


def _list(root: Path, name: str, kind: str, warnings: list[str]) -> list[dict]:
    items = yamlio.read(root / name, [])
    if not isinstance(items, list):
        raise SchemaError(t("schema.not_list", where=name))
    if kind == "replies":
        warnings += validate(kind, items, name)
    else:
        for i, x in enumerate(items):
            warnings += validate(kind, x, f"{name}[{i}]")
    return items


def load_work(root: Path, config=None) -> WorkView:
    from mekanik.config import load_config
    from mekanik.plugins import registry

    root = Path(root)
    if not (root / "work.yaml").exists():
        raise SchemaError(t("work.missing", root=str(root)))
    doc = yamlio.read(root / "work.yaml")
    warnings = validate("work", doc, "work.yaml")
    proc = doc["process"]
    profile = load_profile(proc["profile"])
    if proc["stage"] not in profile.stages:
        raise SchemaError(t("work.bad_stage", stage=proc["stage"], stages=", ".join(profile.stages)))
    if doc["risk_class"] not in profile.classes:
        raise SchemaError(t("work.bad_class", cls=doc["risk_class"], classes=", ".join(profile.classes)))

    cfg = config or load_config()
    profiles = doc.get("profiles") or {}
    manufacturing = cfg.machine(profiles["manufacturing"]) if profiles.get("manufacturing") else None
    instruments = {i: cfg.instrument(i) for i in profiles.get("instruments") or []}

    params = parse_params(yamlio.read(root / "params.yaml", {}))
    for p in params.values():
        if p.measured and p.instrument not in instruments:
            raise SchemaError(t("work.instrument_not_pinned", param=p.name, instrument=p.instrument))

    req = yamlio.read(root / "requirements.yaml", None)
    if req:
        warnings += validate("requirement", req, "requirements.yaml")
    cards = []
    for f in sorted((root / "cards").glob("*.yaml")):
        card = yamlio.read(f)
        warnings += validate("card", card, f"cards/{f.name}")
        cards.append(card)

    view = WorkView(
        root=root, code=doc["code"], title=doc["title"], stage=proc["stage"], risk_class=doc["risk_class"],
        gates=list(proc["gates"]), doc=doc, profile=profile, params=params,
        requirements=list((req or {}).get("items") or []),
        decisions=_list(root, "decisions.yaml", "decision", warnings), cards=cards,
        approvals=_list(root, "approvals.yaml", "approval", warnings),
        replies=_list(root, "replies.yaml", "replies", warnings),
        manufacturing=manufacturing, instruments=instruments, warnings=warnings)
    for name, loader in registry().loaders.items():
        view.ext[name] = loader(root, view)
    return view
