# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.6: the old panel's 17 end-to-end tests (surec testler/test_panel_e2e.py) on the new front end, in Chromium.
Same scenarios on the old e2e work (a block with a hole and a pin through it, fit G-01); the page is read by data
attributes and keys, not Turkish text (a number is compared with the catalog's decimal sign). Old test → this file:
test_<n>_… keeps the old number. A test that changes geometry or the gate of the shared work uses its own work."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import urllib.error
import urllib.request

import pytest
from conftest import go, new, prepare, review
from stage import g0_passed, pinned, rich

from mekanik.agent import hook
from mekanik.core import yamlio
from mekanik.core.i18n import catalogs
from mekanik.core.store import git

pytestmark = pytest.mark.e2e
CLEAR = "() => document.querySelectorAll('.bildirim').forEach((b) => b.remove())"
CSRF_POST = """async ([url, body]) => { const s = await (await fetch('/api/session')).json();
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': s.csrf},
    body: JSON.stringify(body)}); return {status: r.status, body: await r.json()}; }"""
FETCH = "async (url) => { const r = await fetch(url); return {status: r.status, type: r.headers.get('content-type'), text: await r.text()}; }"
SCREEN_XY = """([x, y, z]) => { const v = window.__mekanikViewer; const cam = v.camera.getCamera();
  const r = v.renderer.domElement.getBoundingClientRect(); const p = cam.position.clone(); p.set(x, y, z); p.project(cam);
  return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""


def dec(x: str) -> str:
    return x.replace(".", catalogs()["tr"]["num.decimal"])


def ui(key: str) -> str:
    return catalogs()["tr"][f"panel.ui.{key}"]


@pytest.fixture(scope="module")
def w1(shop_e2e):
    """The old e2e work, G0 requested."""
    return pinned(new, prepare, review)


@pytest.fixture(scope="module")
def w4(shop_e2e):
    """The work with an assumed value (V-01), a calculation and a decision K-01 (old KARAR_VE_LISTE, HESAP_EKLE)."""
    return rich(new, prepare, review)


def test_1_gate_approval_from_the_panel_commit_and_tag(page, panel_e2e, w1):
    """2.6: old e2e 1 — a gate card is never approved in one click: the confirmation window first; cancel writes
    nothing; the server refuses an unconfirmed request; confirmed, the chief's signed commit and the gate tag"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/cards?card=O-G0", "cards")
    page.wait("#card-area [data-card-std='O-G0']")
    head = git.head(d)
    page.click("#card-area [data-act=approve]")
    page.wait("dialog[data-confirm][open]")
    page.click("dialog[data-confirm] [data-answer=no]")
    assert git.head(d) == head
    r = page.eval(CSRF_POST, [f"/api/works/{code}/cards/O-G0/decision", {"action": "approve"}])
    assert r["status"] == 409 and r["body"]["error"]["key"] == "panel.confirm.required" and git.head(d) == head
    page.click("#card-area [data-act=approve]")
    page.wait("dialog[data-confirm][open]")
    with page.response("/cards/O-G0/decision") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    assert git.head(d) != head and f"{code}-G0" in git.git("tag", "--list", cwd=d).split()
    assert git.git("log", "-1", "--format=%an", f"{code}-G0", cwd=d) == "Test Mühendis"
    rec = [x for x in yamlio.read(d / "approvals.yaml") if x["card"] == "O-G0"][-1]
    assert (rec["action"], rec["channel"]) == ("approve", "panel_confirmed")


def test_2_finished_stage_shows_its_3d_model(page, panel_e2e, w1):
    """2.6: old e2e 2 — the finished stage (G0) opens with its last model in a small viewer, its steps; "open in
    Model" opens the full viewer of that commit"""
    code, d = w1
    g0_passed(d)
    go(page, panel_e2e, f"/{code}/flow")
    page.click("[data-gate='G0'][data-status='done']")
    page.wait("#mini-3d canvas", 30000)
    assert "hazırlık: blok ve pim" in page.text("[data-stage-detail='G0']")   # the step's own line (record text)
    href = page.attr("[data-open-model]", "href")
    assert "commit=" in href
    page.goto(f"{panel_e2e.url}/{href}")
    page.wait("#viewer canvas", 30000)


def test_3_clip_tab_and_exact_diameters(page, panel_e2e, w1):
    """2.6: old e2e 3 — the viewer's clip tab; cylinder diameters from the exact geometry (hole Ø10, pin Ø9.7)
    beside the model; a measurement answered by the exact solid"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.wait("#viewer canvas", 30000)
    page.click("text=Clip")
    page.wait("[data-cylinders] .kucuk")
    side = page.text("[data-cylinders]")
    assert f"Ø{dec('10.0')}" in side and f"Ø{dec('9.7')}" in side
    sha = git.head(d)
    cyl = page.eval(FETCH, f"/api/works/{code}/cylinders?commit={sha}")
    pin = next(c for c in json.loads(cyl["text"]) if c["part"] == "B")
    m = page.eval(CSRF_POST, ["/api/measure", {"work": code, "commit": sha, "paths": [pin["path"]]}])["body"]
    assert abs(next(x["diameter"] for x in m["result"] if "diameter" in x) - 9.7) < 1e-9 and m["source"] == "exact"


def test_4_card_approval_then_a_value_change_drops_it(page, panel_e2e, shop_e2e):
    """2.6: old e2e 4 — the fit card approved from the panel (a hold card: confirmed); the chief's value changes
    what it rests on: the approval drops, the card is open again with its note; the value's record is written"""
    code, d = pinned(new, prepare, review, "Değer sınaması")
    go(page, panel_e2e, f"/{code}/cards?card=G-01", "cards")
    page.click("#card-area [data-act=approve]")
    page.wait("dialog[data-confirm][open]")
    with page.response("/cards/G-01/decision") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    go(page, panel_e2e, f"/{code}/cards?card=G-01", "cards")
    page.wait("#card-area [data-card-status='approved']")
    r = page.eval(CSRF_POST, [f"/api/works/{code}/values", {"param": "g01_bosluk", "value": 0.35, "reason": "sınama",
                                                            "card": "G-01"}])
    assert r["status"] == 200, r
    go(page, panel_e2e, f"/{code}/cards?card=G-01", "cards")
    page.wait("#card-area [data-card-status='open']")
    assert page.count("#card-area [data-note]") == 1
    assert yamlio.read(d / "approvals.yaml")[-1]["action"] == "value_change"


def test_5_open_a_branch_here_deletes_nothing(page, panel_e2e, w1):
    """2.6: old e2e 5 — "open a branch here" on the branch map: a new work branch at that step; no ref is deleted
    or moved"""
    code, d = w1
    refs = set(git.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags", cwd=d).splitlines())
    first = next(c for c in json.loads(page.eval(FETCH, f"/api/works/{code}/branches")["text"])["commits"]
                 if c["title"] == "hazırlık: blok ve pim")
    go(page, panel_e2e, f"/{code}/branches")
    page.click(f"[data-sha='{first['sha']}']")
    page.wait(f"[data-selected-step='{first['sha']}']")
    page.click("[data-branch-here]")
    page.wait("dialog[data-confirm][open]")
    with page.response("/branches") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    after = set(git.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags", cwd=d).splitlines())
    assert refs < after and f"refs/heads/{code}/work/{ui('br.default_name')} {first['sha']}" in after


def test_6_new_step_announces_a_new_version(page, panel_e2e, w1):
    """2.6: old e2e 6 — the agent makes a step (another process): "new version" with its line; the open model does
    not change by itself; "Load" shows the new commit"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.wait("#viewer canvas", 30000)
    old = git.head(d)[:7]
    p = subprocess.run([sys.executable, "-c", "import sys; from mekanik.core.process.step import step; from mekanik.core.store "
                        "import works; step(works.find(sys.argv[1]), 'ajan adımı: sınama', 'design_engineer')", code],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    page.wait(".bildirim[data-toast='new_version']", 20000)
    assert "ajan adımı: sınama" in page.text(".bildirim[data-toast='new_version']")
    assert page.visible(".bildirim[data-toast='new_version'] [data-toast-act]")
    assert page.text("[data-foot-commit]") == old
    page.click(".bildirim[data-toast='new_version'] [data-toast-act]")
    page.wait(f"[data-foot-commit]:has-text('{git.head(d)[:7]}')")


def test_7_session_waiting_for_a_permission_is_shown(page, panel_e2e, w1):
    """2.6: old e2e 7 — the session asks for a permission in its terminal: the mascot looks at you, a notice says the
    agent waits; the badge leads to the team panel with the reason"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/flow")
    hook.handle("Notification", {"session_id": "e2e-7", "cwd": str(d), "message": "Claude needs your permission to use "
                                 "Bash", "notification_type": "permission_prompt"})
    try:
        page.wait("[data-live='waiting'] .maskot-waiting", 20000)
        page.wait(".bildirim[data-toast='waiting']", 20000)
        assert code in page.text(".bildirim[data-toast='waiting']")
        page.eval(CLEAR)
        page.click("[data-live]")
        page.wait("[data-team-state='waiting'] [data-team-reason='permission']")
    finally:
        hook.handle("SessionEnd", {"session_id": "e2e-7", "cwd": str(d)})


def test_8_security_host_origin_and_branch(panel_e2e, w1):
    """2.6: old e2e 8 (A9) — a foreign Host is refused; a write without or with a foreign Origin is refused; a
    branch that is not this work's work or decision branch is refused"""
    from mekanik.panel import auth

    code, d = w1
    cookie = f"{auth.COOKIE}={auth.session_value()}"

    def ask(path, body=None, headers=None):
        r = urllib.request.Request(panel_e2e.url + path, data=json.dumps(body).encode() if body is not None else None,
                                   headers={"Content-Type": "application/json", "Cookie": cookie, **(headers or {})},
                                   method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(r) as c:
                return c.status, {}
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    assert ask("/api/tree", headers={"Host": "kotu.example"})[1]["error"]["key"] == "panel.auth.host"
    assert ask(f"/api/works/{code}/read-mark", {}, {"Origin": "http://kotu.example"})[1]["error"]["key"] == "panel.auth.origin"
    assert ask(f"/api/works/{code}/read-mark", {})[1]["error"]["key"] == "panel.auth.origin"
    ok = {"Origin": panel_e2e.url, auth.CSRF_HEADER: auth.csrf_token()}
    for branch in (git.head(d), "HEAD", f"{code}/main"):
        st, body = ask(f"/api/works/{code}/cards/G-01/decision", {"action": "comment", "reason": "x", "branch": branch}, ok)
        assert (st, body["error"]["key"]) == (409, "panel.branch.not_work"), (branch, st, body)


def test_9_fit_card_shows_the_dimensioned_section(page, panel_e2e, w1):
    """2.6: old e2e 9 — the fit card's figure is the dimensioned section through the fit's axis, loaded"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/cards?card=G-01", "cards")
    page.wait("#card-area figure img[alt='G-01 kesiti']")
    page.eval("async () => { const i = document.querySelector('#card-area figure img'); if (!i.complete) await new Promise(r => i.onload = r); }")
    assert page.eval("() => document.querySelector('#card-area figure img').naturalWidth") > 0
    s = page.eval(FETCH, f"/api/works/{code}/sections/G-01")
    assert s["status"] == 200 and s["type"].startswith("image/svg+xml") and "G-01" in s["text"]


def test_10_fit_markers_coloured_and_lead_to_the_card(page, panel_e2e, w1):
    """2.6: old e2e 10 — the fit marker sits on the hole's axis, coloured by the state the checks and the card give;
    clicking it shows the fit and its card beside the model"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.wait("[data-fit-marker='G-01']", 30000)
    kv = json.loads(page.eval(FETCH, f"/api/works/{code}/cards")["text"])
    failed = [r for r in kv["results"] if r["ref"] == "G-01" and r["status"] != "pass"]
    card = next((k for k in kv["cards"] if "G-01" in (k.get("subject") or {}).values()), None)
    want = "fail" if failed or (card and card["status"] == "rejected") else "review" if card and card["status"] in (
        "open", "awaiting_reply") else "pass"
    m = "[data-fit-marker='G-01']"
    assert page.attr(m, "data-state") == want
    rgb = {"pass": "rgb(46, 107, 70)", "fail": "rgb(179, 38, 30)", "review": "rgb(138, 90, 0)"}[want]
    assert page.eval(f"() => getComputedStyle(document.querySelector(\"{m}\")).color") == rgb
    mark = next(x for x in json.loads(page.eval(FETCH, f"/api/works/{code}/fit-markers")["text"]) if x["id"] == "G-01")
    assert abs(mark["position"][0]) < 0.01 and abs(mark["position"][1]) < 0.01
    page.eval("() => new Promise((r) => setTimeout(r, 500))")
    box, (ex, ey) = page.box(m), page.eval(SCREEN_XY, mark["position"])
    assert abs(box["x"] + box["width"] / 2 - ex) < box["width"] and abs(box["y"] + box["height"] / 2 - ey) < box["height"]
    page.click(m)
    page.wait("[data-fit-detail='G-01']")
    assert ui("fit_task.centering") in page.text("[data-fit-detail='G-01']") and "G-01" in page.text("aside.sag .panel-baslik")


def _window(png: bytes, x: float, y: float, half: int = 4):
    from PIL import Image

    im = Image.open(io.BytesIO(png)).convert("RGB")
    px = [im.getpixel((int(x) + dx, int(y) + dy)) for dx in range(-half, half + 1) for dy in range(-half, half + 1)]
    return tuple(sum(p[i] for p in px) / len(px) for i in range(3))


def test_11_clip_plane_cuts_and_the_cut_face_is_filled(page, panel_e2e, w1):
    """2.6: old e2e 11 — the clip plane at x = 0 cuts the block and the pin; the cut faces take the cap colour (plane
    0's, red-dominant); with object-coloured caps the colour goes back to the object's: the cap gives the colour"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.wait("#viewer canvas", 30000)
    page.eval("() => { window.__mekanikViewer.presetCamera('right'); return new Promise((r) => setTimeout(r, 800)); }")
    block, pin = page.eval(SCREEN_XY, [0, 10, 2]), page.eval(SCREEN_XY, [0, 0, 8])
    before = _window(page.png(), *block)
    page.eval("""() => { const v = window.__mekanikViewer; v.setActiveTab('clip'); v.setClipNormal(0, [-1, 0, 0], 0);
      v.setClipSlider(0, 0); v.setClipPlaneHelpers(false); return new Promise((r) => setTimeout(r, 1000)); }""")
    png = page.png()
    assert page.eval("() => window.__mekanikViewer.renderer.localClippingEnabled")
    red = lambda c: c[0] > 150 and c[0] - max(c[1], c[2]) > 60  # noqa: E731
    assert red(_window(png, *block)) and red(_window(png, *pin)) and not red(before), (before, _window(png, *block))
    page.eval("() => { window.__mekanikViewer.setClipObjectColorCaps(true); return new Promise((r) => setTimeout(r, 800)); }")
    assert not red(_window(page.png(), *block))


def test_12_decision_card_options_confirmation_and_undo(page, panel_e2e, w4):
    """2.6: old e2e 12 — a decision card: options side by side with drawings from the model, the team's proposal;
    choosing B and approving goes through the confirmation window; the choice is recorded; undo (with its reason,
    confirmed) adds an undo record and opens the card again (Ö-15)"""
    code, d = w4
    go(page, panel_e2e, f"/{code}/cards?card=K-01", "cards")
    page.wait("#card-area [data-card-std='K-01'] .secenek img")
    assert page.count("#card-area .secenek") == 2
    for i in range(2):
        page.eval(f"async () => {{ const i = document.querySelectorAll('#card-area .secenek img')[{i}]; if (!i.complete) await new Promise(r => i.onload = r); }}")
        assert page.eval(f"() => document.querySelectorAll('#card-area .secenek img')[{i}].naturalWidth") > 0
    assert page.count("#card-area .neden") == 1 and page.text("#card-area .oneri-kutu .etiket").endswith("A")
    page.click("#card-area [data-option='b']")
    assert page.text("#card-area [data-act=approve]") == ui("card.approve_option").format(o="B")
    page.click("#card-area [data-act=approve]")
    page.wait("dialog[data-confirm][open]")
    with page.response("/cards/K-01/decision") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    assert next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == "K-01")["chosen"] == "b"
    go(page, panel_e2e, f"/{code}/cards?card=K-01", "cards")
    page.eval(CLEAR)
    page.click("#card-area [data-act=undo]")
    page.wait("dialog[data-confirm][open] [data-field]")
    page.fill("dialog[data-confirm] [data-field]", "geri-donus")
    with page.response("/cards/K-01/revert") as got:
        page.click("dialog[data-confirm] [data-answer=yes]")
    assert got["status"] == 200, got["body"]
    last = yamlio.read(d / "approvals.yaml")[-1]
    assert (last["card"], last["action"], last["reason"], last["channel"]) == ("K-01", "undo", "geri-donus", "panel_confirmed")


def test_13_assumption_list_rows_are_approved(page, panel_e2e, w4):
    """2.6: old e2e 13 — the assumption list (not a hold card): the checked rows are approved in one click, no
    confirmation window; the record names the row"""
    code, d = w4
    go(page, panel_e2e, f"/{code}/cards?card=V-01", "cards")
    page.wait("#card-area [data-card-std='V-01'] figure img")
    assert "elle tutulsun" in page.text("#card-area [data-row='pim_boy']")   # the team's rationale (record text)
    with page.response("/cards/V-01/decision") as got:
        page.click("#card-area [data-act=approve]")
    assert got["status"] == 200, got["body"]
    assert page.count("dialog[data-confirm][open]") == 0
    last = yamlio.read(d / "approvals.yaml")[-1]
    assert (last["card"], last.get("row"), last["action"]) == ("V-01", "pim_boy", "approve")


def test_14_calculations_open_from_the_tree_step_by_step(page, panel_e2e, w4):
    """2.6: old e2e 14 — "Calculations" under the work in the tree: the calculation with its steps (formula,
    value), inputs and chart"""
    code, d = w4
    go(page, panel_e2e, f"/{code}/model")
    page.click("[data-tree='calcs']")
    page.shown("calcs")
    text = page.text("[data-calc='alan']")
    assert "A = b²" in text and dec("900.0") in text and "blok" in text
    assert page.count("[data-calc='alan'] [data-chart] svg path") >= 1


def test_15_team_panel_opens_a_steps_detail(page, panel_e2e, w1):
    """2.6: old e2e 15 — the mascot on every screen; the team panel's "work done": a step opens with what was done
    and why, and the files it changed"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/flow?side=team", "flow")
    page.wait("[data-team-state]")
    assert page.count("[data-live] .maskot") == 1
    page.click("details[data-step] summary")
    page.wait(".adim-detay [data-step-text]")
    assert page.count(".adim-detay [data-step-files] li") >= 1


def test_16_files_only_from_the_allowed_folders(page, panel_e2e, w1):
    """2.6: old e2e 16 (A9) — the files screen under the work in the tree; nothing outside out/, records/, inputs/
    downloads, no path escapes the work folder"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.click("[data-tree='files']")
    page.shown("files")
    page.wait("[data-tree='files'].secili")
    assert page.count("[data-folder='records']") == 1
    for path in ("params.yaml", "out/../params.yaml", "../../../etc/passwd", "records/../../../../etc/passwd"):
        assert page.eval(FETCH, f"/api/works/{code}/download/{path}")["status"] == 404, path


def test_17_mark_the_model_and_send_a_note(page, panel_e2e, w1):
    """2.6: old e2e 17 — "mark and write a note": drag an area on the model, write, send; card N-01 holds the
    screenshot (PNG), the part and the 3D point under the area; the note's marker shows on the model"""
    code, d = w1
    go(page, panel_e2e, f"/{code}/model")
    page.wait("#viewer canvas", 30000)
    page.wait("[data-mark]:not([disabled])")
    page.eval("() => new Promise((r) => setTimeout(r, 800))")
    x, y = page.eval(SCREEN_XY, [0, 10, 2])
    page.click("[data-mark]")
    page.wait("[data-marking]")
    page.mouse("move", x - 15, y - 15)
    page.mouse("down")
    page.mouse("move", x + 15, y + 15, {"steps": 4})
    page.mouse("up")
    page.wait("[data-note-form] img")
    page.fill("[data-note-form] textarea", "Bu köşeyi yuvarlat")
    page.click("[data-note-form] [data-send]")
    page.wait("[data-note-marker='N-01']", 30000)
    k = yamlio.read(d / "cards" / "N-01.yaml")
    assert k["question"] == "Bu köşeyi yuvarlat" and k["subject"].get("point") and k["subject"].get("part")
    png = (d / k["visuals"][0]["path"]).read_bytes()
    assert png[:4] == b"\x89PNG" and len(png) > 2000 and hashlib.sha256(png).hexdigest()
