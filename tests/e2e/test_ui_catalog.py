# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.7 and guide §1 rule 4 for the front end: every text the page shows is a catalog key (panel.ui.* and the back
end's panel.*, status.*, agent.liveness.* served by GET /api/catalog); every key the code asks for exists in Turkish;
English has every panel key (100 %). No browser needed."""

from __future__ import annotations

import re
from pathlib import Path

from mekanik.core import i18n

SRC = Path(__file__).resolve().parents[2] / "panel-ui" / "src"
TURKISH = re.compile("[çğıöşüÇĞİÖŞÜ]")
# keys built from a template in the code: prefix → the values the code puts in
TEMPLATES = {
    "br.f.": ["all", "gates", "open"], "calc.lead_": ["calcs", "analyses"], "calc.none_": ["calcs", "analyses"],
    "card.k.": ["all", "hold", "provisional", "question"], "design.": ["done", "found", "waiting"],
    "flow.f.": ["all", "decisions", "hold", "checks", "visuals"], "flow.side.": ["summary", "status", "team"],
    "flow.sum.": ["decisions", "pending", "risks", "agents"], "intake.s.": ["type", "analysis", "questions", "summary"],
    "live.": ["working", "quiet", "waiting", "stopped"], "std.p": ["1", "2", "3", "4", "5"],
    "nav.": ["flow", "intake", "cards", "model", "stdmap", "files", "calcs", "analyses", "branches", "design", "session"],
    "new.": ["org", "project", "work_title", "purpose", "done", "class"], "step.": ["text", "params", "calcs", "diff", "files"],
}


def _code() -> str:
    return "\n".join(f.read_text(encoding="utf-8") for f in sorted(SRC.rglob("*.ts")))


def _strings(code: str) -> list[str]:
    no_comments = re.sub(r"^\s*//.*$", "", code, flags=re.M)
    return re.findall(r'"((?:[^"\\\n]|\\.)*)"', no_comments) + re.findall(r"`((?:[^`\\]|\\.)*)`", no_comments)


def test_front_end_has_no_turkish_text_outside_the_catalog():
    """2.7: guide §1 rule 4 — no Turkish letter in a string of panel-ui/src (comments aside)"""
    assert [s for s in _strings(_code()) if TURKISH.search(s)] == []


def _first_args(code: str, fn: str) -> set[str]:
    """String literals of the first argument of every `fn(…)` call (a ternary there gives both keys)."""
    out = set()
    for m in re.finditer(rf"\b{fn}\(", code):
        i, depth, arg = m.end(), 1, []
        while i < len(code) and depth:
            ch = code[i]
            depth += {"(": 1, ")": -1}.get(ch, 0)
            if depth == 1 and ch == ",":
                break
            arg.append(ch)
            i += 1
        out |= set(re.findall(r'(?<![=!]== )"([a-z_0-9.]+)"', "".join(arg)))   # not the compared value
    return out


def test_every_key_the_page_asks_for_exists():
    """2.7: every panel.ui key the code names (literal, ternary or from a template) is in the Turkish catalog"""
    tr, code = i18n.catalogs()["tr"], _code()
    asked = set().union(*(_first_args(code, f) for f in ("u", "uh", "empty", "say")))
    asked |= {p + v for p, vs in TEMPLATES.items() for v in vs}
    missing = sorted(k for k in asked if f"panel.ui.{k}" not in tr and k not in tr)
    assert missing == []


def test_english_has_every_panel_key():
    """2.7: EN catalog coverage of the panel (back end and front end): 100 %, 0 missing keys"""
    cats = i18n.catalogs()
    want = {k for k in cats["tr"] if k.startswith(("panel.", "agent.liveness.", "status."))}
    assert sorted(want - set(cats.get("en", {}))) == []
