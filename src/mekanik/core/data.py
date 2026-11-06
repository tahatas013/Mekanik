# SPDX-License-Identifier: AGPL-3.0-or-later
"""Location of bundled data (schemas, stdlib): inside the wheel, or the repo root in a development checkout."""

from __future__ import annotations

from pathlib import Path

_PKG = Path(__file__).resolve().parent.parent  # src/mekanik
REPO_ROOT = _PKG.parents[1]


def data_dir(name: str) -> Path:
    """`name` is 'schemas' or 'stdlib'."""
    bundled = _PKG / "_data" / name
    return bundled if bundled.is_dir() else REPO_ROOT / name


def stdlib(*parts: str) -> Path:
    return data_dir("stdlib").joinpath(*parts)


def schemas(*parts: str) -> Path:
    return data_dir("schemas").joinpath("v1", *parts)
