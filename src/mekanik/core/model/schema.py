# SPDX-License-Identifier: AGPL-3.0-or-later
"""JSON Schema validation of records (schemas/v1) with the phase-1 strictness list (phase-1 guide G-27)."""

from __future__ import annotations

import json
import re
from functools import cache

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .. import data, yamlio
from ..errors import SchemaError
from ..i18n import t

_REQ = re.compile(r"^'([^']+)' is a required property$")


@cache
def _registry() -> Registry:
    reg = Registry()
    for f in sorted(data.schemas().glob("*.schema.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        reg = reg.with_resource(doc["$id"], Resource.from_contents(doc))
    return reg


@cache
def _validator(kind: str) -> Draft202012Validator:
    doc = json.loads(data.schemas(f"{kind.replace('_', '-')}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(doc, registry=_registry(), format_checker=FormatChecker())


@cache
def required_later() -> dict[str, frozenset[str]]:
    doc = yamlio.read(data.stdlib("strictness", "phase1.yaml"), {})
    return {k: frozenset(v) for k, v in (doc.get("required_later") or {}).items()}


def validate(kind: str, doc, where: str) -> list[str]:
    """Validate `doc`; raise SchemaError on a hard error, return the soft (phase-1) findings as warnings."""
    later = required_later().get(kind, frozenset())
    warnings = []
    for e in sorted(_validator(kind).iter_errors(doc), key=lambda e: list(map(str, e.absolute_path))):
        m = _REQ.match(e.message) if e.validator == "required" else None
        if m and not e.absolute_path and m.group(1) in later:
            warnings.append(t("schema.later_required", where=where, field=m.group(1)))
            continue
        path = "/".join(map(str, e.absolute_path)) or "."
        raise SchemaError(t("schema.invalid", where=where, path=path, error=e.message))
    return warnings
