# SPDX-License-Identifier: AGPL-3.0-or-later
"""Helpers of the intake and standard map tests: the synthetic cases (tests/intake/cases, architecture §7.2), a
registry with the core and stand-ins for the domain packages (their real data folders, none of their code: OCCT-free),
and a quality review record as the quality engineer's subagent leaves it."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from mekanik.core import builtin, clock, yamlio
from mekanik.core.evidence.calc import input_hash
from mekanik.core.store import git
from mekanik.plugins import PackageSpec

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEKANIK_CONFIG_DIR", str(ROOT / "tests" / "fixtures" / "config"))
CASES = ROOT / "tests" / "intake" / "cases"
NAMES = sorted(p.name for p in CASES.iterdir() if p.is_dir())
PKG = ROOT / "packages"


def specs() -> list[PackageSpec]:
    return [builtin.SPEC, PackageSpec(id="mech", version="0.1.0", i18n=PKG / "mech/src/mekanik_mech/i18n"),
            PackageSpec(id="print3d", version="0.1.0", profile_types={"print3d.fdm": lambda p, where: None},
                        i18n=PKG / "print3d/src/mekanik_print3d/i18n"),
            PackageSpec(id="analysis", version="0.1.0", i18n=PKG / "analysis/src/mekanik_analysis/i18n")]


def case(name: str, dest: Path) -> Path:
    shutil.copytree(CASES / name, d := dest / name, ignore=shutil.ignore_patterns("expected.yaml"))
    return d


def expected(name: str) -> dict:
    return yamlio.read(CASES / name / "expected.yaml")


def review(root: Path, findings=()) -> str:
    """A clean-context review of HEAD (records/quality/*.yaml); → its id."""
    rid = f"QR-{1 + len(list((root / 'records/quality').glob('*.yaml'))):03d}"
    yamlio.write(root / "records/quality" / f"20261106-000000-{rid.lower()}.yaml", {
        "kind": "quality_review", "schema_version": "1.0", "id": rid, "work": yamlio.read(root / "work.yaml")["code"],
        "subject": "anlama özeti", "commit": git.head(root), "input_hash": input_hash(root),
        "reviewer": {"role": "quality_engineer", "context": "clean"}, "at": clock.now(), "findings": list(findings)})
    return rid


def events(root: Path, kind: str | None = None) -> list[dict]:
    import json

    path = root / "records" / "events.jsonl"
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x] if path.exists() else []
    return [e for e in lines if kind is None or e["type"] == kind]
