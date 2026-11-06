# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.8: the old panel e2e tests (testler/test_panel_e2e.py) on the new back end, where they need a server answer:
4 (a value change drops the approval), 5 (a branch from a past point, nothing deleted), 12 (a decision card's
option with confirmation, then undo), 13 (assumption list rows), 14 (calculations), 15 (a step's detail), 17 (a
model note). 1, 2, 6, 7, 8, 16 are in test_jobs, test_live and test_security; 3, 9, 10 in test_model; 11 is the
viewer alone. Card figures come from a stand-in package (as in tests/core/test_policy_flow.py)."""

from __future__ import annotations

import base64

import pytest
from test_policy_flow import TEXT, Figures, _opts
from test_process import CALC

from mekanik.core import yamlio
from mekanik.core.builtin import SPEC
from mekanik.core.decisions import open_decision
from mekanik.core.process.step import step
from mekanik.core.store import git
from mekanik.plugins import PackageSpec, set_registry
from test_store import PARAMS, new, prepare


@pytest.fixture(autouse=True)
def _figures(_core_only):
    set_registry([SPEC, PackageSpec(id="fig", version="0.1.0", model=Figures())])


def _ready(params=None):
    code, d = new()
    prepare(d, params=params or PARAMS)
    step(d, "hazırlık", "project_engineer")
    return code, d


def _card(panel, code, cid):
    return next(c for c in panel.get(f"/api/works/{code}/cards").json()["cards"] if c["id"] == cid)


def test_4_value_change_drops_the_approval(panel, shop):
    """2.8: e2e 4 — the chief approves a card from the panel; his value entered from the panel changes what it rests
    on, the approval drops and the card is open again; the value's commit is in the log"""
    code, d = _ready()
    (d / "calcs").mkdir()
    (d / "calcs" / "h1.py").write_text(CALC.format(id="h1", k=1.0, level=1, method="elle", status="ok"))
    (d / "calcs" / "h2.py").write_text(CALC.format(id="h2", k=1.3, level=2, method="VLM", status="ok"))
    step(d, "hesaplar", "project_engineer")
    cid = next(c["id"] for c in panel.get(f"/api/works/{code}/cards").json()["cards"] if c["key"] ==
               "consistency:alan")
    r = panel.post(f"/api/works/{code}/cards/{cid}/decision", json={"action": "approve", "confirmed": True})
    assert r.status_code == 200, r.text
    assert _card(panel, code, cid)["status"] == "approved"
    r = panel.post(f"/api/works/{code}/values", json={"param": "blok_en", "value": 24.0, "reason": "sınama",
                                                      "card": cid})
    assert r.status_code == 200, r.text
    c = _card(panel, code, cid)
    assert (c["status"], c.get("approval_state")) == ("open", "dropped")
    assert yamlio.read(d / "approvals.yaml")[-1]["action"] == "value_change"
    assert any("blok_en" in e["line"] for e in panel.get(f"/api/works/{code}/stream").json()["events"][-3:])


def test_5_branch_from_a_past_point_deletes_nothing(panel, g0):
    """2.8: e2e 5 — "open a branch here": a new work branch at the chosen commit; every ref stays where it was"""
    code, d = g0
    refs = set(git.git("for-each-ref", "--format=%(refname) %(objectname)", cwd=d).splitlines())
    first = panel.get(f"/api/works/{code}/branches").json()["commits"][-1]["sha"]
    r = panel.post(f"/api/works/{code}/branches", json={"commit": first, "name": "geri-donus"})
    assert r.status_code == 200 and r.json()["branch"] == f"{code}/work/geri-donus"
    after = set(git.git("for-each-ref", "--format=%(refname) %(objectname)", cwd=d).splitlines())
    assert refs < after and f"refs/heads/{code}/work/geri-donus {first}" in after
    assert panel.post(f"/api/works/{code}/branches", json={"commit": first, "name": "Kötü Ad"}).json()["error"][
        "key"] == "panel.branch.bad_name"
    names = {b["name"]: b for b in panel.get(f"/api/works/{code}/branches").json()["branches"]}
    assert names[f"{code}/work/geri-donus"]["kind"] == "work" and names[f"{code}/main"]["kind"] == "main"


def test_12_decision_option_confirmed_then_undone(panel, shop):
    """2.8: e2e 12 — a decision card: approval needs the confirmation (Ö-14); the chosen option is recorded with the
    channel panel_confirmed; undo needs a reason and the confirmation and writes an `undo` record (Ö-15)"""
    code, d = _ready()
    open_decision(d, "K-01", "biçim", _opts(a="x", b="y"), "sınama", branched=False, **TEXT)
    url = f"/api/works/{code}/cards/K-01"
    assert len(_card(panel, code, "K-01")["options"]) == 2
    r = panel.post(url + "/decision", json={"action": "approve", "option": "b"})
    assert r.json()["error"]["key"] == "panel.confirm.required"
    r = panel.post(url + "/decision", json={"action": "approve", "option": "b", "confirmed": True})
    assert r.status_code == 200, r.text
    rec = next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == "K-01")
    assert rec["chosen"] == "b" and yamlio.read(d / "approvals.yaml")[-1]["channel"] == "panel_confirmed"
    r = panel.post(url + "/revert", json={"reason": "yanlış tık"})
    assert r.json()["error"]["key"] == "panel.confirm.required"
    assert panel.post(url + "/revert", json={"confirmed": True}).json()["error"]["key"] == "panel.confirm.undo_reason"
    r = panel.post(url + "/revert", json={"reason": "geri-donus", "confirmed": True})
    assert r.status_code == 200, r.text
    last = yamlio.read(d / "approvals.yaml")[-1]
    assert (last["action"], last["reason"], last["channel"]) == ("undo", "geri-donus", "panel_confirmed")


def test_13_assumption_list_rows(panel, shop):
    """2.8: e2e 13 — the assumption list is not a hold card: approved without the dialog, row by row"""
    params = {**PARAMS, "pim_boy": {"value": 20.0, "unit": "mm", "source": "assumption", "description": "Pimin boyu.",
                                    "rationale": "Bloktan iki yana taşsın, elle tutulsun."}}
    code, d = _ready(params)
    v01 = _card(panel, code, "V-01")
    assert v01["level"] != "hold" and "pim_boy" in v01["subject"]["params"]
    r = panel.post(f"/api/works/{code}/cards/V-01/decision", json={"action": "approve", "rows": ["pim_boy"]})
    assert r.status_code == 200, r.text
    last = yamlio.read(d / "approvals.yaml")[-1]
    assert (last["card"], last.get("row"), last["action"]) == ("V-01", "pim_boy", "approve")


def test_14_15_calculations_and_step_detail(panel, shop):
    """2.8: e2e 14, 15 — the recorded calculation with its steps and results; a step's detail: its text, the files it
    changed, params before → after"""
    code, d = _ready()
    (d / "calcs").mkdir()
    (d / "calcs" / "h1.py").write_text(CALC.format(id="h1", k=1.0, level=1, method="elle", status="ok"))
    raw = yamlio.read(d / "params.yaml")
    raw["blok_en"]["value"] = 22.0
    yamlio.write(d / "params.yaml", raw)
    sha = step(d, "hesap eklendi", "design_engineer", "Ne yaptı: alan hesabı")["commit"]
    calcs = panel.get(f"/api/works/{code}/calcs").json()["calcs"]
    assert calcs[0]["id"] == "h1" and calcs[0]["results"][0]["value"] == 22.0
    det = panel.get(f"/api/works/{code}/steps/{sha[:7]}").json()
    assert det["title"] == "hesap eklendi" and det["trailers"]["Role"] == "design_engineer"
    assert {f["path"] for f in det["files"]} >= {"calcs/h1.py", "params.yaml"}
    assert [(p["name"], p["before"]["value"], p["after"]["value"]) for p in det["params"]] == [("blok_en", 20.0, 22.0)]
    assert det["code_diff"][0]["path"] == "calcs/h1.py" and panel.get(f"/api/works/{code}/steps/zzz").status_code == 404


def test_17_model_note(panel, g0):
    """2.8: e2e 17 — a note on the model: card N-01 with the screenshot, the part and the point; it waits for the
    team's reply; a broken image is refused"""
    code, d = g0
    png = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 2100).decode()
    r = panel.post(f"/api/works/{code}/model-notes", json={"text": "Bu köşeyi yuvarlat", "png": png, "part": "blok",
                                                          "point": [1.234, 2.0, 3.0], "box": [0.1, 0.1, 0.3, 0.3]})
    assert r.status_code == 200, r.text
    k = yamlio.read(d / "cards" / "N-01.yaml")
    assert k["question"] == "Bu köşeyi yuvarlat" and k["subject"]["part"] == "blok" and k["subject"]["point"] == [
        1.23, 2.0, 3.0]
    assert (d / k["visuals"][0]["path"]).read_bytes()[:4] == b"\x89PNG"
    assert [c["id"] for c in panel.get(f"/api/works/{code}/status").json()["team_cards"]] == ["N-01"]
    bad = panel.post(f"/api/works/{code}/model-notes", json={"text": "x", "png": "data:image/png;base64,***"})
    assert bad.json()["error"]["key"] == "process.note.bad_image"
