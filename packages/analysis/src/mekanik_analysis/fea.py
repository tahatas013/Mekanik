# SPDX-License-Identifier: AGPL-3.0-or-later
"""Linear elastic FEA (old `fea.py`) for calculation scripts: solid → TetGen tetrahedra → scikit-fem (linear) → stress
per element (von Mises, σ_zz, σ_yy, centroid). Units mm, N, MPa, t, s. Linear elements are too stiff in thin-plate
bending (stress may come out low) and a fixed boundary shows a singular stress: read results away from it."""

from __future__ import annotations

import numpy as np


def mesh(solid, surface_tol: float = 0.05, angle: float = 0.3, volume: float = 1.0):
    """TetGen, quality (q) and largest element (a, mm³), boundary points added (pre-splitting made TetGen unstable).
    source: assumption — tolerances and element size are meshing settings, not engineering values."""
    import tetgen
    from mekanik_mech.export import clean_mesh

    m = clean_mesh(solid, surface_tol, angle)
    nodes, elems, *_ = tetgen.TetGen(np.asarray(m.vertices), np.asarray(m.faces)).tetrahedralize(
        switches=f"pq1.8a{volume}Q")
    return np.asarray(nodes, float), np.asarray(elems, int)


def solve(solid, E: float, nu: float, density_g_cm3: float, accel_mm_s2, fixed) -> dict:
    """Static solution under an inertial load (ρ·a on every element); nodes where `fixed(x, y, z)` is true are fixed."""
    from skfem import Basis, ElementTetP1, ElementVector, LinearForm, MeshTet, asm, condense, solve as fe_solve
    from skfem.models.elasticity import lame_parameters, linear_elasticity

    X, T = mesh(solid)
    m = MeshTet(X.T, T.T)
    basis = Basis(m, ElementVector(ElementTetP1()))
    lam, mu = lame_parameters(E, nu)
    K = asm(linear_elasticity(lam, mu), basis)
    rho, a = density_g_cm3 * 1e-9, np.asarray(accel_mm_s2, float)   # g/cm³ → t/mm³

    @LinearForm
    def load(v, w):
        return rho * (a[0] * v.value[0] + a[1] * v.value[1] + a[2] * v.value[2])

    fixed_nodes = np.where(fixed(*m.p))[0]
    u = fe_solve(*condense(K, asm(load, basis), D=basis.nodal_dofs[:, fixed_nodes].ravel()))
    U = u[basis.nodal_dofs].T                                    # (node, 3)
    t = m.t.T
    P = m.p.T[t]                                                   # (n, 4, 3)
    G = np.linalg.inv(np.concatenate([np.ones((len(t), 4, 1)), P], axis=2))[:, 1:, :]   # shape-function gradients
    grad = np.einsum("nij,njk->nik", G, U[t])                    # ∂u_k/∂x_i, constant per element
    eps = 0.5 * (grad + np.transpose(grad, (0, 2, 1)))
    s = 2 * mu * eps + lam * np.trace(eps, axis1=1, axis2=2)[:, None, None] * np.eye(3)
    d = s[:, [0, 1, 2], [0, 1, 2]] - s[:, [1, 2, 0], [1, 2, 0]]                 # σxx−σyy, σyy−σzz, σzz−σxx
    vm = np.sqrt(0.5 * (d ** 2).sum(axis=1) + 3 * (s[:, 0, 1] ** 2 + s[:, 1, 2] ** 2 + s[:, 0, 2] ** 2))
    return {"vm": vm, "szz": s[:, 2, 2], "syy": s[:, 1, 1], "centers": P.mean(axis=1), "nodes": m.p.shape[1],
            "elements": len(t), "fixed_nodes": len(fixed_nodes), "u_max": float(np.abs(U).max())}
