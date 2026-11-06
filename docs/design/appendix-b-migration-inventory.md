# Taşıma envanteri: surec (v0) → v1

- Kaynak: `/home/user/surec`, dal `claude/surec-v1-architecture-qphgcj`, HEAD `d26af89` (2026-10-27, main ile aynı). Yalnız okundu; hiçbir dosya değişmedi, test çalıştırılmadı (pytest `__pycache__`/önbellek yazardı).
- Envanter zamanı: 2026-11-06 06:06 (sistem saati).
- Karar seçenekleri: **taşınır** (mantık ve testleri aynen ya da yalnız adlandırmayla gelir; yeni repoya testlerini geçerek girer) · **yeniden yazılır** (fikir kalır, kod baştan) · **taşınmaz**.
- Kesin kural: git geçmişi, kurum ve Üstteknik verisi, kişisel yollar ve adlar taşınmaz; H-001 regresyon vakası sentetik vakaya dönüşür.
- "Satır": `wc -l`. Büyük modüller iş parçalarına bölündü; parça satırı yaklaşık satır aralığıdır.
- "Testleri": `testler/` içindeki test fonksiyonu adları (`test_` öneki atıldı). "e2e N" = `test_panel_e2e.py::test_N_…`. "S-001 n" / "H-001 n" = regresyon vakasının n. alt vakası.

## 1. Özet

### Karar başına sayı (bölüm 2–10'daki envanter satırları)

| Karar | Sayı |
| --- | --- |
| taşınır | 105 |
| yeniden yazılır | 47 |
| taşınmaz | 29 |
| **Toplam** | 181 |

Bölüm başına dağılım:

| Bölüm | taşınır | yeniden yazılır | taşınmaz | toplam |
| --- | --- | --- | --- | --- |
| 2. Çekirdek ve kontroller | 34 | 13 | 2 | 49 |
| 3. CLI | 18 | 5 | 2 | 25 |
| 4. Panel arka ucu | 5 | 2 | 1 | 8 |
| 5. Panel ön yüzü | 8 | 12 | 0 | 20 |
| 6. Kural kataloğu | 18 | 1 | 0 | 19 |
| 7. Profiller | 4 | 0 | 0 | 4 |
| 8. Ajanlar, ayarlar, paketleme, kurumlar | 5 | 5 | 2 | 12 |
| 9. Testler ve vakalar | 6 | 1 | 1 | 8 |
| 10. Belgeler ve kayıtlar | 7 | 8 | 21 | 36 |

Dersler (E), öneriler (Ö) ve bağımsız inceleme (B) tabloları durum tablosudur; karar sayısına girmez.

### Öne çıkan bulgular

1. **Katalogda olmayan kod kuralları.** `kontroller/hesap_tutarliligi.py` HESAP-01, HESAP-02, KARAR-01 sonuçları üretir; üçü de `kurallar/katalog.yaml`'da yok (Ö-22…Ö-24 onay bekliyor). Kimliği hiç olmayan denetimler de var: tabla teması (E-25), ayrık katı (E-28), kart standardı (metinsiz/görselsiz kart ENGEL, Ö-10), kalite YÜKSEK engeli (Ö-20), kötü sonuçta gerekçe şartı (Ö-23). v1'de "her `Sonuc.kural` katalogda, her katalog `kontrol`'ü kodda" bağ testi gerekir.
2. **Kodda duran eşik sayıları.** `CAP_FARKI_SINIRI=3.0` (karar), `GIRISIM_ESIGI=0.001` (varsayim), `TUTARLILIK_ESIGI=0.10`, `ORAN=4` (standart), `TEMAS_ARALIGI=0.5` (varsayim), `KABUK_MM=0.8`, `DOLGU=(0.15,0.25)`, `UST_SINIR_BAYT=5 GB`, `BOS_ALAN_ALT_SINIR=10 GB`. Kaynak etiketi yalnız yorumda; v1'de katalogun `sinir` alanına ya da atölye ayarına (config) çıkmalı.
3. **Kişisel ve kurum izleri** (taşınmaz, v1'de config'ten gelir): "Taha" sabiti (`git.py`, `cli/ana.py` istemi, `main.ts`, `ekip.ts`), `github.com/tahatas013/surec` bağlantısı (`ortak.ts`), `/home/tahatas013/...` (`.claude/settings.json`), `~/is/calisma`, `~/is/arsiv`, `~/is/ust-gecis` (`isler.py`, `gecis.py`), `kurumlar/ust` (ustteknik-arge), H-001 `KAYNAK.md` (ustteknik-arge commit `a9688e6…`, dizlik yolları), testlerde "Taha Test" kimliği, `S-001/onaylar.yaml` `kim: Taha`.
4. **Bütün kurum ve ayar verisi surec reposunun içinde** (`kurumlar/`, `profiller/`, `SUREC_KOK` göreli yollar). v1'in 4. katmanı (atölye ayarı, `~/.config/<ad>/`) ile 5. katmanı (kurum başına repo) bunu ayırır; `veri.py`, `isler.py`, `gozcu.py`, `veriler.py`, `regresyon.py` bu yüzden yol değiştirir.
5. **Eskimiş belgeler:** `ajanlar/kalite-muhendisi.md` "yalnız Kesinleştirme'de" diyor (B1 ile her kapıda çalışıyor); `ajanlar/README.md` "`surec ac` kopyalar" diyor (K-11 ile yalnız `--claude-ayarlari`); `izin-onerileri.md`'deki deny ekleri `.claude/settings.json`'a girmemiş.
6. **Test sayıları:** 107 test fonksiyonu (parametrize ile yaklaşık 144 durum): test_akis 36, test_cekirdek 42 (62), test_gecis 4, test_onbellek 6, test_panel_e2e 17, test_regresyon 2 (19). Son kurulum raporunda 123/123 geçiyordu (2026-10-26, bundan sonra testler eklendi).

## 2. Çekirdek modülleri (`cekirdek/surec_cekirdek/*.py`)

`akis.py` 1086 satırdır; aşağıda yedi parçaya bölündü. `kart_gorsel.py` (925), `veri.py` (460) ve `isler.py` (327) da parçalıdır.

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `__init__.py` | 0 | Boş paket dosyası | — | taşınmaz | — | v1 paket yapısı yeni; içerik yok |
| `akis.py` · adım (`adim`, `_Yazim`, `_yaz`, `_slug`, `_ana_dalda_mi`, `_ozet_kontrol`, `_sinir_kutusu`, `kullanilmis_kartlar`, `KAYIT_YOLLARI`, `ACIK_GECICI_KARAR_SINIRI`) | 34–200 (~150) | Kontrolleri çalıştırır, kartları eşitler, görsel üretir, Adım/Rol/Kart/Görsel ekli commit ve ayrı "Günlük:" commit'i atar (K-12), önbelleğe model yazar, nabzı tazeler; metni ya da görseli eksik açık kart varsa ENGEL; yazımı atomik yapar, hata olursa geri alır | akis: g0_dan_g3_e_ilerler_ve_gunlukte_gorunur, ana_hatta_adim_atilamaz, ekip_bas_muhendis_rolu_kullanamaz, ekip_adimlarinin_hepsi_gorselli, kirli_agacta_kismi_adim_onbellege_yanlis_model_yazmaz, kart_standardi_metinsiz_karar_ve_izsiz_varsayim_adimi_durdurur; e2e 6 | yeniden yazılır | core.store (commit, atomik yazım) + core.report (günlük) + core.cards (eşitleme) | Tek fonksiyonda altı iş ve Türkçe ek anahtarları; v1'de store yazar, report ve cards olayla bağlanır. Korunacak: atomik yazım ve geri alma, kirli ağaçta önbelleğe yazmama, ana hatta adım yasağı, `bas-muhendis` rolü yalnız BM kimliğiyle |
| `akis.py` · kapı listesi ve plan (`gecen_kapilar`, `gercek_asama`, `istek_durumu`, `ISTEK_DURUMU`, `_g0_sinifi`, `kapi_listesi`, `ZORUNLU_KAPI_MADDELERI`, `_kapi_on_kosul`, `DENEY_DESENI`, `g4_gerekli`, `kapi_planini_guncelle`, `asama_bitir`, `KAPI_ANLAMI`, `kapi_metni`) | 105–120, 201–400 (~215) | El kitabı §6 kapı kontrol listesi (G0–G5), §5 sınıf kuralı (dört soru), istek–kanıt durumu (B2), deneyle doğrulanan zorunlu istek → G4 (B7), aşamanın etiketlerden okunması, O-Gn kapı kartı ve metni | akis: g0_dan_g3…, g3_engel_varken_etiket_konmaz, kapanis_alani_hold_kapatmaz, asama_etiketlerden_okunur, deneyle_dogrulanan_zorunlu_istek_g4_ekler; e2e 1 | taşınır | core.flow (+ core.intake: G0 soruları) | Saf kural mantığı; yalnız adlandırma. v1'de eklenecek eksikler: G2'de risk kaydı/DFMEA maddesi (E-31), G4/G5'te zorunlu isteklerin "karşılandı" şartı (Ö-21), G3 → G2 dönüşü (Ö-17) |
| `akis.py` · kapı geçişi (`_kartli_commit`, `_kapi_hazir_mi`, `_agac_onayla`, `kapi_gec`) | 401–483 (~83) | Onaylı kapıda istek ağacı ve onay kaydı `commit-tree` ile ana hatta iki ebeveynli birleşim olur (K-10), BM imzalı etiket konur; ön koşullar kayıttan önce denetlenir, geçiş yarım kalmaz | akis: istekten_sonra_tasarim_degisirse_kapi_onayi_yazilmaz, gecilmis_kapi_yeniden_onaylanamaz_yarim_kalmaz, kapi_etiketi_onay_kaydini_icerir_ve_bas_muhendis_imzalar; e2e 1 | yeniden yazılır | core.flow + core.store | Düşük seviye git işlemleri store arayüzüne iner. Güvenceler (içeriğe bağlı onay, yarım kalmama, imzalı etiket) testlerle aynen taşınır |
| `akis.py` · baskı Hold'u (`baski_klasoru`, `_dosya_ozeti`, `baski`, `_baski_hazir_mi`, `baski_cik`) | 484–627 (~118) | Baskı isteği: ENGEL yokken, ayrık katı reddi (E-28), tabla teması (E-25), kalite incelemesi (B1), STEP/STL özetli B kartı; onayda `<kod>-baski-<no>` etiketi ve `cikti/`; kendi B kartı "açık Hold" sayılmaz (E-24) | akis: baski_hold_onaydan_sonra_etiket_ve_cikti, engel_varken_baski_istenmez, kesinlestirmede_baski_kendi_hold_kartina_takilmaz, kalite_yuksek_bulgu_kapanmadan_baski_istenmez | yeniden yazılır | core.flow (genel "üretime gönderme" Hold'u) + pkg_fdm (dosyalar, ayrık katı, tabla, baskı ayarı) | FDM'e özgü denetimler alan paketine çıkar. Eksik: baskı ayarı zorunlu alan ve kabul ölçümü (E-41), "G3 içinde" sınırı (Ö-08) |
| `akis.py` · `tabla_temasi_kusuru`, `TEMAS_ARALIGI` | 494–519 (~26) | En alt noktanın 0,5 mm (varsayim) üstünde temastan büyük düz alt yüz varsa baskıyı reddeder | cekirdek: tabla_temasi_kusuru | taşınır | pkg_fdm (kontrol) | Saf geometri; testli. Kural kimliği yok: v1'de katalog kimliği alır, eşik profile |
| `akis.py` · karar (`karar_ac`, `_temiz_mi`, `karar_sonucu`, `dayanagi_yenile`) | 628–773, 985–998 (~160) | Bütün seçenekler tek kartta; geçici kararda seçenek başına `<kod>/karar/K-<no>-<s>` dalı; seçenek tanımı kayıtta (E-15); seçeneğin değiştirdiği her ölçü her seçenekte açık (E-17); `hedef_etkisi` zorunlu (B8), ölçümsüz gözlem uyarısı (B6), dayanak hesap özeti (B5); ret yalnız kendi dalını etkiler; onaylanan dal iş dalına birleşir | akis: reddedilen_karar_yalniz_kendi_dalini_etkiler, onaylanan_karar_dali_is_dalina_birlesir, karar_secenek_tanimi_kayitta_durur, secilen_secenegin_olcusu_obur_secenege_sizmaz, kapanmis_kararin_karsilastirmasi_donar, tutarlilik_ve_dayanak_karti_onaylaninca; e2e 12 | yeniden yazılır | core.decisions | Dal yönetimi store'a, karar kaydı JSON Schema'ya geçer; doğrulamalar aynen kurala dönüşür |
| `akis.py` · onay, değer, geri alma (`_yazmaya_hazir`, `onay_ver`, `deger_gir`, `onay_geri_al`, `istek_geri_cek`) | 774–984 (~200) | BM kaydı yalnız temiz klasörde ve görülen sürüm son sürümken (Ö-07); kötü sonuç varken gerekçe şartı (B4); karar kartında seçenekle onay, V-01'de satır onayı; `geri_al` kaydı (Ö-15), kapı/baskı ve birleşmiş seçenek geri alınmaz; ekip baskı isteğini geri çeker | akis: cli_onay_terminal_ister, kirli_klasorde_bas_muhendis_yazmaz, eski_surumu_goren_onay_veremez, istek_geri_cekilir_onay_geri_alinir, birlesmis_secenegin_onayi_geri_alinmaz_satir_geri_alinir; e2e 4, 12, 13 | yeniden yazılır | core.flow (onay) | Git kimliği ve dosya yolları store'a iner; güvenceler testlerle taşınır. Gerekçe şartının (B4) testi yok |
| `akis.py` · model notu, yorum–yanıt (`NOT_KLASORU`, `model_notu`, `bekleyen_yorumlar`, `yanitla`) | 999–1086 (~88) | BM'nin model üstündeki notu N-nn kartı olur (ekran görüntüsü, parça, 3B nokta, kamera); yorum–yanıt dizisi, yanıt bekleyenler, yanıtla kart kapanır | akis: yorum_yanit_bekler_yanitlaninca_kapanir, model_notu_acilir_ekibe_duser_yanitla_kapanir; e2e 17 | yeniden yazılır | core.cards (N türü, yorum–yanıt) | Kart motorunun bir türü olur; `yanitlar.yaml` JSON Schema'ya |
| `disari.py` | 77 | STEP, STL (temiz ağ: sıfır alanlı üçgen atılır, çakışık nokta birleşir, E-29), ocp_tessellate ile görüntüleyici verisi | cekirdek: step_stl_tessellation, yuvarlatilmis_kose_agi_kapali | taşınır | cad (dışa aktarma, ağ) | Saf adaptör; `STL_TOLERANSI` gibi çizim/ağ sabitleri varsayim etiketiyle ayara |
| `durum.py` | 108 | Claude Code kancalarından oturum durumu (çalışıyor, bekliyor, durdu, kapandı) `~/.local/state/surec/durum/<kod>.json`; kancaları `.claude/settings.json`'a yazar | akis: durum_kancasi; e2e 7 | taşınır | agent (claude_code adaptörü) | Adaptöre özgü, testli; durum kökü config/XDG'den |
| `fea.py` | 66 | Katı → TetGen dörtyüzlü ağ → scikit-fem doğrusal elastik çözüm; eleman başına von Mises ve σ_zz | yok (yalnız BAG-PLU-01 hesaplarında kullanıldı) | taşınır | cad (ağ) + pkg_aero (yapısal çözücü yardımcısı) | Küçük ve sahada çalıştı; bilinen çözümlü bir kirişle yeni test gerekir |
| `gecis.py` | 406 | ustteknik-arge'yi yeni düzene geçirme planı (kuru çalıştırma): `params.py` ayrıştırma, etiket eşleme (K-22), sayı korunumu, geçme dönüşümü, rapor | gecis: 4 test (biri `~/is/ust-gecis/girdi.yaml` yoksa atlanır) | taşınmaz | — | K-28 ile rafa kalktı; Üstteknik dal adları (`p0-s2`) ve kişisel yol içerir. Fikir (sayı korunumu ölçümü, bölüm etiketi kaynak sayılmaz) ileride bir içe aktarma eklentisine not |
| `git.py` | 104 | git çağrısı, ekip ve BM kimliği, Türkçe ekli commit mesajı ve kendi ek ayrıştırıcısı (K-08), dal yardımcıları | dolaylı: test_akis bütünü (ekleri_oku g0_dan_g3'te) | yeniden yazılır | core.store | v1'de ASCII ek anahtarları (Step/Role/Card/Image) `git interpret-trailers` ile okunur, kendi ayrıştırıcı gereksiz; BM kimliği config'ten ("Taha" sabiti kalkar) |
| `gorsel.py` | 146 | İzometrik görünüş (gizli çizgili) ve teknik resim dilinde ölçülü kesit SVG (45° tarama, ok uçlu ölçü, ölçek seçimi) | cekirdek: olculu_kesit_teknik_resim_dilinde; e2e 9 | taşınır | cad (render, kesit) | Saf; çizim düzeni sayıları varsayim |
| `gozcu.py` | 97 | Kurum repolarında BM kimlikli yeni commit'leri izler, her olaya bir satır yazar (Claude Code Monitor ekibi uyandırır, E-14), `gozcu.json` damgası | yok (panelde `acik_mi` dolaylı) | taşınır | agent (uyandırma) | Mantık aynen; repo listesi `kurumlar/*.yaml` yerine config'ten; yeni test gerekir |
| `gunluk.py` | 71 | Çalışma günlüğü `kayit/gunluk/YYYY-MM-DD.md`; yalnız eklenir, saat sistemden; okuyucu | akis: g0_dan_g3…, ekip_adimlarinin_hepsi_gorselli | taşınır | core.report | Saf; rol adları çeviri katmanına. "Yalnız eklenir" için doğrudan test eklenmeli |
| `hesap.py` | 265 | Hesap/analiz çalıştırıcı: `Hesap` kaydı (kaynaklı girdi, kaynağı zorunlu ve varsayim olamayan sabit, adım, sonuç, grafik, büyüklük + doğruluk, `diger`), girdi özetiyle önbellek (E-37), analizde `BAGLANTI` zorunlu (Ö-19), tutarsızlık (B3), kötü sonuç (B4), sonuç özeti (B5) | akis: hesaplar_kayda_gecer_kaynaksiz_sabit_reddedilir, tutarlilik_ve_dayanak_karti_onaylaninca; cekirdek: analiz_baglantisiz_olmaz_ve_onbellek; S-001 9–10; e2e 14 | taşınır | core.evidence (hesap çalıştırıcı) | API yalnız adlandırma (input, const, step, result, plot, quantity, other, figure, note) |
| `isler.py` · kod ve iskelet (`KOD_DESENI`, `EN_COK_AKTIF`, `CALISMA_KOKU`, `VARSAYILAN_PROFILLER`, `simdi`, `kurum`, `proje_klasoru`, `kod_coz`, `BIRLESTIRME_KURALLARI`, `repo_ayarla`, `yeni_calisma`, `g0_karti`, `MODEL_SABLONU`, `calisma_klasoru`, `bulundugum_calisma`, `coz`) | 1–218 | Tekrar kullanılmayan çalışma kodu (`calismalar.yaml`), dallar (`<kod>/ana`, `is/genel`), union birleştirme kuralları (K-17), G0 kartı, model şablonu, yeni çalışmaya `.gitignore` | akis: her testin kurulumu, kart_numarasi_dallar_arasinda_tekrar_kullanilmaz | yeniden yazılır | core.store + core.intake + config | Kurumu surec içindeki `kurumlar/*.yaml`'dan, worktree'yi `~/is/calisma`'dan okur; v1'de kurum başına repo ve atölye ayarı |
| `isler.py` · oturum (`_tmux`, `tmux_oturumlari`, `ac`, `ajanlari_koy`, `kapat`, `gec`) | 219–285 | tmux oturumu (en çok 3, K-19); divan şablonlarını ve kancaları `.claude/`'a yalnız `--claude-ayarlari` ile koyar (K-11), `.git/info/exclude` | akis: iki_calisma_acilir_gecilir_en_cok_uc, gec_dogru_oturuma_baglanir | yeniden yazılır | agent (claude_code adaptörü) + cli | tmux ve Claude Code ayrıntısı adaptöre; aktif sınırı config'e |
| `isler.py` · arşiv (`ARSIV_KOKU`, `arsivdekiler`, `arsivle`) | 286–327 | `<kod>-arsiv` etiketi, `arsiv.yaml` kaydı, worktree taşıma; hiçbir şey silinmez | akis: arsivle_hicbir_sey_silmez_panelden_gizler | taşınır | core.store | Mantık aynen; arşiv kökü config'ten |
| `kalite.py` | 154 | Her kapı ve baskı isteğinde temiz bağlamlı inceleyici (`claude -p`, salt okunur, donmuş kopya); rapor `kayit/kalite/`; açık YÜKSEK varken istek reddi; girdi özeti aynıysa yeniden çalışmaz; bulgu kapatma | akis: kalite_yuksek_bulgu_kapanmadan_baski_istenmez (sahte inceleyici `SUREC_KALITE_KOMUTU`) | taşınır | core.quality (+ agent: inceleyici komutu) | Mantık aynen; `claude -p` komutu adaptörden gelir |
| `kart_gorsel.py` · ölçü bulma ve görünüş (`Olcu`, `Etki`, `_yuz_imzasi`, `_degisen_yuzler`, `_adim`, `_yon_sec`, `en_iyi_yon`, `_silindir`, `_ayni_eksen`, `_olcu_adaylari`, `param_etkisi`, `_kenar_noktalari`, `gorunus`, `_silindir_siluetleri`, `imza`) | 26–436 (~410) | Değeri biraz oynatıp modeli yeniden üretir, değişen yüzlerden ölçünün yerini bulur; ölçü vurgulu görünüş SVG'si | dolaylı: akis kart standardı testleri; e2e 12 | taşınır | cad (render) + core.cards | Saf geometri; doğrudan birim testi yok, yeni test gerekir |
| `kart_gorsel.py` · seçenek ve geçmiş sürüm modeli (`model_uretici`, `degerler`, `secenek_degerleri`, `_secenek_modeli`, `_secenek_figurleri`, `_secenek_parcalari`, `_commit_modeli`) | 437–490, 712–779 (~120) | Karar seçeneğinin değerleri; kapanmış kararda onay commit'indeki `params.yaml` (E-21), seçenekte açık değerler (E-17) | akis: secilen_secenegin_olcusu_obur_secenege_sizmaz, kapanmis_kararin_karsilastirmasi_donar | taşınır | core.decisions | Testli. E-21 kalanı: model kodu da onay sürümünden alınmalı |
| `kart_gorsel.py` · geçme kesiti ve izometrik (`gecme_eksenleri`, `gecme_kesiti`, `izometrik`) | 491–552 (~62) | Kayıtlı geçmenin eksenini silindirlerden bulur, ölçülü kesit çizer | dolaylı: e2e 9 | taşınır | cad (kesit) | Saf; doğrudan test eklenmeli |
| `kart_gorsel.py` · baskı tahmini ve tabla (`KABUK_MM`, `DOLGU`, `baski_tahmini`, `tabla_olcusu`, `yerlesim_bul`, `tabla_yerlesimi`, `baski_yonu`) | 553–618 (~66) | Kabuk + dolgu ile filament/süre tahmini (E-23); Z'de döndürerek kenar paylı tablaya sığdırma (E-22) | cekirdek: tabla_yerlesimi_dondurerek_sigdirir (tahminin testi yok) | taşınır | pkg_fdm | Kabuk, dolgu ve tabla ölçüleri makine profiline (config) çıkar (E-01, E-23 kalanı) |
| `kart_gorsel.py` · kart görselini bağlama (`_girdi_ozeti`, `_onbellekli`, `_yaz`, `param_figurleri`, `hesap_girdisi_svg`, `_kart_gorselleri`, `_metin_gorseli`, `_tutarlilik_gorseli`, `ozet_gorseli`, `ekle`, `VURGU`, `YONLER`) | 619–711, 780–925 (~240) | Kart türüne göre görsel seçer (parametre, geçme, karar, baskı, kapı, tutarlılık), önbellekler, `kayit/gorseller/kartlar/`'a yazar | akis: kart_standardi…, ekip_adimlarinin_hepsi_gorselli; e2e 12, 13 | yeniden yazılır | core.cards (görsel sağlayıcı arayüzü) | Tür → görsel eşlemesi sabit kodlu; v1'de her paket kendi kart görselini eklenti olarak kaydeder |
| `kartlar.py` | 465 | Kart üretici: tetikleyiciler (kritik varsayım, V-01 listesi, kaynaksız, geçme, geçici profil, esneme, ölçme belirsizliği, tutarlılık, dayanak), kritiklik, metinler (soru, "bu nedir", onaylarsan/reddedersen/kayda geçer), eksik denetimi, dallar arası tekrarsız numara, eşitleme (tetikleyici kalkınca kapanır, dosya silinmez) | cekirdek: kart_numaralari_kararli, kritik_varsayim_tek_kart_uretici_kaynagi_kart_acmaz, tetikleyici_kalkan_kart_kapanir, kumpas_varsayim_belirsizligi_kart_acar, onaylanan_deger_degisince_onay_duser_ve_kart_yeniden_acilir; akis: kart_numarasi_dallar_arasinda…, kart_standardi…; H-001/S-001 kart beklentileri | taşınır | core.cards | Mantık aynen; Türkçe kart metinleri çeviri kaynağına |
| `modelci.py` | 74 | `model/model.py`'yi params ile bayt kodu yazmadan yükler (E-19); model içerik imzası + üretici sürümü | akis: kirli_agacta_kismi_adim…, imza kullanan testler | taşınır | cad (model üretimi / içe alma) | Saf. E-19 için doğrudan test yok |
| `nabiz.py` | 93 | Ekip nabzı `~/.local/state/surec/nabiz/<kod>.json`; canlılık: çalışıyor / ses yok / seni bekliyor / durdu (eşikler varsayim) | dolaylı: e2e 7, 15 | taşınır | agent (nabız) + panel | Birim testi yok, eklenmeli; kök config/XDG'den |
| `onay.py` | 173 | Yalnız eklenen `onaylar.yaml`; kanonik JSON SHA-256 özeti; konu değerleri (param, geçme, profil sınırı, belirsizlik, esneme, tutarlılık); tasarım özeti; yetkili denetimi; onay durumu | cekirdek: ozet_kanonik_json_sirasi_onemsiz, onaylar_yalniz_eklenir, bos_liste_onaylar_dosyasi_bozulmaz, yetkisiz_onay_reddedilir_ve_sayilmaz, profil_siniri_degisince_onay_duser, olcum_belirsizligi_degisince_onay_duser, sayi_yazimi_ozeti_degistirmez, reddedilen_deger_degisince_yeniden_incelenir | taşınır | core.flow (onay kaydı) | Saf ve testli; yetkili adı config'ten |
| `onbellek.py` | 83 | `~/.cache/surec/<commit>/`; LRU (toplam 5 GB'ı aşınca en eski kullanılan silinir), kullanım zamanı `.son-kullanim` dosyasından | onbellek: 6 test | taşınır | core.evidence (önbellek) | Saf; kök ve sınır config'e |
| `ortam.py` | 166 | `surec doktor`: araç sürümleri (Node v24.22.1 sabit, Python 3.12), gh kimliği, NVIDIA, disk ≥ 10 GB, paketler, CadQuery duman testi | onbellek: doktor_bos_alan_azsa_uyari | yeniden yazılır | cli (doctor) + config + plugins | Makineye özgü denetimler (NVIDIA, gh, Tailscale, FreeCAD, OrcaSlicer); v1'de her paket kendi denetimini kaydeder. `Bulgu` yapısı korunur |
| `regresyon.py` | 80 | `testler/vakalar/<no>/` dondurulmuş vakalarını çalıştırır; ENGEL/KALDI/GECTI ve kart beklentisi | regresyon: vakalarin_hepsi_gecer, tek_duze_kontrol_regresyondan_gecmez | taşınır | core.checks (regresyon) | Vaka kökü `SUREC_KOK` yerine paket verisi; H-001 sentetiğe |
| `veri.py` · sabitler (`GOREVLER`, `KAYNAK_DESENI`, `KRITIKLIK`, `AD_DESENI`, `ASAMALAR`, `G0_SORULARI`, `SINIF_KAPILARI`, `BIRIMLER`) | 18–38, 97 (~25) | Geçme görevleri, kaynak etiketleri (`uretici:` dahil), birimler, aşamalar, sınıf kapıları, G0 soruları | cekirdek: sema_ihlali_acik_mesajla_durur, bozuk_girdi_acik_mesajla_durur | taşınır | stdlib (etiketler, görevler, birimler) + core.flow + core.intake | Veri olarak aynen; `literatur:` etiketi (Ö-28) onaydan sonra |
| `veri.py` · YAML yükleyici (`Yukleyici`, `yaml_oku`, `_oku`) | 44–66 (~23) | yes/no/on/off → bool dönüşümü kapalı yükleyici (K-02) | cekirdek: yaml_no_anahtari_bool_olmaz | taşınır | core.model | Saf ve testli |
| `veri.py` · formül (`formul_adlari`, `formul_hesapla`, `_ISLEMLER`) | 120–153 (~34) | `turetilir` değerler için güvenli AST dört işlem | cekirdek: sabit_formul_turetilir_sayilmaz, bagimsiz_sayi_atlatilamaz | taşınır | core.model | Saf ve testli |
| `veri.py` · şema ve yükleyiciler (`SemaHatasi`, `_gerekli`, `_sozluk`, `_liste`, `Param`, `params_yukle`, `Gecme`, `gecmeler_yukle`, `gecme_olculeri`, `_uretim_profili_dogrula`, `_olcum_profili_dogrula`, `profil_yukle`, `profil_ref_coz`, `Calisma`, `_montaj/_kararlar/_yanitlar/_onaylar_dogrula`, `calisma_yukle`, `SUREC_KOK`) | 40–43, 68–119, 154–460 (~360) | Elle şema denetimi ve açık hata mesajı; nominal + boşluk → delik/mil ölçüsü; profil sürümü sabitleme; kaynak etiketi ile ölçüm profili eşleşmesi | cekirdek: sema_ihlali… (×4), bozuk_girdi… (×10), tarama_etiketi_kumpas_profiliyle_yazilamaz, olcum_profili_surumu_sabitlenir | yeniden yazılır | core.model (veri modeli + JSON Schema) | v1 kararı JSON Schema doğrulaması; alan adları İngilizce; profil yolu `SUREC_KOK/profiller` yerine config. `gecme_olculeri` hesabı aynen korunur |

### Kontroller (`cekirdek/surec_cekirdek/kontroller/*.py`)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `kontroller/__init__.py` | 30 | Sabit `SIRA` listesi, `calistir` (`onay_durumu` en son ve öteki sonuçlardan üretilen kartlarla), `ozet` | regresyon: tek_duze_kontrol… (`SIRA` üstünden); bütün kontrol testleri | yeniden yazılır | core.checks (çalıştırıcı + katalog bağı) | Sıra sabit liste; v1'de katalogdaki `kontrol` alanından ve eklenti kaydından kurulur. "Kartlarla en son" kuralı korunur |
| `bagimsiz_sayi.py` | 50 | GECME-01: geçmenin iki tarafı bağımsız sabit sayı olamaz; biri öbüründen türemeli | cekirdek: bagimsiz_sayiyla_tanimli_gecme_yakalanir, nominal_bosluk_gecmesi_bagimsiz_sayi_degil, turetilen_taraf_bagimsiz_sayi_degil, bagimsiz_sayi_atlatilamaz (×3), sabit_formul_turetilir_sayilmaz; H-001 1; S-001 2 | taşınır | core.checks | Saf ve testli |
| `gecme_boslugu.py` | 58 | GECME-02 (boşluk görev bandında) ve VIDA-01 (ISO 273 delik çapı) | cekirdek: gecme_boslugu_bantlari (×7), kesinlestirmede_kalan_gecme_engel; H-001 1–3, 6, 7a, 7b; S-001 3 | taşınır | core.checks | Saf ve testli; VIDA tablosu stdlib'e |
| `girisim.py` | 50 | KATI-01 (geçerli kapalı katı) ve GIRISIM-01 (kesişim hacmi), trimesh + manifold3d, temiz ağ | cekirdek: girisim_yakalanir_ve_bosluklu_gecer, yuvarlatilmis_kose_agi_kapali; S-001 5 | taşınır | core.checks + cad (ağ) | Testli; `AG_TOLERANSI`, `GIRISIM_ESIGI` katalog sınırına |
| `hesap_tutarliligi.py` | 54 | HESAP-01 (aynı büyüklük iki hesapta > %10 farklı), HESAP-02 (kötü/güvenilmez sonuç), KARAR-01 (kapanmış kararın dayanağı değişti) | akis: tutarlilik_ve_dayanak_karti_onaylaninca; S-001 9–10 | taşınır | core.checks | Testli. Üç kural katalogda yok: v1'de kataloğa girmeli (dayanak B3–B5; katalog değişikliği BM onayı ister) |
| `kayitsiz_gecme.py` | 72 | KAYITSIZ-01: farklı parçalarda eş eksenli, çap farkı < 3 mm silindir çiftleri geçme kaydında mı (UYARI) | cekirdek: kayitsiz_gecme_uyari_kayitli_gecer, uzak_caplar_kayitsiz_sayilmaz; S-001 7 | taşınır | core.checks | Testli; 3 mm (karar) ve toleranslar (varsayim) katalog sınırına |
| `kaynaksiz.py` | 29 | KAYNAK-01: params ve esnemelerde kaynaksız değer her aşamada ENGEL | cekirdek: kaynaksiz_param_engel_verir, kaynaksiz_her_asamada_engel, kaynakli_params_gecer, kaynaksiz_esneme_engel; H-001 1; S-001 1 | taşınır | core.checks | Saf ve testli |
| `montaj.py` | 25 | MONTAJ-01: her esnemenin geçerli onayı var mı | cekirdek: onaysiz_esneme_kalir_onayli_gecer; H-001 4; S-001 6 | taşınır | core.checks | Saf ve testli; takım erişimi hâlâ yok |
| `olcme_belirsizligi.py` | 54 | OLCU-01 (kritik geçmede U ≤ bant/4) ve OLCU-02 (kritik geçmede geçersiz ölçüm aleti) | cekirdek: kumpas_ortalama_gecmede_sinirda_gecer, lidar_kritik_gecmede_kalir; H-001 5; S-001 4 | taşınır | core.checks | Saf ve testli |
| `onay_durumu.py` | 33 | ONAY-01: Kesinleştirme'de açık Hold, kapanmamış ya da reddedilmiş kart, incelenmemiş karar, düşmüş onay | cekirdek: kesinlestirmede_acik_kart_engel; akis: kesinlestirmede_baski_kendi_hold_kartina_takilmaz; S-001 8 | taşınır | core.checks | Saf ve testli |
| `sonuc.py` | 40 | `Sonuc` veri sınıfı, aşamaya göre seviye (§10: Kesinleştirme'de ENGEL, öncesinde UYARI), mm biçimi | bütün kontrol testleri | taşınır | core.checks | Saf |

## 3. CLI (`cli/surec_cli/ana.py`, 451 satır; `__init__.py` boş)

Alt komutlar doğrudan yalnız iki testte çağrılır: `onay` (akis: cli_onay_terminal_ister) ve `durum-yaz` (e2e 7). Ötekiler yalnız arkalarındaki çekirdek fonksiyonun testleriyle sınanır.

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `ana.py` genel (`main`, argparse, `RENK`, `ROLLER`, `kontrol_raporu`, `_kok`, `PANEL_PORTU = 8765` K-21) | 451 | Komut ayrıştırma, renkli çıktı, kontrol raporu Markdown'u | yukarıdaki iki test | yeniden yazılır | cli | Türkçe komut adları ve tek dosya; v1'de komut grupları ve eklentilerin kendi komutları |
| `cli/surec_cli/__init__.py` | 0 | Boş | — | taşınmaz | — | İçerik yok |
| `doktor [--json]` | 16–31 | Ortamı denetler | onbellek: doktor_bos_alan_azsa_uyari (fonksiyon) | yeniden yazılır | cli: `doctor` | `ortam.py` ile birlikte; paket başına denetim |
| `regresyon` | 34–45 | Bütün hata vakalarını çalıştırır, alt vaka başına ✓/✗ | regresyon (fonksiyon) | taşınır | cli: `regress` | Davranış aynen |
| `kontrol [kod] [--json]` | 63–80 | Kontrolleri çalıştırır; JSON + Markdown; `kontrol.json` önbelleğe; ENGEL'de çıkış 1 | — | taşınır | cli: `check` | Davranış aynen; E-40 için "okuma komutu ağacı kirletmez" testi eklenmeli |
| `yeni-calisma <kurum> <proje> <ad> <sinif> [--amac --bitti]` | 83–88 | Kodu verir, klasörü ve dalları açar, `calisma.yaml` ve O-G0 kartı | akis (fonksiyon) | yeniden yazılır | cli: `work new` | Kurum config'ten, G0 soru ağacı (core.intake) |
| `ac <kod> [--claude --claude-ayarlari]` | 91–96 | Worktree + tmux oturumu (en çok 3); isteğe bağlı ajan ayarları | akis (fonksiyon) | yeniden yazılır | cli: `work open` | tmux ve `.claude/` yazımı agent adaptörüne |
| `arsivle <kod> --neden` | 172–176 | Çalışmayı arşive alır; silmez | akis (fonksiyon) | taşınır | cli: `work archive` | Davranış aynen |
| `kapat <kod>` | 99–104 | tmux oturumunu kapatır; hiçbir şey silinmez | akis (fonksiyon) | taşınır | cli: `work close` | Davranış aynen |
| `gec <kod>` | 107–111 | O çalışmanın tmux oturumuna geçer | akis (fonksiyon) | taşınır | cli: `work attach` | Davranış aynen (adaptör üstünden) |
| `adim <baslik> --rol [--aciklama --kart --gorsel --sonraki]` | 120–127 | El kitabı biçimiyle commit, önbellek, günlük | akis (fonksiyon) | taşınır | cli: `step` | Davranış aynen; ekler İngilizce |
| `asama-bitir <kapi>` | 130–137 | Kapı listesini çalıştırır, O-Gn kartı açar (Hold) | akis (fonksiyon) | taşınır | cli: `gate request` | Davranış aynen |
| `baski` | 140–145 | Baskı Hold'u: dosyalar, B kartı | akis (fonksiyon) | yeniden yazılır | cli: `fdm print-request` (pkg_fdm komutu) | Alan paketine çıkar; baskı ayarı zorunlu (E-41) |
| `onay <kart> --karar onay/ret/yorum/geri-al [--not --secenek --satir]` | 148–169 | Yalnız BM: TTY ister, kart numarası yeniden yazılarak teyit | akis: cli_onay_terminal_ister | taşınır | cli: `approve` / `reject` / `comment` / `revert` | Güvence (TTY + yeniden yazma) aynen; kimlik config'ten |
| `yanitla <kart> --yanit [--yorum --commit --rol]` | 179–184 | Ekip BM yorumunu yanıtlar | akis (fonksiyon) | taşınır | cli: `reply` | Davranış aynen |
| `bekleyenler [--kanca]` | 187–209 | Yanıt bekleyen yorumlar; `--kanca` Claude Code kancası JSON'u | — | taşınır | cli: `pending [--hook]` | Kanca biçimi agent adaptörüne |
| `karar <no> <baslik> --secenek/--tanim --gerekce [--bagimli --tur --dalsiz]` | 212–225 | Karar kaydı; geçici kararda seçenek dalları | akis (fonksiyon) | taşınır | cli: `decision open` | Davranış aynen |
| `durum-yaz [--kod]` | 228–231 | Kanca girişi: oturum durumunu yazar (stdin JSON) | e2e 7 | taşınır | cli: `agent hook` (iç komut) | Adaptörün iç komutu |
| `durum` | 267–271 | Ajan oturumlarının durumu | — | taşınır | cli: `agent status` | Davranış aynen |
| `gozcu` | 243–246 | BM commit'lerini izler, satır yazar | — | taşınır | cli: `watch` | Davranış aynen |
| `kalite [--konu]` | 249–256 | Kalite incelemesini çalıştırır | — | taşınır | cli: `review` | Davranış aynen |
| `kalite-kapat <rapor> <bulgu> --not [--commit]` | 259–264 | Kalite bulgusunu gerekçeyle kapatır | akis (fonksiyon) | taşınır | cli: `review close` | Davranış aynen |
| `nabiz <kod> [--rol --is --durdu]` | 234–240 | Ekip nabzını yazar | — | taşınır | cli: `pulse` | Davranış aynen |
| `gecis-plani [--girdi --onizleme]` | 285–299 | ustteknik-arge geçiş planı (kuru çalıştırma) | gecis | taşınmaz | — | Üstteknik'e özgü, K-28 ile rafta |
| `panel [--port]` | 278–282 | Paneli 127.0.0.1'de başlatır | e2e (uygulama.calistir) | taşınır | cli: `panel serve` | Davranış aynen |

v1'de CLI'ye eklenmesi gerekenler (bugün yalnız panelde ya da hiç yok; sayıma girmez): `value set` (`akis.deger_gir`), `print withdraw` (`akis.istek_geri_cek`), `branch from` (`veriler.dal_ac`), `gate back` (Ö-17, kodda yok).

## 4. Panel arka ucu (`panel/backend/surec_panel/*.py`)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `__init__.py` | 0 | Boş | — | taşınmaz | — | İçerik yok |
| `uygulama.py` · güvenlik ve yazma kuralları (`IZINLI_HOST`, `_host_izinli`, Host/Origin/JSON ara katmanı, hata işleyicileri, `_vaka_degil`, `_teyit_gerekir`) | ~25–91, 276–300 (~80) | Yalnız 127.0.0.1 + izinli Host (`SUREC_PANEL_HOSTS`); yazmada aynı köken Origin ve JSON (K-21, DNS rebinding ve CSRF önlemi); teyitsiz Hold/karar onayı reddi (Ö-14); regresyon vakasına yazma yok | e2e 8, 1, 12 | taşınır | panel (backend ara katmanı) | Testli güvenlik kuralları; aynen |
| `uygulama.py` · uç noktalar ve çalıştırma (28 uç, aşağıdaki tablo; `calistir`, açılışta model ısıtma) | ~92–415 (~320) | Okuma ve yazma uçları, SSE akışı, ön yüz dosyaları | e2e 1–17 | yeniden yazılır | panel (FastAPI) | Yollar ve alanlar İngilizce; core API'sine bağlanır; TS istemci OpenAPI'den üretilebilir |
| `veriler.py` · okuma katmanı (kurumlar, ağaç, çalışma özeti, aşamalar, etkinlik, kartlar, tasarım dosyası, okundu, dal haritası, hesaplar, durum ekranı/top kimde, canlılık, adım ayrıntısı/params farkı, yardımcı worktree) | ~730 | Panelin okuma katmanı; doğruluk kaynağı repo (etiket, commit eki, dosya); `--no-optional-locks` (E-20); kirli klasörde HEAD'i önbellekten gösterir | e2e 1–17 | yeniden yazılır | panel + core.report + core.store (okuma API'si) | `SUREC_KOK/kurumlar` ve `testler/vakalar`'dan okur, yardımcı worktree `~/.cache/surec/dallar`; v1'de store okuma API'si ve config |
| `veriler.py` · dosya indirme (`DOSYA_KLASORLERI`, `_sha256`, `dosyalar`, `indirilecek`) | 577–624 (~48) | Yalnız `cikti/` ve `deney/` indirilir, klasör dışına çıkış yok; SHA-256 onay raporuyla karşılaştırılır | e2e 16 | taşınır | panel | Yol güvenliği testli; aynen |
| `veriler.py` · `dal_ac` | 541–553 (~13) | Geçmiş bir noktadan yeni iş dalı; hiçbir şey silinmez | e2e 5 | taşınır | core.store (+ panel ucu) | Testli; dal adı doğrulaması korunur |
| `model_servisi.py` | 313 | Commit modeli (önbellekte yoksa geçici worktree'de üretim, bellekte en çok 6, üretim kilidi); OCC katılarından ölçüm (three-cad-viewer dış ölçüm sözleşmesi); silindirler; geçme eksenleri; kesit | e2e 2, 3, 9, 10, 11 | taşınır | cad (ölçüm, kesit) + panel (servis) | Testli; yalnız adlandırma |
| `izleyici.py` | 141 | watchdog ile ortak `.git`'te ref değişimi → SSE (sunucudan tarayıcıya olay akışı) "yeni-surum"; durum dosyası → "durum"; 0,8 s erteleme (varsayim) | e2e 6, 7 | taşınır | panel | Testli; yalnız adlandırma |

### Uç noktalar (yeniden adlandırma önerisi; sayıma girmez)

| eski | v1 önerisi | test |
| --- | --- | --- |
| GET `/api/agac` | GET `/api/tree` | e2e (her test), 8 |
| GET `/api/sekmeler` | GET `/api/tabs` | e2e (her test) |
| GET `/api/calisma/{kod}` | GET `/api/works/{code}` | e2e (her test) |
| GET `…/asamalar` | GET `…/stages` | e2e 2 |
| GET `…/durum` | GET `…/status` | e2e 2, 7 |
| GET `…/dosyalar` | GET `…/files` | e2e 16 |
| GET `…/indir/{yol}` | GET `…/download/{path}` | e2e 16 |
| GET `…/adim/{sha}` | GET `…/steps/{sha}` | e2e 15 |
| GET `…/canlilik` | GET `…/liveness` | e2e 7 (dolaylı) |
| GET `…/hesaplar` | GET `…/calcs` | e2e 14 |
| GET `…/kartlar` | GET `…/cards` | e2e 1, 4, 10, 12, 13 |
| GET `…/gecme-isaretleri` | GET `…/fit-markers` | e2e 10 |
| GET `…/kesit/{gecme}` | GET `…/sections/{fit}` | e2e 9 |
| GET `/api/kartlar` | GET `/api/cards` | yok |
| GET `…/dosya` | GET `…/design-file` | yok |
| POST `…/okundu` | POST `…/read-mark` | e2e 8 (yalnız güvenlik) |
| GET `…/dallar` | GET `…/branches` | e2e 5 |
| GET `…/gorsel/{yol}` | GET `…/images/{path}` | e2e 12 (dolaylı) |
| GET `…/model` | GET `…/model` | e2e 2, 3, 11 |
| GET `…/silindirler` | GET `…/cylinders` | e2e 3 |
| POST `/api/olc` | POST `/api/measure` | e2e 3 |
| POST `…/kart/{no}` | POST `…/cards/{no}/decision` | e2e 1, 4, 8, 12, 13 |
| POST `…/model-notu` | POST `…/model-notes` | e2e 17 |
| POST `…/kart/{no}/geri-al` | POST `…/cards/{no}/revert` | e2e 12, 13 |
| POST `…/deger` | POST `…/values` | e2e 4 |
| POST `…/dal-ac` | POST `…/branches` | e2e 5 |
| GET `/api/olaylar` (SSE) | GET `/api/events` | e2e 6, 7 |
| GET `/{yol}` | statik ön yüz | e2e (her test) |

## 5. Panel ön yüzü (`panel/frontend/`)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| Yapılandırma: `index.html` (15), `package.json` (19; three-cad-viewer 5.1.3, vite 8.3.5, typescript 6.0.2), `tsconfig.json` (14), `vite.config.ts` (7), `package-lock.json` (955) | 1010 | Vite + TS derlemesi, `/api` vekili | e2e (derlenmiş `dist/` ister) | taşınır | panel (ön yüz) | Sabit sürümler korunur; kilit dosyası yeniden üretilir |
| `src/api.ts` | 44 | Sunucu uçlarının istemcisi; `{hata}` cevabında hata fırlatır | dolaylı: bütün e2e | yeniden yazılır | panel | Uçlar İngilizceye döner; OpenAPI'den üretilmeli |
| `src/main.ts` | 200 | Kabuk: üst satır, çalışma sekmeleri (en çok 3), ekran yönlendirme, SSE, 15 s'de bir nabız sorma, bildirim | dolaylı: bütün e2e; 6, 7 | yeniden yazılır | panel | Rota ve ekran listesi İngilizce; "Taha" varsayılan kimliği config'ten |
| `src/genislet.ts` | 62 | Sütunları sürükleyerek genişletme, `localStorage`'da hatırlama (E-09) | yok | taşınır | panel | Bağımsız yardımcı; yeni test gerekir |
| `src/goruntuleyici.ts` | 111 | three-cad-viewer sarmalayıcısı; dış ölçüm arka ucu; sürüm karşılaştırma; geçme işaretleri | e2e 2, 3, 10, 11 | taşınır | panel | Testli; yalnız adlandırma |
| `src/isaretle.ts` | 168 | Model notu: alan sürükleme, ışın izleme, ekran görüntüsü, açık not işaretleri | e2e 17 | taşınır | panel | Testli |
| `src/maskot.ts` | 44 | "Top" maskotu ve nabız rozeti | e2e 7, 15 | taşınır | panel | Testli |
| `src/yardim.ts` | 54 | Güvenli HTML kaçışı, Türkçe sayı ve saat biçimi, rol rozetleri, durum renkleri | dolaylı | taşınır | panel (çeviri katmanına bağlanır) | Saf yardımcılar; doğrudan test (özellikle HTML kaçışı) gerekir |
| `src/stil.css` | 209 | Panel stili; görüntüleyicinin `body` üstündeki `overflow:hidden; user-select:none`'unu geri alır (E-08); kart görseli boy sınırı (E-10) | yok | taşınır | panel | Görsel kurallar; E-08 için e2e testi gerekir |
| `src/vite-env.d.ts` | 2 | Vite tip başvurusu | — | taşınır | panel | Önemsiz |
| `src/ekranlar/asamalar.ts` | 112 | Durum içindeki aşama bölümü: kapı kartları, seçili aşamanın ayrıntısı (mini 3B, adımlar, kararlar, kontroller) | e2e 2 | yeniden yazılır | panel | API alanları İngilizceye döner; düzen ve davranış e2e testleriyle korunur |
| `src/ekranlar/ciktilar.ts` | 59 | Dosyalar: onaylı baskı klasörleri, SHA kontrolü, `KULLANMA.md` kırmızı, `deney/` | e2e 16 | yeniden yazılır | panel | Aynı gerekçe |
| `src/ekranlar/dallar.ts` | 176 | Dal haritası; "bu noktadan dal aç" (hiçbir şey silinmez) | e2e 5 | yeniden yazılır | panel | Aynı gerekçe |
| `src/ekranlar/dosya.ts` | 88 | Tasarım dosyası: son okumandan beri, günlük, güncel durum | yok | yeniden yazılır | panel + core.report | Aynı gerekçe; ekranı açan e2e testi yok |
| `src/ekranlar/durum.ts` | 74 | Açılış ekranı: top kimde, senden ve ekipten beklenenler | e2e 2, 7 | yeniden yazılır | panel | Aynı gerekçe |
| `src/ekranlar/ekip.ts` | 156 | Ajan şeması, rol tablosu (Taha sabit), yapılan işlerin ayrıntısı | e2e 15 | yeniden yazılır | panel + agent | Rol ve model adları config'ten |
| `src/ekranlar/hesaplar.ts` | 101 | Hesap ve analiz ayrıntısı, grafik, güvenli SVG (betik ve dış bağlantı ayıklanır) | e2e 14 | yeniden yazılır | panel | Aynı gerekçe; SVG temizleme kuralı korunur |
| `src/ekranlar/kartlar.ts` | 348 | İnceleme kuyruğu, kart standardı görünümü, teyit penceresi (Ö-14), geri alma, V-01 satır seçimi, isteklere etkisi tablosu | e2e 1, 4, 9, 12, 13 | yeniden yazılır | panel | Aynı gerekçe |
| `src/ekranlar/model.ts` | 118 | Görüntüleyici, özellikler, geçme tablosu, ölçüm listesi, not düğmesi | e2e 3, 10, 11, 17 | yeniden yazılır | panel | Aynı gerekçe |
| `src/ekranlar/ortak.ts` | 63 | Gezinti, sol ağaç, dal seçici, alt çubuk (`github.com/tahatas013` el kitabı bağlantısı) | dolaylı | yeniden yazılır | panel | Kişisel bağlantı kalkar; aynı gerekçe |

## 6. Kural kataloğu (`kurallar/katalog.yaml`, 74 satır)

Her kural v1'de standart kütüphanesine (stdlib) veri olarak, kontrol bağıyla birlikte gelir. Dayanaktaki "H-001 kök neden n" atıfları gerçek kurum verisine işaret ettiği için sentetik vakaya ya da adsız ders kaydına çevrilir.

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| Katalog başlığı (`surum: v0`, `tarih`, `onaylayan: Taha`) | 1–5 | Sürüm ve onaylayan | — | yeniden yazılır | stdlib | Onaylayan config'teki kişiden; v1 sürüm numarası |
| KAYNAK-01 | 8–13 | Her ölçünün kaynak etiketi var; her aşamada ENGEL | kaynaksiz testleri; H-001 1; S-001 1 | taşınır | stdlib + core.checks (`kaynaksiz`) | Dayanak el kitabı §1, §9, §10 |
| GECME-01 | 15–19 | Tek nominal + tek boşluk; iki bağımsız sabit sayı yok | bagimsiz_sayi testleri; H-001 1; S-001 2 | taşınır | stdlib + core.checks | — |
| GECME-02 | 21–25 | Boşluk görev bandında (profil) | gecme_boslugu testleri; H-001; S-001 3 | taşınır | stdlib + core.checks | Dayanak ISO 286-1 |
| VIDA-01 | 27–31 | Cıvata geçiş deliği ISO 273 ince seri (M4 → Ø4,3; M6 → Ø6,4) | gecme_boslugu; H-001 7a | taşınır | stdlib (standart maddesi + tablo) + core.checks | Tablo profilden stdlib'e çıkmalı (standart verisi) |
| OLCU-01 | 33–37 | Kritik geçmede U ≤ bant/4 | olcme_belirsizligi testleri; H-001 5; S-001 4 | taşınır | stdlib + core.checks | Dayanak ISO 14253-1, Z540.3, GUM |
| OLCU-02 | 39–43 | Kritik geçmede geçersiz ölçüm aleti (iPhone LiDAR) | lidar_kritik_gecmede_kalir | taşınır | stdlib + core.checks | Kural genelleşir: "aletin `kritik_gecme` geçerliliği yoksa kalır"; dayanak Yanchuk vd. (literatür) |
| KATI-01 | 45–49 | Her parça geçerli, kapalı katı | girisim; S-001 5 (ref A) | taşınır | stdlib + core.checks | — |
| GIRISIM-01 | 51–56 | Kesişim hacmi ≤ 0,001 mm³ (varsayim) | girisim_yakalanir…; S-001 5 | taşınır | stdlib + core.checks | Eşik varsayim; kart açar |
| MONTAJ-01 | 58–62 | Her esneme BM onaylı | onaysiz_esneme…; H-001 4; S-001 6 | taşınır | stdlib + core.checks | Dayanak "H-001 (K kulağı 3,2 mm)" adsızlaştırılır |
| KAYITSIZ-01 | 64–68 | Eş eksenli, çap farkı < 3 mm silindirler kayıtta | kayitsiz_gecme testleri; S-001 7 | taşınır | stdlib + core.checks | 3 mm karar; K1'de yalnız UYARI notu güncellenir |
| ONAY-01 | 70–74 | Serbest bırakmada açık Hold yok, incelenmemiş karar yok, onay özetleri güncel | onay_durumu testleri; S-001 8 | taşınır | stdlib + core.checks | Dayanak §10, ISO 9001 madde 8.3 |
| HESAP-01 (katalogda yok) | — | Aynı büyüklük iki hesapta > %10 farklı → UYARI, düşük doğruluklu "yerini aldı" | akis: tutarlilik_ve_dayanak…; S-001 9 | taşınır | stdlib + core.checks | Kodda var, katalogda yok (Ö-22); kataloğa girmesi BM onayı ister |
| HESAP-02 (katalogda yok) | — | Kötü ya da güvenilmez sonuçlu hesap UYARI; onay gerekçe ister | S-001 9 | taşınır | stdlib + core.checks | Ö-23; gerekçe şartının testi yok |
| KARAR-01 (katalogda yok) | — | Kapanmış kararın dayanağı değişti ya da yerini daha doğru hesap aldı → kart | akis: tutarlilik_ve_dayanak…; S-001 10 | taşınır | stdlib + core.decisions/checks | Ö-24 |
| Kimliksiz: tabla teması (E-25) | — | Baskıda havada kalan alt yüz reddi | cekirdek: tabla_temasi_kusuru | taşınır | stdlib (yeni kimlik, ör. FDM-TABLA-01) + pkg_fdm | Kural kimliği ve dayanak (PLU B-01 olayı, adsız) gerekir |
| Kimliksiz: ayrık katı (E-28) | — | Tek parçada birden çok ayrık katı varsa baskı reddi | yok | taşınır | stdlib (yeni kimlik) + pkg_fdm | Test ve kimlik gerekir |
| Kimliksiz: kart standardı (Ö-10) | — | Metni ya da görseli eksik açık kart açılamaz (adım ENGEL) | akis: kart_standardi… | taşınır | stdlib (ör. KART-01) + core.cards | Kimlik gerekir |
| Kimliksiz: kalite engeli (Ö-20) | — | Açık YÜKSEK bulgu varken kapı/baskı isteği açılmaz | akis: kalite_yuksek… | taşınır | stdlib (ör. KALITE-01) + core.quality | Kimlik gerekir |

Onaylanmamış önerilen kural: KOSE-01 (Ö-16, iç köşe yarıçapı). Kodda yok; v1'e ancak BM onayından sonra girer.

## 7. Profiller (`profiller/**`)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `profiller/uretim/fdm-bambu-a1-pla.yaml` | 38 | Bambu Lab A1 + PLA, v0, geçici; görev başına boşluk bandı (çoğu varsayim, ortalama/dönme üst sınırı karar), ISO 273 tablosu, model düzeltme payı ve baskı yönü boş | cekirdek profil testleri; H-001 ve S-001 bu profille | taşınır | config (`~/.config/<ad>/` makineler) | Atölyeye özgü; v1 reposuna yalnız adsız örnek şablon ve test fikstürü girer; `onaylayan: Taha` config kişisinden; E-01 için `printer.bed`/`nozzle` alanı eklenir |
| `profiller/uretim/fdm-cr10se-pla.yaml` | 39 | CR-10 SE + PLA, v0, hepsi varsayim, onaylayan yok (K-25) | yok | taşınır | config (makineler) | Aynı; onaylanmamış profil olarak |
| `profiller/olcum/kumpas.yaml` | 12 | Kumpas, ±0,05 mm (varsayim), kritik geçmede geçerli | kumpas_ortalama_gecmede_sinirda_gecer | taşınır | config (ölçüm aletleri) | Aynı |
| `profiller/olcum/iphone-lidar-kiri.yaml` | 18 | iPhone LiDAR (KIRI Engine), ≥ 1 mm (varsayim, alt sınır), kritik geçmede geçersiz | lidar_kritik_gecmede_kalir | taşınır | config (ölçüm aletleri) | Kişinin aleti; dayanak (Yanchuk vd.) stdlib literatürüne |

## 8. Ajan şablonları, ayarlar, paketleme, kurum dosyaları

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `ajanlar/README.md` | 9 | Divan şablonlarının tablosu (model ve iş) | — | yeniden yazılır | agent (şablon belgesi) | "`surec ac` kopyalar" ifadesi K-11 ile eskidi |
| `ajanlar/kalite-muhendisi.md` | 17 | opus, salt okunur araçlar; ilkeler listesiyle tek tur inceleme; çıktı `[YÜKSEK/ORTA/DÜŞÜK] dosya:satır — sorun — ilke — kanıt` | dolaylı (kalite testi sahte inceleyici kullanır) | yeniden yazılır | agent (quality-engineer) | Açıklaması "yalnız Kesinleştirme'de"; B1 ile her kapıda çalışıyor. Çıktı biçimi `kalite.SATIR` ayrıştırıcısıyla aynı kalmalı (test gerekir) |
| `ajanlar/tasarim-muhendisi.md` | 17 | sonnet; brief'le tek parça/tek yön; params dışında sayı yok; tek nominal + boşluk | — | taşınır | agent (design-engineer) | İçerik geçerli; yalnız dosya adı |
| `ajanlar/tekniker.md` | 15 | haiku; yalnız komut çalıştırır, karar vermez; GEÇTİ/KALDI | — | taşınır | agent (technician) | İçerik geçerli; yalnız dosya adı |
| `.claude/settings.json` | 65 | İzin listesi (allow/ask/deny): ask'te sudo, push, gh, curl, systemctl, tailscale ve süreç belgeleri; deny'da `rm -rf`, force push, ustteknik-arge düzenleme, `.ssh` okuma | — | yeniden yazılır | agent (claude_code adaptörü: izin şablonu config'ten üretilir) | `/home/tahatas013/...` kişisel yolları ve ustteknik-arge içerir; `izin-onerileri.md` deny ekleri (surec onay, git tag, git config, `--author`) girmemiş; E-34 |
| `panel/sistem/surec-panel.service` | 17 | systemd kullanıcı servisi; `%h/surec`, `surec panel --port 8765` | — | taşınır | panel (dağıtım) | `%h` kullanıyor, kişisel ad yok; birim adı ve komut v1 adına; kurulumu Hold (BM yapar) |
| `pyproject.toml` | 40 | Tek paket `surec`: üç kaynak klasörü, bütün bağımlılıklar tek listede, Python 3.12, pytest `panel` işareti | — | yeniden yazılır | v1 paket düzeni | core / cad / panel / pkg_fdm / pkg_aero / pkg_mold için ayrı ek gruplar: aerosandbox → pkg_aero; tetgen, scikit-fem, meshio → analiz; cadquery, ocp-tessellate, manifold3d, trimesh → cad; fastapi, uvicorn, watchdog → panel |
| `uv.lock` | — | Bağımlılık kilidi | — | yeniden yazılır | v1 kökü | Yeni pyproject'ten `uv lock` ile yeniden üretilir |
| `.python-version` | 1 | `3.12` | — | taşınır | v1 kökü | Aynen |
| `.gitignore` | 26 | venv, önbellek, `node_modules`, `panel/frontend/dist`, `.env`, `.claude/settings.local.json`, log | — | taşınır | v1 kökü | Aynen |
| `kurumlar/bag/kurum.yaml` | 12 | Bağımsız kurum: onay yetkilisi Taha, `yerel: ~/is/bag`, projeler TST (arşiv), PLU | — | taşınmaz | — | Kurum verisi ve kişisel yol; şeması v1'de config kurum şemasına dönüşür |
| `kurumlar/ust/kurum.yaml` | 13 | Üstteknik: `repo: tahatas013/ustteknik-arge`, arşiv yolları, projeler DZL, KLB | — | taşınmaz | — | Üstteknik verisi |

## 9. Testler (`testler/`)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `test_akis.py` | 745 | 36 test. K2 kabul: G0 → G3, günlük, karar dalları, en çok 3 aktif, baskı Hold'u, ana hatta yazma yasağı, kancalar, CLI onayı TTY, kimlik koruması, içeriğe bağlı kapı onayı, yarım kalmayan geçiş, kart numarası, kirli klasör, eski sürüm, kart standardı, geri alma, arşiv, yorum–yanıt, hesap, karar hataları (E-15, E-17, E-21, E-24), model notu, B1, B3/B5, B7 | — | taşınır | v1 kabul testleri (core.flow, core.store, core.decisions, core.cards) | Senaryolar aynen; çağrılar v1 API'sine uyarlanır; "Taha Test" kimliği ve `BAG-TST` kodu nötr adlarla değişir |
| `test_cekirdek.py` | 457 | 42 test (parametrize ile 62 durum). K1 kabul: şema, kaynaksız, bağımsız sayı, onay özeti, geçme bantları, esneme, girişim, kayıtsız geçme, kart numaraları, STEP/STL, ölçme belirsizliği, profil/belirsizlik değişince onayın düşmesi, kesit, tabla yerleşimi ve teması, temiz ağ, analiz önbelleği | — | taşınır | core.model, core.checks, core.cards, cad, pkg_fdm testleri | Senaryolar aynen; alan adları İngilizce |
| `test_gecis.py` | 76 | 4 test: etiket eşlemesi, ayrıştırma, geçme dönüşümü, kuru çalıştırma (girdi yoksa atlanır) | — | taşınmaz | — | `gecis.py` taşınmıyor |
| `test_onbellek.py` | 60 | 6 test: LRU silme, sınır altında silmeme, korunan giriş, 5 GB, doktorda disk uyarısı, commit adı olmayan klasör | — | taşınır | core.evidence, cli (doctor) | Aynen |
| `test_panel_e2e.py` | 522 | 17 test (Playwright, başsız Chromium, `-m panel`): kapı onayı ve teyit, 3B açılması, kesit ve tam geometriden çap, onayın düşmesi, dal açma, yeni sürüm bildirimi, ajan izin beklerken, Host/Origin/dal güvenliği, geçme kesiti, renkli işaretler, kesit kapağı, karar kartı, V-01, hesaplar, ekip, dosyalar, model notu | — | taşınır | panel e2e testleri | Senaryolar aynen; seçiciler ve uçlar yeni ön yüze uyarlanır |
| `test_regresyon.py` | 32 | 2 test (parametrize ile 19 durum): bütün vakalar geçer; her kontrolün "hep ENGEL" ve "hep GEÇTİ" sahte sürümü regresyondan geçemez | — | taşınır | core.checks | Aynen |
| `vakalar/H-001/` (8 dosya: `KAYNAK.md`, `beklenen.yaml`, `calisma.yaml`, `gecmeler.yaml`, `kararlar.yaml`, `montaj.yaml`, `onaylar.yaml`, `params.yaml`) | 115 | Üstteknik P1-N1 menteşesinin dondurulmuş kopyası; 8 alt vaka (1, 2, 3, 4, 5, 6, 7a, 7b) | regresyon | yeniden yazılır | core.checks test verisi: sentetik vaka | Kesin kural: gerçek kurum verisi yok. Aynı sayılarla (3,0 mm ortalama, 1,0 mm dönme, 1,0 mm kayma + varsayım, kaynaksız Ø14, onaysız 3,2 mm esneme, kritik geçmede LiDAR, 0,5 mm GEÇTİ, M4 Ø4,3 GEÇTİ, görevsiz 0,2 bindirme) uydurma parça adlarıyla yeniden kurulur; `KAYNAK.md` (ustteknik-arge commit'i, dizlik yolları) taşınmaz |
| `vakalar/S-001/` (10 dosya: `beklenen.yaml`, `calisma.yaml`, `gecmeler.yaml`, `kararlar.yaml`, `montaj.yaml`, `onaylar.yaml`, `params.yaml`, `model/model.py`, `kayit/hesaplar/h_elle.json`, `h_vlm.json`) | ~200 | Sentetik vaka; her kontrol için GEÇTİ ve KALDI; 10 alt vaka (HESAP-01, KARAR-01 dahil) | regresyon | taşınır | core.checks test verisi | Zaten sentetik; `onaylar.yaml`'daki `kim: Taha` ve `BAG-TST-01` kodu nötr adlarla değişir |

## 10. Belgeler

### El kitabı (`el-kitabi.md`, 386 satır, sürüm 0.2)

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| Başlık ve sürüm satırı | 1–3 | Sürüm 0.2, onaylayan Taha | — | yeniden yazılır | v1 el kitabı (belge katmanı) | Sürüm ve onaylayan config kişisinden |
| §1 Amaç, kapsam, ilkeler | 5–28 | Kapsam, kurum profili, BAG, sekiz ilke | — | yeniden yazılır | v1 el kitabı + core değişmezleri | İlkeler aynen; "ilk uygulayıcı Üstteknik" ve magnet/dizlik örnekleri çıkar |
| §2 Dayanak standartlar | 30–52 | 17 satırlık standart ve literatür tablosu | — | taşınır | stdlib (standart maddeleri, dayanaklar) | Veri olarak aynen; "ürüne özel (dizlik) EN 1621-1" ürün bağı olmadan kalır |
| §3 Belge yapısı | 54–68 | Beş belge katmanı ve repo yerleri | — | yeniden yazılır | v1 el kitabı | v1 katmanları (çekirdek, paketler, stdlib, atölye ayarı, çalışma verisi) farklı; `surec/...` yolları ve ustteknik-arge çıkar |
| §4 Roller ve ekip modeli | 70–89 | Rol tablosu, divan kuralları | — | yeniden yazılır | agent (rol tanımları) + config (kişi) | Taha ve model adları config'ten; divan kuralları aynen |
| §5 Risk sınıfları | 91–110 | A/B/C, dört G0 sorusu, sınıf kuralı | akis: g0_dan_g3… (sınıf, kapılar) | taşınır | core.flow (`SINIF_KAPILARI`) + core.intake (G0 soru ağacı) | Kural aynen; Ö-26 (deney → G4) onayla eklenir |
| §6 Yaşam döngüsü ve kapılar | 112–129 | G0–G5 tablosu, kapı soruları ve kontrol listesi | akis kapı testleri | taşınır | core.flow (kapı motoru) | Aynen; G3 → G2 dönüş yolu (Ö-17) ve G2 risk kaydı maddesi (E-31) eksik |
| §7 Karar seviyeleri, tetikleyiciler, onay | 131–162 | Hold/geçici/inceleme/bildir, soru tetikleyicileri, kart içeriği, BM seçenekleri, kayda geçenler | kartlar, onay testleri | taşınır | core.cards + core.decisions + core.flow | Aynen; onaylanırsa Ö-01, Ö-07, Ö-09…Ö-15, Ö-24, Ö-25, Ö-27 işlenir |
| §8 Hiyerarşi, adlandırma, sürüm, dallar | 164–205 | Kurum → proje → çalışma, kod kuralları, dal ve etiket adları, en çok 3 aktif, birleştirme | akis dal/etiket testleri | yeniden yazılır | core.store + config (kurumlar) | "Mevcut işler: UST-DZL-01…" satırı Üstteknik verisi; ad kuralları aynen kalır |
| §9 Ölçü, kural, profiller | 207–241 | Kaynak etiketleri, geçme kaydı, kural katmanları, üretim ve ölçüm profilleri | veri, kontrol testleri | taşınır | core.model + stdlib + config + pkg_fdm/pkg_mold | Aynen; `uretici:` (Ö-12), `oran` (Ö-06), `literatur:` (Ö-28) onaya bağlı |
| §10 Kontroller ve serbest bırakma | 243–272 | Kontrol tablosu, G5 dört şartı, bağımsız inceleme, regresyon | kontrol ve regresyon testleri | taşınır | core.checks + core.quality + stdlib | Aynen; "Üretilebilirlik" satırı kodda yok (E-04 → pkg_fdm/pkg_mold); bağımsız sayı satırı (Ö-02) ve HESAP satırları eklenir |
| §11 Tasarım dosyası | 274–294 | Son okumandan beri, günlük, güncel durum; yazma kuralları | akis günlük testleri | taşınır | core.report | Aynen |
| §12 Panel, gözlem, altyapı | 296–329 | Panel sayfaları, görüntüleyici katmanı, altyapı tablosu, izin listesi | e2e | yeniden yazılır | panel + agent + config | Beş ekran bugün altı sekme (Durum, Ekip, Model, Kartlar, Tasarım dosyası, Dal haritası); Ubuntu makinesi ve Tailscale satırları atölye ayarına |
| §13 Hatalardan öğrenme | 331–352 | 8D hata kaydı alanları; H-001 örneği | regresyon | yeniden yazılır | core (hata kaydı şeması) + stdlib (dersler) | Yöntem aynen; H-001 örneği sentetik örnekle değişir |
| §14 Açık konular ve uygulama sırası | 354–386 | Kurulum sırası, açık konular (maliyet eşiği, açık geçici karar sınırı 5, kayıt başına 3 görsel, repo adı) | — | taşınmaz | — | Kurulum planı ve makineye özgü; varsayılanlar (5, 3) varsayim etiketiyle config'e |

### Öteki belgeler ve kayıtlar

| öğe | satır | ne yapar | testleri | karar | v1 hedef | gerekçe |
| --- | --- | --- | --- | --- | --- | --- |
| `CLAUDE.md` | 74 | Kalıcı kurallar özeti: roller, dil, zaman, sayılar, adlandırma, Hold listesi, divan, commit biçimi, ortam | — | yeniden yazılır | agent (claude_code adaptörü: proje talimatı şablonu) | Kişi, Hold listesi ve yollar config'ten; kurallar (sistem saati, kaynaksız sayı yok, tek nominal + boşluk, ekip ana hatta yazmaz) aynen; commit ekleri İngilizce |
| `hata-kayitlari/H-001.md` | 54 | P1-N1 menteşe hata kaydı, kök nedenler, önlemler, regresyon beklentisi | regresyon (H-001) | taşınmaz | — | Üstteknik verisi; dersi adsız biçimde stdlib dayanağına ve sentetik vakaya geçer |
| `prosedurler/README.md` | 4 | Yer tutucu | — | taşınmaz | — | İçerik yok; v1 belge katmanında yeniden açılır |
| `talimatlar/README.md` | 4 | Yer tutucu | — | taşınmaz | — | İçerik yok |
| `panel/README.md` | 3 | "K3'te yazılır" notu | — | taşınmaz | — | Eskimiş |
| `kayit/kurulum/el-kitabi-onerileri.md` | 34 | Ö-01…Ö-28 | — | taşınmaz | — | Kurulum kaydı; içeriği "Öneriler" bölümünde; onaylananlar v1 el kitabına |
| `kayit/kurulum/plu-eksikleri.md` | 48 | E-01…E-41 | — | taşınmaz | — | Kurulum/PLU kaydı; dersleri "Dersler" bölümünde v1 kural ve testlerine |
| `kayit/kurulum/izin-onerileri.md` | 18 | `.claude` deny ek önerileri | — | taşınmaz | — | Önerileri v1 izin şablonuna (agent) işlenir |
| `kayit/kurulum/kurulum-notlari.md` | 106 | Makine, kurulanlar, FreeCAD/OrcaSlicer, Tailscale, panel servisi komutları | — | taşınmaz | — | Makineye ve kişiye özgü (dizüstü modeli, kullanıcı adı); v1 kurulum belgesi genel yazılır |
| `kayit/kurulum/son-rapor.md` | 36 | İş paketi 2 ve kart standardı son raporu | — | taşınmaz | — | Kurulum kaydı |
| `kayit/kurulum/kararlar.yaml` | 283 | Kurulum kararları K-01…K-28 | — | taşınmaz | — | Kurulum kaydı. v1 tasarımında yeniden kayda alınacak kararlar: K-02 (YAML no → bool), K-10 (commit-tree birleşim), K-12 (günlük ayrı commit), K-17 (union birleştirme), K-18 (baskı koşulu), K-19 (aktif tanımı), K-21 (port, Host/Origin) |
| `kayit/kurulum/hiz-olcumleri.txt` | 15 | Panel hız ölçümleri (metin 0,04–0,94 s, 3B 1,0–1,7 s) | — | taşınmaz | — | Ölçüm kaydı; v1 panel performans testine referans |
| `kayit/kurulum/gunluk/2026-10-26.md` | 208 | Kurulum günlüğü | — | taşınmaz | — | Kurulum kaydı |
| `kayit/kurulum/kalite/K1.md` | 27 | K1 kalite incelemesi (5 YÜKSEK; hepsi teste dönüştü) | — | taşınmaz | — | Bulgular test_cekirdek ve S-001'de |
| `kayit/kurulum/kalite/K2.md` | 24 | K2 incelemesi (4 YÜKSEK: kimlik, içeriğe bağlı onay, yarım geçiş, rol) | — | taşınmaz | — | Bulgular test_akis'te |
| `kayit/kurulum/kalite/K3.md` | 24 | K3 incelemesi (temiz klasör, dal doğrulama, Host/Origin) | — | taşınmaz | — | Bulgular test_akis ve e2e 8'de |
| `kayit/kurulum/kalite/K4.md` | 19 | K4 geçiş incelemesi | — | taşınmaz | — | Üstteknik geçişine ait |
| `kayit/kurulum/kalite/KS.md` | 19 | Kart standardı incelemesi (1 YÜKSEK: birleşmiş dalda geri alma) | — | taşınmaz | — | Bulgu test_akis'te |
| `kayit/kurulum/kalite/P2.md` | 24 | İş paketi 2 incelemesi (6 YÜKSEK) | — | taşınmaz | — | Bulgular test_akis ve e2e 11'de; bulgu 12 (Ö-08 kodda yok) açık |
| `kayit/kurulum/kart-goruntuleri/*.png` (12 dosya) | — | UST-KLB-01 ve BAG-PLU-01 kart ekran görüntüleri | — | taşınmaz | — | Kurum ve çalışma verisi |
| `kayit/kurulum/gorseller/.gitkeep` | 0 | Boş klasör işareti | — | taşınmaz | — | İçerik yok |

## 11. Dersler E-01…E-41 (`kayit/kurulum/plu-eksikleri.md`)

Durum, belgedeki "Düzeltildi / Kısmen" işaretinden ve koddan alındı.

| No | Ders (tek satır) | Durum | Eski koddaki karşılığı | v1'de korunacak kural ya da test |
| --- | --- | --- | --- | --- |
| E-01 | Profilde yazıcının kendi ölçüleri (tabla x/y/z, nozul) yok; sığma denetimi profilden yapılmalı | açık (kısmen: tabla ölçüsü `params.yaml`'dan) | `kart_gorsel.tabla_olcusu` | Makine şemasında `printer.bed{x,y,z}`, `nozzle` (kaynaklı); pkg_fdm sığma kontrolü + test |
| E-02 | Kontroller yalnız geçme/ölçü/girişim üstüne; alan analizleri (kütle, AM, Re, kararlılık) yok | kısmen (altyapı kuruldu; aero hesaplar çalışma verisinde) | `hesap.py`, `hesaplar.ts` | core.evidence hesap API'si; pkg_aero hazır analizler; test: hesaplar kayda geçer |
| E-03 | Deney (atış) kaydı için biçim yok | açık | yok (panelde yalnız `deney/` indirme) | core.evidence deney şeması (yöntem, ölçümler, ortam, ortalama ± sapma) + test |
| E-04 | Basılabilirlik (destek gerektiren çıkıntı, en ince duvar) kontrolü yok | açık | yok | pkg_fdm üretilebilirlik kontrolü; sınırlar profilde; regresyon vakası |
| E-05 | Tek parça (montajsız) şartı denetlenmiyor | kısmen (ayrık katı reddi, E-28) | `akis.baski` | İstek listesine bağlı "parça sayısı = 1" kontrolü + test |
| E-06 | Boş panelde "Son okumandan beri · undefined" | düzeltildi | `main.ts` | e2e: boş çalışma listesinde "undefined" yok |
| E-07 | G0 kartında dört soru ve cevaplar ayrı görünmüyordu | düzeltildi | `akis._g0_sinifi`, `kapi_metni`; `kartlar.ts` | core.intake G0 soru ağacı; test: G0 kartında dört soru ve sınıf önerisi |
| E-08 | Görüntüleyici CSS'i sayfa kaymasını ve metin seçimini kapatıyordu | düzeltildi | `stil.css` | e2e: `body` kayar ve metin seçilir |
| E-09 | Sütunlar genişletilemiyordu | düzeltildi | `genislet.ts` | e2e: sürüklenir, genişlik hatırlanır |
| E-10 | Model yokken kapı kartı görseli dev boyutta | düzeltildi | `stil.css`, `kartlar.ts` | Kart görseli en büyük yükseklik kuralı (CSS) + görsel test |
| E-11 | Yorum ekibe ulaşmıyor, kartta yanıt yeri yok | düzeltildi | `akis.yanitla`, `bekleyen_yorumlar`; `kartlar.yorum_dizileri`; `cli bekleyenler --kanca`; `durum.kancalari_yaz` | Kural: yanıtlanmamış yorum kartı açık tutar; test_yorum_yanit_bekler_yanitlaninca_kapanir |
| E-12 | Sol alttaki profil satırı her çalışmada aynı | düzeltildi | `ortak.ts` | e2e: seçili çalışmanın profili görünür |
| E-13 | Yalnız hesapta kullanılan ölçü kart açtıramıyordu | düzeltildi | `kart_gorsel.hesap_girdisi_svg`, `hesap.kullanan_hesaplar` | Test: modelde izi olmayan ama hesapta kullanılan ölçünün kartı hesap listesini gösterir |
| E-14 | Onaydan sonra ekip kendiliğinden uyanmıyor | kısmen (gözcü + Durum ekranı; oturum kapalıyken çözüm yok) | `gozcu.py`, `nabiz.py`, `veriler.durum_ekrani`, `top_kimde` | agent: BM olayı ajanı uyandırır; gözcü birim testi; kapalı oturumu başlatma kararı açık |
| E-15 | Karar seçeneklerinin model tanımı yalnız kartta, kayıtta değil | düzeltildi | `akis.karar_ac` | test_karar_secenek_tanimi_kayitta_durur |
| E-16 | G1'de taslak ölçüler V-01'i şişiriyor; ölçülere erken onay | açık (öneri) | `kartlar.uret` (V-01) | G1'de "kavram taslağı" tek satır, onay G2'de (el kitabı onayıyla) |
| E-17 | Seçilen seçeneğin ölçüleri öbür seçeneklerin hesabına sızdı | düzeltildi | `akis.karar_ac`, `kart_gorsel.secenek_degerleri` | test_secilen_secenegin_olcusu_obur_secenege_sizmaz |
| E-18 | Panel ekibin çalışıp çalışmadığını gösteremiyordu | düzeltildi | `nabiz.py`, `maskot.ts`, `ekip.ts` | e2e 7, 15; nabız birim testi eklenmeli |
| E-19 | Model ve hesap kodunun `__pycache__`'i tasarım reposuna girdi | düzeltildi | `modelci.modul_yukle` (`dont_write_bytecode`), `isler` (`.gitignore`) | Test: model ve hesap yüklemesi bayt kodu yazmaz (yok, eklenmeli) |
| E-20 | Panelin `git status`'u index kilidi alıp ekibin commit'iyle çakışıyor | düzeltildi | `veriler` (`--no-optional-locks`) | Kural: panel okumaları kilitsiz; test yok, eklenmeli |
| E-21 | Kapanmış kararın karşılaştırması bugünkü ölçülerle yeniden hesaplanıyordu | kısmen (params onay sürümünde donar; model kodu o sürümden alınmıyor) | `kart_gorsel.secenek_degerleri`, `_commit_modeli` | test_kapanmis_kararin_karsilastirmasi_donar; v1'de model kodu da onay commit'inden |
| E-22 | Tabla yerleşimi döndürmüyor, yalnız kare tabla okuyordu | düzeltildi | `kart_gorsel.yerlesim_bul`, `tabla_olcusu` | test_tabla_yerlesimi_dondurerek_sigdirir |
| E-23 | İnce parçada filament ve süre tahmini yarı yarıya düşük | kısmen (kabuk + dolgu; değerler kodda) | `kart_gorsel.baski_tahmini` (`KABUK_MM`, `DOLGU`) | Değerler profile; tahmin testi yok, eklenmeli |
| E-24 | Onaylanacak B kartı kendi "açık Hold" ENGEL'ine takılıyordu | düzeltildi | `akis._baski_hazir_mi` | test_kesinlestirmede_baski_kendi_hold_kartina_takilmaz |
| E-25 | Tablaya oturmayan köşeli dosya onaylandı (tabla teması) | düzeltildi | `akis.tabla_temasi_kusuru` | test_tabla_temasi_kusuru; kural kimliği verilmeli |
| E-26 | G3 → G2 dönüş yolu yok | açık (Ö-17) | yok | core.flow `gate back` (gerekçeli, BM onaylı) + test |
| E-27 | İç köşe yarıçapı kuralı yok (burun birleşme yerinden kırıldı) | açık (Ö-16) | yok | KOSE-01 BM onayından sonra; pkg_fdm |
| E-28 | Tek parçada birden çok ayrık katı yakalanmıyordu | düzeltildi | `akis.baski` | Test yok, eklenmeli; kural kimliği verilmeli |
| E-29 | Yuvarlatılmış köşeli katı "su geçirmez değil" çıkıyordu | düzeltildi | `disari.temiz_ag`, `girisim.ag` | test_yuvarlatilmis_kose_agi_kapali |
| E-30 | Ekibin elle hesabında formül hatası; baskı bu hatayla yapıldı | düzeltildi (çalışma hesabında); Ö-18 açık | Sistemde karşılığı yok (çalışma verisi); HESAP-01 dolaylı | Ö-18: elle hesap bağımsız yöntemle sınanmadan baskı istenmez (kural + kapı maddesi) |
| E-31 | G2 kapısı risk kaydı ya da DFMEA sormuyor | açık | `akis.kapi_listesi` (madde yok) | G2 kapı maddesi "risk kaydı / DFMEA var" (A, B) + test |
| E-32 | Elle hesaplar VLM ile çelişiyor; denge ve hız için tek kaynak yok | kısmen (HESAP-01 "yerini aldı") | `kontroller/hesap_tutarliligi`, `Hesap.buyukluk` | Doğruluk düzeyi yüksek olan esas; düşük doğruluklu değeri okuyan hesap UYARI |
| E-33 | Kavramda tek başına C_D0 varsayımı seçim dayanağı oldu | açık | yok | pkg_aero: kavram seçiminde profil verisi (NeuralFoil ya da deney) zorunlu |
| E-34 | Hold işleri (repo açma) için onaylı yürütme yolu yok | açık | `.claude/settings.json` | agent: Hold komutu BM'ye hazır komut olarak sunulur; izin şablonu |
| E-35 | Denge ağırlık merkezine çok hassas; atış öncesi ölçülmeli | açık | yok | pkg_aero deney yöntemi: atış öncesi AM ±1 mm kabul ölçümü |
| E-36 | Yapısal analizde doğrulama yoktu; kırılmayı ancak FEA açıkladı | kısmen (`fea.py`; Ö-19 `BAGLANTI`) | `fea.py`, `hesap.py` | Ö-19 analiz planı; FEA birim testi |
| E-37 | Hesaplar her adımda baştan çalışıyor, birbirinin sonucunu okuyamıyordu | düzeltildi | `hesap.calistir` (girdi özeti önbelleği), `Hesap.diger` | test_analiz_baglantisiz_olmaz_ve_onbellek |
| E-38 | Kalite mühendisi PLU'da hiç çalışmamıştı | düzeltildi | `kalite.py`, `akis.asama_bitir`, `akis.baski` | test_kalite_yuksek_bulgu_kapanmadan_baski_istenmez |
| E-39 | NeuralFoil eğitim alanı dışında; tahmin güvenilmez | kısmen ("güvenilmez" sonuç durumu, HESAP-02) | `Hesap.sonuc(durum)`, `hesap_tutarliligi` | Sonuç güveni kayıtta; "güvenilmez" UYARI (S-001 9) |
| E-40 | `surec kontrol` (okuma komutu) kart dosyalarını yeniden yazıyor | açık | `cli kontrol`, `kartlar` | Test: okuma komutundan sonra çalışma ağacı temiz. Not: bugünkü `kontrol` yolu kartları `kartlar.uret` ile yalnız bellekte üretiyor; yazmanın kaynağı doğrulanmadı |
| E-41 | Baskı kartında dilimleyici ayarı zorunlu değil; hesap varsayımıyla çelişti | açık | `akis.baski` | pkg_fdm baskı isteğinde zorunlu ayar (dolgu, katman, kabuk, destek, tutunma) = hesap varsayımı; atış öncesi kabul ölçümü (kütle ±%5, AM) |

Sayım: düzeltildi 21 · kısmen 8 · açık 12.

## 12. Öneriler Ö-01…Ö-28 (`kayit/kurulum/el-kitabi-onerileri.md`)

Belgenin başında "Uygulanmadı; baş mühendis onayı bekliyor (el kitabı §3)" yazıyor ve el kitabı hâlâ 0.2. Bu yüzden **hiçbir önerinin el kitabı metni onaylanmış değil**; "onay durumu" sütunu metinde ya da kayıtta geçen BM kararını gösterir.

| No | Bölüm | Öneri (tek satır) | Onay durumu | Kodda | v1 notu |
| --- | --- | --- | --- | --- | --- |
| Ö-01 | §7 | Kalibre profilde standart görevle sınır içindeki geçme kart açmaz | BM kararı 2026-10-26 (cevap 6); el kitabı metni bekliyor | evet (`kartlar.uret`: `gecici_profil`) | core.cards; testle |
| Ö-02 | §10 | "Bağımsız sayı" satırı: Keşif/Geliştirme UYARI, Serbest bırakma ENGEL | Dayanak K-06 (proje mühendisi, inceleme bekliyor) | evet (`kalan_seviye`) | Katalog GECME-01 seviyesi |
| Ö-03 | §10 | Onay durumuna kapanmamış ve reddedilmiş-düzeltilmemiş kart eklensin | bekliyor | evet (`onay_durumu`) | — |
| Ö-04 | §9 | Esneme gibi param olmayan sayılar da kaynak etiketi taşır | bekliyor (K1 kalite bulgusu) | evet (`kaynaksiz` esneme; test_kaynaksiz_esneme_engel) | — |
| Ö-05 | §8, §10 | Baskı etiketi (izlenebilirlik) ile "basmaya hazır" sürüm etiketi (G5) ayrı | K-18 BM onayı (şartlı, 2026-10-26 12:55) | evet (`baski`: G5 şartı aranmaz) | core.flow + pkg_fdm |
| Ö-06 | §9 | Boyutsuz `oran` birimi; işleme ayarları için `ayar` kaynağı | bekliyor | kısmen (`oran` `BIRIMLER`'de; `ayar` kaynağı yok) | stdlib etiketleri |
| Ö-07 | §7 | BM onayı yalnız ajanın kaydedilmemiş değişikliği yokken ve görülen sürüm son sürümken | bekliyor (K3 bulgusu 1, 9) | evet (`_yazmaya_hazir`; testli) | core.flow |
| Ö-08 | §6, §8, §10 | Prototip baskısı (G3 içinde, onaylı B kartıyla) ile üretim serbest bırakması (G5) ayrı | BM kararı (K-18 şartı); el kitabı metni bekliyor | kısmen (ENGEL yok + B kartı var; "G3 içinde" sınırı yok, P2 bulgu 12) | core.flow: aşama sınırı + test |
| Ö-09 | §7 | Kart işi izlemeyen mühendise yazılır: "bu nedir" kutusu, öneri, onaylarsan/reddedersen/kayda geçer | BM isteği (kart standardı 2026-10-26); metin bekliyor | evet (`kartlar.metinler`, `eksikler`) | core.cards |
| Ö-10 | §7 | Görselsiz kart açılamaz; görsel modelden ve türe göre | BM isteği (kart standardı); metin bekliyor | evet (`kart_gorsel`, adım ENGEL) | core.cards; kural kimliği |
| Ö-11 | §7 | Kritik olmayan varsayımlar tek V-01 listesinde, toplu onay | BM isteği 2026-10-26; metin bekliyor | evet (`kartlar`: `V_NO`) | core.cards |
| Ö-12 | §9 | Yeni etiket `uretici:<belge>`; kart açmaz | BM isteği 2026-10-26; metin bekliyor | evet (`KAYNAK_DESENI`) | stdlib |
| Ö-13 | §7, §8 | Kararın bütün seçenekleri tek kartta | BM isteği 2026-10-26; metin bekliyor | evet (`karar_ac`) | core.decisions |
| Ö-14 | §7, §12 | Karar ve Hold kartında teyit penceresi; sunucu da teyitsizi reddeder | bekliyor (olay: K-01-c yanlış tıklama) | evet (`kartlar.ts`, `_teyit_gerekir`; e2e 1, 12) | panel |
| Ö-15 | §7 | BM kendi onay/retini geri alır (`geri_al` kaydı); kapı ve baskı geri alınmaz | bekliyor (aynı olay) | evet (`akis.onay_geri_al`; testli) | core.flow |
| Ö-16 | §9 | Yeni kural KOSE-01: iç köşe dolgu yarıçapı ≥ ince duvar kalınlığı (UYARI) | BM isteği ("geçiş noktalarına radyus atılsın"); katalog değişikliği onay bekliyor | hayır | stdlib + pkg_fdm, onaydan sonra |
| Ö-17 | §8 | `geri-don <kod> G2`: gerekçeli, BM onaylı G3 → G2 dönüşü | bekliyor | hayır | core.flow `gate back` |
| Ö-18 | §9, §10 | Elle her hesap ikinci bağımsız yöntemle sınanır; sınanmamış hesaba dayanan baskı istenmez | bekliyor | kısmen (HESAP-01 yalnız iki hesap varsa çelişkiyi yakalar; zorunluluk ve kapı maddesi yok) | core.evidence + core.flow |
| Ö-19 | §8, §9 | İlk prototip öncesi analiz planı (`analizler.yaml`, bağlantı zorunlu, ucuz yöntemle başla, G2 maddesi) | BM isteği 2026-10-27; metin bekliyor | kısmen (`TUR="analiz"`, `BAGLANTI` zorunlu, önbellek; `analizler.yaml` ve G2 maddesi yok) | core.evidence + core.flow |
| Ö-20 | §10 | Kalite mühendisi her kapı ve baskı isteğinde temiz bağlamla; açık YÜKSEK varken istek açılmaz | bekliyor (B1) | evet (`kalite.py`) | core.quality |
| Ö-21 | §8 | Kapı kartında istek başına durum ve kanıt yeri; G4/G5'te zorunlu istekler "karşılandı" | bekliyor (B2) | kısmen (kart alanı `istek_durumu` var; G4/G5 şartı kapı listesinde yok) | core.flow + test |
| Ö-22 | §10, HESAP-01 | Aynı büyüklük iki hesapta > %10 farklı → UYARI; doğruluk düzeyi (1 elle, 2 sayısal, 3 ölçüm) | bekliyor (B3) | evet (katalogda yok) | stdlib + core.checks |
| Ö-23 | §10, HESAP-02 | Kötü/güvenilmez sonuç kartta listelenir, UYARI; BM gerekçesiz onaylayamaz | bekliyor (B4) | evet (gerekçe şartının testi yok) | core.checks + core.flow |
| Ö-24 | §7, KARAR-01 | Karar dayandığı hesapları özetiyle kaydeder; değişince "dayanağı değişti" kartı | bekliyor (B5) | evet | core.decisions |
| Ö-25 | §7 | Ölçülmemiş gözlem tek başına tasarım değişikliği gerekçesi olmaz; kartta uyarı | bekliyor (B6) | evet (`gozlemler`; test yok) | core.decisions + test |
| Ö-26 | §5, §8 | Deneyle doğrulanan zorunlu istek varsa sınıftan bağımsız G4 | bekliyor (B7) | evet (`g4_gerekli`; testli) | core.flow |
| Ö-27 | §7 | Karar kartında "isteklere etkisi" zorunlu satır | bekliyor (B8) | evet (`hedef_etkisi`, `kartlar.eksikler`; negatif test yok) | core.decisions + test |
| Ö-28 | §9 | Yeni etiket `literatur:<atıf>`; okunmamış kaynak sayı vermez | bekliyor (A4, literatür karşılaştırması) | hayır | stdlib etiketi, onaydan sonra |

Sayım: kodda evet 20 · kısmen 5 (Ö-06, Ö-08, Ö-18, Ö-19, Ö-21) · hayır 3 (Ö-16, Ö-17, Ö-28). Kodda olup testi olmayanlar: Ö-23 (gerekçe şartı), Ö-25, Ö-27 (negatif durum).

## 13. Bağımsız inceleme B1–B8

Kaynak: `456fdd6` ("Bağımsız inceleme B1–B8: kalite mühendisi, istek–kanıt, tutarlılık, kötü sonuç, dayanak, G4"; 17 dosya, +585/−12), `cfb1698` ("İnceleme bulguları B6, B8 (kısmen B5) ve A2 altyapısı") ve `d26af89` ("Tutarlılık ve dayanak kartlarının onayı (B3, B5)"). Bulguların özgün metni repoda yok (inceleme ayrı bir inceleme reposunda yapılmış, E-34); tanımlar commit mesajlarından ve Ö-20…Ö-27 gerekçe sütunundan çıkarıldı. Eşleme bire birdir: B1–B8 = Ö-20–Ö-27. Ö-28 B'ye değil A4'e (literatür) bağlıdır; A2 analiz altyapısıdır (`cfb1698`).

| B | Bulgu | Ö | Kod (commit) | Test | v1 |
| --- | --- | --- | --- | --- | --- |
| B1 | Kalite mühendisi BAG-PLU-01'de hiç çalışmamıştı; her kapı ve baskı isteğinde temiz bağlamlı inceleme olmalı | Ö-20 | `kalite.py` (yeni, 154 satır), `akis.asama_bitir`/`baski`, `cli kalite`/`kalite-kapat` (456fdd6) | test_kalite_yuksek_bulgu_kapanmadan_baski_istenmez | core.quality (taşınır); ajan şablonu güncellenir |
| B2 | İstekten kanıta bağ yok: kapı kartında istek başına durum (karşılandı / karşılanmadı / kanıt bekliyor) ve kanıt yeri | Ö-21 | `akis.istek_durumu`, kapı kartı alanı; `asamalar.ts`, `dallar.ts`, `goruntuleyici.ts` (456fdd6) | yok | core.flow; G4/G5 "karşılandı" şartı ve test eklenir |
| B3 | Hesaplar arası tutarlılık: aynı büyüklük iki hesapta > %10 farklı | Ö-22 | `hesap.tutarsizliklar`, `hesap_tutarliligi` HESAP-01, `kartlar` tutarlılık kartı (456fdd6); onay özetinin büyüklükleri kapsaması (d26af89) | test_tutarlilik_ve_dayanak_karti_onaylaninca; S-001 9 | core.checks; HESAP-01 kataloğa |
| B4 | Kötü ya da güvenilmez sonuçlu hesap sessiz kalıyordu | Ö-23 | `hesap.kotu_sonuclar`, HESAP-02, kapı ve baskı kartında liste, `onay_ver` gerekçe şartı (456fdd6); "guvenilmez" durumu (cfb1698) | S-001 9 (hesap_sonucu); gerekçe şartının testi yok | core.checks + core.flow; HESAP-02 kataloğa; test eklenir |
| B5 | Kararın dayandığı hesap değişince karar yeniden incelenmiyordu | Ö-24 | `karar_ac(dayanak)`, `hesap.sonuc_ozeti` (cfb1698, kısmen); KARAR-01 (456fdd6); `dayanagi_yenile` (d26af89) | test_tutarlilik_ve_dayanak_karti_onaylaninca; S-001 10 | core.decisions; KARAR-01 kataloğa |
| B6 | Ölçülmemiş gözleme dayanan karar (K-04 bu durumdaydı) | Ö-25 | `karar_ac(gozlemler)`, kartta "Ölçümsüz gözleme dayanıyor" (cfb1698) | yok | core.decisions + test |
| B7 | Deneyle doğrulanan zorunlu istek varken G4 (geçerleme) sınıfa bağlıydı | Ö-26 | `akis.g4_gerekli`, `kapi_planini_guncelle` (456fdd6) | test_deneyle_dogrulanan_zorunlu_istek_g4_ekler | core.flow |
| B8 | Karar kartı kararın istek listesindeki hedeflere etkisini söylemiyordu | Ö-27 | `karar_ac(hedef_etkisi)` zorunlu, `kartlar.eksikler` (cfb1698) | yalnız fikstürde kullanılıyor; "eksikse açılmaz" testi yok | core.decisions + negatif test |

## 14. Taşınan ama testi olmayan parçalar (yeni test gerekir)

Bunlar "taşınır" kararlı olup bugün doğrudan testi olmayan parçalardır.

1. `fea.py`: hiç test yok. Bilinen çözümlü (ör. ankastre kiriş) bir FEA testi.
2. `gozcu.py`: test yok. BM kimlikli commit → bir satır; "Günlük:" commit'i atlanır; arşiv repoları izlenmez.
3. `nabiz.py`: yalnız e2e'de dolaylı. Canlılık eşikleri (çalışıyor / ses yok / durdu) için birim testi.
4. `gunluk.py`: "yalnız eklenir" ve sistem saati kuralı doğrudan sınanmıyor.
5. `modelci.py`: bayt kodu yazmama (E-19) testi yok.
6. `kart_gorsel.py` ölçü bulma ve görünüş (`param_etkisi`, `gorunus`): doğrudan birim testi yok (çap, düzlem ve parça kayması durumları).
7. `kart_gorsel.py` geçme kesiti ve izometrik: yalnız e2e 9'da dolaylı.
8. `kart_gorsel.baski_tahmini` (E-23): test yok (yerleşimin testi var).
9. Kimliksiz kural "ayrık katı reddi" (E-28): test yok.
10. HESAP-02'nin "onay gerekçe ister" yarısı (Ö-23): test yok (sonuç UYARI'sı S-001'de sınanıyor).
11. Katalog–kod bağı: her `Sonuc.kural` katalogda, her katalog `kontrol`'ü kodda. Test yok; bugün HESAP-01, HESAP-02, KARAR-01 yüzünden kalır.
12. CLI alt komutları (`regress`, `check`, `work archive/close/attach`, `step`, `gate request`, `reply`, `pending --hook`, `decision open`, `agent status`, `watch`, `review`, `review close`, `pulse`, `panel serve`): CLI düzeyinde test yok (yalnız `onay` ve `durum-yaz` sınanıyor). En azından çıkış kodu ve çıktı biçimi duman testi; `check` için ağacı kirletmeme testi (E-40); `pending --hook` için kanca JSON biçimi.
13. Panel ön yüzü: `genislet.ts` (E-09), `stil.css` (E-08 kayma ve seçim, E-10 görsel boyu), `yardim.ts` (HTML kaçışı, sayı ve saat biçimi): test yok.
14. Profiller: `fdm-cr10se-pla.yaml` hiçbir testte kullanılmıyor; config şemasına karşı doğrulama testi.
15. `ajanlar/tasarim-muhendisi.md`, `ajanlar/tekniker.md`: test yok. Ön madde (name, model, tools) ayrıştırma testi; kalite şablonu için çıktı biçiminin `kalite.SATIR` ile eşleşmesi.
16. `panel/sistem/surec-panel.service`: test yok (`systemd-analyze --user verify` ile denetlenebilir; kurulum Hold).
17. `.python-version`, `.gitignore`: test gerekmez (yapılandırma).

Yeniden yazılan parçalarda testi olmayan davranışlar (yeni kodla birlikte test yazılmalı): `veriler.py`'nin kilitsiz git okuması (E-20); tasarım dosyası ekranı (`dosya.ts`, `GET …/dosya`) ve `GET /api/kartlar`; ölçümsüz gözlem uyarısı (B6); `hedef_etkisi` eksikse kartın açılmaması (B8); istek–kanıt durumu (B2).
