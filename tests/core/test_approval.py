# SPDX-License-Identifier: AGPL-3.0-or-later
"""Approval records, approval state, design hash and APPROVAL-02 signatures (old test_cekirdek and new)."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from mekanik.core import yamlio
from mekanik.core.cards import approval, makers, signature
from mekanik.core.checks.builtin import CHECKS
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.model.work import load_work
from mekanik.core.store import git as gitmod
from mekanik.plugins import PackageSpec, reset_registry, set_registry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONFIG = ROOT / "tests" / "fixtures" / "config"
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(FIXTURE_CONFIG))
CHIEF = ("Test Mühendis", "test@example.org")
TEAM = ("mekanik-ekip", "ekip@mekanik.local")
CORE = PackageSpec(id="core", version="0", checks=CHECKS, card_makers=[makers.make])
WORK = {"kind": "work", "schema_version": "1.0", "code": "TST-SYN-09", "title": "Sınama", "org": "TST",
        "project": "SYN", "work_type": "part", "risk_class": "B", "purpose": "sınama", "done_criterion": "testler",
        "stdlib": "2026.11", "packages": [], "opened_at": "2026-11-06T10:00:00+03:00",
        "profiles": {"instruments": ["caliper", "scanner-lidar"]},
        "process": {"profile": "default@1", "gates": ["G0", "G1", "G2", "G3", "G5"], "stage": "G2", "gate_status": {}}}
PARAMS = {"hole_dia": {"value": 10.0, "unit": "mm", "source": "measured:caliper"},
          "gap": {"value": 0.3, "unit": "mm", "source": "decision"},
          "shaft_dia": {"value": None, "unit": "mm", "source": "derived", "formula": "hole_dia - gap"}}
SUBJECT = {"params": ["gap", "hole_dia", "shaft_dia"]}


def work(tmp, params=None):
    yamlio.write(tmp / "work.yaml", WORK)
    yamlio.write(tmp / "params.yaml", PARAMS if params is None else params)
    return load_work(tmp)


@pytest.fixture(autouse=True)
def _registry():
    set_registry([CORE])
    yield
    reset_registry()


def test_hash_canonical_json_order_irrelevant():
    """old: test_cekirdek::ozet_kanonik_json_sirasi_onemsiz"""
    assert approval.digest({"a": 1, "b": [1, 2]}) == approval.digest({"b": [1, 2], "a": 1})
    assert approval.digest({"a": 1.0}) != approval.digest({"a": 1.05})


def test_number_format_does_not_change_hash():
    """old: test_cekirdek::sayi_yazimi_ozeti_degistirmez"""
    assert approval.digest({"a": 10}) == approval.digest({"a": 10.0})


def test_approvals_only_appended(tmp_path):
    """old: test_cekirdek::onaylar_yalniz_eklenir"""
    v = work(tmp_path)
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF))
    approval.append(v, approval.record(v, "S-01", SUBJECT, "reject", CHIEF, reason="boşluk dar"))
    assert [r["action"] for r in yamlio.read(tmp_path / "approvals.yaml")] == ["approve", "reject"]
    assert approval.state(load_work(tmp_path), "S-01", SUBJECT) == "rejected"


def test_empty_list_approvals_file_not_broken(tmp_path):
    """old: test_cekirdek::bos_liste_onaylar_dosyasi_bozulmaz"""
    v = work(tmp_path)
    (tmp_path / "approvals.yaml").write_text("[]\n")
    v.approvals = []
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF))
    approval.append(v, approval.record(v, "S-01", SUBJECT, "comment", CHIEF, reason="not"))
    assert [r["action"] for r in load_work(tmp_path).approvals] == ["approve", "comment"]


def test_unauthorized_approval_refused_and_not_counted(tmp_path):
    """old: test_cekirdek::yetkisiz_onay_reddedilir_ve_sayilmaz"""
    v = work(tmp_path)
    with pytest.raises(PermissionError):
        approval.record(v, "S-01", SUBJECT, "approve", TEAM)
    rec = {**approval.record(v, "S-01", SUBJECT, "approve", CHIEF), "identity": dict(zip(("name", "email"), TEAM))}
    v.approvals.append(rec)
    assert approval.state(v, "S-01", SUBJECT) == "none"


def test_first_name_alone_is_not_the_chief(tmp_path):
    """new: Ek A, onay.py:112 — 'Test Sahte' passed the old first-name check; v1 compares name and e-mail exactly"""
    v = work(tmp_path)
    for who in (("Test Sahte", CHIEF[1]), (CHIEF[0], "baska@example.org"), ("test mühendis", CHIEF[1])):
        assert not approval.authorized(v, who)
        with pytest.raises(PermissionError):
            approval.record(v, "S-01", SUBJECT, "approve", who)
    assert approval.authorized(v, CHIEF) and approval.authorized(v, {"name": CHIEF[0], "email": CHIEF[1]})


def test_instrument_uncertainty_change_drops_approval(tmp_path):
    """old: test_cekirdek::olcum_belirsizligi_degisince_onay_duser"""
    v = work(tmp_path)
    subject = {"params": ["hole_dia"]}
    approval.append(v, approval.record(v, "S-01", subject, "approve", CHIEF))
    assert approval.state(v, "S-01", subject) == "approved"
    v.instruments["caliper"] = {**v.instruments["caliper"],
                                "uncertainty": {"value": 0.02, "unit": "mm", "source": "measured:caliper"}}
    assert approval.state(v, "S-01", subject) == "dropped"


def test_rejected_value_change_reviewed_again(tmp_path):
    """old: test_cekirdek::reddedilen_deger_degisince_yeniden_incelenir"""
    v = work(tmp_path)
    subject = {"params": ["gap"]}
    approval.append(v, approval.record(v, "S-01", subject, "reject", CHIEF, reason="dar"))
    assert approval.state(v, "S-01", subject) == "rejected"
    v.params["gap"].value = 0.25
    assert approval.state(v, "S-01", subject) == "none"


def test_undo_cancels_the_nearest_decision(tmp_path):
    """new: `undo` cancels the nearest earlier approve or reject; nothing is deleted (old geri_al)"""
    v = work(tmp_path)
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF))
    approval.append(v, approval.record(v, "S-01", SUBJECT, "reject", CHIEF, reason="dar"))
    approval.append(v, approval.record(v, "S-01", SUBJECT, "undo", CHIEF, undoes="abc1234"))
    assert approval.state(v, "S-01", SUBJECT) == "approved" and len(v.approvals) == 3


def test_design_hash_covers_core_and_package_files(tmp_path):
    """new: gate approvals are bound to the design files of the core and of packages (design_files)"""
    v = work(tmp_path)
    set_registry([CORE, PackageSpec(id="pkg", version="0", design_files=("extra.yaml",))])
    h0 = approval.design_hash(tmp_path)
    (tmp_path / "extra.yaml").write_text("a: 1\n")
    h1 = approval.design_hash(tmp_path)
    (tmp_path / "calcs" / "__pycache__").mkdir(parents=True)
    (tmp_path / "calcs" / "__pycache__" / "x.pyc").write_bytes(b"x")
    assert h0 != h1 == approval.design_hash(tmp_path)
    assert approval.state(v, "O-G2", {"gate": "G2", "design": True}) == "none"


# ------------------------------------------------------------------ APPROVAL-02: commit signature


def _run(*args, **kw):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kw).stdout


@pytest.fixture
def gpg_work(tmp_path, monkeypatch):
    """A work in a git repo; two GPG keys (chief, other); the workshop config pins the chief key."""
    if not shutil.which("gpg"):
        pytest.skip("gpg not installed")
    home = tmp_path / "gnupg"
    home.mkdir(mode=0o700)
    monkeypatch.setenv("GNUPGHOME", str(home))
    (tmp_path / "gitconfig").write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    keys = {}
    for who, uid in (("chief", f"{CHIEF[0]} <{CHIEF[1]}>"), ("other", "Başka <baska@example.org>")):
        _run("gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key", uid,
             "ed25519", "sign", "never")
        out = _run("gpg", "--with-colons", "--list-secret-keys", uid.split()[-1])
        keys[who] = next(x.split(":")[9] for x in out.splitlines() if x.startswith("fpr:"))
    cfg = tmp_path / "config"
    shutil.copytree(FIXTURE_CONFIG, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["identities"]["chief_signing_key"] = keys["chief"]
    yamlio.write(cfg / "config.yaml", doc)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    root = tmp_path / "work"
    root.mkdir()
    gitmod.git("init", "-q", cwd=root)
    gitmod.git("config", "user.signingkey", keys["chief"], cwd=root)
    work(root)
    gitmod.commit(root, gitmod.message("open", None, "project_engineer"), identity=TEAM)
    yield root, keys
    subprocess.run(["gpgconf", "--kill", "gpg-agent"], capture_output=True)


def _approve(root, card="S-01", sign=True, **extra):
    v = load_work(root)
    rec = approval.record(v, card, SUBJECT, "approve", CHIEF, commit=gitmod.head(root), **extra)
    approval.append(v, rec)
    return gitmod.commit(root, gitmod.message("approve", None, "chief_engineer", [card]), identity=CHIEF, sign=sign)


def _problems(root):
    return [r.extra.get("problem") for r in approval_checks.signature(load_work(root))]


def test_signed_approval_valid_unsigned_or_other_key_invalid(gpg_work):
    """new: APPROVAL-02 (architecture §4.6, KM-04): only a commit signed with the chief's key carries an approval"""
    root, keys = gpg_work
    _approve(root, "S-01")
    assert _problems(root) == [None]
    _approve(root, "S-02", sign=False)
    gitmod.git("config", "user.signingkey", keys["other"], cwd=root)
    _approve(root, "S-03")
    v = load_work(root)
    approval.append(v, approval.record(v, "S-04", SUBJECT, "approve", CHIEF))      # not committed
    assert _problems(root) == [None, "unsigned", "other_key", "uncommitted"]
    assert {r.status for r in approval_checks.signature(load_work(root))[1:]} == {"block"}


def test_record_changed_in_unsigned_commit_invalid(gpg_work):
    """new: APPROVAL-02 — a record belongs to the commit that added it; editing it in place (even signed) breaks the
    append-only history and voids every record (KF1-03)"""
    root, _ = gpg_work
    _approve(root)
    recs = yamlio.read(root / "approvals.yaml")
    recs[0]["approved_hash"] = "0" * 64
    yamlio.write(root / "approvals.yaml", recs)
    gitmod.commit(root, gitmod.message("edit", None, "project_engineer"), identity=TEAM)
    assert _problems(root) == ["rewritten"]


def test_identity_other_than_chief_invalid_even_if_signed(gpg_work):
    """new: APPROVAL-02 — the record's identity must be the chief's (name and e-mail)"""
    root, _ = gpg_work
    v = load_work(root)
    rec = {**approval.record(v, "S-01", SUBJECT, "approve", CHIEF), "identity": {"name": "Test Sahte",
                                                                                "email": CHIEF[1]}}
    approval.append(v, rec)
    gitmod.commit(root, gitmod.message("approve", None, "chief_engineer"), identity=CHIEF, sign=True)
    assert _problems(root) == ["identity"]


def test_migrated_approval_needs_signed_migration_approval(gpg_work):
    """new: guide §8 — a migrated approval is unsigned; it counts when its migration_approval commit is the chief's
    signed approval of the migration card MG-01 (V5; KF1-02)"""
    root, _ = gpg_work
    signed = _approve(root, "MG-01")                   # the chief's approval of the migration report
    unsigned = gitmod.commit(root, gitmod.message("x", None, "project_engineer"), identity=TEAM, allow_empty=True)
    v = load_work(root)
    for card, ref in (("S-02", signed), ("S-03", None), ("S-04", unsigned)):
        extra = {"migrated_from_hash": "eski-ozet", **({"migration_approval": ref} if ref else {})}
        approval.append(v, approval.record(v, card, SUBJECT, "approve", CHIEF, **extra))
    gitmod.commit(root, gitmod.message("migrate", None, "system"), identity=TEAM)
    assert _problems(root) == [None, None, "migrated", "migrated"]          # an unsigned team commit adds no MG-01


def test_approvals_outside_git_are_invalid(tmp_path):
    """new: APPROVAL-02 — no repository, no signed commit"""
    v = work(tmp_path)
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF))
    assert _problems(tmp_path) == ["no_repo"]
    (tmp_path / "approvals.yaml").unlink()
    assert [r.msg for r in approval_checks.signature(load_work(tmp_path))] == ["checks.signature.none"]


def test_fingerprint_matching():
    """new: SSH fingerprints match exactly; GPG fingerprints ignore case and spaces and accept a long key id"""
    fpr = "0123456789ABCDEF0123456789ABCDEF01234567"
    assert signature.matches("SHA256:abcDEF", "SHA256:abcDEF")
    assert not signature.matches("SHA256:abcdef", "SHA256:abcDEF")
    assert signature.matches(fpr.lower(), "", fpr) and signature.matches("89ABCDEF01234567", fpr)
    assert not signature.matches("01234567", fpr) and not signature.matches("", fpr)


@pytest.mark.skipif(not shutil.which("ssh-keygen"), reason="ssh-keygen yok: SSH imza yolu bu kapsayıcıda sınanamıyor")
def test_ssh_signed_approval_valid(tmp_path, monkeypatch):
    """new: APPROVAL-02 with an SSH key (fingerprint SHA256:…)"""
    (tmp_path / "gitconfig").write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    _run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", CHIEF[1], "-f", str(tmp_path / "key"))
    fpr = _run("ssh-keygen", "-lf", str(tmp_path / "key.pub")).split()[1]
    cfg = tmp_path / "config"
    shutil.copytree(FIXTURE_CONFIG, cfg)
    doc = yamlio.read(cfg / "config.yaml")
    doc["identities"]["chief_signing_key"] = fpr
    yamlio.write(cfg / "config.yaml", doc)
    monkeypatch.setenv("MEKANIK_CONFIG_DIR", str(cfg))
    root = tmp_path / "work"
    root.mkdir()
    gitmod.git("init", "-q", cwd=root)
    gitmod.git("config", "gpg.format", "ssh", cwd=root)
    gitmod.git("config", "user.signingkey", str(tmp_path / "key.pub"), cwd=root)
    work(root)
    gitmod.commit(root, gitmod.message("open", None, "project_engineer"), identity=TEAM)
    _approve(root)
    assert _problems(root) == [None]
