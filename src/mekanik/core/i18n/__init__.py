# SPDX-License-Identifier: AGPL-3.0-or-later
"""UI text catalogs (architecture §4.12). Code holds keys; text lives in <lang>.yaml or <lang>.<part>.yaml.

Nested YAML keys are flattened with dots. A key missing in the active language falls back to Turkish,
then to the key itself (so a missing entry is visible, never silent).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

_DIRS: list[Path] = [Path(__file__).resolve().parent]
_CATALOGS: dict[str, dict[str, str]] | None = None
_LANG = os.environ.get("MEKANIK_LANG", "tr")


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        out.update(_flatten(v, key + ".") if isinstance(v, dict) else {key: str(v)})
    return out


def add_catalog(directory: Path) -> None:
    """Register a package catalog folder (holds tr.yaml and optionally en.yaml)."""
    global _CATALOGS
    directory = Path(directory)
    if directory not in _DIRS:
        _DIRS.append(directory)
        _CATALOGS = None


def catalogs() -> dict[str, dict[str, str]]:
    global _CATALOGS
    if _CATALOGS is None:
        _CATALOGS = {}
        for d in _DIRS:
            for f in sorted(d.glob("*.yaml")):
                cat = _CATALOGS.setdefault(f.stem.split(".")[0], {})   # tr.yaml, tr.cards.yaml …
                cat.update(_flatten(yaml.safe_load(f.read_text(encoding="utf-8")) or {}))
    return _CATALOGS


def set_lang(lang: str) -> None:
    global _LANG
    _LANG = lang


def lang() -> str:
    return _LANG


def has(key: str) -> bool:
    return key in catalogs().get("tr", {})


def t(key: str, **kw) -> str:
    cats = catalogs()
    text = cats.get(_LANG, {}).get(key) or cats.get("tr", {}).get(key) or key
    return text.format(**kw) if kw else text


def num(x: float | None, digits: int = 3) -> str:
    """Number for display, at least one decimal: 3.0 → '3,0', 0.25 → '0,25' (old `sonuc.mm`)."""
    if x is None:
        return "—"
    s = f"{x:.{digits}f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s.replace(".", t("num.decimal"))
