Durum: ONAYLI — baş mühendis, 2026-11-06 08:33 UTC (T-23; ileti: "ediyorum"). v1 çalışmalarında bağlayıcıdır. Eski sistemde süren işler eski el-kitabi.md (0.2) ile sürer (aşağıda karar 11).

# Tasarım ve Mühendislik Süreç El Kitabı (mekanik v1)

Sürüm: v1 taslağı (sürüm numarasını onayla alır) · 2026-11-06 (sistem saati) · yazan rol: proje mühendisi · onaylayan: — · önceki: 0.2 (eski sistem `surec`, 2026-10-26)

**Dayanak etiketleri.** Değişen ya da yeni her kuralın yanında dayanağı parantez içinde yazılıdır. Eski metinden değişmeden gelen kuralda etiket yoktur.

| Etiket | Ne | Nerede |
| --- | --- | --- |
| Ö-nn | Eski el kitabı değişiklik önerileri | `surec/kayit/kurulum/el-kitabi-onerileri.md`; Ek B §12 |
| E-nn | Eski sistemin kurulum ve pilot dersleri | Ek B §11 |
| B-n | Bağımsız inceleme bulguları (B1–B8 = Ö-20…Ö-27) | Ek B §13 |
| T-nn | Baş mühendisin kararları | Mimari belge §20.2–§20.4 |
| G-nn | Geçici kararlar (onaylı) | Mimari belge §20.1 |
| KM-nn, KM2-nn | Kalite mühendisi bulguları ve kapanışları | Mimari belge §22 |
| kesin karar n | Faz 0 talimatının tartışılmaz kararları | Mimari belge §2.1 |
| mimari §x | `docs/design/architecture.md` bölümü | — |

## 1. Amaç, kapsam ve temel ilkeler

Bu el kitabı, her tasarım ve mühendislik işinin, hangi kurum için yapılırsa yapılsın, tek bir süreçle yürütülmesini tanımlar. Süreci `mekanik` aracı yürütür ve denetler. Küçük bir varyant da kalıplı bir ürün de aynı süreçten geçer; fark, uygulanan adım sayısındadır. İşi AI ekip üyeleri yürütür, baş mühendis izler, inceler ve onaylar.

**Kapsam:**

- ürün tasarımı (CAD) ve mühendislik hesapları;
- analiz ve deney;
- prototip, test ve üretime ya da baskıya çıkış.

Grafik tasarım işleri (katalog, kutu, etiket, web) v1'in dışındadır. İleride ayrı bir alan paketiyle gelir (T-03). *Alan paketi*, bir iş alanının (3B baskı, kalıp, analiz) kontrollerini, soru ağaçlarını ve profil türlerini getiren eklentidir.

**Kullanıcı.** Tek kullanıcı vardır; hesap sistemi yoktur. Baş mühendis, atölye ayarında tanımlı kişidir (kesin karar 2). *Atölye ayarı*, kişinin kendi makinesindeki ayardır: kişi, kimlikler, kurumlar, makineler, ölçme aletleri.

**Geçiş.** Bu el kitabı onaylandıktan sonra mekanik'te yürüyen çalışmalara uygulanır. Eski sistemde süren çalışmalar eski el kitabıyla (0.2) sürer. Eski bir çalışma yalnız baş mühendis isterse v1'e taşınır (G-23).

**Kurumlar.** Süreç kuruma bağlı değildir. Her kurumun bir kurum profili olur: ad, maliyet eşiği, gizlilik kuralları ve kurum verisinin model sağlayıcısına gidip gidemeyeceği (KM-50; mimari §3.3). Maliyet eşiği kurum başınadır (T-07). Veri aktarımına izin vermek DUR'dur ve kurulumda sorulur (mimari §13.2). Onay yetkilisi her kurumda baş mühendistir (kesin karar 2). Her kurumun işleri kendi reposunda durur; bir kurumun verisi başka bir kurumun işinde görünmez.

Bir kuruma bağlı olmayan işler **Bağımsız** kurumu altında açılır ve aynı kurallarla yürür. v1'de kodu `IND`'dir (mimari §13.2; bkz. açık noktalar).

**Temel ilkeler:**

1. **Kaynaksız sayı yok.** Her ölçünün kaynağı ve belirsizliği yazılıdır. Kural, model ve hesap kodundaki sayılar için de geçerlidir (G-17).
2. **Kaynaksız kural yok.** Her kural bir standarda, literatüre ya da kayıtlı bir üretim deneyimine dayanır.
3. **Neyin önemli olduğunu kurallar belirler, modelin kanaati değil.** Soru tetikleyicileri bölüm 7'dedir.
4. **Geri dönüşsüz adımı yalnız baş mühendis onaylar.** Onay imzalıdır (T-17).
5. **Her önemli karar geri alınabilir tutulur:** dal, etiket ve bağımlılık kaydıyla.
6. **İşi yapan kendi işini onaylamaz** (dört göz ilkesi).
7. **Süreç riske göre uyarlanır.** Küçük bir varyanta güvenlik parçası kadar süreç uygulanmaz.
8. **Her hata kalıcı bir kurala ve bir regresyon vakasına dönüşür** (mimari §2.2). *Regresyon vakası*, hatayı yeniden üreten ve kontrolün onu yakalayıp yakalamadığını sınayan örnektir.
9. **Saat her zaman sistemden alınır.** Ajan saat yazmaz (mimari §2.2, §4.13).

**Dil.** Arayüz ve belgeler Türkçedir; İngilizcesi de vardır. Kod, komut, dosya, dal, etiket ve kayıt alanı adları İngilizcedir. Gerekçe ve yorum metni yazıldığı dilde kalır, çevrilmez (kesin karar 1; mimari §4.12).

**Terimler** (arayüzde Türkçe, kayıtta İngilizce; mimari §2.3):

| Arayüz | Kayıtta | Anlamı |
| --- | --- | --- |
| DUR | `hold` | Baş mühendis onayı olmadan geçilmeyen karar |
| geçici karar | `provisional` | Ekibin verip kayda yazdığı, itiraz edilebilen karar |
| bildir | `witness` | Bilgi; karar değildir |
| ENGEL / UYARI / GEÇTİ | `block` / `warn` / `pass` | Kontrol sonucu |
| kart | `card` | Baş mühendisin göreceği her şey |
| baskı/üretim isteği | `release` | Bir parçanın basılması ya da üretilmesi için açılan DUR kartı |
| serbest bırakma | G5 | Ürün çıkışı: dondurulmuş sürüm, Rev A |
| kanıt | `evidence` | Bir isteği ya da standart maddesini karşılayan kayıt |
| istek listesi | `requirements` | Zorunlu (`mandatory`) ve istek (`wish`) maddeleri |
| geçme | `fit` | Tek nominal ve tek boşlukla tanımlı parça bağlantısı |
| anlama özeti | `intake summary` | Tanımlamanın çıktısı (bölüm 6) |
| standart haritası | `stdmap` | Çalışmaya uygulanan mevzuat ve standart maddeleri (bölüm 6) |

## 2. Dayanak standartlar ve literatür

Sürecin her parçası oturmuş bir standarda ya da literatüre dayanır. Standart metinleri çoğunlukla ücretlidir. Kütüphanede yalnız madde numarası ve kendi sözümüzle özet tutulur; metin kopyalanmaz (mimari §12). Önce açık bir karşılık aranır. Bulunamazsa standart, gerekçesiyle satın alma listesine girer. Satın alma maliyet etkisidir, DUR'dur ve ihtiyaç doğunca kartla istenir (T-08).

| Konu | Dayanak | Bu sistemde nerede |
| --- | --- | --- |
| Tasarım ve geliştirme kontrolü | ISO 9001, madde 8.3 ([ISO 9001:2026](https://www.lrqa.com/en/latest-news/iso-9001-publication-date-confirmed/); iskelet 2015 sürümüyle aynı) | Kapılar, gözden geçirme, doğrulama, geçerleme, değişiklik |
| Sistematik tasarım | VDI 2221 Blatt 1; Pahl–Beitz, *Engineering Design* | İstek listesi, kavram seçimi |
| Gereksinim–doğrulama eşlemesi | VDI 2206 (V-modeli) | Doğrulama planı, kapı kartında istek durumu |
| Aşamalar ve karar kapıları | Cooper, Stage-Gate | G0–G5 |
| Tasarım risk analizi | AIAG-VDA FMEA El Kitabı (2019) | Risk kaydı, A sınıfında DFMEA |
| Risk sınıflandırma örnekleri | IEC 62304 (A/B/C), AIAG-VDA eylem önceliği (Y/O/D) | Üç risk sınıfı |
| Konfigürasyon yönetimi | ISO 10007 | Sürüm, dal, etiket |
| Geçme ve tolerans | ISO 286-1/-2, ISO 2768-1 | Üretim profilleri |
| Geometrik tolerans | ISO 1101 | Teknik resim (talaşlı, kalıp) |
| Cıvata geçiş delikleri | ISO 273 | Bağlantı geçmeleri |
| Ölçme belirsizliği | JCGM 100 (GUM) | Ölçü kaynağı |
| Belirsizlikle uygunluk kararı | ISO 14253-1; ANSI/NCSL Z540.3 (4:1 oranı); JCGM 106:2012 (karar kuralı, koruma bandı) | 1/4 kuralı, korumalı kabul (mimari §10.7) |
| Optik tarayıcı doğruluğu | [VDI/VDE 2634](https://vdi.de/en/home/vdi-standards/details/vdivde-2634-blatt-2-optical-3-d-measuring-systems-optical-systems-based-on-area-scanning) Blatt 2 ve 3 | Ölçme aleti kaydı |
| Muayene noktaları | Muayene ve test planlarındaki Hold / Witness uygulaması | Karar seviyeleri |
| Model ve benzetim güvenilirliği | NASA-STD-7009B, NASA-HDBK-7009B | Geçerlilik alanı, hesap güvenilirliği, uyarlama kaydı (G-18, T-12; mimari §10.3–§10.4) |
| Gerilme yığılması | Pilkey ve Pilkey, *Peterson's Stress Concentration Factors* | İç köşe kuralı KOSE-01 (Ö-16) |
| Ürün güvenliği mevzuatı | AB ve TR mevzuatı; başlangıç listesi mimari §10.8'de | Standart haritası |
| Problem çözme | 8D | Hata kaydı |
| AI gözetimi | ISO/IEC 42001:2023; NIST AI RMF 1.0 | İnsan gözetimi, izlenebilirlik |
| Ürüne özel standart örneği | EN 1621-1 | İstek listesi, standart haritası |

## 3. Belge yapısı

Belgeler beş katmandır: üst katman neyin yapılacağını, alt katman nasıl yapılacağını söyler. Her belgede sürüm, tarih ve onaylayan yazılıdır. El kitabında, prosedürlerde, talimatlarda, kural kataloğunda ve standart kütüphanesinde yapılan her değişiklik baş mühendis onayı ister; DUR'dur (mimari §12).

| Katman | Ne | Örnekler | Nerede durur |
| --- | --- | --- | --- |
| 1. El kitabı | Bu belge: ilkeler, roller, kapılar | — | mekanik reposu |
| 2. Prosedür | Bir sürecin adımları | Tasarım, değişiklik, ölçüm, hata kaydı | mekanik reposu (bkz. açık noktalar) |
| 3. Talimat | Tek bir işin nasıl yapıldığı | Geçme tanımlama, FDM baskı, tarama, ölçülü kesit üretme | mekanik reposu (bkz. açık noktalar) |
| 4. Kural ve profil | Makinenin okuyabildiği kurallar | Kural kataloğu, süreç profili, rol tanımları, standart maddeleri, analiz aracı kayıtları; makine ve ölçme aleti profilleri | Standart kütüphanesi (mekanik reposu); makine ve alet profilleri atölye ayarında (mimari §3.3, §12) |
| 5. Kayıt | İşin kanıtı | İstek listesi, parametreler, kararlar, kartlar, onaylar, hesaplar, deneyler, günlük, kalite incelemeleri | Kurumun çalışma reposu, çalışmanın kendi klasörü (mimari §3.4) |

Katman 1–4 bütün kurumlar için ortaktır. Kod reposunda kişi, kurum ve makine verisi durmaz; bunlar atölye ayarındadır (mimari §3.1). Dosya düzeni el kitabının konusu değildir; mimari §3'te yazılıdır.

**Süreç profili.** Aşamalar, kapılar, sınıf–kapı eşlemesi, risk soruları ve kapı kontrol listesi maddeleri standart kütüphanesinde veri olarak durur. Varsayılan profil bu el kitabının §5–§6'sının birebir karşılığıdır (G-07).

**Sürüm sabitleme.** Standart kütüphanesi sürümlüdür. Çalışma kullandığı sürümü sabitler. Sürüm değişince standart haritasındaki fark bir kart olarak gelir (mimari §12).

Prosedür ve talimatlar bir seferde yazılmaz. Her biri ilk kullanıldığı işte yazılır, sonraki işlerde düzeltilir.

## 4. Roller ve ekip modeli

Tek onay yetkilisi baş mühendistir. Ekip karar verir ve rapor eder; hataları baş mühendisten önce bulmak ekibin görevidir.

| Rol | Kim | Yetkisi | Sorumluluğu |
| --- | --- | --- | --- |
| Baş mühendis | Atölye ayarındaki kişi | Onay, ret, itiraz, müdahale, geri alma; süreç belgelerini değiştirme. Onayları imzalıdır (T-17) | İnceler, onaylar, reddeder, yorum yazar, değer değiştirir |
| Proje mühendisi | Ana ajan oturumu: kullanıcının kendi açtığı Claude Code oturumu (T-01) | Geçici karar verir. DUR kategorisindeki kararı yalnız önerir (KM-02) | Plan, brief, karar kaydı, soru tespiti, rapor, divanı yönetme |
| Tasarım mühendisi | Alt ajan | Verilen brief içinde çizer | Tek parça ya da tek yön üretir; brief dışına çıkmaz |
| Tekniker | Alt ajan | Karar yetkisi yok | Kontrol, render, dışa aktarma, dosya işleri; geçti/kaldı raporu. Modeli değiştirmez, model notu açmaz (KM-28) |
| Kalite mühendisi | Alt ajan: kendi bağlamıyla çalışır, ana konuşmayı görmez, araçları salt okunurdur (T-01; mimari §4.8) | Bulgu yazar, karar vermez | Her kapı isteğinde, her baskı/üretim isteğinde ve anlama özeti onayından önce bağımsız inceleme (Ö-20, G-11; bölüm 10) |

*Alt ajan*, ana oturumun açtığı ve kendi bağlamıyla çalışan yardımcı ajandır. Hangi rolü hangi modelin yürüttüğü atölye ayarında ve eklenti tanımında durur; el kitabında yazılmaz. Kalıcı kayıtlara model adı değil rol yazılır (mimari §4.9).

**Ajan oturumu.** Oturumu kullanıcı kendisi açar: Claude Code masaüstü uygulaması, VS Code ya da terminal. mekanik bu oturuma eklenti olarak bağlanır; buna *eklenti kipi* denir. Kimlik doğrulama yalnız kullanıcının Claude Code aboneliğidir; mekanik ek API ücreti doğurmaz ve kimlik bilgisine dokunmaz. mekanik'in ajanı kendisi başlattığı *başsız kip* v1'de yoktur (T-01, G-10). Kapanmış bir oturum kendiliğinden yeniden başlatılmaz (T-09).

**Divan kuralları:**

1. Tasarım kararı teknikere verilmez; tekniker çizmez, seçmez, yorumlamaz.
2. Alt ajan yalnız iş paralelleşiyorsa ya da ana bağlamı dosya dökümüyle dolduracaksa açılır. Küçük iş ana oturumda yapılır.
3. Ajana kısa bağlam verilir: kilitli kurallar, tek görev, çıktı yolu. Dar çıktı istenir: dosya yolu ve tek satır, ya da geçti/kaldı ve nedeni.
4. İşi yapamayan ajanın işi bir üst katmana bir kez verilir; yine olmazsa proje mühendisi devralır.
5. Ucuz modelin hatasını kontroller yakalar. Bu yüzden kontroller modelden bağımsız betiklerdir (bölüm 10).
6. Karar kaydında her kararın hangi rolce verildiği yazılır.
7. Ekip DUR kapsamındaki bir sistem komutunu (sudo, kurulum, repo açma, dışarıya gönderme) kendisi çalıştırmaz. Komutu hazır yazar; baş mühendis çalıştırır (E-34).

## 5. Risk sınıfları ve uyarlama

Her iş G0'da A, B ya da C sınıfı alır. Sınıf, hangi kapıların ve belgelerin uygulanacağını belirler. Sınıf yükseltmek serbesttir; düşürmek baş mühendis onayı ister.

| Sınıf | Ölçüt (biri yeterli) | Örnek | Uygulanan |
| --- | --- | --- | --- |
| A | Güvenlikle ilgili; ya da hatayı düzeltmek eşiğin üstünde maliyet doğurur (kalıp, takım, toplu üretim); ya da standart veya mevzuat şartı var | Koruyucu ekipman, fren parçası, enjeksiyon kalıplı ürün | Bütün kapılar G0–G5; istek listesi; DFMEA; doğrulama planı; geçerleme; bağımsız inceleme |
| B | Yeni tasarım ama hata eşiğin altında maliyetle düzelir | Bağlantı parçası prototipi, yeni aparat, talaşlı tek parça | G0–G3 ve G5; kısa risk listesi; geçerleme isteğe bağlı |
| C | Mevcut ürünün varyantı; hata yeniden üretimle, eşiğin altında düzelir | Renk ya da ölçü varyantı | G0 brief, G1 keşif, G3 kontroller, G5 serbest bırakma |

**G0'da sorulan dört soru:**

1. Bu üründeki bir hata bir kişiye zarar verebilir mi?
2. Hatayı düzeltmek eşiğin üstünde maliyet doğurur mu (kalıp, takım, stok, toplu baskı)?
3. Uyulması gereken bir standart ya da mevzuat var mı?
4. Daha önce yapılmış bir şeyin varyantı mı?

İlk üç sorudan birine "evet" A demektir. Hepsine "hayır" ve 4'e "evet" C demektir. Geri kalan her şey B'dir.

**Sınıftan bağımsız G4.** İstek listesinde deneyle doğrulanacak bir zorunlu istek varsa G4 (geçerleme) kapısı sınıfa bakılmadan eklenir (Ö-26, B7).

**Maliyet eşiği.** TL değeri kurum başınadır ve kurulumda sorulur. Değer girilene kadar G0'daki 2. soru baş mühendise sorulur (T-07).

## 6. Yaşam döngüsü ve kapılar

Her iş G0'dan G5'e altı kapıdan geçer. Kapı, bir sonraki aşamaya geçmeden önce cevaplanması gereken sorudur. Tasarım akışı bu kapılara oturur: Keşif G1, Geliştirme G2, Kesinleştirme G3–G5. Dondurulmuş bir sürümde yapılan her değişiklik değişiklik prosedürüyle yürür ve DUR'dur.

**Kapılar çalışma seviyesinde işler.** Her çalışma kendi G0–G5 aşamalarından geçer; hangi kapıların uygulanacağını risk sınıfı belirler. Bir aşama bitince "tamamlandı" denir ve kapı etiketi konur. Çalışmanın G5'i **kapanış**tır: sonucu projeye birleşir ya da öğrenme olarak kapanır. **Serbest bırakma** yalnız ürün çıkışıdır: projeye birleşen sonuç dondurulur, Rev A ve ürün kodu alır. Projenin durumu ona birleşen çalışmalardan çıkar.

(Çizim: G0 → G1 → G2 → G3 → G4 → G5 akışı; G3'te kalan kontrol işi G2'ye geri gönderir; G5 baş mühendis onayı ister.)

**G3 → G2 dönüşü** (Ö-17, E-26). Doğrulamada kalan bir kontrol işi G2'ye geri gönderir. Dönüş gerekçesiyle yazılır ve baş mühendis onaylar. G2 etiketi yerinde kalır; düzeltilmiş tasarım için yeni bir G2 kapısı istenir. G5'i yalnız baş mühendis onayı açar.

**Aşama bitirme ve kapı geçişi** (mimari §4.2):

1. Ekip aşamayı `mekanik stage finish` ile bitirir. Kapı kontrol listesi ve kontroller çalışır.
2. Kalite mühendisi temiz bağlamla inceler. Açık YÜKSEK bulgu varken kapı kartı açılmaz (Ö-20).
3. Kapı kartı açılır. Kartta şunlar bulunur:
   - her istek için durum (karşılandı / karşılanmadı / kanıt bekliyor) ve kanıtın yeri (Ö-21, B2);
   - kötü ya da güvenilmez sonuçlu hesaplar (Ö-23, B4);
   - açık geçici kararlar ve itirazsız geçici kararlar (bölüm 7);
   - kapatılmış YÜKSEK kalite bulguları (mimari §10.5);
   - aşama sonu soru paketi (bölüm 7).
4. Baş mühendis kartı imzalı onaylar. Kapı yalnız onay özeti güncelse geçer; kapı etiketi bu onayla konur. İtirazsız geçici kararlar "kapıda kabul" olur (mimari §8.1).

| Kapı | Soru | Çıktı (kayıt) | Kontrol listesinden örnekler | Sınıf |
| --- | --- | --- | --- | --- |
| G0 Talep | Ne istiyoruz, başarıyı nasıl ölçeriz? | İstek listesi (zorunlu / istek, sayısal ölçütüyle), risk sınıfı, üretim yöntemi varsayımı, maliyet hedefi, anlama özeti, standart haritası | Her gereksinim ölçülebilir mi? Kaynağı (müşteri, standart, baş mühendis) yazılı mı? Anlama özeti onaylı mı (mimari §7.1)? Standart haritası var mı (mimari §10.8)? | A B C |
| G1 Kavram | Hangi çözüm, hangi ölçütle? | Seçenekler, değerlendirme matrisi, seçim kararı, kavram taslağı | En az üç seçenek var mı? Ölçüt ağırlıklarını baş mühendis verdi mi? Seçim tek bir varsayıma mı dayanıyor (E-33)? | A B C |
| G2 Tasarım | Ayrıntılar doğru ve kaynaklı mı? | Model, kaynak etiketli parametreler, geçme kaydı, risk kaydı ya da DFMEA, hesaplar, analiz planı | Kaynaksız ölçü yok mu? Her geçmenin görevi ve boşluk sınırı var mı? Üretim profili seçildi mi? Risk kaydı ya da DFMEA var mı (E-31)? Plandaki analizler yapıldı mı ya da baş mühendis vazgeçti mi (Ö-19)? Kritik hesaplar bağımsız yöntemle doğrulandı mı (Ö-18)? | A B |
| G3 Doğrulama | Gereksinimleri karşılıyor mu? | Kontrol sonuçları, hesap raporu, prototip ve test raporu, deney kayıtları, gereksinim–test eşlemesi | Her gereksinimin bir doğrulaması var mı? ENGEL sayısı sıfır mı? | A B C |
| G4 Geçerleme | Gerçek kullanımda işe yarıyor mu? | Kullanım denemesi, bayi ya da kullanıcı görüşü | Deneme koşulları ve kabul ölçütü yazılı mı? Zorunlu isteklerin hepsi "karşılandı" mı (Ö-21)? | A (B isteğe bağlı; deneyle doğrulanan zorunlu istek varsa her sınıf, Ö-26) |
| G5 Serbest bırakma | Üretime ya da baskıya gidebilir mi? | Dondurulmuş ve etiketli sürüm, teknik resim (bkz. açık noktalar) veya üretim/baskı dosyası, onay kaydı | Bütün kararlar onaylı ya da kapıda kabul edilmiş mi? Açık DUR yok mu? Zorunlu istekler karşılandı mı? Standart haritasında tiksiz zorunlu madde yok mu? Baş mühendis onayı var mı? | A B C |

**Baskı/üretim isteği ve serbest bırakma ayrıdır** (Ö-05, Ö-08, G-09):

- Baskı/üretim isteği, bir parçanın basılması ya da üretilmesi için açılan DUR kartıdır. 3B baskıda, kalıpta ve sacda aynı kuraldır (G-09). Ekip bunu `mekanik release request` ile açar.
- Prototip baskısı G3 içinde yapılır: ENGEL yokken ve baş mühendisin onayladığı baskı kartıyla. Basılan her parça `<code>-release-<no>` etiketi alır. Prototip baskısında G5 koşulu aranmaz.
- Üretim serbest bırakması G5'tir: dondurulmuş sürüm, Rev A ve G5 koşulu (bölüm 10).
- Her baskı/üretim isteğinde kalite mühendisi çalışır (Ö-20). Sınanmamış kritik hesaba dayanan baskı istenmez (Ö-18; bölüm 9).

### G0'dan önce: tanımlama ve anlama özeti (mimari §7)

Tanımlama sabit bir anket değildir. Ajan önce eldeki veriyi analiz eder, sonra yalnız veriden çıkmayanı sorar.

1. **İş türü.** Türleri alan paketleri getirir: sıfırdan parça, verilen parçaya kalıp, mevcut modelde değişiklik, analiz, taramadan model. Türü baş mühendis seçer ya da onaylar.
2. **Veri analizi.** Paketin analizcileri soru sorulmadan önce çalışır. Sonuçlar `derived` kaynaklıdır ve gerçek modelden görsel taşır.
3. **Sorular.**
   - Veriden çıkan soru sorulmaz; cevap `derived` kaynağıyla yazılır ve akışa bir satır düşer.
   - Her soruda neden önemli olduğu, cevap gelmezse ne varsayılacağı, bir görsel ve aciliyet yazılıdır.
   - DUR kategorisindeki soru varsayılanla geçilmez; iş o konuda durur (KM-03).
   - Aşama başına en çok 5 "şimdi" sorusu sorulur; gerisi aşama sonu paketine girer (T-06).
4. **Bulgular.** Çelişki, sayısız istek, gözden kaçan şey ve alternatif yakalanır. Onaylı bir zorunlu istek ölçütsüz olamaz.
5. **Anlama özeti.** İş türü, analizler, soruların durumu, bulgular, istek listesi, yöntem, alan paketleri ve standart haritası özetini taşır. Özet önce kalite mühendisine, sonra baş mühendise DUR kartı olarak gider (G-11). Onay olmadan tasarım başlamaz; G0 kapısının ön koşuludur.

### Standart haritası (mimari §10.8)

Standart haritası, çalışmaya uygulanan mevzuat, müşteri şartnamesi, standart, kılavuz ve literatür maddelerinin listesidir. G0'da çıkar; G0 kapısının ön koşuludur (STDMAP-01).

- Her maddenin alanları: amaç, neden burada, test yöntemi, kabul ölçütü (sayı + kaynak), kanıt, doğrulama durumu, tür.
- Doğrulama durumu üçtür: metin elde, ikincil kaynak, doğrulanmadı.
- Bir madde yalnız kanıtla ve kalite mühendisinin kontrolünden sonra tiklenir.
- Kaynak önceliği: (1) mevzuat; (2) müşteri şartnamesi; (3) açık teknik kaynaklar (JCGM, NASA, MIL, NIST); (4) üretici kılavuzları; (5) paralı standartlar.
- Mevzuat atfı okuma tarihini taşır. Okuma tarihi 365 günden eskiyse atıf yeniden doğrulanmak üzere uyarı verir (mimari §10.8; T-02).
- G5'te tiksiz zorunlu madde kalmaz.

## 7. Karar seviyeleri, soru tetikleyicileri ve onay

Ekip baş mühendisin ekran başında olmasını beklemez: kararını verir, kayda yazar, devam eder. Durduğu tek yer DUR eşikleridir.

**Karar iki seviyelidir** (KM-02, G-21):

| Seviye | Ne olur | Ne zaman |
| --- | --- | --- |
| DUR (`hold`) | Onay olmadan geçilmez. Ekip bağımsız işlere geçer; bağımsız iş yoksa durur ve bildirir | Sekiz kategori (kesin karar 7): üretim yöntemi; malzeme; ana ölçüler; standarttan sapma; maliyet etkisi (satın alma, kalıp, takım, paralı standart dahil); baskı ve üretim; istek listesi değişikliği (bir güvenlik gereksinimini gevşetmek dahil); yalnız baş mühendiste olan bilgi. Ayrıca dondurulmuş sürümü değiştirme ve süreç belgesini değiştirme (bkz. açık noktalar) |
| Geçici karar (`provisional`) | Karar gerekçesi ve görseliyle akışa düşer, iş sürer. En az bir alternatif kayda geçer. Baş mühendis bir sonraki kapıya kadar itiraz edebilir | DUR dışındaki bütün kararlar |

Eski "inceleme bekliyor" seviyesi yoktur. O seviyedeki kararlar geçici karara katıldı (KM-02).

**Bildir (`witness`) karar değildir, yalnız bildirimdir.** Panele ve akışa düşer, bildirim gider, iş beklemez. Örnekler: kalan kontrol, gecikme, bilgi notu. Bir kural sınırının dışındaki değeri kabul etmek bildirim değildir; sapmadır ve DUR'dur (KM-27).

### Kategoriyi kim belirler (mimari §8.1)

Kategoriyi kararı açan rol yazar. Kural tabanlı bir sınıflayıcı da çalışır; hangisi daha sıkıysa o geçerlidir. Sınıflayıcı şunlara bakar:

- karar bir ana ölçüyü değiştiriyor mu;
- bir malzeme ya da üretim profilini değiştiriyor mu;
- maliyet hedefine dokunuyor mu;
- bir standart maddesinin kabul ölçütünü gevşetiyor mu;
- bir kural kataloğu sınırının dışında kalan değeri kabul ediyor mu (sapma);
- istek listesini değiştiriyor mu.

**Ana ölçü:** istek ölçütünde geçen, dış arayüze giren ya da baş mühendisin işaretlediği parametre. Ana ölçü işaretini ekip koyamaz ve kaldıramaz; değişiklik onay ister (KM-19).

**UYARI'yı işi yapan kabul edemez.** Bir kural sınırının dışında kalan değeri kabul etmek standarttan sapma kategorisinde DUR'dur (KM-27).

### Geçici kararın yaşamı (mimari §8.1)

1. Karar görseli ve gerekçesiyle akışa bir satır olarak düşer.
2. En az bir alternatif kayda geçer. Önceki durum da alternatif sayılır.
3. Modeli ya da bağımlı parametreleri değiştiren karar ayrı bir karar dalında ilerler (`<code>/decision/K-<no>-<option>`); bağımlı işler işaretlenir. Diğerleri çalışma dalında kayda geçer (G-21).
4. Baş mühendis bir sonraki kapıya kadar itiraz edebilir: akış satırından ya da karttan.
5. İtiraz gelirse ekip ya alternatife döner ya da gerekçeyle sürdürmeyi önerir. Dönüşte bağımlı işler bağımlılık kaydından listelenir. Sürdürmenin kendisi baş mühendis onayı ister.
6. İtiraz gelmezse karar kapı geçişiyle "kapıda kabul" olur. Kapı kartı bu kararları listeler ve kapıyı onaylamanın onları da onaylamak olduğunu açıkça yazar.
7. **Açık dallı geçici karar sınırı 5'tir** (T-06). Yalnız ayrı dalda ilerleyen kararlar sayılır. Sınır doluysa yeni dallı karar açılmaz; ekip bağımsız işe geçer. Dalsız geçici kararlar sınırı tüketmez (G-21).
8. Her seçenek değiştirdiği bütün değerleri açıkça taşır; seçilen seçeneğin ölçüsü öbür seçeneğin hesabına sızmaz (E-17). Seçeneklerin model tanımı kayıtta da durur (E-15).
9. Kapanmış bir karar onaylandığı sürümle değerlendirilir; bugünkü ölçülerle yeniden hesaplanmaz (E-21).

### Ölçüm ve eşik ayarı (mimari §8.2)

Her aşama sonunda şunlar hesaplanır: baş mühendise giden DUR soruları, açılan geçici kararlar, itiraz edilip geri alınan geçici kararlar, kategori başına geri dönüş oranı, DUR kartının cevap süresi.

Bir kategoride son 10 geçici kararın %20'sinden fazlası geri dönmüşse sistem o kategoriyi DUR listesine almayı **önerir** (kart) (T-06). Ayarı baş mühendis değiştirir; sistem kendi kendine ne gevşer ne sıkılaşır. Sekiz kesin kategori hiçbir zaman listeden çıkmaz.

### Soru tetikleyicileri

Neyin sorulacağını ekibin kanaati değil, aşağıdaki kurallar belirler. Her tetikleyici bir kart açar:

- kaynağı `assumption` (varsayım) olan değer: kritikse tek başına kart açar. Kritik demek bir geçmeye giriyor, güvenliği ya da maliyet hedefini etkiliyor demektir. Kritik olmayan varsayımlar çalışma başına tek bir "varsayım listesi" kartında (V-01) toplanır ve toplu onaylanır (Ö-11);
- G1'de kavram taslağının geometri değerleri tek tek sorulmaz; varsayım listesinde "kavram taslağı" diye tek satır görünür. Bu ölçülerin onayı G2'dedir (E-16);
- her geçme, profil kalibre edilene kadar. Kalibre profilde standart görevle sınır içinde kalan geçme kart açmaz; listede "standart" görünür (Ö-01);
- kritik olarak işaretli her değer: güvenlik, maliyet ya da parçalar arası arayüz (G-22);
- bir kurala ya da standarda uymayan her durum (sapma; DUR);
- belirsizliği tolerans bandının dörtte birini aşan her kritik ölçü; kritik ölçüde yalnız biçim için geçerli bir aletle alınmış ölçü (UNCERT-01);
- kalibre edilmemiş (geçici) profil değeriyle kurulan her geçme;
- montaj esnemesi, geçmeli kilit, takım erişimi;
- güvenlik ya da standart gereksinimine dokunan her karar;
- maliyet hedefini aşan her seçim (DUR: maliyet etkisi);
- kontrollerin açtığı kartlar: keskin iç köşe (KOSE-01), hesap tutarsızlığı, kötü ya da güvenilmez sonuç, dayanağı değişen karar, geçerlilik alanı tanımsız hesap (bölüm 9–10);
- ekibin kendi "emin değilim" bildirimi. Bu ek bir tetikleyicidir; sistem buna dayanmaz.

**Acil olmayan sorular aşama sonunda toplu gelir.** Aciliyeti "aşama sonu" olan sorular `mekanik stage finish` sırasında tek bir "aşama sonu soru paketi" kartında toplanır (mimari §8.1).

### Kart

**Kart standardı** (Ö-09, Ö-10, Ö-13, Ö-27):

- Kart, işi izlemeyen bir mühendis için yazılır.
- En üstte "Bu nedir, neden sana soruluyor?" kutusu bulunur.
- Ardından ekibin önerisi ve gerekçesi gelir.
- "Onaylarsan", "reddedersen" ve "kayda geçer" ayrı kutulardadır.
- Görseli olmayan ya da metni eksik kart açılamaz (CARD-01). Görsel modelden üretilir ve türe göre değişir:
  - parametre ve varsayım: ölçü vurgulu parça görünüşü;
  - geçme: ölçülü kesit;
  - karar: seçeneklerin çizimleri yan yana, tek kartta;
  - baskı: tabla yerleşimi, baskı yönü, süre ve filament;
  - kapı: aşama özeti ve son model.
- Kartta türüne göre en çok 4 görsel, akış satırında 1 küçük görsel bulunur (T-02; mimari §9.2).
- Bir kararın bütün seçenekleri tek kartta sunulur. Baş mühendis birini seçer ya da hepsini reddeder. Seçenek başına kart açılmaz (Ö-13).
- Karar kartında "isteklere etkisi" zorunlu satırdır: kararın istek listesindeki hedeflere etkisi (Ö-27, DECISION-02).
- Karar, dayandığı hesapları onay anındaki sonuç özetiyle kaydeder. Sonuçlar değişirse ya da yerine daha doğru bir hesap gelirse "dayanağı değişti" kartı açılır (Ö-24, DECISION-01).
- Ölçülmemiş gözlem tek başına tasarım değişikliği gerekçesi olmaz. Böyle bir gözleme dayanan karar kartında "ölçümsüz gözleme dayanıyor" uyarısı bulunur (Ö-25, B6).
- Numaralar çalışma içinde türe göre sıralıdır; kullanılmış numara tekrar verilmez (mimari §4.3).

**Kartın içeriği:** karar, değer, kaynak, gerekçe, alternatifler, bağımlı işler, kontrol sonucu, görsel. Geçmelerde görsel ölçülü kesittir.

### Baş mühendisin seçenekleri

- **Onay** ya da **ret.** Ret hâlinde etkilenen işlerin listesi kendiliğinden çıkar.
- **İtiraz.** Geçici karara, bir sonraki kapıya kadar (mimari §8.1).
- **Yorum.** Ekip yanıtlamak zorundadır; yanıtlanmamış yorum kartı açık tutar. Kart kapanmadan iş bitmiş sayılmaz (E-11). Ekip yanıtı `mekanik reply` ile yazar.
- **Müdahale.** Değeri baş mühendis kendisi değiştirir. Değer `decision` kaynağıyla ve kararı verenin baş mühendis olduğu yazılarak kayda girer; model yeniden üretilir.
- **Geri alma.** Baş mühendis kendi onayını ya da retini geri alabilir. Kayıt silinmez; bir geri alma kaydı eklenir. Kapı ve baskı onayı geri alınmaz, çünkü etiket konmuştur; onların geri dönüşü yeni bir karardır (Ö-15).

### Onay kuralları

- **Onayı yalnız baş mühendis verir.** Onay panelden (teyit penceresiyle) ya da terminalde `mekanik approve` ile verilir. Komut gerçek bir terminal (TTY) ister ve ajana yasaktır (mimari §4.6). Panel gelene kadar (Faz 2) onay terminalden verilir (mimari §17).
- **Onay imzalıdır** (T-17 b; APPROVAL-02; KM-04). Her onay baş mühendisin imza anahtarıyla imzalanır. Anahtar `ssh-add -c` ile eklenir: her imzada masaüstünde bir onay penceresi çıkar ve baş mühendis kullanım başına onaylar. İmzasız ya da başka anahtarla imzalı onay geçersizdir; kapı ve baskı geçmez.
- Panel her imza isteğinde neyin imzalandığını gösterir. Panel eylemi olmadan çıkan bir imza penceresi ajan girişimidir; baş mühendis reddeder (mimari §4.6).
- **DUR kartlarında tek tıkla onay yoktur.** Önce sonucu söyleyen bir teyit penceresi çıkar (ör. "K-01'de c seçeneğini onaylıyorsun, model buna göre değişecek"). Onay ancak pencerede yeniden onaylanınca yazılır (Ö-14).
- Onay ve değer girişi yalnız ajanın kaydedilmemiş değişikliği yokken ve ekranda görülen sürüm son sürümken geçerlidir (Ö-07).
- Kart dizisinde ve karar geçmişinde onay, ret ve geri alma olaylarını baş mühendisten başka rol yazamaz (KM-12).
- Kötü ya da güvenilmez sonuçlu bir hesabı listeleyen kartı baş mühendis gerekçe yazmadan onaylayamaz (Ö-23).

**Kayda geçenler:** kim, ne zaman, hangi sürüm, onaylanan değerlerin özeti ve imza. *Özet (hash)*, onaylanan değerlerden hesaplanan parmak izidir. Değer sonradan değişirse onay kendiliğinden düşer ve kart yeniden açılır.

## 8. Hiyerarşi, adlandırma, sürüm ve dallar

Her iş üç seviyededir: **Kurum → Proje → Çalışma**. Bir kuruma bağlı olmayan iş **Bağımsız** altında açılır. Yeni çalışma `mekanik work new` ile açılır.

| Seviye | Nedir | Örnek | Kod | Ne zaman biter |
| --- | --- | --- | --- | --- |
| Kurum | İşin sahibi | Örnek kurum · Bağımsız | `ORN` · `IND` | Bitmez |
| Proje | Ürün çıkaracak iş; ürün, birleşen çalışmalardan serbest bırakmayla çıkar | Braket | `ORN-BRK` | Ürün çıkışıyla (G5) |
| Çalışma | Projenin bir iş paketi; amacı ve "bitti" ölçütü açılışta yazılır; kendi G0–G5 aşamalarından geçer | Numune, menteşe tasarımı | `ORN-BRK-01` | Bitti ölçütü karşılanınca. Sonucu ya projeye birleşir ya da öğrenme olarak kapanır |

Örnekler kurgusaldır; gerçek kurum ve çalışma kodları atölye ayarında ve kurum reposunda durur (mimari §16).

**Kod kuralları:** kurum ve proje kodu üç büyük harftir, Türkçe karakter içermez. Çalışma numarası proje içinde sıralı ve iki hanelidir; bir numara hiç tekrar kullanılmaz. Bütün diğer adlar çalışma kodundan türer. Dal ve etiket adları İngilizcedir (T-15):

| Ne | Biçim | Örnek |
| --- | --- | --- |
| Ana hat | `<code>/main` | `ORN-BRK-01/main` |
| Çalışma dalı | `<code>/work/<topic>` | `ORN-BRK-01/work/hinge` |
| Karar dalı | `<code>/decision/K-<no>-<option>` | `ORN-BRK-01/decision/K-07-a` |
| Kapı etiketi | `<code>-G<n>` | `ORN-BRK-01-G1` |
| Baskı ya da üretim etiketi | `<code>-release-<no>` | `ORN-BRK-01-release-01` |
| Kart | `<code>:<tür>-<no>` | `ORN-BRK-01:G-01` (geçme), `:E-01` (esneme), `:S-03` (soru), `:K-07` (karar), `:V-01` (varsayım listesi), `:O-G2` (kapı), `:B-01` (baskı) |
| Sürüm | Geliştirmede v0.x; ürün çıkınca Rev A, B | `v0.4`, `Rev A` |
| Hata kaydı | Kurum genelinde sıralı | `H-001` |
| Ürün kodu | Kurumun mevcut kod sistemi; G5'te verilir | — |

*Dal (branch)*, işin ana hattan ayrı ilerleyen kopyasıdır. *Etiket (tag)*, belirli bir sürüme konan kalıcı addır.

**Paralel çalışma:** aynı anda en çok 3 aktif çalışma yürür. Her biri kendi klasöründe ve kendi ajan oturumunda çalışır; klasör, reponun ayrı bir çalışma kopyasıdır (git worktree). Aynı çalışmada aynı anda iki ajan oturumu yazamaz; ikinci oturum salt okunur çalışır (mimari §5.1). Çalışmanın durumu repoda yaşar; oturum kapanınca hiçbir şey kaybolmaz. Ekip çalışmayı `mekanik work open` ile açar, `mekanik work close` ile kapatır, `mekanik work archive` ile arşivler.

**Ürün çıkışı:** projeye birleşen çalışmaların sonucu G5'te dondurulur, Rev A etiketi ve ürün kodu alır, proje tamamlanmış sayılır.

Ana hat yalnız incelenmiş işi taşır; ayrı dal isteyen geçici kararlar karar dallarında yaşar (G-21). Böylece reddedilen bir karar, onun üstüne kurulmuş işi silmeden geri alınır. Dayanak: konfigürasyon yönetimi (ISO 10007).

| Öğe | Adlandırma | Kural |
| --- | --- | --- |
| Ana hat | `<code>/main` | İncelenmiş ve onaylanmış durum. Ekip doğrudan buraya yazmaz; giriş baş mühendis onayıyla olur (mimari §4.10) |
| Çalışma dalı | `<code>/work/<topic>` | Ekip günlük çalışmayı buraya yazar |
| Karar dalı | `<code>/decision/K-<no>-<option>` | Modeli ya da bağımlı parametreleri değiştiren geçici kararın her alternatifi ayrı daldadır. Reddedilen dal bırakılır, alternatif dal devreye girer (G-21) |
| Kapı etiketi | `<code>-G2` | Her kapı geçişinde baş mühendis onayıyla konur |
| Baskı/üretim etiketi | `<code>-release-<no>` | Basılan ya da üretilen her parça etiketlidir; hangi parçanın hangi koddan çıktığı bilinir (Ö-05) |

- **Bağımlılık kaydı:** her karar, ona dayanan parametreleri ve parçaları listeler.
- **Birleştirme:** dal ana hatta baş mühendis incelemesinden sonra girer. İnceleme kaydı birleştirme isteğidir (pull request).
- **Geri dönüş:** herhangi bir etikete dönmek tek komuttur. Basılmış her parça kendi etiketinden yeniden üretilebilir.
- **Eski adlar:** eski Türkçe dal ve etiket adları (`/ana`, `/is/`, `/karar/`, `-baski-`) yeni dallarda kullanılmaz. Taşınan çalışmaların eski etiketleri geçmiş kaydı olarak kalır (T-15).

**Eski çalışmaların taşınması** (mimari §14):

- Taşıma yalnız baş mühendis eski bir çalışmayı v1'de sürdürmek isterse yapılır (G-23, T-13).
- Taşıma ayrı bir dalda yapılır (`<code>/work/v1-migration`); eski dallara dokunulmaz (G-14). Komut `mekanik migrate`'tir.
- Eskide karşılığı olmayan zorunlu alanlara değer uydurulmaz. Eksikler listelenir ve çalışma bir DUR kartıyla açılır (KM-37).
- Her taşımanın raporu baş mühendise DUR kartıyla gider.

## 9. Ölçü, kural ve profiller

Her sayı ve her kural nereden geldiğini yanında taşır. Üretim ve ölçüm yöntemine özgü değerler profillerde durur.

**Ölçü kaynağı etiketleri** (mimari §2.3):

| Etiket | Anlamı | Belirsizlik | Kart açar mı? |
| --- | --- | --- | --- |
| `measured:<alet>` | Bir ölçme aletiyle ölçüldü: kumpas, mastar, tarayıcı … Alet atölye ayarında tanımlıdır | Alet kaydından | Kritik ölçüde 1/4 kuralını geçmezse ya da alet kritik ölçü için geçerli değilse evet (UNCERT-01) |
| `standard:<no ve madde>` | Bir standarttan (ISO 273, ISO 286 vb.) | — | Hayır |
| `regulation:<belge ve madde>` | Mevzuattan (mimari §2.3) | — | Hayır |
| `customer:<şartname ve madde>` | Müşteri şartnamesinden (mimari §2.3) | — | Hayır |
| `manufacturer:<belge>` | Üretici belgesinden (ör. yazıcı tablası ölçüsü) (Ö-12) | — | Hayır. Varsayım listesinde gri, bilgi olarak görünür |
| `literature:<atıf>` | Okunmuş bir yayından (Ö-28) | — | Hayır. Okunmamış ya da yalnız özeti okunmuş kaynak sayı vermez, nitel not olur |
| `decision` | Bir kararla verildi; kararı veren rol yazılır | — | Baş mühendisin kararıysa hayır. Başka rolün kararı bölüm 7'deki geçici karar kuralına bağlıdır |
| `derived` | Başka değerlerden formülle; formül yazılır | Kaynaklarından yayılır | Hayır |
| `assumption` | Dayanağı yok | — | Kritikse kart; değilse varsayım listesi (Ö-11) |

**Sayı kuralları:**

- Her değer değer + birim + kaynak olarak yazılır. Kayıt kaynaksız değeri reddeder.
- Montaj esnemesi gibi parametre olmayan sayılar da kaynak etiketi taşır (Ö-04).
- Boyutsuz büyüklükler de birimini taşır (`oran`) (Ö-06).
- Hesapta kullanılan sabit varsayım olamaz; yalnız `standard`, `manufacturer`, `literature` ya da `decision` kaynağı alır (mimari §4.5).
- **Kodda da kaynaksız sayı yok.** Model ve hesap kodundaki sayısal sabitler parametre kaydından ya da kaynaklı sabitten gelir. İzinli matematiksel sabitler 0, 1, 2, 0,5, 90, 180 ve 360'tır. Listenin dışındaki sabit Keşif ve Geliştirme'de UYARI, serbest bırakmada ENGEL'dir (SOURCE-02; G-17; mimari §10.1, T-02).
- Kontrol eşikleri kodda değil, kural kataloğunda ya da profilde durur ve kaynak etiketi taşır (mimari §4.7).

**Geçme kaydı.** Her geçme tek bir nominal ölçü ve profilden gelen bir boşlukla tanımlanır; iki parça da aynı kayıttan üretilir. Kayıttaki alanlar: no, parçalar, görev (ortalama, dönme, kayma, sıkı, vida geçişi, dayanma), nominal ve kaynağı, boşluk sınırı ve kaynağı, profil, durum.

**Kural kataloğu.** Her satırda kural, sınır ve dayanak (standart maddesi, literatür ya da hata kaydı numarası) bulunur. Dayanağı olmayan kural kataloğa girmez. Her kontrol sonucunun kural kimliği katalogda bulunur; her katalog kuralının da bir kontrolü vardır (mimari §4.7). Kural kimlikleri İngilizcedir (kesin karar 1).

**Yeni kural KOSE-01: iç köşe yarıçapı** (Ö-16, E-27). Yük taşıyan duvarların birbirine ya da levhaya birleştiği iç köşelerde dolgu yarıçapı, birleşen ince duvarın kalınlığından küçük olmaz. Keskin iç köşe ENGEL değil UYARI'dır ve kart açar. Dayanak: Pilkey ve Pilkey, *Peterson's Stress Concentration Factors* (iç köşede gerilme yığılması) ve kayıtlı bir kırılma deneyimi. Sınır değeri profilde durur; kalibrasyon ve kırılma deneyiyle düzeltilir (bkz. açık noktalar).

**Kural katmanları.** Ortak ilkeler, üretim yöntemi profili ve ürüne özel kural üst üste biner. Ürün kuralı profili yalnız yazılı gerekçe ve onayla ezer. Profiller sürümlüdür; çalışma kullandığı sürümü sabitler.

**Üretim profilleri.** Profil türlerini alan paketleri getirir. Makine profilleri atölye ayarında durur ve değerleri kaynaklıdır. Yeni bir makinenin değerleri `assumption` ile başlar ve kalibrasyona kadar geçicidir (mimari §13.2).

| Profil | İçindekiler |
| --- | --- |
| FDM (makine + malzeme + baskı yönü) | Görev tipine göre boşluk tablosu, model düzeltme payı, en ince et, yazıcı hacmi (tabla x/y/z) ve nozul (E-01), destek kuralları, iç köşe yarıçapı sınırı (KOSE-01). Kalibrasyon baskısıyla doldurulur |
| Talaşlı imalat | ISO 286 geçmeleri, ISO 2768 genel toleranslar, takım erişimi, iç köşe yarıçapı |
| Enjeksiyon | Çekme payı, çıkma açısı, düzgün et, kaburga oranı. Değerler literatürden ve kalıpçıdan |
| Sac | Büküm yarıçapı, K-faktörü, delik–kenar mesafesi |

FDM'de modeldeki ölçü ile basılan ölçü farklıdır. Kayıt parçada istenen boşluğu tutar, profil de model düzeltme payını verir.

**Ölçme aleti kayıtları.** Her ölçme aletinin belirsizliği, dayanağı, kalibrasyonu ve geçerliliği (kritik ölçü ya da yalnız biçim) atölye ayarındaki kaydında durur (mimari §3.3).

- Kural: kritik bir geçmede ölçme belirsizliği tolerans bandının en fazla dörtte biridir.
- Kritik ölçüde yalnız biçim için geçerli bir aletle alınan ölçü ENGEL'dir (UNCERT-01).
- Tarayıcının belirsizliği iki yerden alınır: VDI/VDE 2634'e göre verilmiş katalog değeri, ve ölçüsü bilinen bir parçanın taranmasıyla yapılan kendi doğrulamamız.
- Telefon LiDAR'ı için örnek ayar cm sınıfında bir alt sınırla gelir. Referans parçayla doğrulanana kadar bu değer varsayımdır (G-15).
- **Uygunluk kararı** (mimari §10.7; JCGM 106:2012). Sınıra yakın ölçümde karar kuralı yazılır: basit kabul ya da korumalı kabul. Korumalı kabulde kabul sınırı tolerans içine çekilir; koruma bandı w = r·U'dur ve r `decision` kaynaklıdır. Sınıra yakın ölçüm "uygun" değil "belirsiz" sonucunu verir.

### Hesap, analiz ve deney

**Hesaplar.**

- Hesap yalnız kayıttaki kaynaklı parametreleri okur. Kaynaksız ya da değersiz girdi hata verir (mimari §4.5).
- Hesap, büyüklüğü doğruluk düzeyiyle bildirir: 1 elle, 2 sayısal, 3 ölçüm (Ö-22).
- **Tutarlılık** (Ö-22, B3, CALC-01). Aynı büyüklük iki hesapta %10'dan fazla farklıysa UYARI kartı açılır. Düşük doğruluklu hesap "yerini aldı" diye işaretlenir; kanıt olarak yüksek doğruluklu olan kullanılır (E-32). Sınır büyüklük başına katalogda kaynaklı olarak değiştirilebilir (mimari §10.2; bkz. açık noktalar).
- **Kötü ya da güvenilmez sonuç** (Ö-23, B4, CALC-02). Sonucu kötü ya da güvenilmez olan hesap baskı ve kapı kartında listelenir ve UYARI sayılır. Baş mühendis gerekçe yazmadan onaylayamaz.
- **Kritik hesap iki bağımsız yöntem ister** (Ö-18, E-30; CALC-03; mimari §10.2).
  - Kritik hesap: bir zorunlu isteğin kanıtı, güvenliği etkileyen, bir DUR kararının dayanağı ya da bir baskı/üretim isteğinin dayanağı olan hesaptır. İşareti kararı açan rol koyar; kanıt ve dayanak bağlarından da kendiliğinden çıkar. Hangisi daha sıkıysa o geçerlidir.
  - Bağımsızlık: ikinci yöntem farklı bir doğruluk düzeyinde olmalı ya da farklı formül yapısıyla, ortak ara sonuç kullanmadan çalışmalıdır. Aynı formülün yeniden yazılması bağımsız sayılmaz. Aynı yapıda ve aynı türetilmiş girdiyle çalışan iki şablon da bağımsız sayılmaz (KM-11).
  - İkinci yöntem yoksa hesap kritik kanıt sayılmaz ve kart açık kalır. İkinci yöntem bir ölçüm de olabilir.
  - İki yöntem uyuşmazlık sınırını aşarsa ENGEL'dir: hesaba dayanan karar onaylanamaz, kapı ve baskı isteği açılmaz.

**Geçerlilik alanı** (G-18; mimari §10.3; NASA-STD-7009B). Her analiz aracının bir kaydı vardır: amaçlanan kullanım, sınırlar, doğrulama alanı, geçerleme alanı, varsayımlar, bilinen kusurlar, sürüm. Her hesapta girdiler bu alanlarla karşılaştırılır:

| Bölge | Kanıt olabilir mi |
| --- | --- |
| Geçerleme alanında | Evet |
| Yalnız doğrulama alanında | Evet, "doğrulanmış, geçerlenmemiş" uyarısıyla; kartta görünür |
| Yalnız sınırlar içinde (dış değerleme) | Yalnız baş mühendisin gerekçeli onayıyla |
| Sınır dışında | Hayır: sonuç güvenilmezdir (CALC-04, ENGEL) |
| Alan tanımsız | Kart açar: "geçerlilik alanı tanımsız" |

- Her sonuçta belirsizlik beyanı zorunludur: sayısal, nitel ya da açıkça "belirsizlik tahmini yok". Boş bırakmak hatadır (mimari §10.3).
- Tek bir güvenilirlik puanı üretilmez; güvenilirlik faktörleri ayrı ayrı gösterilir (mimari §10.4, §10.10).
- **Uyarlama.** NASA-STD-7009B'nin uygulanmayan her maddesi gerekçesiyle uyarlama kaydına yazılır ve baş mühendis onaylar. YZ kalite incelemesi teknik inceleme faktöründe en çok seviye 2 sayılır. Kırmızı kutu (en kritik) hesaplarda dış inceleme isteğe bağlı bir karttır (T-12).

**Analiz planı: ilk prototipten önce, sıkı kontrolle** (Ö-19). A ve B sınıfında G2'de bir analiz planı yazılır. Her analiz için şunlar bulunur: sorusu; bağlandığı risk, gözlem, gereksinim ya da karar (boş olamaz); yöntemi; üst yönteme geçme koşulu; maliyeti. Düşünülüp yapılmayan analizler de gerekçesiyle yazılır. Kurallar:

1. En ucuz yöntemle başlanır.
2. Üst yönteme (FEA, CFD) yalnız gerekçeyle geçilir: basit yöntem bir gözlemi açıklamıyor ya da güvenlik payı eşiğin altında.
3. Her yöntem en az bir gerçek gözlemle ya da bağımsız bir yöntemle doğrulanır (Ö-18).
4. Girdisi değişmeyen analiz yeniden çalışmaz (E-37).

G2 kapısında plandaki analizler yapılmış olmalı ya da baş mühendis onlardan vazgeçmiş olmalıdır.

**Deney.**

- Her deneyin kaydı vardır: yöntem, ölçümler, ortam, ortalama ± sapma (E-03).
- Numune, üretildiği baskı/üretim etiketiyle bağlanır. Teste girmeden önce numunenin kabul ölçümü yapılır: kütle ve ağırlık merkezi (E-35, E-41; mimari §4.5).
- Geçersiz deneme nedeniyle kayda geçer.
- Ölçülmemiş gözlem tek başına tasarım değişikliği gerekçesi olmaz (Ö-25).

**Kanıt** (mimari §4.5, §10.6). Kanıt, bir isteği ya da standart maddesini bir kayda bağlar: hesap, deney, kontrol, ölçüm, belge, model görünüşü, kalite incelemesi. Bağ, kaydın içerik özetiyle kurulur; özet değişirse kanıt bayatlar. İsteğin durumu kanıttan türetilir; elle yazılmaz.

## 10. Kontroller ve serbest bırakma koşulu

Kontroller modelden bağımsız betiklerdir. Sonuçları ENGEL, UYARI ya da GEÇTİ'dir ve her sonuç bir kural kimliği taşır. Ekip kontrolleri `mekanik check` ile çalıştırır; bu komut kayıtları değiştirmez (E-40). Kalan bir kontrol işi durdurmaz; ama sürüm serbest bırakılamaz. Kalan kontrol panelde ve akışta kırmızı görünür, baş mühendise bildirim gider.

| Kontrol | Neye bakar | Keşif ve Geliştirme | Serbest bırakma | Dayanak |
| --- | --- | --- | --- | --- |
| Kaynaksız ölçü (SOURCE-01) | Etiketsiz değer var mı | ENGEL | ENGEL | — |
| Kodda kaynaksız sayı (SOURCE-02) | Model ve hesap kodunda izin listesi dışı sabit var mı | UYARI | ENGEL | G-17 |
| Bağımsız sayılı geçme | Geçmenin iki ölçüsü tek kayıttan değil, iki ayrı sayıdan mı geliyor | UYARI | ENGEL | Ö-02 |
| Katı model (SOLID-01) | Geçerli ve kapalı mı | UYARI | ENGEL | — |
| Girişim (INTERF-01) | Parçalar birbirine giriyor mu | UYARI | ENGEL | — |
| Geçme boşluğu (FIT-01) | Her geçme sınırlar içinde mi | UYARI | ENGEL | — |
| Kayıtsız geçme (UNREG-01) | Eş eksenli, birbirine yakın yüzeyler kayıtta mı | UYARI | ENGEL | — |
| Ölçme belirsizliği (UNCERT-01) | Kritik ölçü 1/4 kuralını geçiyor mu; alet kritik ölçü için geçerli mi | UYARI (alet geçersizse ENGEL) | ENGEL | mimari §4.7 |
| Üretilebilirlik | Profil kuralları: et, çıkma açısı, yazıcı hacmi, destek | UYARI | ENGEL | — |
| İç köşe (KOSE-01) | Yük taşıyan iç köşede dolgu yarıçapı | UYARI (kart) | UYARI (kart) | Ö-16 |
| Montaj (ASSY-01) | Esneme, takım erişimi | UYARI | ENGEL | — |
| Hesap tutarlılığı (CALC-01) | Aynı büyüklük iki hesapta sınırdan fazla farklı mı | UYARI (kart) | UYARI (kart) | Ö-22 |
| Hesap sonucu (CALC-02) | Kötü ya da güvenilmez sonuç var mı | UYARI (kart; onay gerekçe ister) | UYARI (kart; onay gerekçe ister) | Ö-23 |
| Kritik hesap (CALC-03) | İkinci bağımsız yöntem var ve uyuşuyor mu | ENGEL | ENGEL | Ö-18 |
| Geçerlilik alanı (CALC-04) | Kanıt alan dışı sonuca mı dayanıyor | ENGEL | ENGEL | G-18 |
| Karar dayanağı (DECISION-01) | Kararın dayandığı hesap değişti mi | Kart | Kart | Ö-24 |
| İsteklere etkisi (DECISION-02) | Karar kartında "isteklere etkisi" dolu mu | Kart açılamaz | Kart açılamaz | Ö-27 |
| Kart standardı (CARD-01) | Görsel ve metin tam mı | Kart açılamaz | Kart açılamaz | Ö-10 |
| Kalite (QUALITY-01) | Açık YÜKSEK kalite bulgusu var mı | Kapı ve baskı kartı açılmaz | Kapı ve baskı kartı açılmaz | Ö-20 |
| İstek durumu (REQ-01) | Zorunlu isteklerin hepsi "karşılandı" mı | — | G4 ve G5'te ENGEL | Ö-21 |
| Standart haritası (STDMAP-01) | Harita var mı; tiksiz zorunlu madde kaldı mı | G0 kapısında ENGEL | G5'te ENGEL | mimari §10.8 |
| Onay imzası (APPROVAL-02) | Onaylar baş mühendisin anahtarıyla imzalı mı | ENGEL | ENGEL | T-17, KM-04 |
| Onay durumu (APPROVAL-01) | Açık DUR, incelenmemiş karar, bayat onay, kapanmamış kart, reddedilip düzeltilmemiş kart var mı | — | ENGEL | Ö-03 |

Kaynaksız ölçü her aşamada ENGEL'dir, çünkü yapısal bir kuraldır: etiketsiz bir değer model üretmez.

Yeni kontroller (SOURCE-02, CALC-03, CALC-04, REQ-01'in G4/G5 şartı, STDMAP-01) Faz 2'de gelir. Faz 1'de eskide olmayan sıkılaştırmalar ENGEL değil UYARI'dır: kritik hesapta ikinci yöntem, geçerlilik bölgesi, belirsizlik beyanı, ölçümsüz gözlem (mimari §17; bkz. açık noktalar).

**Serbest bırakma koşulu (G5).** Dört şart birlikte aranır:

1. Sıfır ENGEL.
2. Bütün kararlar incelenmiş: DUR kararları onaylı; geçici kararlar kapıda kabul edilmiş ya da itirazları çözülmüş (KM-02; mimari §8.1).
3. Onay özetleri güncel ve imzalar geçerli (APPROVAL-02).
4. Baş mühendis onayı verilmiş.

Bu dört şartın içinde ayrıca şunlar aranır: zorunlu isteklerin hepsi "karşılandı" (Ö-21, REQ-01); standart haritasında tiksiz zorunlu madde yok (mimari §10.8).

Bu koşul sağlanmadan hiçbir sürüm "üretime hazır" ya da "basmaya hazır" sürüm etiketi alamaz. Prototip baskısının `<code>-release-<no>` etiketi bundan ayrıdır: izlenebilirlik içindir, yalnız ENGEL yokken ve onaylı baskı kartıyla konur (Ö-05, Ö-08).

**Bağımsız inceleme** (Ö-20, B1; mimari §4.8, §10.5). Kalite mühendisi her kapı isteğinde, her baskı/üretim isteğinde ve anlama özeti onayından önce çalışır; risk sınıfı bunu değiştirmez.

- İnceleme o sürümün donmuş bir kopyasında, salt okunur araçlarla yapılır.
- Kalite mühendisine sohbet özeti verilmez. Yalnız ilkeler listesi, kabul ölçütleri ve dosya yolları verilir.
- Bulgu biçimi: `[YÜKSEK|ORTA|DÜŞÜK] yer — sorun — ilke — kanıt`.
- Açık YÜKSEK bulgu varken kapı ve baskı kartı açılmaz (QUALITY-01). Bulgu gerekçeyle kapatılır. Ekip bir YÜKSEK bulguyu kapatsa bile kapı kartında "kapatılan YÜKSEK bulgular" listesinde görünür.
- Girdiler değişmedikçe inceleme yeniden çalışmaz.
- Bulgu kapanırken "regresyon vakası gerekir mi?" sorusu zorunludur: evetse vakanın yeri, hayırsa gerekçe yazılır (mimari §10.7).
- Ekip incelemeyi `mekanik review` ile başlatır, bulguyu `mekanik review close` ile kapatır.

**Regresyon.** Her kontrol değişikliğinde bilinen hata vakaları yeniden çalıştırılır (`mekanik regress`). Kontrol, kaldırması gerekenleri kaldırmalı ve doğruları geçirmelidir. Her kontrolün "hep ENGEL" ve "hep GEÇTİ" diyen sahte sürümü regresyondan geçemez (mimari §4.7). İlk vaka H-001'dir (bölüm 13).

## 11. Tasarım dosyası

Her çalışmanın tek bir tasarım dosyası vardır. Ekip yaptığını görselleriyle oraya yazar; baş mühendis istediği saat aralığını açıp okur. Dosya üç bölümdür:

1. **Son okumandan beri.** En üstte durur. Okunmamış aralığın kısa özetidir: ne yapıldı, ne karar verildi, ne kaldı, baş mühendisi neler bekliyor. Gün sonu özetinin kişiye göre süzülmüş hâlidir (mimari §9.3).
2. **Günlük.** Zaman sıralıdır, yalnız eklenir. Akışın kalıcı olaylarından üretilir (mimari §9.1). Her kayıtta şunlar bulunur:
   - saat (sistemden) ve kaydı yapan rol;
   - ne yapıldığı ve neden;
   - görsel (ölçülü kesit, render, ekran görüntüsü);
   - kontrol sonucu;
   - açılan kartlar;
   - sürüm ya da commit.
3. **Güncel durum.** İstek listesi ve isteklerin durumu, kararlar, geçmeler, risk kaydı, açık sorular, kapı durumu, standart haritası durumu.

**Akış** (mimari §9.1). Her iş adımı (`mekanik step`) akışa bir satır yazar: saat, rol, tek satır metin, küçük görsel, kart ve karar bağlantıları, kontrol özeti (ENGEL/UYARI sayısı), commit. Saati `mekanik step` yazar; ajan saat göndermez (mimari §4.13).

**Gün sonu özeti** (mimari §9.3). Ayarlı saatte ya da istenince üretilir. Dört bölümü vardır:

1. Verilen kararlar: DUR onayları, geçici kararlar (itiraz süresiyle), kapıda kabul edilenler.
2. Bekleyenler: cevap bekleyen DUR kartları, yanıt bekleyen yorumlar, aşama sonu soru paketi.
3. Riskler: açık ENGEL ve UYARI, güvenilmez ya da alan dışı hesaplar, tutarsız büyüklükler, dayanağı değişmiş kararlar, açık kalite bulguları, "kanıt bekliyor" durumundaki zorunlu istekler, doğrulanmamış standart maddeleri.
4. Ajan kullanımı.

Boş bölüm "yok" yazar.

**Yazma kuralları:**

- Kayıt, her anlamlı iş adımı bittiğinde yazılır; her komutta değil.
- Görsel kararı göstermelidir: geçme için ölçülü kesit, biçim için render. Akış satırında 1 küçük görsel, kartta türüne göre en çok 4 görsel bulunur (T-02).
- Günlük düzeltilmez. Yanlış bir kayıt, onu düzelten yeni bir kayıtla giderilir.
- Kalıcı kayda model adı değil rol yazılır (mimari §4.9).

Kayıtlar kurumun çalışma reposunda, çalışmanın kendi klasöründe durur (mimari §3.4). Panel onları okunur hâle getirir.

## 12. Panel, gözlem ve altyapı

Ekip iki pencereden izlenir (T-18):

- **Ajan penceresi:** kullanıcının Claude Code penceresi (masaüstü uygulaması, VS Code ya da terminal). Ajanla konuşma buradadır.
- **Panel:** kokpittir. Durum, kartlar, onay, dosyalar ve ajana talimat paneldedir; terminal isteğe bağlıdır (kesin karar 6). Panelde isteğe bağlı bir "Oturum" sekmesi, gerçek Claude Code oturumunu panelin içinde açar (T-18a, Faz 2).

Telefondan izleme v1'de yoktur; sonraki sürümdedir (kesin karar 5).

**Panelden yapılan işler** (mimari §5.1):

- proje ve çalışma açma;
- oturumu açma: panel, Claude Code'u çalışma klasöründe açan bağlantıyı ya da kopyalanabilir komutu verir. Oturumu kullanıcı yönetir;
- durdurma: bir durdurma bayrağı konur; eklenti, bayrak varken ajanın araçlarını modelden bağımsız olarak reddeder (KM2-9);
- ajana talimat: talimat çalışmanın gelen kutusuna yazılır ve çalışan oturuma bildirim olarak iletilir (`mekanik agent send`, Faz 2);
- kart onayı, ret, yorum, değer girişi (imzalı; bölüm 7);
- geçici karara itiraz;
- dosya ekleme ve indirme.

Panel ekibin çalışıp çalışmadığını gösterir (E-18; `mekanik agent status`). Baş mühendisin onay, ret, yorum ve değer olayları çalışan oturuma iletilir (E-14; `mekanik watch`).

**Panel ekranları** (mimari §5.2). Ortak çerçeve: üstte konum satırı ve ajan durumu; açık çalışmaların sekmeleri (en çok 3); solda Kurum → Proje → Çalışma ağacı; sağda özellikler paneli; altta durum çubuğu. Ekranlar:

- **Proje açma:** kurum, proje, iş türü, dosya bırakma, önerilen paket, verilecek kod.
- **Tanımlama:** veri analizi görselleri, soru kartları, bulgular, anlama özeti.
- **Akış:** canlı akış, geçici karar ve DUR satırları, gün sonu özeti, aşama sonu soru paketi, talimat kutusu. Sağ panelde ekip durumu.
- **Kart:** karar kartı ve kapı kartı (istek durumu tablosu); inceleme kuyruğu ve karar kaydı.
- **Model:** görüntüleyici, özellikler paneli, geçme tablosu.
- **Standart haritası:** maddeler, tür, doğrulama durumu, tik, satın alma listesi.
- **Tasarım dosyası:** son okumandan beri, günlük, güncel durum.
- **Dal haritası:** adımlar, kapı ve baskı etiketleri, açık ve reddedilen karar dalları. Sürüm seçiciyle iki sürüm karşılaştırılır.

**Görüntüleyici.** Panelin içine [three-cad-viewer](https://www.jsdelivr.com/package/npm/three-cad-viewer) gömülür (G-12): MIT lisanslı, kesit düzlemi, ölçüm aracı ve parça ağacı var. Üstüne bizim katmanımız eklenir:

- geçmeler, kontrol durumuna göre renkli işaretler olarak (yeşil geçti, kırmızı kaldı, sarı karar bekliyor; KM-02, bkz. açık noktalar);
- işarete dokununca açılan kart;
- kartın içinden müdahale.

**Altyapı:**

| Bileşen | Görevi | Not |
| --- | --- | --- |
| Ubuntu masaüstü | mekanik, araçlar, panel | Desteklenen sürümler 24.04 LTS ve 26.04 LTS (T-14) |
| Claude Code + mekanik eklentisi | Ajan oturumu | Kullanıcının kendi aboneliği; eklenti kipi (T-01). Eklenti kullanıcı kapsamında kurulur (mimari §5.4) |
| Kurumun çalışma reposu (git) | Tek doğruluk kaynağı | Kurum başına bir repo; dallar ve etiketler bölüm 8'de |
| Panel | Kokpit | Yalnız bu makineden erişilir (127.0.0.1). Uzaktan erişim isteğe bağlı bir platform eklentisiyle kurulur (ör. Tailscale); çekirdekte değildir (G-13). İnternete açık port yok |
| Araçlar | CadQuery, trimesh; isteğe bağlı: dilimleyici komut satırı (baskı süresi, destek), FreeCAD, CalculiX | Bir kez kurulur. İsteğe bağlı araçları `mekanik doctor` önerir, kurmaz (mimari §13.1). Teknik resim üretimi v1'de yoktur (mimari §19.3) |

**Kurulum ve sağlık denetimi.** Kurulum `mekanik init` sihirbazıyla yapılır. sudo gerektiren adımı mekanik yalnız yazar; kullanıcı çalıştırır (mimari §13.2). `mekanik doctor` araçları, sürümleri ve imza onay penceresini deneme imzasıyla sınar. Onay penceresi açmadan imza atabilen kurulumu kırmızı gösterir (T-17; mimari §5.4).

**İzinler ve güvence.** Gözetimsiz çalışmada ekibin serbestçe çalıştırabileceği komutlar tanımlıdır. Satın alma, silme ve dışarıya gönderme bu listede yer almaz. Eklenti, ajanın onay ve kimlik komutlarını (onay, etiket koyma, git kimliğini değiştirme) araç çalışmadan önce engeller. Bu bir kolaylık katmanıdır; asıl güvence imzadır (mimari §5.4; KM2-1).

**Kurum verisi kapısı** (mimari §5.4; KM-50). Verisinin model sağlayıcısına gitmesine izin vermeyen bir kurumun çalışmasında ajan oturumu panelden açılmaz, istem modele gönderilmez ve ajan o çalışmanın dosyalarına erişemez.

## 13. Hatalardan öğrenme

Her hata bir kayıt, bir kök neden ve kalıcı bir önlem üretir. Önlem bir kural, bir kontrol ya da bir talimattır. Yöntem 8D'dir.

**Hata kaydının alanları:** no, tarih, proje ve sürüm, ne oldu, nasıl fark edildi, kök neden (beş neden), maliyet (malzeme, saat), kalıcı önlem, regresyon vakası.

- Regresyon vakası zorunludur ve en az iki alt vaka içerir: biri kalır, biri geçer. Kapalı her hata kaydının vakası her değişiklikte çalışır (mimari §10.7).
- Kapıdan sonra bulunan her hata en geç 7 gün içinde bir regresyon vakasına dönüşür (mimari §10.11 F6; T-02).
- Hata kaydı kurumun reposunda durur; numarası kurum genelinde sıralıdır.

**H-001 — menteşe oturmadı** (sentetik vaka; Ek B §10, mimari §16)

Eski sistemin ilk hata kaydı v1'de sentetik vakaya dönüştü. Sayılar aynıdır; parça adları uydurmadır, kurum verisi taşımaz.

- **Ne oldu:** A parçasının menteşe deliği Ø17 (taramadan), B parçasının kabartısı Ø14 (kaynaksız). Çapta 3,0 mm boşluk kaldı; A her yöne 1,5 mm oynuyor. Aynı taramada ayrıca:
  - B pivot deliği Ø7 ↔ M6: 1,0 mm, gevşek;
  - toka yarığı 5,0 ↔ pim boynu 4,0 (tahmin): 1,0 mm, gevşek;
  - A kulağının her yanda 3,2 mm esnemesi raporda yazıyor, ama onaylanmadı.
- **Nasıl fark edildi:** baskıdan sonra montajda.
- **Kök nedenler:**
  1. Geçen iki ölçü birbirinden bağımsız iki sayıydı.
  2. Kaynaksız ölçü fark edilmedi.
  3. Kontroller geçmenin işlevini bilmiyordu.
  4. Baş mühendisin kritik ölçüyü görebileceği bir yer yoktu.
- **Kalıcı önlemler:** geçme kaydı (tek nominal, profilden boşluk); zorunlu kaynak etiketi; geçme boşluğu kontrolü; kayıtsız geçme taraması; montaj esnemesi için kart; ölçülü kesitli onay kartı.
- **Regresyon vakası:** kontrol şunları kaldırmalı: 3,0 mm, 1,0 mm, 1,0 mm (tahmin bayrağıyla), kaynaksız Ø14, onaysız 3,2 mm esneme, kritik geçmede tarama ölçüsü. Şunları geçirmeli: 0,5 mm'lik stop pimi, M4 cıvata için Ø4,3 geçiş deliği. Alt vakaların tam listesi mimari §16'dadır.

**Ek bulgu.** Tarama telefon LiDAR'ıyla yapılmıştı. Yayımlanmış çalışmalar bu sensörün küçük nesnelerde düşük doğruluk verdiğini gösteriyor ([Yanchuk vd.](https://geodetski-vestnik.com/arhiv/70/1/47_Yanchuk.pdf)). Ders: yalnız biçim için geçerli bir aletle alınan ölçü kritik bir geçmeye girmez (UNCERT-01; G-15).

**Dersler.** Eski sistemin kurulum ve pilot dersleri (E-01…E-41) ve v1'deki karşılıkları Ek B §11'dedir. Düzeltilmiş ya da kısmen düzeltilmiş her dersin v1'de bir test kimliği olur (mimari §10.11 F7).

## 14. Uygulama sırası ve kapanan açık konular

**Uygulama sırası** (mimari §17):

1. Bu taslağın baş mühendis tarafından incelenip onaylanması (T-05). Onaya kadar eski el kitabı (0.2) bağlayıcıdır.
2. **Faz 1 — Çekirdek:** eski davranışla eşitlik; yeni özellik yok. v1 yalnız sentetik vakalarda ve kuru taşımada kullanılır; gerçek işler eski sistemde sürer (mimari §19.1). Onay imzası (APPROVAL-02) Faz 1'dedir.
3. **Faz 2 — Panel kokpit, tanımlama, soru politikası, akış, standart haritası:** yeni kontroller, G3 → G2 dönüşü ve gerçek işlerin v1'e geçişi bu fazdadır.
4. **Faz 3 — Alan paketleri ve CAD içe alma:** kalıp paketi, 3B baskının yeni kontrolleri, KOSE-01.
5. **Faz 4 — Kurulum, belgeler, örnek proje, yayın hazırlığı.** Yayının kendisi ayrı karardır (T-10).
6. Prosedür ve talimatlar, her biri ilk kullanıldığı işte yazılır.

**Eski el kitabının açık konuları (§14) kapandı:**

- [x] Ubuntu sürümü: 24.04 LTS ve 26.04 LTS desteklenir (T-14). Baş mühendisin sürümü `mekanik doctor` çıktısından okunur.
- [x] Maliyet eşiği: kurum başına, kurulumda sorulur. Girilene kadar G0'daki 2. soru baş mühendise sorulur (T-07).
- [x] Açık geçici karar sınırı: 5; yalnız ayrı dalda ilerleyen kararlar sayılır (T-06, G-21).
- [x] Kayıt başına görsel: akış satırında 1, kartta türüne göre en çok 4 (T-02).
- [x] Süreç reposunun ve aracın adı: `mekanik` (G-01).
- [x] Yazıcı, malzeme ve tarayıcı: makine ve ölçme aleti kayıtları atölye ayarındadır. Değerler kalibrasyona kadar varsayımdır; telefon LiDAR'ı kritik geçme ölçüsü için geçerli değildir (G-15).

## 15. Kaynaklar

- [LRQA — ISO 9001:2026 yayın tarihi](https://www.lrqa.com/en/latest-news/iso-9001-publication-date-confirmed/)
- [VDI — VDI/VDE 2634 Blatt 2](https://vdi.de/en/home/vdi-standards/details/vdivde-2634-blatt-2-optical-3-d-measuring-systems-optical-systems-based-on-area-scanning)
- [three-cad-viewer (jsDelivr)](https://www.jsdelivr.com/package/npm/three-cad-viewer)
- [Yanchuk vd. — iPhone LiDAR doğruluğu](https://geodetski-vestnik.com/arhiv/70/1/47_Yanchuk.pdf)
- [NASA-STD-7009B](https://standards.nasa.gov/standard/NASA/NASA-STD-7009) · [NASA-HDBK-7009B](https://standards.nasa.gov/standard/nasa/nasa-hdbk-7009)
- [JCGM 106:2012](https://doi.org/10.59161/JCGM106-2012) (telif nedeniyle metin repoya konmaz, yalnız bağlantı verilir)
- Mimari belge: `docs/design/architecture.md`; taşıma envanteri: `docs/design/appendix-b-migration-inventory.md`

## Eski el kitabından farklar

**Genel**

- Belge v1 taslağıdır; onayla mekanik'teki işlere uygulanır. Eski sistemdeki çalışmalar 0.2 ile sürer (T-05, G-23).
- Grafik tasarım kapsamdan çıktı; "Baskı ve grafik" profili ve grafik önizleme de çıktı (T-03).
- Kurum ve kişi verisi çıktı: "ilk uygulayıcı Üstteknik", ürün örnekleri, "Mevcut işler" satırı, H-001'in gerçek parça adları. Örnek kodlar kurgusal (`ORN-BRK-01`) (Ek B §10; mimari §16).
- Kurum profilinden "onay yetkilisi" çıktı: tek onay yetkilisi baş mühendistir (kesin karar 2). Kurum profiline "verinin model sağlayıcısına gidip gidemeyeceği" eklendi (KM-50). Marka kuralları grafik işlerle birlikte çıktı (T-03; mimari §3.3).
- Bağımsız kurumun kodu `BAG` yerine `IND` (mimari §13.2; açık nokta).
- Dil kuralı eklendi: kod, komut, dal, etiket, kayıt alanı ve kural kimlikleri İngilizce; arayüz Türkçe (kesin karar 1; G-04).
- İlkelere eklendi: kodda da kaynaksız sayı yok (G-17); her hata bir regresyon vakasına dönüşür (mimari §2.2); saat sistemden (mimari §4.13); onay imzalı (T-17).
- Terimler tablosu eklendi (mimari §2.3).

**Dayanaklar ve belge yapısı**

- §2'ye eklendi: NASA-STD-7009B/HDBK-7009B (G-18, T-12), JCGM 106:2012 (mimari §10.7), Pilkey (Ö-16), ürün güvenliği mevzuatı (mimari §10.8). EN 1621-1 ürün bağı olmadan örnek oldu (Ek B §10).
- Paralı standart: önce açık karşılık aranır; satın alma kartla, DUR (T-08; mimari §10.8).
- §3: `surec/...` yolları çıktı. Katman 4 artık standart kütüphanesi ve atölye ayarıdır. Kütüphane değişikliği de DUR. Süreç profili el kitabının §5–§6'sının birebir karşılığıdır (G-07; mimari §12).

**Roller ve oturum**

- Rol tablosundan model adları çıktı; eşleme atölye ayarında, kayıtta rol yazar (mimari §4.9).
- Proje mühendisinin yetkisi "inceleme bekliyor" yerine geçici karar; DUR'u yalnız önerir (KM-02).
- Tekniker modeli değiştirmez, model notu açmaz (KM-28).
- Kalite mühendisi yalnız A sınıfı Kesinleştirme'de değil, her kapı, her baskı/üretim isteği ve anlama özetinde çalışır; eklentinin salt okunur alt ajanıdır (Ö-20, B1, G-11, T-01).
- Divan kuralı 7 eklendi: DUR kapsamındaki sistem komutu hazır komut olarak yazılır, baş mühendis çalıştırır (E-34).
- Ajan oturumu kullanıcının aboneliğiyle, eklenti kipinde; başsız kip yok; kapalı oturum kendiliğinden açılmaz (T-01, G-10, T-09).

**Risk sınıfları ve kapılar**

- Deneyle doğrulanan zorunlu istek varsa sınıftan bağımsız G4 (Ö-26, B7).
- Maliyet eşiği kurum başına, kurulumda sorulur (T-07).
- G3 → G2 dönüş yolu tanımlandı (Ö-17, E-26).
- Aşama bitirme ve kapı geçişi adımları yazıldı; kapı kartında istek durumu, kötü sonuçlar, geçici kararlar ve kalite bulguları (Ö-21, Ö-23, Ö-20; mimari §4.2).
- G1'e "seçim tek varsayıma mı dayanıyor" maddesi (E-33); G2'ye risk kaydı/DFMEA (E-31), analiz planı (Ö-19) ve kritik hesap maddeleri (Ö-18); G4/G5'e zorunlu istekler "karşılandı" (Ö-21).
- Prototip baskısı (G3 içinde, onaylı baskı kartıyla) ile üretim serbest bırakması (G5) ayrıldı; baskı/üretim isteği bütün üretim yöntemleri için genel DUR (Ö-05, Ö-08, G-09).
- G0'dan önce tanımlama ve anlama özeti; onaysız tasarım başlamaz (mimari §7.1; G-11). G0'da standart haritası (mimari §10.8).

**Kararlar, sorular ve onay**

- Dört seviyeli tablo iki karar seviyesine indi: DUR ve geçici karar. "İnceleme bekliyor" kalktı; bildir karar değil, bilgidir (KM-02, G-21).
- DUR listesi sekiz kategori oldu. Malzeme, üretim yöntemi ve ana ölçüler eskiden geçici karardı; artık DUR (kesin karar 7).
- Kategoriyi rolün yanında kural sınıflayıcısı da belirler; daha sıkı olan geçerli (mimari §8.1). Ana ölçü işaretini ekip koyamaz (KM-19). Kural sınırı dışında değeri kabul etmek DUR; UYARI'yı işi yapan kabul edemez (KM-27).
- Geçici karar: dal yalnız modeli ya da bağımlı parametreleri değiştirende; itiraz ve "kapıda kabul" yolu; sınır 5 yalnız dallı kararları sayar (G-21, T-06).
- Aşama ölçüleri ve eşik ayarı önerisi: pencere 10 karar, eşik %20 (T-06).
- Soru tetikleyicileri: kalibre profilde standart geçme kart açmaz (Ö-01); kritik olmayan varsayımlar V-01 listesinde (Ö-11); G1 kavram taslağı tek satır (E-16); kritik işaretli değerler kart açar (G-22); DUR sorusu varsayılanla geçilmez (KM-03); aşama başına en çok 5 "şimdi" sorusu ve aşama sonu paketi (T-06).
- Kart standardı: "bu nedir" kutusu, öneri, sonuç kutuları (Ö-09); görselsiz kart açılamaz (Ö-10); seçenekler tek kartta (Ö-13); isteklere etkisi zorunlu (Ö-27); dayanak özeti (Ö-24); ölçümsüz gözlem uyarısı (Ö-25).
- Kayıt başına görsel sınırı 3 yerine akış satırında 1, kartta en çok 4 (T-02).
- Karar seçenekleri değerlerini açık taşır, kapanmış karar onay sürümüyle değerlendirilir (E-15, E-17, E-21).
- Onay imzalı ve kullanım başına onaylı (`ssh-add -c`); imzasız onay geçersiz (T-17, APPROVAL-02, KM-04).
- DUR kartında teyit penceresi (Ö-14); onay yalnız kaydedilmemiş değişiklik yokken ve son sürüm görülürken (Ö-07); onay ve ret geri alınabilir, kapı ve baskı onayı geri alınamaz (Ö-15); onay olaylarını başka rol yazamaz (KM-12); kötü sonuçlu kartta gerekçe şartı (Ö-23).
- Yanıtlanmamış yorum kartı açık tutar (E-11). Baş mühendisin "itiraz" seçeneği eklendi (mimari §8.1).

**Adlandırma ve dallar**

- Dal ve etiket adları İngilizce: `<code>/main`, `<code>/work/<topic>`, `<code>/decision/K-<no>-<option>`, `<code>-release-<no>`. Eski etiketler geçmiş kaydı olarak kalır (T-15).
- Aynı çalışmada iki oturum aynı anda yazamaz (mimari §5.1).
- Taşıma kuralları eklendi: yalnız istenirse, ayrı dalda, değer uydurmadan, DUR kartıyla (G-23, G-14, KM-37).

**Ölçü, hesap ve kontroller**

- Kaynak etiketleri genelleşti: `olcu:kumpas/mastar/tarama` → `measured:<alet>`; `karar` → `decision` (kararı veren rol zorunlu); `turetilir` → `derived`; `varsayim` → `assumption` (mimari §2.3). Yeni etiketler: `manufacturer:` (Ö-12), `literature:` (Ö-28), `regulation:`, `customer:` (mimari §2.3).
- Parametre olmayan sayılar da etiketli (Ö-04); boyutsuz `oran` birimi (Ö-06).
- Yeni kural KOSE-01: iç köşe yarıçapı (Ö-16, E-27).
- Katalog–kod bağı kuralı (mimari §4.7); eşikler kodda değil (Ek B bulgu 2).
- Ölçüm profilleri atölye ayarındaki ölçme aleti kayıtlarına dönüştü; yalnız biçim için geçerli alet kritik ölçüde ENGEL (UNCERT-01); JCGM 106 karar kuralı (mimari §10.7); telefon LiDAR'ı varsayım (G-15).
- FDM profiline tabla ölçüleri ve nozul (E-01).
- Yeni "Hesap, analiz ve deney" alt bölümü: tutarlılık (Ö-22), kötü sonuç (Ö-23), kritik hesapta iki bağımsız yöntem (Ö-18, E-30, KM-11), geçerlilik alanı ve NASA uyarlaması (G-18, T-12), analiz planı (Ö-19), deney kaydı ve kabul ölçümü (E-03, E-35, E-41), kanıt.
- Kontrol tablosuna eklenen satırlar: bağımsız sayılı geçme (Ö-02), kodda kaynaksız sayı (G-17), iç köşe (Ö-16), CALC-01…04 (Ö-22, Ö-23, Ö-18, G-18), DECISION-01/02 (Ö-24, Ö-27), CARD-01 (Ö-10), QUALITY-01 (Ö-20), REQ-01 (Ö-21), STDMAP-01 (mimari §10.8), APPROVAL-02 (T-17). "Onay durumu" satırına kapanmamış ve reddedilip düzeltilmemiş kart eklendi (Ö-03). Kural kimlikleri İngilizce (kesin karar 1).
- G5 koşulunda "bütün kararlar incelenmiş" v1 seviyelerine göre tanımlandı; imza ve zorunlu istek şartları eklendi (KM-02, APPROVAL-02, Ö-21).
- Regresyona "hep ENGEL / hep GEÇTİ" sahte kontrol kuralı eklendi (mimari §4.7).

**Tasarım dosyası, panel ve altyapı**

- Tasarım dosyasına akış ve gün sonu özeti eklendi; günlük akıştan üretilir; dosya yolları el kitabından çıktı (mimari §9, §3.4).
- Remote Control ve telefondan izleme çıktı (kesin karar 5). Konuşma Claude Code penceresinde, panel kokpit; isteğe bağlı Oturum sekmesi (T-18, T-18a).
- Panel ekranları v1 listesine göre yazıldı (mimari §5.2); görüntüleyicide sarının anlamı değişti (KM-02; açık nokta).
- Tailscale çekirdekten çıktı, panel yalnız 127.0.0.1 (G-13). "Bulut oturumu (yedek)" satırı çıktı (açık nokta). FreeCAD isteğe bağlı araç oldu; teknik resim üretimi v1'de yok (mimari §13.1, §19.3; açık nokta).
- Onay ve kimlik komutlarının araç öncesi engellenmesi, `mekanik doctor` imza sınaması ve kurum verisi kapısı eklendi (T-17, KM2-1, KM-50).

**Hatalar ve uygulama sırası**

- Regresyon vakası zorunlu, en az iki alt vaka; kapıdan sonra bulunan hata 7 gün içinde vaka olur (mimari §10.7, §10.11 F6).
- H-001 sentetik vakaya dönüştü; dizlik ve iş özelindeki "yeniden ölçmeden tasarıma geçilmez" cümlesi çıktı (Ek B §10; mimari §16).
- §14: uygulama sırası faz planına bağlandı (mimari §17); eski açık konular kapandı (T-14, T-07, T-06, T-02, G-01, G-15).

## Karara bağlanan noktalar

Taslakta açık bırakılan 14 nokta, baş mühendisin 2026-11-06 08:33 UTC onayıyla (T-23) aşağıdaki önerilerle karara bağlandı. Her maddedeki "Öneri" artık karardır.

1. **Bağımsız kurum kodu.** Mimari §13.2 yeni kodu `IND` veriyor, eski çalışmalar `BAG` kodlu. Öneri: yeni işler `IND` ile açılsın; eski `BAG` çalışmaları kodlarını korusun (T-15'teki etiket kuralı gibi).
2. **Sekiz kategoride olmayan iki eski DUR.** "Dondurulmuş sürümü değiştirme" ve "süreç belgesini değiştirme" eski DUR listesinde var, kesin karar 7'nin sekiz kategorisinde yok. Öneri: varsayılan ayarda iki ek DUR kategorisi olarak eklensinler; ayar listeyi zaten yalnız genişletebilir (mimari §8.1).
3. **İşleme ayarları için kaynak.** Ö-06 işleme ayarları (yumuşatma, eşik) için ayrı bir `ayar` kaynağı önermişti; v1 etiketlerinde yok. Öneri: yeni etiket açılmasın; ayarlar kural kataloğunda ya da profilde kaynaklı dursun, dayanağı yoksa `assumption` olsun (kritik değilse V-01'e düşer).
4. **Ö-18'in kapsamı.** Ö-18 "elle yazılan her hesap" için ikinci yöntem istiyor; mimari §10.2 bunu kritik hesapla sınırlıyor. Öneri: v1 tanımı kabul edilsin; baskı/üretim isteğinin dayanağı olan her hesap kritik sayıldığı için "sınanmamış hesaba dayanan baskı istenmez" şartı korunur.
5. **Tutarlılık sınırı %10.** Ö-22'nin sınırı mimari §10.2'de "onay bekliyor" diye işaretli. Öneri: bu el kitabının onayıyla varsayılan olsun; büyüklük başına katalogda kaynaklı olarak değiştirilebilsin.
6. **Kalibrasyon baskısının aşaması (varsayım).** Ö-05 kalibrasyon baskısının G5'ten önce yapılabilmesini istiyor, Ö-08 prototip baskısını G3'e bağlıyor; kalibrasyon baskısının hangi aşamada istenebileceği hiçbir yerde yazılı değil. Öneri: profil kalibrasyon baskısı her aşamada istenebilsin (baskı isteği, DUR, ENGEL yokken); tasarımın prototip baskısı yalnız G3'te.
7. **KOSE-01'in dayanağı.** Ö-28'e göre okunmamış kaynak sayı vermez; Pilkey'in okunduğu kayıtlı değil. Öneri: sınır şimdilik `decision` kaynağıyla girsin (baş mühendisin 2026-10-27 isteği: "geçiş noktalarına radyus atılsın"); kaynak okununca `literature:` olsun.
8. **Teknik resim.** Teknik resim üretimi v1'in dışında (mimari §19.3), ama G5 çıktısında ve talaşlı imalat profilinde geçiyor. Öneri: teknik resim mekanik dışında hazırlanıp değişmez girdi olarak (içerik özetiyle) eklensin ve G5 onayına girsin.
9. **Komut adları.** Süreçte gereken bazı komutlar mimari §4.11 tablosunda yok: itiraz (`mekanik object`, §5.1), imza denetimi (`mekanik verify`, §4.6), kapı geçişi (`gate pass`, §4.2), G3 → G2 dönüşü (Ek B önerisi `gate back`). Öneri: Faz 1 başında §4.11'e eklensinler; el kitabı bu adları ondan sonra yazsın.
10. **Makine denetimi gelmeden yürürlüğe giren kurallar.** G3 → G2 dönüşü, tanımlama, standart haritası, CALC-03/04, REQ-01'in G4/G5 şartı ve SOURCE-02 Faz 2'de, KOSE-01 ile 3B baskının yeni kontrolleri Faz 3'te geliyor (mimari §17). Öneri: v1 gerçek işi devraldığında henüz denetlenmeyen kurallar kalite mühendisinin ilkeler listesine girsin ve kapı kartında "elle denetlendi" diye beyan edilsin.
11. **Eski sistemdeki işler.** Onaylanan v1 el kitabının, Faz 2'ye kadar eski sistemde süren işlere de uygulanıp uygulanmayacağı yazılı değil. Öneri: uygulanmasın; eski işler 0.2 ile sürsün (G-23). Eski kodda zaten çalışan Ö-xx'ler için eski sisteme ayrı bir sürüm yazılmasın.
12. **Görüntüleyicide sarı.** Sarı işaret eskiden "inceleme bekliyor" demekti; bu seviye kalktı (KM-02). Öneri: sarı "baş mühendisin kararını bekleyen açık kart" anlamına gelsin.
13. **Prosedür ve talimatların yeri.** v1'de prosedür ve talimatların nerede duracağı mimari belgede yazılı değil. Öneri: mekanik reposunda el kitabının yanında dursunlar ve aynı onay kuralına bağlı olsunlar.
14. **Bulut oturumu.** Eski altyapıdaki "bulut oturumu (yedek, makine kapalıyken)" satırının v1'de karşılığı yok. Öneri: v1'de çıkarılsın (platform Ubuntu masaüstü, kesin karar 5); gerekirse sonraki sürümde ayrı kararla gelsin.
