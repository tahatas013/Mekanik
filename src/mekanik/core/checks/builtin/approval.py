# SPDX-License-Identifier: AGPL-3.0-or-later
"""APPROVAL-01 (old `onay_durumu.py`, ONAY-01) and APPROVAL-02 (approval signature, architecture §4.6, KM-04).

APPROVAL-01 runs last, with the cards made from the other results; it is not applied before finalizing."""

from __future__ import annotations

from ..result import BLOCK, PASS, Result

OPEN = ("open", "awaiting_reply")


def state(view, model=None, cards: list[dict] | None = None) -> list[Result]:
    if not view.finalizing:
        return []
    rule, out = "APPROVAL-01", []
    for d in view.decisions:
        st = d.get("status")
        ok = st not in (None, "proposed")
        out.append(Result("approval_state", rule, PASS if ok else BLOCK,
                          "checks.approval_state.decision_ok" if ok else "checks.approval_state.decision_open",
                          {"id": d.get("id"), "status": st}, d.get("id")))
    for k in cards if cards is not None else view.cards:
        args = {"id": k["id"], "status": k.get("status")}
        if k.get("status") == "rejected":
            out.append(Result("approval_state", rule, BLOCK, "checks.approval_state.rejected", args, k["id"]))
        elif k.get("status") in OPEN:
            why = "dropped" if k.get("approval_state") == "dropped" else "hold" if k.get("level") == "hold" else "open"
            out.append(Result("approval_state", rule, BLOCK, f"checks.approval_state.{why}", args, k["id"]))
        else:
            out.append(Result("approval_state", rule, PASS, "checks.approval_state.closed", args, k["id"]))
    return out or [Result("approval_state", rule, PASS, "checks.approval_state.none")]


def signature(view, model=None) -> list[Result]:
    """Every approval record must come with a commit signed by the chief's key from the workshop config."""
    from mekanik.config import load_config

    from ...cards import approval, signature as sig

    rule = "APPROVAL-02"
    if not view.approvals:
        return [Result("approval_signature", rule, PASS, "checks.signature.none")]
    key = load_config().signing_key
    out = []
    for i, (rec, problem) in enumerate(zip(view.approvals, sig.verify(view.root, view.approvals, key))):
        if problem is None and not approval.authorized(view, rec.get("identity")):
            problem = ("identity", {"name": (rec.get("identity") or {}).get("name")})
        args = {"card": rec.get("card"), "action": rec.get("action"), "at": rec.get("at")}
        if problem is None:
            out.append(Result("approval_signature", rule, PASS, "checks.signature.ok", args, rec.get("card"),
                              extra={"index": i}))
        else:
            key_, more = problem
            out.append(Result("approval_signature", rule, BLOCK, f"checks.signature.{key_}", {**args, **more},
                              rec.get("card"), extra={"index": i, "problem": key_}))
    return out
