# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schema and example checker for schemas/v1 (old docs/design/schemas/check_examples.py).

Run:  uv run python tests/core/schema_examples.py   (test_model.py::test_schema_examples_clean runs it too)

1. Every schema conforms to the Draft 2020-12 meta-schema.
2. examples/<name>.json validates against <name>.schema.json.
3. Deliberately broken examples must fail: the schema passes what is right and fails what is wrong.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2] / "schemas" / "v1"


def load() -> tuple[dict[str, dict], Registry]:
    schemas = {p.name.removesuffix(".schema.json"): json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(ROOT.glob("*.schema.json"))}
    reg = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas.values())
    return schemas, reg


def validator(schema: dict, reg: Registry) -> Draft202012Validator:
    return Draft202012Validator(schema, registry=reg, format_checker=FormatChecker())


def broken(ex: dict[str, dict]) -> list[tuple[str, str, object]]:
    """(schema, reason, example): every one must FAIL."""
    out = []

    def add(name, reason, edit):
        w = copy.deepcopy(ex[name])
        edit(w)
        out.append((name, reason, w))

    add("calculation", "kaynaksız girdi", lambda w: w["inputs"][0]["quantity"].pop("source"))
    add("calculation", "varsayım sabit", lambda w: w["constants"][0]["quantity"].update(source="assumption"))
    add("calculation", "kritik hesapta ikinci yöntem yok", lambda w: w.pop("cross_check"))
    add("calculation", "alan dışı ama sonuç 'ok'", lambda w: w["validity"].update(in_domain=False))
    add("card", "görselsiz kart", lambda w: w.update(visuals=[]))
    add("card", "DUR kartında kategori yok", lambda w: w.pop("stop_category"))
    add("decision", "DUR kategorisi geçici karar olamaz", lambda w: w.update(mode="provisional"))
    add("provisional-decision", "malzeme geçici karar olamaz", lambda w: w.update(category="material"))
    add("provisional-decision", "alternatifsiz geçici karar", lambda w: w.update(options=w["options"][:1]))
    add("decision", "yalnız ölçümsüz gözleme dayanan karar",
        lambda w: (w.update(observations=[{"text": "uçuşta sağa yattı", "measured": False}]), w.pop("basis")))
    add("standard-item", "kalite incelemesiz ve kanıtsız tik",
        lambda w: w.update(tick={"checked": True, "at": "2026-11-06T10:00:00+03:00"}))
    add("standard-item", "paralı standartta açık karşılık araması yok", lambda w: w.pop("open_equivalent"))
    add("requirement", "onaylı zorunlu istek sayısız", lambda w: w["items"][0].pop("criterion"))
    add("question-tree", "'neden önemli' yok", lambda w: w["nodes"][0].pop("why"))
    add("question-tree", "cevapsız varsayılan yok", lambda w: w["nodes"][0].pop("default_if_unanswered"))
    add("model-oplist", "işlemde kaynaksız ölçü",
        lambda w: w["ops"][0]["params"].update(depth={"value": 6.0, "unit": "mm"}))
    add("config", "kesin DUR kategorileri eksik", lambda w: w["policy"].update(stop_categories=["material"]))
    add("config", "v1'de başsız kip yok", lambda w: w["agent"].update(mode="headless"))
    add("work", "çalışma kodu biçimi", lambda w: w.update(code="ORN-BRK-3"))
    add("experiment", "geçersiz denemenin nedeni yok", lambda w: w["runs"][1].pop("invalid_reason"))
    add("evidence", "içerik özetsiz kanıt", lambda w: w["record"].pop("hash"))
    add("stream-event", "görselsiz geçici karar satırı", lambda w: w.update(visuals=[]))
    add("intake-summary", "onay kaydı olmadan onaylı anlama özeti", lambda w: w.update(status="approved"))
    add("intake-summary", "görselsiz analiz sonucu", lambda w: w["analyses"][0].update(visuals=[]))
    add("agent-run", "kayıtta kimlik bilgisi alanı", lambda w: w["adapter"].update(api_key="sk-..."))
    add("decision", "v1'de 'inceleme bekliyor' kipi yok", lambda w: w.update(mode="review", category="design_detail"))
    out.append(("decision", "geçici karar tek seçenekle (karar şemasıyla)",
                {**copy.deepcopy(ex["provisional-decision"]), "options": ex["provisional-decision"]["options"][:1]}))
    add("decision", "isteklere etkisi yok", lambda w: w.pop("requirement_effects"))
    add("decision", "onay olayını tekniker yazmış", lambda w: w["history"][1].update(role="technician"))
    add("card", "kart dizisinde proje mühendisi onayı", lambda w: w.update(thread=[
        {"at": "2026-11-04T11:00:00+03:00", "role": "project_engineer", "kind": "approve", "text": "onaylıyorum"}]))
    add("card", "kapı kartında kanıtsız 'karşılandı'", lambda w: w.update(
        type="gate", id="O-G2", requirement_table=[{"requirement": "R-01", "status": "met"}]))
    add("card", "açık YÜKSEK bulguyla kapı kartı", lambda w: (w.update(
        type="gate", id="O-G2", requirement_table=[{"requirement": "R-01", "status": "awaiting_evidence"}]),
        w["quality"].update(open_high=3)))
    add("requirement", "kanıtsız 'karşılandı' değerlendirmesi",
        lambda w: w["items"][0].update(evaluation={"status": "met", "at": "G3"}))
    add("standard-item", "çalışma maddesinde test yöntemi yok", lambda w: w.pop("test_method"))
    add("calculation", "sonuçta belirsizlik beyanı yok", lambda w: w["results"][0].pop("uncertainty_note"))
    add("calculation", "dış değerlemede placard yok", lambda w: w["validity"].update(zone="limits"))
    add("calculation", "türetilmiş sabit", lambda w: w["constants"][0].update(
        quantity={"value": 40.0, "unit": "MPa", "source": "derived", "formula": "x"}))
    add("question-tree", "DUR sorusu varsayımla geçiyor", lambda w: w["nodes"][0].update(
        default_if_unanswered={"value": 5000, "source": "assumption", "opens_card": False}))
    add("work", "Türkçe dal adı", lambda w: w["branches"].update(main="ORN-BRK-03/ana"))
    add("model-oplist", "okuma parametreleri kayıtsız", lambda w: w["base"]["import"].pop("read_params"))
    add("config", "kurumun veri aktarım kararı yok", lambda w: w["organizations"][0].pop("data_transfer"))
    add("approval", "onayı baş mühendis dışında biri vermiş", lambda w: w.update(role="project_engineer"))
    add("approval", "imzasız onay", lambda w: w.pop("signature"))
    add("error-record", "regresyon vakası olmayan hata kaydı", lambda w: w.pop("regression_case"))
    add("quality-review", "gerekçesiz kapatılan bulgu", lambda w: w["findings"][0].pop("closure"))
    # Phase 1 (params.yaml, replies.yaml, approval row)
    add("params", "bilinmeyen kaynak etiketi", lambda w: next(iter(w.values())).update(source="tahmin"))
    add("params", "ASCII olmayan parametre adı", lambda w: w.update({"Delik-Çap": {"value": 1.0, "unit": "mm"}}))
    add("params", "formülsüz türetilen değer", lambda w: w.update(x={"value": None, "unit": "mm", "source": "derived"}))
    add("replies", "yorum zamanı olmayan yanıt", lambda w: w[0].pop("comment_at"))
    add("approval", "satır adı ASCII değil", lambda w: w.update(row="Et Kalınlığı"))
    add("work", "rolsüz sıradaki iş", lambda w: w["next_step"].pop("role"))
    add("replies", "commit kısaltması değil", lambda w: w[0].update(commit="HEAD"))
    return out


def main() -> int:
    schemas, reg = load()
    errors = 0
    for s in schemas.values():
        Draft202012Validator.check_schema(s)
    print(f"meta şema: {len(schemas)} şema geçerli")
    ex: dict[str, object] = {}
    for name, s in schemas.items():
        if name == "common":
            continue
        path = ROOT / "examples" / f"{name}.json"
        if not path.exists():
            print(f"EKSİK örnek: {path.name}")
            errors += 1
            continue
        ex[name] = json.loads(path.read_text(encoding="utf-8"))
        found = sorted(validator(s, reg).iter_errors(ex[name]), key=lambda e: list(map(str, e.path)))
        if found:
            errors += 1
            print(f"KALDI (geçmeliydi) {name}:")
            for e in found[:5]:
                print(f"   {'/'.join(map(str, e.path))}: {e.message[:160]}")
        else:
            print(f"geçti  {name}")
    for name, reason, w in broken(ex):
        if validator(schemas[name], reg).is_valid(w):
            errors += 1
            print(f"GEÇTİ (kalmalıydı) {name}: {reason}")
        else:
            print(f"kaldı  {name}: {reason}")
    print("SONUÇ:", "TEMİZ" if errors == 0 else f"{errors} hata")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
