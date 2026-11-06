# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cards (old `kartlar.py`, architecture §4.3).

`generate` makes the cards in memory from check results (the core maker and the packages' `card_makers`), numbers
them, sets their status from approvals and decisions and builds their thread from comments and replies; nothing is
written. `sync` writes cards/<id>.yaml. A card's identity is its `key`: the same trigger gives the same id on the next
run. A card about a record whose id is a card id takes that id: the maker sets `id` (V-01), or the key is
`<kind>:<id>` with subject {<kind>: <id>} (a package record such as G-04 or E-01); otherwise the next free S-nn.
Cards opened by hand (gate, release, decision, the team's question) are kept.
Card standard: an open card with missing text or visual cannot be opened (`missing_fields`, CARD-01)."""

from __future__ import annotations

import re
from pathlib import Path

from mekanik.plugins import registry

from .. import clock, yamlio
from ..i18n import lang, t
from . import approval
from .makers import LIST_ID, check_items  # noqa: F401  (check_items: card makers' helper)

STATUS = {"approved": "approved", "rejected": "rejected", "dropped": "open", "none": "open"}
OPEN = ("open", "awaiting_reply")
TEXT_FIELDS = ("question", "explain", "if_approved", "if_rejected", "recorded_as")
KEEP = ("visuals", "opened_at")   # made at step time; read back from the file for generated cards
DERIVED = ("approval_state",)     # recomputed on every run, not written
CARD_ID = re.compile(r"[A-Z]{1,2}-\d{2,3}")
DECISION_TYPES = ("decision", "provisional_decision")


def generate(view, results: list, used: tuple[str, ...] = ()) -> list[dict]:
    """All cards of the work, in memory. `used`: card ids taken elsewhere (other branches), never given again."""
    made, seen = [], set()
    for maker in registry().card_makers:
        for c in maker(view, results):
            if c["key"] not in seen:
                seen.add(c["key"])
                made.append(c)
    _number(view, made, used)
    on_disk = {c["id"]: c for c in view.cards}
    for c in made:
        c.update({k: on_disk[c["id"]][k] for k in KEEP if k not in c and k in on_disk.get(c["id"], {})})
    cards = made + [from_file(c) for c in view.cards if not c.get("generated")]
    passed = {g: s for g, s in (view.doc.get("process", {}).get("gate_status") or {}).items()
              if s.get("status") == "done"}
    decisions = {d.get("id"): d for d in view.decisions}
    threads = _threads(view)
    for c in cards:
        c["work"], c["thread"] = view.code, threads.get(c["id"], [])
        if c.get("status") in ("withdrawn", "superseded") and not c.get("generated"):
            continue
        c.pop("closed_reason", None)   # closure is decided by the records, not by the card file
        subject = c.get("subject") or {}
        if c["type"] == "assumption_list":
            _rows(view, c)
        elif c["type"] in DECISION_TYPES and subject.get("decision") in decisions:
            d = decisions[subject["decision"]]
            c["status"] = "approved" if d.get("chosen") or d.get("status") == "approved" else (
                "rejected" if d.get("status") == "rejected" else "open")
        else:
            d = approval.state(view, c["id"], subject)
            c["status"], c["approval_state"] = STATUS[d], d
            if subject.get("gate") in passed:
                gate = subject["gate"]
                c["status"] = "closed"
                c["closed_reason"] = t("cards.note.gate_passed", gate=gate, tag=passed[gate].get("tag") or "—")
            elif d == "dropped":
                c["note"] = t("cards.note.dropped")
            elif d == "none" and approval.last(view, c["id"]):
                c["note"] = t("cards.note.rejected_changed")
        if c["status"] == "open" and awaiting(c):
            c["status"] = "awaiting_reply"
        c.setdefault("recorded_as", t("cards.recorded_as"))
    return cards


def _number(view, cards: list[dict], used) -> None:
    known = {c["key"]: c["id"] for c in view.cards if c.get("key")}
    taken = [*(c["id"] for c in view.cards), *used]
    n = max((int(i[2:]) for i in taken if re.fullmatch(r"S-\d{2,3}", i)), default=0)
    for c in cards:
        kind, _, rid = c["key"].partition(":")
        if c["key"] in known:
            c["id"] = known[c["key"]]
        elif not c.get("id") and (c.get("subject") or {}).get(kind) == rid and CARD_ID.fullmatch(rid):
            c["id"] = rid
        elif not c.get("id"):
            n += 1
            c["id"] = f"S-{n:02d}"


def _rows(view, c: dict) -> None:
    """Assumption list: each row is approved on its own (`V-01/<param>`); the card is approved when all rows are."""
    rows = []
    for name in c["subject"]["params"]:
        p = view.params[name]
        d = approval.state(view, f"{c['id']}/{name}", {"params": [name]})
        rows.append({"param": name, "value": p.value, "unit": p.unit, "description": p.description,
                     "rationale": p.rationale, "status": STATUS[d],
                     **({"note": t("cards.note.row_dropped")} if d == "dropped" else {})})
    c["rows"] = rows
    c["info_rows"] = [{"param": p.name, "value": p.value, "unit": p.unit, "description": p.description,
                       "source": p.source}
                      for p in view.params.values() if (p.source or "").startswith("manufacturer:")]
    c["status"] = "approved" if all(r["status"] == "approved" for r in rows) else "open"


def _threads(view) -> dict[str, list[dict]]:
    """Card id → the chief's records with a note (comment, and approve or reject with a reason) and the team's
    replies (replies.yaml, matched by comment time; guide G-29)."""
    out: dict[str, list[dict]] = {}
    for r in view.approvals:
        if r.get("action") not in ("comment", "approve", "reject") or not (r.get("reason") or "").strip():
            continue
        item = {"at": r["at"], "role": "chief_engineer", "kind": r["action"], "text": r["reason"],
                **{k: r[k] for k in ("commit", "row") if r.get(k)}}
        replies = [{"at": y["at"], "role": y["role"], "kind": "reply", "text": y["text"], "reply_to": y["comment_at"]}
                   for y in view.replies if y["card"] == r["card"] and y["comment_at"] == r["at"]]
        out.setdefault(r["card"], []).extend([item, *replies])
    return out


def awaiting(card: dict) -> bool:
    """A chief's note without a reply: the team owes an answer (old `yanit_bekliyor`)."""
    thread = card.get("thread") or []
    replied = {x.get("reply_to") for x in thread if x.get("kind") == "reply"}
    return any(x.get("kind") != "reply" and x["at"] not in replied for x in thread)


def _text(x) -> bool:
    return any(_text(v) for v in x.values()) if isinstance(x, dict) else bool((x or "").strip())


def missing_fields(card: dict) -> list[str]:
    """Card standard: the fields an open card lacks. Empty list = the card can be opened."""
    if card.get("status") not in OPEN:
        return []
    out = [f for f in TEXT_FIELDS if not _text(card.get(f))]
    prop = card.get("proposal") or {}
    if not ((prop.get("choice") or prop.get("option")) and _text(prop.get("rationale") or prop.get("text"))):
        out.append("proposal")
    if not card.get("visuals"):
        out.append("visuals")
    out += [f"untraced:{n}" for n in card.get("untraced") or []]
    if card.get("type") == "assumption_list":
        out += [f"rows:{r['param']}:rationale" for r in card.get("rows") or [] if not _text(r.get("rationale"))]
    if card.get("type") in DECISION_TYPES:
        out += [f"options:{o['id']}:visual" for o in card.get("options") or [] if not o.get("visual")]
        if "requirement_effects" in card and not card["requirement_effects"]:
            out.append("requirement_effects")
    return out


def to_file(card: dict, old: dict | None = None) -> dict:
    """The card as a `card` record: text as {lang: text} (records keep the language they were written in; the
    schema needs a Turkish entry), proposal with its text, result texts as check entries, the first opening time."""
    doc = {"kind": "card", "schema_version": "1.0",
           **{k: v for k, v in card.items() if k not in DERIVED and v is not None and (k != "visuals" or v)}}
    if isinstance(doc.get("explain"), str):
        doc["explain"] = {"tr": doc["explain"]} if lang() == "tr" else {"tr": doc["explain"], lang(): doc["explain"]}
    if isinstance(doc.get("proposal"), dict) and "text" not in doc["proposal"]:
        p = doc["proposal"]
        doc["proposal"] = {"text": p.get("rationale") or p.get("choice") or "", **p}
    if doc.get("checks"):
        doc["checks"] = [c if isinstance(c, dict) else {"rule": "", "result": "warn", "message": str(c)}
                         for c in doc["checks"]]
    doc["opened_at"] = doc.get("opened_at") or (old or {}).get("opened_at") or clock.now()
    return doc


def from_file(doc: dict) -> dict:
    c = {k: v for k, v in doc.items() if k not in ("kind", "schema_version")}
    if isinstance(c.get("explain"), dict):
        c["explain"] = c["explain"].get(lang()) or c["explain"].get("tr", "")
    return c


def sync(view, cards: list[dict], txn=None) -> list[str]:
    """Write cards/<id>.yaml where the content changed and return the changed ids. A generated card whose trigger is
    gone is closed; its file is never deleted (old `esitle`)."""
    folder = Path(view.root) / "cards"
    ids = {c["id"] for c in cards}
    listed = set(next((c["subject"]["params"] for c in cards if c.get("type") == "assumption_list"), []))
    cards = list(cards)
    for old in view.cards:
        if old.get("generated") and old["id"] not in ids and old.get("status") != "closed":
            kind, _, name = (old.get("key") or "").partition(":")
            moved = kind == "assumption" and name in listed
            why = ({"closed_reason": t("cards.note.moved_to_list", id=LIST_ID)} if moved
                   else {"note": t("cards.note.trigger_gone")})
            cards.append({**from_file(old), "status": "closed", **why})
    on_disk = {c["id"]: c for c in view.cards}
    changed, docs = [], []
    for c in cards:
        doc = to_file(c, on_disk.get(c["id"]))
        path, text = folder / f"{c['id']}.yaml", yamlio.dump(doc)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            (txn or yamlio).write_text(path, text)
            changed.append(c["id"])
        docs.append(doc)
    written = {d["id"] for d in docs}
    view.cards = docs + [c for c in view.cards if c["id"] not in written]
    return changed
