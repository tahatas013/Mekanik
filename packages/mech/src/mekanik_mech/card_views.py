# SPDX-License-Identifier: AGPL-3.0-or-later
"""Card figures from the model (old `kart_gorsel.py`). Card standard: a card without a visual cannot open.

A parameter is found in the model by sensitivity: its value is nudged, the model rebuilt and the changed faces
compared. A changed diameter gets a diameter dimension, a moved plane its distance to the facing surface, a moved
part the gap to its neighbour; a dimension line is drawn only when that distance equals the value itself.
Fit: dimensioned section · decision: options at one scale · flex, deviation: isometric · gate: last model.
The core writes, caches and attaches the figures; this module only draws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from html import escape

import cadquery as cq

from mekanik.core.i18n import num, t

from .fits import dims, fits, flexes
from .views import Dim, dia_dim, isometric_svg, section

# source: assumption — drawing layout (px) and colours; not engineering values
W, H, EDGE = 440, 270, 26
ACCENT = "#2F6FDE"
# source: assumption — geometric coincidence (mm, rad), face matching (mm), a found distance counts as the value
# itself within DIM_TOL (mm), label inset of a placement dimension from the part corner (mm, drawing setting)
EPS, MATCH, DIM_TOL, LABEL_INSET = 1e-6, 1e-3, 0.01, 5.0
VIEWS = {"top": ((1, 0, 0), (0, 1, 0)), "front": ((1, 0, 0), (0, 0, 1)), "side": ((0, 1, 0), (0, 0, 1))}


@dataclass
class Effect:
    """Trace of a parameter in the model."""
    name: str
    parts: list[str] = field(default_factory=list)
    faces: dict[str, list] = field(default_factory=dict)   # part → faces to highlight
    dir: str = "top"
    dim: Dim | None = None


def _face_sig(f) -> tuple:
    c = f.Center()
    return f.geomType(), round(c.x, 3), round(c.y, 3), round(c.z, 3), round(f.Area(), 3)


def _changed(old, new) -> list:
    sigs = {_face_sig(f) for f in new.Faces()}
    return [f for f in old.Faces() if _face_sig(f) not in sigs]


def _step(v: float, unit: str) -> float:
    # source: assumption — sensitivity step: 1 count, 5°, else 25 % of the value but at least 0.5
    return 1 if unit == "count" else 5.0 if unit == "deg" else max(abs(v) * 0.25, 0.5)


def _pick_dir(axis) -> str:
    x, y, z = (abs(v) for v in axis.toTuple())
    return "top" if z >= max(x, y) else "front" if y >= x else "side"


def best_dir(v) -> str:
    """The view that shows a direction longest on screen (a dimension must not point at the viewer)."""
    return max(VIEWS, key=lambda k: v.dot(cq.Vector(*VIEWS[k][0])) ** 2 + v.dot(cq.Vector(*VIEWS[k][1])) ** 2)


def _cyl(f):
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    c = BRepAdaptor_Surface(f.wrapped).Cylinder()
    p, d = c.Axis().Location(), c.Axis().Direction()
    return cq.Vector(p.X(), p.Y(), p.Z()), cq.Vector(d.X(), d.Y(), d.Z()), c.Radius()


def _same_axis(o1, d1, o2, d2) -> bool:
    off = o2 - o1
    return abs(abs(d1.dot(d2)) - 1) <= EPS and (off - d1 * off.dot(d1)).Length < MATCH


def _candidates(s, faces) -> list:
    """Distances starting at the given faces: (distance, start, end, direction, kind)."""
    out = []
    cyls = [(g, *_cyl(g)) for g in s.Faces() if g.geomType() == "CYLINDER"]
    for f in faces:
        if f.geomType() == "PLANE":
            n, c = f.normalAt(), f.Center()
            for g in s.Faces():
                if g.geomType() == "PLANE" and abs(abs(g.normalAt().dot(n)) - 1) < EPS:
                    if (d := abs((g.Center() - c).dot(n))) > EPS:
                        out.append((d, c, c - n * ((c - g.Center()).dot(n)), n, "plane"))
            for _, o, ax, r in cyls:
                if abs(ax.dot(n)) < EPS:
                    u = (o - c).dot(n)              # signed distance plane → axis
                    d = abs(u) - r                  # d < 0: a flat cut through the cylinder
                    if abs(d) > EPS:
                        out.append((abs(d), o - n * u, o - n * (r if u > 0 else -r), n, "cut" if d < 0 else "cyl"))
        elif f.geomType() == "CYLINDER":
            o, ax, r = _cyl(f)
            for g, o2, ax2, r2 in cyls:
                if g.isSame(f) or abs(abs(ax.dot(ax2)) - 1) > EPS:
                    continue
                perp = (o2 - o) - ax * (o2 - o).dot(ax)
                if perp.Length >= MATCH and (d := perp.Length - r - r2) > EPS:
                    u = perp.normalized()
                    a = o + ax * ((f.Center() - o).dot(ax)) + u * r
                    out.append((d, a, a + u * d, u, "gap"))
    return out


def _diameter(e: Effect, base: dict, moved: dict, v: float, step: float) -> Effect | None:
    for p in e.parts:
        new = [_cyl(g) for g in moved[p].Faces() if g.geomType() == "CYLINDER"]
        for f in e.faces[p]:
            if f.geomType() != "CYLINDER":
                continue
            o, ax, r = _cyl(f)
            if abs(2 * r - v) > DIM_TOL or not any(_same_axis(o, ax, o2, d2) and abs(r2 - r - step / 2) < EPS
                                                   for o2, d2, r2 in new):
                continue
            mid = o + ax * (f.BoundingBox().center - o).dot(ax)
            e.dir = _pick_dir(ax)
            u = cq.Vector(*VIEWS[e.dir][0])
            e.dim = Dim((mid - u * r).toTuple(), (mid + u * r).toTuple(), f"Ø{num(2 * r)}")
            e.parts, e.faces = [p], {p: [f]}
            return e
    return None


def _placement(e: Effect, base: dict, moved: dict, v: float, step: float) -> Effect | None:
    if not all(len(e.faces[p]) == len(base[p].Faces()) for p in e.parts):
        return None
    box = {p: s.BoundingBox() for p, s in base.items()}
    for p in e.parts:
        b, b2 = box[p], moved[p].BoundingBox()
        for q, k in box.items():
            if q == p or q not in moved:
                continue
            k2 = moved[q].BoundingBox()
            for axis, lo, hi, gap2 in (("y", k.ymax, b.ymin, b2.ymin - k2.ymax),
                                       ("x", k.xmax, b.xmin, b2.xmin - k2.xmax)):
                if abs(hi - lo - v) >= DIM_TOL or abs(gap2 - v - step) > DIM_TOL:   # nudged model: gap grows by step
                    continue
                c = max(b.xmin, k.xmin) + LABEL_INSET if axis == "y" else max(b.ymin, k.ymin) + LABEL_INSET
                e.dim = Dim((c, lo, 0), (c, hi, 0), num(v)) if axis == "y" else Dim((lo, c, 0), (hi, c, 0), num(v))
                e.dir, e.parts = "top", [q, p]
                return e
    return None


def _moved_face(e: Effect, base: dict, moved: dict, v: float, step: float) -> Effect | None:
    """To rule out a coincidence (another distance of the same value), the distance must also appear as
    v + step in the nudged model. A plane cutting a cylinder goes first."""
    for p in e.parts:
        check = [(d, n, kind) for d, _, _, n, kind in _candidates(moved[p], _changed(moved[p], base[p]))]
        for d, a, b, n, kind in sorted(_candidates(base[p], e.faces[p]), key=lambda x: (abs(x[0] - v), x[4] != "cut")):
            if abs(d - v) > DIM_TOL or not any(k2 == kind and abs(abs(n2.dot(n)) - 1) < EPS and
                                               abs(d2 - v - step) < DIM_TOL for d2, n2, k2 in check):
                continue
            e.dir, e.dim, e.parts = best_dir(b - a), Dim(a.toTuple(), b.toTuple(), num(v)), [p]
            return e
    return None


def _unmeasured(e: Effect, v: float) -> Effect:
    """Not a face-to-face distance (e.g. height of engraved digits): the changed faces are highlighted, the view looks
    onto them, and an approximate '≈' extent is drawn along their narrowest screen side."""
    p, areas = e.parts[0], {}
    for f in e.faces[p]:
        if f.geomType() == "PLANE":
            n = f.normalAt()
            k = max(VIEWS, key=lambda k: abs(n.dot(cq.Vector(*VIEWS[k][0]).cross(cq.Vector(*VIEWS[k][1])))))
            areas[k] = areas.get(k, 0) + f.Area()
    e.dir = max(areas, key=areas.get) if areas else "top"
    ex, ey = (cq.Vector(*x) for x in VIEWS[e.dir])
    bb = cq.Compound.makeCompound(e.faces[p]).BoundingBox()
    corners = [cq.Vector(x, y, z) for x in (bb.xmin, bb.xmax) for y in (bb.ymin, bb.ymax) for z in (bb.zmin, bb.zmax)]
    sx, sy = [c.dot(ex) for c in corners], [c.dot(ey) for c in corners]
    a = ex * min(sx) + ey * min(sy)
    b = ex * min(sx) + ey * max(sy) if max(sy) - min(sy) <= max(sx) - min(sx) else ex * max(sx) + ey * min(sy)
    e.dim, e.parts = Dim(a.toTuple(), b.toTuple(), f"≈ {e.name} {num(v)}"), [p]
    return e


def param_effect(make, values: dict, name: str, unit: str, base: dict | None = None) -> Effect:
    """make(values) → {part: solid}. Where `name` acts in the model and the dimension that shows it."""
    v = values[name]
    step = _step(v, unit)
    base = base or make(values)
    moved = make({**values, name: v + step})
    e = Effect(name)
    for p, s in base.items():
        if p in moved and (d := _changed(s, moved[p])):
            e.parts.append(p)
            e.faces[p] = d
    if not e.parts:
        return e
    pat = getattr(make, "prefer", {}).get(name)
    if pat and any(fnmatch(q, pat) for q in e.parts):
        e.parts = [q for q in e.parts if fnmatch(q, pat)]
    e.parts.sort(key=lambda q: -base[q].Volume())   # largest part first: small dimensions read better
    return ((_diameter(e, base, moved, v, step) if unit == "mm" else None) or _placement(e, base, moved, v, step)
            or _moved_face(e, base, moved, v, step) or _unmeasured(e, v))


# ------------------------------------------------------------------ orthographic view

def _edge_points(e, n: int = 24) -> list:
    return [e.startPoint(), e.endPoint()] if e.geomType() == "LINE" else [e.positionAt(i / n) for i in range(n + 1)]


def _silhouettes(s, look, ex, ey) -> list:
    """Outlines of cylinders whose axis is across the view (no edge there, but the view must draw the border)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepClass import BRepClass_FaceClassifier
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.gp import gp_Pnt2d
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON

    out = []
    for f in s.Faces():
        if f.geomType() != "CYLINDER":
            continue
        o, d, r = _cyl(f)
        if abs(d.dot(look)) > EPS:
            continue
        n3 = look.cross(d).normalized()
        ts = [(cq.Vector(*x.toTuple()) - o).dot(d) for x in f.Vertices()] or [0.0]
        t0, t1 = min(ts), max(ts)
        if t1 - t0 < EPS:
            continue
        surf = BRep_Tool.Surface_s(f.wrapped)
        for side in (1, -1):
            proj = GeomAPI_ProjectPointOnSurf((o + d * ((t0 + t1) / 2) + n3 * (r * side)).toPnt(), surf)
            if proj.NbPoints() == 0:
                continue
            u, v = proj.LowerDistanceParameters()
            if BRepClass_FaceClassifier(f.wrapped, gp_Pnt2d(u, v), EPS).State() not in (TopAbs_IN, TopAbs_ON):
                continue   # the outline point is on the cut-away part of the face
            a, b = o + d * t0 + n3 * (r * side), o + d * t1 + n3 * (r * side)
            out.append([(a.dot(ex), a.dot(ey)), (b.dot(ex), b.dot(ey))])
    return out


def label(x, y, s, size=10.5, fill=ACCENT, anchor="start", halo=True, extra="") -> str:
    h = ' paint-order="stroke" stroke="#FAFBFC" stroke-width="3"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{h}{extra}>'
            f'{s}</text>')


def view_svg(parts: dict, direction: str, dims=(), highlight: dict | None = None, title: str = "", extra: str = "",
             bed: tuple | None = None, diameters: bool = False, ground: bool = False, names: bool = False,
             outside: bool = False, frame: tuple | None = None, scale_bar: bool = False) -> str:
    """Orthographic view: thin grey edges, highlighted faces' edges thick blue, arrowed dimensions.
    diameters: diameters of cylinders seen end-on · ground: bed line at Z = 0 · names: part names ·
    outside: dimension lines outside the part with extension lines · frame (x0, x1, y0, y1): common frame in view
    coordinates (options at one scale) · bed (x, y): bed rectangle · scale_bar: mm bar bottom left."""
    ex, ey = (cq.Vector(*v) for v in VIEWS[direction])
    look = ex.cross(ey)
    lines, hl = [], []
    for name, s in parts.items():
        lines += [[(v.dot(ex), v.dot(ey)) for v in _edge_points(e)] for e in s.Edges()]
        lines += _silhouettes(s, look, ex, ey)
        hl += [[(v.dot(ex), v.dot(ey)) for v in _edge_points(e)]
               for f in (highlight or {}).get(name, []) for e in f.Edges()]
    pts = [p for c in lines for p in c] + [(cq.Vector(*d.a).dot(ex), cq.Vector(*d.a).dot(ey)) for d in dims]
    pts += [(0, 0), bed] if bed else []
    xs, ys = ([frame[0], frame[1]], [frame[2], frame[3]]) if frame else ([p[0] for p in pts], [p[1] for p in pts])
    w, h = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    m = EDGE + (26 if outside else 0)   # room for a dimension moved outside
    k = min((W - 2 * m) / w, (H - 2 * m - 14) / h)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2

    def P(x, y):
        return W / 2 + (x - cx) * k, 14 + H / 2 - (y - cy) * k

    def path(c):
        return "M" + " L".join(f"{P(*p)[0]:.1f},{P(*p)[1]:.1f}" for p in c)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Geist Mono, monospace">',
         '<defs><marker id="ko" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" '
         f'orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{ACCENT}"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#FAFBFC"/>']
    if title:
        s.append(label(10, 14, escape(title), 9.5, "#5F6873", halo=False))
    if bed:
        (x0, y0), (x1, y1) = P(0, 0), P(*bed)
        s.append(f'<rect x="{min(x0, x1):.1f}" y="{min(y0, y1):.1f}" width="{abs(x1 - x0):.1f}" '
                 f'height="{abs(y1 - y0):.1f}" fill="#F1F3F5" stroke="#8B939C" stroke-dasharray="4 3" '
                 'stroke-width="0.8"/>')
    s.append(f'<path d="{" ".join(path(c) for c in lines)}" fill="none" stroke="#8B939C" stroke-width="0.6"/>')
    if hl:
        s.append(f'<path d="{" ".join(path(c) for c in hl)}" fill="none" stroke="{ACCENT}" stroke-width="1.6"/>')
    scr = [P(*q) for c in lines for q in c]
    left, bottom = min(x for x, _ in scr), max(y for _, y in scr)
    arrow = f'stroke="{ACCENT}" stroke-width="1"'
    for d in dims:
        a, b = cq.Vector(*d.a), cq.Vector(*d.b)
        A, B = P(a.dot(ex), a.dot(ey)), P(b.dot(ex), b.dot(ey))
        vertical = abs(B[1] - A[1]) >= abs(B[0] - A[0])
        if outside and abs(A[0] - B[0]) + abs(A[1] - B[1]) > 0.01:   # source: assumption — px, not zero length
            if vertical:   # like a drawing: dimension line outside the part, with extension lines
                x = left - 16
                s.append(f'<path d="M{A[0]:.1f},{A[1]:.1f} H{x - 4:.1f} M{B[0]:.1f},{B[1]:.1f} H{x - 4:.1f}" '
                         f'stroke="{ACCENT}" stroke-width="0.6" stroke-dasharray="2 2" fill="none"/>')
                A, B = (x, A[1]), (x, B[1])
            else:
                y = bottom + 16
                s.append(f'<path d="M{A[0]:.1f},{A[1]:.1f} V{y + 4:.1f} M{B[0]:.1f},{B[1]:.1f} V{y + 4:.1f}" '
                         f'stroke="{ACCENT}" stroke-width="0.6" stroke-dasharray="2 2" fill="none"/>')
                A, B = (A[0], y), (B[0], y)
            L = ((B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2) ** 0.5
            if L < 14:   # short dimension: arrows point inwards from outside
                ux, uy = ((B[0] - A[0]) / L, (B[1] - A[1]) / L) if L > EPS else (0, 1)
                s.append(f'<line x1="{A[0] - ux * 14:.1f}" y1="{A[1] - uy * 14:.1f}" x2="{A[0]:.1f}" y2="{A[1]:.1f}" '
                         f'{arrow} marker-end="url(#ko)"/><line x1="{B[0] + ux * 14:.1f}" y1="{B[1] + uy * 14:.1f}" '
                         f'x2="{B[0]:.1f}" y2="{B[1]:.1f}" {arrow} marker-end="url(#ko)"/>')
                tx, ty = (A[0] - 8, (A[1] + B[1]) / 2 + 3) if vertical else ((A[0] + B[0]) / 2, A[1] + 16)
                s.append(label(tx, ty, d.text, anchor="end" if tx < A[0] else "middle", halo=False))
                continue
            mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
            s.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" {arrow} '
                     'marker-start="url(#ko)" marker-end="url(#ko)"/>')
            s.append(label(mx - 6, my + 3, d.text, anchor="end") if vertical
                     else label(mx, my + 14, d.text, anchor="middle"))
            continue
        s.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" {arrow} '
                 'marker-start="url(#ko)" marker-end="url(#ko)"/>')
        s.append(label((A[0] + B[0]) / 2 + 4, (A[1] + B[1]) / 2 - 5, d.text))
    if ground:
        (a0, b0), (a1, _) = P(min(xs), 0), P(max(xs), 0)
        s.append(f'<line x1="{a0 - 10:.1f}" y1="{b0 + 1:.1f}" x2="{a1 + 10:.1f}" y2="{b0 + 1:.1f}" stroke="#3B434C" '
                 f'stroke-width="2.4"/>' + label(a1 + 10, b0 + 13, t("mech.view.bed"), 9, "#5F6873", "end", False))
    if diameters:
        seen = set()
        for sk in parts.values():
            for f in sk.Faces():
                if f.geomType() == "CYLINDER" and abs(abs((c := _cyl(f))[1].dot(look)) - 1) <= EPS:
                    if (key := (round(c[0].dot(ex), 2), round(c[0].dot(ey), 2))) not in seen:
                        seen.add(key)
                        X, Y = P(*key)
                        s.append(label(X, Y + 4.5, num(2 * c[2]), 13, anchor="middle", halo=False,
                                       extra=' font-weight="600"'))
    if names:
        for name, sk in parts.items():
            b = sk.BoundingBox()
            X, Y = P(min(cq.Vector(b.xmin, b.ymin, b.zmin).dot(ex), cq.Vector(b.xmax, b.ymax, b.zmax).dot(ex)),
                     max(cq.Vector(b.xmin, b.ymin, b.zmin).dot(ey), cq.Vector(b.xmax, b.ymax, b.zmax).dot(ey)))
            s.append(label(X, Y - 3, escape(name), 12, "#5F6873", halo=False))
    if scale_bar:
        L = next((x for x in (1, 2, 5, 10, 20, 50, 100, 200) if x * k >= 50), 200)
        s.append(f'<path d="M{EDGE},{H - 12} V{H - 8} H{EDGE + L * k:.1f} V{H - 12}" fill="none" stroke="#3B434C" '
                 f'stroke-width="1"/>' + label(EDGE + L * k + 5, H - 8, f"{L} mm", 10, "#3B434C", halo=False))
    return "\n".join(s + [extra, "</svg>"])


# ------------------------------------------------------------------ fit section, figures per card type

def fit_axes(view, model: dict) -> dict[str, dict]:
    """Per fit, the coaxial cylinder pair in its two parts that matches the hole and shaft diameters:
    {fit id: {center, axis, hole, shaft, parts}}; a fit not found in the model is left out."""
    from .geom import coaxial, cylinders
    from mekanik.core.checks.rules import limit

    tol = {k: limit("UNREG-01", k) for k in ("angle_deg", "axis_distance", "match")}
    cyl = {name: cylinders(s, tol) for name, s in model.items()}
    out = {}
    for f in fits(view):
        if any(p not in model for p in f["parts"]):
            continue
        hole, shaft = dims(f, view.params)
        a = [c for c in cyl[f["parts"][0]] if hole and abs(c["d"] - hole) <= tol["match"]]
        b = [c for c in cyl[f["parts"][1]] if abs(c["d"] - shaft) <= tol["match"]] if shaft else a
        pair = next(((x, y) for x in a for y in b if coaxial(x, y, tol)), None)
        if pair:
            d, p0 = cq.Vector(*pair[0]["dir"]).normalized(), cq.Vector(*pair[0]["p"])
            mid = p0 + d * (model[f["parts"][0]].BoundingBox().center - p0).dot(d)   # middle of the hole's part
            out[f["id"]] = {"center": mid.toTuple(), "axis": d.toTuple(), "hole": hole, "shaft": shaft,
                            "parts": f["parts"]}
    return out


def fit_section(model: dict, e: dict, name: str) -> str:
    """Dimensioned section of a fit through its axis."""
    d = cq.Vector(*e["axis"])
    # source: assumption — any direction not along the axis gives the cut plane; Z unless the axis is near Z
    perp = (d.cross(cq.Vector(0, 0, 1)) if abs(d.z) < 0.9 else d.cross(cq.Vector(1, 0, 0))).normalized()
    c = cq.Vector(*e["center"])
    ds = [dia_dim(c.toTuple(), perp.toTuple(), e["hole"])] + (
        [dia_dim((c - d * 2).toTuple(), perp.toTuple(), e["shaft"])] if e["shaft"] else [])
    return section({p: model[p] for p in e["parts"] if p in model}, c.toTuple(), d.cross(perp).toTuple(), d.toTuple(),
                   ds, name)


def text_svg(title: str, rows: list[str]) -> str:
    """A text figure (e.g. a value that enters calculations only)."""
    h = 60 + 22 * len(rows)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" font-family="Geist, sans-serif">',
         f'<rect width="{W}" height="{h}" fill="#FAFBFC"/>', label(10, 14, escape(title), 9.5, "#5F6873", halo=False)]
    s += [label(24, 48 + 22 * i, escape(r), 15 if i == 0 else 12.5, ACCENT if i == 0 else "#1B1F24", halo=False,
                extra=f' font-weight="{600 if i == 0 else 400}"') for i, r in enumerate(rows)]
    return "\n".join(s + ["</svg>"])


def param_figures(view, names: list[str], numbered: bool, calc_uses: dict | None = None) -> tuple[list, list]:
    """One view per value: changed faces blue, dimension outside the part with its value. A value without a trace in
    the model is drawn as a calculation input if a calculation uses it, else returned as untraced."""
    from .model import builder

    make = builder(view) if (view.root / "model" / "model.py").exists() else None
    vals = {a: p.value for a, p in view.params.items()}
    base = (make(vals) if make else None) or {}
    figs, untraced = [], []
    for i, name in enumerate(names):
        p = view.params[name]
        e = param_effect(make, vals, name, p.unit, base) if base else Effect(name)
        head = (f"{i + 1} · " if numbered else "") + f"{name} = {num(p.value)} {p.unit}"
        if not e.parts:
            if name in (calc_uses or {}):
                title = f"{head} · {t('mech.view.calc_input')}"
                rows = [f"{name} = {num(p.value)} {p.unit}", t("mech.view.calc_list")]
                rows += [f"• {c}" for c in calc_uses[name]]
                figs.append((title, text_svg(title.upper(), rows)))
            else:
                untraced.append(name)
            continue
        title = f"{head} · {' + '.join(e.parts)} · {t('mech.view.dir.' + e.dir)}" + (
            "" if e.dim else t("mech.view.blue"))
        hl = {q: e.faces.get(q, []) for q in e.parts   # when everything moved, a highlight says nothing
              if not e.dim or len(e.faces.get(q, [])) <= len(base[q].Faces()) / 2}
        figs.append((title, view_svg({q: base[q] for q in e.parts}, e.dir, [e.dim] if e.dim else [], hl, title.upper(),
                                     outside=True)))
    return figs, untraced


def _slice(sel: dict, parts: dict) -> dict:
    """Selection {"section": {x|y|z: position}}: a thin slice of the model at that plane."""
    (axis, pos), = sel["section"].items()
    k, B = 0.2, 2000.0   # source: assumption — slice half thickness and a large enough box (mm, drawing setting)
    i = "xyz".index(axis)
    corner = tuple(pos - k if j == i else -B / 2 for j in range(3))
    size = tuple(2 * k if j == i else B for j in range(3))
    cut = {a: s.intersect(cq.Solid.makeBox(*size, pnt=cq.Vector(*corner))) for a, s in parts.items()}
    return {a: s for a, s in cut.items() if s.Volume() > 0} or cut


def option_figures(view, card: dict, option_values: dict | None = None) -> list:
    """Decision options side by side in one frame (same scale) with a scale bar. `option_values` {option id:
    {param: value}} comes from the core's decision module (E-17, E-21); without it, the work's values minus every
    value any option changes, plus the option's own values."""
    from .model import builder

    sel = card.get("visual_selection") or {}
    dec = next((d for d in view.decisions if d.get("id") == (card.get("subject") or {}).get("decision")), {})
    opts = dec.get("options") or card.get("options") or []
    own = {o["id"]: {v["name"]: v["quantity"]["value"] for v in o.get("values") or []} for o in opts}
    changed = {a for v in own.values() for a in v}
    base = {a: p.value for a, p in view.params.items() if a not in changed}
    direction = sel.get("view", "top")
    models = []
    for o in opts:
        values = (option_values or {}).get(o["id"]) or {**base, **own[o["id"]]}
        m = builder(view, **(o.get("model_definition") or {}))(values)
        sub = {a: s for a, s in m.items() if any(fnmatch(a, p) for p in sel.get("parts") or ["*"])} or m
        bb = cq.Compound.makeCompound(list(sub.values())).BoundingBox()
        note = label(W - 10, 14, f"{num(bb.xlen)} × {num(bb.ylen)} × {num(bb.zlen)} mm", 11, "#1B1F24", "end", False)
        if sel.get("section"):
            sub, note = _slice(sel, sub), ""
        models.append((o["id"], sub, note))
    ex, ey = (cq.Vector(*v) for v in VIEWS[direction])
    boxes = [cq.Compound.makeCompound(list(sub.values())).BoundingBox() for _, sub, _ in models]
    corners = [cq.Vector(x, y, z) for bb in boxes for x in (bb.xmin, bb.xmax) for y in (bb.ymin, bb.ymax)
               for z in (bb.zmin, bb.zmax)]
    frame = (min(c.dot(ex) for c in corners), max(c.dot(ex) for c in corners),
             min(c.dot(ey) for c in corners), max(c.dot(ey) for c in corners)) if corners else None
    (axis, pos), = (sel.get("section") or {"": 0}).items()
    where = t("mech.view.slice", axis=axis.upper(), pos=num(pos)) if axis else t(f"mech.view.dir.{direction}")
    return [(oid, view_svg(sub, direction, title=t("mech.view.option", id=oid.upper(), where=where),
                           diameters=sel.get("diameters", True), names=not sel.get("section"), extra=note, frame=frame,
                           scale_bar=True)) for oid, sub, note in models]


def card_visuals(view, card: dict, model: dict | None, option_values: dict | None = None,
                 calc_uses: dict | None = None) -> tuple[list, list] | None:
    """([(title, svg)], untraced params) for a card; None for a card mech does not draw (consistency, basis, model
    note, release, a gate without a model): the core or another package draws those. An empty figure list makes the
    card fail the card standard. `calc_uses` {param: [calc ids]} lets a value without a trace show its calculations."""
    typ, subj = card.get("type"), card.get("subject") or {}
    if typ == "assumption_list":
        return param_figures(view, subj.get("params", []), True, calc_uses)
    if typ in ("consistency", "basis_changed", "model_note", "release") or (typ == "gate" and not model):
        return None
    if subj.get("params") and typ not in ("mech:fit", "decision"):
        names = [a for a in subj["params"] if a in view.params and view.params[a].value is not None][:1]
        return param_figures(view, names, False, calc_uses) if names else ([], [])
    if not model:
        return [], []
    if typ == "gate":
        return [(t("mech.view.last_model"), isometric_svg(model))], []
    if typ == "mech:fit":
        e = fit_axes(view, model).get(subj.get("fit"))
        return ([(t("mech.view.fit_section", fit=subj["fit"]), fit_section(model, e, subj["fit"]))] if e else []), []
    if typ == "decision":
        figs = option_figures(view, card, option_values)
        bodies = [s.split("\n", 4)[-1] for _, s in figs]   # options must differ apart from their title
        return (figs if len(set(bodies)) == len(bodies) else []), []
    if typ not in ("mech:flex", "deviation"):
        return None
    parts = [e.get("part") for e in flexes(view) if e.get("id") == subj.get("flex")] or list(model)
    return [(t("mech.view.part"), isometric_svg({a: model[a] for a in parts if a in model}))], []
