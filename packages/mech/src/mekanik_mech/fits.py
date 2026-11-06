# SPDX-License-Identifier: AGPL-3.0-or-later
"""fits.yaml: fit records, assembly flexes and tool access (old `veri.py` fit part: gecmeler_yukle,
gecme_olculeri, _montaj_dogrula) and what the core asks the package for: param uses, critical dimensions,
sourced values and card subject values. No OCCT here.

Clearance limits and the screw table come from the machine profile (`view.manufacturing["profile"]`):
`clearance.<task>.{lower, upper}` value records and `screw_clearance.{source, table}`. mech defines this
interface; a profile type (print3d.fdm) validates it.
"""

from __future__ import annotations

import re
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.params import SOURCE_RE, formula_names
from mekanik.plugins import CriticalDim, SourcedValue

TASKS = ("centering", "rotation", "sliding", "press", "screw_clearance", "abutment")
_FIT = {"id": None, "parts": None, "task": None, "nominal": None, "clearance": None, "sides": None, "screw": None,
        "limit_source": None, "critical": False, "note": ""}


def _fail(key: str, **kw):
    raise SchemaError(t(f"mech.fits.{key}", **kw))


def is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _fit(k, i: int, params: dict, seen: set) -> dict:
    if not isinstance(k, dict):
        _fail("not_dict", where=f"fits.yaml:fits[{i}]", got=type(k).__name__)
    if k.get("id") is None:
        _fail("required", where=f"fits.yaml:fits[{i}]", field="id")
    f = {**_FIT, **{a: k[a] for a in _FIT if k.get(a) is not None}}
    w = f"fits.yaml:{f['id']}"
    if not re.fullmatch(r"G-\d{2}", str(f["id"])):
        _fail("fit_id", where=w)
    if f["id"] in seen:
        _fail("duplicate", where=w)
    seen.add(f["id"])
    if not (isinstance(f["parts"], list) and len(f["parts"]) == 2 and all(isinstance(x, str) for x in f["parts"])):
        _fail("parts", where=w)
    if f["task"] is not None and f["task"] not in TASKS:
        _fail("task", where=w, task=f["task"], accepted=", ".join(TASKS))
    s = f["sides"]
    if s is not None:
        if not isinstance(s, dict) or not s or set(s) - {"hole", "shaft"}:
            _fail("sides", where=w)
        if f["nominal"] is not None or f["clearance"] is not None:
            _fail("sides_or_nominal", where=w)
    elif f["nominal"] is None:
        _fail("nominal", where=w)
    if not isinstance(f["critical"], bool):
        _fail("critical", where=w)
    if f["task"] == "screw_clearance" and not f["screw"]:
        _fail("screw", where=w)
    for ref in side_names(f):
        if ref not in params:
            _fail("unknown_param", where=w, param=ref)
    return f


def _flex(e, i: int) -> dict:
    if not isinstance(e, dict):
        _fail("not_dict", where=f"fits.yaml:flexes[{i}]", got=type(e).__name__)
    if e.get("id") is None:
        _fail("required", where=f"fits.yaml:flexes[{i}]", field="id")
    w = f"fits.yaml:{e['id']}"
    if not re.fullmatch(r"E-\d{2}", str(e["id"])):
        _fail("flex_id", where=w)
    if e.get("value") is not None and not is_number(e["value"]):
        _fail("number", where=f"{w}.value", got=e["value"])
    if e.get("source") is not None and not SOURCE_RE.match(str(e["source"])):
        _fail("source", where=w, source=e["source"])
    return e


def load(root: Path, view) -> dict:
    """Loader of `view.ext["mech"]`: {fits, flexes, tool_access}. A missing file is an empty record."""
    doc = yamlio.read(Path(root) / "fits.yaml", {})
    if not isinstance(doc, dict):
        _fail("not_dict", where="fits.yaml", got=type(doc).__name__)
    for key in ("fits", "flexes", "tool_access"):
        if not isinstance(doc.get(key) or [], list):
            _fail("not_list", where=f"fits.yaml:{key}", got=type(doc[key]).__name__)
    seen: set = set()
    return {"fits": [_fit(k, i, view.params, seen) for i, k in enumerate(doc.get("fits") or [])],
            "flexes": [_flex(e, i) for i, e in enumerate(doc.get("flexes") or [])],
            "tool_access": list(doc.get("tool_access") or [])}


def fits(view) -> list[dict]:
    return (view.ext.get("mech") or {}).get("fits", [])


def flexes(view) -> list[dict]:
    return (view.ext.get("mech") or {}).get("flexes", [])


def profile(view) -> dict:
    return (view.manufacturing or {}).get("profile") or {}


def side_names(f: dict) -> list[str]:
    return [a for a in [f["nominal"], f["clearance"], *(f["sides"] or {}).values()] if a]


def dims(f: dict, params: dict) -> tuple[float | None, float | None]:
    """(hole, shaft). A nominal + clearance record gives hole = nominal, shaft = nominal − clearance."""
    s = f["sides"]
    if s:
        return (params[s["hole"]].value if "hole" in s else None, params[s["shaft"]].value if "shaft" in s else None)
    d = params[f["nominal"]].value
    if f["clearance"] is None or d is None or params[f["clearance"]].value is None:
        return d, None
    return d, d - params[f["clearance"]].value


def band(view, task: str | None) -> float | None:
    lim = (profile(view).get("clearance") or {}).get(task or "") or {}
    lo, hi = (lim.get("lower") or {}).get("value"), (lim.get("upper") or {}).get("value")
    return None if lo is None or hi is None else hi - lo


def param_uses(view) -> dict[str, list[str]]:
    """Param → fits it enters (old gecmeye_girenler). A derived side brings the values its formula rests on."""
    out: dict[str, list[str]] = {}
    for f in fits(view):
        todo, seen = side_names(f), set()
        while todo:
            a = todo.pop()
            if a in seen or a not in view.params:
                continue
            seen.add(a)
            out.setdefault(a, []).append(f["id"])
            if view.params[a].formula:
                todo += list(formula_names(view.params[a].formula))
    return out


def critical_dims(view) -> list[CriticalDim]:
    """Measured values of critical fits; band = profile clearance.<task>.upper − lower (UNCERT-01)."""
    out = []
    for f in fits(view):
        if f["critical"]:
            for a in dict.fromkeys(x for x in [f["nominal"], *(f["sides"] or {}).values()] if x):
                if view.params[a].measured:
                    out.append(CriticalDim(f["id"], a, band(view, f["task"]), f["task"]))
    return out


def sourced_values(view) -> list[SourcedValue]:
    """Assembly flexes: SOURCE-01 checks their source like a parameter's."""
    return [SourcedValue(e["id"], e.get("value"), e.get("unit", "mm"), e.get("source")) for e in flexes(view)]


def subject_values(view, subject: dict) -> dict | None:
    """Snapshot of a fit or flex subject (old onay.konu_degerleri, fit and flex part). A fit carries the profile
    limit of its task, so a changed limit drops the approval. The core adds the `params` part."""
    out: dict = {}
    if fid := subject.get("fit"):
        f = next((x for x in fits(view) if x["id"] == fid), None)
        out[f"fit:{fid}"] = f
        if f is not None:
            m, p = view.manufacturing or {}, profile(view)
            out["profile"] = {"id": m.get("id"), "version": m.get("version"), "status": m.get("status"),
                              "limit": p.get("screw_clearance") if f["task"] == "screw_clearance"
                              else (p.get("clearance") or {}).get(f["task"] or "")}
    if eid := subject.get("flex"):
        out[f"flex:{eid}"] = next((e for e in flexes(view) if e.get("id") == eid), None)
    return out or None
