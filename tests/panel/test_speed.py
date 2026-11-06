# SPDX-License-Identifier: AGPL-3.0-or-later
"""A3: screen text answers within p95 ≤ 0.5 s (old panel 0.04–0.48 s, at most 0.94 s), measured per endpoint after
the first look (the HEAD state is cached; a new commit makes it again once). The cold first request is printed."""

from __future__ import annotations

import statistics
import time

from mekanik.core.process.step import step

SCREENS = ["/api/tree", "/api/tabs", "/api/cards", "/api/new-work", "/api/session", "/api/catalog", "{w}",
           "{w}/stages", "{w}/status", "{w}/liveness", "{w}/cards", "{w}/calcs", "{w}/files", "{w}/branches",
           "{w}/design-file", "{w}/stream", "{w}/inbox", "{w}/summary", "{w}/policy", "{w}/intake", "{w}/stdmap",
           "{w}/steps/{sha}"]


def test_screen_text_p95(panel, g0):
    """2.1: A3 — every screen endpoint: p95 of 20 answers ≤ 0.5 s on a work with a few steps"""
    code, d = g0
    for i in range(3):
        sha = step(d, f"adım {i}", "design_engineer", f"metin {i}")["commit"]
    w = f"/api/works/{code}"
    cold = time.monotonic()
    assert panel.get(w + "/cards").status_code == 200
    cold, out = time.monotonic() - cold, {}
    for path in (p.format(w=w, sha=sha) for p in SCREENS):
        times = []
        for _ in range(20):
            t0 = time.monotonic()
            r = panel.get(path)
            times.append(time.monotonic() - t0)
            assert r.status_code == 200, (path, r.text[:200])
        out[path] = statistics.quantiles(times, n=20)[-1]
    print(f"A3 cold first /cards {cold:.3f} s; p95 by screen: " + ", ".join(
        f"{p.removeprefix(w) or '/work'} {v:.3f}" for p, v in out.items()))
    assert max(out.values()) <= 0.5, out
