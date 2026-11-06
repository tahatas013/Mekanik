# mekanik v1 JSON şemaları

Faz 0 taslağı · yazan rol: proje-muhendisi · durum: inceleme bekliyor

Şemalar JSON Schema Draft 2020-12 ile yazıldı. Her şemanın `$id`'si `urn:mekanik:schema:v1:<ad>` biçimindedir ve sürümü `x-schema-version` alanında durur (şimdilik `1.0.0`). Her veri belgesi `kind` ve `schema_version` (`1.<alt>`) alanlarını taşır.

## Sürüm kuralı

- **Alt sürüm** (`1.0` → `1.1`): yalnız isteğe bağlı alan eklenir. Eski belgeler doğrulanmaya devam eder.
- **Ana sürüm** (`v1` → `v2`): alan kaldırılır, adı ya da anlamı değişir. Çekirdek her `kind` için bir göç betiği (migrator) taşır: `v1 → v2`. Göç ayrı bir dalda yapılır ve sayı korunumu denetiminden geçer (ana belge §14).
- Paket profil türleri (ör. `print3d.fdm_printer`) kendi şemalarını paketle birlikte taşır ve paket sürümüyle sürümlenir.

## Dosyalar

| Şema | Ne | Nerede durur |
| --- | --- | --- |
| `common` | Ortak tanımlar: kaynaklı değer, kaynak etiketi, rol, başvuru, kimlik desenleri, DUR kategorileri | — |
| `work` | Çalışma | `<proje>/<kod>/work.yaml` |
| `work-type` | İş türü (tanımlamanın ilk adımı) | çekirdek verisi, paketler |
| `requirement` | İstek listesi | `requirements.yaml` |
| `question-tree` | Soru ağacı | paketler |
| `card` | Kart | `cards/<id>.yaml` |
| `decision` | Karar | `decisions.yaml` |
| `provisional-decision` | Geçici karar (kararın daraltılmışı) | `decisions.yaml` |
| `evidence` | Kanıt | `evidence.yaml` |
| `calculation` | Hesap ve analiz kaydı | `records/calcs/<ad>.json` |
| `experiment` | Deney | `experiments/<id>.yaml` |
| `model-oplist` | Model işlem listesi | `model/ops.yaml` |
| `standard-item` | Standart haritası maddesi (çalışmada ve kütüphanede) | `stdmap.yaml`, `stdlib/items/` |
| `config` | Atölye ayarı | `~/.config/mekanik/config.yaml` |
| `agent-run` (ek) | Ajan çalıştırması (A) | `~/.local/state/mekanik/runs/` |
| `stream-event` (ek) | Akış olayı (E) | `records/events.jsonl` |
| `intake-summary` (ek) | Anlama özeti (C) | `intake/summary.yaml` |

## Doğrulama

```bash
uv run --no-project --python 3.12 --with jsonschema --with rfc3339-validator python docs/design/schemas/check_examples.py
```

Araç üç şeyi denetler:

1. 17 şemanın tamamı meta şemaya uyar.
2. 16 örneğin her biri kendi şemasından geçer.
3. Bilerek bozulmuş 25 örneğin her biri kalır. Bunlar sistemin temel kurallarını sınar: kaynaksız sayı, varsayım sabit, kritik hesapta ikinci yöntem yok, alan dışı sonucun "ok" görünmesi, görselsiz kart, DUR kategorisinin geçici karar olması, alternatifsiz geçici karar, yalnız ölçümsüz gözleme dayanan karar, kanıtsız ve kalite incelemesiz tik, açık karşılığı aranmamış paralı standart, sayısız onaylı zorunlu istek, "neden önemli" ya da varsayılanı olmayan soru, işlemde kaynaksız ölçü, kesin DUR kategorilerinin eksik olması, bütçe sınırsız API anahtarı, kayıtta kimlik bilgisi.

2026-11-06 sonucu: `SONUÇ: TEMİZ` (17 şema, 16 geçen örnek, 25 kalan bozuk örnek).

## Şemaların kapsamadığı kurallar

Bazı kurallar tek bir belgeye bakarak denetlenemez; çekirdek kontrolleri bunlara bakar (ana belge §4.7):

- bir geçmenin iki tarafının bağımsız sayı olması (GECME-01);
- dayanak hesabın özetinin değişmesi (KARAR-01);
- aynı büyüklüğün iki hesapta farklı çıkması (HESAP-01);
- onay özetinin bayatlaması;
- G4/G5'te zorunlu isteklerin hepsinin "karşılandı" olması.
