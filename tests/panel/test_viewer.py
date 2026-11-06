# SPDX-License-Identifier: AGPL-3.0-or-later
"""The viewer's model through the package's model hooks (mech, OCCT): A4 (first image p95 ≤ 1.5 s from the cache,
≤ 2.0 s without it), and the old e2e 3 (exact diameters, the measurement contract), 9 (dimensioned section) and 10
(fit markers at the hole's axis, state from the results and the card) on the back end."""

from __future__ import annotations

import json
import shutil
import statistics
import time

import pytest

pytest.importorskip("cadquery")

from test_store import new, prepare  # noqa: E402

from mekanik.core import yamlio  # noqa: E402
from mekanik.core.evidence import cache  # noqa: E402
from mekanik.core.process.step import step  # noqa: E402
from mekanik.core.store import git  # noqa: E402
from mekanik.panel import model  # noqa: E402
from mekanik.plugins import registry, reset_registry  # noqa: E402

pytestmark = pytest.mark.occt
MODEL = '''import cadquery as cq


def parts(p):
    a = cq.Workplane().box(p.blok, p.blok, p.kalinlik).faces(">Z").workplane().hole(p.delik_cap).val()
    b = cq.Workplane().circle(p.mil_cap / 2).extrude(p.pim_boy).translate((0, 0, -p.pim_boy / 2)).val()
    return {"A": a, "B": b}
'''
PARAMS = {"delik_cap": {"value": 10.0, "unit": "mm", "source": "decision"},
          "g01_bosluk": {"value": 0.3, "unit": "mm", "source": "decision"},
          "mil_cap": {"value": None, "unit": "mm", "source": "derived", "formula": "delik_cap - g01_bosluk"},
          "blok": {"value": 30.0, "unit": "mm", "source": "decision"},
          "kalinlik": {"value": 10.0, "unit": "mm", "source": "decision"},
          "pim_boy": {"value": 20.0, "unit": "mm", "source": "decision"},
          "blok_en": {"value": 30.0, "unit": "mm", "source": "decision"}}
FITS = {"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "nominal": "delik_cap",
                  "clearance": "g01_bosluk"}], "flexes": []}


@pytest.fixture
def pinned(shop):
    """A block with a hole and a pin through it (the old panel e2e work), stepped once: the cache holds its model."""
    reset_registry()
    assert registry().model_hooks() is not None
    code, d = new()
    prepare(d, params=PARAMS, model=MODEL)
    yamlio.write(d / "fits.yaml", FITS)
    step(d, "hazırlık: blok ve pim", "design_engineer")
    model._made.clear()
    return code, d, git.head(d)


def test_first_image_from_cache_and_without(panel, pinned):
    """2.1: A4 — the viewer's JSON: from the cache p95 ≤ 1.5 s (10 loads), made from the commit ≤ 2.0 s (3 loads,
    the cache entry and the in-memory model removed each time)"""
    code, d, sha = pinned
    url, sig = f"/api/works/{code}/model", registry().model_hooks().signature(d, sha)
    hot = []
    for _ in range(10):
        t0 = time.monotonic()
        r = panel.get(url)
        hot.append(time.monotonic() - t0)
        assert r.status_code == 200 and json.loads(r.content)["data"]["shapes"]
    cold = []
    for _ in range(3):
        shutil.rmtree(cache.root() / sig)
        model._made.clear()
        t0 = time.monotonic()
        r = panel.get(url)
        cold.append(time.monotonic() - t0)
        assert json.loads(r.content)["commit"] == sha and (cache.root() / sig / "tessellation.json").exists()
    print(f"A4 cached p95 {statistics.quantiles(hot, n=20)[-1]:.3f} s; uncached max {max(cold):.3f} s")
    assert statistics.quantiles(hot, n=20)[-1] <= 1.5 and max(cold) <= 2.0, (hot, cold)


def test_exact_diameters_section_and_markers(panel, pinned):
    """2.1: old e2e 3, 9, 10 — cylinder list and a measurement from the exact solids (hole Ø10, pin Ø9.7);
    the fit's dimensioned section; the marker on the hole's axis (x = y = 0) with the state the results and the
    card give"""
    code, d, sha = pinned
    cyl = panel.get(f"/api/works/{code}/cylinders", params={"commit": sha}).json()
    assert {(c["part"], round(c["diameter"], 6)) for c in cyl} == {("A", 10.0), ("B", 9.7)}
    pin = next(c for c in cyl if c["part"] == "B")
    m = panel.post("/api/measure", json={"work": code, "commit": sha, "paths": [pin["path"]]}).json()
    assert abs(next(x["diameter"] for x in m["result"] if "diameter" in x) - 9.7) < 1e-9 and m["source"] == "exact"
    assert m["tool_type"] == "PropertiesMeasurement" and m["geom_type"] == "Cylinder"
    svg = panel.get(f"/api/works/{code}/sections/G-01")
    assert svg.status_code == 200 and svg.headers["content-type"].startswith("image/svg+xml") and "G-01" in svg.text
    (mark,) = panel.get(f"/api/works/{code}/fit-markers").json()
    assert mark["id"] == "G-01" and abs(mark["position"][0]) < 0.01 and abs(mark["position"][1]) < 0.01
    c = panel.get(f"/api/works/{code}/cards").json()
    failed = [r for r in c["results"] if r["ref"] == "G-01" and r["status"] != "pass"]
    card = next((k for k in c["cards"] if "G-01" in (k.get("subject") or {}).values()), None)
    want = "fail" if failed or (card and card["status"] == "rejected") else "review" if card and card[
        "status"] == "open" else "pass"
    assert mark["status"] == want and mark["card"] == (card and card["id"])
    assert panel.get(f"/api/works/{code}/sections/G-99").status_code == 404
