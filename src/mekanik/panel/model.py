# SPDX-License-Identifier: AGPL-3.0-or-later
"""The model of a commit for the viewer (old model_servisi.py): through the package's model hooks only (the panel
knows no geometry kind). Tessellation from the cache (`<cache>/<model signature>/tessellation.json`, what `step`
writes), else made from the commit in a temporary worktree; at most MEMORY models in memory, one production per
signature at a time. Measurements come from the exact solids (three-cad-viewer's external measurement contract)."""

from __future__ import annotations

import contextlib
import shutil
import tempfile
import threading
from collections import OrderedDict
from pathlib import Path

from mekanik.core.evidence import cache
from mekanik.core.model.work import load_work
from mekanik.core.store import git
from mekanik.core.store.works import dirty
from mekanik.plugins import registry

MEMORY = 6   # source: assumption — old model_servisi.BELLEKTE_EN_COK: commit models kept in memory (16 GB RAM)
_lock, _made, _producing = threading.RLock(), OrderedDict(), {}


def hooks():
    return registry().model_hooks()


def resolve(root: Path, commit: str | None) -> str:
    return git.git("rev-parse", "--verify", f"{commit or 'HEAD'}^{{commit}}", cwd=root)


@contextlib.contextmanager
def at_commit(root: Path, sha: str):
    """The work folder as committed at `sha`: the folder itself when that is HEAD and clean, else a detached
    temporary worktree (removed afterwards; the agent's worktree is never touched)."""
    if sha == git.head(root) and not dirty(root):
        yield root
        return
    tmp, rel = Path(tempfile.mkdtemp(prefix="mekanik-panel-")), git.git("rev-parse", "--show-prefix", cwd=root)
    git.git("worktree", "add", "-q", "--detach", str(tmp / "wt"), sha, cwd=root)
    try:
        yield tmp / "wt" / rel.rstrip("/") if rel else tmp / "wt"
    finally:
        try:
            git.git("worktree", "remove", "--force", str(tmp / "wt"), cwd=root)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def _production(key: str) -> threading.Lock:
    with _lock:
        return _producing.setdefault(key, threading.Lock())


def model(root: Path, sha: str) -> tuple | None:
    """(view, parts) of the commit, or None without model hooks or model."""
    if not (h := hooks()):
        return None
    key = h.signature(root, sha)
    with _production(key):
        with _lock:
            if key in _made:
                _made.move_to_end(key)
                return _made[key]
        with at_commit(root, sha) as d:
            view = load_work(d)
            got = (view, parts) if (parts := h.build(view)) else None
        with _lock:
            _made[key] = got
            while len(_made) > MEMORY:
                _made.popitem(last=False)
        return got


def tessellation(root: Path, sha: str) -> bytes | None:
    """The viewer's JSON as stored (decoding and encoding a few MB would take seconds)."""
    if not (h := hooks()):
        return None
    path = cache.root() / (key := h.signature(root, sha)) / "tessellation.json"
    if not path.exists():
        if not (got := model(root, sha)):
            return None
        with _production("tess-" + key):
            if not path.exists():
                h.write_tessellation(got[1], cache.entry(key) / "tessellation.json")
        cache.prune(keep=key)
    (path.parent / cache.MARK).touch()
    return path.read_bytes()


def markers(root: Path, sha: str, results: list[dict], cards: list[dict]) -> list[dict]:
    """Viewer markers of the package's located records (mech: fits): position and state from the check results and
    the cards about the record — fail (a failed result or a rejected card) | review (an open card) | pass."""
    if not (h := hooks()) or not h.has("fit_axes") or not (got := model(root, sha)):
        return []
    out = []
    for ref, axis in h.fit_axes(*got).items():
        card = next((c for c in cards if ref in (c.get("subject") or {}).values()), None)
        why = [r["reason"] for r in results if r.get("ref") == ref and r["status"] != "pass"]
        state = "fail" if why or (card and card.get("status") == "rejected") else "review" if card and card.get(
            "status") in ("open", "awaiting_reply") else "pass"
        out.append({"id": ref, "status": state, "position": list(axis["center"]), "axis": list(axis["axis"]),
                    "card": card and card["id"], "reasons": why})
    return out


def section(root: Path, sha: str, ref: str) -> str | None:
    """Dimensioned section of a located record through its axis (SVG), None when the model has no such axis."""
    if not (h := hooks()) or not h.has("fit_section") or not (got := model(root, sha)):
        return None
    axis = h.fit_axes(*got).get(ref)
    return h.fit_section(got[1], axis, ref) if axis else None


# ------------------------------------------------------------------ measurement from the exact solids (OCCT, lazy)

def _shape(parts: dict, path: str):
    """'/Group/<part>/faces/faces_3' → (kind, OCCT shape); the order is ocp_tessellate's, as in the viewer."""
    from ocp_tessellate.ocp_utils.topology import get_edges, get_faces, get_vertices

    bits = [p for p in path.split("/") if p]
    for kind, fn in (("faces", get_faces), ("edges", get_edges), ("vertices", get_vertices)):
        if kind in bits:
            i = bits.index(kind)
            return kind, list(fn(parts[bits[i - 1]].wrapped))[int(bits[-1].rsplit("_", 1)[1])]
    return "solid", parts[bits[-1]].wrapped


def _xyz(p) -> list[float]:
    return [round(p.X(), 6), round(p.Y(), 6), round(p.Z(), 6)]


def _props(s, kind: str):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    pr = GProp_GProps()
    {"faces": BRepGProp.SurfaceProperties_s, "edges": BRepGProp.LinearProperties_s}.get(
        kind, BRepGProp.VolumeProperties_s)(s, pr)
    return pr


def _point(s, kind: str):
    from OCP.BRep import BRep_Tool

    return BRep_Tool.Pnt_s(s) if kind == "vertices" else _props(s, kind).CentreOfMass()


def properties(parts: dict, path: str) -> dict:
    from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Circle, GeomAbs_Cylinder, GeomAbs_Line, GeomAbs_Plane

    kind, s = _shape(parts, path)
    out, geom = [], {"vertices": "Point", "solid": "Solid"}.get(kind, "Other")
    if kind == "edges":
        if (c := BRepAdaptor_Curve(s)).GetType() == GeomAbs_Circle:
            geom, ci = "Circle", c.Circle()
            out.append({"center": _xyz(ci.Location()), "radius": ci.Radius(), "diameter": 2 * ci.Radius()})
        geom = "Line" if c.GetType() == GeomAbs_Line else geom
        out.append({"length": _props(s, kind).Mass()})
    elif kind == "faces":
        a = BRepAdaptor_Surface(s)
        if a.GetType() == GeomAbs_Cylinder:
            geom, ax = "Cylinder", a.Cylinder().Axis()
            out.append({"center": _xyz(ax.Location()), "radius": a.Cylinder().Radius(),
                        "diameter": 2 * a.Cylinder().Radius(), "axis": _xyz(ax.Direction())})
        elif a.GetType() == GeomAbs_Plane:
            geom = "Plane"
            out.append({"normal": _xyz(a.Plane().Axis().Direction())})
        out.append({"area": _props(s, kind).Mass()})
    elif kind == "solid":
        out.append({"volume": _props(s, kind).Mass()})
    return {"type": "backend_response", "subtype": "tool_response", "tool_type": "PropertiesMeasurement",
            "shape_type": {"faces": "Face", "edges": "Edge", "vertices": "Vertex", "solid": "Solid"}[kind],
            "geom_type": geom, "refpoint": _xyz(_point(s, kind)), "result": out, "source": "exact"}


def distance(parts: dict, a: str, b: str, center: bool = False) -> dict:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    (k1, s1), (k2, s2) = _shape(parts, a), _shape(parts, b)
    if center:
        p1, p2 = _point(s1, k1), _point(s2, k2)
        d = p1.Distance(p2)
    else:
        (ds := BRepExtrema_DistShapeShape(s1, s2)).Perform()
        p1, p2, d = ds.PointOnShape1(1), ds.PointOnShape2(1), ds.Value()
    x, y = _xyz(p1), _xyz(p2)
    return {"type": "backend_response", "subtype": "tool_response", "tool_type": "DistanceMeasurement",
            "refpoint1": x, "refpoint2": y, "source": "exact",
            "result": [{"distance": d, "⇒ X | Y | Z": [abs(y[i] - x[i]) for i in range(3)],
                        "info": "center" if center else "min"}, {"point 1": x, "point 2": y}]}


def measure(root: Path, sha: str, tool: str, paths: list[str], center: bool = False) -> dict | None:
    if not paths or not (got := model(root, sha)):
        return None
    if tool == "DistanceMeasurement" and len(paths) >= 2:
        return distance(got[1], paths[0], paths[1], center)
    return properties(got[1], paths[0])


def cylinders(root: Path, sha: str) -> list[dict]:
    """Cylindrical faces of every part with their exact diameters (the measurement panel's list)."""
    if not (got := model(root, sha)):
        return []
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    from ocp_tessellate.ocp_utils.topology import get_faces

    return [{"part": name, "face": i, "path": f"/Group/{name}/faces/faces_{i}", "diameter": 2 * a.Cylinder().Radius()}
            for name, s in got[1].items() for i, f in enumerate(get_faces(s.wrapped))
            if (a := BRepAdaptor_Surface(f)).GetType() == GeomAbs_Cylinder]
