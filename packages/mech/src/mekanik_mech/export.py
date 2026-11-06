# SPDX-License-Identifier: AGPL-3.0-or-later
"""Export (old `disari.py`): STEP assembly, clean STL mesh and viewer tessellation (ocp_tessellate)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import cadquery as cq

# source: assumption — STL mesh tolerances (mm, rad); revisit when the print profile is calibrated
STL_TOL, STL_ANGLE = 0.01, 0.1


def _tmp(path: Path) -> Path:
    return path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}")


def step(parts: dict, path: Path) -> Path:
    """All parts in one STEP assembly, by part name; atomic write."""
    asm = cq.Assembly()
    for name, s in parts.items():
        asm.add(s, name=name)
    tmp = _tmp(path).with_suffix(".step")
    asm.export(str(tmp))
    os.replace(tmp, path)
    return path


def clean_mesh(s, tol: float, angle: float = 0.1):
    """Triangle mesh of a solid, cleaned (E-29): OCCT leaves zero-area triangles and coincident points at the tips of
    filleted corners, so the mesh looks open though the geometry has no hole. Degenerate faces are dropped and
    points within 1e-5 mm merged (source: assumption — numerical tolerance)."""
    import numpy as np
    import trimesh

    v, f = s.tessellate(tol, angle)
    m = trimesh.Trimesh(np.array([p.toTuple() for p in v]), np.array(f), process=False)
    m.merge_vertices(digits_vertex=5)
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    return m


def stl(parts: dict, folder: Path) -> list[Path]:
    """Binary STL per part from the clean mesh; atomic write."""
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for name, s in parts.items():
        path, tmp = folder / f"{name}.stl", _tmp(folder / f"{name}.stl")
        tmp.write_bytes(clean_mesh(s, STL_TOL, STL_ANGLE).export(file_type="stl"))
        os.replace(tmp, path)
        out.append(path)
    return out


def tessellation(parts: dict) -> dict:
    """three-cad-viewer format {instances, shapes}; face and edge order is ocp_tessellate's get_faces/get_edges."""
    from OCP.BRepTools import BRepTools
    from ocp_tessellate.convert import tessellate_group, to_ocpgroup
    from ocp_tessellate.utils import numpy_to_buffer_json

    for s in parts.values():    # earlier STEP/STL/SVG triangulation must not change the result
        BRepTools.Clean_s(s.wrapped)
    group, instances = to_ocpgroup(*parts.values(), names=list(parts))
    mesh, shapes, _ = tessellate_group(group, instances)
    return numpy_to_buffer_json({"instances": mesh, "shapes": shapes})


def write_tessellation(parts: dict, path: Path) -> Path:
    tmp = _tmp(path)
    tmp.write_text(json.dumps(tessellation(parts)), encoding="utf-8")
    os.replace(tmp, path)
    return path


def write_cache(parts: dict, folder: Path) -> None:
    """Model output of a content signature (old akis.adim): model.step and tessellation.json, once."""
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / "tessellation.json").exists():
        step(parts, folder / "model.step")
        write_tessellation(parts, folder / "tessellation.json")
