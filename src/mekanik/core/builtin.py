# SPDX-License-Identifier: AGPL-3.0-or-later
"""The core's own registration (architecture §4.7): domain-independent checks and card makers, with those of the
evidence module (CALC-01/02, DECISION-01, QUALITY-01 and the consistency and basis cards) and of intake and the
standard map (INTAKE-01/02, STDMAP-01: the G0 preconditions), the phase-2 assurance checks (SOURCE-02, CALC-03/04,
REQ-01) and the policy's threshold suggestion card (D6)."""

from mekanik.core.cards import makers
from mekanik.core.checks.builtin import assurance, source_code
from mekanik.core.checks.builtin import CHECKS as CORE_CHECKS
from mekanik.core.evidence.register import CARD_MAKERS, CHECKS
from mekanik.core.intake import CHECKS as INTAKE_CHECKS
from mekanik.core.policy import metrics
from mekanik.core.stdmap import CHECKS as STDMAP_CHECKS
from mekanik.plugins import PackageSpec

SPEC = PackageSpec(id="core", version="0.1.0", checks=[*CORE_CHECKS, *CHECKS, *INTAKE_CHECKS, *STDMAP_CHECKS,
                                                          *assurance.CHECKS, *source_code.CHECKS],
                   card_makers=[makers.make, *CARD_MAKERS, metrics.suggestions])
