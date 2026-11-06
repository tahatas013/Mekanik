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
    """Every approval record comes with a commit signed by the chief's key from the workshop config, and every passed
    gate (gate_status done) and cut release (out/<code>-release-<no>) rests on a valid approval of its card (§4.6).
    A migrated record or gate (`migrated`) counts when the chief's signed approval of MG-01 covers it (§14.3 V5); a
    value claimed as the chief's (params `decided_by: chief_engineer`) rests on his valid `value_change` record."""
    from mekanik.config import load_config

    from ... import yamlio
    from ...cards import approval, signature as sig

    rule, out, ok, valid = "APPROVAL-02", [], set(), []
    found = sig.verify(view.root, view.approvals, load_config().signing_key) if view.approvals else []
    took, gates = sig.migration_cover(view, found)
    found = [None if p and p[0] == "migrated" and approval.digest(r) in took else p for r, p in zip(view.approvals,
                                                                                                    found)]
    for i, (rec, problem) in enumerate(zip(view.approvals, found)):
        if problem is None and not approval.authorized(view, rec.get("identity")):
            problem = ("identity", {"name": (rec.get("identity") or {}).get("name")})
        args = {"card": rec.get("card"), "action": rec.get("action"), "at": rec.get("at")}
        if problem is None:
            ok.add((rec.get("card"), rec.get("action")))
            valid.append(rec)
            out.append(Result("approval_signature", rule, PASS, "checks.signature.ok", args, rec.get("card"),
                              extra={"index": i}))
        else:
            out.append(Result("approval_signature", rule, BLOCK, f"checks.signature.{problem[0]}",
                              {**args, **problem[1]}, rec.get("card"), extra={"index": i, "problem": problem[0]}))
    done = [f"O-{g}" for g, s in view.doc["process"]["gate_status"].items() if s.get("status") == "done"
            and not (s.get("migrated") and g in gates)]
    done += [f"B-{d.name.rsplit('-', 1)[1]}" for d in (view.root / "out").glob(f"{view.code}-release-*")]
    out += [Result("approval_signature", rule, BLOCK, "checks.signature.unapproved", {"card": c}, c,
                   extra={"problem": "unapproved"}) for c in done if (c, "approve") not in ok]
    for n, p in sorted((yamlio.read(view.root / "params.yaml", {}) or {}).items()):
        if isinstance(p, dict) and p.get("decided_by") == "chief_engineer":
            last = [r for r in valid if r.get("action") == "value_change" and (r.get("new_value") or {}).get(
                "name") == n][-1:]
            good = bool(last) and last[0].get("approved_hash") == approval.digest(approval.subject_values(
                view, {"params": [n]}))
            out.append(Result("approval_signature", rule, PASS if good else BLOCK, "checks.signature." + (
                "value_ok" if good else "value"), {"param": n, "value": p.get("value")}, n,
                extra={} if good else {"problem": "value"}))
    return out or [Result("approval_signature", rule, PASS, "checks.signature.none")]
