# SPDX-License-Identifier: AGPL-3.0-or-later
"""Workshop config (layer 4, architecture §3.3): person, identities, paths, organizations, machines, instruments.

Lives in ~/.config/mekanik (MEKANIK_CONFIG_DIR overrides it; tests point it at tests/fixtures/config).
Organizations, machines and instruments may sit in config.yaml lists or as one file each in orgs/, machines/,
instruments/; both forms are validated with the same schema definitions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.schema import validate

_SUBDIRS = {"organizations": "orgs", "machines": "machines", "instruments": "instruments"}


def config_dir() -> Path:
    if env := os.environ.get("MEKANIK_CONFIG_DIR"):
        return Path(env)
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "mekanik"


def state_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "mekanik"


@dataclass
class Config:
    root: Path
    doc: dict
    lists: dict[str, list[dict]] = field(default_factory=dict)

    @property
    def chief(self) -> tuple[str, str]:
        c = self.doc["identities"]["chief"]
        return c["name"], c["email"]

    @property
    def team(self) -> tuple[str, str]:
        c = self.doc["identities"]["team"]
        return c["name"], c["email"]

    @property
    def signing_key(self) -> str:
        return self.doc["identities"]["chief_signing_key"]

    def path(self, key: str, default: str | None = None) -> Path:
        return Path(os.path.expanduser(self.doc["paths"].get(key, default)))

    def _find(self, kind: str, key: str, value: str) -> dict:
        for x in self.lists[kind]:
            if x[key] == value:
                return x
        raise SchemaError(t(f"config.missing_{kind}", id=value, root=str(self.root)))

    def org(self, code: str) -> dict:
        return self._find("organizations", "code", code)

    def instrument(self, inst_id: str) -> dict:
        return self._find("instruments", "id", inst_id)

    def machine(self, ref: str) -> dict:
        """`<id>@<version>` → machine record; the version pin must match (old profil_yukle)."""
        mid, _, version = ref.partition("@")
        m = self._find("machines", "id", mid)
        if version and m.get("version", "v0") != version:
            raise SchemaError(t("config.machine_version", ref=ref, found=m.get("version", "v0")))
        from mekanik.plugins import registry

        check = registry().profile_types.get(m["type"])
        if check is None:
            raise SchemaError(t("config.unknown_profile_type", id=mid, type=m["type"]))
        check(m["profile"], f"machines/{mid}")
        return m


_CACHE: dict[Path, tuple[float, Config]] = {}


def _stamp(root: Path) -> float:
    files = [root / "config.yaml", *(f for d in _SUBDIRS.values() for f in (root / d).glob("*.yaml"))]
    return max((f.stat().st_mtime for f in files if f.exists()), default=0.0)


def load_config(root: Path | None = None) -> Config:
    root = Path(root or config_dir())
    stamp = _stamp(root)
    if root in _CACHE and _CACHE[root][0] == stamp:
        return _CACHE[root][1]
    path = root / "config.yaml"
    if not path.exists():
        raise SchemaError(t("config.missing", path=str(path)))
    doc = yamlio.read(path)
    validate("config", doc, str(path))
    lists = {}
    for key, sub in _SUBDIRS.items():
        items = list(doc.get(key) or [])
        for f in sorted((root / sub).glob("*.yaml")):
            item = yamlio.read(f)
            validate("config", {**_minimal(doc), key: [item]}, str(f))
            items.append(item)
        lists[key] = items
    cfg = Config(root=root, doc=doc, lists=lists)
    _CACHE[root] = (stamp, cfg)
    return cfg


def _minimal(doc: dict) -> dict:
    """Required top-level fields, so a single list item can be validated against the config schema."""
    return {k: doc[k] for k in ("kind", "schema_version", "person", "identities", "paths", "agent", "panel", "policy")}
