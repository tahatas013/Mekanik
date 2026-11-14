# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.7: EN catalog coverage — every Turkish catalog key (core src/mekanik/core/i18n/tr*.yaml, packages
packages/*/src/*/i18n/tr*.yaml) has its English text in the same catalog folder, with the same format placeholders;
no English key without a Turkish one, and no Turkish sentence copied as the English text. The files are read
directly (no package import: tests/core runs without the domain packages and OCCT)."""

from __future__ import annotations

import re
import string
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FOLDERS = [ROOT / "src" / "mekanik" / "core" / "i18n", *sorted(ROOT.glob("packages/*/src/*/i18n"))]
TURKISH = re.compile(r"[çğıöşüÇĞİÖŞÜ]")


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    out = {}
    for k, v in (d or {}).items():
        out.update(_flatten(v, f"{prefix}{k}.") if isinstance(v, dict) else {f"{prefix}{k}": str(v)})
    return out


def catalog(folder: Path, lang: str) -> dict[str, str]:
    """All keys of one language in a catalog folder (<lang>.yaml and <lang>.<part>.yaml), as i18n loads them."""
    out: dict[str, str] = {}
    for f in sorted(folder.glob(f"{lang}*.yaml")):
        if f.stem.split(".")[0] == lang:
            out.update(_flatten(yaml.safe_load(f.read_text(encoding="utf-8")) or {}))
    return out


def placeholders(text: str) -> set[tuple]:
    """{name}, {name:<8}, {commit:.7} …: (field, conversion, format spec); escaped braces are text."""
    return {(f, c, s) for _, f, s, c in string.Formatter().parse(text) if f is not None}


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda f: str(f.relative_to(ROOT)))
def test_every_turkish_key_has_its_english_text(folder):
    """2.7: %100 key coverage, missing key 0 — core and every package catalog"""
    tr, en = catalog(folder, "tr"), catalog(folder, "en")
    assert tr or not en, folder
    assert not sorted(set(tr) - set(en)), f"missing in EN: {sorted(set(tr) - set(en))}"
    assert not sorted(set(en) - set(tr)), f"in EN only: {sorted(set(en) - set(tr))}"


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda f: str(f.relative_to(ROOT)))
def test_english_text_keeps_the_placeholders_and_is_translated(folder):
    """2.7: the same format placeholders in both languages (the code fills them by name); a Turkish sentence of more
    than one word copied as the English text is not a translation"""
    tr, en = catalog(folder, "tr"), catalog(folder, "en")
    bad = {k: (placeholders(tr[k]), placeholders(en[k])) for k in tr.keys() & en.keys()
           if placeholders(tr[k]) != placeholders(en[k])}
    assert not bad, bad
    copied = [k for k in tr.keys() & en.keys() if en[k] == tr[k] and TURKISH.search(tr[k]) and " " in tr[k].strip()]
    assert not copied, copied
