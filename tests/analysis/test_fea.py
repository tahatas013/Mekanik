# SPDX-License-Identifier: AGPL-3.0-or-later
"""FEA against a known solution."""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.occt


def test_hanging_bar_matches_closed_form():
    """new: Ek B §14 madde 1 — a bar clamped at its top end, loaded by its own weight (inertial load ρ·a along z).
    Closed form (ν = 0): σ_zz = ρ a z (z from the free end), tip displacement δ = ρ a L² / (2E)."""
    import cadquery as cq
    from mekanik_analysis import fea

    L, E, rho, a = 50.0, 3000.0, 1.24, 1e7            # mm, MPa, g/cm³, mm/s²
    bar = cq.Workplane().box(6, 6, L, centered=(True, True, False)).val()    # z from 0 to L, clamp at z = L
    r = fea.solve(bar, E=E, nu=0.0, density_g_cm3=rho, accel_mm_s2=(0, 0, -a), fixed=lambda x, y, z: z > L - 1e-6)
    q = rho * 1e-9 * a                                # N/mm³
    assert r["fixed_nodes"] > 4 and r["elements"] > 100
    assert r["u_max"] == pytest.approx(q * L ** 2 / (2 * E), rel=0.05)
    mid = np.abs(r["centers"][:, 2] - L / 2) < 3
    assert abs(r["szz"][mid].mean()) == pytest.approx(q * L / 2, rel=0.05)
