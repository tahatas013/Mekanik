# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression of the error cases (old `regresyon.py`; handbook §10, §13).

Each case is a frozen work in tests/cases/<case>/; expected.yaml lists its subcases. A check must fail what should
fail and pass what is right:
  subcases: [{id, description, expect: [{check, ref, param?, result, value?}], cards: [{key, trigger?}]}]
  result block → at least one block from that check for that ref · fail → at least one block or warn ·
  pass → that check has results for that ref and all pass. A card expectation: a card with that key (and trigger)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mekanik.plugins import registry

from .. import data, yamlio
from ..i18n import t
from .result import BLOCK, PASS

CASES = data.REPO_ROOT / "tests" / "cases"
NOISE = 1e-9   # source: assumption — floating-point noise when comparing an expected value, not an engineering value


@dataclass
class Subcase:
    case: str
    id: str
    description: str
    passed: bool
    errors: list[str] = field(default_factory=list)


def _result_error(exp: dict, results) -> str | None:
    rel = [r for r in results if r.check == exp["check"] and r.ref == exp["ref"]
           and (exp.get("param") is None or r.extra.get("param") == exp["param"])]
    want, label = exp["result"], f"{exp['check']}({exp['ref']})"
    got = ", ".join(f"{r.status}: {r.reason}" for r in rel)
    if not rel:
        return t("checks.regress.no_result", label=label, want=want)
    if (want == PASS and any(r.failed for r in rel)) or (want == "fail" and not any(r.failed for r in rel)) \
            or (want == BLOCK and not any(r.status == BLOCK for r in rel)):
        return t("checks.regress.wrong", label=label, want=want, got=got)
    if "value" in exp and not any(r.value is not None and abs(r.value - exp["value"]) < NOISE for r in rel):
        return t("checks.regress.value", label=label, want=exp["value"], got=", ".join(str(r.value) for r in rel))
    return None


def _card_error(exp: dict, cards: list[dict]) -> str | None:
    k = next((k for k in cards if k.get("key") == exp["key"]), None)
    if k is None:
        return t("checks.regress.no_card", card=exp["key"])
    if exp.get("trigger") and exp["trigger"] not in k.get("triggers", []):
        return t("checks.regress.no_trigger", card=exp["key"], trigger=exp["trigger"], got=", ".join(k["triggers"]))
    return None


def _model(view):
    """The work's model when a package gives model hooks (`build(view)`), else None."""
    build = getattr(registry().model_hooks(), "build", None)
    return build(view) if build else None


def run_case(folder: Path, checks=None) -> list[Subcase]:
    """Run one case; `checks` replaces the registered checks (fake checks in the regression's own test)."""
    from ..cards import generate
    from ..model.work import load_work
    from .runner import run

    folder = Path(folder)
    view = load_work(folder)
    results = run(view, _model(view), checks)
    cards = generate(view, results)
    out = []
    for sc in yamlio.read(folder / "expected.yaml")["subcases"]:
        errors = [e for x in sc.get("expect") or [] if (e := _result_error(x, results))]
        errors += [e for x in sc.get("cards") or [] if (e := _card_error(x, cards))]
        out.append(Subcase(folder.name, str(sc["id"]), sc.get("description", ""), not errors, errors))
    return out


def run_all(root: Path | None = None, checks=None) -> list[Subcase]:
    root = Path(root or CASES)
    return [s for f in sorted(p for p in root.iterdir() if (p / "expected.yaml").exists())
            for s in run_case(f, checks)]
