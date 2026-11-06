# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile type `print3d.fdm` (old veri._uretim_profili_dogrula, v1 names; G-30): clearance.<task>.{lower, upper},
screw_clearance.{source, table}; optional model_correction, print_direction, bed.{x, y, margin}. Values: {value, source}
"""

from __future__ import annotations

from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.params import SOURCE_RE
from mekanik_mech.fits import TASKS, is_number


def _fail(key: str, **kw):
    raise SchemaError(t(f"print3d.profile.{key}", **kw))


def _dict(x, where: str) -> dict:
    if not isinstance(x, dict):
        _fail("not_dict", where=where, got=type(x).__name__)
    return x


def _req(d: dict, key: str, where: str):
    if d.get(key) is None:
        _fail("required", where=where, field=key)
    return d[key]


def _value(x, where: str) -> None:
    x = _dict(x, where)
    if x.get("value") is not None and not is_number(x["value"]):
        _fail("number", where=f"{where}.value", got=x["value"])
    if not SOURCE_RE.match(str(_req(x, "source", where))):
        _fail("source", where=where, source=x["source"])


def validate(p: dict, where: str) -> None:
    c = _dict(_req(p, "clearance", where), f"{where}.clearance")
    tasks = [x for x in TASKS if x != "screw_clearance"]
    if missing := [x for x in tasks if x not in c]:
        _fail("missing_tasks", where=f"{where}.clearance", tasks=", ".join(missing))
    for task in tasks:
        s = _dict(c[task], f"{where}.clearance.{task}")
        for end in ("lower", "upper"):
            _value(_req(s, end, f"{where}.clearance.{task}"), f"{where}.clearance.{task}.{end}")
    sc = _dict(_req(p, "screw_clearance", where), f"{where}.screw_clearance")
    _req(sc, "source", f"{where}.screw_clearance")
    for screw, d in _dict(_req(sc, "table", f"{where}.screw_clearance"), f"{where}.screw_clearance.table").items():
        if not is_number(d):
            _fail("number", where=f"{where}.screw_clearance.table.{screw}", got=d)
    for key in ("model_correction", "print_direction"):
        if key in p:
            _value(p[key], f"{where}.{key}")
    for key, v in _dict(p.get("bed") or {}, f"{where}.bed").items():
        _value(v, f"{where}.bed.{key}")
