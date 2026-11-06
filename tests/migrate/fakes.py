# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stand-ins for the v1 side of V4–V8, built from the old-side snapshot (tests/migrate/data/old/*.json)."""

from __future__ import annotations

from build_cases import snapshot
from mekanik.core.checks.result import Result
from mekanik.migrate.convert import V, key

RULES = tuple(sorted(set(V["rule"].values())))


def old_results(case: str, change=None) -> list[Result]:
    """The old `surec kontrol` results as v1 results (what an equal new check set returns)."""
    out = []
    for r in snapshot(case)["results"]:
        res = Result(V["check"][r["check"]], V["rule"][r["rule"]], V["status"][r["status"]], "x", ref=r["ref"])
        out.append(change(res) if change else res)
    return out


def old_cards(case: str, drop=()) -> list[dict]:
    """The old generated cards as v1 cards (key, status) plus the migration-gap card."""
    status = {"acik": "open", "onaylandi": "approved", "reddedildi": "rejected"}
    return [{"id": c["id"], "key": key(c["key"]), "status": status[c["status"]], "subject": {"old": c["key"]}}
            for c in snapshot(case)["cards"] if key(c["key"]) not in drop] + [
        {"id": "MG-01", "key": "migration_gap", "status": "open", "subject": {}}]


class Hooks:
    def __init__(self, metrics):
        self._m = metrics

    def build(self, view):
        return {"model": True}

    def metrics(self, model):
        return self._m
