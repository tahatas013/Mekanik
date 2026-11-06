# SPDX-License-Identifier: AGPL-3.0-or-later
"""mekanik print3d package: profile type print3d.fdm, release checks BED-01/BED-02/SINGLE-01, print request files and
figures, reached by the core through the mech model hooks (release_files, release_visuals). No OCCT at import."""

from pathlib import Path

from mekanik.core import i18n
from mekanik.plugins import PackageSpec
from mekanik_mech import HOOKS

from . import profile, release

i18n.add_catalog(Path(__file__).parent / "i18n")
HOOKS.table.update({n: f"mekanik_print3d.release:{f}" for n, f in
                    (("release_files", "files"), ("release_visuals", "visuals"), ("bed_place", "place"),
                     ("print_estimate", "estimate"))})

SPEC = PackageSpec(id="print3d", version="0.1.0", profile_types={"print3d.fdm": profile.validate},
                   release_hooks=[release.single_solid, release.bed_contact, release.bed_fit],
                   i18n=Path(__file__).parent / "i18n")
