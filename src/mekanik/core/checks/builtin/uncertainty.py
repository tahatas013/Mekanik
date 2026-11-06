# SPDX-License-Identifier: AGPL-3.0-or-later
"""UNCERT-01: on a critical dimension, measurement uncertainty ≤ tolerance band / 4 (ISO 14253-1, Z540.3 4:1),
and an instrument valid only for form is not used (old `olcme_belirsizligi.py`, OLCU-01 and OLCU-02).

Packages report the critical dimensions (`critical_dims`); the instrument comes from the parameter's source."""

from __future__ import annotations

from mekanik.plugins import registry

from ...i18n import num, t
from ..result import PASS, Result, level
from ..rules import limit

RULE = "UNCERT-01"
DIGITS = 9   # source: assumption — floating-point noise when comparing U with band/4, not an engineering value


def run(view, model=None) -> list[Result]:
    out = []
    ratio = limit(RULE, "ratio")
    for d in registry().collect("critical_dims", view):
        p = view.params.get(d.param)
        if p is None or not p.measured:
            continue
        inst = view.instruments[p.instrument]
        unc = inst["uncertainty"]
        u = unc["value"]
        cases = []
        if not inst["valid_for"]["critical_dimension"]:
            cases.append(("form_only", {"instrument": p.instrument}))
        if d.band is None:
            cases.append(("no_band", {"task": d.task or "—"}))
        elif round(u - d.band / ratio, DIGITS) > 0:
            u_text = t("checks.uncertainty.u_min" if unc.get("lower_bound") else "checks.uncertainty.u", u=num(u))
            cases.append(("ratio", {"u": u_text, "band": num(d.band), "ratio": ratio, "limit": num(d.band / ratio)}))
        head = {"ref": d.ref, "param": p.name}
        if cases:
            detail = "; ".join(t(f"checks.uncertainty.{c}", **a) for c, a in cases)
            out.append(Result("uncertainty", RULE, level(view), "checks.uncertainty.fail", {**head, "detail": detail},
                              d.ref, u, {"param": p.name, "instrument": p.instrument, "cases": [c for c, _ in cases]}))
            continue
        borderline = round(u - d.band / ratio, DIGITS) == 0
        assumed = unc.get("source") == "assumption"
        notes = [t(f"checks.uncertainty.{n}") for n, on in (("borderline", borderline), ("assumed", assumed)) if on]
        out.append(Result("uncertainty", RULE, PASS, "checks.uncertainty.ok",
                          {**head, "u": num(u), "band": num(d.band), "ratio": ratio,
                           "notes": t("checks.uncertainty.notes", notes=", ".join(notes)) if notes else ""},
                          d.ref, u, {"param": p.name, "instrument": p.instrument, "borderline": borderline,
                                     "assumed": assumed}))
    return out or [Result("uncertainty", RULE, PASS, "checks.uncertainty.none")]
