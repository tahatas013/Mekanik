"""Belge doğrulama aracı (uygulama kodu değil): v1 şemalarını ve örnekleri denetler.

Çalıştırma:  uv run --with jsonschema --with rfc3339-validator python docs/design/schemas/check_examples.py

1. Her şema Draft 2020-12 meta şemasına uyar.
2. examples/<ad>.json, <ad>.schema.json ile doğrulanır ve geçmelidir.
3. Bilerek bozulmuş örnekler (NEGATIVE) kalmalıdır: kontrol hem doğruyu geçirmeli hem yanlışı kaldırmalı.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

KOK = Path(__file__).resolve().parent / "v1"


def yukle() -> tuple[dict[str, dict], Registry]:
    semalar = {p.name.removesuffix(".schema.json"): json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(KOK.glob("*.schema.json"))}
    kayit = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in semalar.values())
    return semalar, kayit


def dogrulayici(sema: dict, kayit: Registry) -> Draft202012Validator:
    return Draft202012Validator(sema, registry=kayit, format_checker=FormatChecker())


def bozuk_ornekler(ornek: dict[str, dict]) -> list[tuple[str, str, dict]]:
    """(şema, neden, örnek): hepsi KALMALI."""
    out = []

    w = copy.deepcopy(ornek["calculation"]); del w["inputs"][0]["quantity"]["source"]
    out.append(("calculation", "kaynaksız girdi", w))

    w = copy.deepcopy(ornek["calculation"]); w["constants"][0]["quantity"]["source"] = "assumption"
    out.append(("calculation", "varsayım sabit", w))

    w = copy.deepcopy(ornek["calculation"]); del w["cross_check"]
    out.append(("calculation", "kritik hesapta ikinci yöntem yok", w))

    w = copy.deepcopy(ornek["calculation"]); w["validity"]["in_domain"] = False
    out.append(("calculation", "alan dışı ama sonuç 'ok'", w))

    w = copy.deepcopy(ornek["card"]); w["visuals"] = []
    out.append(("card", "görselsiz kart", w))

    w = copy.deepcopy(ornek["card"]); del w["stop_category"]
    out.append(("card", "DUR kartında kategori yok", w))

    w = copy.deepcopy(ornek["decision"]); w["mode"] = "provisional"
    out.append(("decision", "DUR kategorisi geçici karar olamaz", w))

    w = copy.deepcopy(ornek["provisional-decision"]); w["category"] = "material"
    out.append(("provisional-decision", "malzeme geçici karar olamaz", w))

    w = copy.deepcopy(ornek["provisional-decision"]); w["options"] = w["options"][:1]
    out.append(("provisional-decision", "alternatifsiz geçici karar", w))

    w = copy.deepcopy(ornek["decision"]); w["observations"] = [{"text": "uçuşta sağa yattı", "measured": False}]; del w["basis"]
    out.append(("decision", "yalnız ölçümsüz gözleme dayanan karar", w))

    w = copy.deepcopy(ornek["standard-item"]); w["tick"] = {"checked": True, "at": "2026-11-06T10:00:00+03:00"}
    out.append(("standard-item", "kalite incelemesiz ve kanıtsız tik", w))

    w = copy.deepcopy(ornek["standard-item"]); del w["open_equivalent"]
    out.append(("standard-item", "paralı standartta açık karşılık araması yok", w))

    w = copy.deepcopy(ornek["requirement"]); del w["items"][0]["criterion"]
    out.append(("requirement", "onaylı zorunlu istek sayısız", w))

    w = copy.deepcopy(ornek["question-tree"]); del w["nodes"][0]["why"]
    out.append(("question-tree", "'neden önemli' yok", w))

    w = copy.deepcopy(ornek["question-tree"]); del w["nodes"][0]["default_if_unanswered"]
    out.append(("question-tree", "cevapsız varsayılan yok", w))

    w = copy.deepcopy(ornek["model-oplist"]); w["ops"][0]["params"]["depth"] = {"value": 6.0, "unit": "mm"}
    out.append(("model-oplist", "işlemde kaynaksız ölçü", w))

    w = copy.deepcopy(ornek["config"]); w["policy"]["stop_categories"] = ["material"]
    out.append(("config", "kesin DUR kategorileri eksik", w))

    w = copy.deepcopy(ornek["config"]); w["agent"]["mode"] = "headless"; w["agent"]["auth"] = "provider"
    out.append(("config", "başsız kipte (sağlayıcıyla) bütçe sınırı yok", w))

    w = copy.deepcopy(ornek["work"]); w["code"] = "ORN-BRK-3"
    out.append(("work", "çalışma kodu biçimi", w))

    w = copy.deepcopy(ornek["experiment"]); del w["runs"][1]["invalid_reason"]
    out.append(("experiment", "geçersiz denemenin nedeni yok", w))

    w = copy.deepcopy(ornek["evidence"]); del w["record"]["hash"]
    out.append(("evidence", "içerik özetsiz kanıt", w))

    w = copy.deepcopy(ornek["stream-event"]); w["visuals"] = []
    out.append(("stream-event", "görselsiz geçici karar satırı", w))

    w = copy.deepcopy(ornek["intake-summary"]); w["status"] = "approved"
    out.append(("intake-summary", "onay kaydı olmadan onaylı anlama özeti", w))

    w = copy.deepcopy(ornek["intake-summary"]); w["analyses"][0]["visuals"] = []
    out.append(("intake-summary", "görselsiz analiz sonucu", w))

    w = copy.deepcopy(ornek["agent-run"]); w["adapter"]["api_key"] = "sk-..."
    out.append(("agent-run", "kayıtta kimlik bilgisi alanı", w))

    # Kalite incelemesi (KM bulguları) sonrası eklenenler
    w = copy.deepcopy(ornek["decision"]); w["mode"] = "review"; w["category"] = "design_detail"
    out.append(("decision", "v1'de 'inceleme bekliyor' kipi yok", w))

    w = copy.deepcopy(ornek["provisional-decision"]); w["options"] = w["options"][:1]
    out.append(("decision", "geçici karar tek seçenekle (karar şemasıyla)", w))

    w = copy.deepcopy(ornek["decision"]); del w["requirement_effects"]
    out.append(("decision", "isteklere etkisi yok", w))

    w = copy.deepcopy(ornek["decision"]); w["history"][1]["role"] = "technician"
    out.append(("decision", "onay olayını tekniker yazmış", w))

    w = copy.deepcopy(ornek["card"]); w["thread"] = [{"at": "2026-11-04T11:00:00+03:00", "role": "project_engineer", "kind": "approve", "text": "onaylıyorum"}]
    out.append(("card", "kart dizisinde proje mühendisi onayı", w))

    w = copy.deepcopy(ornek["card"]); w.update({"type": "gate", "id": "O-G2", "requirement_table": [{"requirement": "R-01", "status": "met"}]})
    out.append(("card", "kapı kartında kanıtsız 'karşılandı'", w))

    w = copy.deepcopy(ornek["card"]); w.update({"type": "gate", "id": "O-G2", "requirement_table": [{"requirement": "R-01", "status": "awaiting_evidence"}]}); w["quality"]["open_high"] = 3
    out.append(("card", "açık YÜKSEK bulguyla kapı kartı", w))

    w = copy.deepcopy(ornek["requirement"]); w["items"][0]["evaluation"] = {"status": "met", "at": "G3"}
    out.append(("requirement", "kanıtsız 'karşılandı' değerlendirmesi", w))

    w = copy.deepcopy(ornek["standard-item"]); del w["test_method"]
    out.append(("standard-item", "çalışma maddesinde test yöntemi yok", w))

    w = copy.deepcopy(ornek["calculation"]); del w["results"][0]["uncertainty_note"]
    out.append(("calculation", "sonuçta belirsizlik beyanı yok", w))

    w = copy.deepcopy(ornek["calculation"]); w["validity"]["zone"] = "limits"
    out.append(("calculation", "dış değerlemede placard yok", w))

    w = copy.deepcopy(ornek["calculation"]); w["constants"][0]["quantity"] = {"value": 40.0, "unit": "MPa", "source": "derived", "formula": "x"}
    out.append(("calculation", "türetilmiş sabit", w))

    w = copy.deepcopy(ornek["question-tree"]); w["nodes"][0]["default_if_unanswered"] = {"value": 5000, "source": "assumption", "opens_card": False}
    out.append(("question-tree", "DUR sorusu varsayımla geçiyor", w))

    w = copy.deepcopy(ornek["work"]); w["branches"]["main"] = "ORN-BRK-03/ana"
    out.append(("work", "Türkçe dal adı", w))

    w = copy.deepcopy(ornek["model-oplist"]); del w["base"]["import"]["read_params"]
    out.append(("model-oplist", "okuma parametreleri kayıtsız", w))

    w = copy.deepcopy(ornek["config"]); del w["organizations"][0]["data_transfer"]
    out.append(("config", "kurumun veri aktarım kararı yok", w))

    w = copy.deepcopy(ornek["approval"]); w["role"] = "project_engineer"
    out.append(("approval", "onayı baş mühendis dışında biri vermiş", w))

    w = copy.deepcopy(ornek["approval"]); del w["signature"]
    out.append(("approval", "imzasız onay", w))

    w = copy.deepcopy(ornek["error-record"]); del w["regression_case"]
    out.append(("error-record", "regresyon vakası olmayan hata kaydı", w))

    w = copy.deepcopy(ornek["quality-review"]); del w["findings"][0]["closure"]
    out.append(("quality-review", "gerekçesiz kapatılan bulgu", w))

    w = copy.deepcopy(ornek["config"]); w["agent"]["mode"] = "headless"; w["agent"]["auth"] = "subscription"; w["agent"]["max_budget_usd"] = 5
    out.append(("config", "başsız kipte abonelik", w))

    w = copy.deepcopy(ornek["config"]); w["agent"]["mode"] = "headless"; w["agent"]["auth"] = "api_key"
    out.append(("config", "başsız kipte bütçe sınırı yok", w))
    return out


def main() -> int:
    semalar, kayit = yukle()
    hata = 0
    for ad, s in semalar.items():
        Draft202012Validator.check_schema(s)
    print(f"meta şema: {len(semalar)} şema geçerli")

    ornek: dict[str, dict] = {}
    for ad, s in semalar.items():
        if ad == "common":
            continue
        yol = KOK / "examples" / f"{ad}.json"
        if not yol.exists():
            print(f"EKSİK örnek: {yol.name}"); hata += 1; continue
        ornek[ad] = json.loads(yol.read_text(encoding="utf-8"))
        hatalar = sorted(dogrulayici(s, kayit).iter_errors(ornek[ad]), key=lambda e: list(e.path))
        if hatalar:
            hata += 1
            print(f"KALDI (geçmeliydi) {ad}:")
            for e in hatalar[:5]:
                print(f"   {'/'.join(map(str, e.path))}: {e.message[:160]}")
        else:
            print(f"geçti  {ad}")

    for ad, neden, w in bozuk_ornekler(ornek):
        if dogrulayici(semalar[ad], kayit).is_valid(w):
            hata += 1
            print(f"GEÇTİ (kalmalıydı) {ad}: {neden}")
        else:
            print(f"kaldı  {ad}: {neden}")
    print("SONUÇ:", "TEMİZ" if hata == 0 else f"{hata} hata")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())
