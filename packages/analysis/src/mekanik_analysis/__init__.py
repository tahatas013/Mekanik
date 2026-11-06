# SPDX-License-Identifier: AGPL-3.0-or-later
"""mekanik analysis package."""

from pathlib import Path

from mekanik.plugins import PackageSpec

SPEC = PackageSpec(id="analysis", version="0.1.0", i18n=Path(__file__).parent / "i18n")
