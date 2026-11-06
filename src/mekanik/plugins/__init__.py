# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package discovery and registry (architecture §11, phase-1 guide §4.1).

Each package exposes a `PackageSpec` under the entry-point group `mekanik.packages`. The core registers its own
checks the same way (`mekanik.core.builtin:SPEC`). The core never imports a package; it only calls what packages
registered here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Callable


@dataclass
class CheckSpec:
    id: str
    run: Callable[..., list]           # run(view, model, cards=None) -> list[Result]
    rules: tuple[str, ...] = ()
    after_cards: bool = False          # runs last, with cards made from the other results (old KARTLARLA)
    order: int = 100


@dataclass
class CriticalDim:
    """A measured value on which a tolerance band rests (input of UNCERT-01)."""
    ref: str                           # e.g. fit id
    param: str
    band: float | None                 # tolerance band width; None = undefined
    task: str | None = None


@dataclass
class SourcedValue:
    """A value outside params.yaml whose source SOURCE-01 must check (e.g. an assembly flex)."""
    ref: str
    value: float | None
    unit: str
    source: str | None


@dataclass
class PackageSpec:
    id: str
    version: str
    loaders: dict[str, Callable[[Path, Any], Any]] = field(default_factory=dict)
    checks: list[CheckSpec] = field(default_factory=list)
    card_makers: list[Callable[[Any, list], list[dict]]] = field(default_factory=list)
    critical_dims: Callable[[Any], list[CriticalDim]] | None = None
    sourced_values: Callable[[Any], list[SourcedValue]] | None = None
    param_uses: Callable[[Any], dict[str, list[str]]] | None = None   # param → interface records it enters
    subject_values: Callable[[Any, dict], dict | None] | None = None
    profile_types: dict[str, Callable[[dict, str], None]] = field(default_factory=dict)
    model: Any = None
    release_hooks: list[Callable[[Any, Any], list]] = field(default_factory=list)
    design_files: tuple[str, ...] = ()      # work files that enter the design hash (e.g. fits.yaml)
    i18n: Path | None = None


class Registry:
    def __init__(self, specs: list[PackageSpec]):
        self.packages = sorted(specs, key=lambda s: (s.id != "core", s.id))

    def get(self, pkg_id: str) -> PackageSpec | None:
        return next((p for p in self.packages if p.id == pkg_id), None)

    @property
    def checks(self) -> list[CheckSpec]:
        return sorted((c for p in self.packages for c in p.checks), key=lambda c: c.order)

    @property
    def card_makers(self) -> list[Callable]:
        return [m for p in self.packages for m in p.card_makers]

    @property
    def loaders(self) -> dict[str, Callable]:
        return {k: v for p in self.packages for k, v in p.loaders.items()}

    @property
    def profile_types(self) -> dict[str, Callable]:
        return {k: v for p in self.packages for k, v in p.profile_types.items()}

    @property
    def design_files(self) -> list[str]:
        return [f for p in self.packages for f in p.design_files]

    @property
    def release_hooks(self) -> list[Callable]:
        return [h for p in self.packages for h in p.release_hooks]

    def collect(self, attr: str, *args) -> list:
        """Concatenate the lists returned by an optional per-package hook (critical_dims, sourced_values)."""
        return [x for p in self.packages if getattr(p, attr) for x in getattr(p, attr)(*args)]

    def param_uses(self, view) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for p in self.packages:
            for k, v in (p.param_uses(view) if p.param_uses else {}).items():
                out.setdefault(k, []).extend(v)
        return out

    def subject_values(self, view, subject: dict) -> dict | None:
        for p in self.packages:
            if p.subject_values and (v := p.subject_values(view, subject)) is not None:
                return v
        return None

    def model_hooks(self):
        return next((p.model for p in self.packages if p.model is not None), None)


_REGISTRY: Registry | None = None


def registry() -> Registry:
    global _REGISTRY
    if _REGISTRY is None:
        specs = [ep.load() for ep in entry_points(group="mekanik.packages")]
        set_registry(specs)
    return _REGISTRY


def set_registry(specs: list[PackageSpec]) -> Registry:
    """Replace the registry (tests use it to run without a package or with fake checks)."""
    global _REGISTRY
    from mekanik.core import i18n

    _REGISTRY = Registry(specs)
    for s in _REGISTRY.packages:
        if s.i18n:
            i18n.add_catalog(s.i18n)
    return _REGISTRY


def reset_registry() -> None:
    global _REGISTRY
    _REGISTRY = None
