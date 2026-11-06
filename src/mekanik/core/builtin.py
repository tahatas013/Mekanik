# SPDX-License-Identifier: AGPL-3.0-or-later
"""The core's own registration (architecture §4.7): domain-independent checks and card makers, with those of the
evidence module (CALC-01/02, DECISION-01, QUALITY-01 and the consistency and basis cards)."""

from mekanik.core.cards import makers
from mekanik.core.checks.builtin import CHECKS as CORE_CHECKS
from mekanik.core.evidence.register import CARD_MAKERS, CHECKS
from mekanik.plugins import PackageSpec

SPEC = PackageSpec(id="core", version="0.1.0", checks=[*CORE_CHECKS, *CHECKS],
                   card_makers=[makers.make, *CARD_MAKERS])
