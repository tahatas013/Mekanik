# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rule catalog (stdlib/rules/*.yaml, architecture §4.7): thresholds are read from here, not written in code."""

from __future__ import annotations

from functools import cache

from .. import data, yamlio
from ..errors import SchemaError
from ..i18n import t

RUNNER_CHECKS = ("schema",)   # produced by checks.runner itself from view.warnings (SCHEMA-01)


@cache
def catalog() -> dict[str, dict]:
    """Rule id → rule, over every catalog file (core.yaml, evidence.yaml, mech.yaml …)."""
    out: dict[str, dict] = {}
    for f in sorted(data.stdlib("rules").glob("*.yaml")):
        for r in yamlio.read(f, {}).get("rules") or []:
            if r["id"] in out:
                raise SchemaError(t("checks.rules.duplicate", id=r["id"], file=f.name))
            out[r["id"]] = {**r, "file": f.name}
    return out


def rule(rule_id: str) -> dict:
    if rule_id not in catalog():
        raise SchemaError(t("checks.rules.unknown", id=rule_id))
    return catalog()[rule_id]


def limit(rule_id: str, key: str):
    """A named threshold of a rule, e.g. limit("UNCERT-01", "ratio") → 4."""
    lim = rule(rule_id).get("limit")
    if not isinstance(lim, dict) or key not in lim:
        raise SchemaError(t("checks.rules.no_limit", id=rule_id, name=key))
    return lim[key]


def package_of(check_id: str) -> str:
    """Core check ids have no dot; package checks are `<package>.<name>` (guide §2.3)."""
    return check_id.split(".", 1)[0] if "." in check_id else "core"


def link_errors(reg, results=()) -> list[str]:
    """Catalog–code link (Ek B finding 1): every rule a check or result names is in the catalog, and every catalog
    rule of a registered package is claimed by a registered check (or seen in `results`). Empty list = bound."""
    cat = catalog()
    specs = [(c.id, c.rules) for c in reg.checks] + [(h.__name__, getattr(h, "rules", ())) for h in reg.release_hooks]
    claimed = {r for _, rules in specs for r in rules} | {r.rule for r in results}
    named = [(r, i) for i, rules in specs for r in rules] + [(r.rule, r.check) for r in results]
    out = [t("checks.rules.missing", id=r, check=c) for r, c in named if r not in cat]
    loaded = {p.id for p in reg.packages}
    out += [t("checks.rules.unbound", id=i, check=r["check"]) for i, r in cat.items()
            if package_of(r["check"]) in loaded and i not in claimed and r["check"] not in RUNNER_CHECKS]
    return sorted(set(out))
