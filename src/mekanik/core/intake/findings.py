# SPDX-License-Identifier: AGPL-3.0-or-later
"""Findings (architecture §7.1 step 4; C4): contradiction, missing number, overlooked, alternative. Domain-free rules
here (an answer that the data contradicts, a requirement without a number, a mandatory requirement without a
verification, a required input missing); the trees' own `findings` add the domain ones."""

from __future__ import annotations

from ..i18n import t
from . import expr
from .engine import text


def _f(kind: str, ref: str, msg: str, basis: str | None) -> dict:
    return {"kind": kind, "ref": ref, "text": msg, **({"basis": basis} if basis else {})}


def find(view, nodes: list[dict], ctx: dict) -> list[dict]:
    """[{kind, ref, text, basis}] for the plan's nodes, the requirement list and the work type's inputs."""
    out = []
    for x in nodes:
        n = x["node"]
        if x["state"] == "answered" and x["derivable"] and x["derived"] != x["answer"]:
            ev = n["derive_from"]["evidence"]
            out.append(_f("contradiction", x["key"], t("intake.finding.contradiction", q=x["key"], given=x["answer"],
                                                       derived=x["derived"], evidence=ev), ev))
        own = {**ctx, "answer": x["answer"] if x["state"] in ("answered", "derived") else None}
        out += [_f(f["kind"], x["key"], text(f["text"]), f.get("basis")) for f in n.get("findings") or ()
                if expr.holds(f["when"], own)]
    for r in view.requirements:
        if r.get("status") == "withdrawn":
            continue
        if (((r.get("criterion") or {}).get("target") or {}).get("value")) is None:
            out.append(_f("missing_number", r["id"], t("intake.finding.missing_number", id=r["id"], text=r["text"],
                                                        question=r.get("open_question") or "—"), "requirements.yaml"))
        elif r.get("kind") == "mandatory" and not r.get("verification"):
            out.append(_f("overlooked", r["id"], t("intake.finding.unverified", id=r["id"], text=r["text"]),
                          "requirements.yaml"))
    for i in ctx.get("work_type", {}).get("required_inputs") or ():
        if sum(ctx["inputs"].get(e.lstrip("."), 0) for e in i["accept"]) < i["min"]:
            out.append(_f("overlooked", f"input:{i['id']}", t("intake.finding.input_missing", id=i["id"], purpose=text(
                i["purpose"]), accept=", ".join(i["accept"]), n=i["min"]), "work_type"))
    return out
