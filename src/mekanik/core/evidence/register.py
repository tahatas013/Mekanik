# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checks and card makers of the evidence module (old `kontroller/hesap_tutarliligi.py`; the consistency and basis
cards of `kartlar.py`). CALC-01: a magnitude differs between calcs beyond the catalog limit → consistency card.
CALC-02: a bad or unreliable result → warn. DECISION-01: a decision's basis calc changed or was superseded → basis
card. QUALITY-01: the request steps call quality.require_clear; `quality_gate` guards the open gate/release cards."""

from __future__ import annotations

from collections import Counter

from mekanik.plugins import CheckSpec

from ..cards import approval, check_items
from ..checks.result import BLOCK, PASS, WARN, Result
from ..checks.rules import limit
from ..errors import SchemaError
from ..i18n import num, t
from ..quality import current, open_high
from . import calc


def _subject(d: dict) -> dict:
    return {"magnitude": d["name"],
            "results": {x["calc"]: round(x["value"], calc.DIGITS) for x in [d["base"], *d["diffs"]]}}


def _accepted(view, key: str, subject: dict) -> str | None:
    """Id of the card the chief engineer approved with these very values (old onay_durumu == 'onayli')."""
    card = next((c for c in view.cards if c.get("key") == key), None)
    return card["id"] if card and approval.state(view, card["id"], subject) == "approved" else None


def _items(d: dict) -> str:
    return "; ".join(t("evidence.calc01.item", calc=f["calc"], method=f["method"], value=num(f["value"], 4),
                       pct=f"{f['diff'] * 100:+.0f}") for f in d["diffs"])


def run(view, model=None, cards=None) -> list[Result]:
    recs, warns = calc.recorded(view.root), []
    for rec in recs.values():
        try:
            texts = calc.check_schema(rec)
        except SchemaError as e:
            texts = [str(e)]
        warns += [Result("schema", "SCHEMA-01", WARN, "schema.warning", {"text": w}) for w in texts]
    rel = limit("CALC-01", "relative")
    pct, diffs = f"{rel * 100:g}", calc.inconsistencies(recs, rel)
    counts = Counter(m["name"] for r in recs.values() for m in r.get("magnitudes", []))
    out = [Result("calc_consistency", "CALC-01", PASS, "evidence.calc01.within", {"name": n, "limit": pct}, ref=n)
           for n, k in sorted(counts.items()) if k >= 2 and n not in {d["name"] for d in diffs}]
    superseded = {f["calc"] for d in diffs for f in d["diffs"] if f["level"] < d["base"]["level"]}
    for d in diffs:
        b, name, extra = d["base"], d["name"], {"consistency": d, "limit": pct}
        if card := _accepted(view, f"consistency:{name}", _subject(d)):
            out.append(Result("calc_consistency", "CALC-01", PASS, "evidence.calc01.accepted",
                              {"name": name, "card": card, "base": b["calc"]}, name, extra=extra | {"accepted": card}))
        else:
            out.append(Result("calc_consistency", "CALC-01", WARN, "evidence.calc01.differs",
                              {"name": name, "items": _items(d), "base": b["calc"], "method": b["method"],
                               "value": num(b["value"], 4)}, name, extra=extra))
    out += [Result("calc_result", "CALC-02", WARN, "evidence.calc02.bad",
                   {"title": x["title"], "name": x["name"], "value": num(x["value"]), "unit": x["unit"] or "",
                    "status": t(f"evidence.status.{x['status']}")}, x["calc"], extra={"result": x})
            for x in calc.bad_results(recs)]
    for k in (k for k in view.decisions if k.get("status") not in (None, "proposed") and k.get("basis")):
        basis = {x["calculation"]: x.get("result_hash") for x in k["basis"]}
        changed = [a for a, h in basis.items() if h and a in recs and calc.result_hash(recs[a]) != h]
        gone = [a for a in basis if a in superseded]
        items = [t("evidence.decision01.result_changed", calc=a) for a in changed]
        items += [t("evidence.decision01.superseded", calc=a) for a in gone]
        out.append(Result("decision_basis", "DECISION-01", WARN, "evidence.decision01.changed",
                          {"id": k["id"], "items": "; ".join(items)}, k["id"],
                          extra={"decision": k["id"], "changed": changed, "superseded": gone}) if items else
                   Result("decision_basis", "DECISION-01", PASS, "evidence.decision01.same", {"id": k["id"]}, k["id"]))
    return warns + (out or [Result("calc_consistency", "CALC-01", PASS, "evidence.calc01.none")])


def quality_gate(view, model=None, cards=None) -> list[Result]:
    """QUALITY-01 on open gate and release cards: no open high finding in the report of today's inputs."""
    gates = [k for k in (view.cards if cards is None else cards)
             if k.get("type") in ("gate", "release") and k.get("status") == "open"]
    high = open_high(cur[1]) if gates and (cur := current(view.root)) else []
    key = "evidence.quality01." + ("high" if high else "ok")
    return [Result("quality_gate", "QUALITY-01", BLOCK if high else PASS, key, {"id": k["id"], "n": len(high)}, k["id"])
            for k in gates] \
        or [Result("quality_gate", "QUALITY-01", PASS, "evidence.quality01.none")]


def _card(key: str, ctype: str, trigger: str, title: str, subject: dict, r: Result, part: str, **kw) -> dict:
    """Card dictionary of guide §8.2, texts from evidence.card.<part>.* (G-31: level hold)."""
    text = {f: t(f"evidence.card.{part}.{f}", **kw) for f in ("question", "explain", "if_approved", "if_rejected")}
    return {"key": key, "type": ctype, "level": "hold", "title": title, "triggers": [trigger], "subject": subject,
            **text, "proposal": {"choice": t(f"evidence.card.{part}.choice"), "rationale": kw["rationale"]},
            "recorded_as": t("evidence.card.recorded_as"), "generated": True, "opened_by": "system",
            "checks": check_items([r])}


def make_cards(view, results: list[Result]) -> list[dict]:
    """Consistency card `consistency:<magnitude>` (CALC-01) and basis card `basis:K-nn` (DECISION-01)."""
    out = []
    for r in results:
        if r.check == "calc_consistency" and "consistency" in r.extra:
            d = r.extra["consistency"]
            b, low = d["base"], [f["calc"] for f in d["diffs"] if f["level"] < d["base"]["level"]]
            pct = f"{max(abs(f['diff']) for f in d['diffs']) * 100:.0f}"
            title = t(f"evidence.card.consistency.{'accepted_title' if r.extra.get('accepted') else 'title'}",
                      name=d["name"], pct=pct)
            why = t(f"evidence.card.consistency.{'superseded' if low else 'equal'}", base=b["calc"], level=b["level"],
                    low=", ".join(low))
            out.append(_card(f"consistency:{d['name']}", "consistency", "consistency", title, _subject(d), r,
                             "consistency", name=d["name"], base=b["calc"], method=b["method"],
                             value=num(b["value"], 4), items=_items(d), limit=r.extra["limit"], rationale=why))
        elif r.check == "decision_basis" and "changed" in r.extra:
            out.append(_card(f"basis:{r.ref}", "basis_changed", "decision_basis", r.reason,
                             {"decision": r.ref, "changed": r.extra["changed"], "superseded": r.extra["superseded"]},
                             r, "basis", decision=r.ref, checks=r.reason, rationale=t("evidence.card.basis.rationale")))
    return out


CHECKS = [CheckSpec("calc_consistency", run, ("CALC-01", "CALC-02", "DECISION-01"), order=80),
          CheckSpec("quality_gate", quality_gate, ("QUALITY-01",), after_cards=True, order=98)]
CARD_MAKERS = [make_cards]
