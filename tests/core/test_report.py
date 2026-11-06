# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report flow without a model (OCCT-free, architecture §9): the stream line of every step (E1), records/events.jsonl
append-only (E5), the emit contract the other parts call, the merge of a decision branch, the day-end summary (E4).
The model figures (E2, E3) are in tests/flow/test_report_figures.py."""

from __future__ import annotations

import json
import re

import pytest
from test_store import (CHIEF, PARAMS, TEAM, gpg_keys, log_entries, new, prepare, review, run_record,  # noqa: F401
                        shop)

from mekanik.cli.main import main as cli
from mekanik.core import clock, quality, yamlio
from mekanik.core.checks.result import summary as counts
from mekanik.core.errors import SchemaError
from mekanik.core.i18n import t
from mekanik.core.model.schema import errors
from mekanik.core.process import chief, gates
from mekanik.core.process.step import evaluate, step
from mekanik.core.report import stream, summary
from mekanik.core.store import git

ID = re.compile(r"^ev-\d{4}-\d{2}-\d{2}-\d{4,}$")


def _committed(d) -> list[dict]:
    return [json.loads(x) for x in git.git("show", f"HEAD:./{stream.FILE}", cwd=d).splitlines()]


def _rewrite(d, fn) -> None:
    path = d / stream.FILE
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")


def test_every_step_writes_one_full_committed_stream_line(shop):
    """2.4: E1 — every `mekanik step` (function and CLI) adds exactly one complete stream line: role, line, cards,
    check summary and the step's commit; it rides in the log commit, so the line is committed (100 %)"""
    code, d = new()
    prepare(d)
    steps = [step(d, "İlk adım", "project_engineer", "metin"),
             step(d, "Kartlı adım", "design_engineer", cards=["S-09"]),
             step(d, "x" * 300, "technician")]
    assert cli(["step", "CLI adımı", "--role", "design_engineer", "--work", str(d)]) == 0
    steps.append({"commit": git.git("log", "-2", "--format=%H", cwd=d).split()[1], "cards": [],
                  "summary": counts(evaluate(d)[2])})
    events = [e for e in stream.read(d) if e["type"] == "step"]
    assert len(events) == len(steps) == 4 and _committed(d) == stream.read(d) and git.is_clean(d)
    asked = [("İlk adım", "project_engineer"), ("Kartlı adım", "design_engineer"), ("x" * 300, "technician"),
             ("CLI adımı", "design_engineer")]
    for e, s, (title, role) in zip(events, steps, asked):
        assert errors("stream_event", e) == [] and ID.match(e["id"]) and e["work"] == code and e["role"] == role
        assert e["commit"] == s["commit"] and e["line"] == stream._line(title) and len(e["line"]) <= stream.LINE_MAX
        assert e["check_summary"] == {k: s["summary"][k] for k in ("block", "warn")}
        assert [r["id"] for r in e.get("refs") or [] if r["kind"] == "card"] == s["cards"]
        assert s.get("event", e) == e
    assert events[1]["refs"] == [{"kind": "card", "id": "S-09"}]
    assert len({e["id"] for e in stream.read(d)}) == len(stream.read(d))
    assert len([e for e in stream.read(d) if "commit" in e]) == len(log_entries(d))   # one per log entry


def test_gate_and_approval_lines_follow_their_log_entries(shop):
    """2.4: E1 — system steps and the chief's approval also write their line (gate request, decision): one line with
    its commit per log entry (other parts add lines of their own)"""
    code, d = new()
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    chief.approve(d, "O-G0")
    logged = [e for e in stream.read(d) if "commit" in e]
    assert [e["type"] for e in logged] == ["step", "gate", "decision"] and len(logged) == len(log_entries(d))
    assert logged[-1]["role"] == "chief_engineer" and logged[-1]["refs"] == [{"kind": "card", "id": "O-G0"}]
    assert git.is_clean(d)
    stream.verify(d)


def test_rewriting_the_events_file_is_refused(shop):
    """2.4: E5 — events.jsonl is append-only: a changed, cut or deleted line is refused by emit, by the next step
    (nothing is committed) and by verify; appending stays allowed"""
    code, d = new()
    prepare(d)
    step(d, "bir", "project_engineer")
    step(d, "iki", "project_engineer")
    head, good = git.head(d), (d / stream.FILE).read_text(encoding="utf-8")
    for bad in (lambda s: s.replace('"bir"', '"BİR"'), lambda s: s.split("\n", 1)[1], lambda s: ""):
        _rewrite(d, bad)
        for attempt in (lambda: stream.emit(d, "notice", line="ek"), lambda: step(d, "üç", "project_engineer"),
                        lambda: stream.verify(d), lambda: stream.check(d)):
            with pytest.raises(stream.Rewritten) as e:
                attempt()
            assert e.value.where == ""
        assert git.head(d) == head
        _rewrite(d, lambda s: good)
    (d / stream.FILE).unlink()
    with pytest.raises(stream.Rewritten):
        stream.emit(d, "notice", line="ek")
    git.git("checkout", "--", stream.FILE, cwd=d)
    stream.emit(d, "notice", line="ek")                                   # appending is fine
    step(d, "üç", "project_engineer")
    with pytest.raises(stream.Rewritten):
        stream.since(d, (d / stream.FILE).stat().st_size + 1)             # the reader sees a cut file too


def test_a_rewrite_committed_outside_mekanik_is_found_in_the_history(shop):
    """2.4: E5 — a rewrite committed by hand passes HEAD's prefix test but not the first-parent history"""
    code, d = new()
    prepare(d)
    step(d, "bir", "project_engineer")
    step(d, "iki", "project_engineer")
    _rewrite(d, lambda s: s.replace('"bir"', '"BİR"'))
    sha = git.commit(d, git.message("elle", None, "project_engineer"), [str(d / stream.FILE)], TEAM)
    stream.check(d)
    with pytest.raises(stream.Rewritten) as e:
        stream.verify(d)
    assert e.value.where == sha[:12]


def test_emit_contract(shop):
    """2.4: E1 — the emit contract of P and I: system clock, work, id, schema check, shorthands, transient events"""
    code, d = new()
    seen = []
    stream.LISTENERS.append(seen.append)
    try:
        (d / "records" / "visuals").mkdir(parents=True, exist_ok=True)
        (d / "records" / "visuals" / "k.svg").write_text("<svg/>")
        e = stream.emit(d, "provisional_decision", role="project_engineer", line="Geçici karar K-07\nikinci satır",
                        visuals=["records/visuals/k.svg"], refs=[{"kind": "decision", "id": "K-07"}],
                        objection_until="G2", check_summary={"block": 0, "warn": 2, "pass": 9})
        assert e["line"] == "Geçici karar K-07 ikinci satır" and e["check_summary"] == {"block": 0, "warn": 2}
        assert e["visuals"][0]["kind"] == "model_view" and len(e["visuals"][0]["hash"]) == 16
        assert stream.read(d) == [e] and seen == [e] and e["work"] == code and ID.match(e["id"])
        size = (d / stream.FILE).stat().st_size
        tr = stream.emit(d, "agent_message", line="token", persistent=False)
        assert seen[-1] == tr and (d / stream.FILE).stat().st_size == size     # transient: not written
        with pytest.raises(SchemaError):
            stream.emit(d, "provisional_decision", line="görselsiz")           # schema: visuals, refs, objection
        with pytest.raises(SchemaError):
            stream.emit(d, "step", line="commit yok")
        with pytest.raises(TypeError):
            stream.emit(d, "notice", line="x", at="2020-01-01T00:00:00+00:00")  # the clock is the system's
        assert (d / stream.FILE).stat().st_size == size
        events, off = stream.since(d, 0)
        later = stream.emit(d, "notice", line="sonra")
        assert events == [e] and stream.since(d, off) == ([later], (d / stream.FILE).stat().st_size)
        assert next(stream.follow(d, off))[0] == [later]
    finally:
        stream.LISTENERS.remove(seen.append)


def test_decision_branch_lines_survive_the_merge(shop, tmp_path):
    """2.4: E5 — both branches append; the merge keeps both, ours first, the history stays append-only"""
    code, d = new()
    prepare(d)
    step(d, "ortak", "project_engineer")
    git.git("worktree", "add", "-q", "-b", f"{code}/decision/K-01-b", str(wt := tmp_path / "wt"), cwd=d)
    step(wt / "sentetik" / code, "dalda", "design_engineer")
    step(d, "iş dalında", "project_engineer")
    ours = stream.read(d)
    git.git("merge", "--no-ff", "-q", "-m", "birleşim", f"{code}/decision/K-01-b", cwd=d,
            env=git.identity_env(*CHIEF))
    lines = stream.read(d)
    assert lines[:len(ours)] == ours and [e["line"] for e in lines[len(ours):]] == ["dalda"]
    assert len({e["id"] for e in lines}) == len(lines)
    stream.verify(d)
    step(d, "birleşimden sonra", "project_engineer")


def _sections(text: str) -> dict[str, list[str]]:
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = out.setdefault(line[3:], [])
        elif cur is not None and line.strip():
            cur.append(line)
    return out


def test_day_end_summary_has_four_sections_and_none_for_empty_ones(shop):
    """2.4: E4 — records/summaries/<day>.md has the four sections of §9.3 in order; an empty one says "none"; the
    summary and its stream line are committed"""
    code, d = new()
    prepare(d)
    step(d, "hazırlık", "project_engineer")
    review(d, "- [ORTA] model — kaburga kökü ince — et kuralı — kesit\nGenel: tamam")
    gates.stage_finish(d, "G0")                                          # O-G0: a hold card waiting for the chief
    stream.emit(d, "provisional_decision", role="project_engineer", line="Geçici karar K-07: R = 0,5 × et",
                visuals=[{"kind": "model_view", "id": "k.svg"}], refs=[{"kind": "decision", "id": "K-07"}],
                objection_until="G2")
    run = yamlio.read(p := run_record(shop.root / "state", code, "finished"))
    yamlio.write_text(p, json.dumps({**run, "started_at": clock.now(), "usage": {"turns": 7}}))
    out = summary.write(d)
    heads = [t(f"report.summary.section.{k}") for k in summary.SECTIONS]
    got = _sections(out["path"].read_text(encoding="utf-8"))
    assert list(got) == heads and all(got[h] for h in heads)
    assert any("K-07" in x and "G2" in x for x in got[heads[0]])                     # provisional, until G2
    assert any("O-G0" in x for x in got[heads[1]])                                    # the hold card waits
    path, rep = quality.reports(d)[-1]
    f = rep["findings"][0]
    assert "- " + t("report.summary.finding", report=path.name, no=1, severity=t("report.summary.severity.medium"),
                    location=f["location"], problem=f["problem"]) in got[heads[2]]  # the open quality finding
    assert got[heads[3]] == ["- " + t("report.summary.agents", n=1, turns=7)]
    assert out["event"]["type"] == "daily_summary" and stream.read(d)[-1] == out["event"] and git.is_clean(d)
    empty = _sections(summary.write(d, day="2000-01-01")["path"].read_text(encoding="utf-8"))
    assert list(empty) == heads and empty[heads[0]] == empty[heads[3]] == [t("report.summary.none")]
    assert set(summary.build(d, "2000-01-01")) == set(summary.SECTIONS)
