# SPDX-License-Identifier: AGPL-3.0-or-later
"""Builds tests/cases/{S-001,H-001} from the old-format synthetic cases with `mekanik.migrate` (dry run).

    MEKANIK_CONFIG_DIR=tests/fixtures/config uv run python tests/migrate/build_cases.py

expected.yaml is the v1 counterpart of the old beklenen.yaml (format: tests/cases/README.md)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from mekanik.config import load_config
from mekanik.core import yamlio
from mekanik.migrate import surec_work, verify
from mekanik.migrate.convert import V, key

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "tests" / "fixtures" / "surec"
DATA = Path(__file__).with_name("data")
CASES = ("S-001", "H-001")
NOTE = ("Sınama vakası: tests/migrate/build_cases.py ile üretildi; v1'de zorunlu olup eskide olmayan alanlar "
        "stdlib/strictness/phase1.yaml'a göre uyarıdır (G-27).")


def expected(old: dict, code: str) -> dict:
    """beklenen.yaml → expected.yaml: check ids (guide §2.3), results block/warn/pass/failed, v1 card keys."""
    return {"code": code, "subcases": [{
        "id": str(a["no"]), "description": a.get("aciklama", ""),
        "expect": [{"check": V["check"][e["kontrol"]], "ref": e["ref"], "result": V["status"][e["sonuc"]]}
                   | {b: e[a] for a, b in (("deger", "value"), ("param", "param")) if a in e}
                   for e in a.get("beklenen", [])],
        "cards": [{"key": key(k["anahtar"])} | ({"trigger": V["trigger"][k["tetikleyici"]]}
                                                 if "tetikleyici" in k else {})
                  for k in a.get("kartlar", [])]} for a in old["alt_vakalar"]]}


def snapshot(case: str) -> dict:
    return json.loads((DATA / "old" / f"{case}.json").read_text(encoding="utf-8"))


def known() -> list[dict]:
    return yamlio.read(DATA / "v4_known.yaml")["known"]


def build(case: str, out: Path, cfg=None) -> dict:
    cfg = cfg or load_config()
    shutil.rmtree(out, ignore_errors=True)
    surec_work(OLD / case, out, cfg, old=snapshot(case))
    yamlio.write(out / "expected.yaml", expected(yamlio.read(OLD / case / "beklenen.yaml"), snapshot(case)["code"]))
    res = verify(OLD / case, out, cfg, old=snapshot(case), known=known())
    with (out / "records" / "migration-report.md").open("a", encoding="utf-8") as f:
        f.write(f"\n> {NOTE}\n")
    return res


if __name__ == "__main__":
    for c in CASES:
        res = build(c, ROOT / "tests" / "cases" / c)
        print(c, " ".join(f"{k}:{v['status']}" for k, v in res.items()))
