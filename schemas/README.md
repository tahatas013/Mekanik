# mekanik v1 JSON şemaları

Kesinleşen v1 şemaları · Faz 1 · yazan rol: proje-muhendisi. Faz 0 taslağı `docs/design/schemas/`'ta kayıt olarak durur; bağlayıcı olanlar buradakilerdir.

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
| `approval` (ek, kalite incelemesi sonrası) | Onay kaydı: yalnız baş mühendis rolü, imza zorunlu | `approvals.yaml` |
| `error-record` (ek) | Hata kaydı (8D); regresyon vakası zorunlu | `errors/H-nnn.yaml` (kurum reposu) |
| `quality-review` (ek) | Kalite incelemesi; bulgu gerekçeyle ve regresyon sorusuyla kapanır | `records/quality/*.yaml` |
| `params` (Faz 1) | Parametreler: ad → `common#/$defs/param` (kaynak isteğe bağlı; eksikliği SOURCE-01 ENGEL'idir, G-25) | `params.yaml` |
| `replies` (Faz 1) | Ekibin yorum yanıtları; yalnız eklenir (G-29) | `replies.yaml` |

**Faz 1 durumu (ölçüt 1.6).** Faz 1'de kullanılan 13 şema kesinleşti: `work`, `params`, `requirement`, `card`, `decision`, `evidence`, `calculation`, `config`, `approval`, `replies`, `error-record`, `quality-review`, `agent-run` (ve ortak `common`). Faz 1 değişiklikleri geriye uyumludur: isteğe bağlı alanlar; yeni tanımlar (`param`, `params`, `replies`); DUR kategorilerine iki değer (T-23); kart konusunun paket anahtarlarına açılması; hesap şemasındaki koşulların yalnız alan varken işlemesi (düzeltme). `x-schema-version` 1.0.0'da kaldı. v1'de zorunlu olup eski sistemde zorunlu olmayan alanlar Faz 1'de yükleyicide uyarıdır: liste `stdlib/strictness/phase1.yaml` (G-27); Faz 2'de (`1.1`) liste boşalır. Diğer şemalar ait oldukları fazda kesinleşir (architecture.md §17).

## Doğrulama

```bash
uv run python tests/core/schema_examples.py      # ya da: uv run pytest tests/core/test_cleanliness.py tests/core -k schema
```

Araç üç şeyi denetler:

1. 22 şemanın tamamı meta şemaya uyar.
2. 21 örneğin her biri kendi şemasından geçer.
3. Bilerek bozulmuş 50 örneğin her biri kalır. Bunlar sistemin temel kurallarını sınar:
   - kaynaksız sayı; varsayım ya da türetilmiş sabit;
   - kritik hesapta ikinci yöntem yok; alan dışı sonucun "ok" görünmesi; placard'sız dış değerleme; belirsizlik beyanı yok;
   - görselsiz kart; DUR kategorisinin geçici karar olması; "inceleme bekliyor" kipi; alternatifsiz geçici karar; isteklere etkisi olmayan karar;
   - yalnız ölçümsüz gözleme dayanan karar;
   - baş mühendis dışında birinin onayı; imzasız onay;
   - kanıtsız "karşılandı"; açık YÜKSEK bulguyla kapı kartı;
   - kanıtsız ve kalite incelemesiz tik; açık karşılığı aranmamış paralı standart; test yöntemi olmayan madde;
   - sayısız onaylı zorunlu istek;
   - "neden önemli" ya da varsayılanı olmayan soru; varsayımla geçen DUR sorusu;
   - işlemde kaynaksız ölçü; kayıtsız okuma parametreleri;
   - eksik DUR kategorileri; v1'de olmayan başsız kip; veri aktarım kararı olmayan kurum;
   - Türkçe dal adı; kayıtta kimlik bilgisi;
   - regresyon vakasız hata kaydı; gerekçesiz kapatılan bulgu.

2026-11-06 Faz 1 sonucu: `SONUÇ: TEMİZ` (22 şema, 21 geçen örnek, 50 kalan bozuk örnek).

## Şemaların kapsamadığı kurallar

Bazı kurallar tek bir belgeye bakarak denetlenemez; çekirdek kontrolleri bunlara bakar (ana belge §4.7):

- bir geçmenin iki tarafının bağımsız sayı olması (GECME-01);
- dayanak hesabın özetinin değişmesi (KARAR-01);
- aynı büyüklüğün iki hesapta farklı çıkması (HESAP-01);
- onay özetinin bayatlaması;
- G4/G5'te zorunlu isteklerin hepsinin "karşılandı" olması.
