# SPDX-License-Identifier: AGPL-3.0-or-later
"""2.5: F1 — the seeded-error corpus (architecture §10.11): 30 synthetic cases, one seeded error each, in the twelve
kinds and counts of F1. Each case is run twice: seeded, the error must be caught before a gate or a decision (the
rule's block or hold card, the gate's required checklist item failing, or the gate/decision action refused); fixed
(the same case with the error corrected), the same rule must pass and nothing may block (no false alarm).

Frozen cases (tests/corpus/F1/F1-nn.yaml without `flow`) are work folders written from the YAML (the common work
_base.yaml, then the case's `base`, then `seed` or `fix`; calc records are written from their recorded fields and a
`{hash:<calc>}` token takes that calc's result hash at the time of its phase) and judged by the registered checks, the
cards made from them and the checklist of the case's gate. Cases with a `flow` run the process in the shop of
tests/core/test_store.py (git, the chief's GPG-signed approvals). mech cases register the fit checks without the model
hooks: their errors are in the fit record; the geometric checks (SOLID-01, INTERF-01, UNREG-01) need a model and OCCT.
A case not caught is a finding: the test fails, it is not marked xfail."""

from __future__ import annotations

import copy
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.builtin import SPEC as CORE
from mekanik.core.cards import generate
from mekanik.core.checks import runner
from mekanik.core.checks.result import BLOCK
from mekanik.core.errors import MekanikError, SchemaError
from mekanik.core.evidence import calc
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, gates
from mekanik.plugins import PackageSpec, set_registry

HERE = Path(__file__).resolve().parent / "F1"
BASE = yamlio.read(HERE / "_base.yaml")
CASES = {c["id"]: c for c in (yamlio.read(p) for p in sorted(HERE.glob("F1-*.yaml")))}
AT = "2026-11-06T10:00:00+03:00"
GEOMETRIC = ("mech.interference", "mech.unregistered_fit")   # need the model (OCCT); not these cases' errors
F1_KINDS = {"unsourced": 4, "independent_fit": 3, "out_of_domain": 3, "methods_disagree": 3,
            "no_second_method": 2, "stale_approval": 3, "unmeasured_observation": 2, "basis_changed": 2,
            "tick_without_evidence": 2, "open_high_quality": 2, "unmet_mandatory_g5": 2, "form_instrument": 2}


class Figures:
    """Stand-in model hooks of the process cases (as tests/core/test_policy_flow.py): no model, one figure per card
    and per option of a decision card, so that the cards meet the card standard (CARD-01) without OCCT."""

    def build(self, view):
        return None

    def producer_version(self):
        return "0"

    def has(self, name):
        return False

    def card_visuals(self, view, card, model, option_values=None, base=None):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><text>{}</text></svg>'.format
        if card.get("options"):
            return [(o["id"], svg(f"{card['id']} {o['id']}")) for o in card["options"]], []
        return [("fig", svg(card["id"]))], []


def packages(names=(), figures: bool = False):
    """The core and, for `mech`, the fit checks of mech (no model hooks) with the print3d profile type; `figures`
    adds the stand-in card figures (process cases)."""
    specs = [CORE, *([PackageSpec(id="fig", version="0.1.0", model=Figures())] if figures else [])]
    if "mech" in names:
        import mekanik_mech
        import mekanik_print3d

        specs += [replace(mekanik_mech.SPEC, model=None, checks=[c for c in mekanik_mech.SPEC.checks
                                                                 if c.id not in GEOMETRIC]),
                  replace(mekanik_print3d.SPEC, release_hooks=[])]
    return set_registry(specs)


# ---------------------------------------------------------------- frozen cases: build, judge

def record(code: str, cid: str, s: dict) -> dict:
    """A calc record (records/calcs/<id>.json) from the fields the case gives; the rest as a step writes them."""
    mags = [dict(zip(("name", "value", "unit", "level", "method"), m)) if isinstance(m, list) else m
            for m in s.get("magnitudes") or []]
    results = [{"status": "ok", "uncertainty_note": "none_available", **r} for r in s.get("results") or [
        {"name": m["name"], "value": m["value"], "unit": m["unit"]} for m in mags]]
    rec = {"kind": "calculation", "schema_version": "1.0", "id": cid, "work": code, "title": s["title"],
           "purpose": s.get("purpose", s["title"]), "type": "calculation",
           **({"method": {"name": mags[0]["method"], "level": mags[0]["level"]}} if mags else {}),
           **({"critical": True} if s.get("critical") else {}), "inputs": s.get("inputs") or [], "constants": [],
           "steps": [], "results": results, "magnitudes": mags, "charts": [], "notes": [], "visuals": [],
           "read_calculations": s.get("reads") or [], "validity": {"domain": [], "zone": "validation",
                                                                  "in_domain": True, **(s.get("validity") or {})},
           "input_hash": "0" * 16, "ran_at": AT, "error": s.get("error")}
    return {**rec, "result_hash": calc.result_hash(rec)}


def _tokens(root: Path, doc):
    if isinstance(doc, dict):
        return {k: _tokens(root, v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [_tokens(root, v) for v in doc]
    if isinstance(doc, str) and doc.startswith("{hash:") and doc.endswith("}"):
        return calc.current_hash(root, doc[6:-1])
    return doc


def _phase(root: Path, code: str, phase: dict) -> None:
    for cid, spec in (phase.get("calcs") or {}).items():
        yamlio.write_text(root / calc.FOLDER / f"{cid}.json", json.dumps(record(code, cid, spec), ensure_ascii=False))
    for rel, doc in (phase.get("files") or {}).items():
        if doc is None:
            (root / rel).unlink(missing_ok=True)
        elif isinstance(doc, str) and not rel.endswith((".yaml", ".json")):
            yamlio.write_text(root / rel, doc)
        else:
            yamlio.write(root / rel, _tokens(root, doc))


def build(root: Path, case: dict, variant: str) -> Path:
    """The case's work folder: _base.yaml with the case's stage and work fields, `base`, then `seed` or `fix`."""
    files = copy.deepcopy(BASE)
    w, stage = files["work.yaml"], case.get("stage", "G3")
    w["process"].update(stage=stage, gate_status={stage: {"status": "in_progress", "started_at": AT}})
    w.update(copy.deepcopy(case.get("work") or {}))
    first = copy.deepcopy(case.get("base") or {})
    _phase(root, w["code"], {"calcs": first.get("calcs"), "files": {**files, **(first.get("files") or {})}})
    _phase(root, w["code"], copy.deepcopy(case.get(variant) or {}))
    return root


def act(root: Path, a: dict | None) -> str | None:
    """A command the case runs on its work before it is judged → the refusal key, or None."""
    if not a:
        return None
    if a["call"] == "stdmap_tick":   # `mekanik stdmap tick`
        from mekanik.core import stdmap

        return _outcome(lambda: stdmap.tick(root, a["item"], a.get("evidence") or [], a["review"]))["refused"]
    raise ValueError(a["call"])


def judge(root: Path, case: dict) -> dict:
    """{error} when the loader refuses the records, else {results, cards, items}."""
    try:
        view = load_work(root)
    except SchemaError as e:
        return {"error": e}
    results = runner.run(view, None)
    cards = generate(view, results)
    gate = (case["expect"].get("gate") or {}).get("gate")
    return {"view": view, "results": results, "cards": cards,
            "items": gates.items(view, gate, results, cards) if gate else []}


def _matches(results, exp: dict) -> list:
    return [r for r in results if r.rule == exp["rule"] and r.ref == exp["ref"]]


def seeded_caught(case: dict, got: dict) -> list[str]:
    """What caught the seeded error (empty: not caught); every expectation of the case must hold."""
    exp, found, missing = case["expect"], [], []
    if exp.get("load_error"):
        (found if "error" in got else missing).append("loader: SchemaError")
        return found if not missing else []
    if "error" in got:
        return []
    if exp.get("refused"):
        (found if got.get("refused") == exp["refused"] else missing).append(f"refused {exp['refused']}")
    for e in exp.get("results") or []:
        rel = _matches(got["results"], e)
        ok = any(r.status == BLOCK for r in rel) if e["result"] == BLOCK else any(r.failed for r in rel)
        (found if ok else missing).append(f"{e['rule']} {e['result']} ({e['ref']})")
    keys = {c["key"]: c for c in got["cards"] if c.get("status") in ("open", "awaiting_reply")}
    for k in exp.get("cards") or []:
        (found if k in keys and keys[k]["level"] == "hold" else missing).append(f"card {k}")
    if g := exp.get("gate"):
        failed = {x["id"] for x in got["items"] if x["required"] and not x["ok"]}
        (found if set(g["fails"]) <= failed else missing).append(f"{g['gate']} {', '.join(g['fails'])}")
    return found if not missing else []


def fixed_clean(case: dict, got: dict) -> list[str]:
    """Why the fixed twin is not clean (empty: it passes)."""
    if "error" in got:
        return [f"loader: {got['error']}"]
    exp, out = case["expect"], [f"refused {got['refused']}"] if got.get("refused") else []
    for e in exp.get("results") or []:
        rel = _matches(got["results"], e)
        if not rel or any(r.failed for r in rel):
            out.append(f"{e['rule']} ({e['ref']}): " + ("; ".join(f"{r.status} {r.reason}" for r in rel) or "none"))
    out += [f"card {c['key']}" for c in got["cards"] if c["key"] in (exp.get("cards") or [])
            and c.get("status") in ("open", "awaiting_reply")]
    out += [f"block {r.rule} ({r.ref}): {r.reason}" for r in got["results"] if r.status == BLOCK]
    out += [f"{exp['gate']['gate']} {x['id']}" for x in got["items"] if x["required"] and not x["ok"]]
    return out


# ---------------------------------------------------------------- cases with the process (shop): flows

FLOWS = {}


def flow(fn):
    FLOWS[fn.__name__] = fn
    return fn


def _outcome(call) -> dict:
    """{refused: catalog key | None, data}: a refused action. A MekanikError that is not a Refused keeps no key; it is
    named by its type (the quality flow checks what it was)."""
    try:
        return {"refused": None, "data": call()}
    except Refused as e:
        return {"refused": e.key, "data": e.data}
    except MekanikError as e:
        return {"refused": f"error:{type(e).__name__}", "data": {"text": str(e)}}


def _work(case: dict, data: dict, fixed: bool):
    """A new work in the shop (one per twin): one requirement, its params, fit record, calcs and model, committed by
    a step."""
    from test_store import REQUIREMENTS

    from mekanik.core.process.step import step
    from mekanik.core.store import works

    variant = data.get("fix" if fixed else "seed") or {}
    code = works.new_work("TST", "SYN", case["title"], "C", "F1", "hata yakalanır", profiles=data.get("profiles"))
    d = works.find(code)
    yamlio.write(d / "requirements.yaml", {**yamlio.read(d / "requirements.yaml"), "items": REQUIREMENTS})
    yamlio.write(d / "params.yaml", {**data["params"], **(variant.get("params") or {})})
    if data.get("fits"):
        yamlio.write(d / "fits.yaml", {"fits": data["fits"]})
    for name, text in (data.get("calcs") or {}).items():
        yamlio.write_text(d / "calcs" / f"{name}.py", text)
    if data.get("model"):
        yamlio.write_text(d / "model" / "model.py", data["model"])
    step(d, "hazırlık", "design_engineer")
    return d, variant


@flow
def stale_approval(shop, case, fixed) -> dict:
    """Pass G0 and G1; at G3 the chief approves the case's cards; then (seeded) what an approval rests on changes:
    a param in the work, or an instrument or machine file of the workshop in place. G3 is asked and approved."""
    from test_store import review

    from mekanik.core.process import chief
    from mekanik.core.process.step import evaluate, step

    data = case["data"]
    packages(case.get("packages") or (), figures=True)
    d, _ = _work(case, data, fixed)
    for gate in ("G0", "G1"):
        review(d)
        gates.stage_finish(d, gate)
        chief.approve(d, f"O-{gate}")
    for key in data["approve"]:
        chief.approve(d, next(c["id"] for c in evaluate(d)[3] if c["key"] == key))
    ch = data["change"]
    if not fixed and "param" in ch:
        p = yamlio.read(d / "params.yaml")
        p[ch["param"]]["value"] = ch["value"]
        yamlio.write(d / "params.yaml", p)
        step(d, "değer değişti", "design_engineer")
    elif not fixed:   # a workshop file edited in place: not the work's records
        doc = yamlio.read(path := shop.config / ch["file"])
        node = doc
        for k in ch["path"][:-1]:
            node = node[k]
        node[ch["path"][-1]] = ch["value"]
        yamlio.write(path, doc)
    states = {c["key"]: c.get("approval_state") for c in evaluate(d)[3] if c["key"] in data["approve"]}
    review(d)
    gates.stage_finish(d, "G3")
    return {**_outcome(lambda: chief.approve(d, "O-G3")), "states": states}


@flow
def decision_basis(shop, case, fixed) -> dict:
    """A recorded calc is the basis of a (provisional) decision the team opens. Both ways it can close are tried: the
    chief approves it; the gate its objection window ends at (G0) is asked and passed, which would accept it."""
    from test_store import review

    from mekanik.core.decisions import open_decision
    from mekanik.core.process import chief

    data = case["data"]
    packages(figures=True)
    d, _ = _work(case, data, fixed)
    did = "K-01" if fixed else "K-02"   # one repo for both twins: a decision number is never given twice
    open_decision(d, did, data["title"], data["options"], data["rationale"], branched=False,
                  basis=data["basis"], **data["card"])
    zones = {c: calc.recorded(d)[c]["validity"]["zone"] for c in data["basis"]}
    first = _outcome(lambda: chief.approve(d, did, option=data["option"]))
    review(d)
    gates.stage_finish(d, "G0")
    gate = _outcome(lambda: chief.approve(d, "O-G0"))
    status = next(x for x in yamlio.read(d / "decisions.yaml") if x["id"] == did)["status"]
    return {"refused": first["refused"], "data": first["data"], "zones": zones, "gate": gate["refused"],
            "decision": status, "refusals": [first["refused"], gate["refused"]]}


@flow
def gate_request(shop, case, fixed) -> dict:
    """Calcs recorded by a step; the team asks the G0 gate (stage finish), then the chief approves it."""
    from test_store import review

    from mekanik.core.process import chief

    data = case["data"]
    packages(figures=True)
    d, _ = _work(case, data, fixed)
    review(d)
    out = _outcome(lambda: gates.stage_finish(d, "G0"))
    if out["refused"] is None:
        out = _outcome(lambda: chief.approve(d, "O-G0"))
    return {**out, "cross_check": {k: (r.get("cross_check") or {}).get("status") for k, r in calc.recorded(
        d).items() if r.get("critical")}}


@flow
def decide(shop, case, fixed) -> dict:
    """The team opens a decision (`mekanik decide`) resting on observations."""
    from mekanik.core.decisions import open_decision

    data = case["data"]
    packages(figures=True)
    d, variant = _work(case, data, fixed)
    return _outcome(lambda: open_decision(d, "K-01" if fixed else "K-02", data["title"], data["options"],
                                          data["rationale"], branched=False, observations=variant["observations"],
                                          **data["card"]))


@flow
def quality(shop, case, fixed) -> dict:
    """The quality engineer's review of the request has a high finding; the team asks the gate (or a release);
    fixed: the finding is closed with a rationale and its regression note first."""
    from test_store import review

    from mekanik.core import quality as q
    from mekanik.core.process import chief, release

    data = case["data"]
    if data["request"] == "release":
        pytest.importorskip("cadquery")   # the release files come from the model (mech, print3d)
    else:
        packages(figures=True)
    d, _ = _work(case, data, fixed)
    review(d, data["review"])
    if fixed:
        (path, rep), = q.reports(d)
        for f in q.open_high(rep):
            q.close(d, path.name, f["no"], data["close"]["rationale"], True, data["close"]["regression"])
    out = _outcome(lambda: release.release_request(d)) if data["request"] == "release" else _outcome(
        lambda: gates.stage_finish(d, "G0"))
    if out["refused"] == "error:MekanikError":   # the quality gate's refusal: open high findings, no request card
        high, card = q.open_high(q.current(d)[1]), "B-*" if data["request"] == "release" else "O-G0"
        out = {**out, "refused": "quality.open_high", "open_high": len(high)} if high and not list(
            (d / "cards").glob(f"{card}.yaml")) else out
    if out["refused"] is None and data["request"] == "gate":
        out = _outcome(lambda: chief.approve(d, "O-G0"))
    return out


# ---------------------------------------------------------------- the tests

def run_case(case: dict, tmp_path, request) -> dict:
    """{caught: what caught the seeded error, problems: what flagged the fixed twin}."""
    if fl := case.get("flow"):
        shop = request.getfixturevalue("corpus_shop")
        fixed = FLOWS[fl](shop, case, fixed=True)     # first: the seeded twin may change the workshop config
        seeded = FLOWS[fl](shop, case, fixed=False)
        exp = case["expect"]
        ok = all(seeded.get(k) == v for k, v in exp.items())
        caught = [f"refused {seeded['refused']}"] + [f"{k}: {seeded[k]}" for k in exp if k != "refused"] if ok else []
        problems = [f"refused {k}: {fixed['data']}" for k in fixed.get("refusals") or [fixed["refused"]] if k]
        return {"caught": caught, "problems": problems, "seeded": seeded, "fixed": fixed}
    request.getfixturevalue("monkeypatch").setenv("MEKANIK_CONFIG_DIR", str(request.getfixturevalue(
        "corpus_config")))
    packages(case.get("packages") or ())
    twins = {}
    for variant in ("seed", "fix"):
        root = build(tmp_path / variant, case, variant)
        refused = act(root, (case.get(variant) or {}).get("act"))
        twins[variant] = {**judge(root, case), "refused": refused}
    s, f = twins["seed"], twins["fix"]
    return {"caught": seeded_caught(case, s), "problems": fixed_clean(case, f), "seeded": s, "fixed": f}


@pytest.mark.parametrize("cid", [pytest.param(c, marks=pytest.mark.occt) if CASES[c].get("occt") else c
                                 for c in sorted(CASES)])
def test_seeded_error_is_caught_and_its_fix_passes(cid, tmp_path, request, f1_outcomes):
    """2.5: F1 — the seeded error is caught before the gate or the decision; its fixed twin passes (no false
    alarm)"""
    case = CASES[cid]
    out = run_case(case, tmp_path, request)
    f1_outcomes[cid] = {"kind": case["category"], "caught": out["caught"], "clean": not out["problems"]}
    assert out["caught"], f"{cid} not caught: {case['error']}"
    assert not out["problems"], f"{cid} fixed twin flagged: {out['problems']}"


def test_corpus_is_the_thirty_cases_of_f1():
    """2.5: F1 — 30 cases in the twelve kinds and counts of architecture §10.11, each with its error, its fix and
    what must catch it"""
    assert len(CASES) == 30 and Counter(c["category"] for c in CASES.values()) == F1_KINDS
    for cid, c in CASES.items():
        assert c["error"].strip() and c["fixed"].strip() and c["expect"], cid
        assert c.get("flow") in (None, *FLOWS) and (c.get("flow") or c.get("seed") or c.get("fix")), cid
