# mekanik v1 — Mimari belge (Faz 0)

| Alan | Değer |
| --- | --- |
| Belge | `docs/design/architecture.md` |
| Sürüm | 0.1 taslak |
| Tarih | 2026-11-06 (sistem saati) |
| Yazan rol | proje-muhendisi |
| Durum | İnceleme bekliyor. Onaylayan: — (baş mühendis) |
| Kapsam | Yalnız Faz 0: mimari ve teknik araştırma. Uygulama kodu yok. |
| Eski sistem | `surec` (commit `d26af89`) yalnız okundu. Eski sistem, v1 aynı işleri yapana kadar çalışmaya devam eder. |

**Ekler** (aynı klasörde):

| Ek | Dosya |
| --- | --- |
| Araştırma A: panelin ajanı çalıştırması | `research/a-agent-runtime.md` |
| Araştırma B: STEP değişikliği ve taramadan katıya | `research/b-cad.md` |
| Araştırma C: kalıp otomasyonu ve 3B baskı araçları | `research/c-mold-print.md` |
| Araştırma D: NASA-STD-7009B, mevzuat, lisanslar | `research/d-nasa-regulation-licenses.md` |
| Ek A: bağımlılık envanteri (dosya:satır) | `appendix-a-dependency-inventory.md` |
| Ek B: taşıma envanteri | `appendix-b-migration-inventory.md` |
| JSON şemaları, örnekler, doğrulama aracı | `schemas/` |
| Tel kafes taslakları | `wireframes/` |

**Sayılar hakkında.** Bu belgedeki her sayının yanında kaynağı yazılıdır:

- `ölçü:` eski sistemden ölçülmüş değer (komut ve commit yazılı);
- `belge:` bir kaynaktan alıntı;
- `öneri`: proje mühendisinin önerdiği eşik. Bu eşikler baş mühendis onaylayana kadar geçicidir (açık karar T-02).

---

## 1. Özet

**Ne.** mekanik, bir mühendisin yapay zekâ ajanlarından oluşan bir ekiple tasarım işlerini sistematik biçimde yürütmesini sağlayan süreç sistemidir. Eski `surec` sisteminin yaptıklarını kişiden, makineden, kurumdan ve alandan bağımsız bir yapıda yeniden kurar. İleride açık kaynak (AGPL-3.0) olarak yayınlanabilecek biçimde tasarlanır.

**Neden yeniden.** Eski sistem çalışıyor ve dersleri değerli: 41 eksik (E), 28 öneri (Ö), 8 bağımsız inceleme bulgusu (B), 1 hata kaydı (H-001). Ama kişiye ve kuruma bağlı. Bağımlılık envanteri (Ek A) kayıtlar dışında şu bağlılıkları buldu:

- kişi: 45 yer;
- makine ve yol: 46 yer;
- Üstteknik: 22 yer;
- belirli alan: 84 yer (FDM, CAD, aero, tarama);
- Claude Code: 30 yer;
- Türkçeye sabit arayüz metni: yaklaşık 1320 satır.

Kurum verisi ve makine profilleri de kod reposunun içinde duruyor.

**Nasıl.** Beş katman:

1. **Çekirdek:** hiçbir kişiyi, makineyi, kurumu ya da alanı adıyla tanımayan süreç motoru.
2. **Alan paketleri:** eklenti (mekanik CAD, 3B baskı, kalıp, analiz).
3. **Standart kütüphanesi.**
4. **Atölye ayarı:** `~/.config/mekanik/`.
5. **Çalışma verisi:** her kurumun ayrı reposu.

**v1'in altı parçası:**

| Parça | Bir cümle | Bölüm |
| --- | --- | --- |
| A. Panel kokpit | Proje açma, ajanı başlatma ve durdurma, talimat, kart onayı, dosya alışverişi panelden. Ajan Claude Code CLI headless, ince bir adaptörün arkasında. | §5 |
| B. CAD girdisi ve değişikliği | Parametrik model ya da "orijinal STEP + işlem listesi"; her işlem doğrulanır ve yeniden üretilebilir. STL referans ve ölçüm için. | §6 |
| C. Tanımlama | İş türü → veriyi ajan analiz eder → yalnız veriden çıkmayan soruları sorar (soru ağacı) → anlama özeti. Onaysız tasarım başlamaz. | §7 |
| D. Soru politikası | Sekiz DUR kategorisi dışındaki her karar geçici karardır; kapıya kadar itiraz edilebilir. Ölçülür, eşik ayarlanır. | §8 |
| E. Rapor akışı | Canlı akış (her adım bir satır), gerçek modelden görseller, gün sonu özeti. | §9 |
| F. Mühendislik güvencesi | Kaynaksız sayı yok, kritik hesapta iki yöntem, geçerlilik alanı, NASA-STD-7009B, kalite mühendisi her kapıda, standart haritası. | §10 |

**Faz planı** (§17):

- **Faz 1:** çekirdek ve CLI; yalnız eski sistemin yaptıkları.
- **Faz 2:** panel kokpit, tanımlama, politika, akış, standart haritası.
- **Faz 3:** alan paketleri ve CAD içe alma/değişiklik.
- **Faz 4:** kurulum, belgeler, temiz makinede test, yayın hazırlığı.

Her fazın sayısal kabul ölçütü var. En büyük risk ikinci sistem etkisidir; önlemler §19'da.

**Baş mühendisin açık kararları** §20.2'de listelidir (T-01 … T-14). En önemlisi T-01: ajan abonelikle mi, API anahtarıyla mı çalışacak (maliyet etkisi).

---

## 2. Kesin kararlar, ilkeler ve terimler

### 2.1 Kesin kararlar (Faz 0 talimatı, madde 1; tartışılmaz)

1. Kod, şema, komut ve dosya adları İngilizce. Arayüz ve belgeler TR+EN, varsayılan TR.
2. Tek kullanıcı. İçeride "rol" kavramı var (baş mühendis, ajan rolleri); hesap sistemi yok. Kişi bilgisi ve git kimliği ayardan gelir.
3. Ajan Claude Code'dur ve ince bir arayüzün arkasında durur; ileride başka ajanlar bağlanabilir.
4. Lisans AGPL-3.0. Tamamen ücretsiz; ticari amaç yok.
5. Platform Ubuntu masaüstü. Telefon sonraki sürümde.
6. Panel kokpittir; terminal isteğe bağlıdır.
7. Baş mühendisi mutlaka durduran kararlar: üretim yöntemi, malzeme, ana ölçüler, standarttan sapma, maliyet etkisi, baskı ve üretim, istek listesi değişikliği, yalnız onda olan bilgi.

### 2.2 Eski sistemden korunan ilkeler

Kaynak: el kitabı §1 ve CLAUDE.md.

- Kaynaksız sayı yok, kodda da.
- Kaynaksız kural yok.
- Neyin sorulacağını kurallar belirler, modelin kanaati değil.
- Geri dönüşsüz adımı yalnız baş mühendis onaylar.
- Her karar dal, etiket ve bağımlılık kaydıyla geri alınabilir.
- İşi yapan kendi işini onaylamaz.
- Süreç riske göre uyarlanır.
- Her hata kalıcı bir kurala ve regresyon testine dönüşür.
- Bir geçme tek nominal ve tek boşlukla tanımlanır.
- Saat her zaman sistemden alınır.
- Kontroller modelden bağımsız betiklerdir.

### 2.3 Terimler (arayüzde TR, kodda EN)

| Arayüz (TR) | Kod (EN) | Kısa açıklama |
| --- | --- | --- |
| baş mühendis | `chief_engineer` | Tek onay yetkilisi; ayardaki kişi |
| proje mühendisi | `project_engineer` | Ana ajan oturumu; karar verir, kayda yazar, divanı yönetir |
| tasarım mühendisi | `design_engineer` | Brief içinde çizer |
| tekniker | `technician` | Kontrol, render, dışa aktarma; karar vermez |
| kalite mühendisi | `quality_engineer` | Temiz bağlamla bağımsız inceleme; bulgu yazar |
| kurum / proje / çalışma | `org` / `project` / `work` | Hiyerarşi; çalışma kodu `<KURUM>-<PROJE>-<nn>` |
| aşama, kapı | `stage`, `gate` | G0 … G5 (süreç profilinden) |
| kart | `card` | Baş mühendisin göreceği her şey |
| karar, geçici karar | `decision`, `provisional decision` | — |
| kanıt | `evidence` | İsteği ya da standart maddesini karşılayan kayıt |
| hesap, analiz | `calculation` (`type: calculation`/`analysis`) | — |
| deney | `experiment` | — |
| istek listesi | `requirements` | zorunlu (`mandatory`) / istek (`wish`) |
| geçme | `fit` | tek nominal + tek boşluk |
| kontrol: ENGEL / UYARI / GEÇTİ | `block` / `warn` / `pass` | — |
| DUR (Hold) / geçici karar / inceleme bekliyor / bildir (Witness) | `hold` / `provisional` / `review` / `witness` | Karar seviyeleri |
| alan paketi | `package` | Eklenti |
| atölye ayarı | `config` | Katman 4 |
| standart haritası | `stdmap` | G0'da çıkar |
| baskı/üretim isteği | `release` | Paketten bağımsız "üretime çıkış" DUR'u |
| anlama özeti | `intake summary` | Tanımlamanın çıktısı |

Kaynak etiketleri eski sistemden genelleştirildi:

| Eski | v1 | Neden |
| --- | --- | --- |
| `olcu:kumpas`, `olcu:mastar`, `olcu:tarama` | `measured:<alet-kimliği>` | Alet listesi kodda değil, atölye ayarında (Ek A, 15 yerden 5. madde) |
| `standart:<no>` | `standard:<no ve madde>` | — |
| `uretici:<belge>` (Ö-12) | `manufacturer:<belge>` | — |
| `literatur:<atıf>` (Ö-28) | `literature:<atıf>` | Öneri onay bekliyordu; v1'de etiket var, kural "okunmamış kaynak sayı vermez" |
| — | `regulation:<belge ve madde>`, `customer:<şartname ve madde>` | Standart haritasının kaynak önceliği için |
| `karar` | `decision` (+ `decided_by` rolü) | Kararı hangi rolün verdiği zorunlu |
| `turetilir` | `derived` (+ `formula`) | — |
| `varsayim` | `assumption` | Her zaman kart ya da varsayım listesi |

---

## 3. Katmanlar ve sınırlar

### 3.1 Katmanlar

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 5. Çalışma verisi   kurum başına git reposu: work.yaml, requirements,    │
│                     params, decisions, cards, model, calcs, records …    │
├──────────────────────────────────────────────────────────────────────────┤
│ 4. Atölye ayarı     ~/.config/mekanik/: kişi, git kimlikleri, kurumlar,  │
│                     makineler, ölçme aletleri, yollar, ajan, politika    │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. Standart         madde şablonları (mevzuat, standart, kılavuz),        │
│    kütüphanesi      kural kataloğu, süreç profili; veri, kod değil       │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. Alan paketleri   mech (CAD, geçme) · print3d · molding · analysis …   │
│                     kontroller, hesap şablonları, soru ağaçları, kart     │
│                     türleri, profil türleri, analizler, panel görünümleri │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. Çekirdek         süreç motoru, kayıt deposu, kart, karar, kanıt,      │
│                     kontrol çalıştırıcı, kalite, politika, akış, CLI,    │
│                     panel kabuğu, ajan arayüzü, eklenti API'si           │
└──────────────────────────────────────────────────────────────────────────┘
  Bağımlılık yönü yalnız yukarıdan aşağıya: paket çekirdeği bilir, çekirdek paketi bilmez.
```

**Sınır kuralları ve sınamaları:**

| Kural | Nasıl sınanır | Kabul ölçütü |
| --- | --- | --- |
| Çekirdek paket içe aktarmaz | `import-linter` sözleşmesi: `mekanik.core` → `mekanik_*` paketleri yasak | 0 ihlal |
| Çekirdekte kişi, kurum, makine ve alan adı yok | "temizlik testi": `src/mekanik/core` içinde yasak sözcük listesi taranır (kişi adları, kurum kodları, `fdm`, `print`, `mold`, `wing`, `lidar` …). Liste testte durur; gerçek adlar test sırasında atölye ayarından okunur. | 0 eşleşme |
| Arayüz metni kodda sabit değil | Arayüz metni yalnız `i18n/tr.yaml` ve `i18n/en.yaml` kataloglarında; kodda metin anahtarı | Panel ve CLI'da katalog dışı Türkçe dize: 0 (ast taraması) |
| Görünen metin mantık anahtarı değil | Kapı maddeleri, rol adları ve commit ekleri dil bağımsız kimlikle (Ek A, 15. madde) | Katalog TR → EN değiştirilince bütün testler geçer |
| Gizli bilgi kayıtta yok | Şema `additionalProperties: false`; yazımdan önce gizli bilgi taraması | 0 bulgu |

**Mekanik CAD neden paket?** Ek A'nın önerisi: CadQuery, OCCT, geçme kaydı ve altı mekanik kontrol bugün çekirdeğe gömülü. Bu yüzden CAD'siz bir iş (ör. yalnız analiz) açılamıyor. v1'de bunlar birinci taraf `mech` paketine gider. `mech` varsayılan olarak kurulur ve diğer mekanik paketlerin (print3d, molding) bağımlılığıdır.

Yan kazanç: çekirdek testleri OCCT kurulmadan saniyeler içinde çalışır. Kaynak etiketi, ölçme belirsizliği (1/4 kuralı), kart, karar ve kanıt çekirdekte kalır; bunlar alan bağımsızdır.

### 3.2 Kod reposu (`mekanik`)

```
mekanik/
  pyproject.toml                 uv çalışma alanı (workspace); Python 3.12
  src/mekanik/
    core/
      model/      veri sınıfları + JSON Schema doğrulama (schemas/v1)
      store/      çalışma reposu okuma/yazma, git, kilitsiz okuma, events.jsonl
      process/    süreç profili, aşama/kapı motoru, risk sınıfı
      cards/      kart kayıt defteri, üretici, görsel zorunluluğu, onay özeti
      decisions/  karar, geçici karar, dayanak ve geçersizleşme
      evidence/   kanıt, hesap çalıştırıcı (Calc API), deney, önbellek
      checks/     kontrol kayıt defteri, kural kataloğu bağı, regresyon
      quality/    kalite mühendisi düzeni (temiz bağlam)
      intake/     iş türü, analiz çalıştırma, soru ağacı motoru, anlama özeti
      policy/     DUR kategorileri, geçici karar yaşam döngüsü, ölçüler
      report/     akış olayları, gün sonu özeti, görsel boru hattı (çerçeve)
      stdmap/     standart haritası
      i18n/       tr.yaml, en.yaml
    agent/        AgentAdapter arayüzü, claude_code adaptörü, sahte adaptör (test)
    plugins/      paket keşfi, sürüm uyumu, kayıt defterleri
    config/       atölye ayarı yükleme ve doğrulama
    platform/     isteğe bağlı: tmux, systemd kullanıcı servisi, masaüstü bildirimi, tailscale serve
    cli/          `mekanik` komutu
    panel/        FastAPI arka uç (kabuk, REST, SSE)
  panel-ui/       ön yüz (Vite + TypeScript); derlenmiş hâli tekerleğe girer
  packages/
    mech/         mekanik CAD: OCCT adaptörü, parametrik model, içe alma, işlem listesi, görünüşler, geçme, mekanik kontroller
    print3d/      3B baskı
    molding/      enjeksiyon kalıbı
    analysis/     analiz (aero, FEA şablonları)
  stdlib/         standart kütüphanesi verisi (YAML) + süreç profili + kural kataloğu
  schemas/v1/     JSON şemaları (bu belgedekilerin kesinleşmiş hâli)
  tests/          çekirdek testleri, regresyon vakaları (sentetik)
  docs/           belgeler (TR+EN)
```

### 3.3 Atölye ayarı (`~/.config/mekanik/`)

```
~/.config/mekanik/
  config.yaml          kişi, kimlikler, yollar, ajan, panel, politika, platform   (schemas/v1/config)
  orgs/<KOD>.yaml      kurum: ad, repo yolu, maliyet eşiği, gizlilik, projeler
  machines/<id>.yaml   makine: tür (paket profil türü), profil değerleri (kaynaklı)
  instruments/<id>.yaml ölçme aleti: belirsizlik, geçerlilik (kritik geçme / biçim), kalibrasyon
```

- Önbellek: `~/.cache/mekanik/`. Ajan çalıştırma kayıtları: `~/.local/state/mekanik/` (XDG).
- Gizli bilgi bu dosyalara yazılmaz. API anahtarı ajan aracının kendi akışıyla ya da ortam değişkeniyle verilir (§5.3).

### 3.4 Çalışma reposu (kurum başına)

```
<kurum-reposu>/
  org.yaml                    kurum özeti (kod, ad); ayrıntı atölye ayarında
  works.yaml                  kod kaydı (yalnız eklenir; numara tekrar kullanılmaz)
  <proje>/<KOD>/
    work.yaml                 (schemas/v1/work)
    requirements.yaml         (requirement)
    intake/summary.yaml       (intake-summary) + intake/answers.yaml
    stdmap.yaml               (standard-item listesi)
    params.yaml               kaynaklı değerler (common#quantity)
    fits.yaml                 geçme kaydı (mech paketi şeması)
    decisions.yaml            (decision, provisional-decision)
    cards/<id>.yaml           yalnız durum taşıyan kartlar (üretilenler bellekte)
    approvals.yaml            onay kaydı (yalnız eklenir; baş mühendis kimliğiyle commit)
    evidence.yaml             (evidence)
    experiments/<id>.yaml     (experiment)
    model/                    model.py (parametrik) ya da ops.yaml (işlem listesi) + inputs/
    calcs/<ad>.py             hesap betikleri
    inputs/                   dışarıdan verilen dosyalar (değişmez; SHA-256 work.yaml'da)
    records/
      log/YYYY-MM-DD.md       günlük (yalnız eklenir)
      events.jsonl            akış olayları (yalnız eklenir)
      calcs/<ad>.json         hesap kayıtları (calculation)
      visuals/                kart ve akış görselleri
      quality/<zaman>-<konu>.yaml  kalite incelemeleri
      summaries/YYYY-MM-DD.md gün sonu özetleri
    out/<etiket>/             onaylı baskı/üretim çıktıları (özetleriyle)
```

Dal ve etiket adları eski sistemle aynıdır (el kitabı §8): `<kod>/ana`, `<kod>/is/<konu>`, `<kod>/karar/K-<no>-<seçenek>`, `<kod>-G<n>`, `<kod>-baski-<no>`. Bu adlar çalışma verisinin parçasıdır, kod adı değildir. Eski çalışmalarla süreklilik için korunur.

---

## 4. Çekirdek: süreç motoru

Bu bölüm çekirdeğin hedef hâlini anlatır. Faz 1 yalnız eski sistemin yaptıklarını içerir (§17). "Yeni" diye işaretli kurallar, G3 → G2 dönüşü, tanımlama ve politika modülleri Faz 2'dedir.

### 4.1 Varlıklar ve ilişkiler

```
work ─┬─ requirements ──(verification)──> evidence ──> calculation | experiment | check | document | model_view | quality_review
      ├─ stdmap items ──(evidence)──────┘
      ├─ params (quantity: value+unit+source)
      ├─ decisions ──(basis: calc result hash)──> calculation
      │      └─ options ──(branch)──> <kod>/karar/K-nn-x
      ├─ cards ──(subject)──> params | fits | decisions | gates | releases | findings
      ├─ approvals ──(hash of approved values)──> card
      ├─ model (parametric script | oplist on inputs/*.step)
      └─ records (log, events, calcs, quality, visuals)
```

### 4.2 Süreç profili: aşama ve kapılar veri olarak

Eski sistemde G0–G5, A/B/C sınıf eşlemesi ve G0'ın dört sorusu kodda sabitti (`veri.py:24-37`).

v1'de bunlar standart kütüphanesindeki bir **süreç profilinden** gelir: `stdlib/process/default@1.yaml`. Profilin içeriği:

- aşamalar ve kapılar;
- sınıf → kapı eşlemesi;
- risk soruları;
- kapı kontrol listesi maddelerinin kimlikleri;
- geri dönüş yolları (G3 → G2, Ö-17).

Varsayılan profil el kitabı §5–§6'nın birebir karşılığıdır. Çekirdek "aşama", "kapı", "sınıf" kavramlarını bilir; hangi aşamaların olduğunu profilden okur. Çalışma profili sürümüyle sabitler (`work.process.profile: default@1`).

**Kapı motoru:**

1. `stage finish <G>`: profilin kapı listesi çalışır, kontroller çalışır, kalite mühendisi çalışır (§4.8), sonra kapı kartı açılır.
2. Kapı kartının içeriği: her istek için durum (karşılandı | karşılanmadı | kanıt bekliyor) ve kanıtın yeri (B2); kötü ya da güvenilmez sonuçlar (B4); açık geçici kararlar (§8).
3. `gate pass <G>`: yalnız baş mühendis kimliğiyle, onay özeti güncelse (kart içeriği değişmediyse) geçer. Kapı etiketi konur. İtirazsız geçici kararlar "kapıda kabul" olur.
4. Deneyle doğrulanan zorunlu istek varsa G4 kendiliğinden eklenir (B7).
5. G3 → G2 dönüşü: gerekçeli, baş mühendis onaylı. G2 etiketi kalır, yeni G2 kapısı istenir (Ö-17, E-26).

**G5 koşulu** (el kitabı §10, değişmedi): sıfır ENGEL, bütün kararlar incelenmiş, onay özetleri güncel, baş mühendis onayı.

### 4.3 Kart

- **Kart türleri kayıt defterinden gelir.** Çekirdek türleri: `question`, `decision`, `provisional_decision`, `assumption`, `assumption_list` (V-01), `gate` (O-Gn), `release` (B), `model_note` (N), `consistency`, `basis_changed`, `quality_finding`, `deviation`. Paketler kendi türlerini ekler: `mech:fit` (G), `mech:flex` (E) …
- **Neyin kart açacağını kurallar belirler** (el kitabı §7). Kart tetikleyicileri kontrol ve politika kurallarıdır. Her kartın `triggers` alanı açıldığı kuralı söyler.
- **Kart standardı** (Ö-09 … Ö-14, Ö-27):
  - "Bu nedir, neden sana soruluyor?" kutusu;
  - ekibin önerisi;
  - onaylarsan / reddedersen / kayda geçer kutuları;
  - görsel zorunlu (görselsiz kart açılamaz);
  - karar kartında "isteklere etkisi" zorunlu;
  - DUR kartlarında teyit penceresi.
- **Bellekte üretim.** Üretilen kartlar bellekte üretilir. Yalnız durum değişince (onay, yorum, kapanış) diske yazılır. `check` komutu dosya yazmaz (E-40).
- **Numaralama** çalışma içinde türe göre sıralıdır; kullanılmış numara tekrar verilmez.
- **Yorum–yanıt dizisi.** Kart "yanıt bekliyor" durumuna geçer. Ekip yanıtı bir adımla yazar (E-11).

### 4.4 Karar ve geçici karar

- **Seviyeler** (el kitabı §7, v1'de politika ile bağlanır; §8):
  - `hold`: DUR kategorileri;
  - `provisional`: geçici karar;
  - `review`: kayda geçer, iş sürer;
  - `witness`: bildirim.
- **Seçenekler açık değer taşır.** Her seçenek, herhangi bir seçeneğin değiştirdiği bütün değerleri açıkça taşır (E-17). Model tanımı kayıtta da tutulur (E-15).
- **Kapanmış karar, onaylandığı sürümle değerlendirilir** (E-21): `approved_version`.
- **Dayanak.** Karar dayandığı hesapları sonuç özetiyle kaydeder (B5). Özet değişirse ya da yerine daha doğru bir hesap gelirse karar `review_needed` olur ve "dayanağı değişti" kartı açılır (KARAR-01).
- **Gözlemler.** Karar dayandığı gözlemleri `measured: true|false` ile kaydeder. Yalnız ölçümsüz gözleme dayanan karar şemada geçersizdir (B6).
- **Geçici karar** (§8): ayrı dalda ilerler. Bağımlı işler işaretlenir. En az bir alternatif kayda geçer. Görseli ve gerekçesiyle akışa düşer.

### 4.5 Kanıt, hesap ve deney

**Hesap API'si.** Eski `Hesap` sınıfı korunur ve İngilizceleşir: `Calc.input()`, `const()`, `step()`, `result()`, `magnitude()`, `other()`, `chart()`, `visual()`, `note()`. Kurallar:

- `input()` yalnız `params.yaml`'dan okur. Kaynaksız ya da değersiz girdi hata verir.
- `const()` sabiti varsayım olamaz; yalnız `standard:`, `manufacturer:`, `literature:` ya da `decision` kaynağı alır.
- `magnitude(ad, değer, birim, level, yöntem)` hesaplar arası karşılaştırma için kullanılır. `level`: 1 elle, 2 sayısal, 3 ölçüm.
- Analiz (`type: analysis`) bir riske, gözleme, isteğe ya da karara bağlanmadan çalışmaz (Ö-19).
- Yeni: `validity(domain=…)` aracın geçerlilik alanını kaydeder. Alan dışı sonuç `unreliable` olur (§10.3).
- Yeni: `critical=True` olan hesap ikinci yöntem ister (§10.2).

**Önbellek.** Girdi özeti değişmeyen hesap yeniden çalışmaz (E-37). Sonuç `records/calcs/<ad>.json`'a yazılır (şema: `calculation`).

**Deney.** `experiments/<id>.yaml` (şema: `experiment`). Numune baskı etiketiyle bağlanır. Teste girmeden önce numunenin kabul ölçümü yapılır (kütle, ağırlık merkezi: E-35, E-41). Geçersiz deneme nedeniyle kayda geçer.

**Kanıt.** `evidence.yaml`. Bir isteği ya da standart maddesini bir kayda (hesap, deney, kontrol, ölçüm, belge, model görünüşü, kalite incelemesi) içerik özetiyle bağlar. Özet değişirse kanıt bayatlar.

### 4.6 Onay ve kimlik

- **Onay özeti.** Onaylanan değerlerin kanonik JSON'unun SHA-256'sıdır (eski `onay.py`, aynen). Değer değişirse onay düşer ve kart yeniden açılır.
- **Kimlik doğrulama:**
  - Eskiden onay yetkisi makinenin `git config user.name` değerinden ve yalnız ilk ad karşılaştırılarak veriliyordu. Bağımlılık envanteri bunda bir hata buldu: "Taha Test" de yetkili sayılıyordu (`onay.py:112`).
  - v1'de baş mühendis kimliği atölye ayarındaki `identities.chief` kaydıdır. Eşleşme ad + e-posta tam eşitliğiyle yapılır.
  - Onay commit'leri baş mühendis kimliğiyle, ekip commit'leri `identities.team` kimliğiyle atılır.
- **Onay kanalı.** Onay yalnız panelden ya da `mekanik approve` komutundan verilir. Komut TTY ister ve ajan araç listesinde yasaklıdır.
- **Yazmaya hazırlık.** Ajanın kaydedilmemiş değişikliği varken ya da ekranda görülen sürüm son sürüm değilken onay yazılmaz (Ö-07).
- **Geri alma.** Baş mühendis kendi onayını ya da retini geri alabilir; kayıt silinmez, `undo` kaydı eklenir. Kapı ve baskı onayı geri alınmaz (Ö-15).

### 4.7 Kontroller ve kural kataloğu

- **Kontrol arayüzü.** Kontrol, salt okunur bir `WorkView` alan saf bir fonksiyondur. Sonucu `pass | warn | block` olur; kural kimliği ve iletisiyle birlikte döner. Kontrol çekirdekte ya da pakette yazılır, kayıt defterine kimliğiyle girer.
- **Katalog–kod bağı testi.** Kural kataloğu `stdlib/rules/*.yaml`'dadır. Her sonucun kural kimliği katalogda bulunmalı; her katalog kuralının kontrolü kodda bulunmalı. Eski sistemde bu bağ kopuktu: HESAP-01, HESAP-02, KARAR-01, tabla teması ve ayrık katı katalogda yoktu (Ek B bulgu 1).
- **Eşikler kodda değil.** Kodda duran eşikler (çap farkı 3,0; girişim 0,001; tutarlılık %10; temas 0,5; kabuk 0,8 …; Ek B bulgu 2) katalogun `limit` alanına ya da paketin profil türüne taşınır. Her eşik kaynak etiketi taşır.
- **Çekirdek kontrolleri** (alan bağımsız):

| Kimlik | Konu | Eski karşılığı |
| --- | --- | --- |
| SOURCE-01 | Kaynaksız değer (her aşamada ENGEL) | KAYNAK-01 |
| UNCERT-01 | Kritik ölçüde 1/4 kuralı (U ≤ bant/4); alet geçerliliği (kritik geçmede yalnız biçim için geçerli alet ENGEL) | OLCU-01, OLCU-02 |
| APPROVAL-01 | Serbest bırakmada açık DUR, incelenmemiş karar, bayat onay yok | ONAY-01 |
| CALC-01 | Aynı büyüklük iki hesapta eşikten fazla farklı → tutarlılık kartı | HESAP-01 |
| CALC-02 | Kötü ya da güvenilmez sonuç kapı ve baskı kartında listelenir; onay gerekçe ister | HESAP-02 |
| DECISION-01 | Dayanağı değişen karar → kart | KARAR-01 |
| CALC-03 (yeni) | Kritik hesabın ikinci yöntemi yok ya da uyuşmuyor → ENGEL | Ö-18 |
| CALC-04 (yeni) | Geçerlilik alanı dışında sonuçla kanıt → ENGEL | §10.3 |
| REQ-01 (yeni) | G4/G5'te zorunlu isteklerin hepsi "karşılandı" | B2 |
| STDMAP-01 (yeni) | G0 kapısında standart haritası var; G5'te tiksiz zorunlu madde yok | §10.6 |
| CARD-01 | Görselsiz ya da metni eksik kart açılamaz | Ö-10 (kimliksizdi) |
| QUALITY-01 | Açık YÜKSEK kalite bulgusu varken kapı ve baskı kartı açılmaz | Ö-20 (kimliksizdi) |

- **Mekanik kontroller** `mech` paketindedir: GECME-01/02, VIDA-01, KATI-01, GIRISIM-01, KAYITSIZ-01, MONTAJ-01. Kimlikler İngilizceleşir: FIT-01/02, BOLT-01, SOLID-01, INTERF-01, UNREG-01, ASSY-01.
- **Regresyon.** Her vaka hem geçmesi hem kalması gereken alt vakalar içerir. Her kontrolün "hep ENGEL" ve "hep GEÇTİ" sahte sürümü regresyondan geçemez. Eski `test_regresyon` bunu yapıyordu; aynen taşınır. H-001 sentetik vakaya dönüşür (§16): aynı sayılar, uydurma parça adları, kurum verisi yok.

### 4.8 Kalite mühendisi

Eski `kalite.py` taşınır (B1). Değişiklikler:

- **Çağrı ajan adaptöründen geçer.** Komut ve model sabit değildir (Ek A, 15 yerden 8. madde).
- **Ne zaman çalışır:** her kapı isteğinde, her baskı/üretim isteğinde ve anlama özeti onayından önce (§7).
- **Temiz bağlam.** İnceleme o commit'in donmuş kopyasında (`git worktree --detach`) yapılır. Araçlar salt okunurdur. Sohbet özeti verilmez; yalnız ilkeler listesi, kabul ölçütleri ve dosya yolları verilir.
- **Açık YÜKSEK bulgu varken istek açılmaz.** Bulgular gerekçeyle kapatılır.
- **Girdiler değişmedikçe yeniden çalışmaz:** girdi özeti, eski sistemle aynı yöntemle hesaplanır.
- **Rapor yapılandırılmıştır:** `records/quality/<zaman>-<konu>.yaml`. Bulgu biçimi `[YÜKSEK|ORTA|DÜŞÜK] yer — sorun — ilke — kanıt` aynen kalır.
- **Kalite bulgusu kendiliğinden regresyona dönüşmez.** Kapanırken "regresyon vakası gerekir mi?" sorusu zorunlu alandır (§10.7).

### 4.9 Roller ve ajanlar

- **Rol tanımları çekirdektedir:** yetki, araç sınıfı ve kilitli kurallar (`stdlib/roles/*.yaml`). Rol → model eşlemesi atölye ayarındadır (`agent.roles`). Model adları kalıcı günlüğe yazılmaz; günlükte rol yazar (Ek A, 15 yerden 10. madde).
- **Divan kuralları** (el kitabı §4) aynen kalır:
  - tasarım kararı teknikere verilmez;
  - alt ajan yalnız iş paralelleşiyorsa açılır;
  - ajana kısa bağlam verilir;
  - yapamayanın işi bir üst katmana bir kez verilir;
  - kararı hangi rolün verdiği yazılır.
- **Adaptör ajan dosyalarını üretir.** Claude Code'a özgü dosyalar (`.claude/agents/*.md`, kancalar) rol tanımlarından adaptör tarafından üretilir. Çekirdek bunları bilmez.

### 4.10 Kayıt deposu, dallar ve eşzamanlılık

- **Okuma.** Panel okumaları `--no-optional-locks` ile yapılır (E-20).
- **Paralel çalışma.** Her çalışma kendi worktree'sindedir. Aynı anda en çok 3 aktif çalışma kuralı eskiden tmux oturumlarından sayılıyordu; v1'de ajan çalıştırmalarından (`agent-run`) sayılır. tmux isteğe bağlı platform adaptörü olur.
- **Ana hat.** Ekip ana hatta (`<kod>/ana`) yazmaz. Ana hatta giriş baş mühendis onayıyla olur.
- **`works.yaml`** yalnız eklenir.
- **Bayt kodu.** Model ve hesap kodu bayt kodu yazmadan yüklenir (E-19).

### 4.11 CLI (`mekanik`)

Eski 25 alt komut v1'de şu adlarla karşılanır. Ayrıntılı eşleme Ek B §3'tedir.

| Eski | v1 | Faz |
| --- | --- | --- |
| `doktor` | `mekanik doctor` | 1 |
| `regresyon` | `mekanik regress` | 1 |
| `kontrol` | `mekanik check` (dosya yazmaz) | 1 |
| `yeni-calisma` | `mekanik work new` | 1 |
| `ac`, `kapat`, `gec` | `mekanik work open` (worktree; terminal komutunu yazar), `mekanik agent start/stop` (Faz 2); tmux adaptörü isteğe bağlı | 1 / 2 |
| `arsivle` | `mekanik work archive` | 1 |
| `adim` | `mekanik step` | 1 |
| `asama-bitir` | `mekanik stage finish` | 1 |
| `baski` | `mekanik release request` | 1 |
| `onay` | `mekanik approve` (TTY; baş mühendis) | 1 |
| `yanitla`, `bekleyenler` | `mekanik reply`, `mekanik pending` | 1 |
| `karar` | `mekanik decide` | 1 |
| `durum-yaz`, `durum` | `mekanik agent hook` (adaptör), `mekanik agent status` | 1 |
| `gozcu` | `mekanik watch` | 1 |
| `kalite`, `kalite-kapat` | `mekanik review`, `mekanik review close` | 1 |
| `nabiz` | `mekanik pulse` | 1 |
| `gecis-plani` | taşınmaz (ustteknik-arge'ye özgüydü) | — |
| `panel` | `mekanik panel` | 1 (arka uç) / 2 (kokpit) |
| — | `mekanik migrate`, `mekanik intake`, `mekanik stdmap`, `mekanik pkg list`, `mekanik init` | 1 / 2 / 4 |

### 4.12 Dil (TR+EN)

- Arayüz metinleri `i18n/<dil>.yaml` kataloglarındadır. Varsayılan `tr`.
- Kayıtlardaki metin (gerekçe, yorum) yazıldığı dilde kalır; çevrilmez.
- Kayıt alanlarının adları ve sıralı değerleri İngilizcedir. Arayüz bunları katalogla gösterir (ör. `text_in_hand` → "metin elde").
- Paketler kendi kataloglarını taşır. Eksik EN anahtarı TR'ye düşer ve testte uyarı verir.

### 4.13 Saat

Bütün zaman damgaları sistem saatinden alınır (`core.clock.now()`, saat dilimli ISO 8601). Elle saat yazmak şemada engellenemez. Bu yüzden ajan için iki kural konur: `mekanik step` saati kendisi yazar, ajan saat alanı göndermez.

---

## 5. Parça A — Panel kokpit

### 5.1 Ne yapılır

Panel tek pencerelik kokpittir. Terminal isteğe bağlıdır.

| İş | Panelde | CLI eşdeğeri |
| --- | --- | --- |
| Proje ve çalışma açma (kurum, proje, iş türü, dosyalar) | Proje açma ekranı | `mekanik work new` |
| Ajanı başlatma, durdurma, sürdürme | Üst çubuk + Akış ekranı | `mekanik agent start/stop/resume` |
| Ajana talimat yazma | Akış ekranının altındaki kutu | `mekanik agent send` |
| Kart onayı, ret, yorum, değer girişi | Kart ekranı (DUR kartlarında teyit penceresi) | `mekanik approve` (TTY) |
| Geçici karara itiraz | Akış satırı ya da kart | `mekanik object` |
| Dosya ekleme (STEP, STL, PDF, görsel) | Sürükle-bırak | `mekanik work add-input` |
| Dosya indirme (çıktılar, raporlar, klasör zip) | Dosyalar ekranı | — |
| "Terminalde aç" | Her çalışmanın ve her ajan çalıştırmasının yanında kopyalanabilir komut | — |

"Terminalde aç" komutu ajan oturumunu kaldığı yerden açar:

```bash
cd <worktree> && claude --resume <session-id>
```

Aynı oturumu panel ile terminal aynı anda sürmemelidir. Panel, oturum terminalde açıkken o oturuma talimat göndermez. Bunun için oturum kilidi `~/.local/state/mekanik/locks/` altında tutulur.

### 5.2 Ekranlar

Tel kafesler `wireframes/` klasöründe. Görsel dil eski panelden alındı: aynı renk belirteçleri, üst konum satırı, çalışma sekmeleri (en çok 3), solda Kurum → Proje → Çalışma ağacı, sağda özellikler paneli, altta durum çubuğu.

| Ekran | Dosya | Ne gösterir |
| --- | --- | --- |
| Proje açma | `project-new.html` | Kurum, proje, iş türü (5), dosya bırakma, önerilen paket, verilecek kod, CLI eşdeğeri |
| Tanımlama | `intake.html` | Adım çubuğu, veri analizi görselleri, soru kartı (neden önemli, cevapsız varsayılan, görsel), soru ağacı, bulgular, anlama özeti |
| Akış | `flow.html` | Canlı akış, geçici karar satırları, DUR satırları, gün sonu özeti, aşama sonu soru paketi, ölçüler, talimat kutusu |
| Kart | `card.html` | Karar kartı (kart standardı) ve kapı kartı (istek durumu tablosu) |
| Model | `model.html` | 3B görünüm, işlem listesi, seçili yüz imzası, işlem doğrulaması, önce–sonra |
| Standart haritası | `stdmap.html` | Madde tablosu, tür, doğrulama durumu, tik, satın alma listesi, kaynak önceliği |

Eski panelin ekranları da v1'de karşılanır:

- Durum, Ekip: Akış ekranının sağ paneli;
- Model: `mech` paketinin panel görünümü;
- Kartlar, Tasarım dosyası, Dal haritası: çekirdek ekranları;
- Hesaplamalar ve Analizler: Dosyalar ağacında model altında.

### 5.3 Araştırma: panel ajanı arka planda nasıl çalıştırır?

Ayrıntı ve birebir alıntılar: `research/a-agent-runtime.md` (bütün kaynaklar `metin_elde`, erişim 2026-11-06).

**Bulgular:**

1. **Aynı motor.** Agent SDK, "A library that runs the Claude Code binary". İki yolda da aynı Claude Code ikilisi çalışır ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)).
2. **Kimlik doğrulama.**
   - CLI headless (`claude -p`) abonelik girişini (`/login`), uzun ömürlü abonelik token'ını (`claude setup-token`: "For CI pipelines, scripts …") ve API anahtarını destekler ([Authentication](https://code.claude.com/docs/en/authentication)).
   - Agent SDK için resmî tutum şu: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK." Yani SDK yolu pratikte API anahtarı demektir.
3. **Kullanım şartları.**
   - Consumer Terms (8 Ekim 2025) otomasyonu "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it" koşuluyla sınırlar.
   - Legal sayfası: geliştiriciler "should use API key authentication", "may not collect, store, or intermediate Claude.ai credentials". Aynı sayfa şunu da söyler: "Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription".
   - Abonelik sınırları "ordinary, individual usage" varsayar ([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)).
4. **Maliyet.**
   - Abonelik: Pro aylık 20 USD, Max aylık 100 USD (5× Pro), Ultra aylık 200 USD ([pricing](https://claude.com/pricing)).
   - API, 1M token başına girdi / çıktı: Opus 5.5 4 / 20 USD, Sonnet 5.5 2 / 10 USD, Haiku 5.5 0,10 / 0,50 USD ([API pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
   - Resmî büyüklük sırası: kurumsal geliştirici ortalaması aktif gün başına yaklaşık 13 USD ([Costs](https://code.claude.com/docs/en/costs)).
5. **Teknik uygunluk.** Headless CLI paneli tam karşılar:
   - `--input-format stream-json` + `--output-format stream-json` (çok turlu talimat ve canlı akış);
   - SIGINT ile tur kesme;
   - `--resume <session-id>`;
   - `--permission-prompt-tool` ile onay isteklerini panele taşıma;
   - `total_cost_usd`, `--max-budget-usd`;
   - `capabilities` ile sürüm algılama ([Headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference)).
6. **Lisans.** Python SDK MIT, TS SDK ve Claude Code CLI tescilli. AGPL açısından tescilli ikili mekanik ile birlikte dağıtılmaz; kullanıcı kurar, mekanik ayrı süreç olarak çağırır (§18).

**Karşılaştırma:**

| Ölçüt | CLI headless (kullanıcının kendi girişi) | Agent SDK (API anahtarı) |
| --- | --- | --- |
| Kimlik doğrulama | Abonelik ya da kullanıcının API anahtarı; panel kimlik bilgisine dokunmaz | API anahtarı (abonelik üçüncü taraf üründe izinli değil) |
| Maliyet | Abonelik: sabit aylık, sınırlar içinde; API: token başına | Token başına |
| Şartlar: kişisel kullanım | Belgelenmiş kullanım; sınırlar "ordinary, individual usage" | Açıkça önerilen yol |
| Şartlar: açık kaynak dağıtım | Her kullanıcı kendi değiştirilmemiş ikilisine kendi hesabıyla girer | Her kullanıcı kendi API anahtarı |
| Akış / kesme / sürdürme | stream-json, SIGINT, `--resume` | `ClaudeSDKClient`, `interrupt()`, `resume` |
| Panelde onay | `--permission-prompt-tool` (MCP) | `can_use_tool` |

**Öneri (yorum; karar T-01).** İlk adaptör Claude Code CLI headless olsun:

- mekanik hiçbir kimlik bilgisini okumaz, saklamaz, iletmez;
- kullanıcı `claude` içinde kendi hesabıyla girer ya da kendi `ANTHROPIC_API_KEY`'ini tanımlar;
- atölye ayarında `agent.auth: subscription | api_key` seçilir; `api_key`'de `max_budget_usd` zorunludur (şema bunu denetler);
- Agent SDK ikinci adaptör olarak eklenebilir, yalnız API anahtarıyla.

Gerekçe: SDK zaten aynı ikiliyi çalıştırıyor. Kişisel kullanımda abonelik ancak CLI yoluyla şartlara uygun kullanılabilir. Açık kaynakta iki yol da "her kullanıcı kendi hesabı" ilkesine uyar.

**Açık risk (yorum).** Consumer Terms'teki istisna "where we otherwise explicitly permit it". `-p` ve `setup-token`'ın belgelenmiş olması buna girer diye okunabilir, ama kesin değildir. Bu yüzden mekanik:

- ajanı yalnız baş mühendisin başlattığı çalışmalarda çalıştırır;
- tur ve bütçe sınırı koyar;
- kendiliğinden yeni oturum açmaz.

Eski E-14'ün kalan sorusu ("ekip oturumu kapalıysa `claude -p` ile kendiliğinden başlatılsın mı") bu yüzden **hayır** olarak önerilir. Kesin yorum için Anthropic'e sorulabilir.

### 5.4 Ajan arayüzü (`AgentAdapter`)

```python
class AgentAdapter(Protocol):
    name: str
    def probe(self) -> AdapterInfo: ...                     # kurulu mu, sürüm, yetenekler, giriş durumu (kimlik bilgisini okumadan)
    def start(self, work: WorkRef, role: Role, prompt: str, opts: RunOptions) -> RunHandle: ...
    def send(self, run: RunHandle, message: str) -> None: ... # çok turlu talimat
    def interrupt(self, run: RunHandle) -> None: ...          # turu bitir (Claude Code: SIGINT)
    def stop(self, run: RunHandle) -> None: ...               # süreci kapat (SIGTERM; tur kayda geçmez)
    def resume(self, work: WorkRef, session_id: str, opts: RunOptions) -> RunHandle: ...
    def events(self, run: RunHandle) -> AsyncIterator[AgentEvent]: ...
    def terminal_command(self, run: RunHandle) -> str: ...
    def render_role_files(self, worktree: Path, roles: list[RoleDef]) -> None: ...  # ör. .claude/agents/*.md
    def answer_permission(self, run: RunHandle, request_id: str, allow: bool, note: str = "") -> None: ...
```

- **Normalleştirilmiş olaylar:** `started`, `message` (metin), `tool_call`, `tool_result`, `permission_request`, `usage`, `error`, `turn_ended`, `ended`. Bunlar akış olayına (şema `stream-event`) dönüşür; kalıcı olanlar `records/events.jsonl`'e yazılır.
- **Claude Code eşlemesi:** stream-json `system/init` → `started`; `assistant` metin ve `tool_use` → `message` / `tool_call`; `user` `tool_result` → `tool_result`; `result` → `usage` + `turn_ended`; `permission_denied` → `permission_request` sonucu.
- **Sürüm kayması.** Ajan aracının çıktı biçimi değişebilir. Bu yüzden:
  - adaptör testleri kaydedilmiş stream-json örneklerine (fixture) karşı çalışır;
  - `capabilities` dizisi denetlenir;
  - `mekanik doctor` sürümü raporlar;
  - desteklenen sürüm aralığı adaptörde yazılıdır.
- **Sahte adaptör.** `FakeAdapter`, testlerde ve panel e2e'de gerçek ajan çağırmadan senaryo oynatır. Eski `SUREC_KALITE_KOMUTU` fikrinin genelleşmiş hâlidir.

### 5.5 Arka uç

- **Kabuk ve uç noktalar.** FastAPI kabuğu (eski `uygulama.py`). REST okuma uçları ve olaylar için SSE kullanılır. Eski uç noktalar İngilizceleşir; eşleme Ek B §4'tedir.
- **Ağ ve güvenlik.**
  - Varsayılan `127.0.0.1` (ayardan).
  - Host ve Origin denetimi korunur (eski e2e testi).
  - Dışarı açmak platform adaptörünün işidir (`platform.remote_access: tailscale_serve`); çekirdek Tailscale'i bilmez.
- **Ajan gözetmeni.** Her çalıştırma bir alt süreçtir. Panel kapanınca çalıştırma kesilmez; oturum kimliğiyle yeniden bağlanılır. Panel yeniden başlayınca `~/.local/state/mekanik/runs/` okunur.
- **Dosya yükleme.**
  - STEP/STL/PDF/görsel `inputs/` altına yazılır; SHA-256 `work.yaml`'a eklenir.
  - Boyut sınırı ayardan gelir.
  - İndirme yalnız `out/`, `records/` ve `inputs/` altından yapılır. Yol kaçışı (`..`) reddedilir; eski güvenlik testi taşınır.
- **Gözcü** (eski `gozcu.py`, E-14). Baş mühendisin commit'lerini izler ve çalışan ajan oturumuna olay olarak iletir. Oturum yoksa olay "bekleyen" kalır; kendiliğinden oturum açılmaz (§5.3).

### 5.6 Veri şeması

- `agent-run`: çalıştırma kaydı; kimlik bilgisi alanı yok; `additionalProperties: false`.
- `stream-event`: akış satırı.
- `config.agent`: adaptör, kimlik doğrulama türü, rol → model, sınırlar.

### 5.7 Kabul ölçütleri (Faz 2)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| A1 | Proje açma, ajan başlatma/durdurma, talimat, kart onayı, dosya ekleme/indirme panelden, terminal adımı olmadan | 7/7 iş, her biri bir Playwright e2e testiyle | öneri |
| A2 | Akış gecikmesi: ajan olayından panel satırına | p95 ≤ 1,0 s (sahte adaptörle, 100 olay) | öneri |
| A3 | Ekran metni yanıt süresi | p95 ≤ 0,5 s. Eski panel ölçüsü 0,04–0,48 s, en çok 0,94 s (ölçü: `kayit/kurulum/hiz-olcumleri.txt`) | öneri, eski ölçüye dayalı |
| A4 | 3B model ilk görüntü | p95 ≤ 1,5 s önbellekte; ≤ 2,0 s önbelleksiz. Eski: 1,0–1,4 s; önbelleksiz 1,6 s (aynı dosya) | öneri, eski ölçüye dayalı |
| A5 | Durdurma: "Durdur"dan sürecin bitmesine | ≤ 5 s; tur kaydı "interrupted" | öneri |
| A6 | Sürdürme: panel yeniden başladıktan sonra çalışan ajana yeniden bağlanma | 10 denemede 10 | öneri |
| A7 | Kimlik bilgisi sızıntısı | `agent-run`, `events.jsonl`, günlük ve panel yanıtlarında gizli bilgi taraması: 0 bulgu | öneri |
| A8 | Oturum kilidi: terminalde açıkken panelden talimat | reddedilir, 3/3 test | öneri |
| A9 | Yol kaçışı ve Host/Origin | eski güvenlik e2e testleri geçer | ölçü: `testler/test_panel_e2e.py` |

---

## 6. Parça B — CAD girdisi ve değişikliği

Bu parça `mech` paketinde yaşar (§3.1). Çekirdek yalnız "model üretici" arayüzünü ve görsel boru hattının çerçevesini bilir.

### 6.1 Üç model türü

| Tür | Ne | Kayıt |
| --- | --- | --- |
| `parametric` | Ajan modeli sıfırdan çizer: `model/model.py`, ölçüleri yalnız `params.yaml`'dan okur | Eski sistemle aynı (CadQuery) |
| `imported` | Dışarıdan STEP: "orijinal dosya + işlemler = yeni model" | `model/ops.yaml` (şema `model-oplist`) |
| `hybrid` | İçe alınan parça + parametrik ekler (ör. kalıp bloğu, maça) | ikisi birlikte; işlem listesinde `boolean_body` araç gövdesi betiği |

### 6.2 İşlem listesi: izlenebilir, geri alınabilir, yeniden üretilebilir

```
inputs/braket-v2.step (SHA-256 sabit)
  └─ OP-00 import+heal (okuma ve iyileştirme parametreleri kayıtlı)
       └─ OP-01 hole Ø{m6_clearance_hole}   hedef: yüz #12 + imza
            └─ OP-02 fillet R{rib_root_radius}  hedef: kenar #41 + imza   ← K-07 (geçici karar)
                 └─ …  her adımın çıktısı: geçerlilik, katı sayısı, hacim farkı, yüz imza tablosu, şekil özeti
```

**Kurallar:**

1. **Orijinal değişmez.** Orijinal dosya `inputs/` altındadır ve SHA-256 ile sabitlenir.
2. **İçe alma da bir işlemdir.** Okuma ve iyileştirme (`ShapeFix`, `UnifySameDomain`) geometriyi ve toleransı değiştirir. Bu yüzden parametreleriyle kaydedilen bir işlemdir (OP-00).
3. **Kaynaksız ölçü yok.** Her ölçü `params.yaml`'daki kaynaklı parametre adıyla ya da satır içi kaynaklı değerle verilir. Şema bunu denetler.
4. **Geri alma kayıt silmez.** Geri alma `enabled: false` yapmak ya da listeden çıkarıp yeniden oynatmaktır. Ara şekiller şekil özetiyle önbelleğe alınır.
5. **Doğrulama zinciri.** Her işlemden sonra denetlenenler (Araştırma B, a):
   - `IsDone` / uyarı listesi;
   - `BRepCheck_Analyzer`;
   - katı sayısı;
   - kabuğun kapalı olması;
   - en büyük tolerans;
   - geçmiş tutarlılığı;
   - beklenen hacim değişimi yönü (`expect.volume_change`).

   Kısmi sonuç kabul edilmez: fillet'te `NbFaultyContours`, detay silmede `HasWarnings`. Başarısız işlem "yapılamadı" diye kart açar; sessizce atlanmaz.
6. **Yüz başvurusu dört katmanlıdır** (Araştırma B, b):
   1. İndeks: `TopExp::MapShapes` sırası; aynı çekirdek sürümünde ve aynı girdide belirlenimci.
   2. Geçmiş soyu: `BRepTools_History` Modified/Generated.
   3. Geometrik imza: yüzey türü, alan, ağırlık merkezi, normal ya da eksen, yarıçap, kenar sayısı, komşu yüzey türleri.
   4. Sıfır ya da birden çok aday varsa **dur ve kart aç**.

   `index` dışındaki her eşleşme akışa bildirilir. Kıyım (hash) tabanlı kümelerin sırası kullanılmaz; bellek adresine bağlıdırlar.
7. **Araç katısı + Boolean.** Kendi ürettiğimiz yüzler belirlenimci araç katısı üzerinden adlandırılır. Bu yüzden delik ve kabartma `BRepFeat` yerine "araç katısı + Boolean" ile yapılır.
8. **Çekirdek sürümü sabittir.** OCCT, OCP ve CadQuery sürümü `model-oplist.kernel`'de yazılıdır. Sürüm yükseltmesi tam regresyon ister. OCCT'de Boolean sonuç sırası sürümler arasında değişmiştir (Araştırma B, K31).
9. **Yeniden üretim denetimi.** Aynı işlem listesi iki kez oynatılır; yüz imza tabloları ve şekil özeti aynı çıkmalıdır.

### 6.3 İçe alınan STEP'te neler güvenle yapılabilir (dürüst tablo)

Kaynak: `research/b-cad.md` (OCCT kılavuzu ve başlık dosyaları `metin_elde`; güvenilirlik belgelerdeki sınırlara dayanan nitel değerlendirmedir, ölçüm değildir).

| İşlem | Yol | Güvenilirlik | Sınır |
| --- | --- | --- | --- |
| Kesme, ekleme (Boolean) | `BRepAlgoAPI_Cut/Fuse`, `SetNonDestructive`, gerekirse `SetFuzzyValue` | Geçerli girdide yüksek; kötü STEP'te orta | Argümanlar geçerli olmalı; büyük tolerans ve teğetlik hata verir |
| Delik | Döndürülmüş araç katısı + Cut (`BRepFeat_MakeCylindricalHole` yalnız düz silindir) | Yüksek | Havşa ve kademe araç katısıyla |
| Pah | `BRepFilletAPI_MakeChamfer` | Orta–yüksek | Yayılma ve köşe sorunları fillet gibi |
| Yuvarlatma | `BRepFilletAPI_MakeFillet` | Basit dışbükey kenarda orta–yüksek; köşe birleşimi, karışık kenar ve B-spline'da düşük–orta | Teğet zincir boyunca kendiliğinden yayılır (seçilmeyen kenar da yuvarlanır); kısmi sonuç dönebilir |
| Kalıptan çıkma açısı | `BRepOffsetAPI_DraftAngle` | Orta | Yalnız düzlem, silindir ve koni; topolojiyi değiştiremez |
| Kabuk | `MakeThickSolidByJoin` | Düşük–orta | Bazı modlar belgeye göre "tam uygulanmadı" |
| Yüz öteleme | Düzlemsel yüz + dik komşularda araç prizması + Boolean; genel durumda `BRepOffset_MakeOffset::SetOffsetOnFace` (sıfır global ofset) | Dik komşuda orta–yüksek; eğik ve eğri komşuda düşük | **OCCT'de doğrudan "yüzü taşı" API'si yok**; ikinci yol kaynak kodundan çıkarım, test edilmedi |
| Detay silme | `BRepAlgoAPI_Defeaturing` | Orta | Özellik tanımaz, yüzleri biz veririz; silemezse uyarı verip devam eder: `HasWarnings()` zorunlu kapı |
| Aynı yüzeydeki yüzleri birleştirme | `ShapeUpgrade_UnifySameDomain` | Yüksek | Bütün yüz indekslerini değiştirir; başvurular geçmişle taşınır |
| Parametrik ölçüyü değiştirme ("bu deliği 8'den 10'a çıkar") | — | **Yapılamaz** (özellik ağacı yok) | Yerine: detay silme + yeni delik, ya da yüz öteleme. Özellik tanıma için Analysis Situs (BSD-3, C++) var, Python bağlaması yok |
| PMI (AP242 GD&T) | OCP `XCAFDoc_DimTolTool` ile okunur | Okuma kısıtlı | Düzenleme yüz kimliklerini değiştirir; PMI → yüz bağları taşınmazsa PMI bayatlar. Çıktıda "bayat" işaretlenir ya da yazılmaz |
| Kötü STEP toleransı | Okuma parametreleri (`read.maxprecision.*`) | — | Varsayılanla tolerans 1 mm mertebesini aşabilir; içe almada ölçülür, eşik aşılırsa dur ve kart aç |

### 6.4 STL (tarama): referans, ölçüm, karşılaştırma

| Yapılabilen (açık kaynak) | Yapılamayan |
| --- | --- |
| Okuma, onarım: trimesh (MIT); PyMeshLab (GPL-3.0, AGPL ile uyumlu; §18) | Tasarım niyetli parametrik katıya otomatik geçiş |
| CAD ile hizalama: ICP (Open3D, trimesh); kaba başlangıç hizası ister | Otomatik bölge bölütleme → özellik → kısıtlı çizim akışı (Geomagic Design X gibi) |
| Sapma haritası: `trimesh.proximity.signed_distance`; CAD üçgenleme sapması ölçülen sapmadan küçük seçilir | Otomatik NURBS yama yerleşimi |
| Düzlem, silindir, küre uydurma (pyransac3d, Open3D yalnız düzlem) | Koni RANSAC'ı (incelenen kütüphanelerde yok) |
| Kesitten çap, aralık ve et ölçüsü + uydurma artığı | Tarayıcının sistematik hatasını (ölçek) uydurmayla düzeltmek |
| Ağdan çok yüzlü (faceted) katı: Boolean'a girebilir, ağır | Serbest yüzeyde katı model (elle yapılır) |

**Taramadan modele** iş türü yarı otomatiktir. Prizmatik parçada ilkel uydurma, ajana ölçü ve eksen önerir; ajan parametrik modeli kurar; sapma haritası modeli taramayla karşılaştırır. Serbest yüzeyde tarama yalnız görsel referanstır.

**Doğruluk** (önemli düzeltme). Bulunan çalışmalar iPhone LiDAR için **santimetre** sınıfı doğruluk bildiriyor (ör. ±1 cm, RMSE 1–1,5 cm; Araştırma B, K33, `ikincil_kaynak`). Eski profildeki "≥1 mm" alt sınırı iyimserdir. v1'de taramadan türetilen her ölçünün belirsizliği atölye ayarındaki alet kaydından gelir (`instruments/<id>.yaml`). Belirsizlik bir referans parçanın kendi ölçümümüzle taranmasıyla kayda alınmadan tarama ölçüsü kritik geçmede kullanılamaz (UNCERT-01). Satıcı sayısı kaynak sayılmaz.

### 6.5 Görseller

Görseller gerçek modelden üretilir (§9.2). Eski `kart_gorsel.py` ve `gorsel.py` `mech`'e taşınır:

- ölçü vurgulu görünüş;
- ölçülü kesit;
- izometrik;
- seçenekler aynı ölçekte;
- değişen yüz renkli önce–sonra (eski `_degisen_yuzler` yüz imzasıyla çalışıyordu; v1'de işlem listesinin `faces_changed` alanından).

### 6.6 Kabul ölçütleri (Faz 3)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| B1 | Belirlenimcilik: aynı işlem listesini iki kez oynatma | Test derleminin %100'ünde şekil özeti ve yüz imza tablosu aynı | öneri |
| B2 | Sessiz başarısızlık | 0: her başarısız ya da kısmi işlem kart açar (bilerek bozulmuş 12 vakada 12/12) | öneri |
| B3 | İşlem başarı oranı (derlem: 20 STEP × 6 işlem türü; açık kaynak ve sentetik parçalar) | Boolean, delik ve pahta ≥ %95; fillet, draft ve detay silmede başarı ya da açık "yapılamadı" %100 (oran raporlanır, eşik yok) | öneri |
| B4 | Hacim özdeşlikleri: V(A−B) = V(A) − V(A∩B) | bağıl fark ≤ 1e-6 | öneri (`turetilir`; eşik T-02) |
| B5 | Yüz başvurusu: derlemde indeks dışı eşleşme | %100'ü akışa bildirilir; belirsizlikte 0 otomatik seçim | öneri |
| B6 | Sapma haritası: bilinen öteleme verilmiş sentetik tarama (0,5 mm) | ölçülen ortalama sapma 0,5 ± 0,05 mm | öneri |
| B7 | İlkel uydurma: sentetik silindir (Ø20, gürültü σ = 0,1 mm) | çap hatası ≤ 0,05 mm | öneri |
| B8 | İçe alma: en büyük tolerans eşiği aşan STEP | dur + kart, 3/3 | öneri |

---

## 7. Parça C — Tanımlama (durum tespiti)

Tanımlama sabit bir anket değildir. Veriyi önce ajan analiz eder, sonra yalnız veriden çıkmayanı sorar. Bu bölüm Faz 2 kapsamındadır; alan analizleri Faz 3'te paketlerle gelir.

### 7.1 Akış

```
1 İş türü            ──>  2 Veri analizi           ──>  3 Sorular (ağaç)            ──>  4 Anlama özeti
  (5 tür; paket            (paketin analizcileri;        (yalnız veriden çıkmayan;       (istekler + sayısal ölçüt,
   ekleyebilir)             sonuçlar + görseller,         neden önemli + cevapsız         yöntem, paket, standart
                            kaynak: derived)              varsayılan + görsel)            haritası) → kalite → DUR
```

**1. İş türü.** Çekirdek beş türü veri olarak taşır (şema `work-type`):

| Kimlik | Tür | Model türü | Tipik paket |
| --- | --- | --- | --- |
| `new_part` | Sıfırdan parça | parametric | mech (+ print3d / molding) |
| `mold_for_part` | Verilen parçaya kalıp | hybrid | mech + molding |
| `modify_model` | Mevcut modelde değişiklik | imported | mech |
| `analysis` | Analiz | none / imported | analysis |
| `scan_to_model` | Taramadan model | parametric (+ STL referans) | mech |

Tür önerisi girdi dosyalarından gelir (ör. STEP + "kalıp" → `mold_for_part`). Türü baş mühendis proje açarken seçer ya da onaylar.

**2. Veri analizi.** İş türünün `analyzers` listesi soru sorulmadan önce çalışır. Her analizcinin sonucu kaynak `derived` olan değerlerdir ve gerçek modelden üretilmiş görsel taşır. Örnekler:

- `mold_for_part`: çekme yönü adayları, çıkma açısı haritası, negatif açı bölgeleri, et kalınlığı haritası, izdüşüm alanı, hacim ve kütle (yoğunluk malzeme profilinden; yoksa `assumption`). Hepsi deterministik ve açık kaynakla yapılabilir (Araştırma C, a#1–#6).
- `modify_model`: içe alma raporu (katı sayısı, geçerlilik, en büyük tolerans), yüz türleri dağılımı, delik ve yuvarlatma adayları (yüzey türü + yarıçap).
- `scan_to_model`: ağ onarım raporu, kapalılık, ilkel uydurma adayları, simetri adayı.
- `new_part`: girdi yoksa analiz yok; varsa (eskiz, rakip ürün taraması) ölçü çıkarma.

**3. Sorular.** Soru ağaçlarını alan paketi tanımlar (şema `question-tree`). Her düğümde zorunlu alanlar:

- soru metni;
- **neden önemli** (`why`): hangi karar ya da hesap bu cevaba dayanıyor;
- **cevap gelmezse ne varsayılacağı** (`default_if_unanswered`): değer, kaynak, kart açar mı;
- **görsel** (`visual.generator`): gerçek modelden ya da veriden;
- aciliyet (`now` ya da `stage_end`).

Düğüm kuralları:

- **Veriden çıkan soru sorulmaz.** Düğüm `derive_from` taşır; analiz sonucu ifadeyi karşılarsa cevap `derived` kaynağıyla yazılır ve akışa bir satır düşer (ör. "Çekme yönü +Z: tek aday, veriden çıkarıldı").
- **Cevap alt soruları açar.** `children[].when` güvenli bir ifadedir (eski `formul_hesapla` gibi AST sınırlı; fonksiyon çağrısı yok).
- **DUR kategorisindeki soru varsayılanla geçilmez.** Düğümün `stop_category` alanı varsa iş o konuda durur.
- **Az soru.** Paket ağacı en çok `max_questions_per_stage` (politika) kadar "şimdi" sorusu üretebilir; geri kalanı aşama sonu paketine girer.

**4. Bulgular.** Çelişki, sayısız istek ve gözden kaçan şey yakalanır. Gerekirse alternatif önerilir. Bunlar kontrol kurallarıdır (`work-type.contradiction_rules`) ve soru düğümlerinin `findings` alanından gelir:

| Bulgu türü | Örnek | Dayanak |
| --- | --- | --- |
| Çelişki | "Tek parça" istenmiş ama verilen STEP'te 2 katı var | içe alma raporu |
| Sayısız istek | "Sağlam olsun" → ölçüt önerisi: "50 N'da emniyet katsayısı ≥ 2" (öneri kaynağı yazılır; onay sorusu açılır) | requirement şeması: onaylı zorunlu istek ölçütsüz olamaz |
| Gözden kaçan | 6 yüzde çıkma açısı en küçük değerin altında; negatif açı var ama sürgü sorusu cevaplanmamış | analiz + kural |
| Alternatif | "Bu adette kalıp maliyeti karşılamaz → 3B baskı ya da silikon kalıp" | `molding.tooling_breakeven` hesabı. Kalıp maliyeti girdisi kaynaksızsa bulgu "varsayıma dayanıyor" uyarısıyla çıkar; kesin dil kullanılmaz |

**5. Anlama özeti** (şema `intake-summary`). İçerik:

- iş türü;
- analizlerin özeti ve görselleri;
- her sorunun durumu (cevaplandı, veriden çıkarıldı, varsayıldı, bekliyor);
- bulgular;
- istek listesi (`requirements.yaml`, sayısal ölçütleriyle);
- yöntem (üretim yöntemi DUR kararıdır; K kaydı);
- alan paketleri ve sürümleri;
- standart haritası özeti (madde sayısı, paralı madde, doğrulanmamış madde).

Özet önce kalite mühendisine (temiz bağlam), sonra baş mühendise DUR kartı olarak gider. **Onay olmadan tasarım başlamaz:** G0 kapısının ön koşuludur.

### 7.2 Kabul ölçütleri (Faz 2 motoru, Faz 3 paket ağaçları)

Ölçüm düzeni: 3 sentetik tanımlama vakası. Sorulması gereken ve veriden çıkan sorular önceden yazılıdır.

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| C1 | Veriden çıkarılabilen soruyu sorma | 0 (3 vakada) | öneri |
| C2 | Her soruda neden, varsayılan ve görsel | %100 (şema zorunlu; negatif şema testi var) | şema |
| C3 | "Şimdi" soru sayısı, vaka başına | ≤ 5 | öneri |
| C4 | Bilerek konmuş çelişki, sayısız istek ve gözden kaçan şey | 9/9 yakalanır (vaka başına 3) | öneri |
| C5 | Onaysız anlama özetiyle tasarım adımı | engellenir (G0 ön koşulu testi) | öneri |
| C6 | DUR kategorisindeki soru varsayılanla geçer mi | hayır, 3/3 test | kesin karar |

---

## 8. Parça D — Soru politikası

### 8.1 Kurallar

- **Durup sorar** (DUR, `hold`). Kesin karar 7'deki sekiz kategori: `manufacturing_method`, `material`, `main_dimensions`, `standard_deviation`, `cost_impact`, `release_production`, `requirement_change`, `chief_only_info`. Ayarda bu liste yalnız genişletilebilir; şema sekizinin de bulunmasını zorunlu tutar.
- **Geri kalan her şey geçici karardır** (`provisional`):
  1. Görseli ve gerekçesiyle akışa bir satır olarak düşer (şema `stream-event`: görsel zorunlu).
  2. Ayrı dalda ilerlenir (`<kod>/karar/K-nn-x`); bağımlı işler işaretlenir; en az bir alternatif kayda geçer.
  3. Baş mühendis bir sonraki kapıya kadar itiraz edebilir (akış satırında ya da kartta "İtiraz et").
  4. İtiraz gelirse karar `objected` olur; ekip ya alternatife döner (`objected_reverted`: bağımlı işler bağımlılık kaydından listelenir) ya da gerekçeyle sürdürmeyi önerir. Sürdürmenin kendisi baş mühendis onayı ister (`objected_kept`).
  5. İtiraz gelmezse kapı geçişiyle karar `accepted_at_gate` olur. Kapı kartı itirazsız geçici kararları listeler; kapıyı onaylamak onları da onaylamaktır. Kart bunu açıkça yazar.
- **Kategoriyi kim belirler?** Kategoriyi kararı açan rol yazar. Ama kural tabanlı sınıflayıcı da çalışır ve hangisi daha sıkıysa o geçerli olur. Sınıflayıcı şunlara bakar:
  - karar bir `main_dimensions` olarak işaretli parametreyi değiştiriyor mu;
  - bir malzeme ya da üretim profilini değiştiriyor mu;
  - maliyet hedefine dokunuyor mu;
  - bir standart maddesinin kabul ölçütünü gevşetiyor mu;
  - istek listesini değiştiriyor mu.

  "Neyin sorulacağını kurallar belirler, modelin kanaati değil" ilkesinin karşılığıdır.
- **Acil olmayan sorular aşama sonunda toplu gelir.** `urgency: stage_end` soruları ve inceleme bekleyen kararlar `stage finish` sırasında tek bir "aşama sonu soru paketi" kartında toplanır.
- **Açık geçici karar sınırı.** El kitabı §14'teki varsayılan 5'tir (ayarda `max_open_provisional`). Sınır doluysa yeni geçici karar açılmaz; ekip bağımsız işe geçer.

### 8.2 Ölçüm ve eşik ayarı

Her aşama sonunda çekirdek şunları hesaplar (kaynak: `decisions.yaml` + `events.jsonl`; ayrı kayıt gerekmez):

| Ölçü | Tanım |
| --- | --- |
| `questions_asked` | Aşamada baş mühendise giden DUR soruları ve kartları |
| `provisional_made` | Açılan geçici karar |
| `provisional_reverted` | İtiraz edilip geri alınan geçici karar |
| `revert_rate[kategori]` | Son `revert_window` geçici kararda geri dönen oranı |
| `time_to_answer` | DUR kartının açılışından cevabına geçen süre |

**Eşik ayarı.** Bir kategoride `revert_rate > revert_rate_threshold` olursa çekirdek o kategoriyi DUR listesine almayı **önerir** (kart). Ayarı baş mühendis değiştirir; sistem kendi kendine gevşemez ve sıkılaşmaz. Sekiz kesin kategori hiçbir zaman listeden çıkmaz.

Varsayılan değerler `revert_window = 10` ve `revert_rate_threshold = 0,2`'dir (öneri, T-06).

### 8.3 Kabul ölçütleri (Faz 2)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| D1 | DUR kategorisindeki karar geçici karar olarak açılabilir mi | hayır: şema + sınıflayıcı testi, 8/8 kategori | kesin karar |
| D2 | Geçici karar akışta görselsiz görünür mü | hayır (şema) | şema |
| D3 | İtiraz edilen kararın bağımlı işleri listelenir | 3/3 senaryo | öneri |
| D4 | Kapı geçişinde itirazsız geçici kararlar "kapıda kabul" olur ve kapı kartında listelenir | 3/3 senaryo | öneri |
| D5 | Aşama ölçüleri her `stage finish`'te hesaplanır ve akışa düşer | %100 | öneri |
| D6 | Eşik aşılınca öneri kartı açılır, ayar kendiliğinden değişmez | 2/2 test | öneri |

---

## 9. Parça E — Rapor akışı

### 9.1 Canlı akış

**Her adım bir satır** (şema `stream-event`, `line` en çok 200 karakter). Satırda:

- saat (sistemden);
- rol;
- tek satır metin;
- küçük görsel;
- kart ve karar bağlantıları;
- kontrol özeti (ENGEL/UYARI sayısı);
- commit kısa özeti.

**Kaynaklar:**

- çekirdek: adım, kart, karar, kontrol, kapı, baskı/üretim, kalite, hesap;
- ajan adaptörü: normalleştirilmiş ajan olayları;
- paketler: analiz ve model değişikliği.

**Kalıcılık.** Kalıcı olaylar `records/events.jsonl`'e yalnız eklenir. Ajanın token akışı ve araç ayrıntısı kalıcı değildir; ayrıntı ajan aracının kendi oturum kaydında durur (Claude Code'da `~/.claude/projects/…`, 30 gün).

**Günlük ile ilişki.** Günlük (`records/log/YYYY-MM-DD.md`, el kitabı §11) akışın kalıcı olaylarından üretilen okunur hâlidir. Günlük düzeltilmez; düzeltme yeni kayıttır.

### 9.2 Görseller gerçek modelden

| Görsel | Üretici | Nerede |
| --- | --- | --- |
| Çoklu görünüş (ön, üst, yan, izometrik; gizli çizgi) | `mech.views` (eski `gorsel.izometrik`, `kart_gorsel.gorunus`) | Kart, akış, gün sonu |
| Kesit | `mech.section` (eski `gorsel.kesit`) | Geçme kartı, karar kartı |
| Ölçülü görünüş | `mech.dimensioned` (eski `param_etkisi`) | Parametre ve varsayım kartları |
| Önce–sonra (değişen yüz renkli) | `mech.diff`: işlem listesindeki `faces_changed` ya da iki commit'in yüz imza farkı | Akış (model değişikliği), geçici karar |
| Analiz grafikleri | Hesap kaydındaki `charts` → SVG (matplotlib); gerçek sonuç verisi, temsilî değil | Hesap ekranı, karar kartı |
| Analiz haritaları | Paket analizcileri (çıkma açısı, et kalınlığı, sapma) | Tanımlama, model ekranı |
| Metin görseli (geometrisi olmayan kart için) | `core.report.text_visual` (eski `_metin_gorseli`) | Kapı ve tutarlılık kartı |

**Görsel kuralları:**

- **Önbellek.** Görseller girdi özetiyle önbelleğe alınır (eski `_onbellekli`). Aynı commit'te yeniden üretilmez.
- **Sayı sınırı.** Kayıt başına görsel sınırı el kitabı §14'te 3'tü (açık konu). v1'de akış satırında 1 küçük görsel, kartta türüne göre en çok 4 görsel önerilir (öneri, T-02).
- **SVG güvenliği.** SVG içindeki betik ve dış bağlantılar ayıklanır (eski panel bunu yapıyordu).

### 9.3 Gün sonu özeti

Ayarlı saatte (`daily_summary.time`) ya da istenince `records/summaries/YYYY-MM-DD.md` üretilir. Akışa da tek satır düşer. Bölümleri:

1. **Verilen kararlar:** DUR onayları, geçici kararlar (itiraz süresiyle), kapıda kabul edilenler.
2. **Bekleyenler:** cevap bekleyen DUR kartları (bekleme süresiyle), yanıt bekleyen yorumlar, aşama sonu soru paketi.
3. **Riskler:**
   - açık ENGEL ve UYARI;
   - güvenilmez ya da alan dışı hesaplar;
   - tutarsız büyüklükler;
   - dayanağı değişmiş kararlar;
   - açık kalite bulguları;
   - "kanıt bekliyor" durumundaki zorunlu istekler;
   - doğrulanmamış standart maddeleri.
4. **Ajan kullanımı:** çalıştırma sayısı, tur, tahmini maliyet (API anahtarında).

"Son okumandan beri" bölümü (el kitabı §11) özetin kişiye göre süzülmüş hâlidir. Okundu işareti panelde tutulur (eski `/okundu` ucu).

### 9.4 Kabul ölçütleri (Faz 2)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| E1 | Her `mekanik step` tam bir akış satırı üretir | %100 (commit'li) | öneri |
| E2 | Akış görselleri modelden üretilir; aynı commit için ikinci üretim önbellekten | önbellek isabeti %100 (test) | öneri |
| E3 | Önce–sonra görselinde değişen yüzler | sentetik 5 değişiklikte değişen yüz kümesi beklenenle aynı | öneri |
| E4 | Gün sonu özetinin bölümleri | 4/4 bölüm; boş bölüm "yok" yazar | öneri |
| E5 | `events.jsonl` yalnız eklenir | yeniden yazma girişimi testte reddedilir | ilke (el kitabı §11) |

---

## 10. Parça F — Mühendislik güvencesi

**Hedef: fark edilmeden karara ulaşan sıfır hata.** "Sıfır"ın ölçülebilir karşılığı iki şeydir:

1. **Tohumlanmış hata derlemi:** sistemin yakalaması gereken bilinen hata türlerinden kurulmuş sentetik vakalar. Her biri karar ya da kapı aşamasına ulaşmadan yakalanmalıdır.
2. **Kapıdan sonra bulunan hata sayısı:** pilot çalışmalarda, her biri bir regresyon vakasına dönüşür.

Kabul ölçütleri §10.11'de.

### 10.1 Kaynaksız sayı yok

- **Kayıtta.** Her değer `quantity` (değer + birim + kaynak) olarak yazılır. Şema kaynaksız değeri reddeder. `derived` formül, `decision` karar veren rol ister (common şeması). Esneme gibi parametre olmayan sayılar da etiket taşır (Ö-04).
- **Model ve hesap kodunda** (SOURCE-02, yeni). Model ve hesap betiklerinde (`model/model.py`, `calcs/*.py`) bir AST taraması sayısal sabitleri arar:
  - İzin listesi: {0, 1, 2, 0,5, 90, 180, 360} (öneri).
  - Listedeki sabitler matematiksel sabittir; listenin dışında kalan her sabit `params.yaml`'dan ya da `const()` ile kaynaklı gelmelidir.
  - Keşif ve geliştirmede UYARI, serbest bırakmada ENGEL.
- **Paket kodunda.** Kontrol fonksiyonlarındaki eşikler katalog ya da profilden okunur. Paket CI'sinde aynı AST taraması çalışır (Ek B bulgu 2'deki 9 eşik bu yüzden taşınır).

### 10.2 Kritik hesaplar iki bağımsız yöntemle

- **Kritik hesap tanımı:** bir zorunlu isteğin kanıtı, güvenliği etkileyen, bir DUR kararının dayanağı ya da bir baskı/üretim isteğinin dayanağı olan hesap. İşaret iki yoldan gelir: kararı açan rol koyar, ayrıca kanıt ve dayanak bağlarından kendiliğinden türetilir. Hangisi daha sıkıysa o geçerlidir.
- **Bağımsızlık tanımı:** ikinci yöntem farklı bir yöntem sınıfı (`level` 1/2/3) ya da farklı araç ve farklı formül olmalı. Aynı formülün yeniden yazılması bağımsız sayılmaz. Örnek: E-30'daki formül hatası VLM ile bulundu.
- **Uyuşmazlık sınırı** büyüklük başına kural kataloğundadır (`limit` + kaynak). Varsayılan: eski HESAP-01'in bağıl %10'u (Ö-22, onay bekliyor). Sınır aşılırsa CALC-03 ENGEL verir: hesaba dayanan karar onaylanamaz, kapı ve baskı isteği açılmaz.
- **Kanıt seçimi.** Düşük doğruluklu hesap, yüksek doğruluklu olanın "yerini aldı" diye işaretlenir (eski HESAP-01). Kanıt olarak yüksek doğruluklu olan kullanılır.

### 10.3 Geçerlilik alanı

NASA-STD-7009B'nin üç bölgesine göre (Araştırma D, 1.K):

- **M&S limits:** aracın sonuç üretebildiği en geniş alan;
- **domain of verification:** çözümün doğru olduğu gösterilmiş alan;
- **domain of validation:** referansla karşılaştırması iyi olan alan.

**Analiz aracı kaydı.** Her analiz aracı ve yöntemi (ör. scikit-fem doğrusal elastik, NeuralFoil, kapama kuvveti formülü) standart kütüphanesinde bir kayıt taşır (`stdlib/tools/*.yaml`). Kaydın alanları:

- amaçlanan kullanım;
- sınırlar;
- doğrulama alanı;
- geçerleme alanı (çıktı büyüklüğü başına);
- varsayımlar;
- bilinen kusurlar;
- sürüm.

**Her hesap çalıştırmasında** girdi kümesi bu bölgelerle karşılaştırılır:

| Bölge | Sonuç durumu | Kanıt olabilir mi |
| --- | --- | --- |
| Geçerleme alanında | `ok` / `marginal` / `bad` (hesabın kendi değerlendirmesi) | Evet |
| Yalnız doğrulama alanında | Uyarı etiketi (placard): "doğrulanmış, geçerlenmemiş" | Evet, uyarıyla; kartta görünür |
| Yalnız sınırlar içinde (dış değerleme) | Placard + aşılan sınırın türü ve miktarı + sonuca etkisi (M&S 26 b) | Yalnız baş mühendis gerekçeli onayıyla |
| Sınır dışında | `unreliable` ("güvenilmez") | **Hayır** (CALC-04 ENGEL) |
| Alan tanımsız | `in_domain: null` | Kart açar: "geçerlilik alanı tanımsız" |

Örnek: E-39'da NeuralFoil eğitim alanı dışındaydı (güven 0,01–0,06). v1'de bu sonuç sınır dışı sayılır ve kanıt olamaz.

### 10.4 NASA-STD-7009B'nin uygulanması

Kaynak: NASA-STD-7009B (onay 2024-03-05, 43 gereksinim) ve NASA-HDBK-7009B (kapak onayı 2026-02-03). İkisi de standards.nasa.gov'dan okundu (`metin_elde`; Araştırma D, §1).

Uyarlama ilkesi: "Tailoring … is acceptable when formally approved by the delegated NASA Technical Authority". Bu araçta o rolün karşılığı baş mühendistir. Uygulanmayan her madde gerekçesiyle bir **uyarlama kaydına** yazılır (`stdlib/process/nasa-7009b-tailoring.yaml`; çalışma bazında ezilebilir) ve baş mühendis onaylar.

**Uygulanan maddeler:**

| Konu | 7009B maddesi | mekanik'te karşılığı |
| --- | --- | --- |
| Amaçlanan kullanım | [M&S 40] | Analiz aracı kaydında zorunlu alan |
| Kritiklik | [M&S 6], Ek D | Hesap çalıştırmasında `criticality` (sonuç × etki); kırmızı kutu "kritik hesap" sayılır (§10.2) |
| Kabul ölçütleri | [M&S 43] | Araç kaydı; eşikler `decision` kaynaklı ("This Standard levies no requirements with respect to what levels to achieve") |
| Gerçek sistem verisi ve soyağacı | [M&S 10], [M&S 24] | Kaynak etiketi + belirsizlik; girdi soyağacı seviyesi etiketten türetilir. Eşleme: `assumption` → Notional/Informed, `standard`/`decision` → Specified, `derived` → Derived, `measured:*` → Measured. Zincir kuralı: bir hesabın çıktısı başka hesabın girdisiyse soyağacı kaynağın güvenilirliğiyle sınırlıdır. |
| Birim ve eksen takımı | [M&S 46] | Birim zorunlu (şema); eksen takımı model kaydında |
| Varsayımlar | [M&S 11] | `assumption` + kart/varsayım listesi; hesap kaydında `notes` |
| Sınırlar, doğrulama ve geçerleme alanı | [M&S 13], [M&S 16], [M&S 18] | §10.3 |
| Doğrulama ve geçerleme | [M&S 15], [M&S 17] | Araç kaydındaki doğrulama vakaları (analitik çözüm) regresyonda çalışır. Geçerleme deney ya da yüksek doğruluklu modelle; asgari ölçüt belirsizlik aralıklarının örtüşmesi (Ek E.3.4) |
| Kullanım değerlendirmesi | [M&S 22], [M&S 23] | Hesap çalıştırılmadan önce önerilen kullanım ile izinli kullanım karşılaştırılır: kabul ya da ret |
| Alan dışı kullanım | [M&S 26] | Placard: sınır türü, aşım miktarı, etkisi |
| Uyarı ve hata iletileri | [M&S 27] | Çözücü günlüğü ayrıştırılır; açıklanmamış uyarı varsa sonuç "açıklama bekliyor" |
| Sonuç belirsizliği | [M&S 28], [M&S 29], [M&S 33], [M&S 34] | Her sonuçta `uncertainty` ya da açık "belirsizlik tahmini yok" beyanı; boş bırakmak hata. Emniyet katsayısının hangi belirsizliği karşıladığı yazılır |
| Duyarlılık | [M&S 30] | Duyarlılık çalışması kaydı; "anahtar duyarlılık" işareti |
| Sonuç raporu | 4.3.8, [M&S 32] | Rapor şablonunda sekiz zorunlu uyarı satırı: kabul ölçütü sağlanmadı, varsayım ihlali, sınır ihlali, çalışma uyarıları, olumsuz kullanım değerlendirmesi, kurulum sorunları, feragatler, açık kusurlar. Kanıt yoksa uyarı kendiliğinden yazılır: "kanıt yok" sessizce "sorun yok" sayılmaz |
| Güvenilirlik değerlendirmesi | [M&S 48] (yetenek, 5 faktör), [M&S 31] (sonuç, 6 faktör), Ek E.2 | Faktörler ayrı ayrı 0–4 seviyeyle gösterilir; **tek bir güvenilirlik puanı üretilmez** ("combining of factor assessments … should be avoided") |
| Kusur takibi | [M&S 51] | Kart (`quality_finding`, `deviation`) + hata kaydı; açık kusur raporda uyarıdır |
| Risk | [M&S 49] | Gün sonu ve kapı kartındaki risk bölümü bu başlıklardan doldurulur |
| Yeniden üretme | §4 girişi ("re-established as a result of any changes") | Her kayıt commit'e bağlıdır; araç sürümü ya da girdi değişince kayıt bayatlar; bağımlılık kilidi değişince regresyon çalışır (Ek E.3.3) |
| ML vekil modeller | HDBK 4.5.2 | NeuralFoil gibi araçlar ayrı araç kaydı ve tam doğrulama/geçerleme ister |
| Üretken YZ ajanları | HDBK 4.5.3 | Ajanlar sonucu tahmin etmez, süreci yürütür. Sayılar her zaman betikten gelir; ajan metni model sonucu sayılmaz |

**Uyarlama adayı (T-12).** 7009B'de teknik inceleme faktörünün seviye 3'ü "Favorable independent peer review" ister. Peer review tanımı "persons of equal technical standing"dir. Yapay zekâ kalite mühendisinin incelemesi bu tanıma girmez (Araştırma D, 1.P, yorum). Tek kişilik ekipte bu seviye dışarıdan bir kişi gerektirir. Öneri: YZ incelemesi en çok seviye 2 sayılsın; kritik (kırmızı kutu) hesaplarda dış inceleme isteğe bağlı bir kart olsun.

### 10.5 Kalite mühendisi

§4.8'deki düzen geçerlidir. Temiz bağlamla çalıştığı yerler:

- her kapı isteği;
- her baskı/üretim isteği;
- anlama özeti onayı.

Bulgusu kapanmadan geçiş olmaz (QUALITY-01). Bulgu kapatmak gerekçe ister. YÜKSEK bulguyu kapatan ekip olsa bile kapı kartında "kapatılan YÜKSEK bulgular" listesi görünür; baş mühendis görmeden kapı geçmez.

### 10.6 Kapı kartında istek durumu

Her istek için durum (karşılandı | karşılanmadı | kanıt bekliyor) ve kanıtın yeri (şema `card.requirement_table`, B2). G4 ve G5'te zorunlu isteklerin hepsi "karşılandı" olmalıdır (REQ-01). Durum kanıttan türetilir; elle yazılmaz.

### 10.7 Diğer güvence kuralları

| Kural | Uygulama | Kaynak |
| --- | --- | --- |
| Kapanmış kararın dayandığı hesap değişirse karar yeniden incelemeye düşer | DECISION-01, `review_needed`, "dayanağı değişti" kartı | B5 |
| Ölçülmemiş gözlem tek başına tasarım değişikliği gerekçesi olamaz | Şema (decision) + kartta uyarı | B6 |
| Her hata bir regresyon testine dönüşür | Hata kaydı (8D) şemasında `regression_case` zorunlu. Kalite bulgusu ve E maddesi kapanırken "regresyon vakası" alanı doldurulur ya da "gerekmez" gerekçesi yazılır. CI, her kapalı hata kaydının vakasını çalıştırır. | el kitabı §13 |
| Kontrol değişince regresyon çalışır | `mekanik regress` CI'de her commit'te; bağımlılık kilidi değişince de | CLAUDE.md, 7009B Ek E.3.3 |
| Belirsizlikle uygunluk kararı | 1/4 kuralı (UNCERT-01). Ek: JCGM 106 karar kuralı: basit kabul ya da korumalı kabul; koruma bandı w = r·U, r `decision` kaynaklı. Sınıra yakın ölçüm "uygun" değil "belirsiz" sonucu verir. | ISO 14253-1, JCGM 106:2012 §8.3 (Araştırma D, 2.3) |

### 10.8 Standart haritası

G0'da çıkar (STDMAP-01: G0 kapısının ön koşulu). Kaynağı:

- anlama özetinin standart haritası önizlemesi;
- standart kütüphanesinin `applies_to` ifadeleri (iş türü, paket, ürün özelliği);
- müşteri şartnamesi.

**Her maddenin alanları** (şema `standard-item`): amaç, neden burada, test yöntemi, kabul ölçütü (sayı + kaynak), kanıt, doğrulama durumu, tür.

- Doğrulama durumu: `text_in_hand` (metin elde) | `secondary_source` (ikincil kaynak) | `unverified` (doğrulanmadı).
- Tür: `regulation` (mevzuat) | `customer_spec` (müşteri şartnamesi) | `standard` | `guideline` (kılavuz) | `literature` (literatür).

**Tik** yalnız kanıtla ve kalite mühendisinin kontrolünden sonra konur. Şema bunu zorunlu tutar: `tick.checked = true` ise kanıt ≥ 1, `quality_review` ve `status = met`.

**Kaynak önceliği** (`priority` alanı türetilir):

1. mevzuat (AB: EUR-Lex; TR: mevzuat.gov.tr, Resmî Gazete);
2. müşteri şartnamesi;
3. açık teknik kaynaklar (JCGM, NASA, MIL, NIST);
4. üretici kılavuzları;
5. paralı standartlar.

**Paralı standart.** Önce açık karşılık aranır (`open_equivalent.searched` zorunlu). Bulunamazsa satın alma listesine gerekçesiyle girer (`procurement`); satın almanın kendisi maliyet etkisidir ve DUR'dur.

**Mevzuat atfı** okuma tarihi taşır (sistem saati). Mevzuat değişkendir; okuma tarihi 365 günden eskiyse atıf yeniden doğrulanmak üzere uyarı verir (öneri).

**Kütüphanenin başlangıç içeriği** (Araştırma D, §2; `stdlib`, §12):

| Belge | Künye | Durum |
| --- | --- | --- |
| (EU) 2023/988 GPSR | CELEX 32023R0988 | ikincil_kaynak: EUR-Lex bot korumasından okunamadı |
| (EU) 2023/1230 Makine Tüzüğü | CELEX 32023R1230; uygulama 20.1.2027 (TR metniyle çapraz doğrulandı) | ikincil_kaynak |
| REACH | CELEX 32006R1907 | ikincil_kaynak |
| RoHS | CELEX 32011L0065 | ikincil_kaynak |
| 7223 sayılı Kanun | RG 12/03/2020, 31066 | metin_elde |
| Genel Ürün Güvenliği Yönetmeliği | RG 11.03.2021, 31420 | metin_elde. Not: hâlâ 2001/95/AT'ye dayanıyor, GPSR'ye uyumlu yeni yönetmelik bulunamadı (okuma 2026-11-06) |
| PGD Çerçeve Yönetmeliği | RG 10/7/2021 | metin_elde |
| KKDİK | Son değişiklik RG 23/12/2023, 32408; ilk kayıt son tarihi 31/12/2026 | metin_elde |
| Makine Emniyeti Yönetmeliği | RG 16.10.2026, 33402 | metin_elde |
| TR RoHS | — | metin_elde |
| JCGM 100:2008 (+Amd.1:2026), JCGM 106:2012 | — | metin_elde. JCGM PDF'leri telif nedeniyle repoya konmaz, yalnız bağlantı verilir |
| NASA-STD-7009B, NASA-HDBK-7009B | — | metin_elde |

### 10.9 Kalite ve güvence verisinin yeri

| Kayıt | Şema / dosya |
| --- | --- |
| Hesap ve geçerlilik | `calculation` (`validity`, `cross_check`, `critical`) |
| Kanıt | `evidence` |
| Standart haritası | `standard-item` |
| Analiz aracı kaydı | `stdlib/tools/*.yaml` (Faz 1'de şeması kesinleşir; alanları §10.3 ve §10.4'te) |
| Kalite incelemesi | `records/quality/*.yaml` |
| Hata kaydı | `stdlib` dışında, kurum reposunda `errors/H-nnn.md` + regresyon vakası |

### 10.10 Bilerek yapılmayan

- **Tek güvenilirlik puanı üretilmez** (7009B Ek E.2).
- **Ajanın kendi "emin değilim" bildirimi** ek tetikleyicidir; sistem buna dayanmaz (el kitabı §7).

### 10.11 Kabul ölçütleri

| # | Ölçüt | Eşik | Faz | Kaynak |
| --- | --- | --- | --- | --- |
| F1 | Tohumlanmış hata derlemi: 30 vaka (kaynaksız sayı ×4, bağımsız sayılı geçme ×3, alan dışı sonuç ×3, uyuşmayan iki yöntem ×3, ikinci yöntemsiz kritik hesap ×2, bayat onay ×3, ölçümsüz gözleme dayanan karar ×2, dayanağı değişen karar ×2, kanıtsız tik ×2, kalite YÜKSEK açıkken kapı ×2, G5'te karşılanmamış zorunlu istek ×2, kritik geçmede biçim aleti ×2) | 30/30 kapı ya da karar öncesi yakalanır | 1: eski sistemin yakaladığı 21 vaka (kaynaksız 4, bağımsız sayı 3, bayat onay 3, uyuşmayan iki yöntem 3, ölçümsüz gözlem 2, dayanak 2, kalite 2, biçim aleti 2); 2: 30 vakanın tamamı | öneri |
| F2 | Her kontrolün "hep ENGEL" ve "hep GEÇTİ" sahte sürümü regresyondan geçemez | %100 kontrol | 1 | ölçü: eski `test_regresyon` |
| F3 | Model/hesap kodunda izin listesi dışı sayısal sabit (SOURCE-02, yeni) | Serbest bırakmada 0 | 2 | öneri |
| F4 | Kalite mühendisi çağrısı | Kapı ve baskı isteklerinin %100'ünde; açık YÜKSEK varken istek açılmaz (test) | 1 | B1 |
| F5 | Kapı kartında istek tablosu | Zorunlu isteklerin %100'ü (Faz 1, eski davranış); G4/G5'te karşılanmamış zorunlu istek varken geçiş 0 (REQ-01, Faz 2) | 1 / 2 | B2 |
| F6 | Pilot çalışmalarda kapıdan sonra bulunan hata | Her biri ≤ 7 gün içinde regresyon vakası olur; Faz 3 pilotunda sayı raporlanır | 2–3 | öneri |
| F7 | E-01…E-41'in "düzeltildi" ve "kısmen" olanları ile H-001 | %100'ünün v1'de test kimliği var (Ek B §11 eşlemesi) | 1 | Ek B |
| F8 | Standart haritası | G0 kapısı haritasız geçmez; kanıtsız ya da kalite incelemesiz tik 0 (şema + test) | 2 | şema |

---

## 11. Eklenti arayüzü

### 11.1 Bir paket neler ekleyebilir

| Katkı noktası | Ne | Kayıt defteri | Örnek |
| --- | --- | --- | --- |
| Kontroller | Saf fonksiyon: `WorkView` → `[CheckResult]`; kimlik `<paket>:<KURAL>`; kural kataloğu kaydı zorunlu | `checks` | `print3d:BED-01` |
| Hesap şablonları | Calc API ile yazılmış betik şablonu + araç kaydı (geçerlilik alanı) | `calc_templates` | `molding.clamp_force@1` |
| Soru ağaçları | `question-tree` şeması | `question_trees` | `molding.basics` |
| Kart türleri | Tür kimliği, zorunlu alanlar (ek JSON Schema), görsel üreteci, metin şablonları | `card_types` | `molding:side_action` |
| Profil türleri | Makine, malzeme ve süreç profilleri için JSON Schema; atölye ayarındaki `machines[].type` buna bağlanır | `profile_types` | `print3d.fdm_printer` |
| Standart maddeleri | `standard-item` (library: true) + `applies_to` | `standard_items` | `iso.20457.tolerances` |
| Analizciler | Tanımlama ve model ekranı için: girdi → `named_quantity[]` + görsel | `analyzers` | `molding.draft_map` |
| İş türleri | `work-type` şeması | `work_types` | — |
| Görsel üreteçleri | SVG/PNG üreten fonksiyon (önbellekli) | `visuals` | `mech.section` |
| Panel görünümleri | Önceden derlenmiş ES modülü; özel öğe (`<mekanik-print3d-bed>`) + yönlendirme adı + tip sözleşmesi | `panel_views` | tabla yerleşimi |
| Dil katalogları | `i18n/tr.yaml`, `en.yaml` | `i18n` | — |
| Regresyon vakaları | Her kontrol için geçen ve kalan alt vaka | `regression` | `cases/E-25/` |
| Dış araç tanımları | Ayrı program olarak çağrılan araç: komut, sürüm sorgusu, lisans notu | `external_tools` | OrcaSlicer CLI |

### 11.2 Keşif

- Python dağıtımı `mekanik-<id>`, giriş noktası grubu `mekanik.packages`: `id = "mekanik_print3d:PACKAGE"`.
- Çekirdek `importlib.metadata.entry_points(group="mekanik.packages")` ile bulur. Ayarda `packages.enabled` listesinde olmayan paket yüklenmez.
- Yalnız veri içeren paketler (soru ağacı, standart maddesi, profil) klasör olarak da verilebilir: `packages.data_paths`. Bu klasörde `package.yaml` bildirimi ve YAML dosyaları bulunur; kod çalıştırmaz.
- `mekanik pkg list` her paketin sürümünü, API uyumunu, katkılarını ve regresyon durumunu gösterir.

### 11.3 Bildirim (`package.yaml`)

```yaml
id: molding
version: 0.3.0                  # semver
api: 1                          # çekirdek eklenti API ana sürümü
requires: {core: ">=1.0,<2", packages: {mech: ">=1.0,<2"}}
provides:
  checks: [MOLD-DRAFT-01, MOLD-WALL-01, MOLD-UNDERCUT-01, MOLD-CLAMP-01, MOLD-FLOW-01, MOLD-QTY-01]
  calc_templates: [clamp_force_area@1, clamp_force_rule@1, cooling_time_slab@1, coolant_flow@1]
  question_trees: [molding.basics]
  card_types: [side_action, parting_line, gate_location]
  profile_types: [press, material]
  analyzers: [draft_map, undercut, wall_thickness, projected_area, pull_candidates, side_action_need]
  standard_items: [iso.20457.tolerances, iso.6751.ejector-pins, spi.mold-classes]
  panel_views: [draft_map, undercut, mold_concept]
  external_tools: [openinjmoldsim]
license: AGPL-3.0-or-later      # T-11 kararına göre
```

### 11.4 Sürümleme ve uyum

- **Paketler semver ile sürümlenir.** Çekirdek eklenti API'sinin ana sürümü (`api: 1`) değişirse uyumsuz paket yüklenmez ve açık bir hata verir.
- **Çalışma kullandığı paket sürümlerini sabitler** (`work.packages`). Kurulu sürüm farklıysa:
  1. çalışma açılırken uyarı çıkar;
  2. `mekanik pkg repin <kod>` ile yeni sürüme geçilir;
  3. geçişte kontroller ve hesaplar yeniden çalışır;
  4. dayanağı değişen kararlar `review_needed` olur;
  5. değişiklik bir adım olarak kayda geçer.
- **Kural kimlikleri** paket adıyla ad alanlıdır. Çekirdek kuralı aynı kimlikle ezilemez.

### 11.5 Güvenlik ve yalıtım

- **Paket kodu kayda yazamaz.** Kontrol ve analizci salt okunur `WorkView` alır ve sonuç döndürür; kaydı çekirdek yazar. Böylece paket "kendi işini onaylayamaz".
- **Paket hatası kaydedilir, süreç sürer.** Paket hatası `package_error` sonucu (UYARI) olur. Kontrol zaman aşımı ayardandır.
- **Panel görünümleri** yalnız aynı kaynaktan (same-origin) yüklenir. Görünümlerin API erişimi çekirdeğin istemcisi üzerinden, çalışma kapsamıyla sınırlıdır.
- **Regresyon sözleşmesi.** Her kontrolün en az bir geçen ve bir kalan regresyon alt vakası olmalıdır. `mekanik regress` sözleşme testi, vakası eksik kontrol için CI'yi kırar.

### 11.6 Örnek paket 1: `print3d` (3B baskı)

| Katkı | İçerik | Eski karşılığı / ders |
| --- | --- | --- |
| Profil türleri | `print3d.fdm_printer`: tabla x, y, z ve şekli, nozul; hepsi kaynaklı (`manufacturer:` …). `print3d.material`: yoğunluk vb. `print3d.process`: katman, çizgi genişliği, duvar sayısı, dolgu, kabuk; geçme görevi başına boşluk sınırları (`mech` paketinin `fit_limits` arayüzüne uyar), model düzeltme payı | Eski `profiller/uretim/*.yaml`; E-01 (yazıcı ölçüleri profile), E-23 (kabuk/dolgu kodda) |
| Kontroller | `BED-01` tabla sığması, döndürerek (E-22) · `CONTACT-01` tabla teması (E-25) · `SOLID-01` tek katı (E-05, E-28) · `WALL-01` en ince duvar (E-04) · `OVERHANG-01` çıkıntı/destek (E-04) · `SETTINGS-01` baskı isteğinde dilimleyici ayarı zorunlu ve hesap varsayımıyla aynı (E-41) · `ACCEPT-01` deneyden önce basılan parçanın kabul ölçümü: kütle, ağırlık merkezi (E-41, E-35) · `CORNER-01` iç köşe yarıçapı (Ö-16; **katalog onayından sonra**) | Eski `akis.baski`, `kart_gorsel.*` |
| Hesap şablonları | `print_estimate`: dilimleyici CLI varsa ondan (OrcaSlicer `--export-statistics` süre ve filament; PrusaSlicer G-code yorumu; CuraEngine süre), yoksa kabuk + dolgu kaba tahmini (`level 1`, "yaklaşık") · `mass_cog`: dolgu modeliyle kütle ve ağırlık merkezi | E-23, E-41 |
| Soru ağacı | `print3d.basics`: hangi yazıcı (ayardaki makineler) → malzeme (DUR) → işlevsel yüzler ve yön kısıtı → adet → yüzey. `derive_from`: tabla sığması ve tek katı modelden | — |
| Kart türleri | `print3d:release`: çekirdek `release` kartını genişletir (tabla yerleşimi görseli, baskı yönü, dilimleyici ayarı, süre/filament, dosya özetleri) | Eski B kartı |
| Analizciler | Çıkıntı haritası, et kalınlığı haritası, tabla yerleşimi | — |
| Standart maddeleri | ISO/ASTM 52900 (paralı; terimler), ISO/ASTM 52910 (paralı; açık karşılık: üretici ve Protolabs/Hubs kılavuzları, `secondary_source`), 3MF Core Spec 1.4.0 (açık, BSD-2) | Araştırma C (d) |
| Panel görünümleri | Tabla yerleşimi; baskı ayarı formu | — |
| Dış araçlar | OrcaSlicer / PrusaSlicer / CuraEngine CLI. Kullanıcı kurar, ayrı program, AGPL-3.0. Orca ve Prusa bazı derlemelerde `xvfb-run` isteyebilir; yerelde denenmeli | Araştırma C (c1) |
| Regresyon | E-22, E-23, E-25, E-28, E-41 için sentetik vakalar | — |

### 11.7 Örnek paket 2: `molding` (enjeksiyon kalıbı)

| Katkı | İçerik |
| --- | --- |
| Analizciler (otomatik, deterministik) | Çıkma açısı haritası (yüz normali · çekme yönü), negatif açı tespiti (çift yönlü ışın), et kalınlığı (ışın ve küre), izdüşüm alanı (trimesh `projected` + shapely), hacim ve kütle (OCCT `BRepGProp`) |
| Analizciler (yarı otomatik, onaylı) | Çekme yönü adayları, ayırma çizgisi adayı (siluet kenarları), sürgü/lifter ihtiyacı tespiti (yan yönde serbest kalan kilitli noktalar) |
| Kontroller | `DRAFT-01` en küçük çıkma açısı (malzeme ve doku profilinden) · `WALL-01` et aralığı ve düzgünlük · `RIB-01` kaburga/et oranı · `UNDERCUT-01` çözüm kararı olmayan negatif açı → kart · `CLAMP-01` kapama kuvveti × güvenlik çarpanı ≤ pres kapasitesi · `FLOW-01` akış boyu/et oranı ≤ malzeme sınırı · `QTY-01` adet < kalıp başabaş adedi → alternatif bulgusu |
| Hesap şablonları | `clamp_force_area`: F = p·A·k (p, A, k kaynaklı) ve `clamp_force_rule` (ton/inç² kuralı): iki yöntem birbirini sınar, ikisi de `level 1` ve geçerlilik alanı dar. `cooling_time_slab`: levha formülü; katsayı türetmeyle sabitlenir, çünkü kaynaklar çelişiyor. `cycle_time`, `coolant_flow` (Re hedefi), `shrinkage_scale` |
| Soru ağacı | `molding.basics`: yıllık adet (DUR: yalnız onda olan bilgi) → göz sayısı; malzeme (DUR); yüzey/doku → ek çıkma açısı; kritik toleranslar → ISO 20457 maddesi (paralı); kalıbı kim yapacak ve hangi pres (ayardaki makineler); sıcak ya da soğuk yolluk |
| Kart türleri | `molding:side_action` (negatif açı çözümü: sürgü, lifter ya da tasarım değişikliği), `molding:parting_line` (ayırma çizgisi onayı), `molding:gate_location` (her zaman insan kararı) |
| Profil türleri | `molding.press` (kapama kuvveti, atış hacmi, plaka, kolon arası), `molding.material` (yoğunluk, çekme payı, eriyik/kalıp/atma sıcaklıkları, ısıl yayınım; isteğe bağlı Cross-WLF ve Tait). Hepsi kaynaklı |
| Standart maddeleri | ISO 20457:2018 (paralı; açık karşılık yok → satın alma listesi adayı), ISO 6751/8694/8405/10072 (paralı; açık karşılık: üretici katalogları), SPI 101–105 (resmî ücretsiz metin yok; sayılar kaynaklar arasında çelişiyor), VDI 3400 (paralı) |
| Panel görünümleri | Çıkma açısı haritası, negatif açı görünümü, kalıp kavramı montajı |
| Dış araçlar (isteğe bağlı) | openInjMoldSim (GPL-3.0, OpenFOAM 7): yalnız "vaka dışa aktar". Sonuç araştırma düzeyidir ve kanıt olamaz; ayrıca geçerlenirse araç kaydı güncellenir. Isıl analiz için FEniCSx (LGPL-3.0) ya da Elmer (LGPL-2.1+), ayrı program |

**Kalıp paketinde açık kaynakla neler yapılabilir** (Araştırma C, a; dürüst tablo):

| Konu | Durum | Açıklama |
| --- | --- | --- |
| Çıkma açısı, negatif açı tespiti, et kalınlığı, izdüşüm alanı, kütle | **Otomatik** | Deterministik; OCCT/OCP + trimesh (+embreex). FreeCAD DFM Workbench (LGPL-2.1) çalışan bir yöntem örneği. Eşikler kaynaklı olmalı; DFM WB'nin hazır eşikleri kaynaksız, kataloğa alınmaz |
| Çekme yönü önerisi | **Yarı otomatik** | Aday yönler puanlanır; seçim insanın |
| Ayırma çizgisi (düzlemsel ya da tek kademe) | **Yarı otomatik** | Siluet kenarları; sıfır çıkma açılı bantlarda belirsiz; onay gerekir |
| Ayırma yüzeyi | Düzlemsel ve ekstrüzyonda **yarı otomatik**; 3B serbest, çok kademeli, shut-off'lu yüzeyde **yapılamaz** | Açık kaynak araç bulunamadı; karmaşık yüzeyi kalıpçı tasarlar |
| Maça/dişi bölme | **Yarı otomatik** | Ayırma yüzeyi düzgünse Boolean ile; değilse çöker |
| Çekme payı uygulama | İşlem **otomatik**, değer insan | Değer malzeme veri sayfasından ya da ölçümden |
| Sürgü/lifter ihtiyacı | Tespit **otomatik** | Yan yön adaylarını insan verir |
| Sürgü, lifter, maça mekanizması tasarımı | **Yapılamaz** | Açık kaynak tasarım aracı yok; paket yalnız tespit + soru + kart |
| İtici yerleşimi | Öneri **yarı otomatik**, sonuç insan | Kural tabanlı ızgara + çakışma denetimi |
| Yolluk ve giriş yeri | Eleme **yarı otomatik**, karar **yapılamaz** | L/t ile eleme; ticari "gate location" analizinin açık karşılığı yok |
| Soğutma kanalı yerleşimi | **Yarı otomatik** | Kural tabanlı; kaynaklardaki sayılar çelişiyor (yüzey mesafesi 1,5–2,5·D, adım 2–3·D ya da 3–5·D); kaynak seçimi karar |
| Kalıp ısıl analizi | **Yarı otomatik** | Isı iletimi çözücüleri olgun; zayıf halka sınır koşulları |
| Dolum simülasyonu | Araştırma düzeyi; endüstriyel karar için **yapılamaz** | openInjMoldSim README: "prohibitively inconvenient for typical industrial use". Doğrulaması Moldex3D'ye karşı. Malzeme verisi (13 Tait + 7 Cross-WLF parametresi) açık kaynakta yok |
| Çarpılma, lif yönelimi, çöküntü | **Yapılamaz** | Olgun açık kaynak araç yok |
| Kalıp standart parçaları | **Yarı otomatik** | Üretici STEP'leri (Meusburger, HASCO, DME) ücretsiz ama açık lisanslı değil; pakete gömülmez, kullanıcı indirir |

Sonuç: kalıp paketi "parça kalıplanabilirlik analizi + kalıp kavramı + karar desteği" sunar. Kalıbın kendisinin tasarımı (mekanizmalar, giriş, karmaşık ayırma yüzeyi) kalıpçı ve baş mühendis kararıdır. Paket bunu tespit, soru ve kartla yönetir. Bu sınır paket belgesinde ve tanımlama ekranında açıkça yazılır.

### 11.8 Diğer birinci taraf paketler

- **`mech`** (§6). Varsayılan paket: OCCT adaptörü, parametrik model, içe alma, işlem listesi, görünüşler, geçme kaydı ve mekanik kontroller (FIT, BOLT, SOLID, INTERF, UNREG, ASSY).
- **`analysis`**. Aero hesap şablonları (AeroSandbox VLM, NeuralFoil; ikincisi ML vekil olduğu için ayrı araç kaydı), FEA (TetGen + scikit-fem; eski `fea.py`).
  - E-33: kavram seçiminde profil verisi zorunlu.
  - E-35: atış öncesi ağırlık merkezi kabul ölçümü.
  - E-36: analiz planı (Ö-19).

---

## 12. Standart kütüphanesi (katman 3)

```
stdlib/
  process/default@1.yaml          aşamalar, kapılar, sınıf → kapı, risk soruları, kapı maddeleri (el kitabı §5–§6)
  process/nasa-7009b-tailoring.yaml  uyarlama kaydı (baş mühendis onaylı)
  rules/core.yaml                 çekirdek kural kataloğu (id, metin, limit + kaynak, dayanak, kontrol, aşamaya göre seviye)
  roles/*.yaml                    rol tanımları (yetki, araç sınıfı, kilitli kurallar)
  tools/*.yaml                    analiz aracı kayıtları (§10.3)
  items/eu/*.yaml, items/tr/*.yaml, items/jcgm/*.yaml, items/nasa/*.yaml   standart maddesi şablonları
  sources.yaml                    kaynak etiketi türleri ve girdi soyağacı eşlemesi
```

Kurallar:

1. **Dayanaksız kural ve madde girmez.** Şema `basis` alanını zorunlu tutar.
2. **Paralı standart metni kopyalanmaz.** Yalnız numara, madde ve kendi sözümüzle özet yazılır (telif). JCGM PDF'leri de konmaz, yalnız bağlantı verilir.
3. **Kütüphane sürümlüdür:** `stdlib@YYYY.MM`. Çalışma kullandığı sürümü sabitler. Sürüm değişince standart haritası farkı bir kart olarak gelir.
4. **Kütüphane değişikliği baş mühendis onayı ister** (eski "el kitabını, prosedürleri, kural kataloğunu değiştirmek Hold'dur" kuralı).

---

## 13. Kurulum (sıfır Ubuntu makinede tek komut)

### 13.1 Gerekenler

| Bileşen | Nasıl gelir | Not |
| --- | --- | --- |
| Ubuntu 24.04 LTS ya da 26.04 LTS, x86_64 | — | Desteklenen sürümler T-14 |
| git, curl | apt (sudo) | Betik sudo çalıştırmaz; eksikse komutu yazar ve durur |
| uv | Resmî kullanıcı düzeyi kurucu (`~/.local/bin`) | sudo yok |
| Python 3.12 | uv yönetir | Sistem Python'una dokunulmaz |
| mekanik + mech | `uv tool install` | Ön yüz derlenmiş olarak tekerlekte; kullanıcıda Node gerekmez |
| Claude Code | Anthropic'in resmî kurucusu (kullanıcı düzeyi); giriş kullanıcının kendi akışıyla | mekanik kimlik bilgisine dokunmaz |
| İsteğe bağlı | Dilimleyici (AppImage/Flatpak), FreeCAD (teknik resim), CalculiX ve benzeri | `mekanik doctor` önerir, kurmaz |

### 13.2 Adımlar

Faz 4'te kesinleşecek komut biçimi:

```bash
curl -LsSf https://<yayın-adresi>/install.sh | sh
```

Repo özel olduğu sürece baş mühendisin makinesinde `uv tool install git+ssh://…` kullanılır.

1. **Ortam denetimi.** İşletim sistemi ve sürüm; Ubuntu değilse açık iletiyle durur.
2. **git ve curl.** Eksikse `sudo apt install -y git curl` satırını yazar ve durur. Hold kuralı: sudo'yu kullanıcı çalıştırır.
3. **uv.** Yoksa kullanıcı düzeyinde kurar.
4. **mekanik.** `uv tool install mekanik[mech]`.
5. **Claude Code.** `claude --version` yoksa resmî kurulum komutunu ve belge bağlantısını yazar. Kullanıcı `claude` içinde `/login` ile kendi hesabına girer.
6. **`mekanik init` sihirbazı** (terminal ya da panelin ilk açılış sayfası). Sorular:
   - kişi adı ve e-posta (git kimliğiyle karşılaştırılır);
   - iş repolarının kökü;
   - ilk kurum (varsayılan "Bağımsız", `IND`);
   - makine ve ölçme aletleri (isteğe bağlı; değerler `assumption` ile başlar);
   - dil;
   - ajan kimlik doğrulama türü (abonelik / API anahtarı + bütçe);
   - panel portu.

   Sihirbaz `~/.config/mekanik/`'i yazar ve şemayla doğrular.
7. **`mekanik doctor`.** Araçlar ve sürümleri, OCP duman testi (kutu + STEP dışa aktarma), disk, ajan yoklaması (kimlik bilgisi okumadan), port.
8. **İsteğe bağlı.**
   - `mekanik platform service` systemd kullanıcı birimi komutlarını yazar. Baş mühendisin makinesinde Hold: kullanıcı çalıştırır.
   - `.desktop` başlatıcısı `~/.local/share/applications`'a yazılır (sudo yok).
9. **Panel.** `http://127.0.0.1:<port>` açılır; `mekanik example open` örnek projeyi açar.

**Kaldırma.** `mekanik uninstall` önce ne silineceğini listeler: tool, önbellek ve isteğe bağlı olarak ayar. İş repolarına dokunmaz.

### 13.3 Kabul ölçütleri (Faz 4)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| K1 | Temiz Ubuntu 24.04 konteynerinde ve 26.04 sanal makinesinde: tek komut + Claude girişi → `mekanik doctor` | Bütün zorunlu maddeler yeşil | öneri |
| K2 | Kurulum süresi (100 Mbit/s bağlantı, indirme dahil) | ≤ 15 dk | öneri |
| K3 | Betiğin içinde sudo | 0 | Hold kuralı |
| K4 | Örnek proje: G0 → G3 uçtan uca (sahte ajanla, CI'de) | geçer | öneri |
| K5 | Kaldırma sonrası iş repoları | değişmemiş (özet karşılaştırması) | öneri |

---

## 14. Mevcut çalışmaların taşınması

### 14.1 Kapsam

- **Veri baş mühendisin makinesinde.** Eski kurum repoları (ör. `~/is/bag`: BAG-PLU-01) ve arşivler bu oturumdan görünmüyor. Taşınacak çalışma listesini baş mühendis onaylar (T-13).
- **Öneri.** Etkin çalışmalar taşınır. Arşivdekiler eski araçla okunabilir kalır, istenirse sonra taşınır.
- **Eski sisteme dokunulmaz.** Taşıma eski dalları değiştirmez. Yeni dosyalar ayrı bir dalda (`<kod>/is/v1-gecis`) oluşur; eski sistem kendi dallarında çalışmaya devam eder.

### 14.2 Betikler

```bash
mekanik migrate surec-config --from <eski surec klasörü> --dry-run
```

Kurumlar (`kurumlar/*.yaml`) `~/.config/mekanik/orgs/` altına, üretim profilleri (`profiller/uretim`) `machines/` altına (`print3d.fdm_printer` + `print3d.process`), ölçüm profilleri (`profiller/olcum`) `instruments/` altına taşınır.

```bash
mekanik migrate surec-work <çalışma klasörü> --dry-run
mekanik migrate surec-work <çalışma klasörü> --apply
```

`--dry-run` eşleme raporunu ve yeni dosyaları geçici klasöre yazar. `--apply` yeni dalı açar, dosyaları yazar ve DUR kartı açar.

**Alan eşlemesi** (özet; tam tablo Faz 1'de betikle birlikte):

| Eski | Yeni | Not |
| --- | --- | --- |
| `calisma.yaml` (kod, ad, amac, bitti_olcutu, sinif, kapilar, asama, kapi_durumu, profiller) | `work.yaml` (code, title, purpose, done_criterion, risk_class, process.gates, process.stage, process.gate_status, profiles) | `suruyor` → `in_progress`, `bekliyor` → `pending` … |
| `istek-listesi.yaml` | `requirements.yaml` | Ölçüt sayıysa `criterion`; değilse `draft` + `open_question` (sayısız istek görünür olur) |
| `params.yaml` | `params.yaml` | Kaynak etiketi eşlemesi (§2.3); `olcum_profili: kumpas` → `measured:<alet-kimliği>` (ayardan) |
| `gecmeler.yaml`, `montaj.yaml` | `fits.yaml` (mech) | — |
| `kararlar.yaml` | `decisions.yaml` | `veren: proje-muhendisi` → `decided_by: project_engineer`; `hedef_etkisi` → `requirement_effects`; `gozlemler[].olcumlu` → `observations[].measured`; `dayanak` → `basis` |
| `onaylar.yaml`, `yanitlar.yaml` | `approvals.yaml`, kart dizileri | `kim` → ayardaki baş mühendis kimliği; özet yeniden hesaplanır (§14.3 V5) |
| `kartlar/*.yaml` | `cards/*.yaml` | — |
| `model/model.py` | `model/model.py` | CadQuery çağrıları aynı; `p.<ad>` erişimi aynı |
| `hesaplar/*.py`, `kayit/hesaplar/*.json` | `calcs/*.py`, `records/calcs/*.json` | `Hesap` → `Calc` yöntem adı eşlemesi betikle (`h.girdi` → `c.input` …); kayıt şemaya çevrilir |
| `kayit/gunluk`, `kayit/gorseller`, `kayit/kalite` | `records/log`, `records/visuals`, `records/quality` | Günlük olduğu gibi kopyalanır (düzeltilmez) |

### 14.3 Doğrulama

Hepsi geçmeden `--apply` çalışmaz:

| # | Denetim | Ölçüt |
| --- | --- | --- |
| V1 | Şema: her yeni dosya v1 şemasından geçer | 0 hata |
| V2 | Sayı korunumu: eskideki her sayısal değerin çoklu kümesi yenisinde aynı (eski `gecis.sayi_korunumu` fikri) | kayıp 0, yeni sayı 0 |
| V3 | Kaynak etiketi eşlemesi | eşlenmeyen etiket 0; eskide kaynaksız olan yenide de kaynaksız (ENGEL korunur) |
| V4 | Kontrol eşitliği: eski `surec kontrol` ile yeni `mekanik check` | Kural kimliği eşlenmiş (konu, seviye) kümeleri aynı; fark varsa her biri bilinen bir kasıtlı değişiklik listesinde |
| V5 | Onay eşitliği | Eskide geçerli olan onay yenide geçerli. Alan adları değiştiği için özet değişir; `migrated_from_hash` + yeni özet yazılır. İçerik değişmediyse onay korunur |
| V6 | Model eşitliği | Hacim, sınır kutusu, yüz sayısı aynı (bağıl fark ≤ 1e-6, öneri). Farklı OCP sürümünde tessellation özeti değişebilir; geometrik özellik kullanılır |
| V7 | Kart eşitliği | Açık kartların anahtar kümesi aynı |
| V8 | Hesap eşitliği | Hesaplar yeniden çalışır; sonuçlar aynı (bağıl ≤ 1e-9, aynı kod) |

Her çalışma için `migration-report.md` üretilir ve baş mühendise DUR kartıyla gider.

### 14.4 Kabul ölçütleri

| Faz | Ölçüt |
| --- | --- |
| Faz 1 (CI) | S-001 ve sentetik H-001 V1–V8'den geçer |
| Faz 1 çıkışı (baş mühendisin makinesinde) | BAG-PLU-01 kuru çalıştırması V1–V8'den geçer |
| Faz 2 sonu | Taşınan çalışmalar yeni panelde açılır, eski panelle aynı kartları gösterir |

---

## 15. Bağımlılık envanteri (özet)

Tam tablo Ek A'da (`appendix-a-dependency-inventory.md`, dosya:satır ile). Eski repo `d26af89` üzerinde grep ve okumayla çıkarıldı.

| Kategori | Yer (`kayit/` dışı) | `kayit/` içinde (yaklaşık satır) | v1 hedefi |
| --- | --- | --- | --- |
| Kişi (Taha, tahatas013, e-posta, rol = kişi) | 45 | 36 | Atölye ayarı (`person`, `identities`) |
| Makine ve yollar (`/home/tahatas013`, `~/is`, `~/.cache/surec`, port 8765, RAM/GPU) | 46 | 52 | Atölye ayarı (yollar, port); XDG dizinleri |
| Ubuntu ve işletim sistemi (systemd, xdg-open …) | 13 | 38 | Platform adaptörü |
| tmux, Tailscale, Remote Control | 32 | 31 | Platform adaptörü; Remote Control → ajan adaptörü |
| Üstteknik (UST, ustteknik-arge, dizlik …) | 22 | 41 | Çalışma verisi; `gecis.py` kaldırılır |
| Belirli alan (FDM 41, mekanik CAD 15, aero 11, tarama 14, FEA 3) | 84 | 78 | `print3d`, `mech`, `analysis`; tarama → alet kaydı + standart kütüphanesi |
| Claude Code'a özgü (`claude -p`, `.claude/`, kancalar, model adları) | 30 | 27 | Ajan adaptörü |
| Kurum ve çalışma kodları (BAG, PLU, UST-DZL-01 …) | 23 | 46 | Atölye ayarı; örnekler nötrleşir |
| Türkçeye sabit arayüz metni | ≈1320 satır (kod 1085, test 237) + 18 "metin = mantık anahtarı" yeri | — | i18n katalogları; dil bağımsız kimlikler |

**Çekirdekte kalırsa ilkeyi bozacak 15 yerden en kritik beşi** (Ek A §12):

1. Kurum ve profil verisi kod reposunun içinde (`SUREC_KOK/kurumlar`, `profiller`).
2. Onay yetkisi makinenin `git config user.name` değerinden geliyor.
3. Onay yetkisi yalnız ilk adla karşılaştırılıyor; **hata**, "Taha Test" de yetkili.
4. Her yeni çalışma belirli bir yazıcıya bağlanıyor (`VARSAYILAN_PROFILLER`).
5. FDM mantığı süreç motorunun içinde (`akis.baski`, tabla teması, PLA yoğunluğu).

**Envanter sırasında bulunan iki eski sistem hatası** (eski sistem çalıştığı için baş mühendise bildirilir; eski repoya yazılmadı):

- `onay.py:112`: onay yetkisi yalnız ilk ada bakıyor.
- `ana.py:144`: `surec baski` sonucu `onbellek` anahtarını okuyor ama `akis.baski` bu anahtarı dönmüyor; komut `KeyError` ile durur.

İkisi v1'de regresyon testine dönüşür.

---

## 16. Taşıma envanteri ve dersler (özet)

Tam tablo Ek B'de (`appendix-b-migration-inventory.md`). 181 öğenin dağılımı: **105 taşınır**, **47 yeniden yazılır**, **29 taşınmaz**.

| Bölüm | Taşınır | Yeniden yazılır | Taşınmaz |
| --- | --- | --- | --- |
| Çekirdek ve kontroller | 34 | 13 | 2 |
| CLI | 18 | 5 | 2 |
| Panel arka ucu | 5 | 2 | 1 |
| Panel ön yüzü | 8 | 12 | 0 |
| Kural kataloğu | 18 | 1 | 0 |
| Profiller | 4 | 0 | 0 |
| Ajanlar, ayarlar, paketleme, kurumlar | 5 | 5 | 2 |
| Testler ve vakalar | 6 | 1 | 1 |
| Belgeler ve kayıtlar | 7 | 8 | 21 |

**Kurallar:**

- Taşınan parça yeni repoya ancak testlerini geçerek girer.
- Testi olmayan 17 taşınır parçanın her biri için yeni test yazılır (Ek B §14), en önemlileri: `fea.py`, `gozcu.py`, `nabiz.py`, `gunluk.py`, bayt kodu yazmama, ayrık katı reddi, katalog–kod bağı, CLI duman testleri.
- **Taşınmayanlar:** git geçmişi, kurum ve Üstteknik verisi, kişisel yollar ve adlar, `gecis.py` (ustteknik-arge'ye özgü).
- **H-001 sentetik vakaya dönüşür:** aynı sayılar (3,0 / 1,0 / 1,0 + varsayım / kaynaksız Ø14 / onaysız 3,2 mm esneme / kritik geçmede tarama / 0,5 GEÇTİ / M4 Ø4,3 GEÇTİ / görevsiz 0,2 bindirme), uydurma parça adları. `KAYNAK.md` taşınmaz.
- **Testler:** 107 test fonksiyonu (parametrize ile yaklaşık 144 durum; ölçü: Ek B §1 bulgu 6):
  - Faz 1'de taşınır: test_akis 36, test_cekirdek 42, test_onbellek 6, test_regresyon 2.
  - Faz 2'de taşınır: test_panel_e2e 17.
  - Taşınmaz: test_gecis 4.

**Dersler.** E-01…E-41'in durumu: 21 düzeltildi, 8 kısmen, 12 açık. v1'deki karşılıkları:

| v1 mekanizması | Dersler |
| --- | --- |
| Çekirdek: kart ve karar (§4.3–4.4) | E-07, E-11, E-13, E-15, E-17, E-21 (v1'de model kodu da onay commit'inden: "kalan" kapanır), E-24 |
| Çekirdek: kapı ve süreç profili (§4.2) | E-26 (G3 → G2 dönüşü), E-31 (G2'de risk kaydı/DFMEA kapı maddesi) |
| Çekirdek: hesap, deney, kanıt (§4.5, §10) | E-02, E-03 (deney şeması), E-30 (kritik hesapta ikinci yöntem), E-32 (yüksek doğruluk esas), E-37 (önbellek), E-39 (geçerlilik alanı) |
| Çekirdek: kayıt deposu (§4.10) | E-19 (bayt kodu), E-20 (kilitsiz okuma), E-40 (`check` dosya yazmaz) |
| Kalite mühendisi (§4.8, §10.5) | E-38 |
| Ajan ve gözcü (§5) | E-14 (gözcü taşınır; kapalı oturumu kendiliğinden başlatma önerilmez, T-09), E-18 (ajan durumu), E-34 (DUR işleri için hazır komut kartı) |
| Panel (§5, Faz 2 e2e) | E-06, E-08, E-09, E-10, E-12 |
| `mech` | E-29 (temiz üçgen ağı) |
| `print3d` (§11.6) | E-01, E-04, E-05, E-22, E-23, E-25, E-27 (onaydan sonra), E-28, E-35, E-41 |
| `analysis` (§11.8) | E-33, E-36 |
| El kitabı değişikliği gerektirenler (T-05) | E-16 (G1'de kavram taslağı tek satır) |

**Öneriler ve bağımsız inceleme bulguları.** Ö-01…Ö-28'in hiçbirinin el kitabı metni onaylanmadı (el kitabı 0.2). Kodda 20'si uygulanmış, 5'i kısmen, 3'ü hiç (Ö-16, Ö-17, Ö-28). B1–B8 bire bir Ö-20…Ö-27'dir.

v1 tasarımı hepsini içerir:

- Ö-17 ve Ö-28 tasarımda var.
- Ö-16 (KOSE-01) katalog onayını bekler.
- Yeni el kitabı (v1) bu önerileri kural olarak yazar. El kitabı değişikliği Hold: onay T-05.

---

## 17. Faz planı ve kabul ölçütleri

Her faz kullanılabilir bir sonuçla biter. Eski sistem, v1 aynı işi kanıtlanmış biçimde yapana kadar çalışır. Eşikler `öneri`dir (T-02); ölçü dayanağı olanlar yazılıdır.

### Faz 1 — Çekirdek (eşitlik; yeni özellik yok)

**Kapsam:**

- çekirdek (§4);
- `mech` (parametrik CadQuery modeli, geçme kaydı, mekanik kontroller, görünüşler: eski davranış);
- `print3d` (yalnız eskiden olanlar: tabla sığması, tabla teması, tek katı, tahmin, baskı isteği);
- `analysis` (Calc API, eski `fea.py`);
- CLI (§4.11'deki Faz 1 satırları);
- panel **arka ucu** (eski panelin kullandığı veriler, REST);
- atölye ayarı;
- ajan adaptörü (kalite mühendisi ve kancalar);
- taşıma betikleri (§14).

**Kapsam dışı:**

- yeni ön yüz: eski panel çalışmaya devam eder (T-04);
- tanımlama, politika motoru, akış arayüzü, standart haritası;
- içe alma ve işlem listesi;
- "yeni" işaretli kontroller (CALC-03, CALC-04, REQ-01'in G4/G5 şartı, STDMAP-01, SOURCE-02);
- G3 → G2 dönüşü.

| # | Kabul ölçütü | Eşik | Dayanak |
| --- | --- | --- | --- |
| 1.1 | Eski CLI işlevlerinin v1 karşılığı (§4.11 Faz 1 satırları) | %100; her biri duman testiyle | Ek B §3 |
| 1.2 | Eski testlerin taşınması | 86 test fonksiyonu (36 + 42 + 6 + 2) v1 API'siyle geçer | ölçü: Ek B §9 |
| 1.3 | Testsiz parçalara yeni test | Ek B §14'teki çekirdek/CLI maddeleri (1–12) için ≥ 12 yeni test | Ek B §14 |
| 1.4 | Regresyon | Sentetik H-001 (8 alt vaka) + S-001 (10 alt vaka): 18/18 beklenenle aynı; "hep ENGEL" / "hep GEÇTİ" sahte kontroller %100 kalır | ölçü: eski `test_regresyon` |
| 1.5 | Çekirdek temizliği | Yasak sözcük 0; import-linter ihlali 0; CLI'da katalog dışı Türkçe dize 0 | §3.1 |
| 1.6 | Şemalar | 17 şema kesinleşir; örnek ve bozuk örnek denetimi temiz | §schemas |
| 1.7 | Taşıma | S-001 ve sentetik H-001: V1–V8 geçer; BAG-PLU-01 kuru çalıştırması baş mühendisin makinesinde V1–V8 geçer | §14 |
| 1.8 | Bilinen hatalar | İki eski hata (ilk ad yetkisi, `baski` KeyError) v1'de testle kapalı | §15 |
| 1.9 | Boyut bütçesi (ikinci sistem önlemi) | `src/` Python satırı ≤ 8 850 (eski çekirdek + CLI + panel arka ucu: 5 921 + 451 + 1 677 = 8 049 satır × 1,10) | ölçü: `wc -l`, `d26af89` |
| 1.10 | Çekirdek testleri OCCT'siz | `tests/core` OCCT kurulu değilken ≤ 60 s'de geçer | öneri |

### Faz 2 — Panel kokpit, tanımlama, politika, akış, standart haritası

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 2.1 | A1–A9 (§5.7) | hepsi |
| 2.2 | C1–C6 (§7.2): çekirdek iş türü ağaçları + `print3d.basics` ile | hepsi |
| 2.3 | D1–D6 (§8.3) | hepsi |
| 2.4 | E1–E5 (§9.4) | hepsi |
| 2.5 | F1 (30/30), F3, F5'in G4/G5 şartı, F8 (§10.11) | hepsi |
| 2.6 | Eski panel e2e testleri (17) yeni ön yüzde | 17/17 |
| 2.7 | EN katalog kapsamı (panel + CLI) | %100 anahtar; eksik anahtar 0 |
| 2.8 | Eski panelden yeni panele geçiş | Eşitlik kontrol listesi %100; eski panelin kapatılması baş mühendis kararı |

### Faz 3 — Alan paketleri ve CAD içe alma/değişiklik

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 3.1 | B1–B8 (§6.6) | hepsi |
| 3.2 | `molding` analizcileri: cevabı bilinen 5 sentetik parça | Sıfır çıkma açılı yüz sayısı, negatif açılı bölge sayısı, en ince et (±%2) ve izdüşüm alanı (±%1) beklenenle uyumlu (öneri) |
| 3.3 | Kapama kuvveti iki yöntemle | CALC-03 iki yöntemi karşılaştırır; uyuşmazlıkta ENGEL (test) |
| 3.4 | `print3d` yeni kontroller (E-04, E-05, E-41, E-35) | Her biri için geçen ve kalan regresyon alt vakası |
| 3.5 | Analiz aracı kayıtları | Paketlerdeki her analiz aracının geçerlilik alanı kaydı var (%100); alan dışı sonuç kanıt olamaz (test) |
| 3.6 | Eklenti API'si | `molding` yalnız genel API'yle yazılır; çekirdekte ona özel kod 0 satır. API v1 bu fazın sonunda dondurulur |
| 3.7 | Pilot | Her paket için baş mühendisin bir gerçek işi; kapıdan sonra bulunan her hata ≤ 7 günde regresyon vakası |

### Faz 4 — Kurulum, belgeler, örnek proje, temiz makine, yayın hazırlığı

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 4.1 | K1–K5 (§13.3) | hepsi |
| 4.2 | Belgeler TR+EN | Her CLI komutu, her paket, her katkı noktası belgeli (%100) |
| 4.3 | Örnek proje | Sentetik bir parça G0 → G3 uçtan uca (CI, sahte ajan) |
| 4.4 | Lisans denetim betiği | Tekerlek içi `licenses/` dahil tarama: birlikte dağıtılan uyumsuz bileşen 0; her kaynak dosyada SPDX başlığı (%100) |
| 4.5 | Gizli ve kişisel veri taraması | Gizli bilgi 0. Atölye ayarındaki kişi ve kurum adları repoda 0. Faz 0 belgeleri ve ekleri eski sisteme atıf için kişi ve kurum adı içerir; yayından önce bunlar temizlenir ya da yayımlanmayan bir arşive alınır |
| 4.6 | Yayın kontrol listesi | Hazır. **Yayının kendisi ayrı karar ve baş mühendis onayı** (T-10) |

---

## 18. Bağımlılık lisans tablosu (AGPL-3.0 ile uyum)

Ayrıntı ve kaynaklar: `research/d-nasa-regulation-licenses.md` §3. PyPI JSON ve LICENSE dosyaları `metin_elde`; gnu.org genel kuralları erişilemedi, `ikincil_kaynak`.

**Dayanak kurallar:**

- AGPL §13: GPLv3 ile birleşebilir; bütün §13 ağ yükümlülüğüne tabi olur.
- Apache-2.0 ve LGPL GPLv3 ailesiyle uyumludur.
- GPL-2.0-only aynı programda uyumsuzdur, ayrı süreçte sorun değildir.
- Ayrı program "aggregate" sayılır.

| Bileşen | Lisans (SPDX) | AGPL-3.0 durumu | Not |
| --- | --- | --- | --- |
| jsonschema, pydantic, typer, trimesh, aerosandbox, neuralfoil, open3d, meshio, pyyaml, fastapi, three.js, three-cad-viewer, vite, pytest, uv, Node.js | MIT | uyumlu | — |
| click, httpx, numpy, scipy, shapely, scikit-fem, uvicorn | BSD-3-Clause (numpy: BSD karışımı) | uyumlu | shapely tekerleğindeki GEOS LGPL (doğrulanmadı), uyumlu |
| cadquery, build123d, OCP (cadquery-ocp), manifold3d, pyransac3d, watchdog, typescript, Playwright | Apache-2.0 | uyumlu | NOTICE dosyaları korunur |
| OCCT (OCP tekerleği içinde) | LGPL-2.1-only WITH OCCT-exception-1.0 | uyumlu (koşullu) | Dağıtımda LGPL metni ve "Open CASCADE Technology kullanır" bildirimi; değiştirilirse OCCT kaynağı |
| TetGen (tetgen tekerleği içinde) | AGPL-3.0-or-later | uyumlu | PyPI meta verisi yalnız MIT diyor (yanıltıcı); proje AGPL kaldıkça sorun yok, daha gevşek lisansa geçişi engeller |
| gmsh | GPL-2.0-or-later WITH Gmsh-exception | uyumlu (koşullu) | "or later" ile GPLv3 → AGPL §13 |
| PyMeshLab, OpenFOAM, openInjMoldSim | GPL-3.0 (-or-later) | uyumlu (koşullu) | GPLv3 kısmı GPLv3 kalır; ayrı program önerilir |
| FreeCAD, Elmer FEM | LGPL-2.1-or-later | uyumlu | Ayrı program |
| OrcaSlicer, PrusaSlicer, CuraEngine | AGPL-3.0 | uyumlu | Ayrı program; kullanıcı kurar |
| CalculiX (ccx), git | GPL-2.0-only | **yalnız ayrı program olarak** | Komut satırıyla çağrılır |
| Claude Code CLI | Tescilli ("© Anthropic PBC. All rights reserved") | **yalnız ayrı program olarak** | Kullanıcı kurar; repoya ya da paketlere konmaz |
| claude-agent-sdk (Python) | MIT | uyumlu (koşullu) | Platform tekerlekleri tescilli CLI'yi içerir: yeniden dağıtılmaz |
| @anthropic-ai/claude-agent-sdk (TS) | Tescilli | **uyumsuz** (AGPL koda bağlanıp dağıtılırsa) | Ön yüze konmaz; kullanılmaz |

**AGPL yükümlülükleri:**

- Panel uzaktan sunulursa (ör. Tailscale), değiştirilmiş sürümün kaynağı kullanıcıya sunulur. Panelin alt çubuğunda o commit'in kaynağına bağlantı (§13).
- Paketli dağıtımda içerideki ikililerin lisans metinleri eklenir.
- Yeni bağımlılık eklenince lisans tablosu betikle yeniden üretilir; tetgen örneğinde olduğu gibi PyPI alanı yanıltıcı olabilir.

---

## 19. Riskler ve bilerek dışarıda bırakılanlar

### 19.1 İkinci sistem etkisi

Tehlike: yeniden yazılan sürüm "her şeyi daha iyi yapma" isteğiyle şişer, eşitliğe ulaşmadan biter.

| Önlem | Ölçülebilir hâli |
| --- | --- |
| Faz 1 yalnız eşitlik. Kapsam listesi Ek B'nin "taşınır" ve "yeniden yazılır" satırlarıdır | Ek B dışı yeni özellik PR'ı: 0 (inceleme kuralı) |
| Yeni fikir koda değil, `docs/later.md` listesine | Liste var; Faz 1 sırasında kod karşılığı yok |
| Boyut bütçesi | 1.9: `src/` ≤ 8 850 satır; CI her commit'te ölçer ve aşımda uyarır |
| Büyük patlama yok | Eski sistem çalışır; v1 iş akışını ancak eşitlik testleri geçince devralır (CLI Faz 1, panel Faz 2) |
| Eklenti API'si mevcut koddan çıkarılır, önceden tasarlanıp şişirilmez | `mech`, `print3d` ve `analysis` eski koddan gelir; API ancak `molding` (ilk yeni paket) yazıldıktan sonra dondurulur (3.6) |
| Zaman kutusu | Her fazın süresi Faz 1 başında yazılır; %50 aşımda kapsam kesme kararı (baş mühendis) |
| Çerçeve ekleme disiplini | Yeni çerçeve ya da büyük bağımlılık yalnız gerekçe kaydıyla (ör. ön yüzde React yok; eski çerçevesiz düzen) |
| Her fazın sonunda gösterim | Baş mühendise canlı gösterim + kabul ölçütü tablosu |

### 19.2 Diğer riskler

| Risk | Etki | Önlem |
| --- | --- | --- |
| İçe alınan STEP'te OCCT işlemleri başarısız ya da kısmi | Yanlış model | Dürüst işlem tablosu (§6.3), sessiz başarısızlık 0 (B2), derlem testi, sürüm sabitleme |
| Anthropic şartları, fiyatları ya da CLI biçimi değişir | Panel ajanı çalıştıramaz ya da maliyet artar | Adaptör arayüzü; kayıtlı stream-json örnekleriyle testler; `capabilities` algılama; desteklenen sürüm aralığı; kimlik doğrulama seçimi; bütçe sınırı |
| Abonelik sınırları ("ordinary, individual usage") | Kullanım kesilir | Kendiliğinden oturum yok; tur ve bütçe sınırı; kullanım ölçüsü gün sonu özetinde |
| Taşıma hatası | Veri kaybı ya da yanlış onay | V1–V8, kuru çalıştırma, ayrı dal, eski veriye dokunmama |
| CadQuery (OCP 7.9) ile build123d (OCP 8.0) ayrışması | Bağımlılık çıkmazı | G-06: Faz 1'de CadQuery; Faz 3 başında yeniden değerlendirme; OCP çağrıları `mech` içinde yalıtılır |
| Tek bakımcı | Süreklilik | Basit mimari, testler, belgeler, eklenti sınırları |
| İki dil yükü | EN geride kalır | Katalog; TR varsayılan; eksik EN anahtarı uyarısı |
| Paralı standartlara erişim | Kabul ölçütü doğrulanamaz | Açık karşılık araması, satın alma listesi, `secondary_source` görünürlüğü; metin kopyalanmaz |
| AGPL uyumu | Hukuki risk | SPDX başlıkları, lisans denetim betiği, tescilli bileşenin birlikte dağıtılmaması, §13 kaynak bağlantısı |
| Yerel panel güvenliği (ajan çalıştıran web uygulaması) | Yetkisiz komut | 127.0.0.1, Host/Origin denetimi, POST'larda CSRF belirteci, kimlik bilgisi yok, yol kaçışı testleri, ajan izin kipi |
| Model güvenilirliğinin abartılması | Yanlış karar | Geçerlilik alanı, "güvenilmez" damgası, tek puan yok, placard (§10.3–10.4) |
| Baş mühendisin onay zamanı | İş bekler | Politika soru sayısını düşürür; toplu soru paketi; ölçüm ve eşik ayarı |

### 19.3 Bilerek dışarıda bırakılanlar (v1)

- Çok kullanıcı, hesap sistemi, kişiye bağlı roller.
- Telefon arayüzü (sonraki sürüm).
- Bulut barındırma ya da hizmet olarak sunma.
- Windows ve macOS.
- Kendi CFD ve dolum çözücüsü; çarpılma ve lif yönelimi tahmini.
- Karmaşık ayırma yüzeyinin ve kalıp mekanizmalarının otomatik tasarımı.
- Taramadan tasarım niyetli parametrik katıya otomatik geçiş.
- İçe alınan STEP'te parametrik ölçü düzenleme (özellik tanıma); Analysis Situs bağlaması.
- Teknik resim üretimi (FreeCAD TechDraw): sonraki paket.
- GD&T yazma; PMI yalnız okunur ve bayat işaretlenir.
- ERP, satın alma, maliyet veritabanı.
- Telemetri; uzak eklenti pazarı ve paketin kendiliğinden kurulması.
- Grafik tasarım işleri (katalog, etiket, kutu): T-03, sonra paket.
- Tailscale ve uzaktan erişimin çekirdekte olması (yalnız platform adaptörü).
- Ajan oturumunun kendiliğinden başlatılması (T-09).

---

## 20. Geçici kararlar ve açık kararlar

### 20.1 Geçici kararlar

Faz 0 sırasında proje mühendisinin verdiği geçici kararlar. Hepsine itiraz edilebilir; itiraz edilmezse Faz 1 kapısında geçerli olur.

| No | Karar | Gerekçe |
| --- | --- | --- |
| G-01 | Python paketi ve komut adı `mekanik`; yapılandırma `~/.config/mekanik/` | Baş mühendis repo adını seçti. PyPI'de `mekanik` boş (ölçü: `pypi.org/pypi/mekanik/json` → 404, 2026-11-06). GitHub'da aynı adlı küçük, ilgisiz depolar var. Marka araştırması yalnız bu iki kaynakla yapıldı: kısmi |
| G-02 | Repo boş olduğu için Faz 0 belgesi ilk commit olarak `main`'e; sonraki değişiklikler dal + PR | İlk push yetkisi; boş repoda dal açmak varsayılan dalı karıştırırdı |
| G-03 | Veri dosyaları YAML; kayıtlar JSON/JSONL; şemalar JSON Schema 2020-12, `urn:mekanik:schema:v1:*` | İnsan okur (YAML), makine yazar (JSON); eski sistemle süreklilik |
| G-04 | Sıralı değerler İngilizce; arayüzde TR etiket katalogdan (ör. `text_in_hand` = metin elde) | Kesin karar 1 |
| G-05 | Mekanik CAD (OCCT, CadQuery, geçme, mekanik kontroller) `mech` paketinde | Çekirdek alan bilmez; Ek A önerisi; çekirdek testleri OCCT'siz |
| G-06 | Faz 1'de CadQuery 2.8 + OCP 7.9.3; build123d/OCP 8.0 Faz 3 başında yeniden değerlendirilir | İki OCP aynı ortamda kurulamaz (Araştırma B); eski modeller CadQuery |
| G-07 | Süreç (G0–G5, A/B/C, risk soruları) `stdlib/process/default@1.yaml` verisi; davranış el kitabı 0.2 ile aynı | Çekirdek belirli bir süreci kodda taşımaz |
| G-08 | Dal ve etiket adları (`<kod>/ana`, `/is/`, `/karar/`, `-G<n>`, `-baski-`) olduğu gibi kalır | Çalışma verisinin parçası, ASCII; eski çalışmalarla süreklilik. Kesin karar 1 kod ve dosya adlarını kapsar; itiraz edilirse `main/work/decision/-release-` olur |
| G-09 | "Baskı isteği" çekirdekte genel `release` (baskı/üretim isteği); paket genişletir | Kalıp ve sac işinde de aynı DUR gerekir |
| G-10 | İlk ajan adaptörü Claude Code CLI headless (stream-json); Agent SDK ikinci adaptör ve yalnız API anahtarıyla | Araştırma A |
| G-11 | Kalite mühendisi anlama özeti onayından önce de çalışır | Tasarım başlamadan hatayı yakalamak |
| G-12 | Panel ön yüzü Vite + TypeScript, çerçevesiz; three-cad-viewer; SSE | Eski panelle süreklilik; ikinci sistem önlemi |
| G-13 | Panel varsayılan 127.0.0.1; uzaktan erişim platform adaptörü | Çekirdek Tailscale bilmez |
| G-14 | Taşıma ayrı dalda; eski dallara ve eski repoya dokunulmaz | Eski sistem çalışmaya devam eder |
| G-15 | Taramadan türetilen ölçünün belirsizliği alet kaydından; telefon LiDAR'ı için örnek ayar cm sınıfı alt sınır | Araştırma B: ±1 cm sınıfı (ikincil kaynak); referans parçayla doğrulanana kadar varsayım |
| G-16 | PyMeshLab (GPL-3.0) uyumlu ama varsayılan bağımlılık değil; trimesh + Open3D yeter | Bağımlılık hafifliği |
| G-17 | Model ve hesap kodunda izin listesi dışı sayı denetimi (SOURCE-02), Faz 2 | "Kaynaksız sayı yok, kodda da" kuralının makine denetimi |
| G-18 | Analiz aracı kayıtları ve NASA-STD-7009B uyarlama kaydı standart kütüphanesinde | §10.3–10.4 |
| G-19 | Belgeler TR; dosya adları EN; EN belge çevirisi Faz 4 | Kesin karar 1 |
| G-20 | Faz 0 için 3 ek şema: `agent-run`, `stream-event`, `intake-summary` | A, C, E parçalarının veri şeması istendi |

### 20.2 Baş mühendisin açık kararları

| No | Karar | Neden senin kararın | Öneri |
| --- | --- | --- | --- |
| T-01 | Ajan kimlik doğrulama varsayılanı: abonelik (CLI girişi) mi, API anahtarı mı | Maliyet etkisi | Kişisel kullanımda abonelik (Claude Code CLI, kendi girişin). API anahtarı seçenek olarak kalır; seçilirse bütçe sınırı zorunlu |
| T-02 | "öneri" etiketli bütün kabul ölçütü eşikleri | Kabul ölçütü baş mühendisin | Toplu onay ya da tek tek değişiklik |
| T-03 | Grafik işler (katalog, etiket) v1 dışında, sonra paket | Kapsam | Dışarıda |
| T-04 | Eski panel Faz 2 sonuna kadar çalışsın; Faz 1'de yeni ön yüz yazılmasın | Kapsam ve günlük kullanım | Evet |
| T-05 | Yeni el kitabı (v1): Ö-01…Ö-28'in kurala dönüşmesi, Ö-16 (KOSE-01) kataloğa, E-16 | El kitabı ve katalog değişikliği Hold | Faz 1 başında taslak; senin onayınla |
| T-06 | Soru politikası sayıları: geri dönüş penceresi 10 karar, eşik %20, en çok 5 açık geçici karar, aşama başına en çok 5 "şimdi" sorusu | Politika | Bu değerlerle başla, ölç, ayarla |
| T-07 | Maliyet eşiği (TL): "maliyet etkisi" DUR kategorisinin sınırı | El kitabı §14'ten beri açık; yalnız sende olan bilgi | Kurum başına değer |
| T-08 | Paralı standart satın alma (ilk aday: kalıp paketinde ISO 20457) | Maliyet | İhtiyaç doğunca kartla |
| T-09 | Kapalı ajan oturumu kendiliğinden başlatılsın mı (E-14'ün kalan sorusu) | Kullanım şartı ve maliyet riski | Hayır |
| T-10 | Açık kaynak yayın zamanı ve görünürlük | Talimat gereği ayrı karar | Faz 4 sonunda |
| T-11 | Lisans biçimi: AGPL-3.0-only mi, AGPL-3.0-or-later mı | Lisans | `AGPL-3.0-or-later` |
| T-12 | NASA-STD-7009B uyarlaması: YZ kalite incelemesi teknik inceleme faktöründe en çok seviye 2 sayılsın; kırmızı kutu hesaplarda dış inceleme isteğe bağlı kart | Uyarlamayı "Technical Authority" onaylar | Evet |
| T-13 | Taşınacak çalışmaların listesi (BAG-PLU-01 dışında?) ve Faz 1 çıkışında makinende kuru çalıştırma | Veri sende | Yalnız etkin çalışmalar |
| T-14 | Ubuntu sürümün ve desteklenecek sürümler | Yalnız sende olan bilgi (el kitabı §14'te "bekleniyor") | 24.04 LTS + 26.04 LTS |

---

## 21. Kaynaklar

Ayrıntılı kaynak listeleri ve doğrulama durumları araştırma eklerindedir. Bu belgede doğrudan kullanılanlar:

| Kaynak | Doğrulama |
| --- | --- |
| Claude Code belgeleri: headless, cli-reference, authentication, legal-and-compliance, agent-sdk/overview, sessions, costs (code.claude.com) | metin_elde |
| Anthropic Consumer Terms (yürürlük 8 Ekim 2025), claude.com/pricing, platform.claude.com pricing | metin_elde |
| OCCT kullanım kılavuzları ve başlık dosyaları (raw.githubusercontent.com/Open-Cascade-SAS/OCCT), cadquery-ocp-stubs 8.0.1.1.0 | metin_elde |
| dev.opencascade.org, analysissitus.org | ikincil_kaynak (erişilemedi) |
| trimesh, Open3D, pyransac3d, FreeCAD DFM Workbench kaynak kodu | metin_elde |
| openInjMoldSim README, VERSION, LICENSE | metin_elde |
| Kalıp kaba hesap sayıları (SPE, Autodesk Moldflow yardım, üretici blogları) | ikincil_kaynak; kaynaklar arasında çelişki var |
| NASA-STD-7009B (2024-03-05), NASA-HDBK-7009B (2026-02-03), NASA-STD-7009A (2016-07-13) | metin_elde |
| EUR-Lex: GPSR, Makine Tüzüğü, REACH, RoHS | ikincil_kaynak (bot koruması) |
| mevzuat.gov.tr ve Resmî Gazete: 7223, GÜG, PGD, KKDİK, Makine Emniyeti, TR RoHS | metin_elde |
| JCGM 100:2008 (+Amd.1:2026), JCGM 106:2012 (bipm.org) | metin_elde |
| PyPI JSON, npm kayıtları, LICENSE dosyaları (lisans tablosu) | metin_elde |
| gnu.org lisans uyumluluk listesi | ikincil_kaynak (erişilemedi); AGPL ve GPL metinleri başka depolardaki kopyalardan metin_elde |
| Eski sistem: `surec` `d26af89` (el kitabı 0.2, CLAUDE.md, kod, testler, kayit/kurulum) | metin_elde (salt okundu) |

---

## 22. Kalite mühendisi bulguları

<!-- KALITE -->
