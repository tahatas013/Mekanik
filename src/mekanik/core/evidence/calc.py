# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculations and analyses: calcs/*.py, recorded as records/calcs/<id>.json (old `hesap.py`).

A script sets ID, TITLE, PURPOSE (TYPE, SCENARIO, LINKS) and `calculate(c, model)`; `c` is a Calc: input (params.yaml
only), const (source standard:, manufacturer:, literature: or decision; an assumption goes to params.yaml and opens a
card), step, result, magnitude (compared across calcs, CALC-01), other, chart, visual, note. An analysis needs LINKS:
the risk, observation, requirement or decision it is made for (Ö-19). A calc with unchanged inputs does not rerun.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

from .. import clock, yamlio
from ..errors import SchemaError
from ..i18n import t
from ..model.params import SOURCE_RE
from ..model.schema import validate

FOLDER = "records/calcs"
SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
CONST_SOURCE = re.compile(r"^(standard:.+|manufacturer:.+|literature:.+|decision)$")
STATUS = {"": "none", "ok": "ok", "marginal": "marginal", "bad": "bad", "unreliable": "unreliable"}
TYPES = ("calculation", "analysis")
DIGITS = 4   # source: assumption — digests and compared values round off float noise (old ozet_metinden), not a limit


def _num(x) -> float | None:
    if x is not None and not math.isfinite(x := float(x)):
        raise SchemaError(t("evidence.calc.not_number", value=x))
    return x


def _opt(**kw) -> dict:
    return {k: v for k, v in kw.items() if v}


class Calc:
    def __init__(self, view, calc_id: str, done: dict | None = None):
        self.view, self.id, self.title, self.purpose, self._done = view, calc_id, calc_id, "", done or {}
        self.inputs, self.constants, self.steps, self.results, self.magnitudes = [], [], [], [], []
        self.charts, self.notes, self.visuals, self.read = [], [], [], []

    def _fail(self, key: str, **kw):
        raise SchemaError(t(f"evidence.calc.{key}", calc=self.id, **kw))

    def _slug(self, name: str) -> str:
        return name if SLUG.match(str(name)) else self._fail("bad_name", name=name)

    def input(self, name: str) -> float:
        p = self.view.params.get(name)
        if p is None or p.value is None or not p.source:
            self._fail("no_param" if p is None else "no_value" if p.value is None else "no_source", name=name)
        if all(x["name"] != name for x in self.inputs):
            self.inputs.append({"name": name, "quantity": {"value": p.value, "unit": p.unit, "source": p.source}
                                | _opt(formula=p.formula, note=p.description or p.note)})
        return p.value

    def const(self, name: str, value: float, unit: str, source: str, note: str = "", decided_by: str | None = None):
        if not (source and CONST_SOURCE.match(source)):
            self._fail("bad_const", name=name, source=source)
        q = {"value": _num(value), "unit": unit, "source": source} | _opt(decided_by=decided_by, note=note)
        self.constants.append({"name": self._slug(name), "quantity": q})
        return value

    def step(self, title: str, formula: str, value: float, unit: str, source: str | None = None) -> float:
        if source and not SOURCE_RE.match(source):
            self._fail("bad_source", name=title, source=source)
        self.steps.append({"title": title, "formula": formula, "value": _num(value), "unit": unit}
                          | _opt(source=source))
        return value

    def result(self, name: str, value: float, unit: str, comment: str = "", status: str = "") -> float:
        """status: '' | ok | marginal | bad | unreliable (the method's own confidence is low)."""
        if status not in STATUS:
            self._fail("bad_status", name=name, status=status)
        # The old API declares no uncertainty; the record says so explicitly (NASA-STD-7009B [M&S 33]).
        self.results.append({"name": self._slug(name), "value": _num(value), "unit": unit, "status": STATUS[status]}
                            | _opt(comment=comment) | {"uncertainty_note": "none_available"})
        return value

    def magnitude(self, name: str, value: float, unit: str, level: int, method: str) -> float:
        """level: 1 hand formula · 2 numeric method (VLM, FEA) · 3 measurement."""
        if level not in (1, 2, 3):
            self._fail("bad_level", name=name)
        self.magnitudes.append({"name": self._slug(name), "value": _num(value), "unit": unit, "level": level,
                                "method": method})
        return value

    def other(self, calc_id: str) -> dict | None:
        """Another calc's record: this round's if it ran before (files run in name order), else the stored one."""
        rec = self._done.get(calc_id) or _read(Path(self.view.root) / FOLDER / f"{calc_id}.json")
        if rec is not None and calc_id not in self.read:
            self.read.append(calc_id)
        return rec

    def other_magnitude(self, calc_id: str, name: str) -> float | None:
        return next((m["value"] for m in (self.other(calc_id) or {}).get("magnitudes", []) if m["name"] == name), None)

    def chart(self, title: str, x: list, y: list, x_label: str, y_label: str, marker=None, series=None) -> None:
        """Line chart; series: {name: [y…]} on the same x; marker: (x, y, text)."""
        self.charts.append({"title": title, "x": [_num(v) for v in x], "x_label": x_label, "y_label": y_label,
                            "series": {k: [_num(v) for v in s] for k, s in (series or {y_label: y}).items()},
                            "marker": list(marker) if marker else None})

    def visual(self, title: str, svg: str) -> None:
        if not svg.lstrip().startswith("<svg"):
            self._fail("not_svg")
        rel = f"records/visuals/calc-{self.id}-{len(self.visuals) + 1}.svg"
        yamlio.write_text(Path(self.view.root) / rel, svg)
        self.visuals.append({"kind": "file", "id": title or rel, "path": rel})

    def note(self, text: str) -> None:
        self.notes.append(text)


def load_module(name: str, path: Path):
    """Load work code without writing __pycache__ into the design repository (E-19)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod, old, sys.dont_write_bytecode = importlib.util.module_from_spec(spec), sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


def files(root) -> list[Path]:
    return sorted(p for p in (Path(root) / "calcs").glob("*.py") if not p.name.startswith("_"))


def input_hash(root) -> str:
    """Model and calc code, params, decisions and approvals (old `girdi_ozeti`): calcs and review rerun on change."""
    root, h = Path(root), hashlib.sha256()
    for p in sorted([*(root / "model").glob("*.py"), *files(root)]) + [
            root / "params.yaml", root / "decisions.yaml", root / "approvals.yaml"]:
        if p.exists():
            h.update(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def run(view, model=None, cache: bool = True) -> list[dict]:
    """Run every calc; a failing one is recorded with its error and does not stop the step."""
    root, out, ihash = Path(view.root), [], input_hash(view.root)
    for path in files(root):
        old = _read(root / FOLDER / f"{path.stem}.json")
        if cache and old and old.get("input_hash") == ihash and not old.get("error"):
            out.append(old)
            continue
        c, kind, extra, error = Calc(view, path.stem, {r["id"]: r for r in out}), "calculation", {}, None
        try:
            mod = load_module(f"mekanik_calc_{view.code.replace('-', '_')}_{path.stem}", path)
            c.id = c._slug(getattr(mod, "ID", path.stem))
            c.title, c.purpose = getattr(mod, "TITLE", c.id), getattr(mod, "PURPOSE", "")
            kind = getattr(mod, "TYPE", kind)
            if kind not in TYPES:
                c._fail("bad_type", type=kind)
            links = list(getattr(mod, "LINKS", []))
            if (kind == "analysis" and not links) or any(not isinstance(x, dict) for x in links):
                c._fail("unlinked")
            extra = _opt(scenario=getattr(mod, "SCENARIO", ""), links=links)
            mod.calculate(c, model)
        except Exception as e:
            kind, extra, error = kind if kind in TYPES else "calculation", {}, f"{type(e).__name__}: {e}"
        rec = {"kind": "calculation", "schema_version": "1.0", "id": c.id, "work": view.code, "title": c.title,
               **_opt(purpose=c.purpose), "type": kind, **extra, "inputs": c.inputs, "constants": c.constants,
               "steps": c.steps, "results": c.results, "magnitudes": c.magnitudes, "charts": c.charts, "notes": c.notes,
               "visuals": c.visuals, "read_calculations": c.read, "input_hash": ihash, "ran_at": clock.now(),
               "validity": {"domain": [], "in_domain": None, "zone": "undefined"},   # old calcs define no domain
               "error": error}
        out.append(rec | {"result_hash": result_hash(rec)})
    return out


def check_schema(rec: dict) -> list[str]:
    """Validate; phase-1 findings come back as warnings (G-27). The old `decision` source named no decider, so a
    missing decided_by on an input or constant is a warning (checked on a copy)."""
    where, shadow = f"{FOLDER}/{rec.get('id')}.json", json.loads(json.dumps(rec))
    loose = [q for k in ("inputs", "constants") for x in shadow.get(k) or [] if isinstance(q := x.get("quantity"), dict)
             and q.get("source") == "decision" and "decided_by" not in q]
    for q in loose:
        q["decided_by"] = "system"
    soft = [t("schema.later_required", where=where, field="decided_by")] if loose else []
    return validate("calculation", shadow, where) + soft


def write(view, records: list[dict]) -> list[str]:
    """records/calcs/<id>.json; returns the changed paths (ran_at alone is not a change)."""
    root, changed = Path(view.root), []
    for rec in records:
        check_schema(rec)
        path = root / FOLDER / f"{rec['id']}.json"
        if (old := _read(path)) is None or {**old, "ran_at": None} != {**rec, "ran_at": None}:
            yamlio.write_text(path, json.dumps(rec, ensure_ascii=False, indent=1))
            changed.append(str(path.relative_to(root)))
    return changed


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def recorded(root) -> dict[str, dict]:
    recs = ((p.stem, _read(p)) for p in sorted((Path(root) / FOLDER).glob("*.json")))
    return {k: v for k, v in recs if v is not None}


def inconsistencies(recs: dict, limit: float) -> list[dict]:
    """Magnitudes that differ between calcs by more than `limit` (relative; B3). The highest level is the base;
    differing lower-level calcs are superseded. → [{name, unit, base {calc, value, level, method}, diffs}]"""
    by_name: dict[str, list[dict]] = {}
    for cid, rec in recs.items():
        for m in [] if rec.get("error") else rec.get("magnitudes", []):
            by_name.setdefault(m["name"], []).append({"calc": cid, **m})
    out = []
    for name, items in sorted(by_name.items()):
        b = max(items, key=lambda x: (x["level"], x["calc"]))
        diffs = [{**x, "diff": (x["value"] - b["value"]) / abs(b["value"])} for x in items
                 if x is not b and b["value"] and abs(x["value"] - b["value"]) / abs(b["value"]) > limit]
        out += [{"name": name, "unit": b["unit"], "base": b, "diffs": diffs}] if diffs else []
    return out


def bad_results(recs: dict) -> list[dict]:
    """Bad or unreliable results (B4): [{calc, title, name, value, unit, status, comment}]."""
    return [{"calc": cid, "title": rec.get("title", cid), **{k: r.get(k) for k in ("name", "value", "unit", "status",
                                                                                     "comment")}}
            for cid, rec in recs.items() for r in rec.get("results", []) if r.get("status") in ("bad", "unreliable")]


def result_hash(rec: dict) -> str:
    """Digest of the results and magnitudes: has a decision's basis changed (B5)?"""
    doc = {k: [(x["name"], round(x["value"], DIGITS) if isinstance(x["value"], float) else x["value"])
               for x in rec.get(f, [])] for k, f in (("s", "results"), ("b", "magnitudes"))} | {"h": rec.get("error")}
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16]


def current_hash(root, calc_id: str) -> str | None:
    """Result hash of a calc's stored record (old `sonuc_ozeti`); a decision keeps it as its basis."""
    return None if (rec := _read(Path(root) / FOLDER / f"{calc_id}.json")) is None else result_hash(rec)


def param_users(root) -> dict[str, list[str]]:
    """Param → titles of the calcs that read it (old `kullanan_hesaplar`)."""
    out: dict[str, list[str]] = {}
    for rec in recorded(root).values():
        for i in rec.get("inputs", []):
            out.setdefault(i["name"], []).append(rec.get("title") or rec["id"])
    return out
