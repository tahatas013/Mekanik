# SPDX-License-Identifier: AGPL-3.0-or-later
"""mekanik mech package: fit record (fits.yaml), parametric model, mechanical checks, views, export.

This module and the loader/check modules do not import OCCT; the model hooks load it on first use, so the core
and the fit checks run without CadQuery.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from mekanik.core import i18n
from mekanik.plugins import CheckSpec, PackageSpec

from . import cards, checks, fits


class ModelHooks:
    """Model production, views and export, resolved lazily by name (`hooks.build(view)`). `table` maps a hook to
    "module:function"; a package built on mech may add entries (print3d adds release_files, release_visuals)."""

    def __init__(self, table: dict[str, str]):
        self.table = table

    def __getattr__(self, name: str):
        table = self.__dict__.get("table", {})
        if name not in table:
            raise AttributeError(name)
        mod, _, fn = table[name].partition(":")
        return getattr(import_module(mod), fn or name)

    def has(self, name: str) -> bool:
        return name in self.table


_M = "mekanik_mech."
HOOKS = ModelHooks({
    **{n: _M + "model" for n in ("build", "builder", "build_path", "load_module", "metrics", "summary", "signature",
                                 "producer_version")},
    **{n: _M + "export" for n in ("step", "stl", "tessellation", "write_tessellation", "write_cache", "clean_mesh")},
    **{n: _M + "views" for n in ("isometric", "isometric_svg", "section", "dia_dim", "Dim")},
    **{n: _M + "card_views" for n in ("card_visuals", "param_effect", "param_figures", "view_svg", "fit_axes",
                                      "fit_section", "option_figures", "text_svg")},
})

i18n.add_catalog(Path(__file__).parent / "i18n")

SPEC = PackageSpec(
    id="mech", version="0.1.0",
    loaders={"mech": fits.load},
    checks=[CheckSpec("mech.independent_number", checks.independent_number, ("FIT-01",), order=20),
            CheckSpec("mech.fit_clearance", checks.fit_clearance, ("FIT-02", "BOLT-01"), order=30),
            CheckSpec("mech.interference", checks.interference, ("SOLID-01", "INTERF-01"), order=50),
            CheckSpec("mech.assembly", checks.assembly, ("ASSY-01",), order=60),
            CheckSpec("mech.unregistered_fit", checks.unregistered_fit, ("UNREG-01",), order=70)],
    card_makers=cards.MAKERS,
    critical_dims=fits.critical_dims,
    sourced_values=fits.sourced_values,
    param_uses=fits.param_uses,
    subject_values=fits.subject_values,
    model=HOOKS,
    design_files=("fits.yaml",),
    i18n=Path(__file__).parent / "i18n",
)
