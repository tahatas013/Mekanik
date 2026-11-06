# SPDX-License-Identifier: AGPL-3.0-or-later
"""Flow tests with the domain packages (mech, print3d) and OCCT: the shop fixture of tests/core/test_store.py, the
registry from the installed entry points."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

from test_store import gpg_keys, shop  # noqa: E402,F401


@pytest.fixture(autouse=True)
def _packages():
    from mekanik.plugins import reset_registry

    reset_registry()
    yield
    reset_registry()
