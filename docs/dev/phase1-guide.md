# Faz 1 taşıma kılavuzu

Durum: çalışma belgesi · yazan rol: proje-muhendisi · başlangıç 2026-11-06 (sistem saati)

Bu belge Faz 1'de kodu yazan her rol için bağlayıcıdır. Mimari belge (`docs/design/architecture.md`) neyin yapılacağını söyler, bu belge nasıl yapılacağını. Çelişki olursa mimari belge kazanır ve çelişki proje mühendisine yazılır.

## 1. Kilitli kurallar

1. **Faz 1 eşitliktir.** Eski `surec`in (commit `d26af89`, `/home/user/surec`, yalnız okunur) yaptığını yap, fazlasını yapma. İzinli değişiklikler: İngilizce adlandırma, katman taşıma (çekirdek/paket/atölye ayarı), arayüz metnini kataloğa alma, testle kapanan hata düzeltmesi (architecture §17 "yeni özellik tanımı"). Yeni fikir koda değil, `docs/later.md`'ye.
2. **Kaynaksız sayı yok, kodda da.** Koddaki her eşik ya katalogdadır (`stdlib/rules/catalog.yaml`, `limit` + kaynak) ya da paket profilinde. Kodda kalan teknik sabitlerin yanına `# source: <etiket> — <neden>` yorumu yazılır (ör. `# source: assumption — kayan nokta gürültüsü, mühendislik değeri değil`).
3. **Çekirdek alan bilmez.** `src/mekanik/core` içinde `fit`, `fdm`, `printer`, `mold`, `molding`, `wing`, `lidar`, kişi, kurum, makine adı geçmez (tam sözcük; architecture §3.1). Mekanik kavramlar `packages/mech`, 3B baskı `packages/print3d`, analiz `packages/analysis`. Çekirdek paketleri içe aktarmaz; paketler çekirdeği bilir.
4. **Adlar İngilizce, arayüz metni katalogda.** Tanımlayıcılar, alan adları, sıralı değerler, dosya adları, yorumlar ve docstring'ler İngilizce. Kullanıcının gördüğü her metin `t("anahtar", **değişkenler)` ile katalogdan gelir: çekirdek `src/mekanik/core/i18n/{tr,en}.yaml`, paketler kendi `i18n/` klasörü. Testler Türkçe metni değil anahtarı ve yapılandırılmış veriyi denetler (katalog EN'e çevrilince testler geçmeli). EN kataloğu Faz 1'de eksik olabilir; eksik anahtar TR'ye düşer.
5. **Kayıttaki metin yazıldığı dilde kalır.** Ekibin yazdığı gerekçe, soru, açıklama çevrilmez.
6. **Saat sistem saatinden:** `mekanik.core.clock.now()`. Elle saat yazılmaz.
7. **Boyut bütçesi** (ölçüt 1.9): `src/` + `packages/` Python satırı ≤ 6 560 (`wc -l`, boş satır ve yorum dahil). Modül bütçeleri §5'te. Satır uzunluğu en çok 120. Bütçeyi aşan modül sahibi durur ve proje mühendisine yazar.
8. **Ortam:** Python yalnız `uv` ile (`uv run`, `uv sync`), Python 3.12. Testler: `uv run pytest`. Çekirdek testleri (`tests/core`) OCCT kurulu değilken ≤ 60 s'de geçer: `tests/core` hiçbir şekilde `cadquery`/`OCP` içe aktarmaz.
9. **Eski repoya yazılmaz.** Eski kodu oku, karşılığını yaz; kopyalayıp Türkçe adlarıyla bırakma.

## 2. Ad eşlemesi (eski → v1)

Ek B'deki ad önerileri envanter sırasındaydı; bağlayıcı adlar bunlardır. Burada olmayan bir ad gerekirse aynı üslupla seç ve raporunda listele.

### 2.1 Dosyalar

| Eski | v1 | Sahibi |
| --- | --- | --- |
| `calisma.yaml` | `work.yaml` | çekirdek |
| `istek-listesi.yaml` | `requirements.yaml` | çekirdek |
| `params.yaml` | `params.yaml` (sözlük: ad → değer kaydı) | çekirdek |
| `gecmeler.yaml` + `montaj.yaml` | `fits.yaml` (`fits:`, `flexes:`, `tool_access:`) | mech |
| `kararlar.yaml` | `decisions.yaml` | çekirdek |
| `onaylar.yaml` | `approvals.yaml` | çekirdek |
| `yanitlar.yaml` | `replies.yaml` (yalnız eklenir) | çekirdek |
| `kartlar/<no>.yaml` | `cards/<id>.yaml` | çekirdek |
| `model/model.py` | `model/model.py` | mech |
| `hesaplar/*.py` · `kayit/hesaplar/*.json` | `calcs/*.py` · `records/calcs/*.json` | çekirdek (evidence) |
| `kayit/gunluk/*.md` | `records/log/*.md` | çekirdek |
| `kayit/gorseller/` | `records/visuals/` | çekirdek |
| `kayit/kalite/` | `records/quality/` | çekirdek |
| `cikti/` | `out/` | çekirdek |
| `calismalar.yaml` (kurum reposu) | `works.yaml` | çekirdek |
| `profiller/uretim/*.yaml` | `~/.config/mekanik/machines/<id>.yaml` (tür `print3d.fdm`) | print3d |
| `profiller/olcum/*.yaml` | `~/.config/mekanik/instruments/<id>.yaml` | çekirdek (config) |
| `kurumlar/*.yaml` | `~/.config/mekanik/orgs/<KOD>.yaml` | çekirdek (config) |
| `kurallar/katalog.yaml` | `stdlib/rules/catalog.yaml` | stdlib |

### 2.2 Alanlar ve değerler

| Eski | v1 |
| --- | --- |
| `kod, ad, amac, bitti_olcutu, sinif` | `code, title, purpose, done_criterion, risk_class` |
| `kapilar, asama, kapi_durumu` | `process.gates, process.stage, process.gate_status` |
| `kapi_durumu.<G>.{durum, basladi, bitti, etiket}` | `{status, started_at, finished_at, tag}` |
| durum `suruyor, bekliyor, bitti, atlandi` | `in_progress, pending, done, skipped` |
| `profiller.uretim` · `profiller.olcum` | `profiles.manufacturing` · `profiles.instruments` |
| `dallar.ana` · `dallar.is` · `acilis` | `branches.main` · `branches.work[]` · `opened_at` |
| param `ad, deger, birim, kaynak, formul, not, kritik, aciklama, gerekce` | `name (anahtar), value, unit, source, formula, note, critical, description, rationale` |
| `olcum_profili: <ad>` + `kaynak: olcu:*` | `source: measured:<alet-kimliği>` |
| kaynak `standart:X, uretici:X, karar, turetilir, varsayim` | `standard:X, manufacturer:X, decision, derived, assumption` |
| kritik `guvenlik, maliyet, gecme` | `critical: safety, cost, interface` |
| birim `derece, adet, oran, g/cm³` | `deg, count, ratio, g/cm3` (diğerleri aynı: `mm, m, g, N, MPa, %, m/s, -`) |
| geçme `no, parcalar, gorev, nominal, bosluk, taraflar{delik, mil}, vida, sinir_kaynagi, kritik, not` | `id, parts, task, nominal, clearance, sides{hole, shaft}, screw, limit_source, critical, note` |
| görev `ortalama, donme, kayma, siki, vida_gecisi, dayanma` | `centering, rotation, sliding, press, screw_clearance, abutment` |
| esneme `no, parca, yer, deger, birim, kaynak, not` | `id, part, location, value, unit, source, note` |
| profil `bosluk.<görev>.{alt, ust}` · `vida_gecisi.tablo` | `clearance.<task>.{lower, upper}` · `screw_clearance.table` |
| ölçme `etiket, belirsizlik{deger, alt_sinir}, gecerlilik{kritik_gecme, bicim}` | `uncertainty{value, unit, source, lower_bound}`, `valid_for{critical_dimension, form}` |
| karar `no, baslik, veren, durum, gerekce, secenekler, bagimli, taban, tarih, oneri, dayanak, hedef_etkisi, gozlemler, olcut_agirliklari, seviye` | `id, title, decided_by, status, rationale, options, dependents, base_commit, opened_at, proposal, basis, requirement_effects, observations, criteria_weights, mode` |
| karar seviyesi `gecici` · `inceleme` | `mode: provisional` (inceleme seviyesi v1'de yok; KM-02). Dalsız karar `branched: false` |
| karar durumu `inceleme_bekliyor, onaylandi, reddedildi` | `proposed, approved, rejected` |
| seçenek `ad, aciklama, dal, durum, model, params` | `id, title, branch, status, model_definition, values` |
| onay `kart, karar, kim, zaman, commit, ozet, not` | `card, action, identity{name,email}, at, commit, approved_hash, reason` |
| onay kararı `onay, ret, yorum, geri_al` | `approve, reject, comment, undo` |
| yanıt `kart, yorum_zamani, yanit, rol, zaman` | `card, comment_at, text, role, at` |
| kart `no, anahtar, uretilen, seviye, tur, baslik, tetikleyiciler, konu, durum, acan` | `id, key, generated, level, type, title, triggers, subject, status, opened_by` |
| kart metni `soru, aciklama, oneri{secim, gerekce}, onaylarsan, reddedersen, kayda_gecer, uyari` | `question, explain, proposal{choice, rationale}, if_approved, if_rejected, recorded_as, warning` |
| kart konusu `param, gecme, esneme, karar, kapi, baski` | `param, fit, flex, decision, gate, release` |
| kart durumu `acik, onaylandi, reddedildi, yanit_bekliyor` | `open, approved, rejected, awaiting_reply` |
| istek `no (I-nn), metin, tur (zorunlu, istek), olcut, kaynak` | `id (R-nn), text, kind (mandatory, wish), criterion, origin` |
| rol `proje-muhendisi, tasarim-muhendisi, tekniker, kalite-muhendisi, bas-muhendis` | `project_engineer, design_engineer, technician, quality_engineer, chief_engineer` |
| sonuç `ENGEL, UYARI, GECTI` | `block, warn, pass` (arayüz: ENGEL, UYARI, GEÇTİ) |
| hesap `ad, baslik, amac, girdiler, sabitler, adimlar, sonuclar, buyuklukler{dogruluk, yontem}, grafikler, notlar, gorseller, hata, tur, senaryo, baglanti` | `id, title, purpose, inputs, constants, steps, results, magnitudes{level, method}, charts, notes, visuals, error, type, scenario, links` |
| hesap sonucu durumu `iyi, kotu, guvenilmez` | `ok, bad, unreliable` |
| commit ekleri `Adım, Rol, Kart, Görsel, Günlük` | `Step, Role, Card, Visual, Log` (değer dili kayıt dilidir) |

### 2.3 Kural kimlikleri

| Eski | v1 | Yeri |
| --- | --- | --- |
| KAYNAK-01 | SOURCE-01 | çekirdek |
| OLCU-01, OLCU-02 | UNCERT-01 (iki alt durum) | çekirdek (kritik ölçüleri paket verir) |
| ONAY-01 | APPROVAL-01 | çekirdek |
| — | APPROVAL-02 (imza) | çekirdek, yeni (güvenlik düzeltmesi; Faz 1'de) |
| HESAP-01, HESAP-02 | CALC-01, CALC-02 | çekirdek |
| KARAR-01 | DECISION-01 | çekirdek |
| `kartlar.eksikler` (B8) | DECISION-02 | çekirdek |
| kart standardı (kimliksiz) | CARD-01 | çekirdek |
| kalite kapısı (kimliksiz) | QUALITY-01 | çekirdek |
| GECME-01, GECME-02, VIDA-01 | FIT-01, FIT-02, BOLT-01 | mech |
| KATI-01, GIRISIM-01, KAYITSIZ-01, MONTAJ-01 | SOLID-01, INTERF-01, UNREG-01, ASSY-01 | mech |
| tabla teması, tabla sığması | BED-01, BED-02 | print3d (kataloğa girer; dayanağı eski koddaki yorumla) |

Kontrol adları (eski modül adı → v1 kontrol kimliği): `kaynaksiz → source`, `olcme_belirsizligi → uncertainty`, `onay_durumu → approval_state`, `hesap_tutarliligi → calc_consistency`, `hesap_sonucu → calc_result`, `karar_dayanagi → decision_basis`, `bagimsiz_sayi → mech.independent_number`, `gecme_boslugu → mech.fit_clearance`, `girisim → mech.interference`, `kayitsiz_gecme → mech.unregistered_fit`, `montaj → mech.assembly`.

Kart tetikleyicileri: `varsayim → assumption`, `montaj_esnemesi → assembly_flex`, `olcme_belirsizligi → uncertainty`, `gecici_profil → provisional_profile`, `gorev_tanimsiz → task_undefined`, `sinirda → borderline`, `tutarlilik → consistency`, `karar_dayanagi → decision_basis`, `karar → decision`. Kart anahtarları aynı biçimde: `assumption:<param>`, `flex:E-01`, `measured:<param>`, `fit:G-04`, `uncertainty:<alet>`, `consistency:<büyüklük>`, `basis:K-04`.

## 3. Sorunlu yerler ve kararlar

- **G-24 · Dal.** Faz 1 kodu `phase-1` dalında yazılır; Faz 1 çıkışında baş mühendis onayıyla `main`'e girer (ana hatta giriş onayla; §4.10).
- **G-25 · Kaynaksız parametre.** `params.yaml`'da `source` isteğe bağlıdır; eksikliği şema hatası değil, SOURCE-01 ENGEL'idir (eski davranış; taşımada V3 "eskide kaynaksız olan yenide de kaynaksız" bunu gerektirir). Faz 0 şemasındaki `quantity` (kaynak zorunlu) kayıtlarda (hesap, karar seçeneği, standart maddesi) kullanılmaya devam eder; parametre için ayrı `param` tanımı eklenir.
- **G-26 · Dil.** Kod, yorum ve docstring İngilizce; arayüz metni katalogda (kural 4).
- **G-27 · Faz 1 şema sıkılığı.** Yükleyici tam v1 şemasıyla doğrular. v1'de zorunlu olup eski sistemde zorunlu olmayan alanların hatası (liste: `stdlib/strictness/phase1.yaml`) yükleyiciyi durdurmaz, `view.warnings`'e düşer ve `mekanik check` bunu UYARI olarak gösterir. Faz 2'de (şema `1.1`) liste boşalır.
- **G-28 · Sentetik vakalar.** H-001 aynı sayılar, uydurma parça ve parametre adları ve kurum verisi olmadan yeniden yazılır (kaynak notu ve kurum kodu taşınmaz). Vaka kodları `TST-SYN-01` (S-001) ve `TST-SYN-02` (H-001). Ölçme aletleri `caliper` ve `scanner-lidar`, makine `fdm-test`: değerler eski profillerle aynı, adlar nötr.
- **G-29 · Yanıtlar.** Takımın yorum yanıtları `replies.yaml`'da (yalnız eklenir) kalır; kart dizisi (`thread`) bellekte `approvals.yaml` yorumları ile `replies.yaml`'dan kurulur. §14.2'deki "kart dizileri" ifadesinin uygulanışıdır.
- **G-30 · Üretim profili.** Faz 1'de tek profil türü `print3d.fdm` (yazıcı + malzeme + boşluklar; eski üretim profilinin birebir karşılığı). Yazıcı ve süreç ayrımı gerekirse Faz 3'te.

## 4. Mimari iskelet

```
pyproject.toml                  uv workspace kökü: paket `mekanik` (src/), üyeler packages/*
src/mekanik/
  core/clock.py                 now(), today()
  core/errors.py                MekanikError, SchemaError, GitError
  core/yamlio.py                load/read/dump/write (atomik), Txn (çoklu yazım + geri alma)
  core/i18n/                    t(), tr.yaml, en.yaml
  core/data.py                  stdlib/schemas klasörlerinin bulunması
  core/model/schema.py          validate(kind, data, where) → uyarılar; G-27
  core/model/params.py          Param, load_params, formula_names, formula_eval
  core/model/work.py            WorkView, load_work(root)
  core/process/profile.py       süreç profili (stdlib/process/default@1.yaml)
  core/checks/result.py         Result, BLOCK/WARN/PASS, level(), fmt_num()
  core/checks/runner.py         run(view, model, only) ; summary()
  core/checks/builtin/*.py      çekirdek kontrolleri
  core/store/                   git, günlük, works.yaml, worktree
  core/cards/                   üretim, metin, numaralama, eşitleme, onay özeti/durumu
  core/decisions/               karar açma, sonuç, dayanak
  core/process/                 step, stage finish, gate pass, release request, approve, value, undo, reply
  core/evidence/                Calc, önbellek, tutarlılık
  core/quality/                 review prompt/record/close
  plugins/                      paket keşfi (entry point `mekanik.packages`), Registry
  config/                       atölye ayarı (MEKANIK_CONFIG_DIR ile değiştirilebilir)
  agent/                        kanca, durum, nabız, gözcü
  migrate/                      surec-config, surec-work, V1–V8
  cli/                          `mekanik` komutu
packages/mech/src/mekanik_mech/      fits.yaml, model yükleme, mekanik kontroller, görünüşler, kart görselleri, dışa aktarma
packages/print3d/src/mekanik_print3d/ print3d.fdm profil türü, BED-01/02, baskı isteği eki
packages/analysis/src/mekanik_analysis/ fea
stdlib/                         rules/catalog.yaml, process/default@1.yaml, roles/*.yaml, strictness/phase1.yaml
schemas/v1/                     kesinleşen şemalar (docs/design/schemas'tan)
plugin/                         Claude Code eklentisi
tests/core · tests/mech · tests/print3d · tests/cli · tests/migrate · tests/cases/{S-001,H-001}
tests/fixtures/surec/{S-001,H-001}  eski biçimde vaka (taşıma girdisi)  ·  tests/fixtures/config/  sınama atölye ayarı
```

### 4.1 Paket arayüzü (`mekanik.plugins`)

Her paket `pyproject.toml`'da `[project.entry-points."mekanik.packages"]` altında bir `PackageSpec` nesnesi verir. Çekirdek de kendi kontrollerini aynı yolla (`mekanik.core.builtin:SPEC`) kaydeder. Alanlar:

| Alan | Tür | Ne için |
| --- | --- | --- |
| `id`, `version` | str | paket kimliği (`core`, `mech`, `print3d`, `analysis`) |
| `loaders` | `{ad: f(root, view) -> Any}` | çalışma klasöründen paket verisini yükler → `view.ext[ad]` |
| `checks` | `[CheckSpec]` | `CheckSpec(id, run, rules, after_cards=False, order=100)`; `run(view, model, cards=None) -> list[Result]` |
| `card_makers` | `[f(view, results) -> list[dict]]` | sonuçlardan kart üretir (çekirdek numaralar ve eşitler) |
| `critical_dims` | `f(view) -> list[CriticalDim]` | UNCERT-01 için: `CriticalDim(ref, param, band, task)` |
| `sourced_values` | `f(view) -> list[SourcedValue]` | SOURCE-01'in params dışında denetleyeceği değerler: `SourcedValue(ref, value, unit, source)` |
| `subject_values` | `f(view, subject) -> dict | None` | onay özeti için kart konusunun değerleri (ör. `{"fit": "G-01"}`) |
| `profile_types` | `{tür: f(dict, where) -> None}` | atölye ayarındaki makine profilinin doğrulaması |
| `model` | `ModelHooks | None` | model üretimi, görünüşler, dışa aktarma (yalnız mech) |
| `release_hooks` | `[f(view, model) -> list[Result]]` | baskı isteğinde ek denetim (print3d: BED-01/02) |
| `i18n` | `Path | None` | paket kataloğunun klasörü |

Kayıt sırası: `core` önce, sonra paketler `id` sırasıyla. Kontrol sırası `order` ile; `after_cards=True` olanlar (APPROVAL-01) diğer sonuçlardan üretilen kartlarla en son çalışır (eski `KARTLARLA`).

### 4.2 WorkView

`load_work(root) -> WorkView`; alanlar: `root, code, title, stage, risk_class, gates, doc` (ham work.yaml), `profile` (süreç profili), `params: dict[str, Param]`, `requirements: list[dict]`, `decisions: list[dict]`, `cards: list[dict]` (diskteki), `approvals: list[dict]`, `replies: list[dict]`, `manufacturing: dict | None` (makine profili), `instruments: dict[str, dict]`, `ext: dict[str, Any]`, `warnings: list[str]`; özellik `finalizing` (aşama ≥ profilin `finalizing_from` kapısı; eski `kesinlestirme`).

### 4.3 Sonuç

`Result(check, rule, status, msg, args, ref=None, value=None, extra={})`: `msg` katalog anahtarı, `args` değişkenleri; `reason` özelliği metni üretir. `level(view)` eski `kalan_seviye`: kesinleştirmede `block`, öncesinde `warn`. `fmt_num(x)` eski `mm()` (Türkçe sayı yazımı, katalogdaki ondalık işaretiyle).

## 5. Modüller, sahipler, bütçe

| Modül | Eski karşılığı | Bütçe (satır) | Sahibi |
| --- | --- | --- | --- |
| core temel (clock, errors, yamlio, i18n, data, model, plugins, config, checks çerçevesi) | `veri.py`, `kontroller/__init__`, `sonuc.py`, `ortam.py`'nin bir kısmı | 1 000 | proje mühendisi |
| core/checks/builtin + regresyon | `kaynaksiz`, `olcme_belirsizligi`, `onay_durumu`, `hesap_tutarliligi`, `regresyon.py` | 350 | dalga 2 · A |
| core/cards (+ onay özeti) | `kartlar.py`, `onay.py` | 650 | dalga 2 · A |
| core/evidence + core/quality | `hesap.py`, `onbellek.py`, `kalite.py` | 450 | dalga 2 · B |
| mech | `modelci`, `disari`, `gorsel`, `kart_gorsel`, geçme kontrolleri, `veri.py` geçme kısmı | 1 450 | dalga 2 · C |
| print3d + analysis | `akis.py` tabla kısmı, üretim profili doğrulaması, `fea.py` | 270 | dalga 2 · C |
| core/store + core/decisions + core/process | `akis.py`, `git.py`, `gunluk.py`, `isler.py` | 1 150 | dalga 3 · D |
| agent + cli + doctor | `durum`, `gozcu`, `nabiz`, `ortam`, `cli/ana.py` | 800 | dalga 3 · E |
| migrate | yeni (`gecis.py` taşınmaz) | 400 | dalga 2 · F |
| **Toplam** | | **6 520** | bütçe 6 560 |

## 6. Testler

- Eski 86 test (36 `test_akis` + 42 `test_cekirdek` + 6 `test_onbellek` + 2 `test_regresyon`) v1 API'siyle taşınır; her biri aynı davranışı sınar. Taşınan testin adı eski adın İngilizcesidir; docstring'inde eski ad yazar (`"""old: test_akis::g0_dan_g3_e_ilerler..."""`). Böylece 1.2 sayılır.
- Ek B §14'teki testsiz parçalara yeni testler (1.3): docstring'i `"""new: Ek B §14 madde N"""`.
- Regresyon vakaları `tests/cases/`; beklenenler `expected.yaml`. "Hep ENGEL" ve "hep GEÇTİ" sahte kontrolleri regresyondan kalmalı.
- `tests/core` OCCT'siz çalışır (1.10); OCCT isteyen testler `tests/mech` ve `tests/print3d`'de.
- Sınama atölye ayarı `tests/fixtures/config/` (G-28); testler `MEKANIK_CONFIG_DIR` ile kullanır, kullanıcının gerçek ayarına dokunmaz.

## 7. Rapor biçimi (her modül sahibi)

Dönüşte: yazılan dosyalar ve satır sayıları; taşınan/yeni test sayısı ve sonuçları (komut çıktısının son satırı); bu kılavuza eklediğin adlar; eski davranıştan bilerek ayrılan yerler (her biri gerekçesiyle); bitmeyenler. Kodu geri yapıştırma.

## 8. Dalga 2 sözleşmeleri

### 8.1 Paylaşılan dosyalar

- **Katalog dosyaları modül başına:** `src/mekanik/core/i18n/tr.<bölüm>.yaml` (ör. `tr.checks.yaml`, `tr.cards.yaml`, `tr.evidence.yaml`, `tr.process.yaml`, `tr.cli.yaml`, `tr.agent.yaml`, `tr.migrate.yaml`). Her sahip yalnız kendi bölüm dosyasını yazar. Anahtar önekleri bölüm adıyla başlar (`checks.`, `cards.` …). `tr.yaml` temelindir (proje mühendisi).
- **Kural kataloğu paket başına:** `stdlib/rules/core.yaml`, `stdlib/rules/mech.yaml`, `stdlib/rules/print3d.yaml`. Biçim: `rules: [{id, text (TR), limit, limit_source, level, basis: [..], check}]`. Kodda duran eşik `limit`e taşınır ve kod oradan okur (`mekanik.core.checks.rules.limit(rule_id, key)`; sahibi A).
- **Şema değişikliği:** Faz 1 eşitliği için bir şemaya alan eklemek gerekirse yalnız isteğe bağlı alan ekle (alt sürüm kuralı), `schemas/v1/examples/` örneğini güncelle ve raporda yaz. `uv run python tests/core/schema_examples.py` temiz kalmalı (A taşır).
- **Ortak modüller (proje mühendisinin, değiştirmeden kullan):** `core/{clock,errors,yamlio,data}.py`, `core/i18n/__init__.py`, `core/model/{schema,params,work}.py`, `core/process/profile.py`, `core/checks/{result,runner}.py`, `core/store/git.py`, `plugins/__init__.py`, `config/__init__.py`. Değişiklik gerekiyorsa yapma; raporda öner.

### 8.2 Kart sözlüğü (bellekte)

Kart üreticileri (`card_makers`) şu alanlarla sözlük döndürür: `key` (ör. `fit:G-04`), `type` (`assumption`, `mech:fit` …), `level`, `title`, `triggers` (liste), `subject` (ör. `{"fit": "G-04"}`, `{"params": [..]}`), `question`, `explain`, `proposal: {choice, rationale}`, `if_approved`, `if_rejected`, `recorded_as`, `generated: True`, `opened_by: "system"`, isteğe bağlı `checks` (ilgili sonuçların metni), `warning`, `values`. Numara (`id`), durum (`status`), dizi (`thread`) ve `work` alanlarını çekirdek (`core.cards.generate`) koyar. Metinler `t()` ile üretilir.

- **G-31 · Faz 1'de kart seviyesi.** Eski sistemde onay isteyen her üretilmiş kart (`seviye: inceleme`) v1'de `level: hold` olur: baş mühendis onayı ister (eski davranış). Hangi kartın geçici karara dönüşeceğini Faz 2'nin politika motoru belirler.

### 8.3 Eski testlerin dağılımı (86)

| Sahip | Eski testler |
| --- | --- |
| A (26) | `test_cekirdek`: yaml_no_anahtari_bool_olmaz, sema_ihlali_acik_mesajla_durur, sabit_formul_turetilir_sayilmaz, tarama_etiketi_kumpas_profiliyle_yazilamaz, olcum_profili_surumu_sabitlenir, bozuk_girdi_acik_mesajla_durur, kaynaksiz_param_engel_verir, kaynaksiz_her_asamada_engel, kaynakli_params_gecer, onaylanan_deger_degisince_onay_duser_ve_kart_yeniden_acilir, ozet_kanonik_json_sirasi_onemsiz, onaylar_yalniz_eklenir, kart_numaralari_kararli, kritik_varsayim_tek_kart_uretici_kaynagi_kart_acmaz, kumpas_ortalama_gecmede_sinirda_gecer, lidar_kritik_gecmede_kalir, olcum_belirsizligi_degisince_onay_duser, bos_liste_onaylar_dosyasi_bozulmaz, yetkisiz_onay_reddedilir_ve_sayilmaz, sayi_yazimi_ozeti_degistirmez, reddedilen_deger_degisince_yeniden_incelenir, kumpas_varsayim_belirsizligi_kart_acar, kesinlestirmede_acik_kart_engel, tetikleyici_kalkan_kart_kapanir; `test_regresyon`: ikisi |
| B (7) | `test_cekirdek`: analiz_baglantisiz_olmaz_ve_onbellek; `test_onbellek`: doktor_bos_alan_azsa_uyari dışındaki beşi; `test_akis`: hesaplar_kayda_gecer_kaynaksiz_sabit_reddedilir |
| C (17) | `test_cekirdek`: kaynaksiz_esneme_engel, bagimsiz_sayiyla_tanimli_gecme_yakalanir, nominal_bosluk_gecmesi_bagimsiz_sayi_degil, turetilen_taraf_bagimsiz_sayi_degil, gecme_boslugu_bantlari, kesinlestirmede_kalan_gecme_engel, onaysiz_esneme_kalir_onayli_gecer, girisim_yakalanir_ve_bosluklu_gecer, kayitsiz_gecme_uyari_kayitli_gecer, uzak_caplar_kayitsiz_sayilmaz, step_stl_tessellation, bagimsiz_sayi_atlatilamaz, olculu_kesit_teknik_resim_dilinde, tabla_yerlesimi_dondurerek_sigdirir, tabla_temasi_kusuru, yuvarlatilmis_kose_agi_kapali, profil_siniri_degisince_onay_duser |
| D (32) | `test_akis`: aşağıdaki dördü ve B'ninki dışında hepsi |
| E (4) | `test_onbellek`: doktor_bos_alan_azsa_uyari; `test_akis`: durum_kancasi, cli_onay_terminal_ister, gec_dogru_oturuma_baglanir |

A ve C'nin UNCERT-01 testleri `tests/core`'da sahte bir paket kaydıyla (critical_dims veren) yazılır; gerçek geçmeyle aynı senaryo C'nin `tests/mech`'inde tekrar taşınmaz.

- **Taşınmış onay ve APPROVAL-02:** taşımayla gelen eski onay (`migrated_from_hash` taşır) imzasızdır; taşıma raporunun baş mühendisçe imzalı onayına (`undoes` değil, `approval` başvurusu) bağlıysa geçerli sayılır (V5). Bunu A (APPROVAL-02) ve F (taşıma) birlikte uygular: kayıt alanı `migration_approval: <commit>`.
