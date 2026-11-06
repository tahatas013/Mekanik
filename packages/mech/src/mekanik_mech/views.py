# SPDX-License-Identifier: AGPL-3.0-or-later
"""Drawings from the model (old `gorsel.py`): isometric view with hidden lines, and a dimensioned section in
technical-drawing style (white ground, thin black lines, 45° hatching, arrowed dimensions, title with scale)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from mekanik.core.i18n import num, t

# source: assumption — page layout (px, pt); drawing settings, not engineering values
PAGE, MARGIN, TITLE_Y, HATCH, ARROW = (640, 480), 60, 28, 6, 7
# source: standard:ISO 5455 — preferred scales; the section takes the largest that fits the page
SCALES = [(10, 1), (5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10)]
PX_MM = 96 / 25.4   # source: standard:CSS 2.1 — px per mm


@dataclass
class Dim:
    """Dimension between two 3D points; `offset` moves the dimension line off a–b (mm)."""
    a: tuple
    b: tuple
    text: str
    offset: float = 0.0


def isometric_svg(parts: dict) -> str:
    from cadquery.occ_impl.exporters.svg import getSVG

    asm = cq.Assembly()
    for name, s in parts.items():
        asm.add(s, name=name)
    return getSVG(asm.toCompound(), {"width": PAGE[0], "height": PAGE[1], "marginLeft": 20, "marginTop": 20,
                                     "showAxes": False, "projectionDir": (1, -1, 0.8), "strokeWidth": 0.4,
                                     "showHidden": True, "hiddenColor": (160, 160, 160)})


def isometric(parts: dict, path: Path) -> Path:
    Path(path).write_text(isometric_svg(parts), encoding="utf-8")
    return Path(path)


def _wire_points(w, step: float = 0.2) -> list:
    """A wire sampled end to end in edge order (BRepAdaptor_CompCurve).
    source: assumption — drawing setting: 0.2 mm spacing, 8–2000 points per wire."""
    from OCP.BRepAdaptor import BRepAdaptor_CompCurve

    c = BRepAdaptor_CompCurve(w.wrapped)
    a, b = c.FirstParameter(), c.LastParameter()
    n = max(8, min(2000, int(w.Length() / step)))
    return [cq.Vector(p.X(), p.Y(), p.Z()) for p in (c.Value(a + (b - a) * i / n) for i in range(n + 1))]


def section(parts: dict, center=(0, 0, 0), normal=(0, 1, 0), up=(0, 0, 1), dims=(), name: str = "A–A",
            width: float | None = None) -> str:
    """Cuts the parts with a plane; section faces hatched (adjacent parts opposite ways) and dimensioned."""
    o, n = cq.Vector(*center), cq.Vector(*normal).normalized()
    ey = (cq.Vector(*up) - n * cq.Vector(*up).dot(n)).normalized()
    ex = ey.cross(n).normalized()
    size = width or 1000.0   # source: assumption — a plane larger than any part (mm), drawing setting
    plane = cq.Face.makePlane(size, size, basePnt=o, dir=n)

    def p2(v):
        d = (v if isinstance(v, cq.Vector) else cq.Vector(*v)) - o
        return d.dot(ex), d.dot(ey)

    faces = [(pn, [[p2(v) for v in _wire_points(w)] for w in (f.outerWire(), *f.innerWires())])
             for pn, s in parts.items() for f in s.intersect(plane).Faces()]
    pts = [p for _, rings in faces for r in rings for p in r] + [p2(x) for d in dims for x in (d.a, d.b)]
    if not pts:
        raise ValueError(t("mech.view.empty_section"))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w_mm, h_mm = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    area = (PAGE[0] - 2 * MARGIN, PAGE[1] - 2 * MARGIN - TITLE_Y)
    sc = next(((a, b) for a, b in SCALES if w_mm * PX_MM * a / b <= area[0] and h_mm * PX_MM * a / b <= area[1]),
              SCALES[-1])
    k = PX_MM * sc[0] / sc[1]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2

    def P(p):
        return PAGE[0] / 2 + (p[0] - cx) * k, TITLE_Y + MARGIN + area[1] / 2 - (p[1] - cy) * k

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE[0]}" height="{PAGE[1]}" '
         f'viewBox="0 0 {PAGE[0]} {PAGE[1]}" font-family="Geist, Arial, sans-serif">',
         '<rect width="100%" height="100%" fill="#fff"/>',
         '<defs>' + "".join(
             f'<pattern id="hatch{i}" width="{HATCH}" height="{HATCH}" patternUnits="userSpaceOnUse" '
             f'patternTransform="rotate({ang})"><line x1="0" y1="0" x2="0" y2="{HATCH}" stroke="#000" '
             'stroke-width="0.5"/></pattern>' for i, ang in enumerate((45, 135))),
         f'<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="{ARROW}" markerHeight="{ARROW}" '
         'orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="#000"/></marker></defs>',
         f'<text x="{MARGIN}" y="{TITLE_Y}" font-size="13" font-weight="600">'
         f'{t("mech.view.section", name=name, scale=f"{sc[0]}:{sc[1]}")}</text>']
    alt = {pn: i % 2 for i, pn in enumerate(dict.fromkeys(p for p, _ in faces))}
    for pn, rings in faces:
        d = " ".join("M" + " L".join(f"{P(p)[0]:.2f},{P(p)[1]:.2f}" for p in r) + " Z" for r in rings)
        s.append(f'<path d="{d}" fill="url(#hatch{alt[pn]})" fill-rule="evenodd" stroke="#000" stroke-width="0.8">'
                 f'<title>{pn}</title></path>')
    for dm in dims:
        a, b = p2(dm.a), p2(dm.b)
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / L * dm.offset, (b[0] - a[0]) / L * dm.offset
        A, B = P((a[0] + nx, a[1] + ny)), P((b[0] + nx, b[1] + ny))
        if dm.offset:
            for u, v in ((P(a), A), (P(b), B)):
                s.append(f'<line x1="{u[0]:.2f}" y1="{u[1]:.2f}" x2="{v[0]:.2f}" y2="{v[1]:.2f}" stroke="#000" '
                         'stroke-width="0.4"/>')
        s.append(f'<line x1="{A[0]:.2f}" y1="{A[1]:.2f}" x2="{B[0]:.2f}" y2="{B[1]:.2f}" stroke="#000" '
                 'stroke-width="0.6" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
        ang = math.degrees(math.atan2(B[1] - A[1], B[0] - A[0]))
        ang += 180 if ang > 90 or ang < -90 else 0
        mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
        s.append(f'<text x="{mx:.2f}" y="{my - 4:.2f}" font-size="12" text-anchor="middle" '
                 f'transform="rotate({ang:.1f} {mx:.2f} {my:.2f})" paint-order="stroke" stroke="#fff" '
                 f'stroke-width="3">{dm.text}</text>')
    s.append(f'<text x="{PAGE[0] - MARGIN}" y="{PAGE[1] - 16}" font-size="10" text-anchor="end" fill="#000">mm</text>')
    return "\n".join(s + ["</svg>"])


def dia_dim(center, perp, d: float, offset: float = 0.0, prefix: str = "Ø") -> Dim:
    """Diameter in the section plane: from the centre ±d/2 along `perp`."""
    c, u = cq.Vector(*center), cq.Vector(*perp).normalized()
    return Dim((c - u * d / 2).toTuple(), (c + u * d / 2).toTuple(), f"{prefix}{num(d)}", offset)
