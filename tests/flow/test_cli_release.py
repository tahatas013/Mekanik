# SPDX-License-Identifier: AGPL-3.0-or-later
"""Criterion 1.8: the old `surec baski` crashed after opening the card (cli/surec_cli/ana.py:144 read a key the
release function did not return: KeyError). The v1 command runs end to end on a real release request."""

from __future__ import annotations

import pytest

pytest.importorskip("cadquery")
pytestmark = pytest.mark.occt

from test_flow import MODEL  # noqa: E402
from test_store import new, prepare, review  # noqa: E402

from mekanik.cli.main import main  # noqa: E402
from mekanik.core.i18n import t  # noqa: E402


def test_release_request_command_does_not_crash(shop, capsys, monkeypatch):
    """new: 1.8 — `mekanik release request` on a work with a model returns 0 and names the opened card."""
    code, d = new()
    prepare(d, model=MODEL)
    review(d)
    monkeypatch.chdir(d)
    assert main(["release", "request"]) == 0
    out = capsys.readouterr().out
    assert t("cli.release", no="01", folder="").split("01")[0] in out and "01" in out
