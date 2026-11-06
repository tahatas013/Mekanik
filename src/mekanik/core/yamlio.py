# SPDX-License-Identifier: AGPL-3.0-or-later
"""YAML reading and atomic writing.

YAML 1.1 turns yes/no/on/off into booleans; that is disabled here so `no: G-01` stays a key.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .errors import SchemaError


class Loader(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    """Safe loader without yes/no booleans; uses libyaml when available."""


_BOOL = "tag:yaml.org,2002:bool"
Loader.yaml_implicit_resolvers = {k: [(t, r) for t, r in v if t != _BOOL]
                                  for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
for _first in "tTfF":
    Loader.add_implicit_resolver(_BOOL, re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), [_first])


def load(text: str) -> Any:
    return yaml.load(text, Loader=Loader)


def read(path: Path, default: Any = None) -> Any:
    """Read a YAML file; a missing file gives `default`, a broken one raises SchemaError."""
    path = Path(path)
    if not path.exists():
        return default
    try:
        data = load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        from .i18n import t

        raise SchemaError(t("yaml.unreadable", path=str(path), error=str(e))) from e
    return default if data is None else data


def dump(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120)


def write_text(path: Path, text: str) -> None:
    """Atomic write: temp file in the same folder, then rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write(path: Path, data: Any) -> None:
    write_text(path, dump(data))


class Txn:
    """Several writes that are undone together (old `akis._Yazim`)."""

    def __init__(self) -> None:
        self._old: dict[Path, str | None] = {}

    def write(self, path: Path, data: Any) -> None:
        self.write_text(path, dump(data))

    def write_text(self, path: Path, text: str) -> None:
        path = Path(path)
        if path not in self._old:
            self._old[path] = path.read_text(encoding="utf-8") if path.exists() else None
        write_text(path, text)

    def rollback(self) -> None:
        for path, old in self._old.items():
            if old is None:
                path.unlink(missing_ok=True)
            else:
                write_text(path, old)
        self._old.clear()

    @property
    def paths(self) -> list[Path]:
        return list(self._old)
