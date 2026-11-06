# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mechanical checks (old kontroller/bagimsiz_sayi, gecme_boslugu, girisim, kayitsiz_gecme, montaj).

Pure functions of a read-only view and the model ({part: solid}); OCCT is imported only by the two geometric
checks, so the fit checks run without it. Limits come from stdlib/rules/mech.yaml and the machine profile.
"""

from __future__ import annotations

from itertools import combinations

from mekanik.core.checks.result import PASS, WARN, Result, level
from mekanik.core.checks.rules import limit
from mekanik.core.i18n import num, t
from mekanik.core.model.params import formula_names

from .fits import dims, fits, flexes, profile

# source: assumption — wipes floating-point noise (17.0 − 16.6 = 0.39999…) at 1e-9 mm; not an engineering value
ROUND = 9


def _r(check: str, rule: str, status: str, key: str, ref=None, value=None, extra=None, **args) -> Result:
    return Result(f"mech.{check}", rule, status, f"mech.{key}", args, ref, value, extra or {})


def independent_number(view, model=None, cards=None) -> list[Result]:
    """FIT-01: the two sides of a fit are not two independent constants; one derives from the other.
    Passes: nominal + clearance; a derived side whose formula rests on the other side; a screw clearance hole."""
    out, fail = [], level(view)

    def rests(child: str, parent: str) -> bool:
        p = view.params[child]
        return p.source == "derived" and parent in formula_names(p.formula)

    for f in fits(view):
        s, fid = f["sides"], f["id"]
        if s is None:
            ok = f["clearance"] is not None
            out.append(_r("independent_number", "FIT-01", PASS if ok else fail,
                          "fit01.nominal" if ok else "fit01.no_clearance", fid, fit=fid))
        elif "hole" in s and "shaft" in s:
            h, m = s["hole"], s["shaft"]
            if rests(m, h) or rests(h, m):
                out.append(_r("independent_number", "FIT-01", PASS, "fit01.derived", fid, fit=fid))
            else:
                out.append(_r("independent_number", "FIT-01", fail, "fit01.independent", fid, fit=fid, hole=h, shaft=m,
                              hole_value=num(view.params[h].value), shaft_value=num(view.params[m].value)))
        elif f["task"] == "screw_clearance" and "hole" in s:
            out.append(_r("independent_number", "FIT-01", PASS, "fit01.screw", fid, fit=fid))
        else:
            out.append(_r("independent_number", "FIT-01", fail, "fit01.one_side", fid, fit=fid,
                          side=t(f"mech.side.{next(iter(s))}")))
    return out


def fit_clearance(view, model=None, cards=None) -> list[Result]:
    """FIT-02: clearance within the profile band of the fit's task; BOLT-01: screw hole as in the profile table."""
    out, fail, prof = [], level(view), profile(view)
    for f in fits(view):
        fid, task = f["id"], f["task"]
        hole, shaft = dims(f, view.params)
        if task is None:
            out.append(_r("fit_clearance", "FIT-02", fail, "fit02.no_task", fid, extra={"undefined": "task"}, fit=fid))
            continue
        if task == "screw_clearance":
            sc = prof.get("screw_clearance") or {}
            target = (sc.get("table") or {}).get(f["screw"])
            args = dict(fit=fid, screw=f["screw"], hole=num(hole), source=sc.get("source", "—"))
            if target is None:
                out.append(_r("fit_clearance", "BOLT-01", fail, "bolt01.no_table", fid, extra={"undefined": "screw"},
                              **args))
            elif hole is not None and round(hole - target, ROUND) == 0:
                out.append(_r("fit_clearance", "BOLT-01", PASS, "bolt01.pass", fid, hole, **args))
            else:
                out.append(_r("fit_clearance", "BOLT-01", fail, "bolt01.outside", fid, hole, target=num(target),
                              **args))
            continue
        lim = (prof.get("clearance") or {}).get(task) or {}
        lo, hi = (lim.get("lower") or {}).get("value"), (lim.get("upper") or {}).get("value")
        name = t(f"mech.task.{task}")
        if lo is None or hi is None:
            out.append(_r("fit_clearance", "FIT-02", fail, "fit02.no_limit", fid, extra={"undefined": "limit"}, fit=fid,
                          task=name, source=(lim.get("lower") or {}).get("source", "—")))
        elif hole is None or shaft is None:
            out.append(_r("fit_clearance", "FIT-02", fail, "fit02.missing", fid, fit=fid))
        else:
            c = round(hole - shaft, ROUND)
            args = dict(fit=fid, clearance=num(c), task=name, band=f"{num(lo)}–{num(hi)}")
            if lo <= c <= hi:
                out.append(_r("fit_clearance", "FIT-02", PASS, "fit02.pass", fid, c, **args))
            else:
                out.append(_r("fit_clearance", "FIT-02", fail, "fit02.outside", fid, c, sign=">" if c > hi else "<",
                              bound=num(hi if c > hi else lo), **args))
    return out


def interference(view, model=None, cards=None) -> list[Result]:
    """SOLID-01: every part is a valid closed solid; INTERF-01: no two parts intersect (manifold3d)."""
    fail = level(view)
    if not model:
        return [_r("interference", "SOLID-01", fail, "solid01.no_model")]
    from . import geom

    out, solids = [], {}
    for name, s in model.items():
        mf, brep, closed = geom.closed_solid(s)
        if mf is not None:
            solids[name] = mf
            out.append(_r("interference", "SOLID-01", PASS, "solid01.pass", name, part=name))
        else:
            out.append(_r("interference", "SOLID-01", fail, "solid01.fail", name, part=name, brep=brep, closed=closed))
    for a, b in combinations(solids, 2):
        v = (solids[a] ^ solids[b]).volume()
        ok = v <= limit("INTERF-01", "volume")
        out.append(_r("interference", "INTERF-01", PASS if ok else fail, "interf01.pass" if ok else "interf01.fail",
                      f"{a}-{b}", v, a=a, b=b, volume=f"{v:.3f}"))
    return out


def _registered(view, a: str, b: str, da: float, db: float, tol: float) -> str | None:
    for f in fits(view):
        if set(f["parts"]) == {a, b}:
            if any(abs(x - y) <= tol for x in dims(f, view.params) if x is not None for y in (da, db)):
                return f["id"]
    return None


def unregistered_fit(view, model=None, cards=None) -> list[Result]:
    """UNREG-01: coaxial cylinder pairs of different parts with close diameters are in the fit record (warn only)."""
    if not model:
        return [_r("unregistered_fit", "UNREG-01", WARN, "unreg01.no_model")]
    from . import geom

    tol = {k: limit("UNREG-01", k) for k in ("diameter_diff", "angle_deg", "axis_distance", "match")}
    cyl = {name: geom.cylinders(s, tol) for name, s in model.items()}
    out = []
    for a, b in combinations(cyl, 2):
        for x in cyl[a]:
            for y in cyl[b]:
                if not geom.coaxial(x, y, tol) or abs(x["d"] - y["d"]) >= tol["diameter_diff"]:
                    continue
                fid = _registered(view, a, b, x["d"], y["d"], tol["match"])
                pair = dict(a=a, da=f"{x['d']:.2f}", b=b, db=f"{y['d']:.2f}")
                if fid:
                    out.append(_r("unregistered_fit", "UNREG-01", PASS, "unreg01.registered", fid, fit=fid, **pair))
                else:
                    out.append(_r("unregistered_fit", "UNREG-01", WARN, "unreg01.unregistered", f"{a}-{b}",
                                  extra={"diameters": [x["d"], y["d"]]}, **pair))
    return out or [_r("unregistered_fit", "UNREG-01", PASS, "unreg01.none")]


def assembly(view, model=None, cards=None) -> list[Result]:
    """ASSY-01: every assembly flex has a valid chief-engineer approval (tool access is not checked yet)."""
    from mekanik.core.cards import approval

    out = []
    for e in flexes(view):
        eid = e["id"]
        card = next((c["id"] for c in view.cards if c.get("key") == f"flex:{eid}"), eid)
        st = approval.state(view, card, {"flex": eid})
        args = dict(flex=eid, part=e.get("part", "?"), location=e.get("location", ""), amount=num(e.get("value")),
                    unit=e.get("unit", "mm"))
        if st == "approved":
            out.append(_r("assembly", "ASSY-01", PASS, "assy01.pass", eid, e.get("value"), **args))
        else:
            out.append(_r("assembly", "ASSY-01", level(view), "assy01.fail", eid, e.get("value"), {"state": st},
                          state=t(f"mech.assy01.state.{st}"), **args))
    return out or [_r("assembly", "ASSY-01", PASS, "assy01.none")]
