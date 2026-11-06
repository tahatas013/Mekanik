# SPDX-License-Identifier: AGPL-3.0-or-later
"""Intake (architecture §7, part C): work type (`trees`), question tree engine (`engine`), findings (`findings`) and
the understanding summary with its G0 precondition check (`summary`). Imported lazily by the core registration."""

from mekanik.plugins import CheckSpec


def _check(view, model=None):
    from .summary import check

    return check(view, model)


CHECKS = [CheckSpec("intake", _check, ("INTAKE-01", "INTAKE-02"), order=8)]
