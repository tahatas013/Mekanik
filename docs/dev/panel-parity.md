# Panel eşitlik listesi (ölçüt 2.8)

Durum: çalışma belgesi · yazan rol: tasarım mühendisi (ajan B, dalga 2.2) · kaynak: Ek B §4 (eski `panel/backend/surec_panel/*.py`, 28 uç nokta) ve `testler/test_panel_e2e.py` (17 test)

Her eski uç noktanın v1 karşılığı ya da gerekçeli kaldırılışı. Yollar `docs/dev/panel-api.md`'deki sözleşmeyle aynıdır; `W` = `/api/works/{code}`. "Test" sütunu arka uç testini gösterir; tarayıcı testlerini (Playwright, eski 17 e2e) ön yüzle birlikte U yazacak (dalga 2.3).

## 1. Uç noktalar

| Eski | v1 | Durum | Arka uç testi | Not |
| --- | --- | --- | --- | --- |
| GET `/api/agac` | GET `/api/tree` | karşılandı | test_speed, test_jobs 1 | Arşivdeki proje ve çalışma görünmez (eski gibi). Regresyon vakaları ağaçta yok (eski `SUREC_PANEL_VAKALAR` kalktı: v1 vakaları `tests/cases`'te, `mekanik regress` ile) |
| GET `/api/sekmeler` | GET `/api/tabs` | karşılandı | test_live (A6) | Açık çalışma tmux oturumundan değil agent-run kayıtlarından (`works.active()`, §4.10) |
| GET `/api/calisma/{kod}` | GET `W` | karşılandı | test_speed | `dal` → `branch` |
| GET `…/asamalar` | GET `W/stages` | karşılandı | test_jobs 5 | Adımlar git günlüğünden değil akış satırlarından (`records/events.jsonl`); "bu aşamanın son modeli" `model_commit` |
| GET `…/durum` | GET `W/status` | karşılandı | test_live, test_parity 17 | Satırlar katalog anahtarıyla (`rows[].key`), metin de verilir |
| GET `…/dosyalar` | GET `W/files` | karşılandı | test_jobs 7 | Klasörler `cikti/`, `deney/` yerine `out/`, `records/`, `inputs/` (§5.6) |
| GET `…/indir/{yol}` | GET `W/download/{path}` | karşılandı | test_security (A9), test_jobs 7 | Yol kaçışı 404 (eski e2e 16) |
| GET `…/adim/{sha}` | GET `W/steps/{sha}` | karşılandı | test_parity 14–15 | Değişen ölçüler params.yaml sözlüğünden (önce → sonra kaydı) |
| GET `…/canlilik` | GET `W/liveness` | karşılandı | test_live (e2e 7) | `lock`, `stop`, `inbox` eklendi |
| GET `…/hesaplar` | GET `W/calcs` | karşılandı | test_parity 14 | |
| GET `…/kartlar` | GET `W/cards` | karşılandı | test_parity 4, 12, 13 | Eski `gecmeler` alanı paket kayıtlarına (`records`, mech: `fits`) taşındı: panel geçmeyi bilmez |
| GET `…/gecme-isaretleri` | GET `W/fit-markers` | karşılandı | test_viewer (e2e 10) | Durum adları `pass/fail/review` (eski `gecti/kaldi/inceleme`); konum paket kancasından (`fit_axes`) |
| GET `…/kesit/{gecme}` | GET `W/sections/{ref}` | karşılandı | test_viewer (e2e 9) | Paket kancası `fit_section` |
| GET `/api/kartlar` | GET `/api/cards` | karşılandı | test_speed | |
| GET `…/dosya` | GET `W/design-file` | karşılandı | test_speed | "Son okumandan beri" akış satırlarından; günlük dosyaları listelenir |
| POST `…/okundu` | POST `W/read-mark` | karşılandı | test_security (A9) | |
| GET `…/dallar` | GET `W/branches` | karşılandı | test_parity 5 | Dal türleri `main/work/decision` |
| GET `…/gorsel/{yol}` | GET `W/images/{path}` | karşılandı | test_security (A9) | Yanıt CSP `sandbox` ile (SVG betik çalıştırmaz) |
| GET `…/model` | GET `W/model` | karşılandı | test_viewer (A4) | Önbellek model imzasıyla (`step`'in yazdığı); gövdede `veri` → `data` |
| GET `…/silindirler` | GET `W/cylinders` | karşılandı | test_viewer (e2e 3) | |
| POST `/api/olc` | POST `/api/measure` | karşılandı | test_viewer (e2e 3) | Gövde `kod, yollar, merkez` → `work, paths, center`; `kaynak` → `source: exact` |
| POST `…/kart/{no}` | POST `W/cards/{id}/decision` | karşılandı | test_jobs 5, test_parity 12, 13 | `karar onay/ret/yorum` → `action approve/reject/comment`; `teyit` → `confirmed`; teyit kuralı K-/O-/B- önekinden değil kart seviyesinden ve türünden (DUR, karar, kapı, baskı); kanal `panel_confirmed` |
| POST `…/model-notu` | POST `W/model-notes` | karşılandı | test_parity 17 | |
| POST `…/kart/{no}/geri-al` | POST `W/cards/{id}/revert` | karşılandı | test_parity 12 | Teyit ve neden zorunlu (eski gibi) |
| POST `…/deger` | POST `W/values` | karşılandı | test_parity 4 | Kart zorunlu (`value_change` kaydı kartı adlandırır, APPROVAL-02) |
| POST `…/dal-ac` | POST `W/branches` | karşılandı | test_parity 5 | |
| GET `/api/olaylar` (SSE) | GET `/api/events` | karşılandı | test_live (A2, e2e 6, 7) | `yeni-surum` → `new_version`, `durum` → `status`; yeni: `stream`, `inbox`, `signing` |
| GET `/{yol}` | GET `/{path}` | karşılandı | test_security | `/api/…` altında bilinmeyen yol 404 (ön yüze düşmez) |

Yeni uçlar (v1'de eskide yoktu): `/login`, `/api/session`, `/api/catalog`, `/api/new-work`, POST `/api/works`, POST `W/session`, POST `W/instructions`, POST `W/stop`, POST `W/resume`, GET `W/inbox`, GET `W/stream`, GET `W/summary`, GET `W/policy`, GET `W/intake`, POST `W/intake/answer`, GET `W/stdmap`, POST `W/decisions/{id}/objection`, POST `W/gates/{G}/back`, PUT `W/inputs/{name}`, WS `W/pty` (iskelet).

Kaldırılan uç nokta yok. Kaldırılan davranışlar:

| Eski davranış | Neden |
| --- | --- |
| Açılışta her çalışmanın modelini ısıtma (`omur.isit`) ve yeni adımda ısıtma | `step` modeli ve tessellation'ı zaten önbelleğe yazıyor (model imzasıyla); önbelleksiz ilk görüntü ölçüsü 2,0 s sınırının altında (A4). Isıtma her açılışta bütün çalışmaların modelini üreteceği için kaldırıldı |
| `_vaka_degil`: regresyon vakasına yazma yok | v1'de vakalar çalışma reposunda değil `tests/cases`'te; panel onlara erişmez |
| `*.ts.net` Host'larının kendiliğinden izinli olması | Çekirdek Tailscale'i bilmez (§5.6); izinli ek adlar `MEKANIK_PANEL_HOSTS` ile platform adaptöründen |
| Onay commit'inin git genel kimliğiyle (Taha) atılması | v1'de baş mühendis kimliği atölye ayarından ve imzalı (§4.6) |
| Oturumsuz okuma | Her `/api` isteği oturum çerezi ister (§4.6 m.3); eski e2e'deki çerezsiz `urlopen` çağrıları sayfanın istek bağlamıyla yapılmalı |

## 2. Eski e2e testleri (17)

| # | Eski test | Arka uç karşılığı | Ön yüz (U, 2.3) |
| --- | --- | --- | --- |
| 1 | kapı onayı panelden commit ve etiket | test_jobs::test_5 (teyitsiz ret, teyitle imzalı commit, etiket, `panel_confirmed`) | teyit penceresi |
| 2 | tamamlanan aşamanın 3B modeli | test_jobs::test_5 (`stages`), test_viewer (`model?commit=`) | mini 3B |
| 3 | kesit ve tam geometriden çap | test_viewer::test_exact_diameters_section_and_markers | Clip sekmesi |
| 4 | kart onayı, değer değişince onay düşer | test_parity::test_4 | |
| 5 | bu noktadan dal aç, hiçbir şey silinmez | test_parity::test_5 | |
| 6 | yeni adımda yeni sürüm bildirimi | test_live::test_new_version_and_waiting_session | bildirim, "Yükle" |
| 7 | ajan izin beklerken panel gösterir | test_live::test_new_version_and_waiting_session | maskot rozeti |
| 8 | güvenlik: Host, Origin, dal | test_security (Host, Origin, CSRF, JSON, oturum, istemci, dal) | — |
| 9 | geçme kartında ölçülü kesit | test_viewer (`sections`) | kart görseli |
| 10 | geçme işaretleri renkli, tıklanınca kart | test_viewer (`fit-markers`: konum, durum, kart) | renk, tıklama |
| 11 | kesit düzlemi keser, kesit yüzeyi dolu | — (yalnız görüntüleyici) | görüntü testi |
| 12 | karar kartı, teyit ve geri alma | test_parity::test_12 | seçenekler yan yana |
| 13 | varsayım listesi seçili satırlar | test_parity::test_13 | satır seçimi |
| 14 | hesaplamalar adım adım | test_parity::test_14_15 | grafik |
| 15 | ekip ekranı adım ayrıntısı | test_parity::test_14_15 | |
| 16 | dosyalar yalnız izinli klasörden | test_security::test_no_path_escape, test_jobs::test_7 | |
| 17 | modelde işaretleyip not | test_parity::test_17 | işaretleme |
