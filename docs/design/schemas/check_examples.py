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

    w = copy.deepcopy(ornek["config"]); w["agent"]["auth"] = "api_key"
    out.append(("config", "API anahtarında bütçe sınırı yok", w))

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
