# SPDX-License-Identifier: AGPL-3.0-or-later
"""Process flow (old `akis.py`): each public function is what one `mekanik` subcommand calls (§4.11)."""

from ..errors import MekanikError
from ..i18n import t


class Refused(MekanikError):
    """A refused action; `key` is its catalog key and `data` its values (tests read these, not the text)."""

    def __init__(self, key: str, **data):
        super().__init__(t(key, **data))
        self.key, self.data = key, data


def refuse(cond, key: str, **data) -> None:
    """Raise Refused(key) when `cond` holds."""
    if cond:
        raise Refused(key, **data)
