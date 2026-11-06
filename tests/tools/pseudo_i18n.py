# SPDX-License-Identifier: AGPL-3.0-or-later
"""pytest plugin (`-p pseudo_i18n`): a temporary pseudo-language catalog in which every Turkish text is wrapped in «…»
(placeholders and the decimal sign kept), and the language set to it. A test that checks keys and structured data
passes; one that compares output with Turkish text, or cuts values out of printed text, fails (guide §1 rule 4).

The catalog is a file in a temporary folder, registered under the code `en`: records keep card texts per language and
their schema accepts tr and en only, so an unknown code (`xx`) would stop the flow at the first card, not at a test.
It is loaded after the real catalogs and wins over the EN text. From the phase-1 exit review (KF1-11)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import yaml

from mekanik.core import i18n
from mekanik.plugins import registry

LANG, KEEP = "en", ("num.decimal",)   # KEEP: formatting, not text
_dir: Path | None = None


def pytest_configure(config):
    global _dir
    _dir = Path(tempfile.mkdtemp(prefix="mekanik-pseudo-"))
    registry()                                    # the packages' catalogs too (mech, print3d …)
    texts = {k: v if k in KEEP else f"«{v}»" for k, v in i18n.catalogs()["tr"].items()}
    (_dir / f"{LANG}.yaml").write_text(yaml.safe_dump(texts, allow_unicode=True, width=1000), encoding="utf-8")
    i18n.add_catalog(_dir)
    i18n.set_lang(LANG)


def pytest_unconfigure(config):
    if _dir:
        shutil.rmtree(_dir, ignore_errors=True)
