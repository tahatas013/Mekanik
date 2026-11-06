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
    """`kind` is a schema name (work, agent_run …) or a fragment of one (config#/$defs/organization)."""
    name, _, frag = kind.partition("#")
    ref = f"urn:mekanik:schema:v1:{name.replace('_', '-')}" + (f"#{frag}" if frag else "")
    return Draft202012Validator({"$ref": ref}, registry=_registry(), format_checker=FormatChecker())


@cache
def required_later() -> dict[str, frozenset[str]]:
    doc = yamlio.read(data.stdlib("strictness", "phase1.yaml"), {})
    return {k: frozenset(v) for k, v in (doc.get("required_later") or {}).items()}


def errors(kind: str, doc) -> list:
    """All schema errors of `doc`, in path order (jsonschema ValidationError objects)."""
    return sorted(_validator(kind).iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))


def _later_key(e) -> str | None:
    """'field' at top level, 'a/*/field' below it (list indices become *); None if not a missing-field error."""
    m = _REQ.match(e.message) if e.validator == "required" else None
    return m and "/".join(["*" if isinstance(x, int) else str(x) for x in e.absolute_path] + [m.group(1)])


def validate(kind: str, doc, where: str) -> list[str]:
    """Validate `doc`; raise SchemaError on a hard error, return the soft (phase-1) findings as warnings."""
    later = required_later().get(kind, frozenset())
    warnings = []
    for e in errors(kind, doc):
        if (key := _later_key(e)) in later:
            warnings.append(t("schema.later_required", where=where, field=key))
            continue
        path = "/".join(map(str, e.absolute_path)) or "."
        raise SchemaError(t("schema.invalid", where=where, path=path, error=e.message))
    return warnings
