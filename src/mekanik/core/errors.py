# SPDX-License-Identifier: AGPL-3.0-or-later
"""Error types. Messages are user-facing text rendered from the i18n catalog."""


class MekanikError(Exception):
    """Base class for errors shown to the user."""


class SchemaError(MekanikError, ValueError):
    """A record does not match its schema or a structural rule."""


class GitError(MekanikError, RuntimeError):
    """A git command failed."""
