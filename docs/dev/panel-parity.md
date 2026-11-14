# Panel eşitlik listesi (ölçüt 2.8)

Durum: çalışma belgesi · yazan rol: tasarım mühendisi (ajan B, dalga 2.2; ajan U, dalga 2.3: §2 ön yüz sütunu ve §3) · kaynak: Ek B §4 (eski `panel/backend/surec_panel/*.py`, 28 uç nokta), §5 (eski `panel/frontend/`) ve `testler/test_panel_e2e.py` (17 test)

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

Tarayıcı testleri `tests/e2e/test_old_panel.py`'dedir (Chromium, Node Playwright; `pytest -m e2e`). Test adı eski numarayı korur: `test_<n>_…`. Sayfa veri öznitelikleri ve katalog anahtarlarıyla okunur, Türkçe metinle değil.

| # | Eski test | Arka uç karşılığı | Ön yüz (U, 2.3): `tests/e2e/test_old_panel.py` |
| --- | --- | --- | --- |
| 1 | kapı onayı panelden commit ve etiket | test_jobs::test_5 | `test_1_gate_approval_from_the_panel_commit_and_tag`: teyit penceresi, Vazgeç yazmaz, teyitsiz istek 409, teyitle imzalı commit, etiket, `panel_confirmed` |
| 2 | tamamlanan aşamanın 3B modeli | test_jobs::test_5, test_viewer | `test_2_finished_stage_shows_its_3d_model`: akıştaki aşama şeridi, mini 3B, "Modelde tam aç" |
| 3 | kesit ve tam geometriden çap | test_viewer::test_exact_diameters_section_and_markers | `test_3_clip_tab_and_exact_diameters`: Clip sekmesi, Ø10 ve Ø9,7 yan panelde, ölçüm `source: exact` |
| 4 | kart onayı, değer değişince onay düşer | test_parity::test_4 | `test_4_card_approval_then_a_value_change_drops_it` (kendi çalışması: değer modeli değiştirir) |
| 5 | bu noktadan dal aç, hiçbir şey silinmez | test_parity::test_5 | `test_5_open_a_branch_here_deletes_nothing` |
| 6 | yeni adımda yeni sürüm bildirimi | test_live::test_new_version_and_waiting_session | `test_6_new_step_announces_a_new_version`: başka süreçte adım, bildirim, model kendiliğinden değişmez, "Yükle" |
| 7 | ajan izin beklerken panel gösterir | test_live::test_new_version_and_waiting_session | `test_7_session_waiting_for_a_permission_is_shown`: maskot, bildirim, Ekip panelinde neden |
| 8 | güvenlik: Host, Origin, dal | test_security | `test_8_security_host_origin_and_branch` (gerçek port üzerinden) |
| 9 | geçme kartında ölçülü kesit | test_viewer (`sections`) | `test_9_fit_card_shows_the_dimensioned_section` |
| 10 | geçme işaretleri renkli, tıklanınca kart | test_viewer (`fit-markers`) | `test_10_fit_markers_coloured_and_lead_to_the_card`: durum API'den bağımsız hesaplanır, renk, eksen izdüşümü, tıklama |
| 11 | kesit düzlemi keser, kesit yüzeyi dolu | — (yalnız görüntüleyici) | `test_11_clip_plane_cuts_and_the_cut_face_is_filled` (piksel testi) |
| 12 | karar kartı, teyit ve geri alma | test_parity::test_12 | `test_12_decision_card_options_confirmation_and_undo` |
| 13 | varsayım listesi seçili satırlar | test_parity::test_13 | `test_13_assumption_list_rows_are_approved` (teyitsiz) |
| 14 | hesaplamalar adım adım | test_parity::test_14_15 | `test_14_calculations_open_from_the_tree_step_by_step` (grafik dahil) |
| 15 | ekip ekranı adım ayrıntısı | test_parity::test_14_15 | `test_15_team_panel_opens_a_steps_detail` |
| 16 | dosyalar yalnız izinli klasörden | test_security::test_no_path_escape, test_jobs::test_7 | `test_16_files_only_from_the_allowed_folders` |
| 17 | modelde işaretleyip not | test_parity::test_17 | `test_17_mark_the_model_and_send_a_note` |

## 3. Ekranlar (Ek B §5, eski `panel/frontend/`)

Ön yüz `panel-ui/` (Vite + TypeScript, çerçevesiz; G-33). Ekranların bilgi düzeni tel kafeslerdendir (`docs/design/wireframes/`); eski ekranlar §5.2'deki yerlerine taşındı. Ekran testleri `tests/e2e/test_screens.py` (her eski ekranın v1 ekranı açılır, telefon genişliğinde taşma yok, A3, A4, EN).

| Eski öğe | v1 karşılığı | Durum | Test | Not |
| --- | --- | --- | --- | --- |
| Yapılandırma (`index.html`, `package.json`, `tsconfig.json`, `vite.config.ts`, kilit) | `panel-ui/` aynı düzen; `package-lock.json` yeniden üretildi | karşılandı | derleme (`npm run build`), bütün e2e | Sürümler tam sabit ve en az iki haftalık: vite 8.3.5, typescript 6.0.2, three-cad-viewer 5.1.3 (eskiyle aynı), three 0.184.0 ve @types/three 0.184.0 (görüntüleyicinin kendi three sürümü), @xterm/xterm 6.0.0 + addon-fit 0.11.0 (oturum sekmesi), playwright 1.63.0 (yalnız test). Node 22.12+ 22.x (`engines`, `.nvmrc`; `mekanik doctor`). Google Fonts bağlantısı kalktı (dışarıya istek yok) |
| `src/api.ts` | `src/api.ts` | karşılandı | bütün e2e | Uçlar `docs/dev/panel-api.md`; yazmalar CSRF belirteci ve JSON taşır; ret `{error:{key,text}}` → `ApiError`. OpenAPI'den üretilmedi (elle, sözleşmeye göre; `GET /api/openapi.json` denetim için durur) |
| `src/main.ts` | `src/main.ts` (kabuk) | karşılandı | old 6, 7; test_jobs | Üst satır (konum, canlılık + maskot, Durdur/Sürdür, Oturumu aç, TR/EN), sekmeler (en çok 3, `/api/tabs`), ağaç, gezinti, yan panel, alt çubuk (sistem saati), hash yönlendirme, SSE, 15 s'de bir canlılık + SSE `status`. Baş mühendisin adı ayardan (`/api/session`), "Taha" yok |
| `src/genislet.ts` | `main.ts` `resizable()` | karşılandı | `test_columns_widen_by_dragging_and_are_remembered` | Ağaç ve yan panel kenarından sürüklenir, tarayıcıda hatırlanır, çift tık varsayılan (E-09); telefonda yok |
| `src/goruntuleyici.ts` | `src/viewer.ts` | karşılandı | old 2, 3, 10, 11; A4 | three-cad-viewer yalnız model gösterilirken yüklenir (A3). Dış ölçüm arka ucu, karşılaştırma, geçme işaretleri; `window.__mekanikViewer` testler için |
| `src/isaretle.ts` | `src/markup.ts` | karşılandı | old 17 | |
| `src/maskot.ts` | `ui.ts` `mascot()` | karşılandı | old 7, 15 | Durumlar v1 canlılık adlarıyla (`working/quiet/waiting/stopped`) |
| `src/yardim.ts` | `src/util.ts` | karşılandı | `test_record_text_is_shown_as_text_never_run`, `tests/e2e/test_ui_catalog.py` | HTML kaçışı doğrudan sınandı (işaretli başlık metin olarak görünür, betik çalışmaz). Sayı ve saat biçimi katalogdan (`num.decimal`, `panel.ui.locale`); rol rozetleri katalogdan |
| `src/stil.css` | `src/style.css` | karşılandı | `test_page_scrolls_and_selects_text_beside_the_viewer` (E-08), `test_phone_width_has_no_horizontal_overflow` | Renk belirteçleri eskiden/tel kafeslerden. E-08 (görüntüleyicinin `body` kuralları geri alınır) sınandı; kart görseli boy sınırı (E-10) korunur. Telefon genişliği (≤ 760 px) tek sütun |
| `src/vite-env.d.ts` | aynı | karşılandı | derleme | |
| `src/ekranlar/asamalar.ts` | Akış: aşama şeridi + seçili aşamanın ayrıntısı (`screens/flow.ts`) | karşılandı | old 2 | Mini 3B, adımlar, kararlar, kontroller, "Modelde tam aç", "Şimdiki hâlle karşılaştır" |
| `src/ekranlar/ciktilar.ts` | Dosyalar (`screens/files.ts`) | karşılandı | old 16; A1 6, 7 | Klasörler `out/`, `records/`, `inputs/`; SHA karşılaştırması; zip; yeni: dosya bırakma (A1) |
| `src/ekranlar/dallar.ts` | Dal haritası (`screens/branches.ts`) | karşılandı | old 5 | Süzgeç, arama, seçili adım, dal aç (ad onay penceresinde) |
| `src/ekranlar/dosya.ts` | Tasarım dosyası (`screens/design.ts`) | karşılandı | `test_every_old_screen_has_a_v1_screen` | Eskide bu ekranı açan test yoktu; şimdi var |
| `src/ekranlar/durum.ts` | Akış sağ paneli "Durum" sekmesi (§5.2) | karşılandı | `test_every_old_screen_has_a_v1_screen`, old 7 | Top kimde, durum satırları (katalog anahtarıyla), senden ve ekipten beklenenler, son hareket, sıradaki iş |
| `src/ekranlar/ekip.ts` | Akış sağ paneli "Ekip" sekmesi (§5.2) | karşılandı | old 15 | Canlılık ve neden, nabız günlüğü, rol tablosu (modeller atölye ayarının `agent.roles`'undan, baş mühendis adı ayardan), yapılan işlerin ayrıntısı. Eski SVG şema yerine rol tablosu (topun olduğu satır vurgulu) |
| `src/ekranlar/hesaplar.ts` | Hesaplamalar ve Analizler, ağaçta çalışmanın altında (`screens/files.ts` `calcsScreen`) | karşılandı | old 14 | Hesap görselleri `<img>` ile (CSP `sandbox`): SVG sayfaya gömülmez, betik ayıklama kuralı gereksizleşti |
| `src/ekranlar/kartlar.ts` | Kartlar (`screens/cards.ts`) | karşılandı | old 1, 4, 9, 12, 13 | Teyit kuralı kart seviyesinden ve türünden (DUR, karar, kapı, baskı); geri alma nedeni onay penceresinde (prompt yok) |
| `src/ekranlar/model.ts` | Model (`screens/model.ts`) | karşılandı | old 3, 10, 11, 17 | Geçme tablosu paket kayıtlarından (mech `fits`) |
| `src/ekranlar/ortak.ts` | `main.ts` (gezinti, ağaç, alt çubuk) ve `cards.ts` `branchSelect` | karşılandı | bütün e2e | Kişisel el kitabı bağlantısı kalktı |

Yeni ekranlar (eskide yoktu): Proje/çalışma açma (`screens/newwork.ts`, A1 1), Tanımlama (`screens/intake.ts`), Standart haritası (`screens/stdmap.ts`), Oturum sekmesi (`screens/session.ts`, A13: `tests/e2e/test_session_tab.py`). A1'in yedi işi `tests/e2e/test_e2e_jobs.py`'dedir; geçici karara itiraz ve kapıya geri dönüşün pencereleri `test_screens.py::test_objection_and_gate_return_go_through_their_windows`.

Kaldırılan öğe yok. Taşınmayan davranış: eski `ekip.ts`'teki sabit rol tablosu ("Taha", model adları kodda) — v1'de ayardan gelir.
