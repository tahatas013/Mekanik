# Araştırma C: Enjeksiyon kalıbı ve FDM 3B baskı alan paketleri

- Tarih: 2026-11-06 06:19 (sistem saati, `date '+%F %H:%M'`)
- Rol: araştırma alt ajanı (kod yazılmadı, yalnız araştırma)
- Kapsam: açık kaynakla neyin otomatikleşebildiği, neyin insan kararı istediği, neyin yapılamadığı; kaba hesaplar; FDM dilimleyici komut satırları; standartlar.

## 0. Yöntem ve doğrulama etiketleri

- `metin_elde`: Birincil metni okudum. Kaynak ya ham dosyaydı (raw.githubusercontent.com, pypi.org JSON) ya da WebFetch ile github.com sayfası. WebFetch sayfayı küçük bir modelle özetler. O yüzden "metin_elde (WebFetch)" yazan satırlarda bayrak adlarını yeniden denetlemek iyi olur.
- `ikincil_kaynak`: Bilgi WebSearch özetinden geldi, birincil sayfayı açamadım.
- `dogrulanmadi`: Bellekten yazdım ya da yalnız çıkarım yaptım.
- `turetilir`: Bilgi fizik ya da cebirden çıkıyor; türetme raporda gösterildi.
- Erişilemeyen siteler (ağ politikası engelledi): www.orcaslicer.com, wiki.freecad.org, reqrefusion.github.io (FreeCAD wiki aynası), www.mdpi.com, www.ncbi.nlm.nih.gov, solutions.covestro.com. Bu sitelerdeki bilgiler ikincil kaynak olarak işaretlendi. Doğrulamak için bu alan adlarına oturum ağ ayarlarından izin verilmesi gerekir.
- Rapordaki her sayının yanında kaynağı ve etiketi var. Üretici blog sayıları birbiriyle çelişiyor; çelişki olan yerde aralığın tamamı yazıldı.

Terimler (ilk geçtiği yer):
- **Çekme yönü** (pull direction): Kalıbın açıldığı ve parçanın çıktığı eksen.
- **Kalıptan çıkma açısı** (draft): Yüzeyin çekme yönüne göre eğimi.
- **Negatif açı / undercut**: Çekme yönünde parçayı kilitleyen geometri.
- **Ayırma çizgisi / yüzeyi**: Maça (core) ile dişi (cavity) yarılarının buluştuğu çizgi ve yüzey.
- **Sürgü / lifter**: Undercut'ı yanal ya da açılı hareketle serbest bırakan kalıp mekanizmaları.
- **Shut-off**: Çelik çeliğe kapanan yüzey.
- **Cross-WLF**: Sıcaklık, kayma hızı ve basınca bağlı viskozite modeli.
- **Tait pvT**: Basınç, hacim ve sıcaklık arasındaki durum denklemi.

---

## (a) Enjeksiyon kalıbı: otomatikleşebilir / yarı otomatik / yapılamaz

Sınıflar:
- **O (otomatik):** Betik sonucu deterministiktir. İnsan yalnız eşiği ve girdiyi verir.
- **Y (yarı otomatik):** Araç bir öneri üretir, insan onaylar. El kitabındaki "işi yapan onaylamaz" kuralı burada geçerli.
- **X (yapılamaz):** Bugün açık kaynakla güvenilir yapılamıyor. Ticari araç, kalıpçı ya da deneme baskısı gerekir.

Lisans kısaltmaları: OCCT = LGPL-2.1 + Open CASCADE istisnası (`metin_elde`, OCCT_LGPL_EXCEPTION.txt). OCP / CadQuery = Apache-2.0 (`metin_elde`, LICENSE ve PyPI). trimesh = MIT (`metin_elde`). embreex = BSD tarzı lisans (`metin_elde`, PyPI lisans metni). numpy / scipy = BSD (`metin_elde`, PyPI).

| # | Konu | Sınıf | Yöntem | Açık kaynak araç (lisans) | Güvenilirlik | İnsan kararı | Kaynak |
|---|---|---|---|---|---|---|---|
| 1 | Kalıptan çıkma açısı analizi (çekme yönü verilmişse) | O | Yüzeyin UV ızgarasında normal n alınır. Çekme yönü d ile açı ölçülür: draft = 90° − ∠(n, d). İşaret yüzün maça mı dişi mi tarafında olduğunu söyler. | OCCT `BRepLProp_SLProps` (sınıf var, `metin_elde`). Çalışan örnek: FreeCAD DFM Workbench `draft_analyzer.py` (LGPL-2.1, OCP ile). Görselleştirme: Curves WB DraftAnalysis (LGPL-2.1+). Ağ tabanlı: trimesh `face_normals` (MIT). | Yüksek, çünkü geometri deterministik. Eğri yüzeyde sonuç örnekleme sıklığına bağlıdır. | Çekme yönü, en küçük açı eşiği (malzeme ve doku). | DFM WB kaynak kodu (`metin_elde`); Curves WB README/package.xml (`metin_elde`); Curves DraftAnalysis açıklaması (`ikincil_kaynak`, wiki engelli) |
| 2 | Çekme yönü önerisi | Y | Aday yönler denenir: ana eksenler, OBB eksenleri, büyük düzlemsel yüz normalleri. Her aday undercut alanı ve sıfır-draft alanıyla puanlanır. | Hazır açık kaynak araç bulamadım. #1 ve #3 bileşenleriyle kurulabilir. | Orta. Aday listesi dışında kalan bir yön kaçabilir. | Yön seçimi her zaman insanın. | Görünürlük/Gauss haritası literatürü (Chen-Woo vb.) `dogrulanmadi` |
| 3 | Undercut tespiti | O (tespit) | Yüzey noktasından +d ve −d yönlerine ışın atılır. İki yön de parçaya çarparsa nokta "kilitli" sayılır. Kendi yüzeyine çarpmayı ayıklamak için eşik kullanılır. Yüz başına kilitli oran hesaplanır. | DFM WB `undercut_analyzer.py`: OCCT `IntCurvesFace_ShapeIntersector`, UV ızgarası, `self_hit_threshold` (LGPL-2.1). Ağda: trimesh `ray` + embreex hızlandırma. | Orta-yüksek. Seyrek ızgara küçük özellikleri kaçırabilir. Kenarı sıyıran ışınlar yanlış sonuç verebilir. Sonucu ızgara yoğunluğuyla birlikte raporlamak gerekir. | Undercut'ın nasıl çözüleceği: sürgü, lifter ya da tasarım değişikliği. | DFM WB kaynak kodu (`metin_elde`); trimesh `ray/__init__.py` (`metin_elde`) |
| 4 | Et kalınlığı | O | (i) Işın yöntemi: noktadan iç normal yönünde ilk karşı yüzeye olan mesafe. (ii) Küre yöntemi: noktaya teğet en büyük iç küre. | trimesh `proximity.thickness(method='max_sphere' \| 'ray')` (MIT). DFM WB `ray_thickness_analyzer.py` ve `sphere_thickness_analyzer.py` (ışınla başlar, Extrema ile küreyi daraltır). | Işın yöntemi köşe ve eğik duvarda kalınlığı abartabilir; küre yöntemi daha kararlıdır ama yavaştır. Bu kıyas kod okumama dayanan değerlendirmedir (`dogrulanmadi`). | En küçük ve en büyük eşikler malzeme kılavuzundan gelmeli. | trimesh `proximity.py` (`metin_elde`); DFM WB kaynak kodu (`metin_elde`) |
| 5 | İzdüşüm alanı (çekme yönünde) | O | Ağ çekme yönüne dik düzleme izdüşürülür, dış sınır çokgeni çıkarılır, alanı alınır. | trimesh `path.polygons.projected(mesh, normal)` ve `Trimesh.projected` (MIT, shapely BSD-3). B-rep tarafında OCCT `HLRBRep_Algo` dış hattı (sınıf var). | Yüksek. | Yolluk alanının eklenmesi ve deliklerin shut-off olarak düşülüp düşülmeyeceği. | trimesh kaynak kodu (`metin_elde`); OCCT başlık dosyası (`metin_elde`) |
| 6 | Hacim / kütle | O | Hacim B-rep ya da kapalı ağdan hesaplanır. Kütle = ρ·V. | OCCT `BRepGProp` (sınıf var); trimesh `volume` ve `mass_properties`. | Yüksek, katı kapalıysa (watertight). | ρ (yoğunluk) malzeme veri sayfasından gelir. | Kaynak kodlar (`metin_elde`) |
| 7 | Ayırma çizgisi (düzlemsel ya da tek kademeli) | Y | Siluet kenarları bulunur: komşu iki yüzde n·d işaretinin değiştiği kenarlar. Sonra kapalı dış döngü seçilir. | OCCT topoloji gezintisi + `HLRBRep` (LGPL). Algoritma makalelerde var (Nee, Lee vb. 1998–2000); açık kaynak uygulamasını bulamadım. | Orta. Dikey (sıfır-draft) yüz bantlarında siluet belirsizleşir: çizgi bandın altından da üstünden de geçebilir. | Konum, görünür iz, flaş riski, kademeli ayırma. | Makale özetleri (`ikincil_kaynak`) |
| 8 | Ayırma yüzeyi üretimi | Y (düzlemsel, ekstrüzyon) / X (3B serbest, çok kademeli, shut-off'lu) | Ayırma çizgisi çekme yönüne dik olarak dışa doğru çekilir (makalelerdeki klasik yöntem). Gerekirse dolgu yüzeyi kullanılır. | OCCT `BRepPrimAPI_MakePrism` (`dogrulanmadi`), `BRepOffsetAPI_MakeFilling` (sınıf var). Bu işi yapan açık kaynak araç bulunamadı. | Düzlemsel durumda iyi. Karmaşık durumda yüzey dikiş hatası ve yüzey kalitesi sorunu çıkar; endüstriyel kalitede değildir. | Her durumda onay gerekir. Karmaşık yüzeyi kalıpçı tasarlar. | Arama sonucu: açık kaynak depo yok (`ikincil_kaynak`) |
| 9 | Maça/dişi ayırma | Y | Kalıp bloğundan, çekme payıyla ölçeklenmiş parça çıkarılır. Kalan blok ayırma yüzeyiyle bölünür. | OCCT `BRepAlgoAPI_Cut` (`dogrulanmadi`), `BRepAlgoAPI_Splitter` (sınıf var); CadQuery `split` (`dogrulanmadi`). | Ayırma yüzeyi düzgünse yüksek. Yüzey kusurluysa boolean işlemi çöker ya da hatalı katı üretir. | Blok ölçüsü, çekme payı, shut-off'lar. | OCCT başlık dosyası (`metin_elde`) |
| 10 | Çekme payı (çekme/büzülme) uygulaması | O (işlem) / insan (değer) | Parça (1+S) oranında ölçeklenir. Lif katkılı malzemede pay eksene göre farklıdır. | OCCT `gp_GTrsf`, trimesh `apply_scale` (`dogrulanmadi`). | İşlemin kendisi kesin; değer belirsiz. | S değeri malzeme veri sayfasından ya da ölçümden gelir. Ölçüm yöntemi ISO 294-4 (paralı, `dogrulanmadi`). | — |
| 11 | Sürgü / lifter ihtiyacının tespiti | O (tespit) | #3'te kilitli kalan nokta için yan yönler denenir; nokta bir yan yönde serbest kalıyorsa sürgüyle çözülebilir sayılır. | DFM WB `point_released_by_side_action` ve `get_side_action_draft`. Yan yönleri kullanıcı verir. | Orta. Yön adaylarını insan verir. | Yan yön adayları. | DFM WB kaynak kodu (`metin_elde`) |
| 12 | Sürgü / lifter / maça tasarımı (gövde, açılı pim, kilitleme, strok, soğutma) | X | — | Açık kaynak tasarım aracı bulamadım. Standart parçalar katalogdan seçilir (bkz. #19). | — | Tamamen kalıpçı ya da tasarım mühendisi kararı. | Arama: yalnız ticari araçlar (SolidWorks Mold Tools, NX) (`ikincil_kaynak`) |
| 13 | İtici yerleşimi | Y (kural tabanlı öneri) / X (sonuç) | Düz yüzlere ve kaburga diplerine ızgara önerisi; çakışma (kanal, cıvata) OCCT ile denetlenir. | Hazır araç yok. Çakışma denetimi `BRepExtrema_DistShapeShape` (sınıf var). | Öneri düzeyinde. İtme kuvveti ve iz kabulü insan kararıdır. | Konum, çap; pim standardı ISO 6751 / 8694. | `dogrulanmadi` (araç yokluğu arama sonucuna dayanır) |
| 14 | Yolluk ve giriş yeri | X (güvenilir) / Y (eleme) | Aday girişler akış boyu / et oranıyla elenebilir (bkz. (b)). | Ticari araçlarda "gate location" analizi var (`dogrulanmadi`). Açık kaynakta yok. | Eleme düzeyinde. | Giriş yeri, yolluk tipi (sıcak ya da soğuk). | `dogrulanmadi` |
| 15 | Soğutma kanalı yerleşimi | Y | Kural tabanlı yerleşim: kanal çapı D; kanal merkezi kalıp yüzeyinden yaklaşık 2–2,5·D; kanallar arası adım 3–5·D. Ardından çakışma ve en az çelik et denetimi yapılır. | OCCT ile geometri ve çakışma; hazır yerleştirici yok. | Kural düzeyinde. Sayılar kaynaklar arasında çelişiyor: yüzey mesafesi 1,5–2,5·D, adım 2–3·D ya da 3–5·D. | Devre düzeni, bağlantılar, conta ve tapa yerleri. | Autodesk Moldflow yardım sayfası "2–2,5 kat" (`ikincil_kaynak`); üretici bloglarındaki aralıklar (`ikincil_kaynak`) |
| 16 | Kalıp ısıl analizi (iletim, kararlı ya da geçici) | Y | 3B ısı iletimi çözülür. Kanal duvarına ısı taşınım katsayısı (Dittus-Boelter vb.) verilir, kalıp yüzeyine polimerden gelen ısı akısı yazılır. | FEniCSx/dolfinx (LGPL-3.0, `metin_elde`), Elmer FEM (GPL-2 / LGPL-2.1, `metin_elde` WebFetch; hangi bileşenin hangi lisansta olduğu belirtilmemiş), CalculiX (GPL, `dogrulanmadi`). Ağ üretimi: gmsh (GPL-2+, `metin_elde` PyPI). | Isı iletimi çözücüleri olgundur. Zayıf halka sınır koşullarıdır: polimer tarafındaki ısı akısı basitleştirilir. Doğrulama gerekir. | Sınır koşulları, soğutucu debisi ve sıcaklığı. Re ≥ 10000 hedefi (bkz. (b)). | Lisans dosyaları (`metin_elde`); Autodesk Re önerisi (`ikincil_kaynak`) |
| 17 | Dolum (ve ütüleme / soğuma) simülasyonu | Y (araştırma düzeyi) / X (endüstriyel karar) | 3B, sıkıştırılabilir, izotermal olmayan, laminer iki fazlı (polimer + hava) akış; Tait durum denklemi ve Cross-WLF viskozitesi. | **openInjMoldSim** (GPL-3.0, OpenFOAM 7 gerekir; sürüm v7.2). README kendi sınırını şöyle yazıyor: "Currently, the simulation is prohibitively inconvenient for typical industrial use but it can be helpful in research". Çatallar: kristalleşme (openInjMoldDyMSimCr), amorf soğuma hızı (openInjMoldDyMSimAmClr); lif yönelimi (openInjMoldSimF). OpenFOAM: GPL-3 (`metin_elde`, COPYING). | Pedro vd. 2020 doğrulaması Moldex3D'ye karşı yapılmış, yani ticari yazılıma kıyas; deneye kıyas değil. Dikdörtgen boşluk ve çekme çubuğu örneklerinde akış cephesi, basınç, hız ve sıcaklık alanlarında "iyi uyum" bildirilmiş. Hız iddiası iki kaynakta çelişiyor: biri "benzer maliyet" diyor, diğeri "Moldex3D aynı çekirdek sayısında 10 kat hızlı" diyor. Krebelj vd. (Polymers 2021, HDPE) basınç gelişimini deneyle kıyaslamış. | Ağ, sınır koşulları, sayısal kararlılık ayarları (`maxSolidCo`, `pAuxRlx`), malzeme verisi. Kalıp ya da parça kararı bu sonuca dayandırılmamalı. | README, VERSION.md, LICENSE.md (`metin_elde`); doğrulama özetleri (`ikincil_kaynak`, mdpi/ncbi engelli) |
| 17a | Dolum simülasyonu için malzeme verisi | insan / tedarik | openInjMoldSim örneğinin istediği veriler: 13 katsayılı iki bölgeli Tait (b1m…b4m, b1s…b4s, b5…b9), 7 Cross-WLF parametresi (n, τ*, D1, D2, D3, A1, A2), sayısal sınırlar (etaMin, etaMax, TnoFlow), sıcaklığa bağlı cp tablosu, sıcaklık ve basınca bağlı ısıl iletkenlik tablosu. | Açık ve serbest malzeme veritabanı bulamadım. Ticari araçlar kendi veritabanıyla gelir. Kalan seçenekler: makalelerde yayımlanmış parametreler ya da laboratuvar ölçümü (reometre, pvT cihazı). | Veri yoksa simülasyon anlamsızdır. | Veri kaynağı her zaman etiketlenmeli. | Örnek `thermophysicalProperties.poly` (`metin_elde`); Cross-WLF tanımı (`ikincil_kaynak`) |
| 18 | Çarpılma, lif yönelimi, artık gerilme, çöküntü (sink) tahmini | X | — | Olgun açık kaynak araç yok. openInjMoldSimF'te lif yönelimi araştırma düzeyinde var. Moldflow'da Midplane, Dual Domain ve 3B ağlarda çarpılma analizi var (ticari). | — | — | Autodesk yardım sayfaları (`ikincil_kaynak`) |
| 19 | Kalıp standart parçaları (plakalar, pimler, burçlar) | Y | Katalogdan STEP indirilip yerleştirilir. | Meusburger: CAD kütüphanesi ücretsiz; STEP, IGES ve Parasolid sunuluyor. DME: bazı dosyalar girişsiz, tam kütüphane PARTcommunity hesabıyla. HASCO: Mart 2026 duyurusuna göre tüm CAD verisi STEP olarak indirilebiliyor. Hepsinin lisansı üreticiye ait; açık lisans değil. | Veri güvenilir; yeniden dağıtım hakkı belirsiz. | Seçim ve yerleşim. STEP dosyaları pakete gömülmemeli; kullanıcı kendisi indirmeli. | Üretici sayfaları (`ikincil_kaynak`; kullanım koşulları sayfasını okuyamadım) |

---

## (b) Kalıp kaba hesapları

Bu formüller ön boyutlandırma içindir. Sonuç kart ya da karar girdisidir; kesin değer değildir. Her girdi kaynak etiketi taşımalı (`olcu`, `standart`, `karar`, `turetilir`, `varsayim`).

| # | Hesap | Formül | Girdiler (kaynakları) | Geçerlilik alanı ve sınırlar | Kaynak |
|---|---|---|---|---|---|
| B1 | Kapama kuvveti | F = p_boşluk · A_izd · k. Birim dönüşümü: F[kN] = p[bar] · A[cm²] / 100. Türetme: 1 bar · 1 cm² = 10⁵ Pa · 10⁻⁴ m² = 10 N. | A_izd = parça + yolluk izdüşüm alanı, tüm gözler dahil (geometriden, `turetilir`). p_boşluk = simülasyon, malzeme verisi ya da `varsayim`. Veri yoksa "yol gösterici değer" 400 bar. k = güvenlik çarpanı, kaynaklarda %10–20 ya da 1,1–1,3. | Kaba ön seçim. Malzemeler arası basınç ihtiyacı 3–5 kat değişebilir (plasticsengineering.org). Geometri, giriş ve et etkisini görmez. Alternatif kural: malzemeye göre 2–8 ton/inç² (aynı kaynak); bu sayı da kaynaktan kaynağa çelişiyor (PP/PE için 1,5–2,0 ile 2–3). Delik alanı ancak çelik çeliğe kapanıyorsa (shut-off) düşülür; bu kural tek kaynaktan geliyor. | plasticsengineering.org (SPE) 2024; Keyence formül sayfası; firstmold, zetarmold, huarong (hepsi `ikincil_kaynak`); dönüşüm `turetilir` |
| B2 | Akış boyu / et oranı | L/t = (girişten en uzak noktaya akış yolu) / nominal et. | L: ağ üzerinde jeodezik mesafe; ağ kenar grafiği üzerinde `scipy.sparse.csgraph.dijkstra` (`turetilir`). t: #4 et kalınlığı analizi. Sınır değer: reçine üreticisinin spiral akış verisi. | Yalnız kıyas ve eleme için. Sınır değer basınca, sıcaklığa ve dereceye (grade) bağlıdır. Erişebildiğim tek somut değer ikinci elden: ABS için 1 mm ette 100–200 mm akış boyu ("Molding Simulation: Theory and Practice"tan alıntı). Tablo sayılarını kendi kaynağından almak gerekir. | findoutaboutplastics.com; jtrm.polman-bandung.ac.id (`ikincil_kaynak`) |
| B3 | Soğuma süresi (levha) | Ortalama sıcaklığa göre: t_s = s² / (π²·α) · ln[(8/π²) · (T_E − T_K) / (T_A − T_K)]. Merkez sıcaklığına göre: ln içindeki katsayı 8/π² yerine 4/π. Burada α = k / (ρ·c_p). | s: toplam et (iki yüzden soğuma), en kalın bölge. α (ya da k, ρ, c_p), T_E (eriyik), T_K (kalıp yüzeyi), T_A (atma sıcaklığı): hepsi malzeme veri sayfasından. | Varsayımlar: sonsuz levha, iki yüzde sabit kalıp sıcaklığı, sabit özellikler, Fourier serisinin ilk terimi, kristalleşme gizli ısısı yok sayılır. Kaynaklar katsayıda çelişiyor: aPriori paydada 2π kullanıyor (π² yerine). Bir IMechE B (2003) makalesi, yaygın soğuma formüllerinin çoğunda hata olduğunu bildiriyor. Bu yüzden formül türetmeden alınmalı ve tek bir kaynağa yaslanmamalı. | 1B geçici iletim serisi (`turetilir`: merkez ilk terim katsayısı 4/π, ortalama 8/π²); Skill-Lync, aPriori, RJG, IMechE 2003 (`ikincil_kaynak`) |
| B4 | Çevrim süresi | t_çevrim ≈ t_dolum + t_ütüleme + t_soğuma + t_açma-kapama-atma. | B3 ve makine verisi (`varsayim` ya da makine kataloğu). | Kaba. Soğuma çevrimin %60–80'i kadar olabilir (Skill-Lync). | Skill-Lync (`ikincil_kaynak`) |
| B5 | Soğutma kanalı debisi | Re = ρ·v·D / μ. Hedef Re = 10000 için Q = Re · μ · π · D / (4ρ). | D, soğutucunun ρ ve μ değerleri (sıcaklığa bağlı; tablodan). | Autodesk: Re ≥ 10000 önerilir ve en az değer olarak kullanılır; 10000'in çok üstüne çıkmak gerekmez; 4000 altı laminer olabilir. Diğer kaynaklarda türbülans eşiği 3000 ya da 5000. Debiyi iki katına çıkarmak pompa gücünü 8 katına çıkarır. | Autodesk Moldflow yardım sayfaları (`ikincil_kaynak`); debi formülü `turetilir` |
| B6 | Soğutmanın çekmesi gereken ısı | Q̇ ≈ m_atış · [c_p · (T_E − T_A) (+ yarı kristalinde gizli ısı)] / t_s. | m_atış (#6), c_p, T değerleri (veri sayfası). | Kaba. Kalıptan çevreye kaybı ve yolluğu kabaca hesaba katar. | `turetilir` |
| B7 | Kalıp sınıfı / ömür | SPI sınıfları: 101 (≥ 1 milyon çevrim) … 105 (prototip, yaklaşık 500 çevrim). | Müşteri ve karar. | Resmi metni bulamadım; çevrim sınırları kaynaklarda çelişiyor. Örnek: 104 için "≤ 100.000" ile "100.000–300.000". | Fictiv, Boyd, Texas Injection Molding, Scribd kopyası (`ikincil_kaynak`) |

Not: Yaygın tasarım kılavuzlarından erişebildiğim sayılar (hepsi `ikincil_kaynak`):
- Protolabs: "her 1 inç derinliğe 1° draft" pratik kuralı.
- Protolabs: ABS için önerilen et 0,045–0,140 inç; PP için 0,64–3,81 mm.
- Kaburga kalınlığı: duvarın %50–60'ı (≤ %60).
- Doku için ek draft gerekir. Sık anılan "0,001 inç doku derinliği başına X°" oranını doğrulayamadım.

Covestro "Part and Mold Design" ve DuPont "General Design Principles (Module I)" kılavuzları var ama PDF'lerini açamadım (Covestro engelli; DuPont kopyası üçüncü taraf sitesinde). İçlerindeki formül ve tablolar bu raporda kullanılmadı.

Uyarı: FreeCAD DFM Workbench'in hazır eşik değerleri kaynak göstermiyor. `plastic_injection_molding.yaml` dosyasında Default için draft hedef 1,0 / sınır 0,5 ve et 1,0–4,0 / 0,5–5,0 var. ABS değerleri (1,14–3,56) Protolabs aralığıyla örtüşüyor ama dosyada kaynak yazılı değil. "Kaynaksız sayı yok" kuralı gereği bu değerler kataloğa olduğu gibi alınmamalı.

---

## (c) FDM: dilimleyici komut satırları ve kontroller

### c1. Dilimleyici CLI tablosu

| | OrcaSlicer | PrusaSlicer | CuraEngine |
|---|---|---|---|
| Lisans | AGPL-3.0 (`metin_elde`, LICENSE.txt + README). İsteğe bağlı Bambu ağ eklentisi özgür değil (README). | AGPL-3.0 (`metin_elde`, LICENSE) | AGPL-3.0 (`metin_elde`, LICENSE). Yazıcı tanım dosyaları (`fdmprinter.def.json` vb.) Cura deposunda, LGPL-3.0 (`metin_elde`). |
| Son sürüm (github.com sayfası; yıl görünmüyor) | v2.4.2, 7 Temmuz (`metin_elde` WebFetch) | 2.9.7, 2 Kasım (`metin_elde` WebFetch). Ubuntu 24.04 deposunda 2.7.2 var (`metin_elde` manpage). | Cura 5.14.0, 5 Kasım (`metin_elde` WebFetch). CuraEngine'in GitHub "latest" etiketi v2.7.0 gösteriyor; bu eski ve yanıltıcı görünüyor. |
| Örnek komut | `orca-slicer model.3mf --load-settings "process.json;printer.json" --load-filaments filament.json --arrange 1 --slice 0 --export-3mf out.3mf` (wiki örneği) | `prusa-slicer --load profil.ini --export-gcode -o out.gcode model.stl` (manpage bayrakları; sıralama `ikincil_kaynak`) | `CuraEngine slice -j fdmprinter.def.json -s anahtar=değer -l model.stl -o out.gcode` (kaynak kodundaki `-j -s -l -o -e -g -v -m -d` seçenekleri) |
| G-code | Var; `--outputdir` ile çıkış dizini seçilir. | `--export-gcode` (`-g`). Ayrıca `--export-3mf/stl/amf/obj`, `--export-sla`. | `-o` ile G-code dosyası. |
| Süre ve filament tahmini | `--export-statistics`: plaka başına `plate_N.statistics.json`; içinde süre, filament, özellik toplamları, katman ve nesne dökümü var (`metin_elde` WebFetch, cli_misc). | G-code sonundaki yorum satırlarında: `; estimated printing time (normal mode) = …` (forum, `ikincil_kaynak`). `--info` süre vermez, yalnız model bilgisi verir. | Komut satırı modunda günlüğe yalnız "Total print time" yazılır (`metin_elde`, CommandLine.cpp `sendPrintInformation`). Filament miktarı komut satırında raporlanmıyor görünüyor. |
| Profil | JSON (process, machine, filament). Yapı hacmi anahtarları: `printable_area`, `printable_height` (`metin_elde`, Creality profili). CLI'da hiç açılmayan 43 anahtar var (wiki). | INI (`--load`, birden çok kez verilebilir; `--datadir`). Yapı hacmi anahtarları `bed_shape`, `max_print_height` (`dogrulanmadi`). | `def.json` kalıtım zinciri. Yapı hacmi: `machine_width`, `machine_depth`, `machine_height`. Destek açısı: `support_angle`, varsayılan 50° (`metin_elde`). Eksik ayarlar `-s` ile tek tek verilmeli; forumda eksik anahtar hatası bildirilmiş (`ikincil_kaynak`). |
| Ek eylemler | `--info`, `--export-settings`, `--export-stls`, `--no-check`, `--normative-check` (varsayılan açık), `--mstpp` (plaka başına en uzun dilimleme süresi, varsayılan 300 s), `--mtcpp` (plaka başına en çok üçgen, varsayılan 1.000.000) | `--info`, `--split` (ayrık parçaları ayırır), `--center`, `--rotate`, `--scale-to-fit`, `--dont-arrange`, `--loglevel`, `--threads` (varsayılan 4) | `-e<n>` (ekstrüder), `--next` (sıralı dilimleme) |
| Ubuntu'da başsız (headless) çalışma | Wiki "headless çalışır" diyor. Bir üçüncü taraf paket (orca-mcp, PyPI) bazı derlemelerin CLI modunda bile ekran bağlamı istediğini, bu yüzden `xvfb-run -a` önerdiğini yazıyor (`metin_elde`, PyPI açıklaması). Küçük resim (thumbnail) üretimi OpenGL/GLFW istiyor (`ikincil_kaynak`). Kurulum: Flathub ya da AppImage (README). | Komut satırı var. Ekransız Docker'da GTK başlatma hatası bildirilmiş; ekransız çalışan Docker imajları da var (`ikincil_kaynak`). Ubuntu deb paketi var. | Yalnız komut satırı olan C++ programı, GUI bağımlılığı yok (kaynak kodu). Derleme: Conan ≥ 2.7, CMake ≥ 3.23, gcc ≥ 13 (`metin_elde`, wiki). Cura geliştiricisine göre CLI "temelde test amaçlı" (`ikincil_kaynak`). |
| Değerlendirme | En zengin CLI ve yapılandırılmış istatistik çıktısı. Sürümler arası bayrak değişimi riski var. | Kararlı, belgelenmiş bayraklar. Süre için G-code ayrıştırmak gerekir. | Tümleştirmesi en zor olanı: tanım zinciri ve ayar eksikleri. Başsız çalışma için en temiz seçenek. |

AGPL notu: Dilimleyiciyi ayrı süreç (subprocess) olarak çağırmak aracın kendi lisansını etkilemez görünüyor. İkili dosyayı paketle birlikte dağıtmak ya da değiştirip ağ üzerinden sunmak AGPL yükümlülüğü doğurur. Bu bir hukuki yorumdur, `dogrulanmadi`, ve Taha onayı ister. Pratik öneri: dilimleyici paketin içine konmaz; `surec doktor` sürümü denetler ve kullanıcı kendisi kurar.

### c2. Modelden bağımsız FDM kontrolleri (betik)

Eşik değerleri profilden ya da karardan gelmeli: nozul çapı, çizgi genişliği, yapı hacmi. Genel kılavuz sayıları ancak `varsayim` etiketiyle kullanılmalı.

| Kontrol | Yöntem | Araç (lisans) | Eşik kaynağı | Güvenilirlik |
|---|---|---|---|---|
| Çıkıntı (overhang) | Yüz normalinin −Z (baskı yönü) ile açısı ölçülür; açı > 90° + eşik ise destek adayıdır. | trimesh `face_normals`; DFM WB `overhang_analyzer.py` (LGPL-2.1) | Protolabs ağı ve Hubs: "45°'nin üstünden kaçının" (`ikincil_kaynak`). Cura varsayılanı `support_angle` = 50° (`metin_elde`). Profilden alınmalı. | Yüksek (geometri). Köprüler ve kendini taşıyan kısa çıkıntılar yanlış alarm üretir. |
| Destek hacmi | Kesin değer dilimleyiciden alınır: Orca `--export-statistics` özellik toplamları. Kaba değer: çıkıntı yüzünden tablaya inen prizma hacmi. | Orca CLI; trimesh `ray` | — | Dilimleyiciden alınan değer kesin; kaba yöntem yaklaşık. |
| En ince duvar | Et kalınlığı örneklenir (ışın ya da küre) ve en küçük değer alınır. | trimesh `proximity.thickness`; DFM WB ray/sphere analizcileri | Protolabs ağı: ≥ 0,8 mm (`ikincil_kaynak`). Daha iyisi: k × çizgi genişliği; k bir `karar`, çizgi genişliği profilden. | Orta-yüksek (bkz. (a) #4). |
| Tabla sığması | Yerleşim ve yönlendirme sonrası eksen hizalı sınır kutusu, yapı hacmiyle kıyaslanır. | trimesh `bounds`; profil anahtarları (c1); Orca `--normative-check` | Profil (yazıcı verisi) | Yüksek. Dikdörtgen olmayan tablada çokgen içinde-mi testi gerekir (shapely). |
| Tabla teması | z_min + ε düzleminde kesit alınır, kesit çokgeninin alanı ölçülür. Ayrıca normali −Z'ye yakın yüzlerin alanı toplanır. | trimesh `section`, shapely; DFM WB `bed_contact_analyzer.py` | ε ve en küçük alan: `karar` | Yüksek. Devrilme riski için kesit alanı / yükseklik oranı ayrıca bakılabilir. |
| Ayrık katı | Bağlı bileşen sayısı. | trimesh `body_count`, `split`; PrusaSlicer `--split` | 1 beklenir, değilse kart açılır. | Yüksek. |
| Kapalılık / manifold | Su geçirmezlik, sarım tutarlılığı, hacim geçerliliği. | trimesh `is_watertight`, `is_winding_consistent`, `is_volume`; manifold3d (Apache-2.0) | — | Yüksek. |
| Köprü açıklığı | Destek almayan yatay yüzlerin açıklığı ölçülür. | DFM WB `bridge_span_analyzer.py` | Kaynaklar çelişiyor: Xometry > 5 mm için destek önerir, EDUHK sunumu 10–20 mm diyor (`ikincil_kaynak`). Yazıcı ve malzemeyle sınanmalı. | Orta. |
| Basamak etkisi (cusp) | Eğik yüzlerde katman kalınlığına bağlı basamak yüksekliği. | DFM WB `cusp_analyzer.py` | Katman kalınlığı profilden. | Orta. |

Açık kaynak FDM DFM referansı: FreeCAD DFM Workbench. FDM ve enjeksiyon kurallarını OCP üzerinde uygular. LGPL-2.1, FreeCAD 1.1+ resmi destek, depoda 396 commit ve 86 yıldız (`metin_elde` WebFetch). Erken geliştirme aşamasında bir üniversite projesi (`ikincil_kaynak`). Yöntem başvurusu olarak değerli. Bağımlılık olarak alınırsa FreeCAD gerekir; kod lisansı LGPL olduğu için kopyalamak yerine yöntemi yeniden yazmak daha temiz olur.

---

## (d) Standartlar

| No | Konu | Paralı / açık | Açık karşılık ya da not | Kaynak |
|---|---|---|---|---|
| ISO 20457:2018 | Plastik kalıplanmış parçalar: toleranslar ve kabul koşulları | Paralı. Örnek fiyatlar: SIS'te PDF 1.910 SEK; Çek bayisinde 183,53 €. | Açık karşılık yok. Almanca uyarlaması DIN ISO 20457:2021-06 (Austrian Standards'ta 122,03 €). | dinmedia, SIS, technickenormy, austrian-standards (`ikincil_kaynak`) |
| DIN 16742:2013-10 | Aynı konu: TG1–TG9 tolerans grupları | Paralı ve geri çekilmiş; yerine DIN ISO 20457 geldi. | Xometry'nin DIN 16742 tablo PDF'i dolaşımda (lisans durumu belirsiz). | dinmedia, hexagon.de (`ikincil_kaynak`) |
| DIN 16901 | Eski plastik tolerans standardı | Geri çekildi (2009). Yerine DIN 16742 öneriliyor. | — | hexagon.de, DIN (`ikincil_kaynak`) |
| SPI kalıp sınıfları 101–105 | Kalıp yapım sınıfı ve ömrü | Resmi ücretsiz kopya bulunamadı; sahibi Plastics Industry Association. | Üretici özetleri var ama sayıları çelişiyor (bkz. B7). | `ikincil_kaynak` |
| ISO 6751:2011 | Silindirik başlı itici pimler | Paralı | Üretici katalogları (HASCO, Meusburger, DME) | saiglobal, technickenormy (`ikincil_kaynak`) |
| ISO 8694 | Kademeli itici pimler | Paralı (1998 baskısı geri çekildi, 2011 baskısı var) | Katalog | `ikincil_kaynak` |
| ISO 8405:2013 | İtici burçlar | Paralı | Katalog | `ikincil_kaynak` |
| ISO 10072:2004 | Yolluk burçları | Paralı | Katalog | `ikincil_kaynak` |
| ISO 10907-1:2008 / -2:2007 | Merkezleme halkaları | Paralı | Katalog | `ikincil_kaynak` |
| ISO 8404 (2021) | Açılı pimler (sürgü) | Paralı | Katalog | `ikincil_kaynak` |
| ISO 16915 | Yolluk çekiciler | Paralı | Katalog | `ikincil_kaynak` |
| ISO 12165 | Kalıp bileşenleri terim ve simgeleri | Paralı | — | `ikincil_kaynak` |
| ISO 294-4 | Kalıplama çekmesinin ölçümü | Paralı | Malzeme veri sayfasındaki çekme değerleri | `dogrulanmadi` |
| VDI 3400 / SPI yüzey sınıfları (A-1…D-3) | Kalıp yüzeyi ve doku | Paralı ya da üretici yayını | Doku üreticisi katalogları | `dogrulanmadi` |
| ISO/ASTM 52900:2021 | Eklemeli imalat: temel ilkeler ve terimler | Paralı (EVS listesi: 15.12.2021'den beri geçerli) | Terimler için üretici kılavuzları | evs.ee (`ikincil_kaynak`) |
| ISO/ASTM 52910:2018 | Eklemeli imalat tasarımı: gereksinimler, kılavuz, öneriler | Paralı (1. baskı 2018-07). Kapsam notu: "sürece ya da malzemeye özgü veri içermez". DIS 52910:2022 taslağı terk edilmiş olabilir. | Protolabs / Hubs FDM kılavuzları (`ikincil_kaynak`), yazıcı üreticisi profilleri | scc-ccn, technickenormy, genorma (`ikincil_kaynak`) |
| ISO/ASTM 52902 (2019 → 2023) | Test parçaları: geometrik yetenek değerlendirmesi | Paralı | NIST AM test parçası (Moylan vd., SFF 2012 ve J. Res. NIST 2014). Tasarımı ağırlıklı olarak metal sistemler için; açık CAD dosyasını doğrulayamadım. | nist.gov, nimonik (`ikincil_kaynak`) |
| ISO/ASTM 52903-1:2020 (EN 2021) | Plastik malzeme ekstrüzyonu: besleme malzemesi | Paralı (örnek: 70 € İngilizce PDF; 6 sayfa). Bir listede "geri çekildi, yerine yok" diye görünüyor; çelişkili. | Filament üreticisi teknik veri sayfaları | sis.se, en-standard.eu, standards.govt.nz (`ikincil_kaynak`) |
| 3MF Core Specification 1.4.0 | Baskı dosya biçimi | Açık (BSD-2-Clause) | Kendisi açık; lib3mf de BSD tarzı lisanslı. | GitHub 3MFConsortium (`metin_elde`) |
| ISO/ASTM 52915 (AMF) | Baskı dosya biçimi | Paralı | 3MF (açık) | `dogrulanmadi` |

---

## (e) Dürüst özet

1. **Parça analizi açık kaynakla bugün yapılabilir.** Çekme yönü verildiğinde draft, undercut tespiti, et kalınlığı, izdüşüm alanı ve hacim/kütle OCCT/OCP ve trimesh(+embreex) ile deterministik olarak hesaplanır. Lisanslar uyumlu: LGPL-2.1+istisna, Apache-2.0, MIT, BSD. FreeCAD DFM Workbench aynı yöntemleri OCP ile uyguluyor, iyi bir yöntem başvurusu. Ancak eşik değerleri kaynaksız; kataloğa olduğu gibi alınmamalı.
2. **Kalıbın kendisi büyük ölçüde insan işi.** Basit (düzlemsel) ayırma çizgisi, yüzeyi ve maça/dişi bölme yarı otomatik yapılabilir; her adım onay ister. 3B, kademeli ya da shut-off'lu ayırma yüzeyi, sürgü/lifter/itici tasarımı ve giriş yeri seçimi için olgun açık kaynak araç bulamadım. Paket bunları ancak "tespit + soru ağacı + kart" olarak destekleyebilir.
3. **Dolum simülasyonu endüstriyel karar için hazır değil.** openInjMoldSim (GPL-3, OpenFOAM 7) kendi README'sinde "tipik endüstriyel kullanım için aşırı zahmetli, araştırmada yararlı" diyor. Doğrulaması Moldex3D'ye karşı yapılmış. Malzeme verisi (13 Tait + 7 Cross-WLF parametresi ve tablolar) açık ve serbest bir kaynaktan bulunamıyor. Çarpılma ve lif yönelimi için açık kaynakta olgun seçenek yok. Ticari araçla aradaki fark çözücüden çok şunlarda: malzeme veritabanı, çarpılma/ütüleme/soğuma zinciri, kullanılabilirlik ve doğrulama birikimi (son kısım `dogrulanmadi` değerlendirme).
4. **Kaba hesaplar yapılabilir ama girdileri zayıf.** Kapama kuvveti (p·A), L/t ve levha soğuma formülü türetilebilir ve betiğe yazılabilir. Kritik girdiler (boşluk basıncı, L/t sınırı, α, atma sıcaklığı) malzeme veri sayfasından gelmeli. Erişebildiğim sayıların çoğu ikincil kaynak ve birbiriyle çelişiyor. Soğuma formülünün katsayısı bile kaynaklar arasında farklı (π² ve 2π).
5. **FDM tarafı daha olgun.** Üç dilimleyici de AGPL-3.0 ve komut satırıyla G-code üretiyor. OrcaSlicer yapılandırılmış süre/filament istatistiği veriyor; PrusaSlicer'da süre G-code yorumundan okunuyor; CuraEngine komut satırında yalnız süreyi günlüğe yazıyor. Ubuntu'da başsız çalışma CuraEngine için en temiz seçenek. Orca ve Prusa'da bazı derlemeler `xvfb-run` isteyebilir; bu yerelde denenmeli. Geometri kontrolleri (çıkıntı, ince duvar, tabla, temas, ayrık katı, kapalılık) trimesh ile kolay. Eşikler yazıcı profilinden ya da karardan alınmalı.
6. **Standartların neredeyse hepsi paralı.** Bunlar: ISO 20457, ISO kalıp bileşen standartları, ISO/ASTM 529xx. SPI sınıflarının resmi ücretsiz metni bulunamadı. Açık karşılıklar sınırlı: 3MF (BSD-2), NIST test parçası makalesi, üretici kılavuzları ve katalogları (ücretsiz ama özel lisanslı). Kural kataloğuna standart maddesi girecekse, madde numarası ancak standart satın alınıp okunduktan sonra yazılabilir. Aksi halde `varsayim` etiketiyle girer ve kart açılır.

Önerilen ilk kartlar (proje mühendisinin kararına):
- S: Malzeme verisi kaynağı (Cross-WLF / Tait / α / atma sıcaklığı) nereden gelecek?
- S: ISO 20457 ve ISO/ASTM 52910 satın alınacak mı?
- S: Dilimleyici ikilileri pakete gömülecek mi, kullanıcı mı kuracak? (AGPL)
- S: Engelli alan adlarına (orcaslicer.com, wiki.freecad.org, mdpi.com, ncbi, covestro) doğrulama için ağ izni verilecek mi?

---

## (f) Kaynak listesi

| # | URL | Ne için | Durum |
|---|---|---|---|
| 1 | https://raw.githubusercontent.com/krebeljk/openInjMoldSim/master/README.md | openInjMoldSim yetenek, sınır, OpenFOAM 7 | metin_elde |
| 2 | https://raw.githubusercontent.com/krebeljk/openInjMoldSim/master/LICENSE.md | GPL-3.0 | metin_elde |
| 3 | https://raw.githubusercontent.com/krebeljk/openInjMoldSim/master/VERSION.md | v7.2 değişiklikleri | metin_elde |
| 4 | https://raw.githubusercontent.com/krebeljk/openInjMoldSim/master/tutorials/demo/dogbone/constant/thermophysicalProperties.poly | Tait ve Cross-WLF girdileri | metin_elde |
| 5 | https://github.com/krebeljk/openInjMoldSim | 473 commit, 132 yıldız, GPL-3.0 | metin_elde (WebFetch) |
| 6 | https://repositorium.sdum.uminho.pt/handle/1822/65864 ; doi:10.3390/fluids5020084 | Pedro vd. 2020 doğrulama | ikincil_kaynak |
| 7 | https://www.mdpi.com/2073-4360/13/1/138 | Krebelj vd. HDPE kristalleşme | ikincil_kaynak (site engelli) |
| 8 | https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-dev/master/COPYING | OpenFOAM GPL-3 | metin_elde |
| 9 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/master/OCCT_LGPL_EXCEPTION.txt | OCCT lisans istisnası | metin_elde |
| 10 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_0/src/… (IntCurvesFace_ShapeIntersector, BRepOffsetAPI_DraftAngle, HLRBRep_Algo, BRepAlgoAPI_Splitter, BRepGProp, BRepExtrema_DistShapeShape, BRepOffsetAPI_MakeFilling, BRepLProp_SLProps, BRepMesh_IncrementalMesh) | OCCT sınıflarının varlığı | metin_elde |
| 11 | https://raw.githubusercontent.com/CadQuery/OCP/master/LICENSE ; https://raw.githubusercontent.com/CadQuery/cadquery/master/LICENSE | Apache-2.0 | metin_elde |
| 12 | https://raw.githubusercontent.com/mikedh/trimesh/main/LICENSE.md ; …/trimesh/proximity.py ; …/trimesh/path/polygons.py ; …/trimesh/ray/__init__.py ; …/trimesh/base.py | MIT; thickness, projected, ray, body_count/split/is_watertight | metin_elde |
| 13 | https://pypi.org/pypi/{embreex,trimesh,manifold3d,pymeshlab,gmsh,cadquery,cadquery-ocp,shapely,rtree,scipy,numpy,meshio,pyvista}/json | Lisans ve sürüm metaverisi | metin_elde |
| 14 | https://raw.githubusercontent.com/ryankembrey/FreeCAD-DFM-Workbench/main/README.md ; …/LICENSE ; …/freecad/DFM/core/analyzers/*.py ; …/core/processes/*.yaml | DFM yöntemleri, eşikler, LGPL-2.1 | metin_elde |
| 15 | https://github.com/ryankembrey/FreeCAD-DFM-Workbench | Dosya ağacı, 396 commit, 86 yıldız | metin_elde (WebFetch) |
| 16 | https://blog.freecad.org/2026/04/21/new-wip-design-for-manufacture-workbench/ | DFM WB durumu | ikincil_kaynak |
| 17 | https://raw.githubusercontent.com/tomate44/CurvesWB/master/README.md ; …/package.xml | Curves WB LGPL-2.1+ | metin_elde |
| 18 | https://wiki.freecad.org/Curves_DraftAnalysis | DraftAnalysis açıklaması | ikincil_kaynak (site engelli) |
| 19 | https://koreascience.or.kr/article/JAKO200029256813194.pub ; https://research.polyu.edu.hk/en/publications/automatic-determination-of-3-d-parting-lines-and-surfaces-in-plas/ | Ayırma çizgisi/yüzeyi algoritmaları | ikincil_kaynak |
| 20 | https://raw.githubusercontent.com/ElmerCSC/elmerfem/devel/license_texts/GPL-2.txt ; https://github.com/ElmerCSC/elmerfem | Elmer GPL-2 / LGPL-2.1 | metin_elde (WebFetch) |
| 21 | https://raw.githubusercontent.com/FEniCS/dolfinx/main/README.md | dolfinx LGPL-3.0 | metin_elde |
| 22 | https://help.altair.com/hwdesktop/mfs/crossmodel.htm ; https://pmc.ncbi.nlm.nih.gov/articles/PMC10385220 | Cross-WLF parametre tanımları | ikincil_kaynak |
| 23 | https://help.autodesk.com/cloudhelp/2015/ENU/MoldflowComm/files/GUID-62D78349-78EE-4AD1-A758-CCCC923B2A5C.htm ; …GUID-77B82DB8-973E-4CC7-81B7-6EDB868614A6.htm | Re 10000 / 4000 | ikincil_kaynak |
| 24 | https://help.autodesk.com/cloudhelp/2015/ENU/MoldflowComm/files/GUID-67A6F528-BC63-47A5-AF89-838EDB2133FB.htm | Kanal-boşluk mesafesi 2–2,5·D | ikincil_kaynak |
| 25 | https://help.autodesk.com/cloudhelp/2026/ENU/MoldflowInsight-CLC-Analyses/files/analysis-sequences/MoldflowInsight_CLC_Analyses_analysis_sequences_Warp_analysis_html.html ; https://help.autodesk.com/cloudhelp/2015/ENU/MoldflowComm/files/GUID-9C9CCD83-9111-439A-BE3A-F8E2B2DE8450.htm | Moldflow analiz türleri | ikincil_kaynak |
| 26 | https://www.plasticsengineering.org/2024/03/clamping-force-decoding-by-key-strategic-ways-003900 | Kapama kuvveti, 400 bar, 2–8 ton/inç², 3–5 kat | ikincil_kaynak |
| 27 | https://www.keyence.com/ss/products/measure-sys/machining/formula/injection-molding.jsp ; https://firstmold.com/tips/clamping-force/ ; https://zetarmold.com/?p=6016 ; https://huarong.com.tw/page/news/en/company_news/detail/132 | Kapama kuvveti örnekleri ve emniyet payı | ikincil_kaynak |
| 28 | https://resources.skill-lync.com/courses/injection-molding-fundamentals/cooling-system ; https://www.apriori.com/Collateral/Documents/English-US/online_help/2019_R2/COST_MODEL_GUIDE/AP_CMG0109Insert_Injection_Molding_Formulas.html ; https://rjginc.com/injection-molding-cooling-time-a-breakdown/ | Soğuma süresi formülleri | ikincil_kaynak |
| 29 | https://experts.umn.edu/en/publications/calculating-cooling-times-for-polymer-injection-moulding/ | Soğuma formüllerindeki hatalar (IMechE B 2003) | ikincil_kaynak |
| 30 | https://www.findoutaboutplastics.com/2023/04/thin-wall-moulding-of-engineering.html ; https://jtrm.polman-bandung.ac.id/index.php/JTRM/article/view/111 | L/t | ikincil_kaynak |
| 31 | https://www.protolabs.com/services/injection-molding/plastic-injection-molding/design-guidelines/ ; https://protolabs.com/resources/design-tips/improving-part-moldability-with-draft/ | Draft, et kalınlığı | ikincil_kaynak |
| 32 | https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557214249.pdf | Covestro Part and Mold Design | ikincil_kaynak (indirme engelli) |
| 33 | https://www.emcoplastics.com/assets/pdf/acetal/General Design Principles for Engineering Polymers.pdf | DuPont Module I (üçüncü taraf kopyası) | ikincil_kaynak |
| 34 | https://www.meusburger.com/ES/ES/presse/meusburger-provides-tried-and-trusted-cad-tool-free-of-charge ; https://www.dme.net/accualign-cad/ ; https://www.plastikmedia.co.uk/?p=67301 | Standart parça CAD erişimi | ikincil_kaynak |
| 35 | https://www.dinmedia.de/en/standard/din-iso-20457/314652216 ; https://www.sis.se/en/produkter/rubber-and-plastic-industries/rubber-and-plastics-products/general/iso-204572018 ; https://www.austrian-standards.at/en/shop/din-iso-20457-2021-06~p2584315 | ISO 20457 | ikincil_kaynak |
| 36 | https://www.hexagon.de/info141/index.htm ; https://www.dinmedia.de/en/standard/din-16742/192658755 | DIN 16742 / 16901 | ikincil_kaynak |
| 37 | https://www.fictiv.com/articles/what-to-know-about-injection-molding-tooling-life ; https://www.boydcorp.com/blog/classification-plastic-injection-molds.html ; https://texasinjectionmolding.com/society-of-the-plastic-industry-mold-building-standards/ | SPI sınıfları | ikincil_kaynak |
| 38 | https://www.iso.org/ics/25.120.30.html ; https://www.technickenormy.cz/en/bs-iso-10072-2004-tools-for-moulding-sprue-bushes-dimensions | ISO kalıp bileşen standartları | ikincil_kaynak |
| 39 | https://raw.githubusercontent.com/SoftFever/OrcaSlicer/main/LICENSE.txt ; …/README.md | Orca AGPL-3.0, Linux kurulumu | metin_elde |
| 40 | https://github.com/OrcaSlicer/OrcaSlicer/wiki/cli_mode ; …/cli_actions ; …/cli_misc | Orca CLI bayrakları, statistics | metin_elde (WebFetch) |
| 41 | https://github.com/OrcaSlicer/OrcaSlicer/releases/latest | v2.4.2 | metin_elde (WebFetch) |
| 42 | https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/main/resources/profiles/Creality/machine/fdm_creality_common.json | printable_area / printable_height | metin_elde |
| 43 | https://pypi.org/pypi/orca-mcp/json | Orca başsız çalışma, xvfb notu | metin_elde (üçüncü taraf iddiası) |
| 44 | https://www.orcaslicer.com/wiki/cli/cli_mode | Orca CLI resmi sitesi | ikincil_kaynak (site engelli) |
| 45 | https://raw.githubusercontent.com/prusa3d/PrusaSlicer/master/LICENSE | Prusa AGPL-3.0 | metin_elde |
| 46 | https://manpages.ubuntu.com/manpages/noble/man1/prusa-slicer.1.html | Prusa CLI bayrakları, Ubuntu 2.7.2 | metin_elde (WebFetch) |
| 47 | https://github.com/prusa3d/PrusaSlicer/releases/latest | 2.9.7 | metin_elde (WebFetch) |
| 48 | https://forum.prusa3d.com/forum/prusaslicer/how-to-get-duration-and-filament-usage-on-cli/ | Süre G-code yorumunda | ikincil_kaynak |
| 49 | https://github.com/davidk/docker-slic3r-prusa3d ; https://jsr.io/@casys/mcp-prusaslicer | Prusa başsız Docker | ikincil_kaynak |
| 50 | https://raw.githubusercontent.com/Ultimaker/CuraEngine/main/LICENSE ; …/README.md ; …/src/communication/CommandLine.cpp | CuraEngine AGPL-3.0, CLI seçenekleri, "Total print time" | metin_elde |
| 51 | https://raw.githubusercontent.com/wiki/Ultimaker/CuraEngine/Building-CuraEngine-From-Source.md | Derleme gereksinimleri | metin_elde |
| 52 | https://raw.githubusercontent.com/Ultimaker/Cura/main/LICENSE ; …/resources/definitions/fdmprinter.def.json | LGPL-3.0; support_angle 50° | metin_elde |
| 53 | https://github.com/Ultimaker/Cura/releases/latest | Cura 5.14.0 | metin_elde (WebFetch) |
| 54 | https://build.opensuse.org/projects/science/packages/cura-engine/files/CuraEngine.1?expand=0 ; https://community.ultimaker.com/topic/30501-looking-for-help-with-curaengine-slicing/ ; https://community.octoprint.org/t/brainstorming-update-curaengine-plugin/20992 | CuraEngine man sayfası, forum notları | ikincil_kaynak |
| 55 | https://hubs.com/knowledge-base/how-design-parts-fdm-3d-printing ; https://www.33d.ch/en/blog/3d-printing-design-rules-for-beginners-fdm-basic-c ; https://www.eduhk.hk/3d-arch/talk.pdf ; https://xometry.pro/en/?p=22061 | FDM 45°, 0,8 mm, köprü | ikincil_kaynak |
| 56 | https://raw.githubusercontent.com/3MFConsortium/spec_core/master/README.md ; …/LICENSE ; …/3MF%20Core%20Specification.md ; https://raw.githubusercontent.com/3MFConsortium/lib3mf/master/LICENSE | 3MF 1.4.0, BSD-2 | metin_elde |
| 57 | https://scc-ccn.ca/standardsdb/standards/8160198 ; https://technickenormy.cz/en/iso-astm-52910-additive-manufacturing-design-requirements-guidelines-and-recommendations ; https://genorma.com/en/standards/iso-astm-52910-2018/amp | ISO/ASTM 52910 | ikincil_kaynak |
| 58 | https://www.nist.gov/publications/additive-manufacturing-test-artifact ; https://scc-ccn.ca/standardsdb/standards/8167490 | NIST test parçası, ISO/ASTM 52902 | ikincil_kaynak |
| 59 | https://www.sis.se/en/produkter/manufacturing-engineering/additive-manufacturing/ss-en-isoastm-52903-12021/ ; https://www.en-standard.eu/iso-astm-52903-1-2020 ; https://www.standards.govt.nz/shop/bs-isoastm-52903-12020 ; https://www.evs.ee/en/evs-en-iso-astm-52903-1-2021 | ISO/ASTM 52903-1, 52900 | ikincil_kaynak |
| 60 | Chen-Woo görünürlük haritası, ISO 294-4, VDI 3400, CalculiX lisansı, CGAL, `bed_shape`/`max_print_height`, "gate location" analizi | Bellekten | dogrulanmadi |
