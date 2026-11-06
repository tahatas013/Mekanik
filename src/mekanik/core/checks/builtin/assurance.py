# SPDX-License-Identifier: AGPL-3.0-or-later
"""Assurance checks of phase 2 (architecture §10.2, §10.3, §10.6):
- CALC-03: a critical calculation has an independent second method agreeing within the catalog limit (per
  magnitude; default relative 10 %, Ö-22). Critical: declared (`critical`), or made so by the records — evidence of a
  mandatory requirement, basis of a hold decision, fed by a safety-critical value; the stricter wins. Independent:
  another calc reports the same magnitude with another method level, or with another method and no shared derived
  input; neither reads the other's record (no shared intermediate result). Missing or disagreeing: block.
- CALC-04: a calc used as evidence or basis is no evidence outside its validity domain (block), nor in the limits
  zone without the chief's placard approval (block); verification-only and an undefined domain warn; every result
  states its uncertainty (quantitative, qualitative or none_available, [M&S 33]) or blocks.
- REQ-01: at the gates of the catalog limit (G4, G5) every mandatory requirement is met (status from the evidence:
  a 'met' resting only on evidence these checks refuse is awaiting evidence)."""

from __future__ import annotations

import math

from mekanik.plugins import CheckSpec

from ... import yamlio
from ...evidence import calc
from ..result import BLOCK, PASS, WARN, Result
from ..rules import limit, rule

CALC_REFS = ("calculation", "analysis")
NOTES = ("quantitative", "qualitative", "none_available")


def _evidence(view) -> list[dict]:
    return yamlio.read(view.root / "evidence.yaml", []) or []


def _refs(r: dict) -> list[dict]:
    return [x for k in ("verification", "evaluation") for x in (r.get(k) or {}).get("evidence") or []]


def uses(view) -> dict[str, list[str]]:
    """Calc id → where it is evidence or basis: requirement R-nn, evidence record EV-nnn, decision K-nn."""
    out: dict[str, list[str]] = {}
    for r in view.requirements:
        for x in _refs(r):
            if x.get("kind") in CALC_REFS:
                out.setdefault(x["id"], []).append(r["id"])
    for e in _evidence(view):
        if (e.get("record") or {}).get("kind") in CALC_REFS:
            out.setdefault(e["record"]["id"], []).append(e["id"])
    for d in view.decisions:
        for b in d.get("basis") or []:
            out.setdefault(b["calculation"], []).append(d["id"])
    return out


def critical(view, recs: dict) -> dict[str, str]:
    """Calc id → why it is critical (declared, R-nn, EV-nnn, K-nn, safety)."""
    must = {r["id"] for r in view.requirements if r.get("kind") == "mandatory" and r.get("status") != "withdrawn"}
    ev = {e["id"] for e in _evidence(view) if {s.get("target") for s in e.get("supports") or []} & must}
    holds, out = {d["id"] for d in view.decisions if d.get("mode") == "hold"}, {}
    for cid, where in uses(view).items():
        if why := next((w for w in where if w in must | ev | holds), None):
            out[cid] = why
    for cid, rec in recs.items():
        if rec.get("critical"):
            out[cid] = "declared"
        elif cid not in out and any((p := view.params.get(i["name"])) and p.critical == "safety"
                                    for i in rec.get("inputs") or []):
            out[cid] = "safety"
    return out


def _derived(rec: dict) -> set[str]:
    return {i["name"] for i in rec.get("inputs") or [] if i["quantity"].get("source") == "derived"}


def _independent(a: dict, ma: dict, b: dict, mb: dict) -> bool:
    if a["id"] in (b.get("read_calculations") or []) or b["id"] in (a.get("read_calculations") or []):
        return False
    if ma["level"] != mb["level"]:
        return True
    return ma["method"].strip().lower() != mb["method"].strip().lower() and not _derived(a) & _derived(b)


def _limit(name: str) -> float:
    return ((rule("CALC-03").get("limit") or {}).get("magnitudes") or {}).get(name, limit("CALC-03", "relative"))


def cross_check(recs: dict, cid: str) -> dict:
    """{status: agree | disagree | missing, with, magnitude, difference, limit}: the worst independent pair."""
    rec, found = recs[cid], []
    for m in [] if rec.get("error") else rec.get("magnitudes") or []:
        for oid, o in recs.items():
            for om in [] if oid == cid or o.get("error") else o.get("magnitudes") or []:
                if om["name"] == m["name"] and _independent(rec, m, o, om):
                    diff = abs(om["value"] - m["value"]) / abs(m["value"]) if m["value"] else (
                        0.0 if om["value"] == m["value"] else math.inf)
                    found.append({"with": oid, "magnitude": m["name"], "difference": diff, "limit": _limit(m["name"])})
    if not found:
        return {"status": "missing"}
    worst = max(found, key=lambda x: x["difference"] - x["limit"])
    bad = worst["difference"] > worst["limit"] or (rec.get("cross_check") or {}).get("status") == "disagree"
    return {**worst, "status": "disagree" if bad else "agree"}


def _pct(x) -> str:
    return "—" if x is None else "∞" if math.isinf(x) else f"{x * 100:.0f}"


def cross(view, model=None) -> list[Result]:
    """CALC-03."""
    recs, out = calc.recorded(view.root), []
    for cid, why in sorted(critical(view, recs).items()):
        x = cross_check(recs, cid) if cid in recs else {"status": "no_record"}
        args = {"calc": cid, "why": why, "other": x.get("with", "—"), "name": x.get("magnitude", "—"),
                "diff": _pct(x.get("difference")), "limit": _pct(x.get("limit"))}
        out.append(Result("calc_cross_check", "CALC-03", PASS if x["status"] == "agree" else BLOCK,
                          f"policy.calc03.{x['status']}", args, cid, x.get("difference"), extra=x))
    return out or [Result("calc_cross_check", "CALC-03", PASS, "policy.calc03.none")]


def validity(view, model=None) -> list[Result]:
    """CALC-04 and the uncertainty statement of the results used as evidence or basis."""
    recs, out = calc.recorded(view.root), []
    off = {e["record"]["id"] for e in _evidence(view) if (e.get("validity") or {}).get("in_domain") is False}
    for cid, where in sorted(uses(view).items()):
        if (rec := recs.get(cid)) is None:
            continue
        v = rec.get("validity") or {}
        zone = "outside" if v.get("in_domain") is False or cid in off else v.get("zone") or "undefined"
        quiet = [r["name"] for r in rec.get("results") or [] if r.get("uncertainty_note") not in NOTES]
        if zone == "limits" and (v.get("placard") or {}).get("approved"):
            zone = "limits_approved"
        status = BLOCK if quiet or zone in ("outside", "limits") else PASS if zone == "validation" else WARN
        out.append(Result("calc_validity", "CALC-04", status, f"policy.calc04.{'uncertainty' if quiet else zone}",
                          {"calc": cid, "where": ", ".join(where), "results": ", ".join(quiet)}, cid,
                          extra={"zone": zone, "uses": where}))
    return out or [Result("calc_validity", "CALC-04", PASS, "policy.calc04.none")]


def invalid(view) -> dict[str, str]:
    """Calc id → the CALC-03/CALC-04 block that keeps a recorded calc from being evidence."""
    recs = calc.recorded(view.root)
    return {r.ref: r.msg for r in [*cross(view), *validity(view)] if r.status == BLOCK and r.ref in recs}


def requirement_table(view) -> list[dict]:
    """Per requirement: met | not_met | awaiting_evidence and the evidence (B2, §10.6); 'met' needs evidence that
    CALC-03/CALC-04 accept, else it is awaiting evidence."""
    out, bad = [], invalid(view)
    for r in view.requirements:
        refs = (ev := r.get("evaluation") or {}).get("evidence") or (r.get("verification") or {}).get("evidence")
        good = [x for x in refs or [] if not (x.get("kind") in CALC_REFS and x.get("id") in bad)]
        st = "awaiting_evidence" if (st := ev.get("status", "awaiting_evidence")) == "met" and not good else st
        out.append({"requirement": r["id"], "status": st, **({"evidence": refs} if refs else {})})
    return out


def requirements(view, model=None) -> list[Result]:
    """REQ-01, applied while the work is at one of the catalog's gates."""
    if view.stage not in limit("REQ-01", "gates"):
        return []
    table, out = {x["requirement"]: x["status"] for x in requirement_table(view)}, []
    for r in (r for r in view.requirements if r.get("kind") == "mandatory" and r.get("status") != "withdrawn"):
        st = table[r["id"]]
        out.append(Result("requirements_met", "REQ-01", PASS if st == "met" else BLOCK, f"policy.req01.{st}",
                          {"id": r["id"], "gate": view.stage, "text": r.get("text", "")}, r["id"]))
    return out or [Result("requirements_met", "REQ-01", PASS, "policy.req01.none", {"gate": view.stage})]


CHECKS = [CheckSpec("calc_cross_check", cross, ("CALC-03",), order=82),
          CheckSpec("calc_validity", validity, ("CALC-04",), order=84),
          CheckSpec("requirements_met", requirements, ("REQ-01",), order=92)]
