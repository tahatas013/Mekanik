# SPDX-License-Identifier: AGPL-3.0-or-later
"""Geometry of the checks (old girisim.ag/manifold, kayitsiz_gecme.silindirler/_es_eksen): closed solids,
cylinder axes. Imports OCCT, trimesh and manifold3d."""

from __future__ import annotations

import math

import manifold3d as m3d
import numpy as np
from mekanik.core.checks.rules import limit
from OCP.BRepAdaptor import BRepAdaptor_Surface

from .export import clean_mesh


def mesh(shape):
    """The check mesh: the same clean mesh as the STL, at the SOLID-01 mesh tolerance."""
    return clean_mesh(shape, limit("SOLID-01", "mesh_tolerance"))


def closed_solid(shape) -> tuple[m3d.Manifold | None, bool, bool]:
    """(manifold or None when not a valid closed solid, BRep valid, mesh watertight)."""
    t = mesh(shape)
    mf = m3d.Manifold(m3d.Mesh(vert_properties=t.vertices.astype(np.float32), tri_verts=t.faces.astype(np.uint32)))
    brep = shape.isValid()
    return (mf if brep and t.is_watertight and mf.status() == m3d.Error.NoError else None), brep, t.is_watertight


def coaxial(a: dict, b: dict, tol: dict) -> bool:
    da, db = a["dir"], b["dir"]
    cross = np.cross(da, db)
    if math.asin(min(1.0, float(np.linalg.norm(cross)))) > math.radians(tol["angle_deg"]):
        return False
    return float(np.linalg.norm(np.cross(np.subtract(b["p"], a["p"]), da))) <= tol["axis_distance"]


def cylinders(shape, tol: dict) -> list[dict]:
    """Cylindrical faces as {d: diameter, p: axis point, dir: axis direction}; a face split by its seam counts once."""
    out: list[dict] = []
    for f in shape.Faces():
        if f.geomType() != "CYLINDER":
            continue
        cy = BRepAdaptor_Surface(f.wrapped).Cylinder()
        p, d = cy.Axis().Location(), cy.Axis().Direction()
        s = {"d": 2 * cy.Radius(), "p": (p.X(), p.Y(), p.Z()), "dir": (d.X(), d.Y(), d.Z())}
        if not any(coaxial(s, o, tol) and abs(s["d"] - o["d"]) < tol["match"] for o in out):
            out.append(s)
    return out
