"""S-001 modeli: A/B doğru geçme, C/D girişim, E/G kayıtsız eş eksenli çift. Ölçüler params.yaml'dan."""

import cadquery as cq


def _blok(p, delik, x):
    return cq.Workplane().box(p.blok_en, p.blok_en, p.blok_kalinlik).faces(">Z").workplane().hole(delik).translate((x, 0, 0)).val()


def _pim(p, cap, x):
    return cq.Workplane().circle(cap / 2).extrude(p.pim_boy).translate((x, 0, -p.pim_boy / 2)).val()


def parcalar(p):
    return {
        "A": _blok(p, p.a_delik_cap, 0), "B": _pim(p, p.b_mil_cap, 0),
        "C": _blok(p, p.c_delik_cap, p.aralik), "D": _pim(p, p.d_mil_cap, p.aralik),
        "E": _blok(p, p.e_delik_cap, 2 * p.aralik), "G": _pim(p, p.g_mil_cap, 2 * p.aralik),
    }
