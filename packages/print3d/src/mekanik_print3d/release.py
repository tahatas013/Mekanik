# SPDX-License-Identifier: AGPL-3.0-or-later
"""Print request (old akis.baski, tabla_temasi_kusuru; kart_gorsel yerleşim, tabla, baskı yönü, tahmin): release checks
BED-01, BED-02, SINGLE-01, release files and release card figures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from mekanik.core.checks.result import BLOCK, PASS, WARN, Result
from mekanik.core.checks.rules import limit
from mekanik.core.i18n import num, t
from mekanik_mech.fits import profile

# source: assumption — rough estimate without a slicer (E-23): PLA 1.24 g/cm³; the shell (walls, top/bottom) is solid
# 0.8 mm in from the surface; infill 15–25 %; flow 8–12 mm³/s; a thin part is all shell. Supports not included.
DENSITY_G_MM3, SHELL_MM, INFILL, FLOW_MM3_S = 1.24e-3, 0.8, (0.15, 0.25), (8.0, 12.0)


def _r(check: str, rule: str, status: str, key: str, ref=None, value=None, extra=None, **args) -> Result:
    return Result(f"print3d.{check}", rule, status, f"print3d.{key}", args, ref, value, extra or {})


def contact_defect(s, gap: float) -> dict | None:
    """The slicer sets the lowest point on the bed; a larger flat face facing down within `gap` above it stays in the
    air and the first layer does not hold (E-25). None: no defect."""
    zmin, contact, air = s.BoundingBox().zmin, 0.0, []
    for f in s.Faces():
        if f.geomType() != "PLANE" or f.normalAt().z > -0.999:   # source: assumption — faces down within ~2.6°
            continue
        z = f.Center().z
        if abs(z - zmin) <= 1e-3:   # source: assumption — on the bed: within 1 µm of the lowest point
            contact += f.Area()
        elif z - zmin <= gap:
            air.append((z - zmin, f.Area()))
    if not (big := [x for x in air if x[1] > contact]):
        return None
    dz, area = max(big, key=lambda x: x[1])
    return {"zmin": zmin, "height": dz, "area": area, "contact": contact}


def bed_contact(view, model) -> list[Result]:
    out = []
    for name, s in (model or {}).items():
        d = contact_defect(s, limit("BED-01", "contact_gap"))
        args = {k: f"{v:.{0 if k in ('area', 'contact') else 2}f}" for k, v in (d or {}).items()}
        out.append(_r("bed_contact", "BED-01", BLOCK if d else PASS, f"bed01.{'fail' if d else 'pass'}", name, None, d,
                      part=name, **args))
    return out


def single_solid(view, model) -> list[Result]:
    """A part made of several disjoint solids (a splinter) falls apart on the bed (E-28)."""
    return [_r("single_solid", "SINGLE-01", PASS if n == 1 else BLOCK, "single.pass" if n == 1 else "single.fail", name,
               n, part=name, n=n) for name, n in ((a, len(s.Solids())) for a, s in (model or {}).items())]


def bed(view) -> tuple[float, float, float] | None:
    """(x, y, margin) mm from the machine profile `bed`; None when the bed size is not recorded."""
    b = profile(view).get("bed") or {}
    x, y = (b.get("x") or {}).get("value"), (b.get("y") or {}).get("value")
    return (x, y, (b.get("margin") or {}).get("value") or 0.0) if x and y else None


def place(model: dict, bx: float, by: float, margin: float = 0.0) -> tuple[int, dict, bool]:
    """Turns the parts 0–89° about Z for the smallest angle that fits the bed within its margin and centres them;
    when no angle fits, the angle of least overhang (fits = False). (angle, placed parts, fits)."""
    import cadquery as cq

    best = None
    for a in range(90):
        rot = {n: s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a) for n, s in model.items()}
        bb = cq.Compound.makeCompound(list(rot.values())).BoundingBox()
        over = max(bb.xlen - (bx - 2 * margin), bb.ylen - (by - 2 * margin))
        if best is None or over < best[0]:
            best = (over, a, rot, bb)
        if over <= 0:
            break
    over, a, rot, bb = best
    shift = cq.Vector(bx / 2 - (bb.xmin + bb.xmax) / 2, by / 2 - (bb.ymin + bb.ymax) / 2, 0)
    return a, {n: s.translate(shift) for n, s in rot.items()}, over <= 0


def bed_fit(view, model) -> list[Result]:
    if not model or (b := bed(view)) is None:
        return [_r("bed_fit", "BED-02", WARN, "bed02.unknown")] if model else []
    a, _, ok = place(model, *b)
    return [_r("bed_fit", "BED-02", PASS if ok else WARN, "bed02.pass" if ok else "bed02.fail", value=a,
               extra={"angle": a}, x=num(b[0]), y=num(b[1]), margin=num(b[2]), angle=a)]


def estimate(model: dict) -> dict:
    vol = sum(s.Volume() for s in model.values())
    shell = min(vol, sum(s.Area() for s in model.values()) * SHELL_MM)   # surface × shell, at most the solid
    printed = [shell + (vol - shell) * f for f in INFILL]
    return {"filament_g": [round(p * DENSITY_G_MM3) for p in printed],
            "hours": [round(printed[0] / FLOW_MM3_S[1] / 3600, 3), round(printed[1] / FLOW_MM3_S[0] / 3600, 3)],
            "volume_cm3": round(vol / 1000, 1),
            "assumptions": t("print3d.estimate.assumptions", shell=num(SHELL_MM), share=f"{shell / vol * 100:.0f}")}


def visuals(view, model: dict) -> tuple[list, dict]:
    """Release card figures [(title, svg)]: bed layout from above (turned to fit, red when it does not), print
    direction from the front; and the print estimate."""
    import cadquery as cq
    from mekanik_mech.card_views import H, W, label, view_svg

    bb = cq.Compound.makeCompound(list(model.values())).BoundingBox()
    title = t("print3d.view.layout_title")
    if (b := bed(view)) is None:
        info = t("print3d.view.no_bed", x=num(bb.xlen), y=num(bb.ylen), z=num(bb.zlen))
        layout = view_svg(model, "top", title=title, extra=label(W - 10, 14, info, 9.5, "#5F6873", "end", False))
    else:
        a, placed, ok = place(model, *b)
        info = "".join([t("print3d.view.layout", x=f"{bb.xlen:.0f}", y=f"{bb.ylen:.0f}", z=f"{bb.zlen:.0f}",
                          bx=f"{b[0]:.0f}", by=f"{b[1]:.0f}"), t("print3d.view.margin", m=f"{b[2]:g}") if b[2] else "",
                        t("print3d.view.turned", a=a) if a else "", "" if ok else t("print3d.view.no_fit")])
        layout = view_svg(placed, "top", title=title, bed=b[:2],
                          extra=label(W - 10, H - 8, info, 9.5, "#5F6873" if ok else "#B3261E", "end", False))
    return [(t("print3d.view.layout_name"), layout),
            (t("print3d.view.direction_name"), view_svg(model, "front", title=t("print3d.view.direction_title"),
                                                         ground=True))], estimate(model)


def files(view, model: dict, out_dir: Path) -> dict[str, str]:
    """Writes `<code>.step` and `stl/<part>.stl` into out_dir; returns {relative path: SHA-256}."""
    from mekanik_mech.export import step, stl

    out = Path(out_dir)
    paths = [*stl(model, out / "stl"), step(model, out / f"{view.code}.step")]   # stl() creates the folders
    return {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


for _hook, _rule in ((single_solid, "SINGLE-01"), (bed_contact, "BED-01"), (bed_fit, "BED-02")):
    _hook.rules = (_rule,)   # catalog–code link of the release hooks (CheckSpec.rules for checks)
