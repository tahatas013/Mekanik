# SPDX-License-Identifier: AGPL-3.0-or-later
"""Migration of old `surec` works and workshop data to v1 (architecture §14): dry run, V1–V8; --apply is phase 2."""

from .convert import Phase2Error, surec_config, surec_work  # noqa: F401
from .verify import verify, verify_config  # noqa: F401
