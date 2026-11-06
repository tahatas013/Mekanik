# CAD katmanı teknik araştırması: içeri alınan STEP üzerinde doğrudan modelleme ve STL tarama

- Tarih: 2026-11-06 06:17 (sistem saati)
- Rol: araştırma alt ajanı (proje mühendisi için). Bu belge karar değildir; kararlar proje mühendisi ve Taha'dadır.
- Kapsam: Python 3.12 + OCCT çekirdeği (OCP / CadQuery / build123d üzerinden). Kod yazılmadı, hiçbir şey çalıştırılıp test edilmedi.

## 0. Yöntem, sürümler ve erişim

**Terimler (ilk geçtiği yer):**
- **OCCT**: Open CASCADE Technology, açık kaynak geometri çekirdeği (LGPL 2.1 + istisna; başlık dosyalarındaki lisans metni [K10]).
- **BRep**: sınır temsili; katı, yüzlerin, kenarların ve köşelerin bağlantılı yapısıdır.
- **OCP**: OCCT'nin ince Python sarmalayıcısı; CadQuery ve build123d bunun üstünde çalışır [K11].
- **Tolerans**: OCCT'de her köşe, kenar ve yüze bağlı "bu kadar yakınsa çakışık say" yarıçapı. Kötü STEP'te büyür [K4].
- **Geçmiş (history)**: bir işlemden sonra hangi alt şeklin silindiği (Deleted), değiştiği (Modified) ya da yeni üretildiği (Generated) bilgisi [K1].

**Doğrulama yöntemi:**
- OCCT kullanım kılavuzları ve başlık dosyaları `raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master` üzerinden indirildi ve doğrudan okundu. Bu belgeler **master dalına** aittir (8.0 sonrası, içinde "Upgrade to OCCT 8.1.0" bölümü var [K8]). Kullanacağımız OCP 8.0.1 ile küçük farklar olabilir.
- Python'dan erişilebilirlik, **cadquery-ocp-stubs 8.0.1.1.0** tekerleğinin (wheel: Python paket arşivi) tip dosyalarında sınıf ve metot adı aranarak doğrulandı [K12]. "OCP'de var" bu kontrol demektir; çalıştırılarak denenmedi.
- Paket sürümleri ve bağımlılıklar PyPI JSON'undan okundu [K11].

**Erişim sorunları (görevdeki varsayımdan farklı):**
- `dev.opencascade.org`: WebFetch'te DNS çözülmedi; curl ile `occt3d.com`'a yönleniyor, vekil sunucu 403 veriyor. Buradan gelen bilgi yalnız WebSearch özetidir (**ikincil_kaynak**).
- `analysissitus.org`, `pymeshlab.readthedocs.io`, `github.com` 403 verdi. Analysis Situs için GitLab API ve depo ağacı kullanıldı [K25].
- `build123d.readthedocs.io` WebFetch'te çözülmedi, curl ile okundu.

**Paket durumu (PyPI, 2026-11-06) [K11]:**

| Paket | Son sürüm | Lisans (PyPI) | OCP bağımlılığı |
| --- | --- | --- | --- |
| cadquery-ocp | 8.0.1.1.0 (2026-10-05) | Apache-2.0 | (kendisi; VTK'lı) |
| cadquery-ocp-novtk | 8.0.1.1.0 (2026-10-05) | Apache-2.0 | (kendisi; VTK'sız) |
| cadquery | 2.8.0 (2026-06-21) | Apache 2.0 | `cadquery-ocp>=7.9.3.1,<8.0` |
| build123d | 0.13.0 (2026-09-21) | Apache-2.0 | `cadquery-ocp-novtk>=8.0,<8.1` |
| trimesh | 5.2.0 | MIT | yok |
| open3d | 0.20.0 (cp312 tekerleği var) | MIT | yok |
| pymeshlab | 2025.7.post1 | **GPL3** | yok |
| pyransac3d | 0.7.0 | Apache-2.0 | yok |

**Önemli bulgu: CadQuery ile build123d aynı `.venv`'de birlikte kullanılamaz.** CadQuery 2.8.0 OCP 7.9'a, build123d 0.13.0 OCP 8.0'a bağlı. İki OCP paketi de aynı üst düzey `OCP` klasörünü kuruyor (tekerleklerin zip dizini okunarak doğrulandı [K13]). Tek çekirdek sürümü seçilmeli. Bu bir **karar konusu**dur.

---

## (a) İşlem tablosu

Güvenilirlik sütunu **ölçüm değildir**; belgelerdeki sınırlara dayanan nitel bir değerlendirmedir. Doğrulamak için sağdaki testler bir örnek STEP derlemi üzerinde çalıştırılmalıdır. Test eşikleri (hacim farkı, açı farkı vb.) için sayı verilmedi: her biri `varsayim` etiketiyle başlar ve karara bağlanır.

**Her işlemden sonra ortak denetim (bütün satırlar için geçerli):**
1. `IsDone()` ya da hata ve uyarı listesi (`HasErrors` / `HasWarnings`) [K2].
2. `BRepCheck_Analyzer` geçerli mi. Belgeye göre geçerlilik **gerekli ama yeterli değil**, ayrıca analizör kendisi de yanılabilir [K2].
3. Katı sayısı beklenen kadar mı (genelde 1), kabuk kapalı mı.
4. En büyük tolerans eşiği aşıyor mu (`ShapeAnalysis_ShapeTolerance`, OCP'de var [K12]).
5. Geçmiş tutarlılığı: girdinin her yüzü için kendisi, Modified ya da IsDeleted cevaplarından biri gelmeli.
6. Aynı işlem listesini iki kez oynat; yüz imza tabloları (aşağıda b bölümü) aynı çıkmalı.

| İşlem | OCCT API (OCP 8.0.1'de var mı) | İçeri alınan STEP'te güvenilirlik | Bilinen sınırlar (kaynak) | Otomatik test önerisi |
| --- | --- | --- | --- | --- |
| **0. İçeri alma + iyileştirme** (işlem listesinin ilk adımı) | `STEPCAFControl_Reader`, `ShapeFix_Shape`, `ShapeFix_Wireframe`, `BRepCheck_Analyzer`, `BOPAlgo_ArgumentAnalyzer`, `BRepAlgoAPI_Check` (hepsi var) | **orta** | STEP okuyucu Shape Healing'i (şekil iyileştirme) kendiliğinden çalıştırır [K4]. `ShapeFix_Shape` hassasiyet / en büyük / en küçük tolerans ile çalışır. En büyük toleranstan fazlası gereken sorun **düzeltilemez** [K3]. Küçük kenarlar varsayılan modda silinmez (`ModeDropSmallEdges` gerekir) [K3]. İyileştirme geometriyi ve toleransı değiştirir, bu yüzden parametreleriyle **kayda geçen bir işlem** olmalı. | Dosyadaki STEP doğrulama özellikleri (validation properties: hacim, alan, ağırlık merkezi, OCCT okuyabiliyor [K4]) varsa hesaplananla karşılaştır. `BRepCheck` + `BOPAlgo_ArgumentAnalyzer` raporunu sakla. En büyük tolerans eşiği (`varsayim`). |
| **Boolean kesme / birleştirme / ortak** | `BRepAlgoAPI_Cut/Fuse/Common`. Seçenekler: `SetFuzzyValue`, `SetNonDestructive`, `SetGlue`, `SimplifyResult`, `SetRunParallel`, `History()` (var) | Geçerli girdide **yüksek**, kötü STEP'te **orta** | Her argüman `BRepCheck_Analyzer` açısından geçerli olmalı ve kendi kendini kesmemeli. Büyük köşe toleransları, teğetlik ve neredeyse çakışma hataya yol açar [K2]. Bileşik (COMPOUND) içindeki katılar birbirine değmemeli, COMPSOLID desteklenmez [K1]. İçeri alınmış modellerdeki boşluklar için "fuzzy" (bulanık) seçenek var: boşluğu ölç, biraz büyüt, değer olarak ver [K2]. Güvenli mod (`SetNonDestructive`) girdiye dokunmaz; belgeye göre geri al / yinele düzeni için yararlı [K2]. **Önerilen varsayılan: açık.** | Hacim özdeşliği: V(A−B) = V(A) − V(A∩B); V(A∪B) = V(A) + V(B) − V(A∩B) (`turetilir`; eşik `varsayim`). Sonuç geçerli ve tek katı. Kesici gövdenin yüzlerinin sonuçtaki görüntüleri `Modified`'dan gelmeli. |
| **Delik** | (1) `BRepFeat_MakeCylindricalHole`: `Perform`, `PerformThruNext`, `PerformUntilEnd`, `PerformBlind`, `Status()` (var). (2) Önerilen: profilden döndürülmüş kesici katı + `BRepAlgoAPI_Cut` | (1) basit delikte **yüksek**; (2) **yüksek** ve daha genel | (1) Yalnız silindirik delik. `Perform(R)` sonsuz silindirle kesmeye denk [K10]. Havşa, kademeli delik (cbore) ve matkap ucu konisi yok. Kör deliğin düz tabanlı olduğu bir çıkarımdır (**dogrulanmadi**). (2) Kesici katı belirlenimci (deterministic: her seferinde aynı sonucu veren) kurulur. Böylece delik duvarı "op-N kesicisinin yan yüzü" diye adlandırılabilir; geçmiş API'si Boolean ile aynıdır. | Sonuçta yarıçapı r, ekseni verilen eksen olan bir silindirik yüz bulunmalı (yüzey türü + yarıçap + eksen). Paralel yüzlerden geçen delikte hacim farkı = π·r²·L (`turetilir`). `Status() == BRepFeat_NoError`. |
| **Prizma / kabartma / cep** | `BRepFeat_MakePrism`, `BRepFeat_MakeDPrism` (açılı); `Perform(Height)`, `Perform(Until)`, `Perform(From,Until)`, `PerformUntilEnd`, `PerformThruAll` (var). Seçenek: `BRepPrimAPI_MakePrism` + Boolean | BRepFeat ile **orta**; prizma + Boolean ile **yüksek** | BRepFeat yerel (local) çalışır, bu daha hızlıdır ama taban yüzünün çizim yüzüyle ilişkisine duyarlıdır. Kendi kendini kesme denetimi bayrağı "her durumda kullanılmaz" [K1]. `ThruAll` kabartmada sonsuz parçaları sonuca koymaz [K1]. | Hacim farkı = taban alanı × yükseklik (dik prizmada, `turetilir`). Yeni yan yüz sayısı = profil kenar sayısı. |
| **Yüz öteleme (it / çek)** | (i) `BRepOffset_MakeOffset` (global ofset 0, `GeomAbs_Intersection` birleşimi) + `SetOffsetOnFace(F, d)` + `MakeOffsetShape()`. Sınıfta `Generated` / `Modified` / `IsDeleted` / `Error` var. (ii) Düzlemsel yüz için yüzün kendisiyle `BRepFeat_MakePrism` ya da prizma + Boolean. (Hepsi var) | (i) **düşük–orta**; (ii) komşular dikse **orta–yüksek**; eğik ya da eğri komşularda **düşük** | OCCT'de ayrı bir "yüzü taşı" API'si kılavuzlarda bulunamadı. (i) Kaynak kodda doğrulandı: global ofset sıfırken, `SetOffsetOnFace` ile sıfır olmayan en az bir yüz varsa giriş denetimi geçer [K10, `CheckInputData`]. **Risk (kaynak kodu okuması, test edilmedi):** açısal tolerans global ofsetten hesaplanıyor (`TolAngleCoeff = min(tol/(|ofset·0,5|+Confusion), 1)`). Ofset 0 iken değer 1, açı 2π olur; kenar sınıflandırması etkilenebilir. Ofset algoritmasının genel uyarıları: yüzeyler en az C1 olmalı (C1: teğeti sürekli); 3'ten fazla kenarın birleştiği köşede başarısız olabilir; C0 B-spline'da sonuç yok; büyük ofset kendi kendini kesme üretir [K10]. (ii) Prizmanın yan yüzleri yöne paraleldir; komşu yüzleri uzatmaz. | Eski ve yeni yüz arası düzlem mesafesi = d. Komşu yüzlerin yüzey türü korunmalı. Dokunulmayan yüzlerin imzaları değişmemeli. Dik komşularda hacim farkı = alan × d (`turetilir`). |
| **Kalıptan çıkma açısı (draft)** | `BRepOffsetAPI_DraftAngle`: `Add(F, yön, açı, nötr düzlem)`, `AddDone`, `ProblematicShape`, `Remove`, `Build` (var) | **orta** | Yalnız düzlemsel, silindirik ve konik yüzler. **Topolojiyi değiştirecek** (yeni ya da silinen köşe, kenar, yüz) durumda kullanılmaz. Teğet komşu yüzler de açılanır ve aynı koşulu sağlamalıdır [K10]. | Yüz, kenar ve köşe sayıları **değişmemeli** (algoritmanın kendi koşulu; güçlü bir test). Yeni normal ile çekme yönü arasındaki açı 90° − α olmalı. |
| **Kabuk (oyma)** | `BRepOffsetAPI_MakeThickSolid.MakeThickSolidByJoin` (yüz kaldırarak); `MakeThickSolidBySimple` (yüz kaldıramaz) (var) | **düşük–orta** (karmaşık içeri alınmış parçada) | Uyarılar ofset algoritmasıyla aynıdır [K10]. `Intersection=true` "tam uygulanmadı, önerilmez"; `SelfInter` "uygulanmadı" [K10]. | En ince duvar ≥ t: `BRepExtrema_DistShapeShape` ile örneklemeli mesafe (yöntem önerisi). Sonuç geçerli, tek katı. |
| **Tüm gövdeyi ofsetleme** | `BRepOffsetAPI_MakeOffsetShape.PerformByJoin` / `PerformBySimple` (var) | **orta** (basit), **düşük** (karmaşık) | `PerformBySimple` genelde toleransı büyütür [K1]. Diğer sınırlar kabukla aynı [K10]. | En büyük tolerans eşiği. Yüzey çiftleri arası mesafe = ofset değeri. |
| **Yuvarlatma (fillet)** | `BRepFilletAPI_MakeFillet`: `Add(r, E)`, değişken yarıçap, `SetParams`, `SetContinuity`. Tanı: `NbFaultyContours`, `FaultyContour`, `NbFaultyVertices`, `FaultyVertex`, `HasResult`, `BadShape`, `StripeStatus` (var) | Basit dışbükey kenarda **orta–yüksek**; köşe birleşimleri, karışık dışbükey/içbükey kenarlar ve B-spline yüzeylerde **düşük–orta** | Kenar iki yüz arasında paylaşılmalı. Teğet sürekli zincir boyunca yuvarlatma **kendiliğinden yayılır** [K1]; yani seçilmeyen kenarlar da yuvarlanır. Başarısızlık türleri: `ChFiDS_StartsolFailure` ("yarıçap belki çok büyük"), `TwistedSurface`, `WalkingFailure`, `Error`. Köşe dolgusu başarısız olursa delikli kısmi sonuç döner (`HasResult` + `BadShape`) [K10]. | `NbFaultyContours()==0` ve `NbFaultyVertices()==0`. Kısmi sonuç kabul edilmez. Yeni yüz sayısı zincirdeki kenar sayısıyla tutarlı olmalı. Yuvarlatma yüzü silindir ya da torus ise yarıçapı r. Dışbükey kenarda hacim azalmalı. |
| **Pah (chamfer)** | `BRepFilletAPI_MakeChamfer`: `Add(d, E, F)`, `Add(d1, d2, E, F)` (var) | **orta–yüksek** | Oluşan yüzeyler cetvelli (ruled) yüzeydir. Kullanımı fillet ile aynı [K1]; benzer yayılma ve köşe sorunları beklenir (**dogrulanmadi**). | Fillet ile aynı denetimler; pah yüzü düzlemsel ise iki kenar mesafesi d1, d2. |
| **Detay silme (defeaturing)** | `BRepAlgoAPI_Defeaturing`: `SetShape`, `AddFacesToRemove`, `SetRunParallel`, `SetToFillHistory`, `Build`, `HasWarnings`, `DumpWarnings`, `Modified/Generated/IsDeleted` (var) | **orta** | Girdi yalnız SOLID, COMPSOLID ya da katılardan oluşan COMPOUND olabilir; yalnız yüz silinir. **Özellik tanıma yapmaz**, silinecek yüzleri kullanıcı verir. Özellikler tek tek silinir; biri başarısız olursa **uyarı verilir ve sonraki özelliğe geçilir** (`BOPAlgo_AlertUnableToRemoveTheFeature`), yani sessiz kısmi başarı riski vardır. Delik, komşu yüzler uzatılıp kırpılarak doldurulur: komşu yüzeylerin kesişimi boş olmamalı (komşular birbirine teğet olmamalı) ve uzatılan yüzler özelliği tamamen örtmeli. İç (INTERNAL) parçalar silinir [K1, K10]. | `HasWarnings()==False` zorunlu. Silinen yüzler `IsDeleted` olmalı ve imza aramasında bulunmamalı. Doldurulan delikte hacim artışı = π·r²·h (`turetilir`). Sonuç geçerli. |
| **Aynı yüzeydeki yüzleri birleştirme** | `ShapeUpgrade_UnifySameDomain`: `UnifyFaces/UnifyEdges/ConcatBSplines`, `AllowInternalEdges`, `KeepShape(s)`, `SetSafeInputMode` (varsayılan true), `SetLinearTolerance` / `SetAngularTolerance` (varsayılanlar `Precision::Confusion()` / `Precision::Angular()`), `History()` (var) | **yüksek** | Kabuk ve katı yapısını korur. İki kabuğun ortak kenarındaki yüzleri birleştirmez [K10]. **Topolojiyi değiştirdiği için bütün yüz indekslerini geçersiz kılar**; başvurular geçmişle taşınmalı. Boolean'daki `SimplifyResult` aynı aracı kullanır ve geçmişi ana geçmişe katar [K2]. | Hacim değişmemeli (eşik `varsayim`). Yüz sayısı azalmalı ya da aynı kalmalı. Geçerli. |
| **Dikiş (sewing)** | `BRepBuilderAPI_Sewing` (var) | **orta** | Geometriyi değiştirmez, yalnız bağlantı ekler. Çalışma toleransı küçük, en küçük tolerans büyük seçilmeli. Açık kabukta büyük tolerans istenen delikleri de kapatabilir [K1]. | Serbest kenar sayısı 0 (kapalı beklenirse). Sonuç kabuk mu bileşik mi. |
| **Kötü STEP / tolerans** | Okuma parametreleri: `read.precision.mode`, `read.precision.val`, `read.maxprecision.val`, `read.maxprecision.mode` [K4] | — | Varsayılanlar [K4]: `read.precision.mode` = File (0), yani dosyadaki belirsizlik değeri kullanılır. `read.precision.val` = 0,0001 (mm). `read.maxprecision.val` = 1. `read.maxprecision.mode` = 0 ("Preferred"): en büyük tolerans **aşılabilir**. Dolayısıyla okunan bir şekilde 1 mm mertebesinde, hatta üstünde tolerans çıkabilir. Bu da Boolean belgesindeki "büyük köşe toleransı" hatalarına yol açar [K2]. | İçeri almada en büyük tolerans eşiği (`varsayim`) aşılırsa **dur ve kart aç**. Okuma parametrelerini işlem 0'ın kaydına yaz. |

**Ek notlar:**
- **Sürüm duyarlılığı.** OCCT 8.0'da `IsClosed()` / `IsPeriodic()` toleransı değişti [K8]. Boolean sonucundaki alt şekil sırası geçmişte bir sürümden ötekine değişti; testler yeni sıraya göre güncellendi [K31]. **Çekirdek sürümü sabitlenmeli. Sürüm değişikliği tam regresyon gerektirir** (CLAUDE.md'deki `surec regresyon` kuralıyla uyumlu).
- **Paralel mod.** Paralel çalışmanın sonuç sırasını değiştirip değiştirmediği **dogrulanmadi**. Bir commit mesajı sıranın sabit kalması için indeksli eşlemlere (map) geçildiğini söylüyor [K31]. Belirlenimcilik testi paralel açık ve kapalı ayrı ayrı yapılmalı.

---

## (b) Yüz ve kenar başvurusu için önerilen düzen

### Bulgular

1. **`TopExp::MapShapes` sırası.** Bu fonksiyon `TopExp_Explorer`'ın gezdiği sırayla `IndexedMap`'e ekler; indeks, **ekleme sırasıdır** [K7]. Gezinme, şeklin içindeki çocuk listesinin sırasını izler (`TopoDS_TShape` çocukları `NCollection_List` olarak saklanır [K8]). Sonuç: **aynı OCCT sürümü + aynı girdi BRep + aynı okuma ve iyileştirme parametreleri** varsa indeks belirlenimcidir (kaynak okumasından çıkarım; test edilmedi).
2. **Kıyım (hash) tabanlı kümeler belirlenimci değildir.** `TopTools_ShapeMapHasher` kıyımı `TShape` **bellek adresinden** üretir [K10, `TopoDS_Shape.hxx`]. Dolayısıyla `TopTools_MapOfShape`'in, ya da Python'da şekiller üstünde kurulan `set` ve kıyım sıralamasının yineleme sırası çalıştırmadan çalıştırmaya değişebilir. **İndeks yalnız `IndexedMap` / Explorer sırasından alınmalı.**
3. **İndeks, işlemler ve sürümler arasında taşınmaz.** Her işlem yeni bir şekil üretir. Boolean sonuç sırası sürümler arasında değişmiştir [K31]. build123d belgesi de "listedeki sıra aynı kalmayabilir, sabit indeks kullanmayın" diyor [K15].
4. **Geçmiş API'si kullanılabilir durumda.** Bütün topoloji API algoritmaları köşe, kenar ve yüz için Deleted / Modified / Generated verir. Geçmiş, sonuçta olmayan şekli döndürmez. Sonuç boşsa her şey Deleted sayılır [K1]. `BRepTools_History` geçmişleri birleştirir (`Merge`) [K1]. OCP'de `BRepTools_History()` boş kurucu, `AddModified`, `AddGenerated`, `Remove`, `Merge`, `Modified`, `Generated`, `IsRemoved` var. Algoritmadan doğrudan kuran şablon kurucu stub'ta yok, ama Boolean, BRepFeat ve UnifySameDomain sınıflarında `History()` var. Fillet, Draft ve Offset için `Modified/Generated/IsDeleted` ile elle doldurulabilir [K12].
5. **Bölünme belirsizliği.** Bir yüz ikiye bölünürse `Modified` iki yüz döndürür [K1]. Bu durumda "o yüz" artık tek değildir; otomatik seçim yapılmamalı.
6. **OCAF/TNaming.** Üç bileşenden oluşur: algoritma geçmişi, sonucun belgeye kurallara göre yüklenmesi, seçim ve yeniden hesaplama (`TNaming_Selector.Select/Solve`). Katı sonuçta bütün yüzlerin geçmişi yüklenmeli, dikiş kenarları ayrıca izlenmeli [K6]. OCP'de `TNaming_Builder`, `TNaming_Selector`, `TNaming_NamedShape` var [K12]. Python'da sağlam kullanım örneği ve başarım bilgisi bulunamadı (**dogrulanmadi**). FreeCAD 1.0'daki ad algoritması da sorunu "çözmez": amacı önce kırık başvuruyu **tespit etmek**, sonra aday önermek, ancak yüksek güvenle otomatik onarmaktır ("First, do no harm") [K23].
7. **BRepGraph (OCCT 8.0).** Kalıcı UID kavramı var, ama grafik düzeyindeki GUID her yeniden kurulumda rastgele üretiliyor ve arayüz 8.1'de değişecek [K30, ikincil_kaynak]. OCP 8.0.1 stub'larında **yok** [K12]. Şimdilik kullanılamaz.
8. **build123d ve CadQuery geçmiş seçicileri.** build123d'nin geliştirme belgesinde `Select.LAST` / `Select.NEW` ve sonuçla taşınan işlem kaydı anlatılıyor [K16]. Bu özellik 0.13.0 kararlı sürümde **dogrulanmadi** (sayfa 0.13.1.dev). CadQuery belgesinde serbest fonksiyonlara `history: History` parametresi ve `Op.modified/generated/deleted/images` var [K14].

### Önerilen düzen (pratik)

**İlke:** başvuru, işlemin **girdi durumuna** göre yazılır ve üç katmanla doğrulanır. Belirsizlikte tahmin edilmez, durulur.

```yaml
# islemler.yaml (örnek biçim; adlar ASCII)
taban:
  dosya: girdi/parca.step
  sha256: <dosya özeti>
  okuma: {read.precision.mode: 0, read.maxprecision.val: 1, ...}   # kaynak: K4 varsayılanları ya da karar
  cekirdek: {ocp: 8.0.1.1.0}                                         # sabitlenmiş sürüm
islemler:
  - id: op-001
    tur: iyilestir           # ShapeFix parametreleri kayıtlı
  - id: op-002
    tur: delik
    hedef_yuz:
      durum: op-001          # hangi ara modelin yüzü
      indeks: 17             # MapShapes(FACE) sırası; yalnız hızlı yol
      imza:                  # doğrulama
        yuzey: plane         # GeomAbs_SurfaceType
        alan: <turetilir>
        agirlik_merkezi: [..]
        normal: [..]         # düzlem; silindirde eksen + yarıçap
        kenar_sayisi: 4
        komsu_yuzey_turleri: [plane, plane, plane, cylinder]
      soy: girdi             # ya da {op: op-00k, rol: "kesici.yan_yuz"}
    parametre: {cap: ..., kaynak: "standart:..."}   # kaynaksız sayı yok
    cikti_ozeti: {brep_sha256: ..., hacim: ..., yuz_imza_tablosu: kayit/op-002.json}
```

**Çözümleme adımları:**
1. **Hızlı yol.** `durum`'daki şekilde `indeks`'teki yüzü al, imzasını karşılaştır. Eşleşirse kullan.
2. **Soy (geçmiş) yolu.** İndeks tutmazsa, başvurunun kaynağı olan yüzü işlem geçmişleri üzerinden ileri taşı (`Modified` / `Generated`, birleştirilmiş `BRepTools_History`). Sonuç **tek** yüzse ve imza tutarsa kullan.
3. **İmza araması.** Hâlâ yoksa tüm yüzlerde imza ara. **Tam bir** eşleşme varsa kullan ve kayda `yeniden_eslendi` yaz.
4. **Dur.** Sıfır ya da birden çok aday varsa (örnek: bölünme) **durdur, hata ver, kart aç**. Seçimi insan yapar.

**Yan kurallar:**
- **Kendi ürettiğimiz yüzleri** (delik duvarı, kabartma yanları) kesici ya da araç katısının belirlenimci yüzleri üzerinden adlandır ("op-002.kesici.yan_yuz"). Bunlar geçmişte `Modified` olarak izlenir. Bu, BRepFeat yerine "araç katısı + Boolean" tercihinin ana gerekçesidir.
- Her işlemin çıktısının **yüz imza tablosunu** ve BRep özetini sakla. Yeniden oynatmada fark, regresyon bulgusudur.
- **Geçmiş işlemleri.** İşlem listesi değişmez kayıt olarak tutulur: geri alma = listeden çıkarıp yeniden oynatma; ara BRep önbelleği hızlandırır. Boolean'da `SetNonDestructive(True)`, Unify'da `SetSafeInputMode(True)` kullanılmalı ki girdiler bozulmasın [K2, K10].
- **İlk sürümde TNaming kullanılmasın** (karmaşık, Python belgesi zayıf). Düzen ileride TNaming'e taşınabilir; geçmiş verisi aynı veridir [K6].
- **İmza toleransları** (alan, konum, açı) `varsayim` etiketiyle başlar ve regresyon derlemiyle ayarlanıp karara bağlanır.

---

## (c) STEP biçim desteği (OCCT)

| Konu | Okuma | Yazma | Python'dan erişim | Not / kaynak |
| --- | --- | --- | --- | --- |
| AP214 (CC2, CD ve DIS) | var | var (varsayılan `AP214CD`) | CadQuery `importStep`, build123d `import_step`, OCP | [K4] |
| AP203 | var | var (`AP203`) | aynı | [K4] |
| AP242 | "bazı kısımları" | `AP242DIS` seçeneği | aynı | GD&T yazmak için şema elle AP242'ye çekilmeli [K4] |
| Temsil türleri | advanced_brep, faceted_brep, manifold_surface, wireframe, hybrid, **tessellated** | — | — | `read.step.tessellated` varsayılanı 1 (açık) [K4] |
| Montaj (assembly) | `mapped_item` ve `representation_relationship_with_transformation`; iç içe bileşik ya da XCAF montajı | ikinci yol | CadQuery `Assembly.importStep`, OCP `XCAFDoc_ShapeTool` | [K4, K14, K12] |
| Ad | XCAF ile | XCAF ile | OCP `STEPCAFControl_Reader` (`SetNameMode`) | [K4, K5] |
| Renk | montaj, katı, kabuk, yüz, kenar, köşe renkleri ve görünmezlik | köşe rengi yalnız parametreyle | OCP `XCAFDoc_ColorTool` | İki yüze ayrı renk, saydamlık, yansıma, eğri stili ve nokta işareti **okunmaz** [K4] |
| Katman, malzeme | katman; malzeme adı, açıklama, yoğunluk | var | OCP | [K4] |
| Doğrulama özellikleri | alan, hacim, ağırlık merkezi | var | OCP | İçeri alma testinde kullanılabilir [K4] |
| **PMI / GD&T** (ürün ve imalat bilgisi: ölçü, geometrik tolerans, datum) | Anlamsal (semantic) okuma: `Dimensional_Size/Location(_With_Path)`, `Angular_Size/Location` → `XCAFDoc_Dimension`; `Geometric_Tolerance` → `XCAFDoc_GeometricTolerance`; `Datum`, `Datum_Feature`, `Datum_Target` → `XCAFDoc_Datum` | okunabilenlerin hepsi yazılabilir | OCP: `XCAFDoc_DimTolTool`, `XCAFDimTolObjects_DimensionObject` (var [K12]). CadQuery ve build123d belgelerinde PMI erişimine rastlanmadı | Kısıtlar [K4]: yalnız şekle bağlı GD&T alınır (yardımcı geometri başvurusu alınmaz). Tolerans bölgelerinin yalnız bir kısmı alınır. Gösterim (presentation) kısmen: polyline ve tessellated var, karakter tabanlı yok, stil bilgisi yok. AP214'teki GD&T "eskimiş, AP242 kullanın". Kayıtlı görünümler okunur ama **yazılmaz** |
| Kullanıcı tanımlı öznitelikler | parça, örnek (instance) ve geometri düzeyinde | — | OCP | [K4] |
| **Birimler** | Uzunluk, düzlem açı birimi ve belirsizlik `shape_representation`'dan alınır; `xstep.cascade.unit` (varsayılan MM) birimine dönüştürülür | `write.step.unit` (varsayılan MM) | CadQuery `importStep(unit=...)`; build123d `import_step`'te birim parametresi yok [K17] (mm varsayılır, **dogrulanmadi**); OCP `XCAFDoc_LengthUnit` | [K4, K14] |
| Çok iş parçacığı | master belgesi: çağrı başına `DESTEP_Parameters` ile güvenli | — | OCP stub'ında `DESTEP_Parameters` imzalarda geçiyor ama **sınıf tanımı yok** [K12]; Python'dan kurulabilirliği **dogrulanmadi** | [K4] |

**Pratik sonuçlar:**
- **PMI ile düzenleme çakışır.** PMI, yüzlere başvurur. Bizim işlemlerimiz yüz kimliklerini değiştirince PMI bağlantısı bayatlar. PMI'yi korumak için PMI→yüz bağları da (b)'deki geçmiş ve imza düzeniyle taşınmalı; yoksa çıktı STEP'te PMI yazılmamalı ya da "bayat" diye işaretlenmeli (öneri).
- **AP sürümleri.** AP203 temel geometri, AP214 renk ve katman, AP242 anlamsal PMI ve tessellated geometri olarak özetleniyor. AP203'te renk konusunda kaynaklar çelişiyor [K35, ikincil_kaynak].

---

## (d) Taramadan katıya: yapılabilen ve yapılamayan

| Adım | Açık kaynak araç (lisans) | Yapılabilen | Yapılamayan / sınır | Kaynak |
| --- | --- | --- | --- | --- |
| STL okuma | OCCT `RWStl` → `Poly_Triangulation`; `StlAPI_Reader` (her üçgen bir yüz); trimesh (MIT) | Hızlı ağ okuma | `StlAPI_Reader` "çok verimsiz", RWStl öneriliyor | [K10] |
| Onarım | `trimesh.repair`: `fill_holes`, `fix_normals`, `fix_winding`, `fix_inversion`, `stitch`, `broken_faces` (MIT); PyMeshLab (**GPL3**); Open3D aykırı nokta temizleme (MIT) | Normal, sarım yönü ve küçük delik onarımı | `fill_holes` yelpaze kullanır; **dışbükey olmayan** deliklerde kötü sonuç verir [K26]. PyMeshLab GPL3'tür: dağıtılan bir araçta lisans yükümlülüğü doğar (**karar konusu**) | [K26, K11] |
| Noktadan yüzey | Open3D: alpha shapes, ball pivoting, Poisson | Fotogrametri ya da LiDAR nokta bulutundan ağ | Poisson az noktalı bölgelerde de üçgen üretir, dışa taşar. `densities` çıktısıyla süzülmeli | [K27] |
| Hizalama (ICP: en yakın nokta yinelemesi) | Open3D `registration_icp` (noktadan noktaya ve noktadan düzleme), Generalized ICP, renkli ICP, robust kernel, global hizalama (RANSAC + FPFH); trimesh `registration.icp`, `procrustes`, `mesh_other` | CAD ile tarama hizalama | ICP **kaba bir başlangıç hizası ister**; global hizalama ya da işaret noktaları (landmark) gerekir [K27, K26]. Simetrik parçada yanlış yerel minimum riski (**dogrulanmadi**) | [K26, K27] |
| Sapma haritası | CAD → `BRepMesh_IncrementalMesh` ile üçgenle → `trimesh.proximity.signed_distance` / `closest_point`; Open3D `compute_point_cloud_distance` (işaretsiz) | Renkli sapma haritası, istatistik | trimesh işaret kuralı: dışarıdaki nokta **negatif** [K26]. CAD üçgenleme sapması da hataya eklenir; bu yüzden üçgenleme sapması, ölçülen sapmadan küçük seçilmeli (`varsayim`). Kesin BRep mesafesi için `BRepExtrema_DistShapeShape` var; nokta başına hızı **dogrulanmadi** | [K26, K27, K12] |
| İlkel uydurma (RANSAC: rastgele örnekle uzlaşı arama) | Open3D `segment_plane` (**yalnız düzlem**), `detect_planar_patches`; pyransac3d (Apache-2.0): düzlem, silindir, küp, küre, doğru, çember, nokta; FreeCAD Mesh "Segmentation From Best-Fit Surfaces" (düzlem, silindir, küre + parametre); build123d `detect_primitives()` (düzlem, küre, silindir + kod önerisi) | Prizmatik parçalarda ana yüzeyler ve parametreleri | Open3D'de silindir ve küre RANSAC'ı yok. pyransac3d ve FreeCAD listesinde **koni yok**. build123d'de yuvarlatmalar silindir olarak çıkar; "bas-geç STL→CAD dönüştürücü değildir" [K18] | [K27, K11, K21, K17, K18] |
| Kesitten ölçü | `Trimesh.section`, `section_multiplane`, `intersections.mesh_plane`; çember uydurma için `trimesh.nsphere.fit_nsphere` | Çap, aralık, et kalınlığı; kayda `olcu:tarama` + uydurma artığı (residual) | Tarayıcının sistematik hatası (ölçek, kalibrasyon) uydurmayla düzelmez | [K26] |
| Ağdan faceted BRep | FreeCAD Part ShapeFromMesh (+ isteğe bağlı dikiş, RefineShape, MakeSolid); OCCT `BRepBuilderAPI_Sewing` + `ShapeUpgrade_UnifySameDomain` + `BRepBuilderAPI_MakeSolid` | Geçerli katı, Boolean'a girebilir; düzlem bölgeler birleştirilebilir | Çok yüzlü, ağır, parametrik değil. Eğri yüzeyler üçgen kalır | [K22, K24, K1] |
| NURBS yüzey uydurma (B-spline: parçalı polinom serbest yüzey) | OCCT `GeomAPI_PointsToBSplineSurface` (ızgara nokta), `GeomPlate_BuildPlateSurface` (eğri ve nokta kısıtlı); FreeCAD Reverse Engineering "Approximate a B-spline surface" | Tek bir bölgeye serbest yüzey | FreeCAD wiki'si tezgâhı "şu an işlevsellik yok, geliştirici kum havuzu" diye anlatıyor; tek araç listeli [K20]. Yüz bölütleme, kırpma ve kapalı katıya dikme **elle** yapılır | [K1, K12, K20] |
| Parametrik katı (tasarım niyetiyle) | build123d ile elle modelleme + `detect_primitives` yardımı | Prizmatik parça için yarı otomatik akış: simetriyle bölge küçült → BRep önbelleği → ilkel tespit → elle yeniden kurma [K18] | **Otomatik değil.** build123d belgesi: "yavaş, yaklaşık ve elle"; serbest yüzeyli, gürültülü ya da simetrisiz parçada ağı yalnız görsel referans olarak kullanmak daha hızlı olabilir [K18] | [K18] |
| Özellik tanıma (BRep'te) | Analysis Situs (**BSD-3**, C++/Tcl SDK; PyPI'de Python paketi bulunamadı): delik, yuvarlatma zinciri, cep (cavity), mil tanıma; yuvarlatma bastırma, `SuppressFeatures`, Euler işlemleri, `Naming`, `History` modülleri | STEP katısında delik ve yuvarlatma bulup `BRepAlgoAPI_Defeaturing`'e yüz listesi vermek | Python'dan doğrudan kullanılamıyor (bağlama gerekir); işlevlerin kapsamı yalnız dosya adlarından anlaşıldı (**dogrulanmadi**). FreeCAD Part Defeaturing: OCCT defeaturing arayüzü; sonuç parametrik değil, özgün nesneye bağlı değil [K19] | [K25, K19] |

### Doğruluğun tarayıcıya bağlılığı

- **iPhone / iPad LiDAR.** Bulunan çalışmalar **santimetre** sınıfı doğruluk bildiriyor (ör. ±1 cm, RMSE 1–1,5 cm; küçük nesnelerde zorluk) [K33, ikincil_kaynak]. Görev metnindeki "~mm" varsayımını bu kaynaklar **desteklemiyor**. Ön kameradaki TrueDepth yapısal ışık sensörünün yakın mesafede daha iyi olabileceği **dogrulanmadi**.
- **Yapısal ışık.** Metroloji sınıfı sistemler VDI/VDE 2634-2'ye göre doğrulanıyor. Satıcılar µm mertebesi iddia ediyor (ör. 0,007 mm) [K34, ikincil_kaynak, satıcı iddiası]. NIST, bu yönergelerin her hata kaynağına duyarlı olmayabileceği uyarısını yapıyor [K34].
- **Fotogrametri.** Kurulum, ölçek çubuğu ve doku belirler. Bağımsız ve karşılaştırmalı mm verisi bulunamadı [K34].
- **Öneri.** Tarayıcı belirsizliği bir referans parçayla (mastar, bilye çubuğu) **bizim ölçümümüzle** kayda alınmalı (`olcu:tarama`) ve her taramadan türetilen ölçüye eklenmeli. Satıcı sayısı kaynak sayılmaz.

### Ticari araçların yapıp açık kaynağın yapmadıkları (ikincil_kaynak, satıcı ve bayi sayfaları [K36, K37])

- **Geomagic Design X**
  - Bütün ağda otomatik bölge bölütleme ve bölge sınıflandırma.
  - Bölgelerden profil, eksen ve yol çıkarıp extrude, revolve ve sweep özelliklerini **tek zaman çizelgesinde** kuran sihirbazlar.
  - Kesitten kısıtlı çizim.
  - Model ağacıyla bütünleşik canlı sapma analizi (Accuracy Analyzer).
  - Organik yüzeyler için otomatik NURBS yama ağı (auto-surfacing).
  - Geçmişi koruyarak SolidWorks, NX ve Creo'ya aktarım (LiveTransfer).
- **QuickSurface**
  - **Koni dahil** ilkel uydurma.
  - Canlı sapma haritasıyla serbest yüzey uydurma.
  - Otomatik simetri düzlemi bulma.
  - Tek fırça hareketiyle kanal, dikdörtgen ve altıgen tanıma.
  - Hibrit (serbest + ilkel) modelleme.
- **Açık kaynakta karşılığı bulunamayanlar:**
  - Bütünleşik "bölge → özellik → kısıtlı çizim" akışı.
  - Otomatik NURBS yama yerleşimi.
  - Koni RANSAC'ı (incelenen kütüphanelerde).
  - Tasarım niyeti çıkarımı: simetri ve standart ölçüye yuvarlama. build123d bunu elle yapılacak adım olarak anlatıyor [K18].

---

## (e) Dürüst özet

1. **Boolean, delik ve pah güvenli bir temel.** Geçerli bir içeri alınmış katıda Boolean (kesme ve birleştirme), "araç katısı + Boolean" ile delik ve pah güvenle yapılabilir. Hacim özdeşlikleriyle otomatik test edilebilir. Kötü STEP'te fuzzy seçenek ve iyileştirme gerekir.
2. **Fillet, kabuk, ofset ve draft koşulludur.** Başarısızlık olağandır: tanı API'leriyle yakalanmalı, kısmi sonuç kabul edilmemeli, kullanıcıya açıkça "yapılamadı" denmeli. Draft topolojiyi değiştiremez; kabuk ve ofsetin bazı modları belgeye göre "tam uygulanmamış".
3. **Detay silme sessizce kısmi başarı verebilir.** Bir özellik silinemezse uyarı verip devam ediyor. `HasWarnings()` bir kapı (gate) olmalı. Özellik tanıma yapmaz; yüzleri biz (ya da Analysis Situs) vermeliyiz.
4. **Yüz taşımak için OCCT'de doğrudan bir API yok.** `SetOffsetOnFace` + sıfır global ofset kaynak koduna göre mümkün, ama riskli ve test edilmedi. Düzlemsel yüz ve dik komşular için prizma yolu daha güvenilir.
5. **Topolojik ad sorununun hazır çözümü yok.** İndeks yalnız sabit sürüm ve aynı girdi için belirlenimci; kıyım tabanlı kümeler değil. Önerilen düzen: indeks (hızlı yol) + geçmiş soyu + geometrik imza; belirsizlikte **dur ve sor**. TNaming OCP'de var ama ilk sürüm için ağır.
6. **Çekirdek sürümü tek ve sabit olmalı.** CadQuery 2.8 (OCP 7.9) ile build123d 0.13 (OCP 8.0) aynı ortamda kurulamaz, ikisi de `OCP` paketini kuruyor. Hangisi seçilecek: karar konusu. Her sürüm yükseltmesi tam regresyon demek.
7. **PMI.** STEP AP242'deki PMI anlamsal olarak (kısıtlarla) okunabiliyor, ama CadQuery ve build123d bunu açmıyor; OCP üzerinden kendimiz okumalıyız. Düzenleme sonrası PMI→yüz bağları geçmişle taşınmazsa PMI bayatlar.
8. **Kötü STEP toleransları.** Okuma varsayılanlarıyla toleranslar 1 mm mertebesine çıkabilir ve bu sınır aşılabilir (`read.maxprecision.mode=0`). İçeri almada tolerans ölçülmeli ve eşikle durdurulmalı.
9. **Taramadan katıya.** Açık kaynakla ölçüm, hizalama, sapma haritası, düzlem, silindir ve küre uydurma ve faceted katı yapılabilir. **Tasarım niyetli parametrik katı otomatik çıkmaz**; prizmatik parçada yarı otomatik, serbest yüzeyde elle. Ticari araçlar daha çok otomasyon sunuyor ama onlar da kullanıcı yönlendirmeli.
10. **Tarayıcı doğruluğu.** iPhone LiDAR santimetre sınıfı, milimetre değil. Tarayıcı belirsizliği referans parçayla bizim ölçümümüzle kayda alınmadan taramadan türetilen hiçbir ölçü `olcu:tarama` diye kullanılmamalı.

**Taha'nın kararını gerektirenler:**
- (1) build123d 0.13 + OCP 8.0.1 mi, CadQuery 2.8 + OCP 7.9.3 mü?
- (2) PyMeshLab'ın GPL3 lisansı kabul edilebilir mi, yoksa trimesh ve Open3D ile mi yetinilecek?
- (3) Tolerans ve imza eşikleri (şimdilik `varsayim`).
- (4) Analysis Situs için C++ bağlama çalışması yapılacak mı?

---

## (f) Kaynak listesi

Durum: **metin_elde** = metin indirildi ve okundu; **ikincil_kaynak** = yalnız WebSearch özeti ya da üçüncü taraf; **dogrulanmadi** = bellekten ya da çıkarım.

| No | Kaynak | URL | Durum |
| --- | --- | --- | --- |
| K1 | OCCT Modeling Algorithms kılavuzu (Boolean, History, Fillet, Offset, Draft, Shell, Sewing, Features, Defeaturing, Plate) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/modeling_algos/modeling_algos.md | metin_elde |
| K2 | OCCT Boolean Operations belirtimi (sınırlamalar, fuzzy, glue, güvenli mod, uyarılar, sadeleştirme) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/specification/boolean_operations/boolean_operations.md | metin_elde |
| K3 | OCCT Shape Healing kılavuzu (ShapeFix, UnifySameDomain, Shape Processing) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/shape_healing/shape_healing.md | metin_elde |
| K4 | OCCT STEP kılavuzu (AP desteği, parametreler ve varsayılanlar, tolerans, birim, XDE öznitelikleri, GD&T) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/step/step.md | metin_elde |
| K5 | OCCT XDE kılavuzu | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/xde/xde.md | metin_elde |
| K6 | OCCT OCAF kılavuzu (TNaming, topolojik adlandırma) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/ocaf/ocaf.md | metin_elde |
| K7 | OCCT Modeling Data kılavuzu (TopExp_Explorer, MapShapes) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/modeling_data/modeling_data.md | metin_elde |
| K8 | OCCT Upgrade kılavuzu (8.0 değişiklikleri: TShape, IsClosed toleransı) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/upgrade/upgrade.md | metin_elde |
| K9 | OCCT DRAW kılavuzu (bopargcheck, removefeatures, checkshape) | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/dox/user_guides/draw_test_harness/draw_test_harness.md | metin_elde |
| K10 | OCCT başlık ve kaynak dosyaları: `BRepOffset_MakeOffset.hxx/.cxx`, `BRepOffsetAPI_MakeOffsetShape.hxx`, `BRepOffsetAPI_MakeThickSolid.hxx`, `BRepOffsetAPI_DraftAngle.hxx`, `BRepFeat_MakeCylindricalHole.hxx`, `BRepFilletAPI_MakeFillet.hxx`, `BRepAlgoAPI_Defeaturing.hxx`, `ShapeUpgrade_UnifySameDomain.hxx`, `TopoDS_Shape.hxx`, `TopTools_ShapeMapHasher.hxx`, `TopExp.hxx`, `StlAPI_Reader.hxx`, `RWStl.hxx` | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/src/ModelingAlgorithms/TKOffset/BRepOffset/BRepOffset_MakeOffset.cxx (ve aynı ağaçta diğerleri: `src/ModelingAlgorithms/TKOffset/BRepOffsetAPI/`, `TKFeat/BRepFeat/`, `TKFillet/BRepFilletAPI/`, `TKBO/BRepAlgoAPI/`, `TKShHealing/ShapeUpgrade/`, `src/ModelingData/TKBRep/{TopoDS,TopTools,TopExp}/`, `src/DataExchange/TKDESTL/{StlAPI,RWStl}/`) | metin_elde |
| K11 | PyPI JSON: cadquery-ocp, cadquery-ocp-novtk, cadquery, build123d, trimesh, open3d, pymeshlab, pyransac3d | https://pypi.org/pypi/cadquery-ocp/json (ve `/pypi/<paket>/json`) | metin_elde |
| K12 | cadquery-ocp-stubs 8.0.1.1.0 tip dosyaları (sınıf ve metot varlığı) | https://files.pythonhosted.org/packages/46/7f/b91cd251ad52e3540b24f5f4536681c51647376a1700fd82cbbcd6f32d02/cadquery_ocp_stubs-8.0.1.1.0-py3-none-manylinux_2_28_x86_64.whl | metin_elde |
| K13 | OCP tekerleklerinin zip dizini (ikisi de `OCP/` kuruyor) | https://files.pythonhosted.org/packages/33/07/ab496c866d8b3c94c4fe0f8c38dc4773a6dcc7f4826c680ac1cd7dba88b4/cadquery_ocp_novtk-8.0.1.1.0-cp312-cp312-manylinux_2_28_x86_64.whl ; https://files.pythonhosted.org/packages/4f/0b/a86026c205b44fbdadc8e4312e0bc276973d71c43ddce9aa924c3bf2ff5a/cadquery_ocp-8.0.1.1.0-cp312-cp312-manylinux_2_28_x86_64.whl | metin_elde |
| K14 | CadQuery Class Reference (History/Op, importStep, Assembly.importStep, fuse/fillet/draft/hollow/clean/check) | https://cadquery.readthedocs.io/en/latest/classreference.html | metin_elde |
| K15 | build123d Selector Tutorial (sabit indeks uyarısı) | https://build123d.readthedocs.io/en/latest/tutorial_selectors.html | metin_elde |
| K16 | build123d Topology Selection (Select.LAST/NEW, işlem kaydı; 0.13.1.dev belgesi) | https://build123d.readthedocs.io/en/latest/topology_selection.html | metin_elde |
| K17 | build123d Import/Export (import_step, import_stl, detect_primitives; 0.13.0 kararlı belgede de var) | https://build123d.readthedocs.io/en/stable/import_export.html | metin_elde |
| K18 | build123d STL Reconstruction Tutorial | https://build123d.readthedocs.io/en/latest/tutorial_stl_reconstruction.html | metin_elde |
| K19 | FreeCAD wiki: Part Defeaturing | https://wiki.freecad.org/Part_Defeaturing | metin_elde |
| K20 | FreeCAD wiki: Reverse Engineering Workbench | https://wiki.freecad.org/Reverse_Engineering_Workbench | metin_elde |
| K21 | FreeCAD wiki: Mesh SegmentationBestFit | https://wiki.freecad.org/Mesh_SegmentationBestFit | metin_elde |
| K22 | FreeCAD wiki: Part ShapeFromMesh | https://wiki.freecad.org/Part_ShapeFromMesh | metin_elde |
| K23 | FreeCAD wiki: Topological naming problem | https://wiki.freecad.org/Topological_naming_problem | metin_elde |
| K24 | FreeCAD wiki: Part RefineShape | https://wiki.freecad.org/Part_RefineShape | metin_elde |
| K25 | Analysis Situs: GitLab proje API'si (lisans BSD-3), README, `src/asiAlgo` ağacı | https://gitlab.com/api/v4/projects/ssv%2FAnalysisSitus ; https://gitlab.com/ssv/AnalysisSitus/-/raw/master/README.md | metin_elde (işlev kapsamı dosya adlarından: dogrulanmadi) |
| K26 | trimesh belgeleri: repair, proximity, registration, intersections, nsphere, Trimesh | https://trimesh.org/trimesh.repair.html ; https://trimesh.org/trimesh.proximity.html ; https://trimesh.org/trimesh.registration.html ; https://trimesh.org/trimesh.intersections.html ; https://trimesh.org/trimesh.nsphere.html ; https://trimesh.org/trimesh.html | metin_elde |
| K27 | Open3D 0.19 belgeleri: Point cloud, PointCloud API, ICP, Global registration, Robust kernels, Surface reconstruction | https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html ; https://www.open3d.org/docs/release/python_api/open3d.geometry.PointCloud.html ; https://www.open3d.org/docs/release/tutorial/pipelines/icp_registration.html ; https://www.open3d.org/docs/release/tutorial/pipelines/global_registration.html ; https://www.open3d.org/docs/release/tutorial/geometry/surface_reconstruction.html | metin_elde |
| K28 | OCCT 8.0.0 sürüm duyurusu | https://dev.opencascade.org/content/open-cascade-technology-800-release | ikincil_kaynak (site erişilemedi) |
| K29 | OCCT 8.0.1 ve 8.0.0.p1 tartışmaları | https://github.com/Open-Cascade-SAS/OCCT/discussions/1415 ; https://github.com/Open-Cascade-SAS/OCCT/discussions/1316 | ikincil_kaynak |
| K30 | BRepGraph (OCCT 8.0) | https://dev.opencascade.org/content/brepgraph-new-topology-geometry-graph-coming-occt-80 ; https://github.com/Open-Cascade-SAS/OCCT/discussions/1291 | ikincil_kaynak |
| K31 | Boolean sonuç sırası: indeksli eşleme commit'i ve test güncellemesi (ayna) | https://git.rbts.co/OpenCascade/occt/commits/commit/6da574b52307ccbc04fee3f5a78ca4ad2f6945d5/src/BOPTools/BOPTools.cxx | ikincil_kaynak |
| K32 | SetOffsetOnFace başvuru kılavuzu (7.3+ sürümlerde) | https://dev.opencascade.org/doc/occt-7.3.0/refman/html/class_b_rep_offset___make_offset.html | ikincil_kaynak (varlığı K10 ve K12 ile metin_elde) |
| K33 | iPhone / iPad LiDAR doğruluk çalışmaları | https://geodetski-vestnik.com/arhiv/70/1/47_Yanchuk.pdf ; https://fig.net/resources/proceedings/fig_proceedings/fig2022/ppt/ts03g/TS03G_zaczek-peplinska_kowalska_11458_ppt.pdf ; https://acikerisim.ohu.edu.tr/items/d3d4a920-e7f5-42bf-88a4-5953b585f7a3 ; https://dergipark.org.tr/en/pub/mephoj/issue/80446/1354998 | ikincil_kaynak |
| K34 | Yapısal ışık ve fotogrametri doğruluğu (VDI/VDE 2634, NIST uyarısı, satıcı iddiası) | https://isprs-archives.copernicus.org/articles/XL-5-W8/7/2016/ ; https://isprs-archives.copernicus.org/articles/XLIII-B2-2020/791/2020/ ; https://www.nist.gov/node/1565776 ; https://machexhibition.com/news/3d-high-resolution-scanner/ | ikincil_kaynak |
| K35 | AP203 / AP214 / AP242 farkları | https://mycad.visiativ.com/en/knowledge-center/tutorials/solidworks-tutorials/differences-step-ap203-ap214-ap242-solidworks ; https://www.goengineer.com/blog/solidworks-step-export-ap203-vs-ap214 ; https://takuto-na.github.io/step-standards-explained/ | ikincil_kaynak |
| K36 | Geomagic Design X özellikleri | https://www.cadmicro.com/wp-content/uploads/Geomagic_Design_X_2022.pdf ; https://www.cati.com/?p=123053 | ikincil_kaynak |
| K37 | QuickSurface özellikleri | https://novedge.com/blogs/news/quicksurface-2024-the-ultimate-reverse-engineering-software-for-parametric-design | ikincil_kaynak |
| — | FreeCAD lisansı (LGPL); FreeCAD RE tezgâhındaki diğer araçlar; Analysis Situs işlevlerinin ayrıntısı; paralel Boolean belirlenimciliği; TNaming'in Python'da sağlamlığı; kör deliğin düz tabanı; `DESTEP_Parameters`'ın Python'dan kullanımı | — | dogrulanmadi |
