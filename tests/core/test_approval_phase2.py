# SPDX-License-Identifier: AGPL-3.0-or-later
"""Phase-2 attacks on the approval guarantee (architecture §4.6, APPROVAL-02): the chief's value entry (later.md),
the pinned signing key (§4.6 m.4, KF1-07) and what the migration card's approval covers (§14.3 V5, KF1-18).

As in test_approval_attacks: the agent works with the team identity (or puts the chief's name on a commit), cannot
reach the chief's key and writes files in the work repo, and here in the workshop config too. Each test fails on the
phase-1 code at its first assertion about the attack. GPG keys in a temporary GNUPGHOME (no ssh-keygen here)."""

from __future__ import annotations

import pytest
from test_approval_attacks import SUBJECT, _agent, _chief, _problems, _work
from test_process import _approvals
from test_store import CHIEF, TEAM, _core_only, gpg_keys, shop  # noqa: F401

from mekanik.core import yamlio
from mekanik.core.cards import approval, signature
from mekanik.core.checks.builtin import approval as approval_checks
from mekanik.core.model.work import load_work
from mekanik.core.process import Refused, chief
from mekanik.core.store import git


def _blocks(d) -> set:
    return {(r.ref, r.extra.get("problem")) for r in approval_checks.signature(load_work(d)) if r.status == "block"}


def test_agents_value_with_the_chiefs_identity_blocks(shop):
    """Faz 2: later.md · chief.value — the agent's unsigned params commit with the chief's identity and
    `decided_by: chief_engineer` blocks APPROVAL-02 (phase 1: nothing blocked); the chief's value entry writes a
    `value_change` record in his signed commit and passes; the agent changing that value afterwards blocks again"""
    d = _work(shop)
    doc = yamlio.read(d / "params.yaml")
    doc["blok_en"] |= {"value": 31.0, "decided_by": "chief_engineer"}
    yamlio.write(d / "params.yaml", doc)
    git.commit(d, git.message("Değer girildi: blok_en = 31", None, "chief_engineer"), identity=CHIEF)   # unsigned
    assert _blocks(d) == {("blok_en", "value")}

    out = chief.value(d, "blok_kalinlik", 6.0, "ölçüldü", card_id="S-01")
    rec = _approvals(d)[-1]
    assert (rec["action"], rec["card"], rec["new_value"]) == ("value_change", "S-01", {
        "name": "blok_kalinlik", "quantity": {"value": 6.0, "unit": "mm", "source": "decision",
                                              "decided_by": "chief_engineer"}})
    assert signature.signer(d, out["value_commit"])[0] in signature.GOOD and out["commit"] != out["value_commit"]
    assert _blocks(d) == {("blok_en", "value")}
    assert {(r.ref, r.status) for r in approval_checks.signature(load_work(d))} >= {("blok_kalinlik", "pass"),
                                                                                     ("S-01", "pass")}
    doc = yamlio.read(d / "params.yaml")
    doc["blok_kalinlik"]["value"] = 7.0
    yamlio.write(d / "params.yaml", doc)
    git.commit(d, git.message("toparla", None, "project_engineer"), identity=TEAM)
    assert ("blok_kalinlik", "value") in _blocks(d)
    with pytest.raises(Refused) as e:
        chief.value(d, "blok_kalinlik", 6.5)
    assert e.value.key == "process.value.card"


def test_kf1_07_a_key_changed_in_the_config_is_caught_by_the_pin(shop):
    """Faz 2: KF1-07 — with the chief's key pinned in the organization repo (org.yaml, in a commit signed by it), the
    agent's own key put in the workshop config and approvals signed with it are invalid (phase 1: valid); pinning its
    key afterwards voids every record too"""
    d = _work(shop)
    top = git.toplevel(d)
    yamlio.write(top / "org.yaml", {"chief_signing_key": shop.keys["chief"]})      # signature.pin, by hand
    git.commit(top, git.message("anahtar", None, "chief_engineer"), [str(top / "org.yaml")], CHIEF, sign=True)
    _chief(d, "S-01")
    assert _problems(d) == [None]
    cfg = yamlio.read(shop.config / "config.yaml")
    cfg["identities"]["chief_signing_key"] = shop.keys["other"]              # the agent's key in the config
    yamlio.write(shop.config / "config.yaml", cfg)
    git.git("config", "user.signingkey", shop.keys["other"], cwd=d)
    _chief(d, "S-02")                                                          # signed with the agent's key
    assert _problems(d) == ["key_pin", "key_pin"]
    signature.pin(d, shop.keys["other"], CHIEF)                                # re-pinned with its key
    assert _problems(d) == ["pin_changed", "pin_changed"]


def test_kf1_07_a_removed_or_unsigned_pin_voids_every_record(shop):
    """Faz 2: KF1-07 — the pin removed in a team commit, on any branch, is a changed pin; no pin: phase-1 behaviour"""
    d = _work(shop)
    _chief(d, "S-01")
    assert _problems(d) == [None] and signature.pinned(d, shop.keys["chief"]) is None
    signature.pin(d, shop.keys["chief"], CHIEF)
    assert _problems(d) == [None]
    top = git.toplevel(d)
    git.git("checkout", "-q", "-b", "yan", cwd=top)
    git.git("rm", "-q", "org.yaml", cwd=top)
    git.commit(top, git.message("toparla", None, "project_engineer"), identity=TEAM)
    git.git("checkout", "-q", "-", cwd=top)
    assert _problems(d) == ["pin_changed"]


def test_kf1_18_mg01_covers_only_what_its_subject_lists(shop):
    """Faz 2: §14.3 V5, KF1-18 — the chief's signed MG-01 approval covers the migrated records and passed gates its
    subject lists (phase 1: neither); a migrated record the agent adds afterwards pointing at that approval (phase 1
    accepted it) and a gate it marks passed and migrated are not covered; an edited subject covers nothing"""
    d = _work(shop)
    v = load_work(d)
    approval.append(v, approval.record(v, "S-01", SUBJECT, "approve", CHIEF, migrated_from_hash="eski"))
    doc = yamlio.read(d / "work.yaml")
    doc["process"]["gate_status"]["G0"] |= {"status": "done", "migrated": True}
    yamlio.write(d / "work.yaml", doc)
    subj = {"refs": [{"kind": "file", "id": "migration"}], "gates": ["G0"], "approvals": [approval.digest(
        v.approvals[0])]}
    card = {"kind": "card", "schema_version": "1.0", "id": "MG-01", "work": v.code, "type": "migration_gap",
            "level": "hold", "title": "taşıma", "triggers": ["migration_gap"], "subject": subj, "status": "open"}
    yamlio.write(d / "cards" / "MG-01.yaml", card)
    git.commit(d, git.message("taşıma", None, "project_engineer", ["MG-01"]), identity=TEAM)
    assert _blocks(d) == {("S-01", "migrated"), ("O-G0", "unapproved")}
    v = load_work(d)
    approval.append(v, approval.record(v, "MG-01", subj, "approve", CHIEF, commit=git.head(d)))
    mg = git.commit(d, git.message("onay", None, "chief_engineer", ["MG-01"]), identity=CHIEF, sign=True)
    assert _blocks(d) == set()

    _agent(d, "S-02", migrated_from_hash="eski", migration_approval=mg[:12])
    doc["process"]["gate_status"]["G1"] = {"status": "done", "migrated": True}
    yamlio.write(d / "work.yaml", doc)
    git.commit(d, git.message("toparla", None, "project_engineer"), identity=TEAM)
    assert _blocks(d) == {("S-02", "migrated"), ("O-G1", "unapproved")}
    yamlio.write(d / "cards" / "MG-01.yaml", card | {"subject": subj | {"gates": ["G0", "G1"]}})
    git.commit(d, git.message("toparla", None, "project_engineer"), identity=TEAM)
    assert {("S-01", "migrated"), ("O-G0", "unapproved"), ("O-G1", "unapproved")} <= _blocks(d)
