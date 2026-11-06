# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik migrate surec-work --apply` (architecture §14.1–14.3) on the synthetic cases, in a temporary organization
repo (the shop fixture of tests/core/test_store.py: GPG keys in a temporary GNUPGHOME, no ssh-keygen here)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

from build_cases import OLD, snapshot  # noqa: E402
from test_store import gpg_keys, shop  # noqa: E402,F401

from mekanik.config import load_config  # noqa: E402
from mekanik.core import yamlio  # noqa: E402
from mekanik.core.checks.builtin.approval import signature  # noqa: E402
from mekanik.core.model.work import load_work  # noqa: E402
from mekanik.core.process import Refused, chief  # noqa: E402
from mekanik.core.store import git  # noqa: E402
from mekanik.migrate import apply  # noqa: E402

PASSED = {g: {"durum": "bitti", "basladi": f"2026-10-0{i}T09:00:00+03:00", "bitti": f"2026-10-0{i}T17:00:00+03:00",
              "etiket": f"TST-SYN-02-{g}"} for i, g in ((1, "G0"), (2, "G1"))}


def _old(tmp_path, case: str) -> Path:
    """The old work with gates passed in surec (kapi_durumu), next to an old branch the migration must not touch."""
    old = tmp_path / "old" / case
    shutil.copytree(OLD / case, old)
    c = yamlio.read(old / "calisma.yaml")
    yamlio.write(old / "calisma.yaml", c | {"kapi_durumu": {**PASSED, c["asama"]: {
        "durum": "suruyor", "basladi": "2026-10-03T09:00:00+03:00"}}})
    return old


def _blocks(d) -> set:
    return {(r.ref, r.extra.get("problem")) for r in signature(load_work(d)) if r.status == "block"}


def test_apply_writes_the_v1_branch_and_mg01_covers_the_passed_gates(shop, tmp_path):
    """Faz 2: §14.4 --apply — refused without the snapshot or while a V fails; then a new branch
    <code>/work/v1-migration with the files and MG-01 (hold) open, old branches untouched; the gates passed in surec
    block APPROVAL-02 until the chief's signed MG-01 approval covers them; a second apply is refused"""
    old, cfg = _old(tmp_path, "H-001"), load_config()
    git.git("branch", "TST-SYN-02/ana", cwd=shop.repo)                     # an old-system branch
    before = git.git("for-each-ref", "--format=%(refname) %(objectname)", cwd=shop.repo)
    with pytest.raises(Refused) as e:
        apply(old, cfg, None)
    assert e.value.key == "migrate.apply.no_snapshot"
    with pytest.raises(Refused) as e:
        apply(old, cfg, snapshot("H-001"), known=[])                       # V4 fails without the known changes
    assert e.value.key == "migrate.apply.verify" and "V4" in e.value.data["items"]
    assert git.git("for-each-ref", "--format=%(refname) %(objectname)", cwd=shop.repo) == before

    out = apply(old, cfg, snapshot("H-001"))
    d = out["path"]
    assert out["branch"] == "TST-SYN-02/work/v1-migration" == git.branch(d) and d.parent.name == "sentetik"
    assert {k: v["status"] for k, v in out["report"].items()} == dict.fromkeys(("V1", "V2", "V3", "V4", "V5", "V6",
                                                                                "V7", "V8"), "pass")
    after = git.git("for-each-ref", "--format=%(refname) %(objectname)", cwd=shop.repo).splitlines()
    assert set(before.splitlines()) <= set(after)                          # every old ref as it was
    assert git.trailers(git.git("log", "-1", "--format=%B", cwd=d))["Card"] == ["MG-01"]
    w, mg = yamlio.read(d / "work.yaml"), yamlio.read(d / "cards" / "MG-01.yaml")
    assert {g: s.get("migrated") for g, s in w["process"]["gate_status"].items()} == {"G0": True, "G1": True,
                                                                                     "G2": None}
    assert (mg["status"], mg["level"], mg["subject"]["gates"]) == ("open", "hold", ["G0", "G1"])
    assert (d / "records" / "migration-report.md").exists() and not git.git("status", "--porcelain", cwd=d)
    assert _blocks(d) == {("O-G0", "unapproved"), ("O-G1", "unapproved")}

    chief.approve(d, "MG-01")                                              # the chief, signed
    assert _blocks(d) == set()
    with pytest.raises(Refused) as e:
        apply(old, cfg, snapshot("H-001"))
    assert e.value.key == "migrate.apply.exists"


def test_mg01_covers_the_migrated_approvals_it_lists(shop, tmp_path):
    """Faz 2: §14.3 V5, KF1-18 — S-001's old E-01 approval is migrated unsigned; the chief's signed MG-01 approval
    covers it (MG-01's subject lists its hash); a migrated record the agent adds afterwards is not covered"""
    pytest.importorskip("cadquery")
    from mekanik.core.cards import approval

    out = apply(_old(tmp_path, "S-001"), load_config(), snapshot("S-001"))
    d = out["path"]
    assert ("E-01", "migrated") in _blocks(d)
    chief.approve(d, "MG-01")
    assert not {b for b in _blocks(d) if b[0] in ("E-01", "O-G0", "O-G1")}
    v = load_work(d)
    approval.append(v, {**v.approvals[0], "card": "E-02", "at": "2026-11-06T10:00:00+03:00"})
    git.commit(d, git.message("eski onay", None, "project_engineer"), identity=load_config().team)
    assert ("E-02", "migrated") in _blocks(d) and ("E-01", "migrated") not in _blocks(d)
