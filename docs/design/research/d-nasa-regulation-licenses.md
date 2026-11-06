# Araştırma D: NASA-STD-7009B, mevzuat kaynakları, bağımlılık lisansları

- Tarih: 2026-11-06 06:20 (sistem saati, `date '+%F %H:%M'`)
- Hazırlayan rol: araştırma alt ajanı (karar vermez; öneri yazar). Kararlar proje mühendisine, onay Taha'ya aittir.
- Kapsam: (1) NASA-STD-7009B ve NASA-HDBK-7009B gereksinimlerinin tek kişilik tasarım aracına uyarlanması, (2) kaynak önceliği için AB/TR mevzuatı ve açık teknik kaynaklar, (3) AGPL-3.0 ile bağımlılık lisans uyumu.
- Doğrulama etiketleri: `metin_elde` = birincil metin indirildi ve okundu; `ikincil_kaynak` = site engelli, bilgi WebSearch özetinden; `dogrulanmadi` = bellekten ya da kaynağı bulunamadı.
- Erişim notu: eur-lex.europa.eu, curl ile her istekte `HTTP 202` + `x-amzn-waf-action: challenge` (bot koruması) döndü; WebFetch aracı ise alan adını çözemedi (oturumun izinli alanları dışında). www.gnu.org curl ile bağlantıyı kesti ya da `403` verdi; WebFetch yine alan adını çözemedi. Bu iki sitedeki bilgiler `ikincil_kaynak` olarak işaretlendi. GPL/AGPL/LGPL madde metinleri, FSF metninin birebir kopyasını taşıyan GitHub LICENSE dosyalarından okundu.
- Terimler: **M&S** = model ve simülasyon. **RWS** (real-world system) = modelin temsil ettiği gerçek sistem. **Referent** = model sonucunun karşılaştırıldığı veri, bilgi ya da daha yüksek doğruluklu model. **Placard** = sonuca iliştirilen görünür uyarı etiketi. **CM** = yapılandırma yönetimi (sürüm ve değişiklik denetimi).

---

## 1. NASA-STD-7009B

### 1.0 Belge künyesi

| Belge | Künye | Durum |
| --- | --- | --- |
| NASA-STD-7009B "Standard for Models and Simulations" | "Approved: 2024-03-05", "Superseding NASA-STD-7009A w/Change 1"; 88 sayfa; §1.2.4: "This Standard contains 43 requirements." standards.nasa.gov sayfasında "Is Active? ACTIVE". | metin_elde |
| NASA-HDBK-7009B "NASA Handbook for Models and Simulations: An Implementation Guide for NASA-STD-7009B" | Kapakta "Approved: 2026-02-03", "Superseding NASA-HDBK-7009A"; 175 sayfa; "APPROVED FOR PUBLIC RELEASE—DISTRIBUTION IS UNLIMITED". | metin_elde |
| NASA-STD-7009A (karşılaştırma için) | "Approved: 2016-07-13"; "contains 39 requirements". | metin_elde |

Tutarsızlık notu: HDBK-7009B'nin belge geçmişi tablosunda Revizyon B için tarih "2025-09-24" yazıyor, kapak ve imza tarihi "2026-02-03". Ayrıca sayfa başlıklarında hâlâ "DRAFT: NASA-HDBK-7009B" yazısı duruyor. Atıfta kapak tarihini (2026-02-03) kullanmayı öneririm; bu tutarsızlık bir kayıt notu olarak yazılmalı.

Terim notu: 7009B'nin bağlayıcı gereksinimleri "limits of operation" yerine **"M&S limits"** ([M&S 13]) ile **"domain of verification"** ([M&S 16]) ve **"domain of validation"** ([M&S 18]) terimlerini kullanır. "Limits of operation" yalnız öneri maddelerinde (4.1.3 b(10), 4.1.4 b(1)A) ve Ek F'de kalmıştır. Tanımlar (§3.2):
- M&S Limits: "the broadest bounds for potential M&S use that produce results" ve "M&S can be used to extrapolate outside the domains of verification and validation (V&V), but within the M&S limits."
- Domain of Verification: "the region enclosing all sets of M&S inputs for which the solution is determined to be correct".
- Domain of Validation: "the region enclosing all sets of M&S inputs for which the M&S' responses compare favorably with the referent."
- Permissible Use: "The purposes for which an M&S is formally allowed."

Bu üç bölge, aracın "geçerlilik alanı" denetimini doğrudan tanımlar (bkz. 1.K).

### 1.1 Madde tablosu

Uyarlama ilkesi (§1.3 ve §4 girişi): "Tailoring ... is acceptable when formally approved by the delegated NASA Technical Authority" ve "The responsible party is to provide a rationale why any requirement ... is not met." Araçta "delegated NASA Technical Authority" rolünün karşılığı Taha'dır (tek onay yetkilisi). Uygulanmayan her madde gerekçesiyle bir uyarlama kaydına yazılır ve Taha onaylar.

Ayrıca §4 girişi: "maintenance of the record implies that the outcome or product is re-established as a result of any changes to either the RWS or the M&S." Yani model ya da gerçek sistem değişince ilgili kayıtlar yeniden üretilmelidir. Araçta her kayıt bir commit'e bağlanır; araç sürümü ya da girdi değişince eski kayıt "bayat" işaretlenir.

#### A. Yaşam döngüsü ve programatik (geliştirme/kullanım ayrımı)

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| Ek F.1 | "two general parts: M&S development ... and M&S application, which includes use (or operation) and M&S archiving" | İki ayrı kayıt türü: **analiz aracı kaydı** (geliştirme ürünü, serbest bırakılır) ve **analiz koşusu kaydı** (kullanım ürünü). Koşu, aracın serbest bırakılmış bir sürümüne bağlanır. Ek F'ye göre her koşu yeniden "use assessment" ile başlar. |
| [M&S 40] (4.1.1.1) | "A record of the intended use of M&S shall be maintained." | Araç kaydında `amaclanan_kullanim` alanı zorunlu. Gerekçe metnine göre içerik: modellenen RWS yönleri, aracın ne yaptığı, hedeflenen geçerleme alanı, beklenen sonuç ve beslediği karar. |
| [M&S 6] (4.1.1.2) + Ek D | "A record of the assessed criticality associated with M&S use shall be maintained." | Koşu kaydında `kritiklik: {sonuc: I..V, etki: 1..5, renk: G/Y/R}`. Renk, Ek D Şekil 1 matrisinden okunur (ör. "5: Controlling" × "V: Catastrophic" = R). Ek D.1 a: kırmızı kutular "clear candidates for completely adhering to the requirements". Sonuç seviyelerinin sayısal eşiklerini (maliyet, takvim) standart vermez; D.2: "quantitative breakpoints should be established". Bu eşikler `karar` kaynaklı olur. |
| [M&S 41] (4.1.1.3) | "A plan for the acquisition, development, operation, maintenance, and retirement of the M&S ... shall be maintained." | Araç kaydında yaşam döngüsü durumu (`gelistirme / serbest / kullanimda / emekli`) ve sorumlu rol. |
| [M&S 42] (4.1.1.4) | "A record of the programmatic and technical metrics for the M&S shall be maintained." | Teknik metrikler otomatik toplanır: doğrulama ve geçerleme vaka sonuçları, belirsizlik ve duyarlılık çalışmaları (4.1.1.4'teki örnek listesi). |
| [M&S 43] (4.1.1.5) | "A record of acceptance criteria for the M&S shall be maintained, including: a. ... Verification ... e. M&S assessment level thresholds" | Araç kaydında `kabul_olcutleri`: doğrulama, geçerleme, belirsizlik, duyarlılık ölçütleri ve iki değerlendirmenin faktör eşikleri. 4.3.6: "This Standard levies no requirements with respect to what levels to achieve". Eşikler bu yüzden `karar` etiketiyle yazılır. |
| [M&S 44] (4.1.1.6) | "A record of information unique to the M&S necessary when ... reporting results" | Araca özgü rapor alanları (ör. ağ yoğunluğu, katman yüksekliği) araç kaydında tanımlanır; rapor şablonu bunları zorunlu sorar. |
| [M&S 9] (4.1.1.7) | "This Standard does not require technical reviews; if they occur, the results are to be recorded" | Kalite-mühendisi ya da Taha incelemesinin sonucu, bulgular ve gerekçeyle kayda yazılır. |
| [M&S 51] (4.1.1.8) | "A record of M&S defects or problems from discovery through closure shall be maintained." | Mevcut kart sistemi (G/E/S) kullanılır, gerekirse kusur türü eklenir. Açık kusur, raporda zorunlu uyarı olur ([M&S 32] h). |

#### B. Geliştirme

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 10] (4.2.1.1) | "A record of relevant characteristics, including data, of the RWS to be modeled, including its pedigree" | Gerçek sistemin özellikleri (malzeme, yazıcı, parça) kaynak etiketiyle (`olcu`, `standart`, ...) yazılır. Etiketsiz değer kabul edilmez. |
| [M&S 45] (4.2.1.2) | "The data sets and supporting software used in M&S development shall be maintained." | Geliştirmede kullanılan veri setleri repoda ya da özetiyle (hash) tutulur. Yazılım sürümleri `uv.lock` ve Node sürümüyle sabitlenir. |
| [M&S 46] (4.2.1.3) | "A record of the units and vector coordinate frames for all quantities and input/output variables" | Her girdi ve çıktı alanında `birim` ve `eksen_takimi` zorunlu. Birimsiz sayı kontrol betiğinde hata verir. |
| [M&S 11] (4.2.1.4) | "A record of the assumptions and abstractions ... including their rationales and consequences" | `varsayimlar[]`: metin + gerekçe + kullanım sonuçlarına etkisi. Mevcut `varsayim` etiketi ve kart açma kuralıyla uyumlu. |
| [M&S 12] (4.2.1.5) | "A record of the concepts, structures, and mathematics of the M&S" | Denklemler ve yöntem araç kaydında ya da belgesinde. Hazır yazılımlarda (COTS) 4.2.1.5 izin verir: "a reference to the user guides may suffice". |
| [M&S 13] (4.2.1.6) | "A record of the M&S limits (e.g., boundary conditions) shall be maintained." | `sinirlar`: aracın sonuç üretebildiği en geniş parametre aralığı. Dışında koşu başlatılmaz. |
| [M&S 14] (4.2.1.7) | "A record of the permissible uses of the M&S shall be maintained." | `izinli_kullanimlar`. Metne göre bunlar [M&S 40], [M&S 11], [M&S 13], [M&S 16] ve [M&S 18] kayıtlarından türetilir ve [M&S 23] değerlendirmesinin ölçütüdür. |
| [M&S 48] (4.2.1.8) | "A record of the assessed M&S capability shall be maintained according to each of the following factors" (veri soyağacı, doğrulama, geçerleme, geliştirme teknik incelemesi, süreç/ürün yönetimi) | Araç serbest bırakılırken beş faktörün her biri için 0–4 seviye ve kanıt bağlantısı (Tablo 6–11). |
| [M&S 47] (4.2.1.9) | "Guidance on how to use the M&S shall be maintained, including: ... b. Obsolescence criteria. c. Parameter calibrations. d. Computational requirements" | Araç kaydında `kullanim_kilavuzu`: kurulum, çalıştırma, başka araçla arayüz, sonuç analizi, eskime ölçütü, kalibrasyonlar, hesaplama gereksinimi (`surec doktor` denetimi ile bağlanabilir). |
| 4.2.2 c, d, e, f (öneri) | "messages detailing the failure mode and point of failure"; "assign unique version identifier, description, and the justification"; "test cases ... that span the M&S limits"; "feedback mechanism for users to report unusual results" | Hata mesajı standart biçimde; her araç sürümü commit kimliğiyle; regresyon vakaları sınırların uçlarını da kapsar; panelde "olağandışı sonuç" bildirimi kart açar. |

#### C. Doğrulama (verification: model, tasarımına uygun mu kurulmuş)

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 15] (4.2.3.1) | "The M&S shall be verified." | Her araç için betik halinde doğrulama vakaları (analitik çözüm, kıyas problemi). |
| [M&S 16] (4.2.3.2) | "A record of the domain of verification of the verified M&S shall be maintained." | `dogrulama_alani`: vakaların kapsadığı girdi bölgesi (parametre aralıkları). |
| 4.2.3 a, b | "Implementation (code) verification" ve "Solution verification ... takes place each time the M&S is used" | Kod doğrulaması araç sürümünde bir kez; çözüm doğrulaması (ağ yakınsaması, iterasyon yakınsaması) her koşuda. |
| 4.2.4 b, d (öneri) | "Record numerical error estimates (e.g., ... insufficient discretization, insufficient iterative convergence ...)"; "Record aspects of M&S not verified." | Koşu kaydında `sayisal_hata` alanı; araç kaydında "doğrulanmamış yönler" listesi. |
| Ek E.3.3 | "It is important to also consider changes to the development environment, which includes the compilers, libraries, operating system" | `surec regresyon` yalnız kontrol değişince değil, bağımlılık ya da kilit dosyası (`uv.lock`, `package.json`) değişince de çalışmalı. |
| Ek E.3.3 / HDBK 5.6.2.2 | "One common method is the echoing of all input data ... to a log file for comparison with the intended inputs." | Her koşu, aldığı girdileri kayda geri yazar (girdi yankısı); kontrol betiği bunu niyet edilen girdilerle karşılaştırır. |

#### D. Geçerleme (validation: model gerçeği yeterince temsil ediyor mu)

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 17] (4.2.5.1) | "The M&S shall be validated." | Referent ile karşılaştırma vakaları: ölçüm (kumpas, deney parçası), yayımlı deney verisi ya da daha yüksek doğruluklu model. |
| [M&S 18] (4.2.5.2) | "A record of the domain of validation of the validated M&S shall be maintained." | `gecerleme_alani`. Ek E.3.4'e göre "Each model output may have a unique domain of validation". Alan bu yüzden çıktı niceliği başına tutulur. |
| 4.2.5 | "the source(s) of empirical data ... are to be assessed with the same level of rigor as the validation of the respective M&S" | Geçerleme verisinin kendisi de soyağacı kaydı taşır (kim ölçtü, hangi aletle, belirsizlik). |
| Ek E.3.4 | "requires, at a minimum, some overlap between the uncertainty intervals around the means" | Geçerleme ölçütünün asgarisi: model ve referent belirsizlik aralıkları örtüşmeli. Daha sıkı ölçüt [M&S 43] b'de `karar` olarak yazılır. |
| Ek E.3.4 | "an assessment of any level above "1" is not permitted unless the conditions for "1" are satisfied" | Kavramsal geçerleme (model doğru problemi mi çözüyor) yapılmadan geçerleme faktörü 1'in üstüne çıkamaz. Bu kural kontrol betiğine yazılır. |
| 4.2.6 b, d (öneri) | "Record the validation metrics, referents, and data sets"; "Record the aspects of the M&S not validated." | Araç kaydında referent listesi ve "geçerlenmemiş çıktılar" listesi. |

#### E. Belirsizlik: geliştirme

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 19] (4.2.7.1) | "A record of the processes and rationale for characterizing uncertainty in the referent data" | Ölçüm referentlerinde belirsizlik GUM (JCGM 100) ile değerlendirilir; yöntem kayda yazılır. |
| [M&S 21] (4.2.7.2) | "A record of the qualitatively described or quantitative uncertainties incorporated into the M&S" | Araç içine gömülü belirsizlikler (malzeme saçılımı, kalibrasyon) listelenir. |
| 4.2.8 (öneri) | "record significant physical processes, effects, scenarios, or environments not considered" | "Dikkate alınmayanlar" listesi; raporda görünür. |

#### F. Kullanım

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 22] (4.3.1.1) | "A record of the proposed use(s) of the M&S shall be maintained." | Koşu kaydında `onerilen_kullanim`. |
| [M&S 23] (4.3.1.2) | "The result of the use assessment is that either the M&S is or is not accepted for the proposed use." | Koşu başlamadan önce öneri ile izinli kullanım karşılaştırılır (Tablo 14'teki dört boyut: kullanım türü, varsayım/kapsam, parametre sınırları, sonuç türü). Sonuç `kabul/ret`. Ret ise koşu yalnız placard ile yapılabilir. |
| [M&S 24] (4.3.1.3) | "A record of the Input(s) to the M&S, including their pedigrees" | Bkz. 1.G. |
| [M&S 25] (4.3.1.4) | "A record of the processes and rationales for setting up and utilizing the M&S" | Kurulum seçimleri ve gerekçesi (ağ boyu, sınır koşulu). Metin: "Setup and execution rationale includes any assumptions made when using the M&S." |
| [M&S 26] (4.3.1.5) | "a. Ensure M&S uses are conducted in accordance with the permissible uses and within the domains of V&V ... or b. Placard the M&S and analysis results with a warning" | Bkz. 1.K. |
| [M&S 27] (4.3.1.6) | "A record of the observed warning messages, error messages, and explanations" | Çözücü günlüğü ayrıştırılır; açıklanmamış uyarı varsa koşu "açıklama bekliyor" durumunda kalır. Gerekçe: "Unexplained warning or error messages are a cause for concern (increase risk)". |
| 4.3.2 b, c, f, h (öneri) | "Record the computational M&S used (including revision numbers)"; "parameter calibrations and the domain of calibration"; "Record the versions of M&S results"; "Record and explain all failure modes" | Koşu kaydı araç commit'ini, kalibrasyon alanını ve sonuç sürümünü taşır. |

#### G. Girdi soyağacı (input pedigree)

Tanım (§3.2): "A record of traceability from the input data's source through all aspects of its transmission, storage, and processing to its final form when using an M&S."

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 24] | (yukarıda) ve 4.3.1.3: "The span of inputs used for the M&S delineates the domain of M&S use, which must always be within the M&S limits" | Girdi kümesinin kapsadığı aralık otomatik hesaplanır ve [M&S 13] sınırlarıyla karşılaştırılır. |
| Ek E.4.3, Tablo 16 | Seviye 2: "Most input data are known and traceable to formal documentation. ... Uncertainties in all data are at least estimated." | Girdi soyağacı seviyesi, girdi kayıtlarından türetilir: belirsizliği olmayan girdi varsa seviye 2'ye çıkamaz. |
| HDBK 5.6.1.3.2 | Nitelik sınıfları: "Notional", "Informed", "Specified", "Derived", "Measured" | Mevcut kaynak etiketlerine eşleme önerisi: `varsayim` → Notional ya da Informed; `standart` ve `karar` → Specified; `turetilir` → Derived; `olcu:kumpas/mastar/tarama` → Measured. Eşleme `nitelik` adlı ikinci bir alanla tutulur. |
| HDBK 5.6.1.3.2 | "Whenever notional data are used, these data should be clearly noted." | `varsayim` değerleri raporda ayrı bir listede çıkar (zaten kart açılıyor). |
| HDBK 5.6.1.3.2 | "the input pedigree credibility level is limited to the credibility level of the model from which the data are obtained." | Bir aracın çıktısı başka aracın girdisi olursa, girdi soyağacı seviyesi kaynak koşunun güvenilirlik seviyesiyle sınırlanır (zincir kuralı). |

#### H. Sonuç belirsizliği

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 28] (4.3.3.1) | "A record of any processes and rationale for characterizing uncertainty in ... a. The input ... b. The results ... c. The quantities derived from M&S results." | Koşu kaydında belirsizlik yöntemi üç düzeyde: girdi, sonuç, türetilmiş nicelik. |
| [M&S 29] (4.3.3.2) | "including MUFs incorporated into the M&S as well as factors of safety (FS) that are intended to cover uncertainties" | Emniyet katsayısı kullanılıyorsa hangi belirsizliği karşıladığı yazılır. MUF (model belirsizlik katsayısı) aynı şekilde. |
| [M&S 33] (4.3.8.2) | "a. A quantitative estimate ... or b. A qualitative description ... or c. A clear statement that no quantitative estimate or qualitative description of uncertainty is available." | Her sonuçta `belirsizlik.tur: nicel / nitel / yok` zorunlu. "yok" ise rapor bunu açıkça yazar. Boş bırakmak hata olur. |
| [M&S 34] (4.3.8.3) | "A description of the processes used to obtain the estimate of uncertainty ... shall be included" | Raporda yöntem satırı (ör. "Monte Carlo", "aralık analizi", "uzman görüşü"). |
| Ek E.4.4, Tablo 17 | Seviye 1: "Sources of input uncertainty are identified with qualitative estimates"; seviye 3: "Quantitative estimates of uncertainties are reported for most output quantities after a propagation of all known sources" | Belirsizlik faktörü seviyesi, kayıtta yayılım (propagation) yapılıp yapılmadığından türetilir. |

#### I. Duyarlılık ve sağlamlık (robustness)

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 30] (4.3.5) | "A record of the extent and results of any sensitivity analyses performed with the M&S shall be maintained." | Duyarlılık çalışması kaydı: oynatılan parametreler, aralıkları, sonuç değişimi. |
| Tanım (§3.2) | "Key sensitivities are parameters and variables shown to produce large changes in results with relatively small perturbations to input." | Kayıtta "anahtar duyarlılık" işareti. Bunlar raporda öne çıkar. |
| Ek E.4.5 | "few" implies ... less than 20 percent ...; "many" ... between 20 and 50 percent ...; "most" ... (i.e., >50 percent)" | Sağlamlık faktörü önerisi otomatik: duyarlılığı bilinen parametre oranı hesaplanır. Bu oranlar standardın "guideline" (yönerge) değerleridir; kayıtta `standart:NASA-STD-7009B E.4.5` kaynağıyla yazılır. |
| HDBK 5.6.2.3 | "It is equally important, during sensitivity studies, to stay within the permissible uses of the model (unless such excursions are appropriately placarded)." | Duyarlılık taraması da [M&S 26] denetiminden geçer. |

#### J. Kullanım geçmişi

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| 4.3.2 g (öneri) | "Record the use history of M&S, in the same or similar applications" | Araç kaydı, kendisini kullanan koşuların listesini (kimlik + sonuç) tutar. Bu liste koşu kayıtlarından türetilir, elle yazılmaz. |
| Ek E.4.2, Tablo 15 | Seviye 4: "nearly identical to previous M&S uses"; seviye 1: "departs substantially from prior uses ..., or this is the first use of the M&S" | Yeni koşu, önceki koşulara benzerliğe göre sınıflanır. İlk kullanım en fazla seviye 1 olur. |

#### K. Geçerlilik alanı, sınırlar ve alan dışı kullanım

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 26] (4.3.1.5) | b şıkkı: "include the type of limit exceeded, the extent that the limit was exceeded, and an assessment of the consequences" | Placard üç alan taşır: aşılan sınırın türü, aşım miktarı, sonuca etkisi. |
| Tablo 15 (kullanım değerlendirmesi seviyeleri) | 4: "within the domain of M&S validation"; 3: "within the domain of M&S verification"; 2: "within the M&S limits" | **Üç bölgeli denetim önerisi:** girdi geçerleme alanında ise "geçerli"; yalnız doğrulama alanında ise "doğrulanmış, geçerlenmemiş" (placard); yalnız sınırlar içinde ise "dış değerleme" (placard + etki değerlendirmesi); sınır dışında ise koşu reddedilir ya da sonuç **"güvenilmez"** damgası alır ve karar girdisi olamaz. Dayanak: 4.3.1.3 "must always be within the M&S limits". |
| HDBK 5.5.3.2.2 | "If the use of a model predicts beyond the range of currently existing empirical data and is subsequently proven correct with new 'operational' data, then the domain of validation for that model can be justifiably updated." | Yeni ölçümle doğrulanan dış değerleme sonucu geçerleme alanını genişletebilir. Bu bir araç sürümü değişikliğidir ve Taha onayı ister. |
| 4.1.3 b(10) (öneri) | "Best practices for user interface design to constrain the operation of the M&S to within its limits of operations." | Panel ve CLI sınır dışı girdiyi baştan engeller ya da placard'ı zorunlu kılar. |

#### L. Sonuç raporlama

4.3.8 girişi raporun beş parçasını sayar: "(1) the best estimate of the results, (2) a statement on the uncertainty in the results, (3) objective, credibility supporting, assessments ..., (4) explicit caveats ..., and (5) the risks associated with accepting the results".

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 32] (4.3.8.1) | "explicit warnings shall be included for the following occurrences": a. kabul ölçütü sağlanmadı, b. varsayım ihlali, c. sınır ihlali, d. çalışma uyarıları/hataları, e. olumsuz kullanım değerlendirmesi, f. kurulum sorunları, g. feragatler (waiver), h. açık kusurlar | Rapor şablonunda sekiz uyarı satırı sabit (HDBK Tablo 8 biçiminde: var mı, nedir, devam gerekçesi). |
| [M&S 32] açıklama | "In the absence of substantiating evidence ... a warning is to be provided." | Kanıt kaydı yoksa uyarı **otomatik** yazılır. "Kanıt yok" sessizce "sorun yok" sayılmaz. |
| [M&S 50] (4.3.8.4) | "The outcome of the M&S capability assessment ... shall be included"; açıklama: "as well as the gaps between the assessed levels and the thresholds" | Raporda yetenek değerlendirmesi: seviye, eşik, fark. |
| [M&S 35] (4.3.8.5) | "The outcome of the M&S results assessment ... shall be included" | Sonuç değerlendirmesi: seviye, eşik, fark. Ek E.5 bar grafik ya da radar grafik önerir. |
| [M&S 36] (4.3.8.6) | "The findings from technical reviews ... shall be included" | İnceleme bulguları rapora bağlanır. |
| [M&S 37] (4.3.8.7) | "The qualifications of the developers of the M&S and the users, operators, or analysts ... shall be included" | Bkz. 1.O. |
| [M&S 38] (4.3.8.8) | "The records of M&S development and use as shown in Appendix A shall be included" | Rapor, Ek A matrisindeki her kaydın yerini (dosya yolu) listeler. HDBK Tablo 13 bunun kontrol listesidir. |
| [M&S 39] (4.3.8.9) | "The assessment of, and rationale for, acceptance of the risks ... shall be included" | Risk kabul gerekçesi; kabulü Taha verir. |
| 4.3.9 a, b, e (öneri) | "concluding remarks stating whether the M&S results are credible enough for the actual use"; "how to access more detailed backup material"; "Include dissenting technical opinions" | Raporun son satırı "bu kullanım için yeterince güvenilir mi: evet/hayır + gerekçe". Ajanlar arası görüş ayrılığı silinmez, rapora girer. |

#### M. Risk değerlendirmesi

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 49] (4.3.6.2) | "A record of the assessed risks associated with the use of the M&S-based analysis shall be maintained." Konular: a. kritiklik [M&S 6], b. teknik inceleme [M&S 9], c. kusurlar [M&S 51], d. uyarılar [M&S 32], e./f. belirsizlik [M&S 29]/[M&S 28], g. yetenek [M&S 48], h. sonuç [M&S 31], i. kişi yeterliliği, j. önceki sürümlerden farklar, k. önceki kullanımlardan farklar | Risk kaydı bu on bir başlıkla şablonlanır; çoğu başlık diğer kayıtlardan otomatik doldurulur. j ve k, git farkından türetilir. |
| HDBK 5.6.3.3 | "Not all caveats, uncertainties, ... necessarily introduce M&S risk. Each of them is to be evaluated (and reported)" | Her uyarının yanına "risk doğurur mu: evet/hayır + gerekçe". |

#### N. M&S yönetimi (süreç ve ürün yönetimi)

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| 4.1.2 b (öneri) | "work product management, process definition, process measurement, process control, process change, and continuous improvement, including configuration management (CM)" | Bu repodaki el kitabı, commit biçimi, kapılar ve panel onayları bu faktörün kanıtıdır. |
| 4.2.2 g, h (öneri) | "Maintain (conceptual, mathematical, and computational) models, simulations, and associated records in a controlled CM system." | Git ve `<kod>/ana` hattı. Ana hatta yalnız onaylı birleştirme. |
| Ek E.3.6 / E.4.7, Tablo 11 ve 20 | Seviye 2: "Roles and responsibilities are defined in the context of an M&S process that is formally documented and approved"; seviye 3: "Compliance with the process is formally documented. Measurements of process and product compliance are made" | Onaylı el kitabı ve roller seviye 2'nin; süreç uyum ölçümleri (kontrol betikleri, regresyon geçme oranı) seviye 3'ün kanıtı olur. |

#### O. Kişi yeterliliği

| Madde | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| [M&S 37] | (yukarıda) | Rapor, insan rolleri (Taha) ve ajan rolleri için yeterlilik satırı taşır. Ajanlar için yeterlilik yerine model kimliği, sürümü ve verilen görev sınırı yazılır (öneri; standart ajanları ele almaz). |
| 4.1.4 a, b (öneri) | "Determine the depth of required training or equivalent experience (i.e., qualifications) for developers, operators, and analysts." Konular arasında "The limits of operation for M&S", "How to recognize unrealistic results from simulations" | Rol şablonlarına (`ajanlar/`) sınırlar ve gerçekçi olmayan sonucu tanıma talimatı eklenir. |
| HDBK Tablo 12 | "Developers. Testers. Users (Operators). Analysts." | Rapordaki yeterlilik bölümü bu dört rolü ayrı satırda listeler. |

#### P. Güvenilirlik değerlendirmesi (credibility assessment) 7009B'de nasıl

- Ek E.2: "In this version, the factors of M&S development and the factors of M&S use are assessed separately." İki değerlendirme vardır: **yetenek değerlendirmesi** ([M&S 48], 5 faktör, geliştirme sonunda) ve **sonuç değerlendirmesi** ([M&S 31], 6 faktör: kullanım değerlendirmesi, girdi soyağacı, belirsizlik, sonuç sağlamlığı, kullanım/analiz teknik incelemesi, kullanım süreç/ürün yönetimi).
- Ek E.2: "The assessment of each factor level is a discrete step function, with no intentions for partial credit" ve "comparison between or combining of factor assessments and thresholds is not intended and should be avoided". Araç **tek bir güvenilirlik puanı üretmemeli**; faktörler ayrı ayrı gösterilir.
- Ek E.2: "Reporting factor level assessment is recommended using a 5-tier labeling system" (örnekte 0–4). Seviye tanımlarında birden çok koşul varsa hepsi sağlanmalıdır.
- Ek E.2 (hazır yazılım): "both the tool and the computational model constructed using the tool are to be considered". CalculiX, OCCT, gmsh gibi araçlarda iki katmanlı değerlendirme: aracın kendisi + onunla kurulan model.
- HDBK D.2: değerlendirme "The role of the person/team performing the credibility assessment" bilgisini içermeli. Bu kural, "işi yapan kendi işini onaylamaz" ilkesiyle örtüşür.
- Teknik inceleme faktörü (Tablo 10 ve 19): seviye 3 "Favorable independent peer review"; Ek E.3.5 peer review tanımı: "conducted by one or more persons of equal technical standing". **Yorum (karar gerektirir):** bir YZ ajanının incelemesi bu tanıma göre "peer review" sayılmaz. Tek kişilik ekipte bağımsız inceleme dışarıdan bir kişi gerektirir. YZ incelemesinin hangi seviyeye sayılacağı bir uyarlama kararıdır.

#### Q. YZ modelleri (HDBK-7009B §4.5.2–4.5.3, yeni)

| Kaynak | Kısa alıntı | Araca uygulanışı |
| --- | --- | --- |
| HDBK 4.5.2 notu | "the ML surrogates used for (M&S supported) critical decisions are subject to the same M&S credibility evaluation and risk evaluations as other non-AI M&S approaches." | neuralfoil gibi makine öğrenmesi vekil modelleri (surrogate), ayrı bir analiz aracı kaydı ve tam doğrulama/geçerleme ister. Eğitim verisi soyağacı veri soyağacı faktörüne girer. |
| HDBK 4.5.3 | "When the AI application in an M&S lifecycle is not associated with predicting the RWS response, the processes in the standard may have less applicability. Such cases may include ... generative AI (genAI) chatbots" | Claude ajanları sonucu "tahmin etmiyor", süreci yürütüyor. Standart bunlara doğrudan uygulanmaz; HDBK "appropriated AI discipline evaluation criteria should be applied" der. Ajan çıktısı model sonucu sayılmaz; sayılar her zaman betikten gelir (mevcut kuralla uyumlu). |
| HDBK 4.5.3 | "many commercial tools are trained on user inputs and are not suitable for use with any data that is not already publicly available" | Genel bir uyarı. Dışarıya veri gönderen her şey zaten dur noktası; gizli veriyle çalışmadan önce Taha'ya sorulur. |

### 1.2 NASA-STD-7009A'dan farklar (kısa)

| Konu | 7009A (2016-07-13) | 7009B (2024-03-05) | Doğrulama |
| --- | --- | --- | --- |
| Gereksinim sayısı | "contains 39 requirements" ([M&S 1]–[M&S 39]) | "contains 43 requirements". Ek A'daki numaralar: 6, 9–19, 21–51. 1–5, 7, 8 ve 20 numaraları B'de yok; 40–51 yeni. | metin_elde (numaralar Ek A listesinden `turetilir`) |
| Güvenilirlik değerlendirmesi | Tek değerlendirme, 8 faktör, 3 kategori: "Data Pedigree, Verification, Validation, Input Pedigree, Uncertainty Characterization, Results Robustness, M&S History, and M&S Process/Product Management" | İkiye bölündü: yetenek (5 faktör) + sonuç (6 faktör). Belge geçmişi: "splitting the M&S Results Credibility Assessment into M&S Capability and M&S Results Assessments." | metin_elde |
| Geçmiş faktörü | "M&S History" (değişiklik geçmişi + kullanım geçmişi alt faktörleri) | Faktör olarak kalktı. Kullanım geçmişi "M&S Use Assessment" seviyelerine girdi (Tablo 15). Sürüm ve kullanım farkları [M&S 49] j, k risk başlıkları oldu. | metin_elde |
| Teknik inceleme | Değerlendirme faktörü değil; yalnız raporlama ([M&S 36]) | İki faktör: "M&S Development Technical Review" ve "M&S Use/Analysis Technical Review" | metin_elde |
| Sınır kavramı | "Limits of Operation: ... beyond which the accuracy, precision, and uncertainty of the results are indeterminate." [M&S 26](1): "within the limits of operation" | "M&S limits" (en geniş sınır) ile doğrulama ve geçerleme alanları ayrıldı. [M&S 26] a: "within the domains of V&V" | metin_elde |
| Öneriden gereksinime | Birimler ve eksen takımları 4.2.2 b'de öneriydi ("Should document units and vector coordinate frames") | Yaşam döngüsü planı [M&S 41], veri ve yazılım [M&S 45], birim ve eksen [M&S 46], kullanım kılavuzu [M&S 47] gereksinim oldu | metin_elde |
| Yeni gereksinimler | yok | Kusur takibi [M&S 51]; ayrıntılı risk değerlendirmesi [M&S 49]; iki değerlendirmenin raporu [M&S 50], [M&S 35] | metin_elde |
| El kitabı | HDBK-7009A (2019-05-08) | HDBK-7009B: belge geçmişine göre YZ modellerine uygulama rehberi, kullanım beyanları (use statements) eki, yeni çalışma sayfası | metin_elde |

### 1.3 Araca uygulama özeti (öneri, karar değildir)

1. **Analiz aracı kaydı** (geliştirme ürünü) alanları: `amaclanan_kullanim` [40], `yasam_dongusu` [41], `kabul_olcutleri` + eşikler [43], `gercek_sistem` [10], `veri_ve_yazilim` [45], `birim/eksen` [46], `varsayimlar` [11], `matematik` [12], `sinirlar` [13], `dogrulama_alani` [16], `gecerleme_alani` (çıktı başına) [18], `izinli_kullanimlar` [14], `yetenek_degerlendirmesi` (5 faktör) [48], `kullanim_kilavuzu` [47], `kusurlar` [51], `kullanim_gecmisi` (türetilir).
2. **Analiz koşusu kaydı** (kullanım ürünü) alanları: `arac_surumu` (commit), `onerilen_kullanim` [22], `kullanim_degerlendirmesi` [23], `kritiklik` [6], `girdiler` (kaynak etiketi + nitelik + belirsizlik) [24], `kurulum_gerekcesi` [25], `alan_denetimi` + `placard` [26], `uyarilar` [27], `belirsizlik` (nicel/nitel/yok + yöntem) [28, 29, 33, 34], `duyarlilik` [30], `sonuc_degerlendirmesi` (6 faktör) [31], `risk` [49].
3. **Kontrol betikleri** (modelden bağımsız): birimsiz değer, kaynaksız değer, sınır dışı girdi, boş belirsizlik alanı, kanıtsız "uyarı yok" beyanı, kavramsal geçerleme olmadan geçerleme seviyesi > 1 olması.
4. **Rapor şablonu**: 4.3.8'in beş parçası + [M&S 32]'nin sekiz uyarısı + iki değerlendirmenin seviye/eşik/fark gösterimi + kişi yeterliliği + kayıt yerleri + "yeterince güvenilir mi" sonucu.
5. **Uyarlama kaydı**: uygulanmayan maddeler ve gerekçeleri. Taha onaylar. İlk aday: teknik inceleme faktörlerinde bağımsızlık şartı ve YZ incelemesinin sayılma biçimi.

---

## 2. Mevzuat ve açık teknik kaynaklar

Kaynak önceliği önerisi: (1) yürürlükteki resmî mevzuat metni (EUR-Lex, mevzuat.gov.tr, Resmî Gazete); (2) uyumlaştırılmış standart (ücretli; bu araştırmada yok); (3) açık teknik kılavuz (JCGM, NASA); (4) ikincil kaynak. Araçta her mevzuat kaydı `kaynak` (URL), `kunye` (CELEX ya da RG tarih/sayı), `okuma_tarihi` (sistem saati) ve `dogrulama` alanı taşımalı. Mevzuat değişkendir; okuma tarihi olmayan mevzuat atfı geçersiz sayılmalı.

### 2.1 AB

| Kaynak | Resmî URL | Ne olduğu | Künye | Doğrulama |
| --- | --- | --- | --- | --- |
| (EU) 2023/988 GPSR | https://eur-lex.europa.eu/eli/reg/2023/988/oj · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0988 | Genel ürün güvenliği tüzüğü; tüketici ürünlerinde temel güvenlik çerçevesi | CELEX 32023R0988; OJ L 135, 23.5.2023, s. 1–51; uygulama 13.12.2024; EUR-Lex'te konsolide sürüm 29/05/2026 ve 2025-01-21 tarihli düzeltme görünüyor | ikincil_kaynak |
| (EU) 2023/1230 Makine Tüzüğü | https://eur-lex.europa.eu/eli/reg/2023/1230/oj · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1230 | Makine ve ilgili ürünlerin sağlık ve güvenlik gereklilikleri; 2006/42/AT direktifinin yerine geçer | CELEX 32023R1230; kabul 14/6/2023 (TR Makine Emniyeti Yönetmeliği md. 50 metninden `metin_elde`); uygulama 20.1.2027 (2023-07-04 düzeltmesiyle; TR yönetmeliği md. 52 b de "20/1/2027" diyor, `metin_elde`); OJ sayı/sayfa: `dogrulanmadi` | ikincil_kaynak (tarihler TR metniyle çapraz doğrulandı) |
| (EC) 1907/2006 REACH | https://eur-lex.europa.eu/eli/reg/2006/1907/oj · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006R1907 | Kimyasalların kaydı, değerlendirilmesi, izni ve kısıtlanması | CELEX 32006R1907; OJ L 396, 30.12.2006, s. 1; en yeni görülen konsolide metin 02006R1907-20260622 | ikincil_kaynak |
| 2011/65/EU RoHS | https://eur-lex.europa.eu/eli/dir/2011/65/oj · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011L0065 | Elektrikli ve elektronik eşyada bazı tehlikeli maddelerin kısıtlanması | CELEX 32011L0065; OJ L 174, 1.7.2011, s. 88–110; tarih 8/6/2011 (TR RoHS yönetmeliği md. 20 metninden `metin_elde`); konsolide sürüm 01/01/2025 | ikincil_kaynak |

Not: GPSR'nin 2001/95/AT direktifini yürürlükten kaldırdığı bilgisi `dogrulanmadi` (EUR-Lex okunamadı). Bu bilgi TR tarafı için önemli (bkz. 2.2'deki GÜG notu).

### 2.2 Türkiye

| Kaynak | Resmî URL | Ne olduğu | Künye | Doğrulama |
| --- | --- | --- | --- | --- |
| 7223 sayılı Ürün Güvenliği ve Teknik Düzenlemeler Kanunu | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=7223&MevzuatTur=1&MevzuatTertip=5 · https://www.resmigazete.gov.tr/eskiler/2020/03/20200312-1.htm | Ürün güvenliği, teknik düzenleme, piyasa gözetimi ve denetimi (PGD) çerçeve kanunu; 4703 sayılı Kanunu kaldırdı (md. 25) | Kabul 5/3/2020; RG 12/03/2020, sayı 31066; md. 26: "yayımı tarihinden bir yıl sonra yürürlüğe girer"; değişiklik tablosu: 7418 sayılı Kanun md. 16'yı (yürürlük 1/4/2023), 7511 sayılı Kanun md. 20'yi (yürürlük 29/5/2024) değiştirdi; para cezaları 2026/13 sayılı Tebliğ ile 1/1/2026–31/12/2026 için güncellendi | metin_elde |
| 7223 md. 24 (uygulama mevzuatı) | (yukarıdaki metin) | (2) a: PGD, "CE" işareti, uygunluk değerlendirme kuruluşları ve onaylanmış kuruluşlar Cumhurbaşkanınca; b: uygunluk değerlendirme, e-ticarette PGD, genel ürün güvenliği vb. Bakanlıkça | — | metin_elde |
| Genel Ürün Güvenliği Yönetmeliği (Ticaret Bakanlığı) | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=38396&MevzuatTur=7&MevzuatTertip=5 | Tüketici ürünlerinin genel güvenliği | RG 11.03.2021, sayı 31420; yürürlük 12/3/2021 (md. 16); dayanak 7223 md. 24 (md. 3) | metin_elde |
| ↳ önemli not | — | md. 15: "Genel Ürün Güvenliğine İlişkin 2001/95/AT sayılı ... Direktifi dikkate alınarak" hazırlandı. mevzuat.gov.tr metninde değişiklik tablosu yok; başlık aramasında (EU) 2023/988'e uyumlu yeni bir GÜG yönetmeliği çıkmadı (okuma: 2026-11-06). TR GÜG, AB GPSR'nin gerisinde kalıyor olabilir. | — | metin_elde (arama sonucu); "geride kalma" yorumu dogrulanmadi |
| Ürünlerin Piyasa Gözetimi ve Denetimine Dair Çerçeve Yönetmelik | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=4269&MevzuatTur=21&MevzuatTertip=5 | PGD'nin genel usul ve esasları | Cumhurbaşkanı Kararı 9/7/2021, sayı 4269; RG 10/7/2021, sayı 31537; dayanak 7223 md. 24 | metin_elde |
| Uygunluk Değerlendirme Kuruluşları ve Onaylanmış Kuruluşlar Yönetmeliği | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=4022&MevzuatTur=21&MevzuatTertip=5 | Test, muayene, belgelendirme kuruluşlarının asgari nitelikleri | CK 26/5/2021, sayı 4022; RG 27/5/2021, sayı 31493; dayanak 7223 md. 24/2-a | metin_elde |
| Uzaktan İletişim Araçları Yoluyla Piyasaya Arz Edilen Ürünlerin PGD Yönetmeliği | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=42348&MevzuatTur=7&MevzuatTertip=5 | E-ticaretle satılan ürünlerde PGD | RG 30.10.2024, sayı 32707; dayanak 7223 md. 24 ve 4269 sayılı CK | metin_elde |
| Ticaret Bakanlığı PGD Yönetmeliği | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=39359&MevzuatTur=7&MevzuatTertip=5 | Ticaret Bakanlığı sorumluluğundaki tüketici ürünlerinde PGD | RG 09.02.2022, sayı 31745 | metin_elde (künye ve amaç maddesi) |
| Sanayi ve Teknoloji Bakanlığı PGD Yönetmeliği | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=38796&MevzuatTur=7&MevzuatTertip=5 | Sanayi ürünlerinde (makine dahil) PGD | RG 14.07.2021, sayı 31541 | metin_elde (künye) |
| Makine Emniyeti Yönetmeliği (2023/1230/AB) | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=46338&MevzuatTur=7&MevzuatTertip=5 | AB Makine Tüzüğü'nün TR uyumu (Sanayi ve Teknoloji Bakanlığı) | RG 16.10.2026, sayı 33402; dayanak 7223 md. 4/3; md. 52: bazı maddeler yayımda, "Diğer hükümleri 20/1/2027 tarihinde" yürürlüğe girer | metin_elde |
| EEE'de Bazı Zararlı Maddelerin Kullanımının Kısıtlanmasına İlişkin Yönetmelik (TR RoHS) | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=39913&MevzuatTur=7&MevzuatTertip=5 | 2011/65/AB'nin TR uyumu | RG 26/12/2022, sayı 32055; değişiklik RG 20/1/2024, sayı 32435 (tabloda ikinci satır okunamadı); dayanak 2872 sayılı Çevre Kanunu ve 7223 | metin_elde |
| KKDİK Yönetmeliği (Kimyasalların Kaydı, Değerlendirilmesi, İzni ve Kısıtlanması Hakkında Yönetmelik) | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=23694&MevzuatTur=7&MevzuatTertip=5 · ilk metin: https://www.resmigazete.gov.tr/eskiler/2017/06/20170623M1-18.htm · son değişiklik: https://www.resmigazete.gov.tr/eskiler/2023/12/20231223-9.htm | REACH'in TR karşılığı (Çevre, Şehircilik ve İklim Değişikliği Bakanlığı) | RG 23/6/2017, sayı 30105 (Mükerrer); değişiklikler: RG 29/11/2019, sayı 30963 ve RG 23/12/2023, sayı 32408. Güncel kayıt son tarihleri (geçici md. 2/1, 2023 değişikliği): a) 31/12/2026: yıllık ≥1000 ton; yıllık ≥100 ton ve Sucul Akut 1/Sucul Kronik 1 (H400, H410); yıllık ≥1 ton ve kanserojen/mutajen/üreme toksik Kategori 1A-1B; b) 31/12/2028: yıllık ≥100 ton; c) 31/12/2030: yıllık ≥1 ton | metin_elde (konsolide metin + RG) |
| "CE" İşaretine Dair Yönetmelik | — | 7223 md. 24/2-a'ya göre Cumhurbaşkanınca çıkarılır | mevzuat.gov.tr başlık aramasında bulunamadı | dogrulanmadi |

Okuma tarihi notu: KKDİK'in ilk kademe son tarihi (31/12/2026) bu raporun tarihinden sonraki ilk son tarihtir. Kimyasal içeren bir ürün tasarımında KKDİK denetimi gündeme gelirse güncel metin yeniden okunmalı.

### 2.3 Açık teknik kaynaklar (BIPM / JCGM)

| Kaynak | Resmî URL | Ne olduğu ve özet | Doğrulama |
| --- | --- | --- | --- |
| JCGM 100:2008 (GUM) "Evaluation of measurement data — Guide to the expression of uncertainty in measurement" | Sayfa: https://www.bipm.org/en/committees/jc/jcgm/publications · DOI: https://doi.org/10.59161/JCGM100-2008E · PDF: https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf | Ölçüm belirsizliğini değerlendirme ve ifade etme kılavuzu. Standart belirsizlik (2.3.1): "uncertainty of the result of a measurement expressed as a standard deviation"; A tipi (tekrarlı ölçüm, 4.2) ve B tipi (diğer bilgi, 4.3) değerlendirme; birleşik standart belirsizlik (2.3.4) ve genişletilmiş belirsizlik (6.2.1): "U = k uc(y)", sonuç "Y = y ± U" biçiminde yazılır; k kapsam çarpanıdır (2.3.6). | metin_elde |
| JCGM 100:2008/Amd.1:2026 "AMENDMENT 1: Nonlinearity in measurement models" | Aynı sayfa; DOI: https://doi.org/10.59161/PPDI3267 | GUM'a 2026'da eklenen değişiklik: doğrusal olmayan ölçüm modelleri; 5 sayfa. İçeriği okunmadı, yalnız kapak. | metin_elde (kapak ve künye) |
| JCGM 106:2012 "The role of measurement uncertainty in conformity assessment" | DOI: https://doi.org/10.59161/JCGM106-2012 · PDF: https://www.bipm.org/documents/20126/2071204/JCGM_106_2012_E.pdf | Belirsizlikle uygunluk değerlendirmesi (bir parça toleransa uyuyor mu kararı). **Karar kuralı** (3.3.12): "documented rule that describes how measurement uncertainty will be accounted for with regard to accepting or rejecting an item". **Koruma bandı** (3.3.11): "interval between a tolerance limit and a corresponding acceptance limit". Basit kabulde (8.2) tolerans sınırına çok yakın ölçümde yanlış karar olasılığı "can be as large as 50 %" (8.3.1.2). Korumalı kabulde (8.3.2) kabul sınırı tolerans içine çekilir: "w = TU − AU", çoğu uygulamada "w = rU"; "A common choice is r = 1". ISO 14253-1 örneğinde w = U = 2u ile yanlış kabul olasılığı normal dağılımda "at most 2.3 %". | metin_elde |

Araca uygulanışı (öneri):
- Ölçülen her değer (`olcu:kumpas|mastar|tarama`) yanında standart belirsizlik `u` ve kaynağı (A ya da B tipi) taşır. Kumpasın belirsizliği aletin belgesinden (B tipi) ya da tekrarlı ölçümden (A tipi) gelir. Uydurulmaz; bilinmiyorsa `varsayim` + kart.
- Geçme, boşluk ve tolerans kontrolleri JCGM 106 karar kuralıyla yazılır: kontrolün kaydında `karar_kurali: basit_kabul | korumali_kabul`, `r` (koruma bandı çarpanı) `karar` kaynağıyla ve `standart:JCGM 106:2012 8.3.2.3` atfıyla. Sınıra yakın ölçüm "uygun" değil "belirsiz" sonucu verir.
- Telif notu: JCGM metinlerinde "Third parties cannot rewrite or re-brand, issue or sell copies to the public, broadcast or use on-line" (JCGM 100) ve benzer hüküm (JCGM 106) var. **JCGM PDF'leri AGPL repoya konmamalı; yalnız bağlantı verilmeli.** NASA belgeleri "APPROVED FOR PUBLIC RELEASE—DISTRIBUTION IS UNLIMITED" taşıyor; yine de bağlantı vermek yeterli.

---

## 3. Bağımlılık lisans tablosu (AGPL-3.0 ile uyum)

### 3.1 Genel kurallar ve dayanakları

| Kural | Dayanak (birebir) | Doğrulama |
| --- | --- | --- |
| AGPL ile GPLv3 birleşebilir (AGPL §13 ikinci paragraf) | "you have permission to link or combine any covered work with a work licensed under version 3 of the GNU General Public License into a single combined work ... the work with which it is combined will remain governed by version 3 of the GNU General Public License." | metin_elde (AGPL-3.0 metni, OrcaSlicer LICENSE.txt kopyası) |
| GPLv3 §13 karşı yönü | "you have permission to link or combine any covered work with a work licensed under version 3 of the GNU Affero General Public License ... the special requirements of the GNU Affero General Public License, section 13, concerning interaction through a network will apply to the combination as such." | metin_elde (GPL-3.0 metni, PyMeshLab LICENSE kopyası) |
| AGPL §13 ağ yükümlülüğü | "if you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network ... an opportunity to receive the Corresponding Source" | metin_elde. **Panel (FastAPI + web arayüzü) uzaktan (ör. Tailscale üzerinden) kullanılırsa, değiştirilmiş sürüm kaynağını kullanıcıya sunmalı.** Panelde o commit'in kaynağına bağlantı önerilir. |
| Ayrı programlar: "aggregate" (GPLv3/AGPLv3 §5 son paragraf) | "Inclusion of a covered work in an aggregate does not cause this License to apply to the other parts of the aggregate." | metin_elde |
| Ayrı süreçle iletişim | GPL SSS (gnu.org): boru (pipe), soket ve komut satırı argümanları "normally used between two separate programs"; karmaşık iç veri yapıları paylaşılırsa tek program sayılabilir. | ikincil_kaynak (gnu.org erişilemedi) |
| Apache-2.0 → GPLv3/AGPLv3 | gnu.org lisans listesi: Apache-2.0 GPLv3 (ve AGPLv3) ile uyumlu, GPLv2 ile uyumsuz. | ikincil_kaynak |
| LGPL-2.1 → GPLv3 | LGPL-2.1 §3: "You may opt to apply the terms of the ordinary GNU General Public License instead of this License ... (If a newer version than version 2 of the ordinary GNU General Public License has appeared, then you can specify that version instead if you wish.)" Bu yol LGPL-2.1-only kütüphaneyi de GPLv3'e, oradan AGPL §13 ile birleşime taşır. Dinamik bağlamada buna gerek yoktur; LGPL koşulları doğrudan yeter. | metin_elde (LGPL-2.1 metni, OCCT deposu) |
| GPL-2.0-only + AGPL-3.0 | Aynı programda birleşirse uyumsuz (GPLv2-only, GPLv3 ek koşullarına izin vermez). Ayrı süreçte (komut satırıyla çağırma) sorun yok. | ikincil_kaynak (gnu.org erişilemedi); kural genel bilgi |
| Tescilli ayrı program | AGPL "System Libraries" istisnası işletim sistemi bileşenleri içindir; Claude Code gibi bir program buna girmez. Ama ayrı kurulan bir programı alt süreç olarak çağırmak "aggregate"/ayrı program durumudur; AGPL o programa uzanmaz, Corresponding Source onu içermez. | metin_elde (AGPL §1 ve §5 metni); uygulama yorumu |

### 3.2 Eski sistem: `pyproject.toml` ve `uv.lock` (salt okundu)

Kaynak: her satır için `https://pypi.org/pypi/<ad>/<sürüm>/json` (license_expression, license, sınıflandırıcılar). Sürümler `uv.lock`'tan. "Doğrudan" = `pyproject.toml` bağımlılığı; "dev" = geliştirme grubu.

| Paket | Sürüm (lock) | SPDX (PyPI'den) | Kaynak | AGPL-3.0 durumu |
| --- | --- | --- | --- | --- |
| aerosandbox **(doğrudan)** | 4.2.10 | MIT | `pypi.org/pypi/aerosandbox/4.2.10/json` | uyumlu |
| aiohappyeyeballs | 2.7.1 | PSF-2.0 | `pypi.org/pypi/aiohappyeyeballs/2.7.1/json` | uyumlu |
| aiohttp | 3.14.5 | Apache-2.0 AND MIT | `pypi.org/pypi/aiohttp/3.14.5/json` | uyumlu |
| aiosignal | 1.4.0 | Apache-2.0 | `pypi.org/pypi/aiosignal/1.4.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| annotated-doc | 0.0.5 | MIT | `pypi.org/pypi/annotated-doc/0.0.5/json` | uyumlu |
| annotated-types | 0.8.0 | MIT | `pypi.org/pypi/annotated-types/0.8.0/json` | uyumlu |
| anyio | 4.15.1 | MIT | `pypi.org/pypi/anyio/4.15.1/json` | uyumlu |
| attrs | 26.1.0 | MIT | `pypi.org/pypi/attrs/26.1.0/json` | uyumlu |
| cachetools | 7.2.5 | MIT | `pypi.org/pypi/cachetools/7.2.5/json` | uyumlu |
| cadquery **(doğrudan)** | 2.8.0 | Apache-2.0 | `pypi.org/pypi/cadquery/2.8.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| cadquery-ocp | 7.9.3.1.1 | Apache-2.0 (bağlama kodu); tekerlekte OCCT 7.9.3 .so: LGPL-2.1-only WITH OCCT-exception-1.0 | `pypi.org/pypi/cadquery-ocp/7.9.3.1.1/json` | uyumlu (koşullu: yeniden dağıtımda OCCT LGPL-2.1 metni ve OCCT istisnasının istediği belirgin bildirim eklenir; tekerlekteki diğer .so dosyaları incelenmedi) |
| cadquery-ocp-proxy | 7.9.3.1.1 | Apache-2.0 | `pypi.org/pypi/cadquery-ocp-proxy/7.9.3.1.1/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| casadi | 3.8.1 | LGPL-3.0-or-later | `pypi.org/pypi/casadi/3.8.1/json` | uyumlu (koşullu: LGPLv3 yükümlülükleri; casadi değiştirilirse kaynağı verilir) |
| click | 8.5.0 | BSD-3-Clause | `pypi.org/pypi/click/8.5.0/json` | uyumlu |
| colorama | 0.4.6 | BSD (yalnız sınıflandırıcı) | `pypi.org/pypi/colorama/0.4.6/json` | uyumlu |
| contourpy | 1.4.0 | BSD-3-Clause | `pypi.org/pypi/contourpy/1.4.0/json` | uyumlu |
| cycler | 0.12.1 | BSD (sınıflandırıcı) | `pypi.org/pypi/cycler/0.12.1/json` | uyumlu |
| dill | 0.4.1 | BSD-3-Clause | `pypi.org/pypi/dill/0.4.1/json` | uyumlu |
| ezdxf | 1.4.5 | MIT (sınıflandırıcı) | `pypi.org/pypi/ezdxf/1.4.5/json` | uyumlu |
| fastapi **(doğrudan)** | 0.162.0 | MIT | `pypi.org/pypi/fastapi/0.162.0/json` | uyumlu |
| fonttools | 4.67.0 | MIT | `pypi.org/pypi/fonttools/4.67.0/json` | uyumlu |
| frozenlist | 1.8.0 | Apache-2.0 | `pypi.org/pypi/frozenlist/1.8.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | `pypi.org/pypi/greenlet/3.5.6/json` | uyumlu |
| h11 | 0.16.0 | MIT | `pypi.org/pypi/h11/0.16.0/json` | uyumlu |
| httpcore2 | 2.16.0 | BSD-3-Clause | `pypi.org/pypi/httpcore2/2.16.0/json` | uyumlu |
| httpx2 **(doğrudan, dev)** | 2.16.0 | BSD-3-Clause | `pypi.org/pypi/httpx2/2.16.0/json` | uyumlu |
| httpx2-jsfetch | 1.0 | BSD-3-Clause | `pypi.org/pypi/httpx2-jsfetch/1.0/json` | uyumlu |
| idna | 3.20 | BSD-3-Clause | `pypi.org/pypi/idna/3.20/json` | uyumlu |
| imagesize | 2.0.1 | MIT | `pypi.org/pypi/imagesize/2.0.1/json` | uyumlu |
| iniconfig | 2.3.1 | MIT | `pypi.org/pypi/iniconfig/2.3.1/json` | uyumlu |
| kiwisolver | 1.5.1 | BSD-3-Clause ("Modified BSD") | `pypi.org/pypi/kiwisolver/1.5.1/json` | uyumlu |
| llvmlite | 0.50.0 | BSD-2-Clause AND Apache-2.0 WITH LLVM-exception | `pypi.org/pypi/llvmlite/0.50.0/json` | uyumlu |
| manifold3d **(doğrudan)** | 3.5.4 | Apache-2.0 (sınıflandırıcı) | `pypi.org/pypi/manifold3d/3.5.4/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| markdown-it-py | 4.2.0 | MIT (sınıflandırıcı) | `pypi.org/pypi/markdown-it-py/4.2.0/json` | uyumlu |
| matplotlib | 3.11.2 | Matplotlib lisansı (PSF tabanlı; SPDX kimliği yok) | `pypi.org/pypi/matplotlib/3.11.2/json` | uyumlu (PSF tabanlı izin verici; gnu.org teyidi alınamadı) |
| mdurl | 0.1.2 | MIT (sınıflandırıcı) | `pypi.org/pypi/mdurl/0.1.2/json` | uyumlu |
| meshio **(doğrudan)** | 5.3.5 | MIT | `pypi.org/pypi/meshio/5.3.5/json` | uyumlu |
| more-itertools | 11.2.1 | MIT | `pypi.org/pypi/more-itertools/11.2.1/json` | uyumlu |
| msgpack | 1.2.3 | Apache-2.0 | `pypi.org/pypi/msgpack/1.2.3/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| multidict | 7.2.1 | Apache-2.0 | `pypi.org/pypi/multidict/7.2.1/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| multimethod | 1.12 | Apache-2.0 | `pypi.org/pypi/multimethod/1.12/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| neuralfoil | 0.3.3 | MIT | `pypi.org/pypi/neuralfoil/0.3.3/json` | uyumlu |
| nlopt | 2.11.0 | MIT (Python sarmalayıcı meta verisi) | `pypi.org/pypi/nlopt/2.11.0/json` | uyumlu |
| numba | 0.68.0 | BSD (sınıflandırıcı) | `pypi.org/pypi/numba/0.68.0/json` | uyumlu |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | `pypi.org/pypi/numpy/2.5.4/json` | uyumlu |
| ocp-tessellate **(doğrudan)** | 3.6.3 | Apache-2.0 | `pypi.org/pypi/ocp-tessellate/3.6.3/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| opentelemetry-api | 1.45.1 | Apache-2.0 | `pypi.org/pypi/opentelemetry-api/1.45.1/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | `pypi.org/pypi/packaging/26.3/json` | uyumlu |
| pandas | 3.1.0 | BSD-3-Clause | `pypi.org/pypi/pandas/3.1.0/json` | uyumlu |
| pillow | 13.0.0 | MIT-CMU | `pypi.org/pypi/pillow/13.0.0/json` | uyumlu |
| playwright **(doğrudan, dev)** | 1.64.1 | Apache-2.0 | `pypi.org/pypi/playwright/1.64.1/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| pluggy | 1.7.0 | MIT | `pypi.org/pypi/pluggy/1.7.0/json` | uyumlu |
| propcache | 0.5.4 | Apache-2.0 | `pypi.org/pypi/propcache/0.5.4/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| pydantic | 2.14.1 | MIT | `pypi.org/pypi/pydantic/2.14.1/json` | uyumlu |
| pydantic-core | 2.50.1 | MIT | `pypi.org/pypi/pydantic-core/2.50.1/json` | uyumlu |
| pyee | 14.0.0 | MIT | `pypi.org/pypi/pyee/14.0.0/json` | uyumlu |
| pygments | 2.21.0 | BSD-2-Clause | `pypi.org/pypi/pygments/2.21.0/json` | uyumlu |
| pyparsing | 3.3.3 | MIT | `pypi.org/pypi/pyparsing/3.3.3/json` | uyumlu |
| pytest **(doğrudan, dev)** | 9.1.1 | MIT | `pypi.org/pypi/pytest/9.1.1/json` | uyumlu |
| python-dateutil | 3.0.0 | Apache-2.0 ve BSD-3-Clause ("Dual License") | `pypi.org/pypi/python-dateutil/3.0.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| pyyaml **(doğrudan)** | 6.0.3 | MIT | `pypi.org/pypi/pyyaml/6.0.3/json` | uyumlu |
| rich | 15.0.0 | MIT | `pypi.org/pypi/rich/15.0.0/json` | uyumlu |
| runtype | 0.5.3 | MIT | `pypi.org/pypi/runtype/0.5.3/json` | uyumlu |
| scikit-fem **(doğrudan)** | 12.0.2 | BSD (sınıflandırıcı) | `pypi.org/pypi/scikit-fem/12.0.2/json` | uyumlu |
| scipy | 1.18.1 | BSD-3-Clause | `pypi.org/pypi/scipy/1.18.1/json` | uyumlu |
| seaborn | 0.13.2 | BSD (sınıflandırıcı) | `pypi.org/pypi/seaborn/0.13.2/json` | uyumlu |
| six | 1.17.0 | MIT | `pypi.org/pypi/six/1.17.0/json` | uyumlu |
| sortedcontainers | 2.4.0 | Apache-2.0 | `pypi.org/pypi/sortedcontainers/2.4.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| starlette | 1.10.0 | BSD-3-Clause | `pypi.org/pypi/starlette/1.10.0/json` | uyumlu |
| tetgen **(doğrudan)** | 0.8.4 | meta veri: MIT; gerçekte MIT AND AGPL-3.0-or-later (tekerlekte derlenmiş TetGen + src/tetgen-license) | `pypi.org/pypi/tetgen/0.8.4/json` | uyumlu (koşullu: TetGen kısmı AGPL; proje AGPL kaldıkça sorun yok, başka lisansa geçişi engeller) |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | `pypi.org/pypi/tqdm/4.70.1/json` | uyumlu (MPL-2.0 dosya düzeyinde copyleft; ikincil lisans yolu) |
| trame | 4.0.0 | Apache-2.0 | `pypi.org/pypi/trame/4.0.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| trame-client | 4.1.4 | MIT | `pypi.org/pypi/trame-client/4.1.4/json` | uyumlu |
| trame-common | 1.2.9 | Apache-2.0 (sınıflandırıcı) | `pypi.org/pypi/trame-common/1.2.9/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| trame-components | 2.5.0 | Apache-2.0 | `pypi.org/pypi/trame-components/2.5.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| trame-server | 4.1.0 | Apache-2.0 | `pypi.org/pypi/trame-server/4.1.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| trame-vtk | 2.11.17 | BSD | `pypi.org/pypi/trame-vtk/2.11.17/json` | uyumlu |
| trame-vuetify | 3.3.0 | MIT | `pypi.org/pypi/trame-vuetify/3.3.0/json` | uyumlu |
| trimesh **(doğrudan)** | 5.2.0 | MIT | `pypi.org/pypi/trimesh/5.2.0/json` | uyumlu |
| truststore | 0.10.5 | MIT | `pypi.org/pypi/truststore/0.10.5/json` | uyumlu |
| typing-extensions | 4.16.0 | PSF-2.0 | `pypi.org/pypi/typing-extensions/4.16.0/json` | uyumlu |
| typing-inspection | 0.4.4 | MIT | `pypi.org/pypi/typing-inspection/0.4.4/json` | uyumlu |
| tzdata | 2026.5 | Apache-2.0 | `pypi.org/pypi/tzdata/2026.5/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| uvicorn **(doğrudan)** | 0.54.0 | BSD-3-Clause | `pypi.org/pypi/uvicorn/0.54.0/json` | uyumlu |
| vtk | 9.6.2 | BSD (sınıflandırıcı) | `pypi.org/pypi/vtk/9.6.2/json` | uyumlu |
| watchdog **(doğrudan)** | 6.0.0 | Apache-2.0 | `pypi.org/pypi/watchdog/6.0.0/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |
| webcolors | 25.10.0 | BSD-3-Clause | `pypi.org/pypi/webcolors/25.10.0/json` | uyumlu |
| wslink | 2.6.0 | BSD (sınıflandırıcı) | `pypi.org/pypi/wslink/2.6.0/json` | uyumlu |
| yarl | 1.25.1 | Apache-2.0 | `pypi.org/pypi/yarl/1.25.1/json` | uyumlu (Apache-2.0: GPLv3/AGPLv3 ile tek yönlü uyumlu) |

Kilit dosyası notları:
- **tetgen 0.8.4**: PyPI meta verisi `License-Expression: MIT` diyor, ama tekerlek `tetgen/_tetgen.abi3.so` (derlenmiş TetGen) ve `licenses/src/tetgen-license` (AGPL metni) içeriyor (tekerlek listelendi, `metin_elde`). pyvista README: "This Python wrapper is licensed under the MIT license. However, the underlying TetGen library is licensed under AGPL". Gerçek ifade: `MIT AND AGPL-3.0-or-later`.
- **cadquery-ocp 7.9.3.1.1**: tekerlekte `cadquery_ocp.libs/libTK*.so.7.9.3` (OCCT) ve freeimage, freetype, libraw, libgomp, lcms2, libtiff, openjp2, libwebp, OpenEXR, zstd gibi paylaşımlı kütüphaneler var (aralıklı indirme ile listelendi, `metin_elde`). Tekerlekte yalnız `cadquery_ocp/LICENSE` (Apache-2.0) bulunuyor; OCCT LGPL metni görünmüyor. Bu alt kütüphanelerin lisansları tek tek incelenmedi (`dogrulanmadi`). Yalnız `pip/uv` ile kurdurmak (yeniden dağıtmamak) sorunu en aza indirir; kap imajı ya da paketli dağıtımda lisans metinleri eklenmeli.
- **httpx2 / httpcore2**: kilitte `httpx` yok, `pydantic/httpx2` çatalı var (BSD-3-Clause).
- **nlopt 2.11.0**: PyPI meta verisi MIT (Python sarmalayıcı). İçindeki NLopt C kütüphanesinin lisansı (kısmen LGPL olabilir) `dogrulanmadi`; LGPL çıksa da uyumlu.

### 3.3 v1'de düşünülenler

| Bileşen | Sürüm | SPDX | Kaynak | AGPL-3.0 durumu | Gerekçe |
| --- | --- | --- | --- | --- | --- |
| jsonschema | 4.26.0 | MIT | pypi.org/pypi/jsonschema/json | uyumlu | İzin verici |
| pydantic | 2.14.3 | MIT | pypi.org/pypi/pydantic/json | uyumlu | İzin verici |
| typer | 0.27.3 | MIT | pypi.org/pypi/typer/json | uyumlu | İzin verici |
| click | 8.5.0 | BSD-3-Clause | pypi.org/pypi/click/json | uyumlu | İzin verici |
| httpx | 0.28.1 | BSD-3-Clause | pypi.org/pypi/httpx/json | uyumlu | İzin verici |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | pypi.org/pypi/numpy/json | uyumlu | Hepsi izin verici |
| scipy | 1.18.1 | BSD-3-Clause | pypi.org/pypi/scipy/json | uyumlu | İzin verici |
| matplotlib | 3.11.2 | Matplotlib lisansı (PSF tabanlı) | pypi.org/pypi/matplotlib/json | uyumlu | PSF tabanlı izin verici; gnu.org teyidi alınamadı |
| shapely | 2.2.0 | BSD-3-Clause | pypi.org/pypi/shapely/json; raw.githubusercontent.com/shapely/shapely/main/LICENSE.txt | uyumlu | Tekerlekte GEOS (LGPL-2.1) olması beklenir, `dogrulanmadi`; LGPL olsa da uyumlu |
| build123d | 0.13.0 | Apache-2.0 | pypi.org/pypi/build123d/json; raw.githubusercontent.com/gumyr/build123d/dev/LICENSE | uyumlu | Apache-2.0 → AGPLv3 tek yönlü uyumlu |
| OCP (cadquery-ocp) | 8.0.1.1.0 (en yeni) | Apache-2.0 (bağlama) | pypi.org/pypi/cadquery-ocp/json; raw.githubusercontent.com/CadQuery/OCP/master/LICENSE | uyumlu (koşullu: içindeki OCCT LGPL koşulları) | Tekerlek OCCT ikili dosyalarını taşır (3.2 notu) |
| OCCT | 7.9.3 (OCP içinde) | LGPL-2.1-only WITH OCCT-exception-1.0 | raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/LICENSE_LGPL_21.txt, .../OCCT_LGPL_EXCEPTION.txt, README.md | uyumlu (koşullu: LGPL-2.1 yükümlülükleri + istisnanın bildirimi) | Başlık dosyası: "GNU Lesser General Public License version 2.1 ... with special exception". İstisna, başlık dosyalarından gelen kodu içeren nesne kodunu "under terms of your choice" dağıtmaya izin verir, koşulu: "you give prominent notice in supporting documentation to this code that it makes use of or is based on facilities provided by the Open CASCADE Technology software." Dinamik bağlama; OCCT değiştirilirse onun kaynağı verilir. |
| neuralfoil | 0.3.3 | MIT | pypi.org/pypi/neuralfoil/json; raw.githubusercontent.com/peterdsharpe/NeuralFoil/master/LICENSE.txt | uyumlu | İzin verici. Not: ML vekil model, 1.Q'ya göre ayrı güvenilirlik kaydı ister |
| open3d | 0.20.0 | MIT | pypi.org/pypi/open3d/json; raw.githubusercontent.com/isl-org/Open3D/main/LICENSE | uyumlu | İzin verici; tekerlekteki üçüncü taraf kütüphaneler incelenmedi |
| pyransac3d | 0.7.0 | Apache-2.0 | pypi.org/pypi/pyransac3d/json; raw.githubusercontent.com/leomariga/pyRANSAC-3D/master/LICENSE | uyumlu | Apache-2.0 → AGPLv3 |
| pymeshlab | 2025.7.post1 | GPL-3.0 ("only" ya da "or-later" ayrımı `dogrulanmadi`) | pypi.org/pypi/pymeshlab/json; raw.githubusercontent.com/cnr-isti-vclab/PyMeshLab/main/LICENSE | uyumlu (koşullu: AGPL §13) | Birleşimde pymeshlab kısmı GPLv3 kalır, bütün AGPL §13'e tabi; MeshLab eklentilerinin lisansları incelenmedi |
| gmsh (Python paketi) | 4.15.2 | GPL-2.0-or-later WITH Gmsh-exception | pypi.org/pypi/gmsh/json (sınıflandırıcı "GPL v2 or later"); istisna metni raw.githubusercontent.com/spdx/license-list-data/main/text/Gmsh-exception.txt | uyumlu (koşullu: "or later" ile GPLv3 seçilir, sonra AGPL §13) | gmsh kütüphanesi Python sürecine yüklenir; "or later" olmasaydı uyumsuz olurdu. İstisna yalnız Netgen, METIS, OpenCASCADE, ParaView ile birleşime izin verir |
| FreeCAD | — | LGPL-2.1-or-later | raw.githubusercontent.com/FreeCAD/FreeCAD/main/LICENSE; src/App/Application.cpp: "SPDX-License-Identifier: LGPL-2.1-or-later" | uyumlu | LGPL; ayrı program ya da modül olarak |
| OrcaSlicer | — | AGPL-3.0 | raw.githubusercontent.com/SoftFever/OrcaSlicer/main/LICENSE.txt; README: "licensed under the GNU Affero General Public License, version 3" | uyumlu | Aynı lisans |
| PrusaSlicer | — | AGPL-3.0 | raw.githubusercontent.com/prusa3d/PrusaSlicer/master/LICENSE | uyumlu | Aynı lisans |
| CuraEngine | — | AGPL-3.0 | raw.githubusercontent.com/Ultimaker/CuraEngine/main/LICENSE | uyumlu | Aynı lisans |
| CalculiX (ccx) | — | GPL-2.0-only (ikincil) | GitHub aynası raw.githubusercontent.com/Dhondtguido/CalculiX/master/LICENSE (GPLv2 metni); Debian copyright: "(version 2)"; MSYS2 "GPL-2.0-or-later" diyor | **yalnız ayrı program olarak** | Kaynak başlığı doğrudan okunamadı; ihtiyatla "only" kabul edildi. `ccx` girdi dosyasıyla alt süreç olarak çağrılır; kodu AGPL koda bağlanmaz |
| Elmer FEM | — | LGPL-2.1-or-later (incelenen çekirdek dosyalar) | raw.githubusercontent.com/ElmerCSC/elmerfem/devel/fem/src/Solver.F90, ElmerSolver.F90, modules/StressSolve.F90 başlıkları; fem/LICENSES (METIS, AMD vb. üçüncü taraf) | uyumlu (koşullu: ayrı program önerilir) | Çekirdek LGPL; dağıtımdaki üçüncü taraf parçalar (METIS'in ticari dağıtım koşulları dahil) ve ElmerGUI lisansı incelenmedi |
| OpenFOAM | — | GPL-3.0-or-later | raw.githubusercontent.com/OpenFOAM/OpenFOAM-dev/master/COPYING; argList.C başlığı "either version 3 of the License, or (at your option) any later version" | uyumlu (koşullu: AGPL §13 birleşimde; pratikte ayrı program) | GPLv3+ |
| openInjMoldSim | — | GPL-3.0 ("or later" `dogrulanmadi`) | raw.githubusercontent.com/krebeljk/openInjMoldSim/master/LICENSE.md (GPLv3 metni); README "OpenFOAM 7 installation ... is required" | uyumlu (koşullu: AGPL §13; pratikte ayrı program) | OpenFOAM çözücüsü türevi |
| TetGen (C++ kütüphanesi) | 1.5.1 (ufz aynası) | AGPL-3.0-or-later (ya da WIAS ticari lisansı) | raw.githubusercontent.com/ufz/tetgen/master/LICENSE: "dual licensing scheme ... GNU Affero General Public License ... either version 3 of the License, or (at your option) any later version" | uyumlu | **Evet, TetGen AGPL.** Proje AGPL kaldıkça sorun yok; ileride daha gevşek lisansa geçişi engeller |
| tetgen (Python sarmalayıcı) | 0.8.4 | MIT (sarmalayıcı) AND AGPL-3.0-or-later (içindeki TetGen) | pypi.org/pypi/tetgen/0.8.4/json; raw.githubusercontent.com/pyvista/tetgen/main/LICENSE, README.rst, src/tetgen-license | uyumlu (koşullu: meta veri eksik, AGPL kısmı bilinmeli) | Bkz. 3.2 notu |
| three.js | 0.187.0 (npm en yeni) | MIT | registry.npmjs.org/three/latest; raw.githubusercontent.com/mrdoob/three.js/dev/LICENSE | uyumlu | İzin verici |
| three-cad-viewer | 5.1.3 | MIT | registry.npmjs.org/three-cad-viewer/5.1.3; raw.githubusercontent.com/bernhard-42/three-cad-viewer/master/LICENSE | uyumlu | İzin verici |
| @types/three | 0.183.1 | MIT | registry.npmjs.org/@types/three/0.183.1 | uyumlu | Yalnız geliştirme |
| vite | 8.3.5 | MIT | registry.npmjs.org/vite/8.3.5; raw.githubusercontent.com/vitejs/vite/main/LICENSE | uyumlu | Derleme aracı |
| typescript | 6.0.2 | Apache-2.0 | registry.npmjs.org/typescript/6.0.2; raw.githubusercontent.com/microsoft/TypeScript/main/LICENSE.txt | uyumlu | Derleme aracı; Apache-2.0 → AGPLv3 |
| Playwright (Python ve Node) | 1.64.1 / 1.65.0 | Apache-2.0 | pypi.org/pypi/playwright/json; registry.npmjs.org/playwright/latest; raw.githubusercontent.com/microsoft/playwright/main/LICENSE | uyumlu | Yalnız test. İndirdiği tarayıcı ikilileri ayrı programdır, dağıtılmaz |
| pytest | 9.1.1 / 9.2.0 | MIT | pypi.org/pypi/pytest/json; raw.githubusercontent.com/pytest-dev/pytest/main/LICENSE | uyumlu | Yalnız test |
| uv | 0.13.7 | MIT OR Apache-2.0 | pypi.org/pypi/uv/json; raw.githubusercontent.com/astral-sh/uv/main/LICENSE-MIT ve LICENSE-APACHE | uyumlu | Ayrı araç |
| Node.js | — | MIT (+ paketlenmiş bağımlılıkların kendi lisansları) | raw.githubusercontent.com/nodejs/node/main/LICENSE | uyumlu | Ayrı çalışma ortamı |
| git | — | GPL-2.0-only | raw.githubusercontent.com/git/git/master/COPYING: "the only valid version of the GPL as far as this project is concerned is _this_ particular version of the license (ie v2, not v2.2 or v3.x" | **yalnız ayrı program olarak** | Komut satırıyla çağrılır, zaten ayrı program; libgit2 benzeri bir kütüphaneye bağlanmak gerekirse ayrıca bakılmalı |
| Claude Code CLI (@anthropic-ai/claude-code) | 2.1.318 (npm) | tescilli (SPDX kimliği yok; npm: "SEE LICENSE IN README.md") | raw.githubusercontent.com/anthropics/claude-code/main/LICENSE.md: "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service" | **yalnız ayrı program olarak** | Kullanıcı kendisi kurar; araç alt süreç olarak çağırır; repoya ya da dağıtıma konmaz. "System Libraries" istisnasına girmez. Ayrıca dışarıya veri gönderir: dur noktası kuralı geçerli |
| claude-agent-sdk (Python) | 0.2.178 | MIT (kaynak kod) | pypi.org/pypi/claude-agent-sdk/json; raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/LICENSE; README: "The Claude Code CLI is automatically bundled with the package" | uyumlu (koşullu: CLI'yi içeren platform tekerlekleri yeniden dağıtılmaz) | Platform tekerlekleri 138–152 MB ve tescilli CLI'yi içeriyor (PyPI dosya listesi). Kaynak kod MIT; bağımlılık olarak bildirmek sorun değil, tekerleği paketlemek sorun |
| @anthropic-ai/claude-agent-sdk (TS) | 0.3.318 (npm) | tescilli (npm: "SEE LICENSE IN README.md") | raw.githubusercontent.com/anthropics/claude-agent-sdk-typescript/main/LICENSE.md: "© Anthropic PBC. All rights reserved." | **uyumsuz** (AGPL kodla aynı pakete bağlanıp dağıtılırsa); yalnız ayrı program olarak | Panel ön yüzüne ya da AGPL Node koduna bağlanmamalı. Gerekirse Python SDK (MIT) ile CLI alt süreç olarak çağrılır |

### 3.4 Özet listeler

**Uyumsuz (aynı programa bağlanıp dağıtılırsa):**
- `@anthropic-ai/claude-agent-sdk` (TS): tescilli. AGPL koda gömülmemeli.
- GPL-2.0-only bileşenler (CalculiX ccx, git): AGPL koda bağlanamaz. Ayrı süreç olarak sorun yok.
- Claude Code CLI: tescilli. Repoya ya da dağıtım paketine konamaz; ayrı program olarak çağrılır.

**Yalnız ayrı program olarak:**
- CalculiX (GPL-2.0-only, ikincil kaynak), git (GPL-2.0-only), Claude Code CLI (tescilli), TS Agent SDK (tescilli).
- Önerilen: OpenFOAM, openInjMoldSim, Elmer, slicer'lar (OrcaSlicer, PrusaSlicer, CuraEngine) da ayrı program olarak çağrılsın. Lisans gerektirmiyor ama sınırı netleştirir.

**Uyumlu (koşullu):**
- OCCT (cadquery-ocp içinde): LGPL-2.1-only + OCCT istisnası. Dağıtımda LGPL metni ve "Open CASCADE Technology kullanır" bildirimi; değiştirilirse OCCT kaynağı.
- tetgen (PyPI): meta veri MIT diyor ama TetGen AGPL-3.0-or-later. Proje AGPL kaldıkça uyumlu. Lisans değişikliği düşünülürse engel.
- gmsh: GPL-2.0-or-later WITH Gmsh-exception. "or later" sayesinde GPLv3 → AGPL §13.
- pymeshlab, OpenFOAM, openInjMoldSim: GPLv3 ailesi. AGPL §13 ile birleşir; GPLv3 kısımları GPLv3 kalır.
- casadi (LGPL-3.0-or-later), Elmer (LGPL-2.1-or-later), FreeCAD (LGPL-2.1-or-later): LGPL koşulları.
- tqdm (MPL-2.0 AND MIT): MPL dosya düzeyinde copyleft; değiştirilen MPL dosyalarının kaynağı açık kalır.
- claude-agent-sdk (Python): MIT, ama CLI'li tekerlek yeniden dağıtılmaz.
- Apache-2.0 bileşenler (cadquery, build123d, OCP bağlamaları, manifold3d, typescript, Playwright, ...): AGPLv3 ile uyumlu, GPLv2 ile değil. Proje "GPL-2.0" kodla birleşmediği sürece sorun yok. Apache-2.0 §4 NOTICE dosyası korunmalı.

**Genel yükümlülükler (AGPL tarafı):**
- AGPL §13: panel uzaktan sunulursa değiştirilmiş sürümün kaynağı kullanıcıya sunulmalı.
- Kap imajı ya da paketli dağıtım yapılırsa (ör. `.venv` ya da Docker), içindeki ikililerin (OCCT, TetGen, freeimage, ...) lisans metinleri eklenmeli. Yalnız `uv sync` ile kurdurmak bu yükü azaltır.
- Yeni bağımlılık eklenince bu tablo bir kontrol betiğiyle yeniden üretilmeli: PyPI `license_expression` alanı boş ya da yanıltıcı olabiliyor (tetgen örneği). Betik tekerlek içindeki `licenses/` klasörünü de okumalı.

---

## 4. Kaynak listesi

| # | URL | İçerik | Durum |
| --- | --- | --- | --- |
| 1 | https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf | NASA-STD-7009B tam metin (88 s.) | metin_elde |
| 2 | https://standards.nasa.gov/standard/NASA/NASA-STD-7009 | Standart sayfası, "ACTIVE" | metin_elde |
| 3 | https://standards.nasa.gov/system/files/tmp/NASA-HDBK-7009B_Final%2002-03-2026.pdf | NASA-HDBK-7009B tam metin (175 s.) | metin_elde |
| 4 | https://standards.nasa.gov/standard/nasa/nasa-hdbk-7009 | El kitabı sayfası, "ACTIVE" | metin_elde |
| 5 | https://standards.nasa.gov/sites/default/files/standards/NASA/w/CHANGE-1/1/Historical/NASA_STD_7009A.pdf | NASA-STD-7009A (karşılaştırma) | metin_elde |
| 6 | https://eur-lex.europa.eu/eli/reg/2023/988/oj (CELEX 32023R0988) | GPSR | ikincil_kaynak (WAF engeli; WebSearch) |
| 7 | https://eur-lex.europa.eu/eli/reg/2023/1230/oj (CELEX 32023R1230) ve https://eur-lex.europa.eu/eli/reg/2023/1230/corrigendum/2023-07-04/oj/eng | Makine Tüzüğü ve düzeltmesi | ikincil_kaynak |
| 8 | https://eur-lex.europa.eu/eli/reg/2006/1907/oj (CELEX 32006R1907) | REACH | ikincil_kaynak |
| 9 | https://eur-lex.europa.eu/eli/dir/2011/65/oj (CELEX 32011L0065) | RoHS | ikincil_kaynak |
| 10 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=7223&MevzuatTur=1&MevzuatTertip=5 | 7223 sayılı Kanun, güncel metin | metin_elde |
| 11 | https://www.resmigazete.gov.tr/eskiler/2020/03/20200312-1.htm | 7223, RG 12/03/2020 sayı 31066 | metin_elde |
| 12 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=23694&MevzuatTur=7&MevzuatTertip=5 | KKDİK güncel metin ve değişiklik tablosu | metin_elde |
| 13 | https://www.resmigazete.gov.tr/eskiler/2017/06/20170623M1-18.htm | KKDİK ilk yayım | metin_elde |
| 14 | https://www.resmigazete.gov.tr/eskiler/2023/12/20231223-9.htm | KKDİK 2023 değişikliği (sayı 32408) | metin_elde |
| 15 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=38396&MevzuatTur=7&MevzuatTertip=5 | Genel Ürün Güvenliği Yönetmeliği | metin_elde |
| 16 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=4269&MevzuatTur=21&MevzuatTertip=5 | Ürünlerin PGD'ye Dair Çerçeve Yönetmelik | metin_elde |
| 17 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=4022&MevzuatTur=21&MevzuatTertip=5 | UDK ve Onaylanmış Kuruluşlar Yönetmeliği | metin_elde |
| 18 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=42348&MevzuatTur=7&MevzuatTertip=5 | Uzaktan iletişim araçlarıyla arz edilen ürünlerde PGD | metin_elde |
| 19 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=39359&MevzuatTur=7&MevzuatTertip=5 | Ticaret Bakanlığı PGD Yönetmeliği | metin_elde (künye) |
| 20 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=38796&MevzuatTur=7&MevzuatTertip=5 | Sanayi ve Teknoloji Bakanlığı PGD Yönetmeliği | metin_elde (künye) |
| 21 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=46338&MevzuatTur=7&MevzuatTertip=5 | Makine Emniyeti Yönetmeliği (2023/1230/AB), RG 16.10.2026 | metin_elde |
| 22 | https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=39913&MevzuatTur=7&MevzuatTertip=5 | TR RoHS yönetmeliği | metin_elde |
| 23 | https://www.mevzuat.gov.tr/Anasayfa/MevzuatDatatable (başlık araması, POST) | Yönetmelik künyeleri ve "CE İşareti" aramasının boş dönmesi | metin_elde |
| 24 | https://www.bipm.org/en/committees/jc/jcgm/publications | JCGM yayın listesi | metin_elde |
| 25 | https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf | GUM tam metin | metin_elde |
| 26 | https://www.bipm.org/documents/20126/2071204/JCGM_100_Amd1_2026.pdf | GUM Değişiklik 1 (2026), kapak | metin_elde |
| 27 | https://www.bipm.org/documents/20126/2071204/JCGM_106_2012_E.pdf | JCGM 106 tam metin | metin_elde |
| 28 | https://www.gnu.org/licenses/license-list.html | Lisans uyum listesi | ikincil_kaynak (site erişilemedi; WebSearch ve ayna özetleri) |
| 29 | https://www.gnu.org/licenses/agpl-3.0.html | AGPL-3.0 | gnu.org erişilemedi; aynı FSF metni raw.githubusercontent.com/SoftFever/OrcaSlicer/main/LICENSE.txt'den okundu → metin_elde |
| 30 | https://www.gnu.org/licenses/gpl-3.0.html | GPL-3.0 | aynı metin raw.githubusercontent.com/cnr-isti-vclab/PyMeshLab/main/LICENSE'tan → metin_elde |
| 31 | https://www.gnu.org/licenses/gpl-faq.html#MereAggregation | Ayrı program / birleşim | ikincil_kaynak |
| 32 | raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/{LICENSE_LGPL_21.txt, OCCT_LGPL_EXCEPTION.txt, README.md} | OCCT lisansı, istisna, LGPL-2.1 §3 | metin_elde |
| 33 | raw.githubusercontent.com/ufz/tetgen/master/LICENSE; raw.githubusercontent.com/pyvista/tetgen/main/{LICENSE, README.rst, src/tetgen-license} | TetGen ve sarmalayıcı lisansı | metin_elde |
| 34 | https://files.pythonhosted.org/.../tetgen-0.8.4-...whl ve cadquery_ocp-7.9.3.1.1-cp312-...whl | Tekerlek içerik listesi | metin_elde |
| 35 | raw.githubusercontent.com/spdx/license-list-data/main/json/{licenses.json, exceptions.json}, text/Gmsh-exception.txt | SPDX kimlik doğrulaması | metin_elde |
| 36 | raw.githubusercontent.com/anthropics/{claude-code/main/LICENSE.md, claude-agent-sdk-typescript/main/LICENSE.md, claude-agent-sdk-python/main/LICENSE, claude-agent-sdk-python/main/README.md} | Anthropic lisansları | metin_elde |
| 37 | registry.npmjs.org/{three, three-cad-viewer, vite, typescript, @types/three, playwright, @playwright/test, @anthropic-ai/claude-code, @anthropic-ai/claude-agent-sdk} | npm lisans alanları | metin_elde |
| 38 | pypi.org/pypi/<ad>/<sürüm>/json (3.2 ve 3.3'teki tüm Python paketleri) | PyPI lisans meta verisi | metin_elde |
| 39 | raw.githubusercontent.com/{FreeCAD/FreeCAD, SoftFever/OrcaSlicer, prusa3d/PrusaSlicer, Ultimaker/CuraEngine, OpenFOAM/OpenFOAM-dev, krebeljk/openInjMoldSim, ElmerCSC/elmerfem, git/git, nodejs/node, mrdoob/three.js, bernhard-42/three-cad-viewer, vitejs/vite, microsoft/TypeScript, microsoft/playwright, pytest-dev/pytest, astral-sh/uv, gumyr/build123d, shapely/shapely, isl-org/Open3D, leomariga/pyRANSAC-3D, peterdsharpe/NeuralFoil, CadQuery/OCP, CadQuery/cadquery, casadi/casadi}/... LICENSE dosyaları | Program lisansları | metin_elde |
| 40 | raw.githubusercontent.com/Dhondtguido/CalculiX/master/LICENSE; https://metadata.ftp-master.debian.org/changelogs/main/c/calculix-ccx/stable_copyright | CalculiX lisansı (ayna + Debian) | ikincil_kaynak ("only" ayrımı) |

Açık kalan işler (kart önerisi):
- EUR-Lex metinleri tarayıcıyla açılıp künyeler `metin_elde`'ye yükseltilmeli (bu oturumda bot koruması ve WebFetch alan kısıtı nedeniyle okunamadı; eur-lex.europa.eu ve www.gnu.org oturum ağ ayarlarında izinli olmalı).
- gnu.org lisans listesi doğrudan okunup 3.1'deki iki ikincil satır doğrulanmalı.
- CalculiX kaynak başlığındaki "version 2" ifadesi resmî kaynak paketinden okunmalı.
- "CE" İşaretine Dair Yönetmelik künyesi bulunmalı.
- cadquery-ocp tekerleğindeki alt kütüphanelerin (freeimage, freetype, libraw, libgomp) lisansları tek tek çıkarılmalı.
