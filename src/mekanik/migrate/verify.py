# SPDX-License-Identifier: AGPL-3.0-or-later
"""Migration checks V1–V8 (architecture §14.3) and migration-report.md. A check passes, fails or is pending
(pending: the v1 side it needs — phase-1 strictness list, checks, cards, model hooks, calc runner — is missing)."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.errors import MekanikError
from mekanik.core.i18n import t
from mekanik.core.model import schema
from mekanik.core.model.params import SOURCE_RE

from .convert import COPY, V, Log, key, new_side, src

WORK = {"work.yaml": "work", "params.yaml": "params", "decisions.yaml": "decision", "approvals.yaml": "approval",
        "replies.yaml": "replies", "requirements.yaml": "requirement", "cards/*.yaml": "card",
        "records/calcs/*.json": "calculation"}
CONFIG = {"orgs/*.yaml": "config#/$defs/organization", "machines/*.yaml": "config#/$defs/machine",
          "instruments/*.yaml": "config#/$defs/instrument"}
OLD = ("calisma.yaml", "params.yaml", "gecmeler.yaml", "montaj.yaml", "kararlar.yaml", "onaylar.yaml", "yanitlar.yaml",
       "istek-listesi.yaml", "kayit/hesaplar/*.json")
TOL = {"V6": 1e-6, "V8": 1e-9}    # source: architecture §14.3 V6, V8 (proposed relative differences)


def _read(f: Path):
    return json.loads(f.read_text(encoding="utf-8")) if f.suffix == ".json" else yamlio.read(f)


def v1(root: Path, gaps: set, files: dict) -> list[str]:
    """Every new file passes its v1 schema; the only accepted errors are missing fields listed as migration gaps."""
    bad = []
    for pat, kind in files.items():
        for f in sorted(root.glob(pat)):
            rel, doc = str(f.relative_to(root)), _read(f)
            for i, d in enumerate(doc) if kind in ("decision", "approval") else [(None, doc)]:
                for e in schema.errors(kind, d):
                    p = [str(x) for x in ([] if i is None else [i]) + list(e.absolute_path)]
                    m = re.match(r"^'([^']+)' is a required property$", e.message)
                    gap = m and ((rel, "/".join(p + [m[1]])) in gaps or "then" in e.schema_path and any(    # an `if`
                        g[0] == rel and g[1].rpartition("/")[0] == "/".join(p) for g in gaps))   # without `required`
                    bad += [] if gap else [f"{rel}:{'/'.join(p)}: {e.message}"]
    return bad


def _nums(x) -> list[float]:
    if isinstance(x, (bool, str)) or x is None:
        return []
    if isinstance(x, (int, float)):
        return [round(float(x), 9)]
    return [n for v in (x.values() if isinstance(x, dict) else x) for n in _nums(v)]


def v2(old: Path, new: Path) -> list[str]:
    """Number conservation (old gecis.sayi_korunumu): equal multisets of numbers; copied files are byte-equal."""
    cards = [f for f in old.glob("kartlar/*.yaml") if not yamlio.read(f).get("uretilen")]
    a = Counter(n for f in [*cards, *(g for p in OLD for g in old.glob(p))] for n in _nums(_read(f)))
    b = Counter(n for p in [*WORK, "fits.yaml"] for f in new.glob(p) for n in _nums(_read(f)))
    copied = [(f, new / d / f.relative_to(old / s)) for s, d in COPY.items() for f in (old / s).rglob("*")
              if f.is_file() and "__pycache__" not in f.parts]
    return [f"- {x} ×{n}" for x, n in (a - b).items()] + [f"+ {x} ×{n}" for x, n in (b - a).items()] + [
        str(f) for f, g in copied if not g.exists() or g.read_bytes() != f.read_bytes()]


def v3(old: Path, new: Path, log: dict) -> list[str]:
    """Source tags: none unmapped, and an old unsourced value stays unsourced (the SOURCE-01 block is kept)."""
    pairs = [({p["ad"]: p for p in yamlio.read(old / "params.yaml", [])}, yamlio.read(new / "params.yaml", {})),
             ({e["no"]: e for e in yamlio.read(old / "montaj.yaml", {}).get("esnemeler") or []},
              {e["id"]: e for e in yamlio.read(new / "fits.yaml", {}).get("flexes", [])})]
    return log["unmapped"] + [f"{k}: {a} → {b}" for o, n in pairs for k, x in o.items()
                              if ((a := x.get("kaynak")) is None) != ((b := (n.get(k) or {}).get("source")) is None)
                              or b and (not SOURCE_RE.match(b) or b != src(Log(), k, a, x.get("olcum_profili")))]


def v4(old: dict, results, cards, known) -> list[str] | str:
    """Check equality: the (v1 rule, subject, level) sets are equal, except for listed intentional changes."""
    from mekanik.plugins import registry

    have = {r for c in registry().checks for r in c.rules}
    ok, nk = {c["id"]: key(c["key"]) for c in old["cards"]}, {c["id"]: c.get("key") for c in cards}
    o = {(V["rule"].get(r["rule"], r["rule"]), ok.get(r["ref"], r["ref"]), V["status"][r["status"]])
         for r in old["results"]}
    n = {(r.rule, nk.get(r.ref, r.ref), r.status) for r in results}
    diff = [f"{'-' if x in o else '+'} {x}" for x in sorted(o ^ n, key=str) if x[0] in have and not any(
        all(k.get(f) in (None, v) for f, v in zip(("rule", "ref", "status"), x)) for k in known)]
    missing = sorted({x[0] for x in o} - have)
    return diff or (t("migrate.pending.rules", rules=", ".join(missing)) if missing else [])


def v5(view, old: dict, cards) -> list[str]:
    """An approval valid in surec (subject unchanged) is valid in v1; an invalid one stays invalid."""
    from mekanik.core.cards.approval import digest, subject_values

    olds, news, bad = {key(c["key"]): c for c in old["cards"]}, {c["id"]: c for c in cards}, []
    for a in (a for a in view.approvals if a.get("migrated_from_hash")):
        o = (n := news.get(a["card"])) and olds.get(n.get("key"))
        was = bool(o) and a["migrated_from_hash"] == o["subject_hash"]
        now = bool(n) and a["approved_hash"] == digest(subject_values(view, n["subject"]))
        bad += [f"{a['card']}@{a.get('at')}: {was} → {now}"] if was != now else []
    return bad


def _close(a, b, tol) -> bool:
    return b is not None and math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def v6(hooks, model, old: dict) -> list[str] | str:
    """Model equality per part: volume, bounding box and face count (contract: mech ModelHooks.metrics)."""
    if not old["model"] and model is None:
        return []
    if not hasattr(hooks, "metrics"):
        return t("migrate.pending.model")
    new, om = hooks.metrics(model or {}), old["model"]
    vec = lambda m: [m["volume"], *m["bbox"]]  # noqa: E731
    return [f"{p}: {om.get(p)} ≠ {new.get(p)}" for p in sorted(set(om) | set(new)) if p not in new or p not in om
            or any(om[p][k] != new[p].get(k) for k in ("faces", "solids") if k in om[p])
            or not all(_close(x, y, TOL["V6"]) for x, y in zip(vec(om[p]), vec(new[p])))]


def v7(old: dict, cards) -> list[str]:
    """Card equality: the key sets of open cards are equal (the migration-gap card is the one new card)."""
    o = {key(c["key"]) for c in old["cards"] if c["status"] == "acik"}
    n = {c.get("key") for c in cards if c.get("status") in ("open", "awaiting_reply")} - {"migration_gap"}
    return [f"- {k}" for k in sorted(o - n)] + [f"+ {k}" for k in sorted(n - o)]


def v8(view, model, old_work: Path) -> list[str] | str:
    """Calculations re-run with the same results (mekanik.core.evidence.calc.run without cache, wave 2 · B)."""
    from mekanik.core.evidence.calc import run

    bad = []
    for r in run(view, model, cache=False):
        o = _read(f) if (f := old_work / "kayit/hesaplar" / f"{r['id']}.json").exists() else {}
        nv = {x["name"]: x["value"] for x in r.get("results", []) + r.get("magnitudes", [])}
        bad += [f"{r['id']}.{x['ad']}: {x['deger']} ≠ {nv.get(x['ad'])}" for x in o.get("sonuclar", []) + o.get(
            "buyuklukler", []) if x["deger"] is not None and not _close(x["deger"], nv.get(x["ad"]), TOL["V8"])]
    return bad


def verify(old_work, new_work, config=None, old: dict | None = None, known=()) -> dict:
    """V1–V8 for one migrated work; writes records/migration-report.md. `old` is the old-side snapshot."""
    ow, new = Path(old_work), Path(new_work)
    log = yamlio.read(new / "records" / "migration.yaml")
    out = {"V1": v1(new, {(g["file"], g["path"]) for g in log["gaps"]}, WORK), "V2": v2(ow, new),
           "V3": v3(ow, new, log)}
    try:
        view, hooks, model, res, cards = new_side(new, config)
        out |= {"V4": v4(old, res, cards, known), "V5": v5(view, old, cards), "V6": v6(hooks, model, old),
                "V7": v7(old, cards), "V8": v8(view, model, ow)}
    except (ImportError, MekanikError) as e:
        out |= dict.fromkeys(("V4", "V5", "V6", "V7", "V8"), f"{type(e).__name__}: {e}")
    return _done(new / "records" / "migration-report.md", log, out)


def verify_config(out_dir) -> dict:
    """V1 (and V3's unmapped tags) for the surec-config output; writes migration-report.md next to it."""
    out, log = Path(out_dir), yamlio.read(Path(out_dir) / "migration.yaml")
    return _done(out / "migration-report.md", log, {
        "V1": v1(out, {(g["file"], g["path"]) for g in log["gaps"]}, CONFIG), "V3": log["unmapped"]})


def _done(path: Path, log: dict, out: dict) -> dict:
    res = {k: {"status": "pending" if isinstance(v, str) else "fail" if v else "pass",
               "details": [v] if isinstance(v, str) else v} for k, v in out.items()}
    L = [f"# {t('migrate.report.title', code=log.get('code', log['kind']))}", "", t("migrate.report.intro"), "",
         f"| V | {t('migrate.report.status')} | {t('migrate.report.detail')} |", "| --- | --- | --- |"] + [
        f"| {k} | {t('migrate.status.' + v['status'])} | {'; '.join(map(str, v['details']))[:400] or '—'} |"
        for k, v in res.items()]
    for sec, rows in (
            ("gaps", [f"`{g['file']}` · `{g['path']}`" + (f" — {t('migrate.report.proposal')}: `{g['proposal']}`"
                                                         if "proposal" in g else "") for g in log["gaps"]]),
            ("derived", [f"`{d['file']}` · `{d['path']}` — " + t("migrate.why." + d["why"].split(":")[0],
                                                                 detail=d["why"].partition(":")[2])
                         for d in log["derived"]]),
            ("dropped", log["dropped"]), ("unmapped", log["unmapped"]),
            ("pending", [f"{p['step']}: {p['reason']}" for p in log["pending"]])):
        L += ["", f"## {t('migrate.report.' + sec)} ({len(rows)})", ""] + ([f"- {r}" for r in rows] or ["- —"])
    yamlio.write_text(path, "\n".join(L) + "\n")
    return res
