# SPDX-License-Identifier: AGPL-3.0-or-later
"""surec-work dry run, migration gaps and V1–V3 (architecture §14.2, §14.3)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import mekanik.migrate.convert as convert
from build_cases import CASES, OLD, ROOT, build
from mekanik.core import yamlio
from mekanik.core.i18n import catalogs
from mekanik.migrate.verify import WORK, v1, v2, v3

GAPS = {   # architecture §14.3 V1: v1 requires these, the old records have no counterpart (KM-37)
    "H-001": {("work.yaml", p) for p in ("done_criterion", "opened_at", "work_type", "packages", "stdlib")}
    | {("cards/MG-01.yaml", "visuals")},
    "S-001": {("work.yaml", p) for p in ("purpose", "done_criterion", "opened_at", "work_type", "packages", "stdlib")}
    | {("decisions.yaml", f"{i}/{f}") for i in range(4) for f in ("category", "options", "rationale", "opened_at")}
    | {("decisions.yaml", f"{i}/{f}") for i in (1, 2, 3) for f in ("chosen", "approved_version")}
    | {("decisions.yaml", f"{i}/basis/0/at") for i in (2, 3)}
    | {("approvals.yaml", f"0/{f}") for f in ("commit", "signature", "channel")}
    | {(f"records/calcs/{c}.json", f) for c in ("h_elle", "h_vlm")
       for f in ("purpose", "method", "validity", "input_hash", "ran_at", "code", "results/0/uncertainty_note")}
    | {("cards/MG-01.yaml", "visuals")}}


def _gaps(out: Path) -> set:
    return {(g["file"], g["path"]) for g in yamlio.read(out / "records" / "migration.yaml")["gaps"]}


@pytest.mark.parametrize("case", CASES)
def test_gap_list_and_nothing_invented(migrated, case):
    """new: KM-37 — each gap is absent from the new file; proposals are only in the report."""
    _, out, log = migrated(case)
    assert {(g["file"], g["path"]) for g in log.gaps} == GAPS[case]
    assert log.unmapped == [] and log.dropped == []
    for file, path in GAPS[case]:
        doc = json.loads((out / file).read_text()) if file.endswith(".json") else yamlio.read(out / file)
        *head, last = path.split("/")
        for p in head:
            doc = doc[int(p)] if isinstance(doc, list) else doc.get(p, {})
        assert last not in doc, (file, path)
    hint = {"file": "work.yaml", "path": "work_type", "proposal": "new_part"}     # parametric model → new_part
    assert (hint in log.gaps) == (case == "S-001")
    card = yamlio.read(out / "cards" / "MG-01.yaml")
    assert (card["type"], card["level"], card["status"], card["key"]) == ("migration_gap", "hold", "open",
                                                                          "migration_gap")
    assert f"({len(log.gaps)} " in card["title"] and card["explain"]["tr"]


@pytest.mark.parametrize("case", CASES)
def test_v1_v2_v3_pass(migrated, case):
    """new: architecture §14.3 V1 (schema with gaps only), V2 (numbers kept), V3 (source tags mapped)."""
    old, out, log = migrated(case)
    assert v1(out, _gaps(out), WORK) == []
    assert v2(old, out) == []
    assert v3(old, out, log.__dict__) == []


def test_mapping_of_names_and_sources(migrated):
    """new: guide §2 names: measured:<instrument>, derived formula, fit sides and tasks, flex sources, approvals."""
    _, out, _ = migrated("S-001")
    p = yamlio.read(out / "params.yaml")
    assert p["a_delik_cap"] == {"value": 10.0, "unit": "mm", "source": "measured:caliper"}
    assert p["e_delik_cap"]["source"] == "measured:scanner-lidar"
    assert p["b_mil_cap"] == {"unit": "mm", "source": "derived", "formula": "a_delik_cap - g01_bosluk"}
    assert "source" not in p["x_et"]                         # unsourced stays unsourced (SOURCE-01 block, G-25)
    fits = yamlio.read(out / "fits.yaml")
    assert fits["fits"][1]["task"] == "sliding" and fits["fits"][1]["sides"] == {"hole": "c_delik_cap",
                                                                                "shaft": "d_mil_cap"}
    assert [e["source"] for e in fits["flexes"]] == ["decision", "assumption"]
    a = yamlio.read(out / "approvals.yaml")[0]
    assert (a["action"], a["role"], a["identity"]["email"]) == ("approve", "chief_engineer", "test@example.org")
    assert a["migrated_from_hash"] == "316212deb71f3fad10b593ee252d71c8aca256294e03acef1f73015ea8009f20"
    d = yamlio.read(out / "decisions.yaml")
    assert [(x["status"], x["mode"], x["decided_by"]) for x in d] == [("proposed", "hold", "project_engineer")] + [
        ("approved", "hold", "project_engineer")] * 3
    assert d[2]["basis"][0]["result_hash"] == json.loads((out / "records/calcs/h_vlm.json").read_text())["result_hash"]
    assert d[3]["basis"][0]["result_hash"] != d[2]["basis"][0]["result_hash"]    # K-04's basis changed
    w = yamlio.read(out / "work.yaml")
    assert w["process"]["gates"] == ["G0", "G1", "G2", "G3", "G5"] and (w["org"], w["project"]) == ("TST", "SYN")


def test_unversioned_manufacturing_profile_is_pinned_as_derived(migrated, tmp_path):
    """new: KF1-19 — an old manufacturing profile without a version is written <id>@v0 and listed as derived"""
    old = tmp_path / "old"
    shutil.copytree(OLD / "H-001", old)
    yamlio.write(old / "calisma.yaml", (c := yamlio.read(old / "calisma.yaml")) | {
        "profiller": {**c["profiller"], "uretim": "fdm-test"}})
    _, out, log = migrated("H-001", old)
    assert yamlio.read(out / "work.yaml")["profiles"]["manufacturing"] == "fdm-test@v0"
    assert {"file": "work.yaml", "path": "profiles/manufacturing", "why": "unversioned_profile"} in log.derived
    assert catalogs()["tr"]["migrate.why.unversioned_profile"]


def test_v1_fails_on_a_wrong_value_or_an_unlisted_missing_field(migrated):
    """new: V1 accepts only missing fields recorded as gaps."""
    _, out, _ = migrated("S-001")
    w = yamlio.read(out / "work.yaml")
    yamlio.write(out / "work.yaml", w | {"risk_class": "Z9"})
    d = yamlio.read(out / "decisions.yaml")
    del d[0]["title"]
    yamlio.write(out / "decisions.yaml", d)
    bad = v1(out, _gaps(out), WORK)
    assert any(b.startswith("work.yaml:risk_class") for b in bad)
    assert any(b.startswith("decisions.yaml:0") and "'title'" in b for b in bad)


def test_v2_catches_a_broken_conversion(migrated, monkeypatch):
    """new: number conservation (old gecis.sayi_korunumu) catches a mapping that drops a value."""
    flex = dict(convert.M["fields"]["flex"]) | {"deger": None}         # a converter bug: flex values lost
    monkeypatch.setitem(convert.M["fields"], "flex", flex)
    old, out, _ = migrated("S-001")
    assert sorted(v2(old, out)) == ["- 2.0 ×1", "- 3.0 ×1"]


def test_v2_catches_a_changed_number_and_a_changed_copy(migrated):
    """new: a number changed on the way (e.g. a unit slip) and a copied model file that differs."""
    old, out, _ = migrated("S-001")
    p = yamlio.read(out / "params.yaml")
    p["blok_en"]["value"] = 3.0
    yamlio.write(out / "params.yaml", p)
    (out / "model" / "model.py").write_text("changed\n")
    bad = v2(old, out)
    assert "- 30.0 ×1" in bad and "+ 3.0 ×1" in bad and any(b.endswith("model/model.py") for b in bad)


def test_v3_catches_a_new_source_and_an_unmapped_tag(migrated, tmp_path):
    """new: an old unsourced value must stay unsourced; an old tag without a v1 mapping is reported."""
    old, out, log = migrated("S-001")
    p = yamlio.read(out / "params.yaml")
    p["x_et"]["source"] = "assumption"
    yamlio.write(out / "params.yaml", p)
    assert v3(old, out, log.__dict__) == ["x_et: None → assumption"]
    src = tmp_path / "old-H"
    shutil.copytree(OLD / "H-001", src)
    rows = yamlio.read(src / "params.yaml")
    rows[1]["kaynak"] = "tahmin"
    yamlio.write(src / "params.yaml", rows)
    _, out2, log2 = migrated("H-001", src)
    assert log2.unmapped == ["params.yaml:p2_pivot_kabarti_cap: tahmin"]
    assert v3(src, out2, log2.__dict__) == log2.unmapped + ["p2_pivot_kabarti_cap: tahmin → tahmin"]
    assert any("p2_pivot_kabarti_cap/source" in b for b in v1(out2, _gaps(out2), WORK))


def test_calc_scripts_get_the_v1_names(migrated, tmp_path):
    """new: hesaplar/*.py → calcs/*.py with the Calc names of wave 2 · B (h.girdi → h.input …)."""
    src = tmp_path / "old-S"
    shutil.copytree(OLD / "S-001", src)
    (src / "hesaplar").mkdir()
    (src / "hesaplar" / "h_x.py").write_text('AD = "h_x"\nBASLIK = "x"\n\ndef hesapla(h, model):\n'
                                             '    a = h.girdi("blok_en")\n    h.sabit("g", 9.8, "m/s", "standart:x")\n'
                                             '    h.buyukluk("sm", a, "-", 1, "elle")\n')
    _, out, _ = migrated("S-001", src)
    text = (out / "calcs" / "h_x.py").read_text()
    assert 'ID = "h_x"' in text and "def calculate(h, model)" in text and 'h.input("blok_en")' in text
    assert 'h.const("g"' in text and 'h.magnitude("sm"' in text


def test_cases_are_the_migration_output(tmp_path, cfg):
    """new: tests/cases/{S-001,H-001} are what build_cases.py makes now. Not compared: stamps and the report
    (records/, MG-01) and approvals.yaml, whose v1 hash follows the card subjects of waves 2 · A and C."""
    for case in CASES:
        build(case, tmp_path / case, cfg)
        for f in sorted((ROOT / "tests" / "cases" / case).rglob("*")):
            rel = f.relative_to(ROOT / "tests" / "cases" / case)
            if f.is_file() and rel.parts[0] != "records" and rel.name not in ("MG-01.yaml", "approvals.yaml"):
                assert (tmp_path / case / rel).read_text() == f.read_text(), (case, rel)


def test_catalog_has_every_migration_key():
    """new: the report and card texts come from tr.migrate.yaml (and en), rule 4."""
    reasons = {d["why"].split(":")[0] for case in CASES
               for d in yamlio.read(ROOT / "tests" / "cases" / case / "records" / "migration.yaml")["derived"]}
    reasons |= {"machine_type", "name_from_id", "instrument_tag"}
    for lang in ("tr", "en"):
        cat = catalogs()[lang]
        assert all(f"migrate.why.{r}" in cat for r in reasons), lang
        assert all(f"migrate.{k}" in cat for k in ("apply_phase2", "card.title", "card.explain", "report.title",
                                                   "report.gaps", "status.pending", "pending.rules", "pending.model"))
