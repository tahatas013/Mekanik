# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dry-run conversion of old `surec` data to v1 (architecture §14.2); name tables in names.yaml.

No value is invented (KM-37): a field v1 requires without an old counterpart is a migration gap (with a proposal when
one can be derived); a value computed by an old-system rule is listed as derived; an old field with no v1 place is
listed as dropped. All of it goes to migration.yaml for `verify` and the report."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from mekanik.core import clock, yamlio
from mekanik.core.errors import MekanikError
from mekanik.core.evidence.calc import result_hash
from mekanik.core.i18n import catalogs, t
from mekanik.core.process.profile import load_profile

M = yamlio.read(Path(__file__).with_name("names.yaml"))
V, SV, GAP_CARD, HEX = M["values"], "1.0", "MG-01", re.compile(r"^[0-9a-f]{7,64}$")
COPY = {"model": "model", "kayit/gunluk": "records/log", "kayit/gorseller": "records/visuals",
        "kayit/kalite": "records/quality", "cikti": "out"}


class Phase2Error(MekanikError):
    """The real migration (--apply) is phase 2 (architecture §14.1, KM-25)."""


class Log:
    def __init__(self, **kw):
        self.gaps, self.derived, self.dropped, self.unmapped, self.pending = [], [], [], [], []
        self.__dict__.update(kw)

    def derive(self, file, path, value, why):
        self.derived.append({"file": file, "path": path, "why": why})
        return value

    def need(self, file, d, fields, prefix="", proposal=None):
        """Fields v1 requires that are missing or empty become gaps (`fields` may also be a single gap path)."""
        for f in [fields] if isinstance(fields, str) else fields:
            if d is None or d.get(f) in (None, ""):
                d and d.pop(f, None)
                p = (proposal or {}).get(f)
                self.gaps.append({"file": file, "path": prefix + f} | ({} if p is None else {"proposal": p}))


def guard(dry_run: bool) -> None:
    if not dry_run:
        raise Phase2Error(t("migrate.apply_phase2"))


def key(old: str | None) -> str | None:
    """Old card key → v1 key (`gecme:G-04` → `fit:G-04`)."""
    a, b = next(((a, b) for a, b in M["key_prefix"] if old and old.startswith(a)), ("", ""))
    return old and b + old[len(a):]


def ts(v) -> str | None:
    """An ISO 8601 stamp with offset as is; a naive old stamp ('2026-10-26 11:22') has no zone and is not converted."""
    try:
        d = datetime.fromisoformat(str(v))
    except ValueError:
        return None
    return d.isoformat() if d.tzinfo else None


def src(log, where, tag, instrument=None, cfg=None):
    """Old source tag → v1 tag (V3). An unmapped tag is kept as is, so the schema and V3 both catch it."""
    tag = str(tag)
    if tag.startswith("olcu:") and instrument and (cfg is None or any(
            i["id"] == instrument for i in cfg.lists["instruments"])):
        return f"measured:{instrument}"
    a, b = next(((a, b) for a, b in M["source_prefix"].items() if tag.startswith(a)), (None, None))
    log.unmapped += [] if a or tag in V["source"] else [f"{where}: {tag}"]
    return b + tag[len(a):] if a else V["source"].get(tag, tag)


def ren(log, where, d, table, cfg=None):
    """Rename `d` by names.yaml fields.<table>; filled old keys the table does not know are listed as dropped."""
    out, T = {}, M["fields"][table]
    for k, v in (d or {}).items():
        if k not in T:
            log.dropped += [f"{where}.{k}"] if v not in (None, "", [], {}) else []
        elif T[k] and v is not None:
            new, fn = (T[k], None) if isinstance(T[k], str) else T[k]
            if (x := _fn(log, where, fn, v, d, cfg) if fn else v) is not None:
                out[new] = x
    return out


def _fn(log, where, fn, v, d, cfg):
    kind, _, arg = fn.partition(":")
    val = lambda x: ren(log, where, x, "value") | {"value": x.get("deger")}  # noqa: E731  (null stays null)
    special = {
        "source": lambda: src(log, where, v, d.get("olcum_profili"), cfg), "ts": lambda: ts(v), "key": lambda: key(v),
        "each": lambda: [_fn(log, where, f"table:{arg}", x, d, cfg) for x in v], "req": lambda: "R-" + v[2:],
        "table": lambda: {"name": v["ad"], "quantity": ren(log, where, v, "quantity")} if arg == "quantity"
        else ren(log, where, v, arg, cfg), "i18n": lambda: {"tr": v}, "value": lambda: val(v),
        "branch": lambda: v.replace("/karar/", "/decision/"), "triggers": lambda: [V["trigger"].get(x, x) for x in v],
        "origin": lambda: {"type": V["req_origin"].get(v, v)},
        "projects": lambda: [{"code": c} | ren(log, where, p, "project") for c, p in v.items()],
        "proposal": lambda: {"text": " — ".join(str(v[x]) for x in ("secim", "gerekce") if v.get(x))},
        "clearance": lambda: {V["task"][g]: {"lower": val(s["alt"]), "upper": val(s["ust"])}
                              for g, s in v.items() if g != "vida_gecisi"}}
    return special[kind]() if kind in special else V[fn].get(v, v)


def surec_config(old_root, out_dir, dry_run: bool = True) -> Log:
    """kurumlar → orgs/, profiller/uretim → machines/ (type print3d.fdm, G-30), profiller/olcum → instruments/."""
    guard(dry_run)
    old, out, log = Path(old_root), Path(out_dir), Log(kind="config")
    for f in sorted((old / "kurumlar").glob("*")):
        if (f := f / "kurum.yaml" if f.is_dir() else f).suffix == ".yaml" and f.exists():
            k = yamlio.read(f, {})
            rel = f"orgs/{k['kod']}.yaml"
            yamlio.write(out / rel, o := ren(log, rel, k, "org") | {"remote": k.get("repo")})
            log.need(rel, o, ("repo", "data_transfer"))
    for f in sorted((old / "profiller" / "uretim").glob("*.yaml")):
        p, rel = yamlio.read(f), f"machines/{f.stem}.yaml"
        vg = (p.get("bosluk") or {}).get("vida_gecisi") or {}
        m = ren(log, rel, p, "machine") | {"profile": ren(log, rel, p, "machine_profile") | {"screw_clearance": {
            "source": src(log, rel, vg.get("kaynak")), "table": vg.get("tablo")}}}
        if p.get("yontem") == "fdm":
            m["type"] = log.derive(rel, "type", "print3d.fdm", "machine_type")
        log.need(rel, m, ("type", "name"))
        yamlio.write(out / rel, m)
    for f in sorted((old / "profiller" / "olcum").glob("*.yaml")):
        p, rel = yamlio.read(f), f"instruments/{f.stem}.yaml"
        i = ren(log, rel, p, "instrument") | {"name": log.derive(rel, "name", p["ad"], "name_from_id")}
        if p.get("etiket") in V["instrument_kind"]:
            i["kind"] = log.derive(rel, "kind", V["instrument_kind"][p["etiket"]], "instrument_tag")
        log.need(rel, i, ("kind", "valid_for"))
        log.need(rel, i.get("valid_for", {}), ("critical_dimension", "form"), "valid_for/")
        yamlio.write(out / rel, i)
    yamlio.write(out / "migration.yaml", log.__dict__)
    return log


def _work(log, c, has_model):
    W, code, prof, pr = "work.yaml", c["kod"], load_profile("default@1"), c["profiller"]
    d = {"kind": "work", "schema_version": SV} | ren(log, W, c, "work") | {
        "org": log.derive(W, "org", code[:3], "code_parts"),
        "project": log.derive(W, "project", code[4:7], "code_parts"),
        "process": {"profile": log.derive(W, "process/profile", prof.ref, "old_process"), "stage": c["asama"],
                    "gates": c.get("kapilar") or log.derive(W, "process/gates", list(prof.classes[c["sinif"]]),
                                                            "class_gates"), "gate_status": {}},
        "profiles": {"manufacturing": pr["uretim"] if "@" in pr["uretim"] else pr["uretim"] + "@v0",
                     "instruments": [x.partition("@")[0] for x in pr.get("olcum") or []]}}
    for g, s in (c.get("kapi_durumu") or {}).items():
        d["process"]["gate_status"][g] = st = ren(log, f"{W}:{g}", s, "gate")
        log.need(W, st, [b for a, b in (("basladi", "started_at"), ("bitti", "finished_at")) if s.get(a)],
                 f"process/gate_status/{g}/", {"started_at": str(s.get("basladi")), "finished_at": str(s.get("bitti"))})
    if has_model:
        d["model"] = log.derive(W, "model", {"kind": "parametric", "entry": "model/model.py"}, "model_file")
    if (br := c.get("dallar") or {}).get("ana"):
        d["branches"] = {"main": f"{code}/main", "work": [f"{code}/work/" + br.get("is", "").rsplit("/", 1)[-1]]}
    log.need(W, d, ("purpose", "done_criterion", "opened_at", "work_type", "packages", "stdlib"), proposal={
        "work_type": "new_part" if has_model else None, "packages": ["mech", "print3d"],
        "opened_at": str(c["acilis"]) if c.get("acilis") else None})
    return d


def _decision(log, i, k, code, has_req):
    F, P = "decisions.yaml", f"{i}/"
    d = {"kind": "decision", "schema_version": SV, "work": code} | ren(log, f"kararlar.yaml:{k['no']}", k, "decision")
    d["mode"] = "provisional" if k.get("seviye") == "gecici" else log.derive(F, P + "mode", "hold", "old_hold")
    d["status"] = d.get("status") or log.derive(F, P + "status", "proposed", "old_unreviewed")
    if "requirement_effects" not in d and not has_req:
        d["requirement_effects"] = log.derive(F, P + "requirement_effects", [], "no_requirements")
    for j, (calc, h) in enumerate((k.get("dayanak") or {}).items()):
        if not HEX.match(str(h)):        # keeps "differs from the current result" (DECISION-01); old value in report
            h = log.derive(F, f"{P}basis/{j}/result_hash", hashlib.sha256(str(h).encode()).hexdigest()[:16], f"old:{h}")
        d.setdefault("basis", []).append({"calculation": calc, "result_hash": h})
        log.need(F, None, f"{P}basis/{j}/at")
    log.need(F, d, ["category", "options", "rationale", "opened_at", "requirement_effects"]
             + ["chosen", "approved_version"] * (d["status"] == "approved")
             + ["objection_until", "visual", "provisional"] * (d["mode"] == "provisional"), P,
             {"opened_at": str(k["tarih"]) if k.get("tarih") else None})
    return d


def _approvals(log, rows, code, cfg):
    (name, email), out, F = cfg.chief, [], "approvals.yaml"
    for a in rows:
        if (a.get("kim") or "-").split()[0].casefold() != name.split()[0].casefold():   # old onay.yetkili_mi
            log.dropped.append(f"onaylar.yaml:{a['kart']}@{a['zaman']}:{a.get('kim')}")
            continue
        P = f"{len(out)}/"
        card, _, row = a["kart"].partition("/")      # V-01/<param>: one row of the assumption list
        r = {"kind": "approval", "schema_version": SV, "work": code, "card": card, "row": row,
             "action": V["action"].get(a["karar"], a["karar"]),
             "role": log.derive(F, P + "role", "chief_engineer", "authorized"),
             "identity": log.derive(F, P + "identity", {"name": name, "email": email}, "chief_identity"),
             "at": ts(a["zaman"]), "approved_hash": a["ozet"], "migrated_from_hash": a["ozet"],
             "commit": a.get("commit"), "reason": (a.get("not") or "").strip()}
        out.append(r := {k: v for k, v in r.items() if v})
        log.need(F, r, ("commit", "signature", "channel", "at") + ("undoes",) * (r["action"] == "undo"), P)
    return out


def _calc(log, f, v, code):
    F, methods = f"records/calcs/{f.stem}.json", {(b["yontem"], b["dogruluk"]) for b in v.get("buyuklukler") or []}
    r = {"kind": "calculation", "schema_version": SV, "work": code, "type": "calculation", "title": f.stem} | ren(
        log, F, v, "calc") | ({"code": {"path": "calcs/" + Path(v["dosya"]).name}} if v.get("dosya") else {})
    r["result_hash"] = log.derive(F, "result_hash", result_hash(r), "old_result_summary")   # B5, wave 2 · B
    log.need(F, r, ("purpose", "method", "validity", "input_hash", "ran_at", "code"), proposal={
        "method": dict(zip(("name", "level"), *methods)) if len(methods) == 1 else None})
    log.need(F, r.get("code", {"commit": "-"}), "commit", "code/")
    for part, i, q in ((p, i, q) for p in ("inputs", "constants") for i, q in enumerate(r.get(p, []))):
        log.need(F, q["quantity"], "source", f"{part}/{i}/quantity/")
    for i, _ in enumerate(r.get("results", [])):
        log.need(F, None, f"results/{i}/uncertainty_note")
    return r


def _gap_card(log, code):
    tx = lambda k: {lang: c[k].format(n=len(log.gaps), code=code) for lang, c in catalogs().items() if k in c}  # noqa
    log.need(f"cards/{GAP_CARD}.yaml", None, "visuals")
    return {"kind": "card", "schema_version": SV, "id": GAP_CARD, "work": code, "key": "migration_gap",
            "type": "migration_gap", "level": "hold", "title": t("migrate.card.title", n=len(log.gaps), code=code),
            "explain": tx("migrate.card.explain"), "triggers": ["migration_gap"], "status": "open",
            "subject": {"refs": [{"kind": "file", "id": "migration", "path": "records/migration.yaml"}]},
            "if_approved": t("migrate.card.if_approved"), "if_rejected": t("migrate.card.if_rejected"),
            "recorded_as": t("migrate.card.recorded_as"), "opened_by": "system", "opened_at": clock.now()}


def surec_work(old_work, out_dir, config, dry_run: bool = True, old: dict | None = None) -> Log:
    """Old work folder → v1 files in `out_dir`; the old log is copied as is. `old` is the old-side snapshot
    (tests/migrate/old_probe.py): with it, an approval whose subject did not change gets the v1 hash (V5)."""
    guard(dry_run)
    s, out = Path(old_work), Path(out_dir)
    rd = lambda n, default=None: yamlio.read(s / n, default)  # noqa: E731
    c, req, mont = rd("calisma.yaml"), rd("istek-listesi.yaml", []), rd("montaj.yaml", {})
    code, log = c["kod"], Log(kind="work", code=c["kod"])
    docs = {"work.yaml": _work(log, c, (s / "model" / "model.py").exists()),
            "params.yaml": {p["ad"]: ren(log, f"params.yaml:{p['ad']}", p, "param", config)
                            for p in rd("params.yaml", [])},
            "fits.yaml": {"fits": [ren(log, f"gecmeler.yaml:{g['no']}", g, "fit") for g in rd("gecmeler.yaml", [])],
                          "flexes": [ren(log, f"montaj.yaml:{e['no']}", e, "flex")
                                     for e in mont.get("esnemeler") or []],
                          "tool_access": mont.get("takim_erisimi") or []},
            "decisions.yaml": [_decision(log, i, k, code, bool(req)) for i, k in enumerate(rd("kararlar.yaml", []))],
            "approvals.yaml": _approvals(log, rd("onaylar.yaml", []), code, config),
            "replies.yaml": [ren(log, "yanitlar.yaml", y, "reply") for y in rd("yanitlar.yaml", [])]}
    if req:
        docs["requirements.yaml"] = {"kind": "requirement_list", "schema_version": SV, "work": code, "items": [
            {"status": log.derive("requirements.yaml", f"items/{i}/status", "draft", "requirement_draft"),
             "open_question": r["metin"]} | ren(log, "istek-listesi.yaml", r, "requirement")
            for i, r in enumerate(req)]}
    for f in sorted((s / "kartlar").glob("*.yaml")):     # generated cards are rebuilt in memory; the rest keep state
        if not (k := yamlio.read(f)).get("uretilen"):
            d = {"kind": "card", "schema_version": SV, "work": code} | ren(log, f.name, k, "card")
            docs[f"cards/{f.name}"] = d
            log.need(f"cards/{f.name}", d, ("visuals", "opened_by", "opened_at", "explain", "triggers"))
    docs |= {f"records/calcs/{f.stem}.json": _calc(log, f, json.loads(f.read_text(encoding="utf-8")), code)
             for f in sorted((s / "kayit" / "hesaplar").glob("*.json"))}
    for a, b in ((a, b) for a, b in COPY.items() if (s / a).is_dir()):
        shutil.copytree(s / a, out / b, ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    for f in sorted((s / "hesaplar").glob("*.py")):     # Hesap → Calc names (contract with evidence, wave 2 · B)
        text = re.sub(r"\.(" + "|".join(M["calc_api"]) + r")\(", lambda m: f".{M['calc_api'][m[1]]}(", f.read_text())
        yamlio.write_text(out / "calcs" / f.name, re.sub(
            r"^(" + "|".join(M["calc_names"]) + r")\b", lambda m: M["calc_names"][m[1]], text, flags=re.M))
    docs[f"cards/{GAP_CARD}.yaml"] = _gap_card(log, code)
    for rel, d in docs.items():
        yamlio.write_text(out / rel, json.dumps(d, ensure_ascii=False, indent=1)) if rel.endswith(".json") \
            else yamlio.write(out / rel, d)
    yamlio.write(out / "records" / "migration.yaml", log.__dict__)
    rehash(out, log, config, old)
    yamlio.write(out / "records" / "migration.yaml", log.__dict__)
    return log


def new_side(root, cfg):
    """The v1 side of V4–V8 and the re-hash: view, model hooks, model, check results and cards (contracts: checks
    runner and mekanik.core.cards.generate, wave 2 · A; ModelHooks.build, mech, wave 2 · C)."""
    from mekanik.core.cards import generate
    from mekanik.core.checks.runner import run
    from mekanik.core.model.work import load_work
    from mekanik.plugins import registry

    view, hooks = load_work(root, cfg), registry().model_hooks()
    model = hooks.build(view) if hasattr(hooks, "build") else None
    res = run(view, model)
    return view, hooks, model, res, generate(view, res)


def rehash(out, log, cfg, old) -> None:
    """V5: an old approval whose subject did not change gets the v1 subject hash (mekanik.core.cards.approval,
    wave 2 · A); otherwise the old hash stays and the approval drops, as it did in surec."""
    try:
        from mekanik.core.cards.approval import digest, subject_values

        view, *_, cards = new_side(out, cfg)
    except (ImportError, MekanikError) as e:
        return log.pending.append({"step": "approved_hash", "reason": f"{type(e).__name__}: {e}"})
    rows, olds, new = yamlio.read(out / "approvals.yaml", []), {c["id"]: c for c in (old or {}).get("cards", [])}, {
        c.get("key"): c for c in cards}
    for a in rows:
        if (o := olds.get(a["card"])) and (n := new.get(key(o["key"]))):
            a["card"] = n["id"]
            if a["migrated_from_hash"] == o["subject_hash"]:
                a["approved_hash"] = digest(subject_values(view, n["subject"]))
    yamlio.write(out / "approvals.yaml", rows)
    log.pending += [] if old else [{"step": "approved_hash", "reason": "no old snapshot"}]
