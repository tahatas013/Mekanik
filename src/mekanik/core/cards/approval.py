# SPDX-License-Identifier: AGPL-3.0-or-later
"""Approval records and approval state (old `onay.py`, architecture §4.6).

approvals.yaml is append-only: existing records never change, a new one goes to the end. A record carries the
SHA-256 of the canonical JSON of the card's subject values; when those values change the hash no longer matches,
the approval drops by itself and the card reopens. Only the chief engineer of the workshop config approves, rejects
or undoes, matched on name and e-mail exactly (the old check compared first names only, onay.py:112).
A row of the assumption list is addressed as `V-01/<param>` (record: card V-01, row <param>)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mekanik.plugins import registry

from .. import clock, yamlio
from ..errors import SchemaError
from ..i18n import t
from ..model.schema import validate

FILE = "approvals.yaml"
ACTIONS = ("approve", "reject", "undo", "comment", "value_change", "objection")
DECIDING = ("approve", "reject", "undo")
DESIGN_FILES = ("params.yaml", "requirements.yaml", "decisions.yaml")
DESIGN_DIRS = ("model", "calcs")


def _normal(x):
    """Canonical form: numbers as float (10 and 10.0 give the same hash), keys as text, sorted on dump."""
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, dict):
        return {str(k): _normal(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_normal(v) for v in x]
    return str(x)


def canonical_json(data) -> str:
    return json.dumps(_normal(data), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(data) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def _param(view, name: str) -> dict | None:
    p = view.params.get(name)
    if p is None:
        return None
    out = {"value": p.value, "unit": p.unit, "source": p.source, "formula": p.formula}
    if p.measured:   # the instrument's uncertainty and validity enter the hash (old olcum_profili)
        inst = view.instruments.get(p.instrument) or {}
        out["instrument"] = {"id": p.instrument, "uncertainty": inst.get("uncertainty"),
                             "valid_for": inst.get("valid_for")}
    return out


def subject_values(view, subject: dict) -> dict:
    """Snapshot of the values a card is about: core params and design hash, the subject's own keys (gate, release,
    decision, option, quantity …) and what packages add for their own keys (a record and its limits)."""
    subject = subject or {}
    out: dict = {f"param:{n}": _param(view, n) for n in sorted(subject.get("params") or [])}
    if subject.get("design"):
        out["design"] = design_hash(view.root)
    out.update({k: v for k, v in subject.items() if k not in ("params", "design") and v is not None})
    out.update(registry().subject_values(view, subject) or {})
    return out


def _files(root: Path, names) -> list[Path]:
    out = []
    for n in names:
        p = root / n
        out += sorted(f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts) if p.is_dir() else [p]
    return out


def design_hash(root: Path) -> str:
    """Content a gate approval is bound to: design files (core and packages), then the model/ and calcs/ trees."""
    root = Path(root)
    h = hashlib.sha256()
    for f in _files(root, (*DESIGN_FILES, *registry().design_files)) + _files(root, DESIGN_DIRS):
        if f.is_file():
            h.update(str(f.relative_to(root)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def authorized(view, identity) -> bool:
    """The chief engineer of the workshop config: name and e-mail both equal."""
    from mekanik.config import load_config

    if isinstance(identity, dict):
        identity = (identity.get("name"), identity.get("email"))
    return bool(identity) and tuple(identity) == tuple(load_config().chief)


def _split(card_id: str) -> tuple[str, str | None]:
    card, _, row = card_id.partition("/")
    return card, row or None


def last(view, card_id: str) -> dict | None:
    """The chief's last valid approve or reject of the card (comments are not decisions). Each `undo` cancels the
    nearest earlier approve or reject; nothing is deleted."""
    card, row = _split(card_id)
    undo = 0
    for r in reversed(view.approvals):
        if r.get("card") != card or r.get("row") != row or not authorized(view, r.get("identity")):
            continue
        if r.get("action") == "undo":
            undo += 1
        elif r.get("action") in ("approve", "reject"):
            if undo:
                undo -= 1
                continue
            return r
    return None


def state(view, card_id: str, subject: dict) -> str:
    """'approved' | 'rejected' | 'dropped' (approved, then the values changed) | 'none'."""
    r = last(view, card_id)
    if r is None:
        return "none"
    current = r.get("approved_hash") == digest(subject_values(view, subject))
    if r["action"] == "reject":
        return "rejected" if current else "none"   # rejected value changed: reviewed again
    return "approved" if current else "dropped"


def valid(view, card_id: str, subject: dict) -> bool:
    return state(view, card_id, subject) == "approved"


def record(view, card_id: str, subject: dict, action: str, identity, commit: str | None = None,
           reason: str = "", at: str | None = None, **extra) -> dict:
    """An approval record (schema `approval`); `extra` holds option, signature, channel, viewed_version, undoes …"""
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {ACTIONS}")
    name, email = (identity.get("name"), identity.get("email")) if isinstance(identity, dict) else identity
    if action in DECIDING and not authorized(view, (name, email)):
        raise PermissionError(t("cards.approval.unauthorized", name=name, email=email))
    card, row = _split(card_id)
    return {"kind": "approval", "schema_version": "1.0", "work": view.code, "card": card,
            **({"row": row} if row else {}), "action": action, "role": "chief_engineer",
            "identity": {"name": name, "email": email},
            "at": at or clock.now(), "approved_hash": digest(subject_values(view, subject)),
            **({"commit": commit} if commit else {}), **({"reason": reason} if reason else {}), **extra}


def append(view, rec: dict, txn=None) -> dict:
    """Add one record to approvals.yaml; refuses if the earlier records would not stay as they are."""
    path = Path(view.root) / FILE
    old = yamlio.read(path, []) or []
    validate("approval", rec, f"{FILE}[{len(old)}]")
    text = yamlio.dump([*old, rec])
    if (yamlio.load(text) or [])[: len(old)] != old:
        raise SchemaError(t("cards.approval.not_appended", path=str(path)))
    (txn or yamlio).write_text(path, text)
    view.approvals.append(rec)
    return rec
