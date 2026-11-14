# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.8 (every old screen has its v1 screen, docs/dev/panel-parity.md "Ekranlar"), phone width without overflow, A3
(screen text p95 ≤ 0.5 s, measured in the browser), A4 (the model's first image p95 ≤ 1.5 s from the cache, ≤ 2.0 s
without it, in the browser), 2.7 (the interface in English from the catalog)."""

from __future__ import annotations

import shutil
import statistics

import pytest
from conftest import go, new, prepare, review
from stage import rich

from mekanik.core.i18n import catalogs

pytestmark = pytest.mark.e2e
# old screen (Ek B §5) → v1 route and an element it must show
SCREENS = {"durum, aşamalar (Akış sağ paneli, aşama şeridi)": ("flow", "[data-stages] [data-gate]"),
           "ekip (Akış sağ paneli)": ("flow?side=team", "[data-team-state]"),
           "kartlar": ("cards", "[data-card-std]"), "model": ("model", "#viewer"), "hesaplar": ("calcs", "[data-calc]"),
           "analizler": ("analyses", "#main .bilgi-kutu"), "çıktılar → dosyalar": ("files", "[data-folder]"),
           "dallar": ("branches", "[data-selected-step]"), "tasarım dosyası": ("design", "[data-check-groups]"),
           "tanımlama (yeni)": ("intake", "[data-intake-step]"), "standart haritası (yeni)": ("stdmap", "#main .sayfa-bas"),
           "oturum (yeni, A13)": ("session", "[data-terminal]")}
TEXT_SCREENS = ["flow", "cards", "intake", "stdmap", "files", "calcs", "branches", "design"]


def p95(xs: list[float]) -> float:
    return statistics.quantiles(xs, n=20)[-1] if len(xs) >= 20 else max(xs)


@pytest.fixture(scope="module")
def w(shop_e2e):
    return rich(new, prepare, review)


def test_every_old_screen_has_a_v1_screen(page, panel_e2e, w):
    """2.8: Ek B §5 — each old screen's v1 screen opens with its content and no error; the new-work screen too"""
    code, d = w
    for old, (route, sel) in SCREENS.items():
        go(page, panel_e2e, f"/{code}/{route}", route.split("?")[0])
        page.wait(sel, 30000, "attached")
        assert page.count("#main > .hata-kutu") == 0, old
    go(page, panel_e2e, "/new", "new")
    page.wait("[data-create]")


def test_phone_width_has_no_horizontal_overflow(browser, panel_e2e, w):
    """2.8: the panel is usable on a phone (390 px): no screen is wider than the window"""
    code, d = w
    ph = browser.page("phone", 390, 844)
    ph.goto(panel_e2e.login())
    for route in [*{r for r, _ in SCREENS.values()}, "cards?card=K-01"]:
        go(ph, panel_e2e, f"/{code}/{route}", route.split("?")[0])
        ph.eval("() => new Promise((r) => setTimeout(r, 300))")
        assert ph.eval("() => document.documentElement.scrollWidth - window.innerWidth") <= 0, route
    go(ph, panel_e2e, "/new", "new")
    assert ph.eval("() => document.documentElement.scrollWidth - window.innerWidth") <= 0


def test_screen_text_answers_within_half_a_second(page, panel_e2e, w):
    """2.1: A3 — from a click on a screen's tab to its text on the page (data fetched and drawn), measured in the
    browser over 4 rounds of the text screens: p95 ≤ 0.5 s"""
    code, d = w
    go(page, panel_e2e, f"/{code}/design")   # the last of the round: every click changes the screen
    page.eval("() => { window.__mekanik.times.length = 0; }")
    for _ in range(4):
        for s in TEXT_SCREENS:
            page.eval("() => document.querySelector('#main').removeAttribute('data-shown')")
            page.click(f"[data-nav='{s}'], [data-tree='{s}']")
            page.shown(s)
    times = [x["ms"] / 1000 for x in page.eval("() => window.__mekanik.times")]
    print(f"A3 screen text p95 {p95(times):.3f} s, max {max(times):.3f} s, n {len(times)}")
    assert len(times) == 4 * len(TEXT_SCREENS) and p95(times) <= 0.5, times


FIRST_IMAGE = """async (code) => { location.hash = `#/${code}/flow`;
  await new Promise((r) => { const t = setInterval(() => { if (document.querySelector("#main[data-shown='flow']")) { clearInterval(t); r(); } }, 10); });
  performance.clearMarks('model-shown'); const t0 = performance.now(); location.hash = `#/${code}/model`;
  return await new Promise((r) => { const t = setInterval(() => { const m = performance.getEntriesByName('model-shown');
    if (m.length) { clearInterval(t); r(m[0].startTime - t0); } }, 5); }); }"""


def test_model_first_image_from_the_cache_and_without(page, panel_e2e, w):
    """2.1: A4 — from opening the model screen to the model drawn in the viewer, in the browser: 10 loads with the
    model in the cache (p95 ≤ 1.5 s); 3 loads with the cache entry and the panel's in-memory model removed (≤ 2.0 s)"""
    from mekanik.core.evidence import cache
    from mekanik.core.store import git
    from mekanik.panel import model
    from mekanik.plugins import registry

    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    hot = [page.eval(FIRST_IMAGE, code) / 1000 for _ in range(10)]
    sig = registry().model_hooks().signature(d, git.head(d))
    cold = []
    for _ in range(3):
        shutil.rmtree(cache.root() / sig, ignore_errors=True)
        model._made.clear()
        cold.append(page.eval(FIRST_IMAGE, code) / 1000)
    print(f"A4 first image: cached p95 {p95(hot):.3f} s (max {max(hot):.3f}); uncached max {max(cold):.3f} s")
    assert p95(hot) <= 1.5 and max(cold) <= 2.0, (hot, cold)


def test_interface_in_english(page, panel_e2e, w):
    """2.7: TR/EN switch — the interface text comes from the English catalog (the screens' tabs, the flow's lead)"""
    code, d = w
    en = catalogs()["en"]
    go(page, panel_e2e, f"/{code}/flow")
    try:
        page.click("[data-lang='en']")
        page.wait(f"[data-nav='cards']:has-text('{en['panel.ui.nav.cards']}')")
        for k in ("flow", "intake", "model", "stdmap", "branches", "design", "session"):
            assert page.text(f"[data-nav='{k}']").strip() == en[f"panel.ui.nav.{k}"]
        assert en["panel.ui.flow.lead"] in page.text("#main .sayfa-bas")
    finally:
        page.click("[data-lang='tr']")


def test_record_text_is_shown_as_text_never_run(page, panel_e2e, shop_e2e):
    """2.8: Ek B §5 yardim.ts — HTML escaping: a work title with markup and a script attribute shows as text; no
    element is made, nothing runs"""
    code, d = new(title='<img src=x onerror="window.__xss=1"><b>kalın</b>')
    go(page, panel_e2e, f"/{code}/flow")
    assert page.eval("() => window.__xss === undefined && !document.querySelector('header img, aside.sol img')")
    assert '<b>kalın</b>' in page.text("header .konum")


def test_page_scrolls_and_selects_text_beside_the_viewer(page, panel_e2e, w):
    """2.8: Ek B §5 stil.css, E-08 — three-cad-viewer's CSS sets overflow:hidden and user-select:none on body; the panel
    undoes it: with the model shown, the page scrolls and its text is selectable"""
    code, d = w
    go(page, panel_e2e, f"/{code}/model")
    page.wait("#viewer canvas", 30000)
    over, sel = page.eval("() => { const s = getComputedStyle(document.body); return [s.overflowY, s.userSelect]; }")
    assert over != "hidden" and sel != "none"


def test_columns_widen_by_dragging_and_are_remembered(page, panel_e2e, w):
    """2.8: Ek B §5 genislet.ts, E-09 — the tree and the properties column widen by dragging their edge; the width is
    remembered in this browser; a double click restores the default"""
    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    w0, hb = page.box("aside.sol")["width"], page.box("[data-resize='sol']")
    page.mouse("move", hb["x"] + 3, hb["y"] + 200)
    page.mouse("down")
    page.mouse("move", hb["x"] + 83, hb["y"] + 200, {"steps": 5})
    page.mouse("up")
    assert abs(page.box("aside.sol")["width"] - (w0 + 80)) < 4
    go(page, panel_e2e, f"/{code}/flow")
    assert abs(page.box("aside.sol")["width"] - (w0 + 80)) < 4
    page._c("dblclick", "[data-resize='sol']")
    assert abs(page.box("aside.sol")["width"] - w0) < 2


def test_objection_and_gate_return_go_through_their_windows(page, panel_e2e, w):
    """2.3: D3 (panel side) — a provisional decision's line offers "object": the reason is asked, the objection is
    recorded (the decision is objected); a gate return asks its reason and confirmation, and a return the process
    profile does not allow is refused with its key, nothing written"""
    from stage import g0_passed

    from mekanik.core import yamlio
    from mekanik.core.process import gates
    from mekanik.core.process.step import step
    from mekanik.core.store import git

    code, d = w
    go(page, panel_e2e, f"/{code}/flow")
    page.click("[data-object='K-01']")
    page.wait("dialog[data-confirm][open] [data-field]")
    page.fill("dialog[data-confirm] [data-field]", "boşluk büyük olmalı")
    with page.response("/decisions/K-01/objection") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    assert next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == "K-01")["status"] == "objected"
    code, d = new(title="Geri dönüş sınaması")   # G0 passed (the decision above holds its own G0 open)
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    g0_passed(d)
    head = git.head(d)
    go(page, panel_e2e, f"/{code}/flow?gate=G0", "flow")
    page.click("[data-gate-back='G0']")
    page.wait("dialog[data-confirm][open] [data-field]")
    page.fill("dialog[data-confirm] [data-field]", "yeniden bakılsın")
    with page.response("/gates/G0/back") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 409 and "policy.back.not_allowed" in got["body"] and git.head(d) == head
    page.wait(".bildirim [data-error='policy.back.not_allowed']")
