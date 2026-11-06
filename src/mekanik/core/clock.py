# SPDX-License-Identifier: AGPL-3.0-or-later
"""System clock (architecture §4.13). Every timestamp in a record comes from here; none is typed by hand."""

from __future__ import annotations

from datetime import datetime


def now() -> str:
    """ISO 8601 with the local UTC offset, second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return datetime.now().astimezone().date().isoformat()


def minutes_since(stamp: str) -> int:
    return int((datetime.now().astimezone() - datetime.fromisoformat(stamp)).total_seconds() // 60)
