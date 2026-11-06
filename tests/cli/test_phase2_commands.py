# SPDX-License-Identifier: AGPL-3.0-or-later
"""Smoke test of the phase-2 `mekanik` commands (architecture §4.11, wave 2.2): exit code and output form, compared
with catalog text or structured data, never with literal Turkish. The chief's commands refuse without a terminal;
the core functions they call have their own tests (tests/core, tests/flow), so where one needs a long set-up (a
provisional decision with figures, a passed G2) it is stood in for and only the CLI's mapping is checked."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from test_commands import PARAMS, PHASE1, _approvals

from mekanik.cli import main as cli_main
from mekanik.core import clock, yamlio
from mekanik.core.i18n import t
from mekanik.core.store import git

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))
from intake_data import case, expected, review, specs  # noqa: E402

PHASE2 = {"gate back", "value", "object", "respond", "summary", "intake types", "intake choose", "intake plan",
          "intake ask", "intake answer", "intake summarize", "intake submit", "intake status", "stdmap build",
          "stdmap add", "stdmap tick", "stdmap rows", "panel", "agent send", "agent stop", "mcp"}


def _ready(cli, work) -> tuple[str, Path]:
    code, d = work
    yamlio.write(d / "params.yaml", PARAMS)
    assert cli("step", "hazırlık", "--role", "project_engineer", "--work", code)[0] == 0
    return code, d


def _results(cli, code: str, rule: str) -> list[dict]:
    return [r for r in json.loads(cli("check", code, "--json")[1])["results"] if r["rule"] == rule]


def test_every_command_is_registered_with_help():
    """2.2: architecture §4.11 — phase 1's commands and the phase-2 rows (object, gate back, intake, stdmap, panel,
    agent send/stop) with respond, value, summary and the MCP server; every one has --help"""
    paths = {p for p, _, _ in cli_main.COMMANDS}
    assert paths == PHASE1 | PHASE2
    for p in PHASE2 | {"verify", "release request", "migrate surec-work"}:
        with pytest.raises(SystemExit) as e:
            cli_main.main([*p.split(), "--help"])
        assert e.value.code == 0


def test_chief_commands_refuse_without_a_terminal(cli, work):
    """2.2: architecture §4.6 — object, gate back, value and verify --pin are the chief's (TTY; the agent's Bash has
    none): refused with exit 4, nothing recorded"""
    code, d = work
    for args, command in ((["object", "K-01", "--reason", "x"], "object"), (["gate", "back", "G2", "--reason", "x"],
                                                                            "gate back"),
                          (["value", "S-01", "blok_en", "22"], "value"), (["verify", "--pin"], "verify --pin")):
        rc, out, err = cli(*args, "--work", code)
        assert (rc, out, err.strip()) == (4, "", t("cli.tty", command=command))
    assert _approvals(d) == [] and not (d / "org.yaml").exists() and not git.git("status", "--porcelain", cwd=d)


def test_object_respond_and_gate_back_map_to_the_policy(cli, work, tty, monkeypatch):
    """2.2: D3, Ö-17 — `object <K-nn> --reason` (TTY), `respond <K-nn> --text [--keep] [--option]` (team) and
    `gate back <G> --reason` (TTY) call lifecycle.object_decision, lifecycle.respond and gates.gate_back"""
    from mekanik.core.policy import lifecycle
    from mekanik.core.process import gates

    code, d = work
    calls = []
    monkeypatch.setattr(lifecycle, "object_decision", lambda root, did, reason: calls.append(
        ("object", root, did, reason)) or {"decision": did, "commit": "a" * 40, "dependents": ["param:x"]})
    monkeypatch.setattr(lifecycle, "respond", lambda root, did, text, keep, option, role: calls.append(
        ("respond", did, text, keep, option, role)) or {"decision": {"status": "objected"}, "commit": "b" * 40,
                                                       "dependents": []})
    monkeypatch.setattr(gates, "gate_back", lambda root, gate, reason: calls.append(("back", gate, reason)) or {
        "gate": gate, "from": "G3", "tag": f"{code}-{gate}-back-1", "commit": "c" * 40})
    with tty("yanlış"):
        assert cli("object", "K-01", "--reason", "neden a?", "--work", code)[0] == 4    # the id was not typed
    with tty("K-01"):
        rc, out, _ = cli("object", "K-01", "--reason", "neden a?", "--work", code)
    assert rc == 0 and out.strip() == t("cli.object", id="K-01", sha="a" * 7, n=1, deps="param:x")
    rc, out, _ = cli("respond", "K-01", "--text", "a daha hafif", "--keep", "--work", code)
    assert rc == 0 and out.strip() == t("cli.respond", id="K-01", status="objected", sha="b" * 7, deps="—")
    with tty("O-G2"):
        rc, out, _ = cli("gate", "back", "G2", "--reason", "ölçüler", "--work", code)
    assert rc == 0 and out.strip() == t("cli.gate_back", gate="G2", tag=f"{code}-G2-back-1", commit="c" * 40,
                                        **{"from": "G3"})
    assert calls == [("object", d, "K-01", "neden a?"), ("respond", "K-01", "a daha hafif", True, None,
                                                         "project_engineer"), ("back", "G2", "ölçüler")]


def test_value_sets_the_main_dimension_mark_signed(cli, work, tty):
    """2.2: KM-19 — `value <card> <param> <number> --main on` (the chief, TTY, signed) enters his value and sets the
    main-dimension mark: MAINDIM-01 passes; the team removing the mark in its own commit blocks"""
    code, d = _ready(cli, work)
    assert cli("value", "S-01", "blok_en", "yirmi", "--work", code)[0] == 2           # not a number
    with tty("S-01"):
        rc, out, _ = cli("value", "S-01", "blok_en", "22", "--main", "on", "--note", "ölçüldü", "--work", code)
    p = yamlio.read(d / "params.yaml")["blok_en"]
    assert rc == 0 and json.loads(out)["value_commit"] and (p["value"], p["main_dimension"]) == (22.0, True)
    assert [r["status"] for r in _results(cli, code, "MAINDIM-01")] == ["pass"]
    assert {r["status"] for r in _results(cli, code, "APPROVAL-02")} == {"pass"}   # the record and the value
    doc = yamlio.read(d / "params.yaml")
    doc["blok_en"].pop("main_dimension")
    yamlio.write(d / "params.yaml", doc)
    assert cli("step", "işaret kalktı", "--role", "design_engineer", "--work", code)[0] == 0
    (r,) = _results(cli, code, "MAINDIM-01")
    assert (r["status"], r["msg"], r["ref"]) == ("block", "policy.maindim.removed", "blok_en")


def test_verify_pin_and_summary(cli, work, tty, shop, spy):
    """2.2: KF1-07 — `verify --pin` (TTY): the chief's key pinned in org.yaml by his signed commit, after which
    verify still passes; `summary [--day]`: the day-end summary file and its commit (E4)"""
    code, d = _ready(cli, work)
    with tty("TST"):
        rc, out, _ = cli("verify", "--pin", "--work", code)
    top = git.toplevel(d)
    assert rc == 0 and yamlio.read(top / "org.yaml")["chief_signing_key"] == shop.key
    assert out.strip() == t("cli.verify.pinned", fp=shop.key, sha=git.git("log", "-1", "--format=%h", "--", "org.yaml",
                                                                        cwd=top)[:7])
    assert cli("verify", "--work", code)[0] == 0
    from mekanik.core.report import summary

    made = spy(summary, "write")
    rc, out, _ = cli("summary", "--day", clock.today(), "--work", code)
    path, n = d / "records" / "summaries" / f"{clock.today()}.md", {k: len(v) for k, v in made[0]["sections"].items()}
    assert rc == 0 and made[0]["path"] == path and path.is_file() and out.strip() == t("cli.summary", path=path, **n)
    assert not git.git("status", "--porcelain", cwd=d)


def test_intake_and_standard_map_round_trip(cli, shop, tty, spy):
    """2.2: C1–C5, F8 — intake types/choose/ask/answer/plan/summarize/submit/status on the synthetic case I-01 and
    the chief's approval of T-01; stdmap build/add/tick/rows"""
    import mekanik.core.stdmap as stdmap
    from mekanik.core.intake import engine, summary, trees
    from mekanik.core.model.work import load_work
    from mekanik.core.store import works
    from mekanik.plugins import set_registry

    set_registry(specs())
    rc, out, _ = cli("intake", "types", "--input", "parca.step")
    assert rc == 0 and len(out.splitlines()) == len(trees.work_types())
    code = works.new_work("TST", "SYN", "Braket", "C", "sınama", "testler geçer", profiles={
        "manufacturing": "fdm-test@v0"})
    d, src = works.find(code), case("I-01", shop.root / "cases")
    assert cli("intake", "choose", "new_part", "--work", code)[1].strip() == t("cli.intake.chosen", id="new_part")
    yamlio.write(d / "work.yaml", {**yamlio.read(d / "work.yaml"), "risk_answers": yamlio.read(
        src / "work.yaml")["risk_answers"]})
    for f in ("requirements.yaml", "decisions.yaml", engine.ANSWERS, engine.ANALYSIS):
        yamlio.write_text(d / f, (src / f).read_text(encoding="utf-8").replace("TST-SYN-11", code))
    assert cli("step", "hazırlık", "--role", "project_engineer", "--work", code)[0] == 0
    plans = spy(engine, "plan")
    rc, out, _ = cli("intake", "ask", "--work", code)
    assert rc == 0 and out.splitlines()[-1] == t("cli.intake.plan", now=len(plans[-1]["now"]), later=len(
        plans[-1]["stage_end"]), limit=plans[-1]["limit"], findings=len(plans[-1]["findings"]))
    for key, value in expected("I-01")["answers"].items():
        rc, out, _ = cli("intake", "answer", key, json.dumps(value), "--work", code)
        assert rc == 0 and engine.records(d)[key]["answer"] == value
    assert cli("intake", "answer", "yok/yok", "1", "--work", code)[0] == 2
    rc, out, _ = cli("intake", "plan", "--defaults", "--work", code)
    assert rc == 0 and not [x for x in plans[-1]["nodes"] if x["state"] == "pending"]
    assert cli("intake", "summarize", "--work", code)[0] == 0
    review(d)
    rc, out, _ = cli("intake", "submit", "--work", code)
    assert rc == 0 and out.strip() == t("cli.intake.submit", card="T-01", sha=git.git("rev-parse", "HEAD~1", cwd=d)[
        :7])
    with tty("T-01"):
        assert cli("approve", "T-01", "--action", "approve", "--work", code)[0] == 0
    assert summary.status(load_work(d)) == "approved"
    assert cli("intake", "status", "--work", code)[1].strip() == t("cli.intake.status", status=t(
        "cli.intake.summary.approved"))
    built = spy(stdmap, "build")
    assert cli("stdmap", "build", "--work", code)[0] == 0 and built[0]
    item = shop.root / "madde.yaml"
    yamlio.write(item, {"title": "Şartname md. 4.2", "type": "customer_spec", "access": "customer_provided",
                        "citation": {"document": "MS-01", "clause": "4.2"}, "purpose": "sınama",
                        "why_here": "R-01 bu maddeden", "test_method": "hesap", "acceptance": {
                            "text": "20 N'da kalıcı şekil değişimi yok", "requirement": "R-01"},
                        "verification_status": "text_in_hand"})
    rc, out, _ = cli("stdmap", "add", "--definition", str(item), "--work", code)
    sm = stdmap.load(d)[-1]
    assert rc == 0 and out.strip() == t("cli.stdmap.added", id=sm["id"], title=sm["title"])
    rid = review(d)
    rc, out, _ = cli("stdmap", "tick", sm["id"], "--evidence", "document:MS-01", "--review", rid, "--work", code)
    assert rc == 0 and stdmap.load(d)[-1]["tick"]["checked"]
    assert stdmap.load(d)[-1]["evidence"][-1] == {"kind": "document", "id": "MS-01"}
    rows = stdmap.rows(d)
    rc, out, _ = cli("stdmap", "rows", "--work", code)
    assert rc == 0 and out.splitlines() == [t("cli.stdmap.row", id=r["id"], priority=r["priority"], must="!" if r[
        "mandatory"] else " ", tick="✓" if (r.get("tick") or {}).get("checked") else "✗", level=t(
        f"cli.stdmap.level.{r['shown_status']}"), title=r["title"]) for r in rows]


def test_migrate_apply_writes_the_v1_branch(cli, tmp_path, monkeypatch):
    """2.2: §14.4 — `migrate surec-work --apply` calls migrate.apply (V1–V8 first; refused without the snapshot),
    prints the V rows and the new branch"""
    import importlib

    apply = importlib.import_module("mekanik.migrate.apply")   # the package exports the function under that name
    old = Path(__file__).resolve().parents[1] / "fixtures" / "surec" / "S-001"
    rc, _, err = cli("migrate", "surec-work", str(old), "--apply")
    assert rc == 2 and err.strip() == t("cli.error", error=t("migrate.apply.no_snapshot"))
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"x": 1}))
    got = []
    monkeypatch.setattr(apply, "apply", lambda o, cfg, s: got.append((o, s)) or {
        "code": "TST-SYN-02", "branch": "TST-SYN-02/work/v1-migration", "path": tmp_path, "commit": "d" * 40,
        "report": {f"V{i}": {"status": "pass", "details": []} for i in range(1, 9)}})
    rc, out, _ = cli("migrate", "surec-work", str(old), "--snapshot", str(snap), "--apply")
    assert rc == 0 and got == [(str(old), {"x": 1})] and len(out.splitlines()) == 9
    assert out.splitlines()[-1] == t("cli.migrate.applied", code="TST-SYN-02", branch="TST-SYN-02/work/v1-migration",
                                     path=tmp_path, sha="d" * 7)


def test_panel_inbox_and_mcp_commands(cli, monkeypatch):
    """2.2: A5, A8 — `agent send` and `agent stop [--clear]` write the work's inbox (wave 2.2 · B), `panel` and `mcp`
    start B's servers (stood in for here); a missing module is reported, not a crash"""
    from mekanik.agent import inbox

    rc, out, _ = cli("agent", "send", "TST-SYN-01", "kenarı 2 mm büyüt")
    (m,) = inbox.items("TST-SYN-01")
    assert rc == 0 and (m["kind"], m["text"], m["via"]) == ("instruction", "kenarı 2 mm büyüt", "cli")
    assert out.strip() == t("cli.agent.sent", work="TST-SYN-01", id=m["id"])
    assert cli("agent", "stop", "TST-SYN-01", "--reason", "bekle")[0] == 0 and inbox.items("TST-SYN-01")
    assert cli("agent", "stop", "TST-SYN-01", "--clear")[0] == 0
    calls = []
    import mekanik.agent.mcp as mcp
    import mekanik.panel as panel

    monkeypatch.setattr(panel, "serve", lambda host, port: calls.append((host, port)))
    monkeypatch.setattr(mcp, "serve", lambda: calls.append("mcp"))
    assert cli("panel")[0] == 0 and cli("panel", "--port", "9000")[0] == 0 and cli("mcp")[0] == 0
    assert calls == [(None, None), (None, 9000), "mcp"]
    real = cli_main._m

    def missing(name):
        if name == "agent.mcp":
            raise ModuleNotFoundError("no", name="mekanik.agent.mcp")
        return real(name)
    monkeypatch.setattr(cli_main, "_m", missing)
    rc, _, err = cli("mcp")
    assert rc == 2 and err.strip() == t("cli.error", error=t("cli.not_ready", module="mekanik.agent.mcp"))
