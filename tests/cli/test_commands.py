# SPDX-License-Identifier: AGPL-3.0-or-later
"""Smoke test of every phase-1 `mekanik` command (criterion 1.1; architecture §4.11; Ek B §14 madde 12: exit code and
output form). Each docstring names the old `surec` command it replaces; the two old CLI tests are carried as `old:`.
Output is compared with catalog text or structured data, never with literal Turkish."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mekanik.cli import main as cli_main
from mekanik.core import yamlio
from mekanik.core.checks.regress import Subcase
from mekanik.core.i18n import catalogs, t
from mekanik.core.store import git

MEKANIK = Path(sys.executable).with_name("mekanik")
PARAMS = {"blok_en": {"value": 20.0, "unit": "mm", "source": "decision"},
          "blok_kalinlik": {"value": 5.0, "unit": "mm", "source": "decision"}}
REQUIREMENTS = [{"id": "R-01", "text": "Blok yazıcıya sığar", "kind": "mandatory", "origin": {"type": "chief_engineer"},
                 "criterion": {"measure": "block_edge", "operator": "<=", "target": {
                     "value": 256.0, "unit": "mm", "source": "decision", "decided_by": "chief_engineer"}},
                 "verification": {"method": "check"}, "status": "approved"}]
RISK_C = [{"question_id": q, "answer": a} for q, a in (("harm", False), ("cost", False), ("regulation", False),
                                                       ("variant", True))]
PHASE1 = {"doctor", "regress", "check", "work new", "work open", "work close", "work attach", "work archive", "step",
          "stage finish", "release request", "gate pass", "approve", "reply", "pending", "decide", "agent hook",
          "agent status", "watch", "review prompt", "review record", "review close", "pulse", "migrate surec-config",
          "migrate surec-work", "pkg list", "verify"}


def _approvals(d: Path) -> list:
    return yamlio.read(d / "approvals.yaml", []) or []


def _subagent(cli, monkeypatch, code: str, text: str) -> None:
    """The plugin's SubagentStop hook catches the quality-engineer subagent's last output (KF1-16)."""
    payload = {"hook_event_name": "SubagentStop", "agent_type": "mekanik:quality-engineer",
               "last_assistant_message": text}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert cli("agent", "hook", "SubagentStop", "--work", code)[0] == 0


def _g0(cli, work, monkeypatch) -> tuple[str, Path]:
    """Old _g0_iste: risk answers, a requirement, sourced params, a step, the quality review, the G0 request (O-G0)."""
    code, d = work
    yamlio.write(d / "work.yaml", {**yamlio.read(d / "work.yaml"), "risk_answers": RISK_C})
    yamlio.write(d / "requirements.yaml", {**yamlio.read(d / "requirements.yaml"), "items": REQUIREMENTS})
    yamlio.write(d / "params.yaml", PARAMS)
    assert cli("step", "hazırlık", "--role", "project_engineer", "--work", code)[0] == 0
    rc, out, _ = cli("review", "prompt", "--work", code)
    assert rc == 0 and code in out
    _subagent(cli, monkeypatch, code, "Bulgu yok.")
    monkeypatch.setattr(sys, "stdin", io.StringIO("Bulgu yok.\n"))
    assert cli("review", "record", "--work", code)[0] == 0
    rc, out, _ = cli("stage", "finish", "G0", "--work", code)
    assert rc == 0 and out.strip().endswith(t("cli.stage_finish", gate="G0"))
    return code, d


def test_every_phase1_command_is_registered():
    """new: architecture §4.11 — the phase-1 rows: 21 old commands (gecis-plani not carried, panel in phase 2) and
    the new gate pass, verify, migrate, pkg list"""
    paths = {p for p, _, _ in cli_main.COMMANDS}
    assert paths >= PHASE1                                  # phase 2's: test_phase2_commands.py
    for p in PHASE1:
        with pytest.raises(SystemExit) as e:
            cli_main.main([*p.split(), "--help"])
        assert e.value.code == 0


def test_doctor(cli):
    """new: Ek B §14 madde 12 — old surec doktor --json: every group reported; red (exit 1) only on an error"""
    rc, out, _ = cli("doctor", "--json")
    found = json.loads(out)
    assert {f["group"] for f in found} == {"tool", "identity", "disk", "package", "smoke"}
    assert rc == (1 if any(f["status"] == "error" for f in found) else 0)
    assert next(f for f in found if f["name"] == "signing_key")["status"] in ("warn", "pending", "ok", "error")
    rc, out, _ = cli("doctor")
    assert t("cli.doctor.status.ok") in out


def test_regress(cli, monkeypatch):
    """new: Ek B §14 madde 12 — old surec regresyon"""
    import mekanik.core.checks.regress as regress

    subs = [Subcase("S-001", "1", "a", True), Subcase("S-001", "2", "b", False, ["x"])]
    monkeypatch.setattr(regress, "run_all", lambda: subs)
    rc, out, _ = cli("regress")
    assert rc == 1 and t("cli.regress.case", case="S-001", ok=1, n=2) in out
    monkeypatch.setattr(regress, "run_all", lambda: subs[:1])
    assert cli("regress")[0] == 0


def test_check_writes_nothing(cli, work, env):
    """new: Ek B §14 madde 12 — old surec kontrol [--json]; the tree and the cache stay clean (E-40, §4.11)"""
    code, d = work
    rc, out, _ = cli("check", code, "--json")
    data = json.loads(out)
    assert data["work"] == code and data["stage"] == "G0" and set(data["summary"]) == {"block", "warn", "pass"}
    assert rc == (1 if data["summary"]["block"] else 0)
    rc, out, _ = cli("check", str(d))
    assert out.startswith(t("cli.check.head", code=code, stage="G0", profile="—", **data["summary"]).splitlines()[0])
    assert not git.git("status", "--porcelain", cwd=d) and not (env / "xdg_cache_home").exists()


def test_work_new_open_close_archive(cli, work, shop, spy):
    """new: Ek B §14 madde 12 — old surec yeni-calisma, ac, kapat, arsivle"""
    import mekanik.core.store.works as works

    code, d = work
    assert git.branch(d) == f"{code}/work/general"
    opened = spy(works, "open_work")
    rc, out, _ = cli("work", "open", code)
    assert rc == 0 and out.strip() == t("cli.work.open", **opened[0]) and opened[0]["command"].endswith("claude")
    rc, out, _ = cli("work", "close", code)
    assert rc == 0 and out.strip() == t("cli.work.close", code=code, n=0)
    rc, out, _ = cli("work", "archive", code, "--reason", "sınama")
    assert rc == 0 and json.loads(out)["tag"] == f"{code}-archive"
    rc, _, err = cli("work", "archive", code, "--reason", "yine")
    assert rc == 2 and err.strip() == t("cli.error", error=t("store.archive.already", code=code))


def test_attach_goes_to_the_right_session(cli, shop, monkeypatch):
    """old: test_akis::gec_dogru_oturuma_baglanir"""
    import mekanik.core.store.works as works

    assert cli("work", "attach", "TST-SYN-01")[0] == 2           # no such work yet
    code = works.new_work("TST", "SYN", "Geç", "C")
    calls = {}
    monkeypatch.setattr(works.os, "execvp", lambda p, a: calls.setdefault("exec", a))
    monkeypatch.delenv("TMUX", raising=False)
    assert cli("work", "attach", code)[0] == 0
    assert calls["exec"][-2:] == ["-t", code]
    monkeypatch.setenv("TMUX", "x")
    real = works.subprocess.run
    monkeypatch.setattr(works.subprocess, "run",
                        lambda a, **k: calls.setdefault("run", a) if "switch-client" in a else real(a, **k))
    assert cli("work", "attach", code)[0] == 0
    assert calls["run"][-3:] == ["switch-client", "-t", code]


def test_step(cli, work, spy):
    """new: Ek B §14 madde 12 — old surec adim; --next writes the next job into work.yaml (old adim --sonraki)"""
    import mekanik.core.process.step as stepmod

    code, d = work
    steps = spy(stepmod, "step")
    rc, out, _ = cli("step", "ilk adım", "--role", "design_engineer", "--text", "açıklama", "--next", "G0 kartı",
                     "--work", code)
    sha, s = git.git("rev-parse", "HEAD~1", cwd=d), steps[0]
    assert rc == 0 and s["commit"] == sha and out.strip() == t("cli.step", sha=sha[:7], cards="—", **s["summary"])
    assert git.trailers(git.git("log", "-1", "--format=%B", sha, cwd=d))["Role"] == "design_engineer"
    nxt = yamlio.load(git.git("show", f"{sha}:./work.yaml", cwd=d))["next_step"]
    assert (nxt["text"], nxt["role"]) == ("G0 kartı", "design_engineer") and not git.git("status", "--porcelain", cwd=d)
    with pytest.raises(SystemExit):                                # the chief's role is not a team role
        cli_main.main(["step", "x", "--role", "chief_engineer"])


def test_cli_approval_needs_a_terminal(work, cli, monkeypatch):
    """old: test_akis::cli_onay_terminal_ister"""
    code, d = _g0(cli, work, monkeypatch)
    env = {**os.environ, "PATH": f"{MEKANIK.parent}:{os.environ['PATH']}", "MEKANIK_LANG": "tr"}
    for args in (["approve", "O-G0", "--action", "approve"], ["gate", "pass", "G0"]):
        p = subprocess.run([str(MEKANIK), *args, "--work", code], cwd=d, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, env=env)          # another process: its language pinned here
        assert p.returncode == 4 and p.stderr.strip() == catalogs()["tr"]["cli.approve.tty"]
    assert _approvals(d) == []


def test_stage_finish_comment_pending_reply_gate_pass_verify(cli, work, tty, shop, monkeypatch, spy):
    """new: Ek B §14 madde 12 — old surec asama-bitir, onay (yorum, onay), bekleyenler [--kanca] (hook JSON, data
    gate), yanitla [--commit]; new: gate pass, verify (both show the pinned signing key, KF1-07)"""
    import mekanik.core.process.chief as chief

    code, d = _g0(cli, work, monkeypatch)
    waiting, replies = spy(chief, "pending"), spy(chief, "reply")
    with tty("yanlış"):
        assert cli("approve", "O-G0", "--action", "comment", "--note", "R-01 ekle", "--work", code)[0] == 4
    with tty("O-G0"):
        rc, out, _ = cli("approve", "O-G0", "--action", "comment", "--note", "R-01 ekle", "--work", code)
    assert rc == 0 and json.loads(out)["action"] == "comment"
    rc, out, _ = cli("pending", "--work", code)
    assert rc == 0 and [(p["card"], p["text"]) for p in waiting[-1]] == [("O-G0", "R-01 ekle")] and out.strip()
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"hook_event_name": "UserPromptSubmit"})))
    rc, out, _ = cli("pending", "--hook", "--work", code)
    ctx = json.loads(out)["hookSpecificOutput"]
    assert ctx["hookEventName"] == "UserPromptSubmit" and "R-01 ekle" in ctx["additionalContext"]
    doc = yamlio.read(shop.config / "config.yaml")
    doc["organizations"][0]["data_transfer"]["model_provider_allowed"] = False
    yamlio.write(shop.config / "config.yaml", doc)
    assert cli("pending", "--hook", "--work", code) == (0, "", ""), "data gate: nothing reaches the model"
    doc["organizations"][0]["data_transfer"]["model_provider_allowed"] = True
    yamlio.write(shop.config / "config.yaml", doc)
    step = git.git("rev-parse", "HEAD~1", cwd=d)
    rc, out, _ = cli("reply", "O-G0", "--text", "eklendi", "--commit", step[:7], "--work", code)
    r = replies[0]
    assert rc == 0 and out.strip() == t("cli.reply", card="O-G0", at=r["comment_at"]) and r["commit"] == step
    assert yamlio.read(d / "replies.yaml")[-1]["commit"] == step
    assert cli("pending", "--work", code)[1].strip() == t("cli.pending.none")
    with tty("O-G0"):
        rc, out, err = cli("gate", "pass", "G0", "--work", code)
    assert rc == 0 and json.loads(out)["gate"]["tag"] == f"{code}-G0", err
    assert t("cli.signing_key", fp=shop.key) in err.splitlines()
    rc, out, _ = cli("verify", "--work", code)
    assert rc == 0 and out.strip().endswith(t("cli.verify.summary", n=2, bad=0))
    assert t("cli.signing_key", fp=shop.key) in out.splitlines()


def test_pending_hook_silent_outside_a_work(cli, monkeypatch, tmp_path):
    """new: Ek B §14 madde 12 — old surec bekleyenler --kanca: a hook never stops the session; outside a work it
    prints nothing"""
    monkeypatch.chdir(tmp_path)
    assert cli("pending", "--hook") == (0, "", "")


def test_undo_needs_a_reason(cli, work, tty):
    """new: Ek B §14 madde 12 — old surec onay --karar geri-al (nedeni --not ile)"""
    code, _ = work
    with tty("O-G0"):
        rc, _, err = cli("approve", "O-G0", "--action", "undo", "--work", code)
    assert rc == 4 and err.splitlines()[-1] == t("cli.approve.undo_note")


def test_release_request(cli, work, monkeypatch):
    """new: Ek B §14 madde 12 — old surec baski"""
    import mekanik.core.process.release as release

    code, _ = work
    rc, _, err = cli("release", "request", "--work", code)
    assert rc == 2 and err.strip() == t("cli.error", error=t("process.release.no_model"))
    monkeypatch.setattr(release, "release_request", lambda root, basis: {"no": "01", "folder": "/x", "basis": basis})
    assert cli("release", "request", "--work", code)[1].strip() == t("cli.release", no="01", folder="/x")


def test_decide(cli, work, tmp_path, monkeypatch):
    """new: Ek B §14 madde 12 — old surec karar (--secenek, --tanim, --dalsiz, --tur kavram). The card needs model
    figures (OCCT, tests/flow), so the decision module is stood in for and only the CLI's mapping is checked"""
    import mekanik.core.decisions as decisions

    code, d = work
    spec = tmp_path / "k01.yaml"
    yamlio.write(spec, {"question": "Hangisi?", "explain": "sınama", "proposal": "a", "options": {
        "a": {"title": "birinci", "values": {"blok_en": 20.0}}, "b": {"title": "ikinci"}}})
    calls = []

    def fake(root, did, title, options, rationale, **kw):
        calls.append((root, did, title, options, rationale, kw))
        return {"decision": {"options": [{"id": k, "branch": kw["branched"] and f"{code}/decision/{did}-{k}"}
                                         for k in options]}}
    monkeypatch.setattr(decisions, "open_decision", fake)
    rc, out, _ = cli("decide", "K-01", "--title", "Yön", "--option", "a:birinci", "--option", "b:ikinci",
                     "--rationale", "sınama", "--dependent", "blok", "--concept", "--work", code)
    assert rc == 0 and t("cli.decide.branch", id="a", branch=f"{code}/decision/K-01-a") in out
    assert calls[0][1:5] == ("K-01", "Yön", {"a": "birinci", "b": "ikinci"}, "sınama") and calls[0][0] == d
    assert calls[0][5] == {"dependents": ["blok"], "branched": True, "concept": True}
    rc, out, _ = cli("decide", "K-02", "--title", "Yön", "--rationale", "x", "--definition", str(spec), "--plain",
                     "--work", code)
    assert rc == 0 and t("cli.decide.branch", id="b", branch=t("cli.decide.no_branch")) in out
    assert calls[1][3]["a"]["values"] == {"blok_en": 20.0} and calls[1][5]["question"] == "Hangisi?"
    assert calls[1][5]["branched"] is False
    rc, _, err = cli("decide", "K-03", "--title", "Yön", "--rationale", "x", "--work", code)
    assert rc == 2 and err.strip() == t("cli.error", error=t("cli.decide.no_option"))


def test_agent_hook_and_status(cli, monkeypatch, work):
    """new: Ek B §14 madde 12 — old surec durum-yaz, durum"""
    from mekanik.agent import hook

    code, d = work
    payload = {"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(d), "tool_name": "Bash",
               "tool_input": {"command": "mekanik approve O-G0 --action approve"}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    rc, out, _ = cli("agent", "hook", "PreToolUse")
    assert rc == 0 and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    rc, out, _ = cli("agent", "status")
    (at, r), = hook.runs()
    assert rc == 0 and r["work"] == code and r["status"] == "running"
    assert out.strip() == t("cli.status", work=code, at=at, id=r["id"], status=t("cli.run_status.running"))


def test_watch_outside_a_work_exits_at_once(cli, monkeypatch, tmp_path):
    """new: Ek B §14 madde 12 — old surec gozcu (the monitor binding is phase 2): outside a work it is silent"""
    monkeypatch.chdir(tmp_path)
    assert cli("watch") == (0, "", "")


def test_pulse(cli, env, spy):
    """new: Ek B §14 madde 12 — old surec nabiz --is / --durdu"""
    from mekanik.agent import pulse

    beats = spy(pulse, "beat")
    rc, out, _ = cli("pulse", "TST-SYN-01", "--doing", "model")
    v = beats[-1]
    assert rc == 0 and (v["work"], v["status"], v["doing"]) == ("TST-SYN-01", "working", "model")
    assert out.strip() == t("cli.pulse", work=v["work"], status=t("agent.liveness.working"), doing="model", at=v["at"])
    rc, out, _ = cli("pulse", "TST-SYN-01", "--stopped", "K-02 bekliyor")
    assert beats[-1]["status"] == "stopped" and t("agent.liveness.stopped") in out
    rec = json.loads((env / "xdg_state_home" / "mekanik" / "pulse" / "TST-SYN-01.json").read_text())
    assert rec["status"] == "stopped" and rec["doing"] == "K-02 bekliyor"


def test_review_prompt_record_close(cli, work, monkeypatch, spy):
    """new: Ek B §14 madde 12 — old surec kalite, kalite-kapat"""
    from mekanik.core import quality

    code, d = work
    records = spy(quality, "record")
    rc, out, _ = cli("review", "prompt", "--subject", "G0", "--work", code)
    assert rc == 0 and code in out
    _subagent(cli, monkeypatch, code, "[YÜKSEK] params.yaml:1 — birim — ilke — kanıt")
    monkeypatch.setattr(sys, "stdin", io.StringIO("[YÜKSEK] params.yaml:1 — birim — ilke — kanıt\n"))
    rc, out, _ = cli("review", "record", "--subject", "G0", "--work", code)
    name = records[0][0].name
    assert rc == 0 and out.splitlines()[-1] == t("cli.review.recorded", name=name, n=1, high=1)
    rc, _, err = cli("review", "close", name, "1", "--note", "düzeltildi", "--work", code)
    assert rc == 2 and err.strip() == t("cli.error", error=t("quality.close_regression"))
    rc, out, _ = cli("review", "close", name, "1", "--note", "düzeltildi", "--no-case", "biçim", "--work", code)
    assert rc == 0 and out.strip() == t("cli.review.closed", no=1, note="düzeltildi")


def test_migrate_dry_run(cli, tmp_path):
    """new: architecture §14.2 — mekanik migrate surec-config / surec-work (dry run; --apply in phase 2's tests)"""
    old = Path(__file__).resolve().parents[1] / "fixtures" / "surec"
    rc, out, _ = cli("migrate", "surec-config", "--from", str(old), "--out", str(tmp_path / "cfg"))
    assert rc == 0 and out.splitlines()[0] == t("cli.migrate.row", v="V1", status=t("migrate.status.pass"), detail="—")
    assert (tmp_path / "cfg" / "orgs" / "TST.yaml").exists()
    rc, out, _ = cli("migrate", "surec-work", str(old / "S-001"), "--out", str(tmp_path / "w"))
    assert rc == 0 and (tmp_path / "w" / "work.yaml").exists() and t("cli.migrate.no_snapshot") in out


@pytest.mark.parametrize("case", ["S-001", "H-001"])
def test_migrate_with_snapshot_passes_v1_to_v8(cli, tmp_path, case):
    """new: criterion 1.7 (KF1-10) — `mekanik migrate surec-work --snapshot` with every package registered: V1–V8
    pass with the migration package's own list of intentional V4 changes (no test data injected), exit 0"""
    pytest.importorskip("cadquery")
    from mekanik.plugins import reset_registry

    reset_registry()                                  # the entry-point packages (mech, print3d), not the core alone
    root = Path(__file__).resolve().parents[1]
    rc, out, _ = cli("migrate", "surec-work", str(root / "fixtures" / "surec" / case), "--out", str(tmp_path / case),
                     "--snapshot", str(root / "migrate" / "data" / "old" / f"{case}.json"))
    rows = out.splitlines()[:8]
    assert rc == 0 and rows == [t("cli.migrate.row", v=f"V{i}", status=t("migrate.status.pass"), detail="—")
                                for i in range(1, 9)], out


def test_pkg_list(cli):
    """new: architecture §4.11 — mekanik pkg list"""
    from mekanik.core.builtin import SPEC

    rc, out, _ = cli("pkg", "list")
    assert rc == 0 and out.strip() == t("cli.pkg", id="core", version=SPEC.version, checks=len(SPEC.checks))


def test_verify_without_approvals(cli, work):
    """new: architecture §4.6 — mekanik verify (APPROVAL-02); no record, nothing invalid"""
    code, _ = work
    rc, out, _ = cli("verify", "--work", code)
    assert rc == 0 and out.strip().endswith(t("cli.verify.summary", n=0, bad=0))
