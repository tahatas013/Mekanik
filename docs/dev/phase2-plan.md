# Faz 2 planı

Durum: çalışma belgesi · yazan rol: proje-muhendisi · başlangıç 2026-11-06 16:12 UTC (sistem saati) · baş mühendisin "başla" iletisiyle (T-25)

Faz 2'nin kapsamı ve ölçütleri mimari belgede (§17 Faz 2, 2.1–2.9) bağlayıcıdır. Bu belge iş sırasını, sahipleri ve sözleşmeleri verir. Faz 1 kılavuzunun kuralları (`docs/dev/phase1-guide.md` §1, §2, §8.1, §9) aynen geçerlidir. Çelişki olursa mimari belge kazanır.

## 1. Kapsam

| Parça | Ne | Ölçüt |
| --- | --- | --- |
| A | Panel kokpit: arka uç (FastAPI, REST + SSE) ve yeni ön yüz (Vite + TypeScript, çerçevesiz; eski düzen) birlikte; eklentiye MCP sunucusu, monitor, gelen kutusu (`mekanik agent send/stop`); gömülü oturum sekmesi (T-18a) | 2.1 (A1–A9, A11–A13; A10 Faz 4), 2.6, 2.8 |
| C | Tanımlama: iş türü, soru ağacı motoru, analiz, anlama özeti; G0 ön koşulu | 2.2 (C1–C6) |
| D | Soru politikası: DUR sınıflayıcısı, geçici karar yaşam döngüsü (itiraz, kapıda kabul, geri alma), aşama ölçüleri, eşik önerisi; kartların seviyesi politikadan (G-31 kalkar) | 2.3 (D1–D6) |
| E | Rapor akışı: `records/events.jsonl` (yalnız eklenir), görseller gerçek modelden ve önbellekli, önce–sonra, gün sonu özeti | 2.4 (E1–E5) |
| F | Güvence: CALC-03, CALC-04, REQ-01 (G4/G5), SOURCE-02, STDMAP-01, standart haritası; 30 vakalık tohumlanmış hata derlemi | 2.5 (F1 30/30, F3, F5, F8) |
| Taşıma | `mekanik migrate surec-work --apply` (§14.1); taşınan geçmiş kapıların MG-01 ile kapsanması | §14.4 Faz 2 |
| Kalanlar | `docs/later.md`'deki Faz 2 maddeleri (kalite kaydının alt ajan çıktısına bağlanması, değer girişinin imzalı yazılması, atölye ayarının korunması, S-002 vakası, şema sıkılığının boşaltılması → şema 1.1, doctor sürüm denetimi, `gate back`, `object`) | — |
| Dil | EN kataloğu panel + CLI için %100 | 2.7 |

## 2. Dalgalar

| Dalga | İş | Sahibi | Bağımlılık |
| --- | --- | --- | --- |
| 2.0 | Bu plan, `phase-2` dalı (G-32) | proje mühendisi | — |
| 2.1 · P | Politika (D) + gates/decisions/cards değişiklikleri + CALC-03/04, REQ-01, SOURCE-02 + `object`, `gate back` | ajan P | — |
| 2.1 · I | Tanımlama (C) + standart haritası (F8, STDMAP-01) | ajan I | — |
| 2.1 · S | Akış (E): events.jsonl, akış satırları, görsel önbelleği, önce–sonra, gün sonu özeti | ajan S | — |
| 2.1 · M | Taşıma `--apply` + MG-01 kapsaması + `docs/later.md` güvenlik kalanları + S-002 | ajan M | — |
| 2.2 | Panel arka ucu + MCP sunucusu + gelen kutusu + monitor | ajan B | 2.1 |
| 2.3 | Panel ön yüzü + gömülü oturum sekmesi + eski 17 e2e testi | ajan U | 2.2 |
| 2.4 | F1 derlemi (30 vaka), şema 1.1 (sıkılık listesi boşalır), EN kataloğu %100 | ajan Q | 2.1 |
| 2.5 | Ölçüm, iki bağımsız kalite incelemesi, baş mühendisin makinesinde panel denetimi | proje mühendisi | hepsi |

## 3. Dosya sahipliği (dalga 2.1)

Aynı dosyayı iki ajan yazmaz.

| Sahip | Yazdığı yerler |
| --- | --- |
| P | `src/mekanik/core/policy/**`, `core/decisions/**`, `core/process/gates.py`, `core/cards/**` (seviye ve geçici karar kartı), `core/checks/builtin/` altında yeni dosyalar (CALC-03/04, REQ-01, SOURCE-02), `stdlib/policy/**`, `stdlib/rules/core.yaml` (yalnız kendi kuralları), `tr.policy.yaml` |
| I | `src/mekanik/core/intake/**`, `core/stdmap/**`, `stdlib/work_types/**`, `stdlib/questions/**`, `stdlib/items/**`, `stdlib/rules/intake.yaml`, `tr.intake.yaml`, `tr.stdmap.yaml`, `packages/print3d/src/mekanik_print3d/questions/` (yalnız `print3d.basics` ağacı) |
| S | `src/mekanik/core/report/**`, `core/process/step.py` (yalnız akış olayını yayma ve görsel önbelleği), `tr.report.yaml` |
| M | `src/mekanik/migrate/**`, `core/cards/signature.py`, `core/process/chief.py` (yalnız `value` imzası), `core/quality/**` (alt ajan çıktısına bağlama), `src/mekanik/agent/**` (SubagentStop yakalama), `tests/cases/S-002/**` |

Ortak modüller (`core/model`, `core/checks/{result,runner}.py`, `plugins`, `config`, `core/store/git.py`, `core/i18n/__init__.py`) proje mühendisinindir; değişiklik gerekirse raporda öner. Şemalara yalnız isteğe bağlı alan ekle; örnekleri güncelle.

## 4. Sözleşmeler

- **Akış olayı:** `mekanik.core.report.stream.emit(root, kind, **data) -> dict` (S yazar). `records/events.jsonl`'a `stream-event` şemasıyla bir satır ekler. P (geçici karar), I (soru, anlama özeti) ve S'nin kendi `step`'i bunu çağırır. S işini bitirene kadar P ve I, imzası bu olan küçük bir yerel sarmalayıcıyla çalışır ve raporda belirtir.
- **Kart seviyesi:** P'nin `policy.level(view, card) -> "hold" | "provisional" | "witness"` fonksiyonu kart üretiminde kullanılır. DUR kategorisindeki hiçbir şey geçici olamaz (D1, C6).
- **G0 ön koşulu:** I, anlama özeti onaylanmadan tasarım adımını durduran kontrolü ve STDMAP-01'i `CheckSpec` olarak kaydeder. P bunlar için `gates.py`'ye dokunmaz; kapı listesi maddeleri `stdlib/process/default@1.yaml`'daki `gate_items`'a P ekler.
- **Bütçe (2.9, onaylı):** çekirdeğe eklenen tanımlama + politika + akış ≤ 3 000 satır. Bölüşüm: P 1 200, I 1 100, S 700. M'nin değişiklikleri Faz 1 modüllerinin içinde ve ≤ 400 satır. Panel arka ucu ≤ 1 845, `panel-ui/` TS+CSS ≤ 3 280 (dalga 2.2–2.3).
- **Testler:** her ölçüt satırının bir testi olur; docstring `"""2.x: <ölçüt kimliği> — …"""`. Sahte katalog testi (`tests/tools/test_pseudo_i18n.py`) yeni testleri de kapsamalı.

## 5. Proje mühendisinin geçici kararları

- **G-32 · Dal.** Faz 2 `phase-2` dalında; çıkışta baş mühendis onayıyla `main`'e birleşir.
- **G-33 · Ön yüz.** Vite + TypeScript, çerçevesiz (eski panelin düzeni; §19.1 "ön yüzde React yok"). Derlenmiş çıktı tekerleğe girer; Node sürümü sabittir ve `mekanik doctor` denetler.
- **G-34 · Eski panel.** Eski panel, yeni panel eşitlik listesini (2.8) geçene kadar çalışır. Kapatılması senin kararındır; Faz 2 sonunda sorarım.

## 6. Senden gerekecekler (yalnız bunlar)

- Faz 2 sonunda: yeni paneli kendi makinende açıp eşitlik listesini görmek, eski panelin kapatılması kararı (G-34) ve kapı onayı.
- Gerçek bir eski çalışmanın `--apply` ile taşınması yalnız sen istersen (G-23).
