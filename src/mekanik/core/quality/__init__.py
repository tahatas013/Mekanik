# SPDX-License-Identifier: AGPL-3.0-or-later
"""Quality engineer review on every gate and release request (old `kalite.py`; B1; architecture §4.8).

The reviewer is the plugin's `quality-engineer` subagent, not a headless `claude -p`: `prompt` gives it principles,
acceptance criteria and file paths only, over a frozen copy of HEAD; it returns `[YÜKSEK|ORTA|DÜŞÜK] location —
problem — principle — evidence` lines and `record` writes the report, valid while the inputs are unchanged.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from mekanik.config import state_dir

from .. import clock, data, yamlio
from ..errors import MekanikError
from ..evidence.calc import input_hash
from ..i18n import t
from ..model.schema import validate
from ..store.git import git

FOLDER = "records/quality"
SEVERITY = {"YÜKSEK": "high", "YUKSEK": "high", "ORTA": "medium", "DÜŞÜK": "low", "DUSUK": "low",
            "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
LINE = re.compile(r"^\s*[-*]?\s*\[(" + "|".join(SEVERITY) + r")\]\s*(.+)$")


def _copy(sha: str) -> Path:
    return state_dir() / "review" / sha


def prompt(root, subject: str) -> str:
    """The subagent's prompt; makes the frozen copy of HEAD (removed by `record`)."""
    root = Path(root)
    sha, rel = git("rev-parse", "HEAD", cwd=root), git("rev-parse", "--show-prefix", cwd=root).rstrip("/")
    if not (copy := _copy(sha)).exists():
        copy.parent.mkdir(parents=True, exist_ok=True)
        git("worktree", "add", "-q", "--detach", str(copy), sha, cwd=root)
    return t("quality.prompt", subject=subject, code=yamlio.read(root / "work.yaml")["code"], copy=copy / rel,
             handbook=data.REPO_ROOT / "docs" / "handbook.md")


def parse(text: str) -> tuple[list[dict], str]:
    """Finding lines → findings; the last other non-empty line is the overall assessment."""
    findings, other = [], []
    for line in text.splitlines():
        if not (m := LINE.match(line)):
            other += [line.strip()] if line.strip() else []
            continue
        part = [x.strip() for x in re.split(r"\s+—\s+", m.group(2))] + ["", "", ""]
        findings.append({"no": len(findings) + 1, "severity": SEVERITY[m.group(1)], "location": part[0],
                         "problem": part[1], "principle": part[2], "evidence": " — ".join(part[3:]).strip(" —"),
                         "status": "open"})
    return findings, other[-1] if other else ""


def reports(root) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((Path(root) / FOLDER).glob("*.yaml")):
        try:
            out.append((p, yamlio.read(p, {})))
        except MekanikError:
            continue
    return out


def record(root, subject: str, text: str, reviewer: str | None = None) -> tuple[Path, dict]:
    """Write the subagent's findings as the report of HEAD's frozen copy (not committed; the request step commits)."""
    root = Path(root)
    sha = git("rev-parse", "HEAD", cwd=root)
    if not (copy := _copy(sha)).exists():
        raise MekanikError(t("quality.no_copy", commit=sha[:12]))
    findings, summary = parse(text)
    no = 1 + max((int(r["id"][3:]) for _, r in reports(root) if str(r.get("id", "")).startswith("QR-")), default=0)
    at = clock.now()
    rep = {"kind": "quality_review", "schema_version": "1.0", "id": f"QR-{no:03d}",
           "work": yamlio.read(root / "work.yaml")["code"], "subject": subject, "commit": sha,
           "input_hash": input_hash(root),
           "reviewer": {"role": "quality_engineer", "context": "clean", **({"adapter": reviewer} if reviewer else {})},
           "at": at, "findings": findings, **({"summary": summary} if summary else {})}
    validate("quality_review", rep, FOLDER)
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    path = root / FOLDER / f"{datetime.fromisoformat(at):%Y%m%d-%H%M%S}-{slug}.yaml"
    yamlio.write(path, rep)
    try:
        git("worktree", "remove", "--force", str(copy), cwd=root)
    finally:
        shutil.rmtree(copy, ignore_errors=True)
    return path, rep


def current(root) -> tuple[Path, dict] | None:
    """The latest report made on today's inputs; None means the review must run."""
    ihash = input_hash(root)
    return next(((p, r) for p, r in reversed(reports(root)) if r.get("input_hash") == ihash), None)


def open_high(report: dict) -> list[dict]:
    return [f for f in report.get("findings", []) if f.get("severity") == "high" and f.get("status") == "open"]


def require_clear(root, subject: str) -> tuple[Path, dict]:
    """QUALITY-01: the gate and release request steps call this before opening the card."""
    if (cur := current(root)) is None:
        raise MekanikError(t("quality.review_needed", subject=subject))
    if high := open_high(cur[1]):
        raise MekanikError(t("quality.open_high", n=len(high), report=cur[0].name, items="; ".join(
            f"{f['no']} {f['location']} — {f['problem']}"[:160] for f in high[:3])))
    return cur


def close(root, report: str, finding_id, rationale: str, regression_needed: bool, regression_note: str,
          by_role: str = "project_engineer", commit: str | None = None) -> dict:
    """Close a finding with a rationale. The regression question is mandatory: the case when needed, else why not."""
    if not rationale.strip():
        raise MekanikError(t("quality.close_rationale"))
    if not regression_note.strip():
        raise MekanikError(t("quality.close_regression"))
    path = Path(root) / FOLDER / Path(report).name
    rep = yamlio.read(path) or {}
    f = next((x for x in rep.get("findings", []) if x["no"] == int(str(finding_id).removeprefix("Q-"))), None)
    if f is None:
        raise MekanikError(t("quality.no_finding", report=Path(report).name, no=finding_id))
    f.update(status="closed", closure={
        "by_role": by_role, "note": rationale.strip(), "commit": commit or git("rev-parse", "HEAD", cwd=Path(root)),
        "regression": {"needed": bool(regression_needed),
                       ("case" if regression_needed else "reason"): regression_note.strip()}})
    validate("quality_review", rep, str(path))
    yamlio.write(path, rep)
    return f
