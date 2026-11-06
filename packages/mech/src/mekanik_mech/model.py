# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parametric model (old `modelci.py` and kart_gorsel.model_uretici): `model/model.py` defines
`parts(p, **kw) -> {name: shape}` where `p.<name>` is the value of a parameter. The model is a dict
{part name: cadquery Shape}; Workplane results are unwrapped with `.val()`.

The work's code is loaded without writing bytecode (E-19: no __pycache__ in the design repo).
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.params import formula_eval


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    old, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


def _parts(mod, values: dict, **kw) -> dict:
    fn = getattr(mod, "parts", None) or getattr(mod, "parcalar", None)   # parcalar: model code of a migrated work
    if fn is None:
        raise SchemaError(t("mech.model.no_parts", path=str(mod.__file__)))
    out = fn(SimpleNamespace(**values), **kw) or {}
    return {name: (s.val() if hasattr(s, "val") else s) for name, s in out.items()}


def build_path(model_py: Path, values: dict, **kw) -> dict | None:
    """Parts of a model file for explicit values (no work view needed; migration V6 uses it)."""
    return _parts(load_module(f"mekanik_model_{abs(hash(str(model_py)))}", Path(model_py)), values, **kw) or None


def builder(view, **kw):
    """values → parts. Derived parameters are recomputed from their formulas; `kw` goes to parts() (decision
    options, e.g. form="a"). `make.prefer` is the model's CARD_VIEW {param: part pattern} for card figures."""
    mod = load_module(f"mekanik_model_{view.code.replace('-', '_')}", Path(view.root) / "model" / "model.py")
    derived = [(a, p.formula) for a, p in view.params.items() if p.source == "derived"]

    def make(values: dict) -> dict:
        d = dict(values)
        for _ in range(len(derived) + 1):
            for a, f in derived:
                try:
                    d[a] = formula_eval(f, d)
                except (SchemaError, ArithmeticError):
                    pass
        return _parts(mod, d, **kw)

    make.prefer = getattr(mod, "CARD_VIEW", None) or getattr(mod, "KART_GORSELI", {})
    return make


def build(view, values: dict | None = None, **kw) -> dict | None:
    """The work's model; None when there is no model/model.py or it returns no part."""
    if not (Path(view.root) / "model" / "model.py").exists():
        return None
    return builder(view, **kw)(values or {a: p.value for a, p in view.params.items()}) or None


def metrics(parts: dict) -> dict:
    """Per part: volume (mm³), bounding box (x, y, z lengths, mm), face and solid count (migration V6 compares)."""
    out = {}
    for name, s in parts.items():
        bb = s.BoundingBox()
        out[name] = {"volume": s.Volume(), "bbox": (bb.xlen, bb.ylen, bb.zlen), "faces": len(s.Faces()),
                     "solids": len(s.Solids())}
    return out


def summary(parts: dict) -> str:
    """One line for the log (old akis._sinir_kutusu): part count and bounding box measured from the code."""
    import cadquery as cq

    bb = cq.Compound.makeCompound(list(parts.values())).BoundingBox()
    x, y, z = (f"{v:.1f}".replace(".", t("num.decimal")) for v in (bb.xlen, bb.ylen, bb.zlen))
    return t("mech.model.summary", n=len(parts), x=x, y=y, z=z)


_PRODUCER: str | None = None


def producer_version() -> str:
    """CadQuery, OCP, ocp-tessellate versions and export.py itself: when they change, an old cache entry (same input,
    different output) is not reused."""
    global _PRODUCER
    if _PRODUCER is None:
        from importlib.metadata import version

        digest = hashlib.sha1(Path(__file__).with_name("export.py").read_bytes()).hexdigest()[:12]
        _PRODUCER = " ".join(version(p) for p in ("cadquery", "cadquery-ocp", "ocp-tessellate")) + " " + digest
    return _PRODUCER


def signature(root: Path, sha: str) -> str:
    """Content signature of the model at a commit: model/ tree, params.yaml, fits.yaml and the producer version
    (SHA-1). Log and card commits do not change it, so they reuse the cached model."""
    from mekanik.core.errors import GitError
    from mekanik.core.store.git import git

    rel = git("rev-parse", "--show-prefix", cwd=root).rstrip("/")
    ids = []
    for y in ("model", "params.yaml", "fits.yaml"):
        try:
            ids.append(git("rev-parse", f"{sha}:{rel}/{y}" if rel else f"{sha}:{y}", cwd=root))
        except GitError:
            ids.append("-")
    return hashlib.sha1(" ".join(ids + [producer_version()]).encode()).hexdigest()
