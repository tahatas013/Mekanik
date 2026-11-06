# SPDX-License-Identifier: AGPL-3.0-or-later
"""Work types and question trees as data (architecture §7.1 steps 1 and 3). The core's own are in stdlib/work_types
and stdlib/questions; a package adds its own in `work_types/` and `questions/` beside its catalog folder (the
PackageSpec's `i18n` path). A type is offered only when its provider is installed; the core knows no type by name."""

from __future__ import annotations

from pathlib import Path

from mekanik.plugins import registry

from .. import data, yamlio
from ..errors import SchemaError
from ..i18n import t
from ..model.schema import validate


def _folders(kind: str) -> list[Path]:
    """stdlib/<kind> first, then each registered package's <kind>/ folder."""
    return [data.stdlib(kind)] + [Path(p.i18n).parent / kind for p in registry().packages if p.i18n]


def load(kind: str, schema: str) -> dict[str, dict]:
    """id → record of every `<kind>` file, validated; an id given twice is an error."""
    out: dict[str, dict] = {}
    for folder in _folders(kind):
        for f in sorted(folder.rglob("*.yaml")) if folder.is_dir() else ():
            validate(schema, doc := yamlio.read(f), str(f))
            if doc["id"] in out:
                raise SchemaError(t("intake.duplicate", id=doc["id"], file=str(f)))
            out[doc["id"]] = doc
    return out


def walk(nodes: list[dict]):
    """Every node of a tree, children included."""
    for n in nodes:
        yield n
        yield from walk([c["node"] for c in n.get("children") or ()])


def installed() -> set[str]:
    return {"core", *(p.id for p in registry().packages)}


def work_types(available: bool = True) -> dict[str, dict]:
    """Work types; `available` keeps those whose providing package is installed."""
    ok = installed()
    return {k: v for k, v in load("work_types", "work_type").items() if not available or v["provided_by"] in ok}


def suggest(inputs: list[str], text: str = "") -> list[str]:
    """Type ids ranked by the inputs' extensions and the brief's keywords (a proposal only; the chief confirms)."""
    exts, words = {Path(p).suffix.lower() for p in inputs}, text.casefold()
    score = {k: 2 * len(exts & set((d := v.get("detection") or {}).get("input_extensions") or ()))
             + sum(w.casefold() in words for w in d.get("keywords_tr") or ()) for k, v in work_types().items()}
    return [k for k, s in sorted(score.items(), key=lambda x: -x[1]) if s > 0]


def active(view) -> list[dict]:
    """The work's trees: the type's own list first, then the trees of installed packages the work pins that apply."""
    trees, wt = load("questions", "question_tree"), work_types(available=False).get(view.doc.get("work_type"), {})
    pins = {"core", *(p["id"] for p in view.doc.get("packages") or [])} & installed()
    first = [trees[i] for i in wt.get("question_trees") or () if i in trees and trees[i]["provided_by"] in pins]
    return first + [x for x in trees.values() if x not in first and view.doc.get("work_type") in x["applies_to"]
                    and x["provided_by"] in pins]
