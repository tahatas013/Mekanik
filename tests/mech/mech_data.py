# SPDX-License-Identifier: AGPL-3.0-or-later
"""Base v1 work of the mech tests (old test_cekirdek CALISMA, PARAMS, GECMELER with v1 names)."""

WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-01", "title": "Test", "risk_class": "B",
        "purpose": "sınama", "done_criterion": "sınama", "opened_at": "2026-11-06T10:00:00+03:00",
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G2", "gate_status": {}},
        "profiles": {"manufacturing": "fdm-test@v0", "instruments": ["caliper", "scanner-lidar"]}}
PARAMS = {"hole_d": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
          "shaft_d": {"value": None, "unit": "mm", "source": "derived", "formula": "hole_d - gap"}}
FITS = [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "nominal": "hole_d", "clearance": "gap",
         "critical": True}]
