# SPDX-License-Identifier: AGPL-3.0-or-later
"""Attacks on the approval guarantee (architecture §4.6, APPROVAL-02), from the phase-1 exit review (KF1-01…05).

Each test is the review's proof of concept turned into a regression test: the agent works with the team identity,
cannot reach the chief's key and only writes files in the work repo (its .git included). GPG keys in a temporary
GNUPGHOME (no ssh-keygen in this container)."""

from __future__ import annotations

import os
import subprocess

import pytest
from test_process import _approvals, _g0
from test_store import CHIEF, TEAM, _core_only, gpg_keys, new, prepare, review, shop  # noqa: F401

from mekanik.core import yamlio
from mekanik.core.cards import approval
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, chief, gates
from mekanik.core.process import step as stepmod
from mekanik.core.store import git

SUBJECT = {"params": ["blok_en"]}


def _work(shop) -> object:
    code, d = new()
    prepare(d)
    git.commit(d, git.message("hazırlık", None, "project_engineer"), identity=TEAM)
    return d


def _chief(d, card="S-01", action="approve", **extra) -> str:
    """The chief's record in his signed commit (Card trailer), as chief.approve writes it."""
    v = load_work(d)
    approval.append(v, approval.record(v, card, SUBJECT, action, CHIEF, commit=git.head(d), reason="x", **extra))
    return git.commit(d, git.message(action, None, "chief_engineer", [card]), identity=CHIEF, sign=True)


def _agent(d, card="S-02", **extra) -> str:
    """A record with the chief's name and e-mail, committed by the agent with the team identity (no key)."""
    v = load_work(d)
    approval.append(v, approval.record(v, card, SUBJECT, "approve", CHIEF, commit=git.head(d), **extra))
    return git.commit(d, git.message("toparla", None, "project_engineer"), identity=TEAM)


def _problems(d) -> list:
    return [r.extra.get("problem") for r in approval_checks.signature(load_work(d))]


def test_kf1_01_repo_gpg_program_is_not_trusted(shop, tmp_path, monkeypatch):
    """new: KF1-01 — a gpg.program in the work repo's config that reports every signature good (and 'signs' without
    a key) does not make an approval valid; verification runs the system gpg, never the repo's or PATH's program"""
    d, fpr = _work(shop), shop.keys["chief"]
    fake = tmp_path / "bin" / "gpg"
    fake.parent.mkdir()
    fake.write_text(f"""#!/bin/sh
for a in "$@"; do case "$a" in --verify) cat >/dev/null
  echo "[GNUPG:] NEWSIG"; echo "[GNUPG:] GOODSIG {fpr[-16:]} T"
  echo "[GNUPG:] VALIDSIG {fpr} 2026-11-06 0 0 4 0 22 10 00 {fpr}"; echo "[GNUPG:] TRUST_ULTIMATE 0 pgp"
  exit 0;; esac; done
cat >/dev/null; printf '\\n[GNUPG:] SIG_CREATED D 22 10 00 0 %s\\n' "{fpr}" >&2
printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nZmFrZQ==\\n-----END PGP SIGNATURE-----\\n'
""")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake.parent}:{os.environ['PATH']}")      # first on PATH as well
    git.git("config", "gpg.program", str(fake), cwd=d)                        # the agent's one line in .git/config
    v = load_work(d)
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF, commit=git.head(d)))
    git.git("add", "-A", cwd=d)
    subprocess.run(["git", "commit", "-q", "-S", "-m", "onay"], cwd=d, check=True, capture_output=True,
                   env={**os.environ, **git.identity_env(*CHIEF)})           # plain git: the repo's program signs
    assert _problems(d) not in ([None], [])
    assert {r.status for r in approval_checks.signature(load_work(d))} == {"block"}


def test_kf1_01_missing_program_never_passes(shop, monkeypatch):
    """new: KF1-01 — when the trusted program cannot be found the signature counts as unsigned, never as good"""
    d = _work(shop)
    _chief(d)
    assert _problems(d) == [None]
    monkeypatch.setattr(git, "SAFE", [x.replace("gpg.program=", "gpg.program=/nonexistent") for x in git.SAFE])
    assert _problems(d) == ["unsigned"]


def test_kf1_02_migrated_approval_needs_the_chiefs_migration_card_approval(shop):
    """new: KF1-02 — a migrated record counts only with a migration_approval commit that is signed by the chief,
    carries `Card: MG-01` and adds the chief's approve record of MG-01; any other signed commit does not do"""
    d = _work(shop)
    other = _chief(d, "S-01")                                   # the chief's real approval of some other card
    comment = _chief(d, "MG-01", "comment")                     # signed, Card: MG-01, but not an approval
    _agent(d, "S-02", migrated_from_hash="eski", migration_approval=other[:12])
    _agent(d, "S-03", migrated_from_hash="eski", migration_approval=comment[:12])
    assert _problems(d) == [None, None, "migrated", "migrated"]
    mg = _chief(d, "MG-01")
    _agent(d, "S-04", migrated_from_hash="eski", migration_approval=mg[:12])
    assert _problems(d)[-2:] == [None, None]


def test_kf1_03_deleting_a_signed_record_voids_every_approval(shop):
    """new: KF1-03 — approvals.yaml is append-only against its history: the chief's signed rejection dropped in an
    unsigned commit (or only in the working copy) makes every record invalid (`rewritten`), not the approval valid"""
    d = _work(shop)
    _chief(d, "S-01")
    _chief(d, "S-01", "reject")
    assert approval.state(load_work(d), "S-01", SUBJECT) == "rejected" and _problems(d) == [None, None]
    recs = yamlio.read(d / "approvals.yaml")
    yamlio.write(d / "approvals.yaml", recs[:-1])
    assert _problems(d) == ["rewritten"]                                       # working copy only
    git.commit(d, git.message("toparla", None, "project_engineer"), identity=TEAM)
    assert _problems(d) == ["rewritten"]
    assert {r.status for r in approval_checks.signature(load_work(d))} == {"block"}


def test_kf1_04_repo_hook_cannot_slip_a_record_into_the_chiefs_commit(shop):
    """new: KF1-04 — mekanik runs git without the repo's hooks: a pre-commit hook planted by the agent does not add
    a forged record to the chief's next signed commit"""
    d = _work(shop)
    v = load_work(d)
    forged = yamlio.dump([approval.record(v, "S-09", SUBJECT, "approve", CHIEF, commit=git.head(d))])
    hooks = git.toplevel(d) / git.git("rev-parse", "--git-common-dir", cwd=git.toplevel(d)) / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text(f"#!/bin/sh\ncat >> '{d}/approvals.yaml' <<'EOF'\n{forged}EOF\ngit add -A\n")
    (hooks / "pre-commit").chmod(0o755)
    _chief(d, "S-01")
    assert [r["card"] for r in _approvals(d)] == ["S-01"] and _problems(d) == [None]


def test_kf1_04_chiefs_commit_holds_only_what_was_written(shop, monkeypatch):
    """new: KF1-04 — after the chief's signed commit its paths must be the written ones and approvals.yaml exactly
    the written records; a staged file of the agent or an extra record undoes the commit and refuses the approval"""
    code, d = _g0(shop)
    head, before = git.head(d), _approvals(d)
    top = git.toplevel(d)
    (top / "x.txt").write_text("ajan\n")                       # outside the work folder: not 'dirty' for the chief
    git.git("add", "x.txt", cwd=top)
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "process.approve.tampered" and git.head(d) == head and _approvals(d) == before
    git.git("rm", "-q", "--cached", "--ignore-unmatch", "x.txt", cwd=top)
    real = stepmod.git.commit

    def commit(cwd, msg, paths=None, identity=None, allow_empty=False, sign=False):
        if sign:                                                 # stands for anything that adds to the commit
            v = load_work(d)
            yamlio.write(d / "approvals.yaml", [*_approvals(d), approval.record(v, "S-09", SUBJECT, "approve", CHIEF)])
        return real(cwd, msg, paths, identity, allow_empty, sign)
    monkeypatch.setattr(stepmod.git, "commit", commit)
    with pytest.raises(Refused) as e:
        chief.approve(d, "O-G0")
    assert e.value.key == "process.approve.tampered" and git.head(d) == head and _approvals(d) == before
    assert f"{code}-G0" not in git.git("tag", cwd=d).split()


@pytest.mark.parametrize("card", ["O-G0", "B-01"])
def test_kf1_05_gate_and_release_refused_while_a_signature_is_invalid(shop, monkeypatch, card):
    """new: KF1-05 — §4.6 "kapı ve baskı geçmez": with one APPROVAL-02 block a gate does not pass (in every stage,
    G0 too) and a release is not cut; the chief's rejection still works"""
    code, d = new()
    prepare(d)
    stepmod.step(d, "hazırlık", "project_engineer")
    _agent(d, "S-07")                                            # unsigned record with the chief's name
    review(d)
    gates.stage_finish(d, "G0")
    if card.startswith("B-"):                                    # a release card (the real one needs a model, OCCT)
        real = chief.evaluate
        monkeypatch.setattr(chief, "evaluate", lambda root: (lambda v, m, r, c: (v, m, r, [*c, {
            "id": card, "type": "release", "status": "open", "subject": {"release": "01"}}]))(*real(root)))
    n = len(_approvals(d))
    with pytest.raises(Refused) as e:
        chief.approve(d, card)
    assert e.value.key == "process.approve.signature" and e.value.data["n"] == 1 and len(_approvals(d)) == n
    assert f"{code}-G0" not in git.git("tag", cwd=d).split()
    if card == "O-G0":
        assert chief.approve(d, card, "reject", reason="imza")["action"] == "reject"


def test_qe2_passed_gate_or_cut_release_without_a_signed_approval_blocks(shop):
    """new: QE2 — gate_status done and an out/<code>-release-<no> folder written by the agent, with no signed approval
    of O-G0 / B-01, are each an APPROVAL-02 block; the chief's signed approval of the card clears it."""
    d = _work(shop)
    doc = yamlio.read(d / "work.yaml")
    doc["process"]["gate_status"]["G0"]["status"] = "done"
    yamlio.write(d / "work.yaml", doc)
    code = doc["code"]
    (d / "out" / f"{code}-release-01").mkdir(parents=True)
    git.commit(d, git.message("kapı geçti", None, "project_engineer"), identity=TEAM)
    assert {(r.ref, r.extra.get("problem")) for r in approval_checks.signature(load_work(d))} >= {
        ("O-G0", "unapproved"), ("B-01", "unapproved")}
    _chief(d, "O-G0")
    _chief(d, "B-01")
    assert "unapproved" not in _problems(d)
