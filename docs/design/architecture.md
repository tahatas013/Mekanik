# mekanik v1 — Mimari belge (Faz 0)

| Alan | Değer |
| --- | --- |
| Belge | `docs/design/architecture.md` |
| Sürüm | 0.2 taslak (T-01 kararı işlendi; iki kalite turu) |
| Tarih | 2026-11-06 (sistem saati) |
| Yazan rol | proje-muhendisi |
| Durum | Baş mühendis kararları 2026-11-06 07:20 UTC (§20.4). T-01'in uygulanışı ve yeni açık kararlar T-17, T-18 onay bekliyor |
| Kapsam | Yalnız Faz 0: mimari ve teknik araştırma. Uygulama kodu yok. |
| Eski sistem | `surec` (commit `d26af89`) içeriği için yalnız okundu. Tek istisna baş mühendisin oturum içindeki açık talimatıdır: `.claude/settings.json`'dan 6 "ask" kuralı çıkarıldı (commit `f1e655c`, yalnız `claude/surec-v1-architecture-qphgcj` dalı; `main` değişmedi; §20.3). Eski sistem, v1 aynı işleri yapana kadar çalışmaya devam eder. |

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
- `öneri`: proje mühendisinin önerdiği eşik. 2026-11-06 07:20 UTC'den önce yazılmış "öneri"ler baş mühendisin T-02 kararıyla onaylandı. Bu karardan sonra yazılanlar "öneri (T-01 sonrası; onay bekliyor)" diye işaretlidir (§20.4).

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
| A. Panel kokpit | Proje açma, oturum açma, talimat, kart onayı, dosya alışverişi panelden. mekanik kullanıcının kendi Claude Code'una eklenti/kütüphane olarak bağlanır: skill, alt ajan, kanca, monitor, MCP (T-01). Başsız kip isteğe bağlı, yalnız API anahtarıyla. | §5 |
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

**Baş mühendisin kararları** (2026-11-06 07:20): T-01'de ajanı başsız çalıştırmak yerine mekanik'i kullanıcının kendi Claude Code'una eklenti/kütüphane olarak bağlamayı seçti (§5.4). T-02 … T-16 önerildiği gibi onaylandı; geçici kararlar G-01 … G-22 de onaylandı. Kararın uygulanışı ve T-01'den doğan iki yeni karar (T-17 onay imzası yöntemi, T-18 konuşmanın Claude Code penceresinde olması) onay bekliyor (§20.4). Kalite mühendisinin bulguları ve kapanış durumları §22'dedir.

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
| DUR (Hold) / geçici karar / bildir (Witness) | `hold` / `provisional` / `witness` | v1'de karar iki seviyelidir (DUR ya da geçici); "bildir" karar değil, bilgidir. Eski "inceleme bekliyor" seviyesi geçici karara katıldı (Faz 0 talimatı 2-D) |
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
| Çekirdekte kişi, kurum, makine ve alan adı yok | "Temizlik testi": `src/mekanik/core` içindeki tanımlayıcılar (değişken, fonksiyon, dize sabiti) tam sözcük olarak yasak listeyle karşılaştırılır: kişi adları, kurum kodları, `fdm`, `printer`, `mold`, `molding`, `wing`, `lidar`, `fit` … `print(` ya da `drawing` gibi alt dizgi eşleşmeleri sayılmaz. Liste testte durur; gerçek adlar test sırasında atölye ayarından okunur. | 0 eşleşme |
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
  .claude-plugin/ marketplace.json: repo aynı zamanda Claude Code marketplace'idir (§5.4)
  plugin/         mekanik eklentisi: .claude-plugin/plugin.json, skills/, agents/, hooks/, monitors/, .mcp.json
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

Dal ve etiket adları v1'de İngilizcedir: `<code>/main`, `<code>/work/<topic>`, `<code>/decision/K-<no>-<option>`, `<code>-G<n>`, `<code>-release-<no>`. Şema desenleri bu adları kullanır. Eski adlar (`/ana`, `/is/`, `/karar/`, `-baski-`) kesin karar 1'e aykırı olduğu için geçici kararla korunmadı. Taşınan çalışmaların eski etiketleri geçmiş kaydı olarak kalır; yeni dallar İngilizce açılır. Kesin karardan herhangi bir sapma (eski adların korunması) baş mühendis kararıdır (T-15).

---

## 4. Çekirdek: süreç motoru

Bu bölüm çekirdeğin hedef hâlini anlatır. Faz 1 yalnız eski sistemin yaptıklarını içerir (§17). "Yeni" diye işaretli kurallar, G3 → G2 dönüşü, tanımlama ve politika modülleri Faz 2'dedir.

### 4.1 Varlıklar ve ilişkiler

```
work ─┬─ requirements ──(verification)──> evidence ──> calculation | experiment | check | document | model_view | quality_review
      ├─ stdmap items ──(evidence)──────┘
      ├─ params (quantity: value+unit+source)
      ├─ decisions ──(basis: calc result hash)──> calculation
      │      └─ options ──(branch)──> <code>/decision/K-nn-x
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

- **Kart türleri kayıt defterinden gelir.** Çekirdek türleri: `question`, `decision`, `provisional_decision`, `assumption`, `assumption_list` (V-01), `gate` (O-Gn), `release` (B), `model_note` (N, yalnız baş mühendisin notu), `consistency`, `basis_changed`, `quality_finding`, `deviation`, `migration_gap`. Paketler kendi türlerini ekler: `mech:fit` (G), `mech:flex` (E) …
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
  - `provisional`: geri kalan her karar (geçici karar);
  - `witness`: bildirim; karar değildir.

  El kitabındaki "inceleme bekliyor" seviyesi v1'de yoktur. Faz 0 talimatı "bunların dışındaki her şey geçici karar olur" der; ayrı bir seviye bu kuralı delerdi (kalite bulgusu KM-02). Şema `mode: hold | provisional` dışını reddeder.
- **Seçenekler açık değer taşır.** Her seçenek, herhangi bir seçeneğin değiştirdiği bütün değerleri açıkça taşır (E-17). Model tanımı kayıtta da tutulur (E-15).
- **Kapanmış karar, onaylandığı sürümle değerlendirilir** (E-21): `approved_version`.
- **Dayanak.** Karar dayandığı hesapları sonuç özetiyle kaydeder (B5). Özet değişirse ya da yerine daha doğru bir hesap gelirse karar `review_needed` olur ve "dayanağı değişti" kartı açılır (KARAR-01).
- **Gözlemler.** Karar dayandığı gözlemleri `measured: true|false` ile kaydeder. Yalnız ölçümsüz gözleme dayanan karar şemada geçersizdir (B6).
- **Geçici karar** (§8): görseli ve gerekçesiyle akışa düşer. En az bir alternatif kayda geçer (önceki durum da alternatif sayılır). Modeli ya da bağımlı parametreleri değiştiren geçici karar ayrı dalda ilerler ve bağımlı işler işaretlenir. Diğerleri iş dalında kayda geçer.

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
- **Onay kanalı.** Onay yalnız panelden (teyit penceresi) ya da `mekanik approve` komutundan verilir. Komut TTY ister ve ajan araç listesinde yasaklıdır. Onay kaydının şeması `approval`dır: rol yalnız `chief_engineer` olabilir, imza zorunludur. Kart dizisinde ve karar geçmişinde onay, ret ve geri alma olaylarını başka rol yazamaz (şema).
- **Onay güvenliği** (kalite bulgusu KM-04). Ajan baş mühendisle aynı işletim sistemi kullanıcısıyla çalışırsa ad/e-posta kimliği ve TTY şartı sahtelenebilir: `git -c user.name=…`, `GIT_AUTHOR_*`, sahte pty ya da yerel panele HTTP isteğiyle. Önlemler:
  1. **İmza.** Her onay commit'i baş mühendisin imza anahtarıyla imzalanır (SSH ya da GPG). Açık anahtar atölye ayarındadır (`identities.chief_signing_key`). İmzasız ya da başka anahtarla imzalı onay geçersizdir (APPROVAL-02); kapı ve baskı geçmez. `mekanik verify` bütün onayları denetler; kapı geçişi ve CI bunu çalıştırır.
  2. **Ajan yalıtımı.** Gizli anahtar ajanın erişemeyeceği yerde durur. Ajan, Claude Code'un sandbox özelliğiyle dosya sistemi ve ağ kısıtı altında çalıştırılır (özellik adı ve Linux desteği Faz 1'de belgeden doğrulanacak; bu oturumda doğrulanmadı). `ssh-agent` ve `gpg-agent` soketleri ile anahtar dosyaları ajana verilmez. Ajanın ortamından `SSH_AUTH_SOCK`, `GPG_AGENT_INFO`, `GIT_AUTHOR_*`, `GIT_COMMITTER_*` temizlenir. En güçlü seçenek ajanı ayrı bir Linux kullanıcısıyla çalıştırmaktır; kurulum sudo ister (T-16).
  3. **Panel.** POST istekleri, ajanın okuyamadığı bir oturum sırrıyla (CSRF belirteci) korunur. DUR onayı teyit penceresinden geçer.
  4. **Kalan risk.** Yalıtım kurulmaz ve ajan aynı kullanıcıyla tam yetkiliyse imza anahtarı da okunabilir. Bu yüzden yalıtım varsayılandır ve `mekanik doctor` yalıtımsız çalıştırmayı kırmızı gösterir.
  5. **Eklenti kipi** (T-01 sonrası). Oturumu kullanıcı açtığı için 2. madde mekanik'in elinde değildir. Güvence insan varlığı isteyen imzaya dayanır: donanım anahtarı, kullanım başına onay ya da onay başına parola (§5.4, T-17).
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
| UNCERT-01 | Kritik ölçüde 1/4 kuralı (U ≤ bant/4); alet geçerliliği (kritik ölçüde yalnız biçim için geçerli alet ENGEL; `instruments[].valid_for.critical_dimension`) | OLCU-01, OLCU-02 |
| APPROVAL-02 (yeni) | Onay imzası ve rolü: imzasız, başka anahtarla imzalı ya da baş mühendis dışı onay geçersiz | KM-04 |
| DECISION-02 | İstek listesi olan çalışmada karar kartında "isteklere etkisi" boş olamaz | B8 (eski `kartlar.eksikler`) |
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
- **Ajan dosyaları rol tanımlarından derlenir.** Claude Code'a özgü dosyalar (eklentinin `agents/*.md`'si, kancalar) rol tanımlarından derleme adımıyla üretilir ve eklentiyle dağıtılır (§5.4). Çekirdek bunları bilmez.

### 4.10 Kayıt deposu, dallar ve eşzamanlılık

- **Okuma.** Panel okumaları `--no-optional-locks` ile yapılır (E-20).
- **Paralel çalışma.** Her çalışma kendi worktree'sindedir. Aynı anda en çok 3 aktif çalışma kuralı eskiden tmux oturumlarından sayılıyordu; v1'de ajan çalıştırmalarından (`agent-run`) sayılır. tmux isteğe bağlı platform adaptörü olur.
- **Ana hat.** Ekip ana hatta (`<code>/main`) yazmaz. Ana hatta giriş baş mühendis onayıyla olur.
- **`works.yaml`** yalnız eklenir.
- **Bayt kodu.** Model ve hesap kodu bayt kodu yazmadan yüklenir (E-19).

### 4.11 CLI (`mekanik`)

Eski 23 alt komut (ölçü: `grep -c add_parser cli/surec_cli/ana.py`) v1'de şu adlarla karşılanır. Ek B §3'teki ad önerileri envanter sırasında yazıldı; bağlayıcı adlar bu tablodadır. Ek A ve Ek B'deki modül adlarının karşılıkları: `core.flow` → `core.process`, `pkg_fdm`/`AP:fdm` → `print3d`, `cad`/`AP:cad` → `mech`, `pkg_aero` → `analysis`.

| Eski | v1 | Faz |
| --- | --- | --- |
| `doktor` | `mekanik doctor` | 1 |
| `regresyon` | `mekanik regress` | 1 |
| `kontrol` | `mekanik check` (dosya yazmaz) | 1 |
| `yeni-calisma` | `mekanik work new` | 1 |
| `ac`, `kapat`, `gec` | `mekanik work open` (worktree; terminal komutunu yazar), `mekanik work close`, `mekanik work attach` (isteğe bağlı tmux adaptörü); `mekanik agent send/stop` (gelen kutusu; Faz 2) ve başsız kipte `mekanik agent start` (Faz 2) | 1 / 2 |
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
| `panel` | `mekanik panel` | 2 (arka uç ve kokpit birlikte; KM-25) |
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

Panel kokpittir: durum, kartlar, onay, dosyalar ve ajana talimat paneldedir. Terminal isteğe bağlıdır.

**Ajan modeli** (T-01, baş mühendis kararı, 2026-11-06 07:20 UTC; uygulanışı proje mühendisinin önerisidir, §20.4). mekanik, kullanıcının kendi Claude Code'una eklenen bir **eklenti ve kütüphanedir** (§5.4):

- skill'ler, alt ajanlar, kancalar, bir monitor ve bir MCP sunucusu taşır;
- kullanıcı repoyu kendi Claude'una tanıtır ve yerelde açar;
- ajan oturumunu kullanıcı kendisi açar: Claude Code masaüstü uygulaması (Ubuntu'da beta), VS Code ya da terminal;
- eklenti kipinde mekanik oturum açmaz ve kimlik bilgisine dokunmaz.

Sonuç: ajanla konuşma kullanıcının Claude Code penceresindedir, panel değildir. Bu, kesin karar 6'nın ("panel kokpittir") uygulanışını değiştirir ve baş mühendisin onayını bekler (T-18).

Paneli ajan penceresi olmadan tek başına sürmek isteyenler için başsız kip isteğe bağlıdır. Bu kipte panel ajanı alt süreç olarak çalıştırır; kimlik doğrulama API anahtarı ya da bulut sağlayıcısıdır, abonelik değil (§5.5; öneri, onay bekliyor).

| İş | Panelde | Eklenti kipinde nasıl | CLI eşdeğeri |
| --- | --- | --- | --- |
| Proje ve çalışma açma (kurum, proje, iş türü, dosyalar) | Proje açma ekranı | Aynı; ajan içinden `/mekanik:new` skill'i de olur | `mekanik work new` |
| Ajanı başlatma ve sürdürme | Üst çubuk: "Oturumu aç" | Belgeli yol: `claude-cli://open?cwd=<worktree>&q=/mekanik:resume%20<kod>` derin bağlantısı. Claude Code'u yeni bir terminal penceresinde, çalışma klasöründe ve istem doldurulmuş olarak açar. Masaüstü uygulamasını ya da VS Code'u yerel bir klasörde istemle açmak belgede doğrulanmadı (Faz 2'de denenir). O zamana kadar panel bu yüzeyler için klasör yolunu ve istemi kopyalanabilir verir. Oturumu kullanıcı yönetir | `mekanik work open` |
| Ajanı durdurma | Üst çubuk: "Durdur" | Durdurma bayrağı konur. Eklentinin `PreToolUse` kancası bayrak varken mekanik dışı her aracı modelden bağımsız olarak reddeder; ajan durumunu kaydedip bekler. Monitor ayrıca bildirim gönderir. Yazı üretimi süren bir turu kesmek Claude Code'un kendi arayüzündendir | `mekanik agent stop` |
| Ajana talimat yazma | Akış ekranının altındaki kutu | Talimat çalışmanın gelen kutusuna yazılır; eklentinin monitor'ü onu çalışan oturuma bildirim olarak iletir | `mekanik agent send` |
| Kart onayı, ret, yorum, değer girişi | Kart ekranı (DUR kartlarında teyit penceresi) | Yalnız panelden ya da TTY'den, imzalı; ajan yapamaz (§4.6) | `mekanik approve` (TTY) |
| Geçici karara itiraz | Akış satırı ya da kart | Aynı | `mekanik object` |
| Dosya ekleme (STEP, STL, PDF, görsel) | Sürükle-bırak | Aynı | `mekanik work add-input` |
| Dosya indirme (çıktılar, raporlar, klasör zip) | Dosyalar ekranı | Aynı | — |
| "Terminalde aç" | Her çalışmanın yanında kopyalanabilir komut | `cd <worktree> && claude "/mekanik:resume <kod>"` ya da aynı derin bağlantı | — |

Panel aynı çalışmada iki ajan oturumunun aynı anda yazmasını engeller. Kancalar oturum açılınca kilidi alır (`~/.local/state/mekanik/locks/`); ikinci oturum açılırsa uyarı verir ve salt okunur çalışır.

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

> **Bu araştırmanın sonucu T-01 kararıyla değişti.** Baş mühendis ajanı başsız çalıştırmak yerine mekanik'i kullanıcının kendi Claude Code'una eklenti/kütüphane olarak bağlamayı seçti. Aşağıdaki karşılaştırma, isteğe bağlı başsız kip (§5.5) için geçerliliğini korur. Eklenti yolunun belge doğrulaması: Araştırma A §4a.

Ayrıntı ve birebir alıntılar: `research/a-agent-runtime.md` (erişim 2026-11-06). Kaynaklar indirilip metinden okundu, iki istisna var:

- Max/Ultra API kredisi dipnotu okunamadı: `ikincil_kaynak`.
- Python SDK tekerleğinin Claude Code ikilisini içermesi Araştırma A'da `dogrulanmadi` idi. Araştırma D bunu SDK README'sinden ("The Claude Code CLI is automatically bundled with the package") ve PyPI dosya boyutlarından doğruladı.

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
   - API, 1M token başına girdi / çıktı: Opus 5.5 4 / 20 USD, Sonnet 5.5 2 / 10 USD, Haiku 5.5 0,10 / 0,50 USD (100 000 token'a kadar istemde; üstünde 0,50 / 2,50 USD) ([API pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
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
| Kimlik doğrulama | Abonelik ya da kullanıcının API anahtarı; panel kimlik bilgisine dokunmaz | API anahtarı. Belgeye göre üçüncü taraf ürünlerde claude.ai girişi "previously approved" olmadan izinli değil |
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

Gerekçe:

- **Belgelenmiş olan.** SDK zaten aynı ikiliyi çalıştırıyor. Agent SDK notu, üçüncü taraf ürünlerde claude.ai girişini izinsiz sayıyor (alıntı 6). Legal sayfası ise kullanıcının değiştirilmemiş Claude Code ikilisine kendi aboneliğiyle girmesini açıkça engellemiyor (alıntı 5).
- **Yorum olan.** Kişisel kullanımda abonelikle CLI yolunun şartlara uygun olduğu bir yorumdur, kesin değildir. Aynı sayfanın "Developers building products or services … should use API key authentication" cümlesi (alıntı 4) mekanik'in kendisini de, CLI üstünden çalışsa bile, kapsıyor diye okunabilir. Abonelik sınırlarının "ordinary, individual usage of Claude Code and the Agent SDK" diye anılması da abonelikle SDK kullanımının öngörüldüğünü gösterir.
- **Belirsiz olmayan yol** API anahtarıdır.
- **Açık kaynakta** iki yol da "her kullanıcı kendi hesabı" ilkesine uyar.

T-01 bu belirsizlik görünür biçimde karara bağlanır.

**Açık risk (yorum).** Consumer Terms'teki istisna "where we otherwise explicitly permit it". `-p` ve `setup-token`'ın belgelenmiş olması buna girer diye okunabilir, ama kesin değildir. Bu yüzden mekanik:

- ajanı yalnız baş mühendisin başlattığı çalışmalarda çalıştırır;
- başsız kipte tur ve bütçe sınırı koyar (eklenti kipinde bu bayraklar çalışmaz, §5.4);
- kendiliğinden yeni oturum açmaz.

Eski E-14'ün kalan sorusu ("ekip oturumu kapalıysa `claude -p` ile kendiliğinden başlatılsın mı") bu yüzden **hayır** olarak önerildi ve onaylandı (T-09). Kesin yorum için Anthropic'e sorulabilir.

### 5.4 Eklenti kipi (birincil)

**Dağıtım: repo aynı zamanda bir Claude Code marketplace'idir.** Repo kökünde `.claude-plugin/marketplace.json` bulunur; eklentinin kendisi `plugin/` klasöründedir. Kullanıcı eklentiyi **kullanıcı kapsamında** kurar. Terminalde ya da VS Code'da:

```
/plugin marketplace add <owner>/mekanik
/plugin install mekanik@mekanik
```

(şimdilik `<owner>` = `tahatas013`). Masaüstü uygulamasında eklentiler `/plugin` komutuyla değil eklenti yöneticisi arayüzüyle kurulur (belge, desktop sayfası).

Sonra `/mekanik:setup` skill'i kurulumu kullanıcının izniyle yapar: uv, `mekanik` Python paketi ve `mekanik init` sihirbazı (§13). Repo özel olduğu sürece yalnız erişimi olanlar kurabilir; yayından sonra (T-10) herkes kurar. Eklenti kullanıcı kapsamında kurulunca terminal, masaüstü uygulaması ve VS Code aynı kurulumu görür (Araştırma A §4a).

**"Repoyu kendi Claude'una tanıt"ın düz yolu** (KM2-17). Kullanıcı repoyu klonlayıp ya da adresini verip Claude Code'u içinde açarsa üç şey onu kuruluma götürür:

1. Repo kökündeki `.claude/settings.json`, `extraKnownMarketplaces` ile marketplace'i ve `enabledPlugins` ile eklentiyi tanımlar. Claude Code bunu çalışma alanı güven sorusundan sonra önerir (belge, plugin loading).
2. Repo kökündeki `CLAUDE.md` Claude'a kurulum yönergesini verir: "kullanıcı kapsamında kur, sonra `/mekanik:setup`".
3. `README` aynı yönergeyi insana verir.

Not: depoyla gelen (proje kapsamlı) eklentilerde arka plan monitor'leri yüklenmez (belge: "Background monitors do not load"). Talimat iletimi için kullanıcı kapsamında kurulum zorunludur; `/mekanik:setup` bunu denetler.

**Eklentinin içeriği:**

| Bileşen | İçerik | Eski karşılığı |
| --- | --- | --- |
| `skills/` | `mekanik` (çalışma reposunda geçerli kurallar: kaynaksız sayı, geçme, DUR, kartlar, `mekanik step` ile adım, saat); `new` (çalışma açma); `intake` (tanımlama akışı); `gate` (aşama bitirme); `setup` (kurulum); `resume` (çalışmaya dönüş: durum, bekleyenler, sıradaki iş). Ön madde alanları Agent Skills standardının alanlarıyla sınırlı tutulur; böylece skill'ler başka ajanlarda da çalışır | CLAUDE.md, el kitabı özeti |
| `agents/` | `design-engineer`, `technician`, `quality-engineer`. Rol tanımlarından (`stdlib/roles`) derlenir. Model, derleme anında takma adla yazılır (`opus`, `sonnet`, `haiku`). Ayardaki `agent.roles` yalnız başsız kipte ve yeniden derlemede kullanılır. `${user_config.*}` değerinin ajan ön maddesinde yerine konması doğrulanmadı. Ana oturumun modelini kullanıcı seçer | `ajanlar/*.md` |
| `hooks/hooks.json` | `SessionStart` (engelleyemez, yalnız bağlam verir): çalışma bağlamı, bekleyen yorumlar, kilit, kurum veri kuralı uyarısı. `UserPromptSubmit` (engelleyebilir): bekleyen talimat ve yorumları ekler; veri aktarımı yasak kurumda istemi engeller. `Stop` (engelleyebilir): bekleyen talimat varken durmayı engeller. `PreToolUse` (engelleyebilir): durdurma bayrağında araçları reddeder; ajanın onay ve kimlik komutlarını engeller (`mekanik approve`, `git commit --author`, `git -c user.*`, `GIT_AUTHOR_*`, `git tag`). Bu liste kolaylık katmanıdır, güvence değildir: betikle aşılabilir. Asıl güvence imzadır (§4.6). `PostToolUse`: nabız ve durum | `durum.py`, `bekleyenler --kanca`, izin önerileri |
| `monitors/monitors.json` | `mekanik watch`: panel olaylarını (talimat, onay, ret, yorum, değer, durdurma) çalışan oturuma bildirim olarak iletir. Yalnız etkileşimli oturumda çalışır. Bildirim anahtarı belgeye göre `experimental` altında; masaüstü uygulamasında ve VS Code'da çalıştığı belgede yazmıyor (doğrulanmadı). Yedek yol: `UserPromptSubmit` ve `Stop` kancaları talimatı tur sınırında ekler | `gozcu.py` (E-14) |
| `.mcp.json` | `mekanik mcp`: araçlar `work_status`, `step`, `check`, `decide`, `card_reply`, `calc_run`, `intake_next`, `release_request`, `panel_url` | CLI'nın ajan tarafından Bash ile çağrılması |
| `plugin.json` | Ad, sürüm, `userConfig` (iş repolarının kökü; `mekanik init` bunu atölye ayarındaki `paths.works_root`'a yazar, tek kaynak ayardır) | — |

**Alan paketleri de eklenti olabilir.** `mekanik-molding` gibi bir paket, Python dağıtımının yanında kendi skill'lerini (ör. kalıp tanımlama ağacının konuşma kuralları) bir eklentiyle verir. Bu eklenti `mekanik` eklentisine semver aralığıyla bağımlıdır. Belgenin koyduğu koşullar (KM2-16): aralık git etiketlerinden çözülür (`<eklenti>--v<sürüm>`). Etiketleri sürüm yayınında baş mühendis atar; ajan `git tag` çalıştıramaz. Farklı bir marketplace'teki bağımlılık, kök marketplace'te açık izin olmadan kurulmaz. 0.x sürümleri için aralık `>=0.3 <0.4` biçiminde yazılır (`^1` 0.x'i kapsamaz).

**Neden bu yol** (baş mühendis kararının sonuçları):

- **Kimlik doğrulama belirsizliği büyük ölçüde azalır** (yorum, KM2-10). Kullanıcı kendi Claude Code'unu kendi hesabıyla açar ve yönetir; eklenti kurmak ve skill çalıştırmak belgelenmiş kullanımdır. Panelden gelen talimatlar da insanın yazdığı talimatlardır. Ancak bunları oturuma bir program (monitor) iletir; bu Consumer Terms'teki otomasyon maddesi açısından kesin olarak "otomasyon değildir" denemez. Hiçbir kaynak eklenti kipinin belirsizliği kaldırdığını söylemiyor.
- **Başka ajanlar bağlanabilir, sözleşmeyle** (KM2-11). Skill'ler Agent Skills standardına, araçlar MCP ve CLI'ya dayanır. Ancak bazı güvenceler Claude Code'a özgü kanca ve monitor'lerdedir: talimat iletimi, durdurma, oturum kilidi, veri kapısı. Başka bir ajan barındırıcısı için gereken yetenekler "barındırıcı sözleşmesi" olarak yazılır: araç öncesi kapı, oturum başı bağlam, bildirim kanalı, istem kapısı. Sözleşmeyi karşılamayan barındırıcıda bu güvenceler yoktur ve `mekanik doctor` bunu söyler. Onay ve kapı güvenceleri çekirdektedir (imza, kontroller); barındırıcıya bağlı değildir.
- **"Repoyu kendi Claude'una tanıt, yerelde aç"** karşılanır: marketplace + `/mekanik:setup` ve repo kökündeki ayar ve yönerge (yukarıda).
- **Panel kokpit olarak kalır.** Durum, kart, onay, dosya ve talimat paneldedir. Konuşma kullanıcının Claude Code penceresindedir (T-18). Ubuntu'da masaüstü uygulaması (beta) kurulduktan sonra günlük kullanımda terminal gerekmez. Kurulumu ise terminalde sudo ister (belge: "Open a terminal and run the commands"; `sudo apt install …`); Hold kuralı gereği komutu mekanik yazar, kullanıcı çalıştırır.

**Sınırlar (dürüst):**

- **Durdurma.** Eklenti kipinde panel ajanın sürecini kesmez. Durdurma bayrağı `PreToolUse` kancasıyla araçları modelden bağımsız olarak reddeder (KM2-9). Yazı üreten bir turu kesmek Claude Code'un kendi arayüzündendir.
- **Monitor yalnız etkileşimli oturumda çalışır** (`-p` kipinde başlamaz). Ayrıca kullanıcının tam yetkisiyle ve sandbox dışında çalışır (belge). Bu yüzden `mekanik watch` yalnız okur ve satır yazar; komut çalıştırmaz.
- **Monitor deneyseldir** (KM2-8). Bildirimdeki anahtar `experimental` altında ("manifest shape may still change"); masaüstü ve VS Code'daki davranışı doğrulanmadı. Yedeği tur sınırındaki kancalardır.
- **Channels** (çalışan oturuma doğrudan ileti) araştırma önizlemesinde ve yalnız izin listesindeki eklentileri kabul ediyor. İzin listesi açılırsa monitor'ün yerini alabilir.
- **Tur ve bütçe sınırı yoktur** (KM2-12). `--max-turns` ve `--max-budget-usd` yalnız print kipinde çalışır. Eklenti kipinde kullanım kullanıcının kendi oturumunun ve planının sınırlarındadır; gün sonu özeti ajan kullanımını kancalardan raporlar.
- **Çalışma klasöründeki `.claude/` ve `.mcp.json`** (KM2-14). Kullanıcı oturumu kurum reposunun worktree'sinde açar. Claude Code'un etkileşimli kipteki çalışma alanı güven sorusu ve proje MCP sunucusu onayı burada geçerlidir. Ek olarak `SessionStart` kancası içeriği üretilenle karşılaştırıp fark varsa uyarır. `UserPromptSubmit` kancası fark giderilene kadar istemi engeller.
- **Bağlam maliyeti.** Etkin eklentinin skill ve ajan açıklamaları her turda bağlamdadır; MCP araçları ayrıca araç aramasına göre eklenir. Kullanıcı kapsamında kurulum bu maliyeti bütün projelere yayar. Açıklamalar kısa tutulur, modelin kendiliğinden çağırmasına gerek olmayan skill'ler yalnız kullanıcı çağrılı yapılır ve ölçülür (A11).
- **Güven.** Eklenti kullanıcının yetkisiyle kod çalıştırır (belge). Eklenti dosyaları açık ve okunur tutulur; kurulum belgesi ne çalıştığını listeler.
- **Onay güvenliği bu kipte farklı kurulur** (KM2-1). §4.6'daki ortam temizliği ve sandbox ajanı mekanik başlattığında uygulanabiliyordu. Eklenti kipinde oturumu kullanıcı açar; eklenti sandbox ya da izin ayarı koyamaz (belge: eklenti ayarlarından yalnız `agent` ve `subagentStatusLine` anahtarları etkilidir). Aynı kullanıcıyla çalışan ajan ssh-agent soketine, ayar dosyalarına ve panelin sırrına ulaşabilir. `PreToolUse` listesi betikle aşılabilir. Bu yüzden onay güvencesi ajanı yalıtmaya değil **insanın varlığını isteyen imzaya** dayanır:
  - **(a) Donanım anahtarı.** FIDO2 SSH anahtarı (`ed25519-sk`, dokunma ister). Ajan dokunamaz.
  - **(b) Kullanım başına onay.** `ssh-add -c`: her imzada masaüstü onay penceresi.
  - **(c) Onay başına parola.** Panel imza parolasını her DUR onayında sorar; parola önbelleğe alınmaz.

  `mekanik doctor` önbelleğe alınmış, onaysız bir yazılım anahtarını kırmızı gösterir. APPROVAL-02 yalnız `allowed_signers`'taki baş mühendis anahtarını kabul eder. Kalan risk: kullanıcı onay penceresini ya da dokunmayı ajanın istediği bir anda körlemesine verirse. Bu yüzden panel her imza isteğinde neyin imzalandığını gösterir. Yöntem seçimi T-17. Ayrı Linux kullanıcısı (T-16) başsız kipte geçerlidir; eklenti kipinde ajanın kullanıcı oturumunda çalışması T-01'in doğal sonucudur.
- **Kurum verisi kapısı** (KM2-2). `SessionStart` engelleyemez. Veri aktarımı yasak (`model_provider_allowed: false`) bir kurumun çalışmasında üç katman çalışır:
  1. Panelin "Oturumu aç" düğmesi çalışmaz.
  2. `UserPromptSubmit` kancası istemi engeller; istem modele hiç gitmez (belge: "Blocks the prompt, so it never reaches Claude").
  3. `PreToolUse` kancası o çalışmanın dosyalarına erişen araçları reddeder.

  Kalan risk: kullanıcı eklentiyi kapatıp Claude Code'u o klasörde elle açarsa mekanik engelleyemez; bu kullanıcının kendi kararıdır ve kurulum belgesinde yazılır.

### 5.5 İsteğe bağlı başsız kip (`AgentAdapter`)

Paneli ajan penceresi olmadan sürmek isteyenler için. API anahtarıyla ya da bulut sağlayıcısıyla çalışır (abonelikle değil) ve bütçe sınırı zorunludur; bu, §5.3'teki belirsiz olmayan yoldur (öneri, onay bekliyor: T-01 uygulanışı, §20.4). Ajan yalıtımı (sandbox, ortam temizliği, T-16) bu kipte uygulanır. Arayüz aşağıdadır. Başka ajanlar da bu arayüzle başsız bağlanabilir.

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
- **Çalışma klasöründeki ayar ve kancalar** (kalite bulgusu KM-32). Belgeye göre `--bare` olmadan bir `-p` oturumu, çalışma klasöründeki `.claude/settings.json` kancalarını ve `.mcp.json` sunucularını güven sorusu sormadan çalıştırır. `--bare` ise abonelik kimliğini okumaz (Araştırma A, §2.2 ve §2.6). Kurum repoları dış kaynaklı içerik taşıyabilir. Bu yüzden adaptör ajanı başlatmadan önce çalışma klasöründeki `.claude/` ve `.mcp.json` içeriğini, kendi ürettiği içerikle karşılaştırır (özet). Fark varsa ajan başlamaz ve DUR kartı açılır. Ayarlar `--settings` ile mekanik'in denetlediği dosyadan verilir.
- **Kurum verisinin model sağlayıcıya gitmesi** (KM-50). Ajan çalışınca çalışma verisi model sağlayıcısına gider: dışarıya veri gönderme, Hold. Her kurum kaydında `data_transfer.model_provider_allowed` zorunludur (config şeması). `false` ise ajan o kurumun çalışmasında başlatılmaz. Değeri kurulum sihirbazı baş mühendise sorar.

### 5.6 Arka uç

- **Kabuk ve uç noktalar.** FastAPI kabuğu (eski `uygulama.py`). REST okuma uçları ve olaylar için SSE kullanılır. Eski uç noktalar İngilizceleşir; eşleme Ek B §4'tedir.
- **Ağ ve güvenlik.**
  - Varsayılan `127.0.0.1` (ayardan).
  - Host ve Origin denetimi korunur (eski e2e testi).
  - Dışarı açmak platform adaptörünün işidir (`platform.remote_access: tailscale_serve`); çekirdek Tailscale'i bilmez.
- **Ajan durumu.** Eklenti kipinde ajan durumu kancalardan gelir: oturum açık mı, son araç, son adım, kim bekliyor. Başsız kipte her çalıştırma bir alt süreçtir; panel kapanınca kesilmez, oturum kimliğiyle yeniden bağlanılır, panel yeniden başlayınca `~/.local/state/mekanik/runs/` okunur.
- **Gelen kutusu.** Panelden yazılan talimat ve durdurma istekleri çalışmanın gelen kutusuna (`~/.local/state/mekanik/inbox/<kod>.jsonl`) yazılır. Eklentinin monitor'ü (`mekanik watch`) ve kancaları onu oturuma iletir. İletim ve okunma kayda geçer.
- **Dosya yükleme.**
  - STEP/STL/PDF/görsel `inputs/` altına yazılır; SHA-256 `work.yaml`'a eklenir.
  - Boyut sınırı ayardan gelir.
  - İndirme yalnız `out/`, `records/` ve `inputs/` altından yapılır. Yol kaçışı (`..`) reddedilir; eski güvenlik testi taşınır.
- **Gözcü** (eski `gozcu.py`, E-14). Artık eklentinin monitor'üdür (`mekanik watch`). Baş mühendisin commit'lerini ve gelen kutusunu izler, çalışan oturuma bildirim olarak iletir. Oturum yoksa olay "bekleyen" kalır; kendiliğinden oturum açılmaz (T-09).

### 5.7 Veri şeması

- `agent-run`: çalıştırma kaydı (başsız kipte süreç; eklenti kipinde kancalardan gelen oturum durumu). Kimlik bilgisi alanı yok; `additionalProperties: false`.
- `stream-event`: akış satırı.
- `config.agent`: kip (eklenti ya da başsız), kimlik doğrulama türü (başsız kipte), rol → model, sınırlar. Eklenti kipinde `auth` alanı bilgi amaçlıdır; kimlik doğrulamayı Claude Code yapar.

### 5.8 Kabul ölçütleri (Faz 2; eklenti dağıtımı Faz 4)

| # | Ölçüt | Eşik | Kaynak |
| --- | --- | --- | --- |
| A1 | Proje açma, oturum açma, durdurma talimatı, ajana talimat, kart onayı, dosya ekleme/indirme panelden, terminal adımı olmadan (oturum masaüstü uygulamasında ya da VS Code'da açılabilir) | 7/7 iş, her biri bir Playwright e2e testiyle (ajan tarafı sahte adaptör ya da kaydedilmiş oturumla) | öneri (T-01 sonrası; onay bekliyor) |
| A2 | Akış gecikmesi: kanca ya da adaptör olayından panel satırına | p95 ≤ 1,0 s (100 olay) | öneri (T-01 sonrası; onay bekliyor) |
| A10 | Eklenti kurulumu, temiz bir makinede. Elle adımlar şunlarla sınırlı: Claude Code'un kendi kurulumu ve girişi; eklentinin kurulması (terminal/VS Code'da iki `/plugin` komutu, masaüstünde eklenti yöneticisi arayüzü); `/mekanik:setup`; onun istediği izinler ve `mekanik init` soruları; gerekirse yazdığı sudo komutu | Sayılan adımlar dışında elle adım 0; sonunda `mekanik doctor` yeşil. Faz 4'te elle ölçülür ve adım adım kaydı tutulur | öneri (T-01 sonrası; onay bekliyor) |
| A11 | Eklentinin tur başına bağlam maliyeti: modelin kendiliğinden çağırabildiği skill ve ajan açıklamaları + MCP araçlarının tur başına payı | ≤ 1 500 token; "Measure plugin cost" yöntemiyle ölçülür | öneri (T-01 sonrası; onay bekliyor) |
| A12 | Talimat iletimi: panelden yazılan talimatın çalışan oturuma ulaşması | Terminalde etkileşimli oturumda (monitor) p95 ≤ 5 s. Masaüstü/VS Code'da monitor doğrulanana kadar tur sınırında (kanca). Oturum kapalıysa "bekleyen" görünür ve oturum açılınca ilk bildirimdir (3/3 test) | öneri (T-01 sonrası; onay bekliyor) |
| A3 | Ekran metni yanıt süresi | p95 ≤ 0,5 s. Eski panel ölçüsü 0,04–0,48 s, en çok 0,94 s (ölçü: `kayit/kurulum/hiz-olcumleri.txt`) | öneri, eski ölçüye dayalı |
| A4 | 3B model ilk görüntü | p95 ≤ 1,5 s önbellekte; ≤ 2,0 s önbelleksiz. Eski: 1,0–1,4 s; önbelleksiz 1,6 s (aynı dosya) | öneri, eski ölçüye dayalı |
| A5 | Durdurma. Eklenti kipinde: bayrak konduktan sonra mekanik dışı her araç çağrısı reddedilir (kanca birim testi, modelden bağımsız). Başsız kipte: "Durdur"dan sürecin bitmesine ≤ 5 s, tur kaydı "interrupted" | 3/3 test (iki kip ayrı) | öneri (T-01 sonrası; onay bekliyor) |
| A6 | Sürdürme: panel yeniden başladıktan sonra oturumun durumunu yeniden görme (eklenti) ya da çalışan sürece yeniden bağlanma (başsız) | 10 denemede 10 | öneri (T-01 sonrası; onay bekliyor) |
| A7 | Kimlik bilgisi sızıntısı | `agent-run`, `events.jsonl`, günlük ve panel yanıtlarında gizli bilgi taraması: 0 bulgu | öneri |
| A8 | Oturum kilidi: aynı çalışmada ikinci oturum yazmaya çalışırsa | uyarı + salt okunur, 3/3 test | öneri (T-01 sonrası; onay bekliyor) |
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
2. **İçe alma da bir işlemdir.** Okuma ve iyileştirme (`ShapeFix`, `UnifySameDomain`) geometriyi ve toleransı değiştirir. Bu yüzden parametreleriyle kaydedilen bir işlemdir (OP-00). STEP okuma parametreleri (`read.precision.*`, `read.maxprecision.*`) `base.import.read_params`'a zorunlu olarak yazılır (şema).
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
   1. İndeks: `TopExp::MapShapes` sırası. Belirlenimci olması için üç koşul gerekir: aynı çekirdek sürümü, aynı girdi BRep, aynı okuma ve iyileştirme parametreleri. Bu bilgi OCCT kaynak kodunun okunmasından çıkarımdır, test edilmedi. Faz 3'ün B1 ölçütü bunu sınar; o zamana kadar indeks yalnız hızlı yoldur.
   2. Geçmiş soyu: `BRepTools_History` Modified/Generated.
   3. Geometrik imza: yüzey türü, alan, ağırlık merkezi, normal ya da eksen, yarıçap, kenar sayısı, komşu yüzey türleri.
   4. Sıfır ya da birden çok aday varsa **dur ve kart aç**.

   `index` dışındaki her eşleşme akışa bildirilir. Kıyım (hash) tabanlı kümelerin sırası kullanılmaz; bellek adresine bağlıdırlar.
7. **Araç katısı + Boolean.** Kendi ürettiğimiz yüzler belirlenimci araç katısı üzerinden adlandırılır. Bu yüzden delik ve kabartma `BRepFeat` yerine "araç katısı + Boolean" ile yapılır.
8. **Çekirdek sürümü sabittir.** OCCT, OCP ve CadQuery sürümü `model-oplist.kernel`'de yazılıdır. Sürüm yükseltmesi tam regresyon ister. OCCT'de Boolean sonuç sırası sürümler arasında değişmiştir (Araştırma B, K31).
9. **Yeniden üretim denetimi.** Aynı işlem listesi iki kez oynatılır; yüz imza tabloları ve şekil özeti aynı çıkmalıdır.

### 6.3 İçe alınan STEP'te neler güvenle yapılabilir (dürüst tablo)

Kaynak: `research/b-cad.md`. OCCT kılavuzu ve başlık dosyaları `metin_elde`; güvenilirlik belgelerdeki sınırlara dayanan nitel değerlendirmedir, ölçüm değildir.

**Sürüm notu** (KM-34). API varlığı OCCT master belgeleri ve `cadquery-ocp-stubs 8.0.1` üzerinde doğrulandı. G-06 Faz 1 için OCP 7.9.3 seçiyor; bu sürüm için tablo Faz 3 başında yeniden doğrulanır.

| İşlem | Yol | Güvenilirlik | Sınır |
| --- | --- | --- | --- |
| Kesme, ekleme (Boolean) | `BRepAlgoAPI_Cut/Fuse`, `SetNonDestructive`, gerekirse `SetFuzzyValue` | Geçerli girdide yüksek; kötü STEP'te orta | Argümanlar geçerli olmalı; büyük tolerans ve teğetlik hata verir |
| Delik | Döndürülmüş araç katısı + Cut (`BRepFeat_MakeCylindricalHole` yalnız düz silindir) | Yüksek | Havşa ve kademe araç katısıyla |
| Pah | `BRepFilletAPI_MakeChamfer` | Orta–yüksek | Fillet'e benzer yayılma ve köşe sorunları beklenir (`dogrulanmadi`) |
| Yuvarlatma | `BRepFilletAPI_MakeFillet` | Basit dışbükey kenarda orta–yüksek; köşe birleşimi, karışık kenar ve B-spline'da düşük–orta | Teğet zincir boyunca kendiliğinden yayılır (seçilmeyen kenar da yuvarlanır); kısmi sonuç dönebilir |
| Kalıptan çıkma açısı | `BRepOffsetAPI_DraftAngle` | Orta | Yalnız düzlem, silindir ve koni; topolojiyi değiştiremez |
| Kabuk | `MakeThickSolidByJoin` | Düşük–orta | Bazı modlar belgeye göre "tam uygulanmadı" |
| Yüz öteleme | Düzlemsel yüz + dik komşularda araç prizması + Boolean (komşu yüzleri uzatmaz); genel durumda `BRepOffset_MakeOffset::SetOffsetOnFace` (sıfır global ofset) | Dik komşuda orta–yüksek; eğik ve eğri komşuda düşük | OCCT kullanım kılavuzlarında ayrı bir "yüzü taşı" API'si **bulunamadı** (başvuru kılavuzu erişilemedi; yokluk kanıtlanmadı). İkinci yol kaynak kodundan çıkarım, test edilmedi |
| Detay silme | `BRepAlgoAPI_Defeaturing` | Orta | Özellik tanımaz, yüzleri biz veririz; silemezse uyarı verip devam eder: `HasWarnings()` zorunlu kapı |
| Aynı yüzeydeki yüzleri birleştirme | `ShapeUpgrade_UnifySameDomain` | Yüksek | Bütün yüz indekslerini değiştirir; başvurular geçmişle taşınır |
| Parametrik ölçüyü değiştirme ("bu deliği 8'den 10'a çıkar") | — | **Yapılamaz** (özellik ağacı yok) | Yerine: detay silme + yeni delik, ya da yüz öteleme. Özellik tanıma için Analysis Situs (BSD-3, C++) aday. PyPI'de Python paketi bulunamadı; işlev kapsamı yalnız dosya adlarından anlaşıldı (`dogrulanmadi`) |
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

**1. İş türü.** Çekirdek "iş türü" kavramını bilir; türleri paketler getirir (şema `work-type`, `provided_by`). Böylece çekirdekte alan adı kalmaz (kalite bulgusu KM-05). Faz 0 talimatındaki beş tür:

| Kimlik | Tür | Model türü | Sağlayan paket |
| --- | --- | --- | --- |
| `new_part` | Sıfırdan parça | parametric | mech |
| `mold_for_part` | Verilen parçaya kalıp | hybrid | molding |
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

- **Durup sorar** (DUR, `hold`). Kesin karar 7'deki sekiz kategori: `manufacturing_method`, `material`, `main_dimensions`, `deviation_from_standard`, `cost_impact`, `release_production`, `requirement_change`, `chief_only_info`. Ayarda bu liste yalnız genişletilebilir; şema sekizinin de bulunmasını zorunlu tutar.
- **Geri kalan her şey geçici karardır** (`provisional`). Üçüncü bir "inceleme bekliyor" seviyesi yoktur (§4.4).
  1. Görseli ve gerekçesiyle akışa bir satır olarak düşer (şema `stream-event`: görsel zorunlu).
  2. En az bir alternatif kayda geçer (şema; önceki durum da alternatif sayılır). Modeli ya da bağımlı parametreleri değiştiren karar ayrı dalda ilerler (`<code>/decision/K-nn-x`) ve bağımlı işler işaretlenir. Diğerleri iş dalında kayda geçer.
  3. Baş mühendis bir sonraki kapıya kadar itiraz edebilir (akış satırında ya da kartta "İtiraz et").
  4. İtiraz gelirse karar `objected` olur; ekip ya alternatife döner (`objected_reverted`: bağımlı işler bağımlılık kaydından listelenir) ya da gerekçeyle sürdürmeyi önerir. Sürdürmenin kendisi baş mühendis onayı ister (`objected_kept`).
  5. İtiraz gelmezse kapı geçişiyle karar `accepted_at_gate` olur. Kapı kartı itirazsız geçici kararları listeler; kapıyı onaylamak onları da onaylamaktır. Kart bunu açıkça yazar.
- **Kategoriyi kim belirler?** Kategoriyi kararı açan rol yazar. Ama kural tabanlı sınıflayıcı da çalışır ve hangisi daha sıkıysa o geçerli olur. Sınıflayıcı şunlara bakar:
  - karar bir ana ölçüyü değiştiriyor mu. Ana ölçü: istek ölçütünde geçen, dış arayüze giren ya da baş mühendisin işaretlediği parametre (`quantity.main_dimension`). İşareti ekip koyamaz ve kaldıramaz; değişiklik onay ister (KM-19);
  - bir malzeme ya da üretim profilini değiştiriyor mu;
  - maliyet hedefine dokunuyor mu;
  - bir standart maddesinin kabul ölçütünü gevşetiyor mu;
  - bir kural kataloğu sınırının dışında kalan değeri kabul ediyor mu. Bu da sapmadır (`deviation_from_standard`); UYARI'yı işi yapan kabul edemez (KM-27);
  - istek listesini değiştiriyor mu.

  "Neyin sorulacağını kurallar belirler, modelin kanaati değil" ilkesinin karşılığıdır.
- **Acil olmayan sorular aşama sonunda toplu gelir.** `urgency: stage_end` soruları ve inceleme bekleyen kararlar `stage finish` sırasında tek bir "aşama sonu soru paketi" kartında toplanır.
- **Açık dallı geçici karar sınırı.** El kitabı §14'teki varsayılan 5'tir (ayarda `max_open_provisional`). Sınır yalnız ayrı dalda ilerleyen geçici kararları sayar. Doluysa yeni dallı karar açılmaz; ekip bağımsız işe geçer. Dalsız geçici kararlar sınırı tüketmez; böylece iş tıkanmaz.

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

**Her adım bir satır** (şema `stream-event`; `line` en çok 200 karakter, öneri: dar ekranda iki satırı geçmesin diye). Satırda:

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
- **Bağımsızlık tanımı:** ikinci yöntem farklı bir yöntem sınıfında (`level` 1/2/3) olmalı ya da farklı formül yapısıyla ve ortak ara sonuç kullanmadan çalışmalı. Aynı formülün yeniden yazılması bağımsız sayılmaz. Aynı yapıda ve aynı türetilmiş girdiyle çalışan iki şablon da bağımsız sayılmaz; ör. iki ayrı katsayıyla F = p·A (KM-11). Paylaşılan girdiye ancak o girdinin kendisi iki yöntemle doğrulanmışsa izin verilir (ör. izdüşüm alanı hem B-rep dış hattından hem ağ izdüşümünden). Örnek: E-30'daki formül hatası VLM ile bulundu.
- **Açık kaynakta ikinci yöntem yoksa** (ör. kalıp kapama kuvvetinde dolum simülasyonu araştırma düzeyinde): hesap kritik kanıt sayılmaz. İkinci yöntem bir ölçümdür (`level 3`; kalıp denemesinde pres kuvveti) ve o zamana kadar CALC-03 kartı açık kalır.
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

**Her hesap çalıştırmasında** girdi kümesi bu bölgelerle karşılaştırılır. Sonuç `calculation.validity.zone` alanına yazılır: `validation`, `verification`, `limits`, `outside` ya da `undefined`. Placard'ın üç alanı (sınır türü, aşım miktarı, etki) `verification` ve `limits`'te şemayla zorunludur. Her sonuçta belirsizlik beyanı (`quantitative`, `qualitative` ya da `none_available`) zorunludur ([M&S 33]).

| Bölge | Sonuç durumu | Kanıt olabilir mi |
| --- | --- | --- |
| Geçerleme alanında | `ok` / `marginal` / `bad` (hesabın kendi değerlendirmesi) | Evet |
| Yalnız doğrulama alanında | Uyarı etiketi (placard): "doğrulanmış, geçerlenmemiş" | Evet, uyarıyla; kartta görünür |
| Yalnız sınırlar içinde (dış değerleme) | Placard + aşılan sınırın türü ve miktarı + sonuca etkisi (M&S 26 b) | Yalnız baş mühendis gerekçeli onayıyla |
| Sınır dışında | `unreliable` ("güvenilmez") | **Hayır** (CALC-04 ENGEL) |
| Alan tanımsız | `in_domain: null` | Kart açar: "geçerlilik alanı tanımsız" |

Örnek: E-39'da NeuralFoil eğitim alanı dışındaydı (güven 0,01–0,06). v1'de bu sonuç sınır dışı sayılır ve kanıt olamaz.

### 10.4 NASA-STD-7009B'nin uygulanması

Kaynak: NASA-STD-7009B (onay 2024-03-05, 43 gereksinim) ve NASA-HDBK-7009B (kapak onayı 2026-02-03). İkisi de standards.nasa.gov'dan okundu (`metin_elde`; Araştırma D, §1). Not: HDBK-7009B'nin sayfa başlıklarında hâlâ "DRAFT" yazıyor; belge geçmişi tablosundaki tarih (2025-09-24) kapakla tutarsız. Atıfta kapak tarihi kullanılır.

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
| Her hata bir regresyon testine dönüşür | Hata kaydı şeması (`error-record`) `regression_case`'i zorunlu tutar (en az 2 alt vaka: biri kalır, biri geçer). Kalite bulgusu kapanırken `quality-review` şemasında "regresyon gerekir mi" alanı zorunludur: evet ise vaka yolu, hayır ise gerekçe. CI her kapalı hata kaydının vakasını çalıştırır. | el kitabı §13 |
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
| JCGM 100:2008, JCGM 106:2012 | — | metin_elde. JCGM 100 Amd.1:2026 için yalnız kapak ve künye okundu. JCGM PDF'leri telif nedeniyle repoya konmaz, yalnız bağlantı verilir |
| NASA-STD-7009B, NASA-HDBK-7009B | — | metin_elde |

### 10.9 Kalite ve güvence verisinin yeri

| Kayıt | Şema / dosya |
| --- | --- |
| Hesap ve geçerlilik | `calculation` (`validity`, `cross_check`, `critical`) |
| Kanıt | `evidence` |
| Standart haritası | `standard-item` |
| Analiz aracı kaydı | `stdlib/tools/*.yaml` (Faz 1'de şeması kesinleşir; alanları §10.3 ve §10.4'te) |
| Kalite incelemesi | `quality-review` → `records/quality/*.yaml` |
| Onay | `approval` → `approvals.yaml` |
| Hata kaydı | `error-record` → kurum reposunda `errors/H-nnn.yaml` + regresyon vakası |

**Ölçümün bağımsızlığı** (KM-33). Tohumlanmış hata derlemini (F1) ve tanımlama vakalarının beklenen cevaplarını (§7.2) uygulayıcı ekip değil, kalite mühendisi temiz bağlamla yazar. Derlem ekibe yalnız sonuçlarıyla gösterilir. Böylece ölçü yalnız ekibin bildiği hata türlerine daralmaz.

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
| F6 | Pilot çalışmalarda kapıdan sonra bulunan hata | Baskı/üretim kararına ulaşan: 0. Her biri ≤ 7 gün içinde regresyon vakası olur | 2–3 | öneri |
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
  checks: [DRAFT-01, WALL-01, RIB-01, UNDERCUT-01, CLAMP-01, FLOW-01, QTY-01]   # tam kimlik molding:DRAFT-01 …
  calc_templates: [clamp_force_area@1, cooling_time_slab@1, cycle_time@1, coolant_flow@1, shrinkage_scale@1]
  work_types: [mold_for_part]
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
| Kontroller (tam kimlik `molding:<KURAL>`) | `DRAFT-01` en küçük çıkma açısı (malzeme ve doku profilinden) · `WALL-01` et aralığı ve düzgünlük · `RIB-01` kaburga/et oranı · `UNDERCUT-01` çözüm kararı olmayan negatif açı → kart · `CLAMP-01` kapama kuvveti × güvenlik çarpanı ≤ pres kapasitesi · `FLOW-01` akış boyu/et oranı ≤ malzeme sınırı · `QTY-01` adet < kalıp başabaş adedi → alternatif bulgusu |
| Hesap şablonları | `clamp_force_area`: F = p·A·k (p, A, k kaynaklı; A iki yöntemle: B-rep dış hattı ve ağ izdüşümü). Ton/inç² kuralı aynı formül yapısında olduğu için ikinci bağımsız yöntem **sayılmaz** (§10.2); ikinci yöntem kalıp denemesinde pres kuvveti ölçümüdür. `cooling_time_slab`: levha formülü; katsayı türetmeyle sabitlenir, çünkü kaynaklar çelişiyor (π² ve 2π). `cycle_time`, `coolant_flow` (Re hedefi), `shrinkage_scale` |
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
| Dolum simülasyonu | Araştırma düzeyi; endüstriyel karar için **yapılamaz** | openInjMoldSim README: "prohibitively inconvenient for typical industrial use". Pedro vd. 2020 doğrulaması Moldex3D'ye karşı; Krebelj vd. 2021 basınç gelişimini deneyle kıyaslamış (ikisi de `ikincil_kaynak`). Malzeme verisi (13 Tait + 7 Cross-WLF parametresi) açık kaynakta yok |
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
| Claude Code | Masaüstü uygulaması (Ubuntu'da beta; kurulumu terminalde sudo ister, Hold: komutu mekanik yazar, kullanıcı çalıştırır) ya da CLI/VS Code eklentisi; giriş kullanıcının kendi akışıyla | mekanik kimlik bilgisine dokunmaz |
| İsteğe bağlı | Dilimleyici (AppImage/Flatpak), FreeCAD (teknik resim), CalculiX ve benzeri | `mekanik doctor` önerir, kurmaz |

### 13.2 Adımlar

**Yol 1 (önerilen): kullanıcının kendi Claude Code'u içinden** (T-01). Claude Code açıkken:

```
/plugin marketplace add <owner>/mekanik      # şimdilik <owner> = tahatas013
/plugin install mekanik@mekanik
/mekanik:setup
```

`/mekanik:setup` aşağıdaki 1–8. adımları kullanıcıyla konuşarak, her komut için izin isteyerek yapar. sudo gerektiren adımı yalnız yazar, kullanıcı çalıştırır. Claude Code Ubuntu'da masaüstü uygulaması (beta), VS Code ya da terminal olarak kurulabilir.

**Yol 2: kabuktan tek komut.** Faz 4'te kesinleşecek komut biçimi:

```bash
curl -LsSf https://<yayın-adresi>/install.sh | sh
```

Repo özel olduğu sürece baş mühendisin makinesinde `uv tool install git+ssh://…` kullanılır.

1. **Ortam denetimi.** İşletim sistemi ve sürüm; Ubuntu değilse açık iletiyle durur.
2. **git ve curl.** Eksikse `sudo apt install -y git curl` satırını yazar ve durur. Hold kuralı: sudo'yu kullanıcı çalıştırır.
3. **uv.** Yoksa kullanıcı düzeyinde kurar.
4. **mekanik.** `uv tool install mekanik[mech]`.
5. **Claude Code ve eklenti.** `claude --version` yoksa resmî kurulum yolunu (masaüstü uygulaması ya da CLI) ve belge bağlantısını yazar. Kullanıcı kendi hesabına Claude Code'un kendi akışıyla girer. Eklenti kurulu değilse iki marketplace komutunu yazar (`claude plugin marketplace add …`, `claude plugin install …`).
6. **`mekanik init` sihirbazı** (terminal ya da panelin ilk açılış sayfası). Sorular:
   - kişi adı ve e-posta (git kimliğiyle karşılaştırılır);
   - iş repolarının kökü;
   - ilk kurum (varsayılan "Bağımsız", `IND`), kurumun maliyet eşiği (T-07) ve verisinin model sağlayıcısına gidip gidemeyeceği (`data_transfer.model_provider_allowed`, Hold);
   - makine ve ölçme aletleri (isteğe bağlı; değerler `assumption` ile başlar);
   - dil;
   - ajan kipi: eklenti (varsayılan; kimlik doğrulamayı Claude Code yapar) ya da başsız (API anahtarı ya da bulut sağlayıcısı + bütçe sınırı);
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
| K1 | Temiz Ubuntu 24.04 konteynerinde ve 26.04 sanal makinesinde: tek komut + Claude girişi → `mekanik doctor` | Bütün zorunlu maddeler yeşil. Claude girişi gerçek hesap ister; bu adım CI'de otomatikleşemez, elle ölçülür ve kaydı tutulur. CI kısmı sahte adaptörle koşar | öneri |
| K2 | Kurulum süresi (100 Mbit/s bağlantı, indirme dahil) | ≤ 15 dk | öneri |
| K3 | Betiğin içinde sudo | 0 | Hold kuralı |
| K4 | Örnek proje: G0 → G3 uçtan uca (sahte ajanla, CI'de) | geçer | öneri |
| K5 | Kaldırma sonrası iş repoları | değişmemiş (özet karşılaştırması) | öneri |

---

## 14. Mevcut çalışmaların taşınması

### 14.1 Kapsam

- **Veri baş mühendisin makinesinde.** Eski kurum repoları (ör. `~/is/bag`: BAG-PLU-01) ve arşivler bu oturumdan görünmüyor. Taşınacak çalışma listesini baş mühendis onaylar (T-13).
- **Öneri.** Etkin çalışmalar taşınır. Arşivdekiler eski araçla okunabilir kalır, istenirse sonra taşınır.
- **Eski sisteme dokunulmaz.** Taşıma eski dalları değiştirmez. Yeni dosyalar ayrı bir dalda (`<code>/work/v1-migration`) oluşur; eski sistem kendi dallarında çalışmaya devam eder.
- **Zamanlama** (KM-25). Faz 1'de yalnız kuru çalıştırma yapılır. Gerçek geçiş (`--apply`) Faz 2'de, yeni panel hazır olunca yapılır. Böylece hiçbir çalışma panelsiz kalmaz: eski panel v1 biçimini okuyamaz.

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
| V1 | Şema: her yeni dosya v1 şemasından geçer | 0 hata. Tek istisna "taşıma eksikleri"dir: v1'de zorunlu olup eskide karşılığı olmayan alanlar (ör. `work.work_type`, `work.packages`, onaylı zorunlu istekte `verification`, hesapta `validity`). Betik bunlara değer uydurmaz (KM-37). Alan `migration_gap` listesine yazılır ve çalışma bir `migration_gap` kartıyla (DUR) açılır. Türetilebilenler önerilir ama onaylanmadan yazılmaz (ör. FDM profili → `print3d`, parametrik model → `new_part`). Liste kaynaklı biçimde dolana kadar çalışma kapı geçemez |
| V2 | Sayı korunumu: eskideki her sayısal değerin çoklu kümesi yenisinde aynı (eski `gecis.sayi_korunumu` fikri) | kayıp 0, yeni sayı 0 |
| V3 | Kaynak etiketi eşlemesi | eşlenmeyen etiket 0; eskide kaynaksız olan yenide de kaynaksız (ENGEL korunur) |
| V4 | Kontrol eşitliği: eski `surec kontrol` ile yeni `mekanik check` | Kural kimliği eşlenmiş (konu, seviye) kümeleri aynı; fark varsa her biri bilinen bir kasıtlı değişiklik listesinde |
| V5 | Onay eşitliği | Eskide geçerli olan onay yenide geçerli. Alan adları değiştiği için özet değişir; `migrated_from_hash` + yeni özet yazılır. İçerik değişmediyse onay korunur |
| V6 | Model eşitliği | Hacim, sınır kutusu, yüz sayısı aynı (bağıl fark ≤ 1e-6, öneri). Farklı OCP sürümünde tessellation özeti değişebilir; geometrik özellik kullanılır |
| V7 | Kart eşitliği | Açık kartların anahtar kümesi aynı |
| V8 | Hesap eşitliği | Hesaplar yeniden çalışır; sonuçlar aynı (bağıl ≤ 1e-9, öneri; aynı kod ve aynı kütüphane sürümleri) |

Her çalışma için `migration-report.md` üretilir ve baş mühendise DUR kartıyla gider.

### 14.4 Kabul ölçütleri

| Faz | Ölçüt |
| --- | --- |
| Faz 1 (CI) | S-001 ve sentetik H-001 V1–V8'den geçer |
| Faz 1 çıkışı (baş mühendisin makinesinde) | BAG-PLU-01 kuru çalıştırması V1–V8'den geçer (taşıma eksikleri listesi raporda) |
| Faz 2 | Gerçek geçiş (`--apply`); taşınan çalışmalar yeni panelde açılır, eski panelle aynı kartları gösterir |

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
- Ek B §14'teki testi olmayan taşınır parçalardan 16'sı için yeni test yazılır; 17. madde (`.python-version`, `.gitignore`) test gerektirmez. En önemlileri: `fea.py`, `gozcu.py`, `nabiz.py`, `gunluk.py`, bayt kodu yazmama, ayrık katı reddi, katalog–kod bağı, CLI duman testleri.
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

Her faz kullanılabilir bir sonuçla biter. Eski sistem, v1 aynı işi kanıtlanmış biçimde yapana kadar çalışır. Eşiklerin onay durumu başlıktaki nota göredir (T-02); ölçü dayanağı olanlar yazılıdır.

### Faz 1 — Çekirdek (eşitlik; yeni özellik yok)

**Kapsam:**

- çekirdek (§4);
- `mech` (parametrik CadQuery modeli, geçme kaydı, mekanik kontroller, görünüşler: eski davranış);
- `print3d` (yalnız eskiden olanlar: tabla sığması, tabla teması, tek katı, tahmin, baskı isteği);
- `analysis` (Calc API, eski `fea.py`);
- CLI (§4.11'deki Faz 1 satırları);
- atölye ayarı;
- eklenti iskeleti (§5.4): alt ajanlar, kancalar ve `mekanik` skill'i. Eski `.claude` şablonlarının ve kancalarının karşılığıdır. Eklenti `--plugin-dir` ile yerelden yüklenir. Kalite mühendisi ajan üzerinden çalışır;
- taşıma betikleri (§14; yalnız kuru çalıştırma).

**Kapsam dışı:**

- panel arka ucu ve yeni ön yüz: ikisi birlikte Faz 2'de. Eski panel eski sistemle çalışmaya devam eder; v1'e gerçek geçiş Faz 2'dedir (KM-25);
- tanımlama, politika motoru, akış arayüzü, standart haritası;
- içe alma ve işlem listesi;
- "yeni" işaretli kontroller (CALC-03, CALC-04, REQ-01'in G4/G5 şartı, STDMAP-01, SOURCE-02); APPROVAL-02 (imza) ise güvenlik hatası kapattığı için Faz 1'dedir;
- G3 → G2 dönüşü.

**"Yeni özellik" tanımı** (KM-24). Faz 1'de izin verilen değişiklikler:

- yeniden adlandırma (İngilizce);
- katman taşıma (atölye ayarı, paket);
- arayüz metninin kataloğa alınması;
- testle kapanan hata düzeltmesi (ör. onay yetkisi, imza).

Baş mühendisin gördüğü davranışı değiştiren her şey yeni özelliktir ve Faz 2+'dadır. Faz 1, şemaların eski davranışı kapsayan alt kümesiyle çalışır (`schemas/README.md` faz notu). Eskide olmayan sıkılaştırmalar Faz 1'de uyarıdır: kritik hesapta ikinci yöntem, geçerlilik bölgesi, belirsizlik beyanı, ölçümsüz gözlem kuralı.

| # | Kabul ölçütü | Eşik | Dayanak |
| --- | --- | --- | --- |
| 1.1 | Eski CLI işlevlerinin v1 karşılığı (§4.11 Faz 1 satırları) | %100; her biri duman testiyle | Ek B §3 |
| 1.2 | Eski testlerin taşınması | 86 test fonksiyonu (36 + 42 + 6 + 2) v1 API'siyle geçer | ölçü: Ek B §9 |
| 1.3 | Testsiz parçalara yeni test | Ek B §14'teki 1–12. maddeler (çekirdek, CLI, `mech`, `analysis`) için ≥ 12 yeni test | Ek B §14 |
| 1.4 | Regresyon | Sentetik H-001 (8 alt vaka) + S-001 (10 alt vaka): 18/18 beklenenle aynı; "hep ENGEL" / "hep GEÇTİ" sahte kontroller %100 kalır | ölçü: eski `test_regresyon` |
| 1.5 | Çekirdek temizliği | Yasak sözcük 0; import-linter ihlali 0; CLI'da katalog dışı Türkçe dize 0 | §3.1 |
| 1.6 | Şemalar | Faz 1 alt kümesi (11 şema: `schemas/README.md` faz notu) kesinleşir; örnek ve bozuk örnek denetimi temiz. Diğer şemalar fazlarında kesinleşir | `schemas/` |
| 1.7 | Taşıma | S-001 ve sentetik H-001: V1–V8 geçer; BAG-PLU-01 kuru çalıştırması baş mühendisin makinesinde V1–V8 geçer | §14 |
| 1.8 | Bilinen hatalar | İki eski hata (ilk ad yetkisi, `baski` KeyError) v1'de testle kapalı; onay imzası (APPROVAL-02) testli | §15, §4.6 |
| 1.9 | Boyut bütçesi (ikinci sistem önlemi) | `src/` + `packages/` Python satırı ≤ 6 560. Hesap: eski çekirdek 5 921 + CLI 451 = 6 372; taşınmayan `gecis.py` 406 düşülünce 5 966; bunun 1,10 katı (KM-23) | ölçü: `wc -l`, `d26af89`; çarpan öneri |
| 1.10 | Çekirdek testleri OCCT'siz | `tests/core` OCCT kurulu değilken ≤ 60 s'de geçer | öneri |
| 1.11 | Eklenti iskeleti | `claude plugin validate` hatasız; `--plugin-dir` ile yüklenince `claude plugin list` eklentiyi gösterir; kanca birim testleri geçer. `PreToolUse` engel listesi için 5 negatif test (kolaylık katmanı; güvence imzadadır) | öneri (T-01 sonrası; onay bekliyor) |

### Faz 2 — Panel kokpit, tanımlama, politika, akış, standart haritası

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 2.1 | A1–A12 (§5.8; A10 Faz 4'te) | hepsi. Faz 2'de eklentiye MCP sunucusu, monitor (`mekanik watch`) ve gelen kutusu eklenir (`mekanik watch` CLI komutu Faz 1'de eski gözcünün karşılığı olarak gelir, monitor bağlaması Faz 2'de); başsız kip (API anahtarı) burada gelir |
| 2.2 | C1–C6 (§7.2): çekirdek iş türü ağaçları + `print3d.basics` ile | hepsi |
| 2.3 | D1–D6 (§8.3) | hepsi |
| 2.4 | E1–E5 (§9.4) | hepsi |
| 2.5 | F1 (30/30), F3, F5'in G4/G5 şartı, F8 (§10.11) | hepsi |
| 2.6 | Eski panel e2e testleri (17) yeni ön yüzde | 17/17 |
| 2.7 | EN katalog kapsamı (panel + CLI) | %100 anahtar; eksik anahtar 0 |
| 2.8 | Eski panelden yeni panele geçiş | Eşitlik kontrol listesi = Ek B §4 (uç noktalar) ve §5 (ekranlar) satırları: %100 karşılanır. Eski panelin kapatılması baş mühendis kararı |
| 2.9 | Boyut bütçesi | Panel arka ucu ≤ 1 845 satır (eski 1 677 × 1,10); `panel-ui/` TS+CSS ≤ 3 280 satır (eski 2 189 × 1,5; yeni ekranlar için pay); çekirdeğe eklenen tanımlama, politika ve akış ≤ 3 000 satır (öneri) |

### Faz 3 — Alan paketleri ve CAD içe alma/değişiklik

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 3.1 | B1–B8 (§6.6) | hepsi |
| 3.2 | `molding` analizcileri: cevabı bilinen 5 sentetik parça | Sıfır çıkma açılı yüz sayısı, negatif açılı bölge sayısı, en ince et (±%2) ve izdüşüm alanı (±%1) beklenenle uyumlu (öneri) |
| 3.3 | Kritik hesapta bağımsızlık | Aynı formül yapısını ve aynı türetilmiş girdiyi paylaşan iki şablon CALC-03'te "bağımsız" sayılmaz (negatif test). Kapama kuvvetinin ikinci yöntemi ölçüm olarak işaretlidir; ölçüm gelene kadar kart açık kalır (test) |
| 3.4 | `print3d` yeni kontroller (E-04, E-05, E-41, E-35) | Her biri için geçen ve kalan regresyon alt vakası |
| 3.5 | Analiz aracı kayıtları | Paketlerdeki her analiz aracının geçerlilik alanı kaydı var (%100); alan dışı sonuç kanıt olamaz (test) |
| 3.6 | Eklenti API'si | `molding` yalnız genel API'yle yazılır; çekirdekte ona özel kod 0 satır. API v1 bu fazın sonunda dondurulur |
| 3.7 | Pilot | Her paket için baş mühendisin bir gerçek işi; kapıdan sonra bulunan her hata ≤ 7 günde regresyon vakası |
| 3.8 | Boyut bütçesi | Her yeni paket ≤ 2 500 satır; `mech` içe alma/işlem listesi eki ≤ 2 500 satır (öneri) |

### Faz 4 — Kurulum, belgeler, örnek proje, temiz makine, yayın hazırlığı

| # | Kabul ölçütü | Eşik |
| --- | --- | --- |
| 4.1 | K1–K5 (§13.3) ve A10 | hepsi; eklenti marketplace'ten (repo) kurulur |
| 4.2 | Belgeler ve kataloglar TR+EN | Her CLI komutu, her paket, her katkı noktası belgeli (%100). Paket soru ağaçlarının ve katalogların EN anahtarları %100 (KM-53) |
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
| FreeCAD, Elmer FEM | LGPL-2.1-or-later | uyumlu | Ayrı program. Elmer için yalnız incelenen çekirdek dosyalar LGPL-2.1+ (Araştırma D); Araştırma C bileşen ayrımını belirsiz bulmuştu |
| OrcaSlicer, PrusaSlicer, CuraEngine | AGPL-3.0 | uyumlu | Ayrı program; kullanıcı kurar |
| CalculiX (ccx), git | GPL-2.0-only (CalculiX için `ikincil_kaynak`: kaynak başlığı okunamadı, ihtiyatla "only") | **yalnız ayrı program olarak** | Komut satırıyla çağrılır |
| Claude Code CLI | Tescilli ("© Anthropic PBC. All rights reserved") | **yalnız ayrı program olarak** | Kullanıcı kurar; repoya ya da paketlere konmaz |
| claude-agent-sdk (Python) | MIT | uyumlu (koşullu) | Platform tekerlekleri tescilli CLI'yi içerir: yeniden dağıtılmaz |
| mekanik eklentisi (skill, ajan, kanca, monitor, MCP dosyaları) | AGPL-3.0-or-later (repo lisansı, T-11) | uyumlu (kendi kodumuz) | Kullanıcının Claude Code'una yüklenir; Claude Code ayrı ve tescilli program kalır, birlikte dağıtılmaz. Eklentinin tescilli barındırıcıyla ilişkisi (kanca ve MCP süreçleri ayrı süreçtir, skill metni veridir) Araştırma D'de incelenmedi: yorum |
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
| Boyut bütçesi | 1.9, 2.9 ve 3.8: `src/` + `packages/` + `panel-ui/` faz başına ölçülür. CI her commit'te ölçer ve aşımda uyarır |
| Büyük patlama yok | Eski sistem çalışır. v1 gerçek çalışmaları Faz 2'de devralır: CLI ve panel birlikte, eşitlik testleri geçince. Faz 1'de v1 yalnız sentetik vakalarda ve kuru taşımada kullanılır |
| Eklenti API'si mevcut koddan çıkarılır, önceden tasarlanıp şişirilmez | `mech`, `print3d` ve `analysis` eski koddan gelir; API ancak `molding` (ilk yeni paket) yazıldıktan sonra dondurulur (3.6) |
| Zaman kutusu | Her fazın süresi Faz 1 başında baş mühendisle yazılır; %50 aşımda (öneri) kapsam kesme kararı (baş mühendis) |
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
| Onayın ajan tarafından sahtelenmesi (aynı OS kullanıcısı) | DUR atlanır; "işi yapan onaylamaz" bozulur | İmzalı onay + APPROVAL-02. Eklenti kipinde insan varlığı isteyen imza: donanım anahtarı, kullanım başına onay ya da onay başına parola (T-17, §5.4). Başsız kipte ek olarak ajan yalıtımı ve ortam temizliği; en güçlüsü ayrı Linux kullanıcısı (T-16) |
| Çalışma klasöründeki `.claude/` ve `.mcp.json` içeriğinin ajanla çalışması | Yabancı kanca ya da MCP sunucusu çalışır | Başlamadan önce üretilen içerikle karşılaştırma; farkta DUR (§5.4) |
| Kurum verisinin model sağlayıcıya gitmesi | Gizlilik ve Hold ihlali | Kurum başına `data_transfer.model_provider_allowed` zorunlu; `false` ise panel oturum açmaz, `UserPromptSubmit` kancası istemi engeller, `PreToolUse` kancası çalışmanın dosyalarına erişimi reddeder; başsız kip başlamaz (§5.4–5.5). Kalan risk: eklenti kapatılıp oturum elle açılırsa |
| Eklenti biçiminin ya da monitor/kanca davranışının değişmesi (monitor anahtarı `experimental`) | Talimat iletimi ya da kanca bozulur | Eklenti bildiriminde Claude Code sürümü için alan yok; desteklenen aralık `mekanik doctor` ve `SessionStart` kancasıyla denetlenir. Kanca ve monitor için kayıtlı olaylarla testler; monitor çalışmazsa kancalarla tur sınırında iletim |
| Channels'ın araştırma önizlemesinde kalması | Doğrudan ileti yolu yok | Monitor + kanca yolu kullanılır; channels yalnız izin listesi açılırsa |
| Eklentinin bağlam maliyeti | Kullanıcının kullanım sınırı erir | Kısa açıklamalar; A11 (≤ 1 500 token/tur) ölçülür |
| Ubuntu masaüstü uygulamasının beta olması | Terminalsiz kullanım aksar | VS Code ve terminal yedek yüzeyler; panel kokpit olarak bağımsız |
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
| G-01 | Python paketi ve komut adı `mekanik`; yapılandırma `~/.config/mekanik/` | Baş mühendis 5 ad önerisini beklemeden `mekanik` reposunu açıp orada çalışılmasını istedi. Bu yüzden öneri listesi yapılmadı (KM-39). PyPI'de `mekanik` boş (ölçü: `pypi.org/pypi/mekanik/json` → 404, 2026-11-06). GitHub'da aynı adlı küçük, ilgisiz depolar var. Marka araştırması yalnız bu iki kaynakla yapıldı: kısmi; yayından önce tamamlanır (Faz 4) |
| G-02 | Faz 0 belgesi (kalite incelemesi ve kapanışları dahil) `main`'de; Faz 1'den itibaren değişiklikler dal + PR ile | İlk push baş mühendis yetkisiyle `main`'e yapıldı (§20.3); Faz 0 tek iş paketi |
| G-03 | Veri dosyaları YAML; kayıtlar JSON/JSONL; şemalar JSON Schema 2020-12, `urn:mekanik:schema:v1:*` | İnsan okur (YAML), makine yazar (JSON); eski sistemle süreklilik |
| G-04 | Sıralı değerler İngilizce; arayüzde TR etiket katalogdan (ör. `text_in_hand` = metin elde) | Kesin karar 1 |
| G-05 | Mekanik CAD (OCCT, CadQuery, geçme, mekanik kontroller) `mech` paketinde | Çekirdek alan bilmez; Ek A önerisi; çekirdek testleri OCCT'siz |
| G-06 | Faz 1'de CadQuery 2.8 + OCP 7.9.3; build123d/OCP 8.0 Faz 3 başında yeniden değerlendirilir | İki OCP aynı ortamda kurulamaz (Araştırma B); eski modeller CadQuery |
| G-07 | Süreç (G0–G5, A/B/C, risk soruları) `stdlib/process/default@1.yaml` verisi; davranış el kitabı 0.2 ile aynı | Çekirdek belirli bir süreci kodda taşımaz |
| G-08 | (Kaldırıldı.) Dal ve etiket adları İngilizce (§3.4) | Kesin karardan sapma geçici karar olamaz (KM-06); eski adları korumak T-15 |
| G-09 | "Baskı isteği" çekirdekte genel `release` (baskı/üretim isteği); paket genişletir | Kalıp ve sac işinde de aynı DUR gerekir |
| G-10 | (T-01 kararıyla değişti.) Birincil: Claude Code eklentisi (§5.4). İsteğe bağlı başsız kip: Claude Code CLI headless (stream-json), yalnız API anahtarıyla; Agent SDK ikinci başsız adaptör | Araştırma A §4a; baş mühendis kararı |
| G-11 | Kalite mühendisi anlama özeti onayından önce de çalışır | Tasarım başlamadan hatayı yakalamak |
| G-12 | Panel ön yüzü Vite + TypeScript, çerçevesiz; three-cad-viewer; SSE | Eski panelle süreklilik; ikinci sistem önlemi |
| G-13 | Panel varsayılan 127.0.0.1; uzaktan erişim platform adaptörü | Çekirdek Tailscale bilmez |
| G-14 | Taşıma ayrı dalda (`<code>/work/v1-migration`); eski dallara dokunulmaz; Faz 1'de yalnız kuru çalıştırma, gerçek geçiş Faz 2'de | Eski sistem çalışmaya devam eder; hiçbir çalışma panelsiz kalmaz |
| G-15 | Taramadan türetilen ölçünün belirsizliği alet kaydından; telefon LiDAR'ı için örnek ayar cm sınıfı alt sınır | Araştırma B: ±1 cm sınıfı (ikincil kaynak); referans parçayla doğrulanana kadar varsayım |
| G-16 | PyMeshLab (GPL-3.0) uyumlu ama varsayılan bağımlılık değil; trimesh + Open3D yeter | Bağımlılık hafifliği |
| G-17 | Model ve hesap kodunda izin listesi dışı sayı denetimi (SOURCE-02), Faz 2 | "Kaynaksız sayı yok, kodda da" kuralının makine denetimi |
| G-18 | Analiz aracı kayıtları ve NASA-STD-7009B uyarlama kaydı standart kütüphanesinde | §10.3–10.4 |
| G-19 | Belgeler TR; dosya adları EN; EN belge çevirisi Faz 4 | Kesin karar 1 |
| G-20 | Faz 0 için 7 ek şema: `agent-run`, `stream-event`, `intake-summary` (A, C, E parçalarının veri şeması); `approval`, `error-record`, `quality-review` (kalite bulguları KM-04, KM-12, KM-20) | İstenen 13 şemanın kuralları tek başına zorlanamıyordu |
| G-21 | Karar seviyeleri: yalnız DUR ve geçici karar; "inceleme bekliyor" kalkar. Geçici kararda dal yalnız modeli ya da bağımlı parametreleri değiştirenlerde; açık karar sınırı yalnız dallı kararları sayar | Faz 0 talimatı 2-D; KM-02 |
| G-22 | İş türleri paketlerden gelir; çekirdekte `fit`/`mold` gibi alan adı yok (`critical: interface`, `critical_dimension`) | Kesin karar: çekirdek alan bilmez; KM-05 |

### 20.2 Baş mühendisin kararları

Aşağıdaki tablo Faz 0'da açılan kararlardır. Baş mühendis 2026-11-06 07:20 UTC'de hepsini karara bağladı. Kayıt, uygulanış ve T-01'den doğan yeni kararlar (T-17, T-18) §20.4'tedir.

| No | Karar | Neden senin kararın | Öneri |
| --- | --- | --- | --- |
| T-01 | Ajan kimlik doğrulama varsayılanı: abonelik (CLI girişi) mi, API anahtarı mı | Maliyet etkisi; ayrıca şart yorumu belirsiz (§5.3) | Kişisel kullanımda abonelik (Claude Code CLI, kendi girişin). Bunun şartlara uygunluğu yorumdur; belirsiz olmayan yol API anahtarıdır. API anahtarı seçenek olarak kalır; seçilirse bütçe sınırı zorunlu. İstersen Anthropic'e sorulabilir |
| T-02 | "öneri" etiketli bütün kabul ölçütü eşikleri | Kabul ölçütü baş mühendisin | Toplu onay ya da tek tek değişiklik |
| T-03 | Grafik işler (katalog, etiket) v1 dışında, sonra paket | Kapsam | Dışarıda |
| T-04 | (Kaldırıldı: faz planında belirli, §17 Faz 1 kapsamı; KM-51) | — | — |
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
| T-15 | Dal ve etiket adları: v1'de İngilizce (`/main`, `/work/`, `/decision/`, `-release-`) mi, eski Türkçe adlar korunsun mu | Kesin karar 1'den sapma yalnız senin kararın | İngilizce; taşınan çalışmaların eski etiketleri geçmiş olarak kalır |
| T-16 | Ajan yalıtımı: Claude Code sandbox mı, ayrı Linux kullanıcısı mı (onay sahteciliğine karşı; §4.6) | Ayrı kullanıcı sudo ve sistem ayarı ister (Hold) | Varsayılan sandbox; senin makinende ayrı kullanıcı (komutları ben yazarım, sen çalıştırırsın) |

### 20.3 Faz 0'da baş mühendis yetkisiyle yapılanlar

Hold kapsamındaki işlemler ve dayandıkları talimat (bu oturumdaki iletilerden, birebir):

| İşlem | Talimat | Kayıt |
| --- | --- | --- |
| `mekanik` reposuna ilk push (`main`, commit `847d26a`) | "Ben adı seçince özel (private) bir GitHub reposu aç … Repo oluşturma ve ilk push için onayım var; yalnız bu repo için." Repoyu baş mühendis kendisi açtı: "mekanik adında repo açtım ve ekldim orada çalışalım" | `git log` |
| Eski `surec` reposunda `.claude/settings.json`: "ask" listesinden WebFetch, `curl`, `wget`, `gh`, `git push` kurallarının çıkarılması (commit `f1e655c`, yalnız oturum dalı) | "Bu dosyayı düzenleme yetkisini bu iş için veriyorum: 'ask' listesinden şunları çıkar: WebFetch, Bash(curl *), Bash(wget *), Bash(gh *), Bash(git push), Bash(git push *). 'deny' listesine dokunma. … Değişikliği commit et ve push et." | `git -C surec show f1e655c`; kalite bulgusu KM-01 bu kaydın belgede eksik olduğunu gösterdi |
| Bulut oturumu için kişisel "mekanik" ortamı (yalnız araştırma sitelerine ağ izni) | İnternet sorusuna cevap: "Evet, hepsi". Ağ ayarı değişikliği ayrıca araçta onay penceresiyle baş mühendise soruldu ve onaylandı | Bu oturumun ortam ayarı. Kalsın mı: özet (d) |

### 20.4 Karar kaydı (baş mühendis, 2026-11-06 07:20 UTC)

Baş mühendisin iletisi (birebir): "t01 bunu bir skill bir kütüphane gibi entegre edebilirsek önreğin şu an claude için kişiler bu repoyu kendi claude ajanlarına tanıttıklarında lokalde açabilsinler / diğer her şeyi onaylıyorum".

Saat bu oturumun sistem saatinden (`date '+%F %H:%M'`, UTC) iletinin işlendiği anda alındı. Kayıt iki sütunu ayırır: baş mühendisin söylediği ve proje mühendisinin onu nasıl uyguladığı. İkinci sütundaki her şey, baş mühendis onaylayana kadar öneridir (kalite bulgusu KM2-4).

| No | Baş mühendisin kararı | Proje mühendisinin uygulaması (onay bekliyor olanlar işaretli) |
| --- | --- | --- |
| T-01 | mekanik "bir skill, bir kütüphane gibi" entegre edilsin; kişiler repoyu kendi Claude ajanlarına tanıtıp yerelde açabilsin. İleti koşulludur ("edebilirsek"); yapılabilirlik aşağıda | Yapılabilir, sınırlarıyla: Claude Code eklentisi (skill, alt ajan, kanca, monitor, MCP) + Python kütüphanesi; repo = marketplace; repo kökünde ayar ve yönerge (§5.1, §5.4, §13.2, Araştırma A §4a). **Onay bekleyen uygulama kararları:** (i) eklenti kipi birincil; (ii) isteğe bağlı başsız kip yalnız API anahtarı ya da bulut sağlayıcısıyla, abonelikle değil. Maliyet etkisi: başsız kipi seçen kullanıcı token başına öder. (iii) Agent SDK ikinci başsız adaptör. **Açık yapılabilirlik noktaları (Faz 1–2'de doğrulanır):** onay imzasının eklenti kipinde insan varlığıyla kurulması (T-17); masaüstü ve VS Code'da oturumu klasörde açma ve monitor'ün orada çalışması; yumuşak durdurma |
| T-02 | "öneri" etiketli eşikler onaylandı | Kapsam: 07:20 UTC'den önce belgede bulunan eşikler. Sonra yazılanlar (A1, A2, A5, A6, A8, A10, A11, A12, 1.11) "öneri (T-01 sonrası; onay bekliyor)" diye işaretli |
| T-03 | Onay: grafik işler v1 dışında | §19.3 |
| T-04 | — (faz planına katılmıştı) | — |
| T-05 | Onay: yeni el kitabı taslağı Faz 1 başında | Ö-01…Ö-28 ve KOSE-01 kurala dönüşür. El kitabı metni yine baş mühendis onayıyla kesinleşir (Hold) |
| T-06 | Onay: politika sayıları | Pencere 10 karar, eşik %20, en çok 5 dallı geçici karar, aşama başına en çok 5 "şimdi" sorusu. Kaynak: `decision` (baş mühendis, 2026-11-06) |
| T-07 | Onay: maliyet eşiği kurum başına | Değer kurulum sihirbazında kurum başına sorulur (§13.2); girilene kadar risk sorusu baş mühendise gider |
| T-08 | Onay: paralı standart alımı ihtiyaç doğunca kartla | §10.8 |
| T-09 | Onay: kapalı ajan oturumu kendiliğinden başlatılmaz | §5.3 (gerekçe), §5.6 (gözcü/monitor) |
| T-10 | Onay: yayın Faz 4 sonunda, ayrı karar | §17 |
| T-11 | Onay: AGPL-3.0-or-later | Faz 1'in ilk commit'inde `LICENSE` ve SPDX başlıkları |
| T-12 | Onay: 7009B uyarlaması (YZ incelemesi en çok seviye 2) | §10.4, uyarlama kaydı |
| T-13 | Onay: yalnız etkin çalışmalar taşınır | Liste Faz 1'de baş mühendisin makinesinde kurum repolarından çıkarılır |
| T-14 | Onay: Ubuntu 24.04 + 26.04 | Baş mühendisin sürümü `mekanik doctor` çıktısından okunur |
| T-15 | Onay: dal ve etiket adları İngilizce | §3.4, şemalar |
| T-16 | Onay: ajan yalıtımı (sandbox; baş mühendisin makinesinde ayrı Linux kullanıcısı) | T-01'den sonra yalnız başsız kipte uygulanabilir. Eklenti kipinde yerine T-17 gelir (onay bekliyor) |
| G-01…G-22 | Onay: geçici kararlar | G-10 karardan sonra T-01'e göre değiştirildi; değişen metin onay bekliyor |

**T-01'den doğan yeni açık kararlar** (onay bekliyor):

| No | Karar | Neden senin kararın | Öneri |
| --- | --- | --- | --- |
| T-17 | Eklenti kipinde onay imzası: (a) FIDO2 donanım anahtarı (dokunma ister), (b) `ssh-add -c` ile kullanım başına onay, (c) panelde onay başına parola | (a) satın alma ister (maliyet); güvenlik düzeyi farklı | Başlangıçta (b) ya da (c), ücretsiz; istersen (a) |
| T-18 | Kesin karar 6'nın uygulanışı: eklenti kipinde ajanla konuşma kullanıcının Claude Code penceresinde, panel durum/onay/talimat/dosya kokpiti | Kesin kararın uygulanışını değiştirir | Kabul; paneli tek pencerede isteyen başsız kipi kullanır |

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

İnceleme 2026-11-06'da, commit `847d26a` üzerinde yapıldı. Kalite mühendisi temiz bağlamla çalıştı (sohbet özeti verilmedi; yalnız el kitabı, CLAUDE.md, Faz 0 talimatı ve dosya yolları) ve tek tur inceledi. Bulguları **11 YÜKSEK, 28 ORTA, 17 DÜŞÜK**, toplam 56. Bulgular aşağıda olduğu gibi duruyor; satır numaraları inceleme anındaki dosyaya göredir.

Kapanışları proje mühendisi yazdı. İşi yapan kendi işini onaylamaz: kapanışların doğruluğu bir sonraki kalite turunda ve baş mühendis incelemesinde denetlenir.

**Özet durum.** YÜKSEK 11/11 kapandı. KM-04 tasarımda kapandı; yöntemi T-16'ya ve Faz 1 doğrulamasına bağlı. KM-06 T-15'e bağlandı. ORTA 27 kapandı, 1 açıklandı (KM-39). DÜŞÜK 15 kapandı, 1 kısmen (KM-45), 1 açık (KM-46).

### 22.1 Bulgular ve kapanışlar

| No | Bulgu (kalite mühendisi, olduğu gibi) | Kapanış (proje mühendisi) |
| --- | --- | --- |
| KM-01 | [YÜKSEK] architecture.md:11 — Belge eski sistemin "yalnız okundu" dediğini yazıyor, ama aynı oturumda (Claude-Session aynı) eski repoya `f1e655c` commit'i atılmış (2026-11-06 06:10) ve `origin/claude/surec-v1-architecture-qphgcj` dalına gönderilmiş. Commit `.claude/settings.json`'dan WebFetch, curl, wget, gh ve git push "ask" kurallarını kaldırıyor. Commit mesajı "baş mühendisin bu iş için verdiği yetkiyle" diyor; belgede ve kayıtta bu yetkinin karşılığı yok (doğrulanmadı) — kabul ölçütü 0 ("Eski surec reposunu yalnız oku; ona yazma"), CLAUDE.md Hold (sistem ayarları, ilk push) — kanıt: `git -C /home/user/surec log -1 f1e655c`, `git status -sb` uzak dalla eşit. | Kapandı. Belge başlığı ve §20.3'e yetki kaydı (baş mühendisin birebir talimatı) eklendi. Commit yalnız oturum dalında, `main` değişmedi. |
| KM-02 | [YÜKSEK] architecture.md:828 — "Geri kalan her şey geçici karardır" kuralı ile `review` seviyesi birlikte duruyor (architecture.md:338; decision.schema.json:16; card `level`). Şema, DUR dışı bir kararı `mode: review` ile görselsiz, alternatifsiz ve itiraz penceresiz kabul ediyor; hangi kararın `review`, hangisinin `provisional` olacağı tanımsız. Tersine, her karar geçici olursa her biri ayrı dal ve alternatif ister ve en çok 5 açık geçici karar sınırı (architecture.md:843) işi tıkar; tel kafesler zaten 7 açık geçici karar gösteriyor (wireframes/intake.html:49, flow.html:49) — kabul ölçütü 2-D ("Bunların dışındaki her şey geçici karar olur: görseli ve gerekçesiyle akışa düşer") — kanıt: sınama "DUR dışı karar 'review' kipinde, görselsiz, alternatifsiz" → GEÇER. | Kapandı. `review` kipi kalktı (şema, §2.3, §4.4, §8.1); geçici kararda dal yalnız model/bağımlı parametre değişiminde; sınır yalnız dallı kararları sayar. Negatif test eklendi. |
| KM-03 | [YÜKSEK] wireframes/intake.html:86 — DUR kategorisindeki soru varsayımla geçiyor: yıllık adet §11.7'de ve question-tree örneğinde `chief_only_info` DUR'u, ama tel kafes "Cevap gelmezse 5 000 adet/yıl varsayılır … İş durmaz" yazıyor ve "Bilmiyorum — varsayımla sürsün" düğmesi sunuyor (intake.html:91); akışta aynı soru aşama sonu paketine ertelenmiş (flow.html:173) ve gün sonu riskinde "varsayım girdili" geçiyor; soru ağacı panelinde DUR işareti yalnız "Güvenlik parçası mı?" sorusunda — kesin karar 1 madde 7 ("yalnız onda olan bilgi"), C6 ("DUR kategorisindeki soru varsayılanla geçer mi: hayır"), architecture.md:783 — kanıt: architecture.md:1221 "yıllık adet (DUR: yalnız onda olan bilgi)", schemas/v1/examples/question-tree.json `annual_quantity.stop_category = chief_only_info`. | Kapandı. Tel kafeste DUR sorusu varsayımla geçmez; şema DUR düğümünde varsayılan değeri ve `opens_card: false`'u reddeder (negatif test). |
| KM-04 | [YÜKSEK] architecture.md:366 — Onayın sahtelenmesine karşı tasarım yok: baş mühendis kimliği "ad + e-posta tam eşitliği" ile tanınıyor ve bu değerler ajanın okuyabildiği `~/.config/mekanik/config.yaml`'da; ajan aynı OS kullanıcısıyla Bash çalıştırıyor, `git -c user.name/user.email` ya da `GIT_AUTHOR_*` ile o kimlikle commit atabilir, yerel panele (127.0.0.1) HTTP isteği gönderebilir, TTY şartını `script`/pty ile aşabilir. İmzalı commit/etiket, ajanın okuyamadığı bir sır ya da OS ayrımı önerilmiyor; §19.2 risk tablosunda bu tehdit yok (architecture.md:1634) — el kitabı §1 ilke 4 ve 6 ("Geri dönüşsüz adımı yalnız baş mühendis onaylar", "İşi yapan kendi işini onaylamaz"), kesin karar 1 madde 7 (DUR'un zorlanması) — kanıt: architecture.md:368-370; config.schema.json `identities.chief` düz metin; eski sistemde de imza yok (`surec:cekirdek/surec_cekirdek/akis.py:456` `tag -a`, `-s` değil). Uygulama olmadığı için istismar edilebilirlik doğrulanmadı; tasarım boşluğu kesindir. | Tasarımda kapandı: imzalı onay + APPROVAL-02 + ajan yalıtımı + ortam temizliği + CSRF (§4.6, §19.2), `approval` şeması. Yalıtım yöntemi T-16. Claude Code sandbox özelliği bu oturumda doğrulanmadı (Faz 1). |
| KM-05 | [YÜKSEK] architecture.md:752 — Çekirdek alan adlarını taşıyor: "Çekirdek beş türü veri olarak taşır" (`mold_for_part`, `scan_to_model` dahil); ortak şemada `quantity.critical` değeri `fit` (common.schema.json:102); atölye ayarı şemasında alet geçerliliği `critical_fit` (config.schema.json:193); çekirdek kontrolü UNCERT-01 "kritik geçme"ye bakıyor (architecture.md:384); kart şeması `fit`, `flex`'i çekirdek türü sayıyor (card.schema.json:18), oysa §4.3 bunları `mech:fit`, `mech:flex` paket türü diye yazıyor. İş türü örneği `mold_for_part`'ı `provided_by: molding` veriyor (examples/work-type.json:7), ana belgeyle çelişiyor. Belgenin kendi temizlik testi ("mold" yasak) 1.5 ölçütünde kalır — kabul ölçütü 2 ("Çekirdek hiçbir kişiyi, makineyi, kurumu ya da alanı adıyla tanımamalı"), architecture.md:181 — kanıt: yukarıdaki satırlar. | Kapandı. İş türleri paketlerden gelir (§7.1); `critical: interface`, `critical_dimension`; kart şemasında `fit/flex` çekirdek türü değil; temizlik testi tam sözcük. |
| KM-06 | [YÜKSEK] architecture.md:1673 — G-08 Türkçe dal ve etiket adlarını (`<kod>/ana`, `/is/`, `/karar/`, `-baski-`) geçici karar olarak koruyor ve bunlar şema desenlerine (koda) girmiş: decision.schema.json:29 `/karar/`, work.schema.json:89 `/ana$`. Kesin karar tartışılmaz; ondan sapma proje mühendisinin geçici kararı olamaz, §20.2'ye (baş mühendis) ait — kesin karar 1 madde 1 ("Kod, şema, komut ve dosya adları İngilizce"), kabul 2-D (standarttan/kurallardan sapma DUR) — kanıt: G-08 gerekçesi "itiraz edilirse main/work/decision/-release- olur". | Kapandı → T-15. Şema desenleri İngilizce (`/main`, `/work/`, `/decision/`, `-release-`); G-08 kaldırıldı. |
| KM-07 | [YÜKSEK] wireframes/project-new.html:140 — Tel kafeslerde Türkçe komut, seçenek ve dosya adları var ve ana belgeyle çelişiyor: `mekanik ac --kurum --proje --ad --tur kalip --paket` (ana belge: `mekanik work new`, §5.1/§4.11); `~/.config/mekanik/ayar.toml` (project-new.html:59; ana belge YAML ve `config.yaml`, §3.3/G-03); `model/islemler.yaml`, `kalip/yerlesim.step` (card.html:60; ana belge `model/ops.yaml`); `kararlar.yaml`, `onaylar.yaml` (card.html:87; ana belge `decisions.yaml`, `approvals.yaml`); `kayit/gunluk` (flow.html:188), `kayit/kaynaklar/` (stdmap.html:69; ana belge `records/`); `kontrol/delik_araligi.py` (card.html:139); paket `mekanik-temel` (project-new.html:110) — kesin karar 1 madde 1 — kanıt: grep sonuçları yukarıdaki satırlarda. | Kapandı. Tel kafeslerde komut, dosya, dal ve paket adları ana belgeyle aynı (`mekanik work new`, `config.yaml`, `model/ops.yaml`, `decisions.yaml`, `records/…`, `mekanik-mech/print3d/analysis`). |
| KM-08 | [YÜKSEK] architecture.md:559 — "Kişisel kullanımda abonelik ancak CLI yoluyla şartlara uygun kullanılabilir" kaynağından fazlasını söylüyor: aynı ekin alıntı 7'si abonelik sınırlarını "ordinary, individual usage of Claude Code and the Agent SDK" diye anıyor (abonelikle SDK kullanımı öngörülüyor); alıntı 4 "Developers building products or services … should use API key authentication" mekanik'in kendisini de (CLI üstünden çalışsa bile) kapsayabilir. Ayrım bir yorumdur, belge onu bulgu gibi yazıyor ve T-01 maliyet kararına gerekçe yapıyor (architecture.md:1691) — kabul 2-A (kaynak göster, şartlar açısından karşılaştır), F (kaynaksız iddia yok) — kanıt: research/a-agent-runtime.md:62, :65, :64 ("Unless previously approved"); karşılaştırma tablosu architecture.md:545 "abonelik üçüncü taraf üründe izinli değil". | Kapandı. §5.3 ve Araştırma A'da ayrım yorum olarak işaretlendi; alıntı 4 ve 7 yazıldı; T-01 gerekçesi belirsizliği taşıyor. |
| KM-09 | [YÜKSEK] architecture.md:692 — "**OCCT'de doğrudan 'yüzü taşı' API'si yok**" kesin dili kaynakta yok: Araştırma B tablosu "kılavuzlarda bulunamadı" diyor; başvuru kılavuzu (dev.opencascade.org refman) erişilemedi (K28–K32 `ikincil_kaynak`). Yokluk kanıtı değil, bulunamama — kabul 2-B ("Araştır ve dürüstçe yaz") — kanıt: research/b-cad.md:61 "OCCT'de ayrı bir 'yüzü taşı' API'si kılavuzlarda bulunamadı"; research/b-cad.md:22-23 erişim sorunları. (Araştırma B'nin kendi özeti, b-cad.md:212, aynı yükseltmeyi yapıyor.) | Kapandı. "Bulunamadı (yokluk kanıtlanmadı)" diliyle düzeltildi (§6.3, Araştırma B notu). |
| KM-10 | [YÜKSEK] architecture.md:670 — Yüz indeksinin "aynı çekirdek sürümünde ve aynı girdide belirlenimci" olduğu doğrulanmış bilgi gibi yazılmış; kaynakta bu "kaynak okumasından çıkarım; test edilmedi" ve üçüncü koşul "aynı okuma ve iyileştirme parametreleri" de var. Bu koşulu karşılayacak alan şemada yok: `model-oplist.base.import` yalnız `heal`, `unify_same_domain`, `tolerance` taşıyor, `additionalProperties: false` olduğundan `read.*` parametreleri kaydedilemiyor. Böylece "yeniden üretilebilir" iddiasının dayanağı eksik kalıyor — kabul 2-B ("izlenebilir, geri alınabilir, yeniden üretilebilir") — kanıt: research/b-cad.md:82, :70 ("Okuma parametrelerini işlem 0'ın kaydına yaz"); model-oplist.schema.json:22; sınama "oplist: okuma parametreleri kaydı" → KALIR. | Kapandı. §6.2'de üç koşul ve "çıkarım, test edilmedi"; `base.import.read_params` zorunlu (şema, örnek, negatif test). |
| KM-11 | [YÜKSEK] architecture.md:1220 — Kapama kuvvetinde "iki yöntem birbirini sınar" iddiası belgenin kendi bağımsızlık tanımına aykırı: `clamp_force_area` (F = p·A·k) ve `clamp_force_rule` (ton/inç² × A) aynı formül yapısında, aynı izdüşüm alanı girdisini kullanıyor ve ikisi de `level 1`. Ortak hata (yolluk alanı, göz sayısı, yanlış A) ikisinde de aynı çıkar. Faz 3 ölçütü 3.3 bu örneğe dayanıyor; şema örneği de aynı türden (`clamp_force_flowratio`) — kabul 2-F ("Kritik hesaplar iki bağımsız yöntemle"), architecture.md:967 ("farklı yöntem sınıfı ya da farklı araç ve farklı formül … Aynı formülün yeniden yazılması bağımsız sayılmaz") — kanıt: research/c-mold-print.md:68 (her iki kural da izdüşüm alanı × basınç türü katsayı); examples/calculation.json `cross_check.with = clamp_force_flowratio`. | Kapandı. §10.2 bağımsızlık tanımı (aynı yapı + aynı türetilmiş girdi sayılmaz); kalıpta ikinci yöntem pres ölçümü; ölçüt 3.3 ve hesap örneği güncellendi. |
| KM-12 | [ORTA] schemas/v1/card.schema.json:138 — Onay kaydı rolü zorlanmıyor: kart dizisinde `kind: approve` ve karar geçmişinde `event: approved` herhangi bir rolle (proje mühendisi, tekniker) geçiyor; onayların asıl yeri olan `approvals.yaml` için şema yok (17 şemada yok) — el kitabı §1 ilke 6, CLAUDE.md "İşi yapan kendi işini onaylamaz" — kanıt: sınamalar "kart dizisinde proje mühendisi 'approve'" → GEÇER, "karar geçmişinde tekniker 'approved'" → GEÇER (decision.schema.json:88). | Kapandı. `approval` şeması (rol sabit, imza zorunlu); kart dizisi ve karar geçmişinde onay olayları yalnız baş mühendis (negatif testler). |
| KM-13 | [ORTA] schemas/v1/card.schema.json:157 — Karar kartında ve karar kaydında "isteklere etkisi" (`requirement_effects`) zorunlu değil; eski sistem bunu zorunlu tutuyordu (B8, `hedef_etkisi`) — architecture.md:327 ("karar kartında 'isteklere etkisi' zorunlu"), Ek B §13 B8 — kanıt: sınamalar "karar kartı 'isteklere etkisi' olmadan" → GEÇER, "karar kaydı requirement_effects olmadan" → GEÇER. Eski davranışın gerilemesi. | Kapandı. `requirement_effects` karar kaydında ve karar kartında zorunlu; boş olmama DECISION-02. |
| KM-14 | [ORTA] schemas/v1/standard-item.schema.json:8 — Standart haritası maddesinde "neden burada", "test yöntemi" ve "kabul ölçütü (sayı + kaynak)" zorunlu değil; yalnız amaç, tür ve doğrulama durumu zorunlu — kabul 2-F ("her madde için amaç, neden burada, test yöntemi, kabul ölçütü, kanıt, doğrulama durumu ve tür"), architecture.md:1066 — kanıt: sınama "neden burada / test yöntemi / kabul ölçütü yok" → GEÇER. | Kapandı. Çalışma maddesinde `why_here`, `test_method`, `acceptance` zorunlu. |
| KM-15 | [ORTA] schemas/v1/card.schema.json:72 — Kapı kartının istek tablosunda ve istek kaydının `evaluation` alanında (requirement.schema.json:62) "karşılandı" durumu kanıtsız geçiyor; boş istek tablosu ve açık YÜKSEK = 3 olan kapı kartı da geçiyor. Standart maddesindeki tik için aynı kural şemada zorlanırken burada zorlanmıyor — kabul 2-F ("her istek için durum … kanıtın yeriyle"), architecture.md:1046 ("Durum kanıttan türetilir") — kanıt: sınamalar "kapı kartı: 'karşılandı' ama kanıt yok" → GEÇER, "boş istek tablosu, açık YÜKSEK=3" → GEÇER. | Kapandı. "met" kanıtsız olamaz (kart tablosu ve istek değerlendirmesi); kapı kartında tablo ≥ 1 satır; kapı/baskı kartında açık YÜKSEK = 0. |
| KM-16 | [ORTA] schemas/v1/calculation.schema.json:131 — Hesap şeması §10.3–10.4'ü taşımıyor: (a) geçerlilik yalnız `in_domain: true\|false\|null`; NASA'nın üç bölgesi (sınırlar / doğrulama alanı / geçerleme alanı) ve "yalnız doğrulama alanında" ya da "yalnız sınırlar içinde" placard durumları, aşım türü, miktarı ve etkisi temsil edilemiyor; (b) sonuçta belirsizlik ya da açık "belirsizlik tahmini yok" beyanı zorunlu değil (calculation.schema.json:77) — architecture.md:991-997 (beş durumlu tablo), architecture.md:1022 ("boş bırakmak hata"), kabul 2-F (geçerlilik alanı) — kanıt: sınama "sonuçlarda belirsizlik de 'tahmin yok' beyanı da yok" → GEÇER; examples/calculation.json sonuçlarında `uncertainty` yok. | Kapandı. `validity.zone` (5 değer) + `placard` (sınır türü, aşım, etki); sonuçta `uncertainty_note` zorunlu. |
| KM-17 | [ORTA] schemas/v1/provisional-decision.schema.json:15 — "En az bir alternatif" yalnız `provisional-decision` şemasında; iki şema da `kind: decision` taşıyor ve aynı `decisions.yaml`'da duruyor, hangi şemanın uygulanacağını belirleyen bir alan yok. `decision` şeması `mode: provisional` + tek seçeneği kabul ediyor — el kitabı §7 (geçici kararda en az bir alternatif), kabul 2-D — kanıt: sınama "geçici karar tek seçenekle, decision şemasıyla" → GEÇER. | Kapandı. Karar şemasında `mode: provisional` iken seçenek ≥ 2. |
| KM-18 | [ORTA] schemas/v1/config.schema.json:101 — Ana belgede adı geçen ayarlar şemada yok ve şema `additionalProperties: false` olduğundan reddediliyor: `policy.max_questions_per_stage` (architecture.md:784, T-06), çalışmanın standart kütüphanesi sürümünü sabitlemesi (architecture.md:1277; work.schema.json'da alan yok), dosya yükleme boyut sınırı (architecture.md:605), kontrol zaman aşımı (architecture.md:1194) — kabul 3.3 (şemalar), iç tutarlılık — kanıt: sınamalar "config.policy.max_questions_per_stage" → KALIR, "work.stdlib sürüm sabitleme" → KALIR. | Kapandı. `policy.max_questions_per_stage`, `panel.upload_limit`, `packages.check_timeout`, `work.stdlib` eklendi. |
| KM-19 | [ORTA] architecture.md:835 — Sınıflayıcı "`main_dimensions` olarak işaretli parametreyi" arıyor, ama parametrelerin şeması (`common#quantity`, `additionalProperties: false`) böyle bir işaret taşımıyor; işareti kimin koyacağı da yazılmamış (ekip koyarsa DUR kapsamını ekip belirler) — kesin karar 1 madde 7 (ana ölçüler DUR), el kitabı §1 ilke 3 ("Neyin önemli olduğunu kurallar belirler, modelin kanaati değil") — kanıt: common.schema.json `quantity` alanları: value, unit, source, formula, decided_by, uncertainty, critical, note. | Kapandı. `quantity.main_dimension`; ana ölçü tanımı ve "işareti ekip koyamaz" kuralı §8.1'de. |
| KM-20 | [ORTA] architecture.md:1054 — "Hata kaydı (8D) şemasında `regression_case` zorunlu" deniyor, ama 17 şemada hata kaydı şeması yok ve §10.9 kaydı Markdown dosyası olarak tanımlıyor (architecture.md:1111 `errors/H-nnn.md`); QUALITY-01 ve tikin dayandığı kalite incelemesi kaydı (`records/quality/*.yaml`) da şemasız — kabul 2-F ("Her hata bir regresyon testine dönüşür"), el kitabı §13 — kanıt: schemas/README.md dosya listesi. | Kapandı. `error-record` (regresyon vakası zorunlu) ve `quality-review` (kapanışta regresyon sorusu) şemaları. |
| KM-21 | [ORTA] architecture.md:432 — §4.11 "Ayrıntılı eşleme Ek B §3'tedir" diyor, ama Ek B farklı adlar ve farklı katman veriyor: `asama-bitir` → `stage finish` / Ek B `gate request` (appendix-b:124); `baski` → çekirdek `release request` (G-09) / Ek B `fdm print-request` "pkg_fdm komutu" (appendix-b:125); `karar` → `decide` / `decision open` (appendix-b:129); `panel` → `panel` / `panel serve` (appendix-b:137); `kapat`, `gec` → Ek B `work close`, `work attach`, ana belgede yok. Ek A ve Ek B modül adları (`core.flow`, `pkg_fdm`, `cad`, `AP:fdm`) §3.2'deki (`process/`, `print3d`, `mech`) adlarla da uyuşmuyor — iç tutarlılık; G-09 kararı — kanıt: belirtilen satırlar. | Kapandı. §4.11 bağlayıcı adlar; `kapat`/`gec` satırları; Ek A/B modül adı eşlemesi yazıldı. |
| KM-22 | [ORTA] architecture.md:1168 — `molding` kural kimlikleri ve sayısı üç yerde farklı: bildirimde 6 kontrol `MOLD-DRAFT-01 …` (RIB yok), §11.7'de 7 kontrol `DRAFT-01 … RIB-01 … QTY-01` (architecture.md:1219), §11.1 kuralı `<paket>:<KURAL>` (`print3d:BED-01`); tel kafeste "kontrol 11 · kural 24" (project-new.html:105, intake.html:118). Paket adları tel kafeste `mekanik-am`, `mekanik-machining`, `mekanik-temel`; belgede `print3d`, `mech` (machining paketi yok) — kabul 3.4 (eklenti arayüzü, sürümleme), iç tutarlılık — kanıt: belirtilen satırlar. | Kapandı. Belge içinde 7 kontrol, `molding:<KURAL>` biçimi; tel kafeste paket adları ve sayıları düzeltildi. Ek A/B'deki eski adlar envanter kaydı olarak bırakıldı (eşleme §4.11). |
| KM-23 | [ORTA] architecture.md:1528 — İkinci sistem önlemi olan boyut bütçesi yalnız `src/`'yi ölçüyor; eski 8 049 satırın en az ~1 600'ü `packages/`'a gidiyor ya da taşınmıyor (`kart_gorsel.py` 925, `gorsel.py` 146, `modelci.py` 74, `fea.py` 66 → mech/analysis; `gecis.py` 406 taşınmaz). Bütçe fiilen çekirdeğe ~%20 ek pay veriyor; `packages/`, `panel-ui/` ve Faz 2–3 için bütçe yok — kabul 3.9 (ikinci sistem etkisi önlemleri) — kanıt: `wc -l` eski repo; architecture.md:3.2 ağaç (`packages/` `src/` dışında). | Kapandı. Bütçe `src/` + `packages/` (Faz 1: 6 560), Faz 2 (2.9) ve Faz 3 (3.8) bütçeleri eklendi. |
| KM-24 | [ORTA] architecture.md:1525 — Faz 1'de "17 şema kesinleşir"; bunların yedisi Faz 2–3 özelliklerinin şemasıdır (intake-summary, stream-event, question-tree, work-type, model-oplist, standard-item, provisional-decision). Bu, §19.1'in "önceden tasarlanıp şişirilmez" önlemiyle ve Faz 1'in "yalnız eski sistemin yaptıkları" kuralıyla çelişiyor; Faz 1'e giren yeni davranışlar (i18n, alet kaydı, ad+e-posta kimliği, genel `release`, ölçümsüz gözlemin şemada hata olması) için "yeni özellik" tanımı yok — kabul 3.7 (Faz 1: yeni özellik yok), 3.9 — kanıt: architecture.md:1616. | Kapandı. Faz 1 şema alt kümesi (11) ve "yeni özellik" tanımı §17'de; sıkılaştırmalar Faz 1'de uyarı. |
| KM-25 | [ORTA] architecture.md:1615 — "v1 iş akışını devralır (CLI Faz 1, panel Faz 2)": eski panel v1 biçimini okuyamaz (Ek B §4 uç noktaları yeniden adlandırıyor), yeni kokpit Faz 2'de. Faz 1 sonunda v1'e geçen çalışmalar Faz 2'ye kadar panelsiz kalır ve onay yalnız TTY'den verilir; Faz 1'deki "panel arka ucu"nun bir tüketicisi yok — kesin karar 1 madde 6 ("Panel kokpittir"), kabul 0 ("Mevcut sistem, v1 aynı işleri yapana kadar çalışmaya devam eder") — kanıt: architecture.md:1505, :1512 (T-04). | Kapandı. Panel arka ucu Faz 2'ye; Faz 1'de taşıma yalnız kuru çalıştırma, gerçek geçiş Faz 2. |
| KM-26 | [ORTA] wireframes/stdmap.html:48 — Tel kafes güvence kurallarına aykırı örnekler gösteriyor: madde 2 "karşılandı" ve tikli, ama test yöntemindeki numune deneyi D-01 yalnız "planlandı"; madde 3 tikli, ama test yöntemindeki "ölçü raporu" G1'de var olamaz (stdmap.html:49); tik 11:10'da verilmiş, dayandığı H-03 akışta 13:40 ve 14:31'de yeniden koşmuş (kanıt sonradan değişmiş, tik düşmemiş); kapı kartında R-02 "karşılandı" 0,42 mm ile aynı özet `9c1e4b` (card.html:140), akışta aynı özet 0,47 mm. Tiki kimin koyduğu da belirsiz ("kalite mühendisi ✓ tik verdi", stdmap.html:74; el kitabı §4 kalite mühendisi karar vermez) — kabul 2-F ("Tik yalnız kanıtla"), architecture.md:361 ("Özet değişirse kanıt bayatlar") — kanıt: belirtilen satırlar; flow.html 13:40 ve 14:31 satırları. | Kapandı. Standart haritası tel kafesinde kanıtı planlı madde tiksiz; G1'de var olamayacak kanıt kaldırıldı; tik notu kuralla uyumlu. |
| KM-27 | [ORTA] wireframes/flow.html:96 — Ekip, kaburga 1,6 mm'yi 1,8 mm alt sınırın altında "UYARI kabul edildi" diyerek geçici kararla alıyor. Kural sınırından sapma DUR'dur ve UYARI'yı işi yapanın kabul etmesi dört göz ilkesine aykırı; §8.1 sınıflayıcısı yalnız "standart maddesinin kabul ölçütünü gevşetme"ye bakıyor, katalog sınırlarını kapsamıyor — kesin karar 1 madde 7 ("standarttan sapma"), el kitabı §7 (sapma soru tetikleyicisi) — kanıt: flow.html:96; architecture.md:838. | Kapandı. Sınıflayıcıya "kural sınırı dışındaki değer = sapma (DUR)" eklendi; tel kafeste satır DUR sapma kartına döndü. |
| KM-28 | [ORTA] wireframes/flow.html:120 — Tekniker modeli değiştiriyor ("Delikler büyütüldü: Ø6,0 → Ø6,4 (3 delik)"); model.html'de tekniker model notu açıyor (N-02, bu tür belgeye göre baş mühendisin notu) ve akışta kalite mühendisi "kontrol turu" yürütüyor — CLAUDE.md divan kuralı ("tekniker çizmez, seçmez, yorumlamaz"), architecture.md:116 — kanıt: flow.html:120; model.html N-02; Ek B "BM'nin model üstündeki notu N-nn kartı olur". | Kapandı. Tel kafeste model değişikliği tasarım mühendisinde, kontrol turu teknikerde, N-02 baş mühendisin notu. |
| KM-29 | [ORTA] wireframes/intake.html:123 — Tanımlama onaylanmamışken ("2 soru açık", "sürüm v2") çalışma G1'de görünüyor ve akışta tasarım işleri (kaburga, flanş öteleme) sürüyor; aynı saatte (14:32) flow.html:136 "Tanımlama onaylandı (G0) … anlama özeti v3" diyor. Tel kafes onayı G0 etiketiyle eşitliyor, ana belge onu G0'ın ön koşulu sayıyor (G0 ayrıca standart haritası ve kalite ister) — kabul 2-C ("Baş mühendis onaylamadan tasarım başlamaz"), C5, architecture.md:806 — kanıt: intake.html:104, :123, :160. | Kapandı. Tanımlama ekranı "onaydan önce anlık görüntü" (G0, 2026-11-05); akıştaki onay sırasıyla çelişmiyor. |
| KM-30 | [ORTA] wireframes/stdmap.html:47 — Gerçek mevzuatın doğrulama durumu yanlış verilmiş: GPSR (EU) 2023/988 ve REACH (stdmap.html:50) "metin elde" gösteriliyor; ana belge ve Araştırma D ikisini `ikincil_kaynak` veriyor (EUR-Lex bot engeli). REACH ve RoHS sınırları `standard:` etiketiyle yazılmış, doğrusu `regulation:` — kabul 2-F (doğrulama durumu), architecture.md:143 — kanıt: architecture.md:1089, :1091; research/d-nasa-regulation-licenses.md:243, :485. | Kapandı. GPSR ve REACH "ikincil kaynak"; REACH/RoHS sınırları `mevzuat:` etiketiyle. |
| KM-31 | [ORTA] architecture.md:516 — "bütün kaynaklar `metin_elde`" yanlış: Araştırma A, Max/Ultra API kredisi dipnotunu `ikincil_kaynak`, Python SDK tekerleğinin içeriğini `dogrulanmadi` veriyor — kabul 2-A/F (doğrulama durumu) — kanıt: research/a-agent-runtime.md:42, :78, :138. | Kapandı. §5.3'te istisnalar yazıldı. |
| KM-32 | [ORTA] architecture.md:532 — "Headless CLI paneli tam karşılar" denirken Araştırma A'nın güvenlik uyarısı ana belgeye taşınmamış: `--bare` olmadan bir `-p` oturumu çalışma klasöründeki `.claude/settings.json` kancalarını ve `.mcp.json` sunucularını çalıştırır; `--bare` ise abonelik kimliğini okumaz. Kurum repoları dış kaynaklı içerik taşıyabilir ve adaptör kancaları worktree'ye yazıyor; §19.2 yerel güvenlik satırında bu yok (architecture.md:1634) — kabul 3.9 (riskler) — kanıt: research/a-agent-runtime.md:92, :31. | Kapandı. §5.4: çalışma klasöründeki `.claude/` ve `.mcp.json` üretilen içerikle karşılaştırılır, farkta DUR; §19.2 satırı. |
| KM-33 | [ORTA] architecture.md:950 — "Sıfır hata" hedefinin ölçüsü bağımsız değil: tohumlanmış hata derlemi (F1) ve tanımlama vakalarının beklenen cevapları (architecture.md:810) kimin yazacağı tanımsız; uygulayıcı ekip yazarsa yalnız bilinen hata türlerini ölçer. F6'da kapıdan sonra bulunan hata sayısına eşik yok, yalnız raporlanıyor (architecture.md:1127) — kabul 2-F ("fark edilmeden karara ulaşan sıfır hata"), "İşi yapan kendi işini onaylamaz", soru 2 (ölçülebilirlik) — kanıt: belirtilen satırlar. | Kapandı. Derlemi ve beklenen cevapları kalite mühendisi temiz bağlamla yazar (§10.11); F6'ya eşik (baskı/üretim kararına ulaşan 0). |
| KM-34 | [ORTA] architecture.md:1671 — Araştırma B'nin API varlık doğrulaması OCCT master ve `cadquery-ocp-stubs 8.0.1` üzerinde yapıldı; G-06 Faz 1 için OCP 7.9.3 seçiyor. Model işlem listesi örneği `cadquery-ocp 7.9.1` (examples/model-oplist.json:14) yazıyor; CadQuery 2.8 `cadquery-ocp>=7.9.3.1,<8.0` istediği için bu sürüm birlikte kurulamaz. §6.3'teki "OCP'de var" iddiaları seçilen sürüm için doğrulanmadı — kabul 2-B (dürüst yaz) — kanıt: research/b-cad.md:17-18, :32. | Kapandı. §6.3 sürüm notu; örnek `cadquery-ocp 7.9.3.1`. |
| KM-35 | [ORTA] architecture.md:695 — "Özellik tanıma için Analysis Situs (BSD-3, C++) var, Python bağlaması yok" kaynağından kesin: kaynakta işlev kapsamı "yalnız dosya adlarından anlaşıldı (dogrulanmadi)" ve "PyPI'de Python paketi bulunamadı" — kabul 2-B — kanıt: research/b-cad.md:175, :258. | Kapandı. Analysis Situs ifadesi kaynağın doğrulama durumuyla. |
| KM-36 | [ORTA] wireframes/model.html:105 — Arayüz "Kalıcı ad: işlemler yüze bu imzayla bağlanır, yeniden üretimde kaybolmaz" diyor; §6.2 ve Araştırma B topolojik ad sorununun hazır çözümü olmadığını, belirsizlikte durulacağını söylüyor. Ayrıca §6.2'deki imza alanları (kenar sayısı, komşu yüzey türleri; architecture.md:672) `model-oplist` imza şemasında yok (model-oplist.schema.json:58) — kabul 2-B (dürüst yaz), iç tutarlılık — kanıt: research/b-cad.md:213. | Kapandı. Tel kafes metni ("tahmin edilmez, durur"); `edge_count`, `neighbor_surface_types` şemada. |
| KM-37 | [ORTA] architecture.md:1385 — Taşıma: v1 şemaları eskide karşılığı olmayan zorunlu alanlar istiyor (`work.work_type`, `work.packages`, `requirement.origin`, onaylı zorunlu istekte `verification`, hesapta `validity`, `input_hash`). Betiğin bunları nasıl dolduracağı tanımsız; V1 (şema 0 hata) ile "bilinmeyen değer uydurulmaz" ve V2 ("yeni sayı 0") gerilimde; tam alan eşlemesi Faz 1'e bırakılmış (architecture.md:1364) — kabul 3.6 (betikle taşıma ve doğrulama), CLAUDE.md ("Bilinmeyen değer uydurulmaz") — kanıt: work.schema.json `required`, requirement.schema.json allOf. | Kapandı. §14.3 V1: taşıma eksikleri uydurulmaz, `migration_gap` kartı (DUR). |
| KM-38 | [ORTA] architecture.md:1667 — G-02 (ilk commit `main`'e, "İlk push yetkisi") bir Hold maddesini geçici karar listesine koyuyor; uzak `main`'de `847d26a` var. İzin verildiyse kayda geçmeli, verilmediyse §20.2'ye ait; belgede izin kaydı yok (doğrulanmadı) — CLAUDE.md Hold ("bir repoya ilk kez push etmek"), kabul 0 — kanıt: `git -C /home/user/mekanik ls-remote --heads origin`. | Kapandı. İlk push baş mühendis yetkisiyle; §20.3'e birebir talimat yazıldı; G-02 güncellendi. |
| KM-39 | [ORTA] architecture.md:1666 — Kabul ölçütü 0'daki "5 ad öner; GitHub ve PyPI'da boş mu, marka çakışması var mı" belgede yok; G-01 yalnız `mekanik` için PyPI 404 ve GitHub'a bakmış, marka araştırması "kısmi" — kabul 0 — kanıt: architecture.md:1666. | Açıklandı. Baş mühendis 5 ad önerisini beklemeden `mekanik`'i seçti; öneri listesi yapılmadı; marka araştırması kısmi, Faz 4'te tamamlanır (G-01). |
| KM-40 | [DÜŞÜK] architecture.md:432 — "Eski 25 alt komut": eski CLI'de 23 alt komut var; 25, Ek B tablosunun satır sayısı (`ana.py` genel ve `__init__.py` dahil) — kaynaksız/yanlış sayı — kanıt: `grep -c add_parser surec:cli/surec_cli/ana.py` → 23. | Kapandı. 23 alt komut (ölçü yazıldı). |
| KM-41 | [DÜŞÜK] architecture.md:1458 — "Testi olmayan 17 taşınır parçanın her biri için yeni test yazılır": Ek B §14 madde 17 "test gerekmez" diyor; 1.3 ölçütü (architecture.md:1522) maddeleri "çekirdek/CLI (1–12)" diye adlandırıyor, ama 1, 6, 7, 8 analysis ve mech maddeleri — iç tutarlılık — kanıt: appendix-b-migration-inventory.md:430-449. | Kapandı. 16 test (17. madde test gerektirmez); 1.3 madde etiketleri düzeltildi. |
| KM-42 | [DÜŞÜK] architecture.md:878 — Kaynağı yazılmamış sayılar ve ölçülemeyen ölçüt: akış satırı "en çok 200 karakter" (architecture.md:878), V8 "bağıl ≤ 1e-9" (architecture.md:1392), zaman kutusunda "%50 aşımda" ve faz süreleri yok (architecture.md:1617), 2.8 "Eşitlik kontrol listesi %100" (liste tanımsız, architecture.md:1542); model.html:128 "± 1,0 mm³ türetilir" (formülsüz tolerans; ayrıca 2 797,8 mm² × 1,2 mm = 3 357 mm³, gösterilen 3 656) — CLAUDE.md "Kaynaksız sayı yok", belge girişi (architecture.md:26) — kanıt: belirtilen satırlar. | Kapandı. 200 karakter, 1e-9, %50 "öneri" etiketli; 2.8 listesi Ek B §4–5; model.html hacmi alan × mesafe ile tutarlı. |
| KM-43 | [DÜŞÜK] architecture.md:181 — Temizlik testindeki yasak sözcükler (`print`, `wing`, `mold`) alt dizgi olarak `print(`, `drawing`, `following` gibi sözcüklere çarpar; eşleşme kuralı (tam sözcük, tanımlayıcı) yazılmadığı için 1.5'in "0 eşleşme" eşiği ölçülemez (iş türü örneğinde `drawing` girdisi de var) — soru 2 (ölçülebilirlik) — kanıt: examples/work-type.json `required_inputs.id = drawing`. | Kapandı. Temizlik testi tam sözcük/tanımlayıcı eşleşmesi. |
| KM-44 | [DÜŞÜK] schemas/v1/common.schema.json:134 — `standard_deviation` kimliği İngilizcede istatistiksel standart sapma (σ) demek; belirsizlik kodunun yanında karışır (ör. `deviation_from_standard`) — kesin karar 1 (İngilizce adlar anlamlı olmalı) — kanıt: common.schema.json `uncertainty` tanımı aynı dosyada. | Kapandı. `deviation_from_standard` (şema, örnek, belge). |
| KM-45 | [DÜŞÜK] schemas/v1/standard-item.schema.json:65 — Zayıf şema kısıtları (çoğu çekirdek kontrolüne bırakılmış, ama belgede şemaya atfedilmiş): paralı maddede `open_equivalent.searched=false` ve satın alma kaydı yokken geçer; tikte `quality_review` herhangi bir başvuru türü (ör. commit) olabilir; `priority` türle tutarsız olabilir (mevzuat = 5); kritik hesapta `cross_check.status` `missing` ya da `disagree` geçer; alan dışı hesap kanıtı geçer; `const()` `derived` kaynak alabilir (architecture.md:351 dört kaynak der); `auth: provider` bütçesiz geçer; ekip kimliği baş mühendis kimliğiyle aynı olabilir; DUR sorusunda varsayılan "PLA" + `opens_card: false` geçer — kabul 3.3, 2-F — kanıt: 10 sınama örneğinin hepsi → GEÇER. | Kısmen. Şemada: paralı maddede arama zorunlu ve satın alma, tikte `quality_review` türü, sabitte türetilmiş yasak, DUR sorusunda varsayılan. Çekirdek kontrolüne bırakılanlar (Faz 1 testleri): öncelik–tür tutarlılığı, kritik hesapta uyuşmazlık (CALC-03), alan dışı kanıt (CALC-04), `provider` bütçesi, ekip ≠ baş mühendis kimliği. Şema durumu saklar, kontrol engeller. |
| KM-46 | [DÜŞÜK] wireframes/card.html:105 — Örnek verilerde kimlik biçimleri tutarsız: K-04 şema örneğinde malzeme kararı, tel kafeste yan delik kararı; hesaplar `H-03`, `H-05` (el kitabı §8'de `H-` hata kaydı öneki; şemada hesap kimliği slug); gözlemler `G-02`, `G-04` (G geçme kartı öneki); deney `D-01` (şemada `X-01`); kapı kartı `ORN-BRK-03-G2` (şemada `O-G2`) — el kitabı §8 adlandırma, iç tutarlılık — kanıt: card.html, examples/*.json. | Açık (DÜŞÜK). Tel kafes örnek kimlikleri (H-03, G-02, D-01) şema biçimine çevrilmedi; Faz 2 ön yüzü şema kimliklerini kullanır. |
| KM-47 | [DÜŞÜK] wireframes/flow.html:173 — Gün sonu özeti tel kafeste "verilen kararlar, bekleyenler, riskler" + soru paketi; §9.3 ve E4 dört bölüm ister, "Ajan kullanımı" yok — kabul 2-E, E4 — kanıt: architecture.md:930, :941. | Kapandı. Gün sonu özetine "Ajan kullanımı" eklendi. |
| KM-48 | [DÜŞÜK] architecture.md:688 — Kaynaktaki doğrulama notları ana belgeye geçerken düşmüş: pah "benzer yayılma ve köşe sorunları" kaynakta `dogrulanmadi` (research/b-cad.md:66); Haiku fiyatı "100 000 token'a kadar istem" koşulu (architecture.md:530); JCGM 100 Amd.1:2026 için `metin_elde` ama yalnız kapak okundu (architecture.md:1099; research D:275); HDBK-7009B sayfalarındaki "DRAFT" başlığı ve tarih tutarsızlığı (research D:22); CalculiX "GPL-2.0-only" ikincil kaynak (architecture.md:1591; research D:428); openInjMoldSim için deneysel karşılaştırma (Krebelj vd., research C:55) belirtilmemiş — kabul 2-F (doğrulama durumu) — kanıt: belirtilen satırlar. | Kapandı. Pah `dogrulanmadi`, Haiku koşulu, JCGM Amd.1 yalnız kapak, HDBK "DRAFT" notu, CalculiX ikincil, Krebelj deneysel karşılaştırması eklendi. |
| KM-49 | [DÜŞÜK] wireframes/model.html:116 — Yüz öteleme için "Komşu yüzler uzatılır" yazıyor; §6.3'te seçilen prizma + Boolean yolu komşu yüzleri uzatmaz — kabul 2-B — kanıt: research/b-cad.md:61 "(ii) Prizmanın yan yüzleri yöne paraleldir; komşu yüzleri uzatmaz". | Kapandı. "Dik; prizma + Boolean (komşuları uzatmaz)". |
| KM-50 | [DÜŞÜK] architecture.md:1634 — Kurum verisinin model sağlayıcıya gitmesi ele alınmamış: Araştırma D "Claude Code dışarıya veri gönderir: dur noktası kuralı geçerli" diyor; kurum kaydında `privacy` alanı var ama ajan çalıştırmayla ilişkisi tanımsız — CLAUDE.md Hold ("dışarıya veri gönderen her şey"), el kitabı §1 kurum gizliliği — kanıt: research/d-nasa-regulation-licenses.md:444; config.schema.json `organization.privacy`. | Kapandı. Kurum başına `data_transfer.model_provider_allowed` zorunlu; `false` ise ajan başlamaz (§5.4, §19.2). |
| KM-51 | [DÜŞÜK] architecture.md:1694 — T-04 (eski panel Faz 2 sonuna kadar; Faz 1'de yeni ön yüz yok) kabul ölçütü 3.7'de zaten belirli (panel kokpit Faz 2); açık karar listesinde gereksiz. Buna karşılık listede olması gerekenler: G-08 (kesin karardan sapma), G-02 (Hold), `review` seviyesinin v1'de kalıp kalmayacağı, onay doğrulama yöntemi — soru 8 — kanıt: architecture.md:1689-1704. | Kapandı. T-04 kaldırıldı; T-15 (dal adları) ve T-16 (ajan yalıtımı) eklendi; G-02 §20.3'e taşındı. |
| KM-52 | [DÜŞÜK] wireframes/index.html:1 — Tel kafeslerde ajanı başlatma/sürdürme ve dosya indirme denetimi çizilmemiş (A1'in yedi işinden ikisi görünmüyor; yalnız "Aç ve tanımlamayı başlat" ve "Durdur" var) — kabul 2-A — kanıt: `grep "Başlat\|Sürdür\|İndir" wireframes/*.html` boş. | Kapandı. Akışa "Sürdür" ve "Yeni başlat", model ekranına "İndir" eklendi. |
| KM-53 | [DÜŞÜK] schemas/v1/common.schema.json:69 — `text_i18n`'de `en` isteğe bağlı; paket soru ağaçlarında EN kapsamı zorunlu değil, 2.7 yalnız panel ve CLI'ı ölçüyor — kesin karar 1 (arayüz TR+EN) — kanıt: common.schema.json:66-71. | Kapandı. Ölçüt 4.2 paket katalogları ve soru ağaçlarını kapsar. |
| KM-54 | [DÜŞÜK] schemas/v1/intake-summary.schema.json:59 — `method.manufacturing` ve K kararı her iş türünde zorunlu; `analysis` iş türünde üretim yöntemi kararı anlamsız — iç tutarlılık — kanıt: architecture.md:759 (`analysis`: model türü none/imported). | Kapandı. `method` analizde `not_applicable` alabilir. |
| KM-55 | [DÜŞÜK] architecture.md:1333 — K1 temiz makinede "Claude girişi" istiyor; gerçek hesap gerektirdiği için CI'de otomatikleşemez, ölçüm elle yapılır; belgede yazılmamış — soru 2 (ölçülebilirlik) — kanıt: architecture.md:1333. | Kapandı. K1'in elle ölçüleceği yazıldı. |
| KM-56 | [DÜŞÜK] research/a-agent-runtime.md:78 — Araştırma ekleri birbirini tutmuyor: A, Python SDK tekerleğinin CLI içerdiğini `dogrulanmadi` veriyor, D bunu README ve PyPI dosya boyutlarıyla doğrulamış (research D:445); C, Elmer'i "GPL-2 / LGPL-2.1, hangi bileşen belirsiz" veriyor (research C:54), D ve ana belge LGPL-2.1-or-later — iç tutarlılık — kanıt: belirtilen satırlar. | Kapandı. Araştırma A notu güncellendi; Elmer notu §18'de. |

### 22.2 Kalite mühendisinin diğer notları

#### Doğru bulunan araştırma iddiaları

Agent SDK'nın aynı Claude Code ikilisini çalıştırması (a:20); CLI'nin `/login`, `setup-token` ve API anahtarını desteklemesi (a:28-30); fiyatlar (a:37-51); Consumer Terms otomasyon maddesi (a:60); SIGINT/SIGTERM davranışı, `--resume`, `--permission-prompt-tool`, `capabilities` (a:86-93); CadQuery 2.8 ile build123d 0.13'ün aynı ortamda kurulamaması (b:39); fillet yayılması ve kısmi sonuç (b:65); detay silmede `HasWarnings` (b:67); koni RANSAC'ının incelenen kütüphanelerde olmaması (b:170, :202); iPhone LiDAR'ın santimetre sınıfı (`ikincil_kaynak` olarak doğru verilmiş, b:179).

#### Kalite mühendisinin kapsam tablosu (inceleme anındaki durum)

| Kabul ölçütü maddesi | Belgedeki bölüm | Durum |
| --- | --- | --- |
| 0 Repo ve çalışma düzeni | §20.1 G-01/G-02, README | kısmen (5 ad önerisi ve marka araştırması yok; eski repoya commit; ilk push Hold kaydı yok) |
| 1 Kesin kararlar | §2.1 | kısmen (Türkçe dal adları şemada, tel kafeslerde Türkçe komut/dosya adları; tel kafeste DUR sorusu varsayımla geçiyor) |
| 2 Katmanlar | §3 | kısmen (çekirdekte `mold_for_part`, `scan_to_model`, `fit`) |
| 2-A Panel kokpit | §5, Araştırma A, tel kafesler, `agent-run`, `stream-event` | karşılandı (bir iddia kaynağından fazla; güvenlik uyarısı eksik) |
| 2-B CAD girdisi ve değişikliği | §6, Araştırma B, `model-oplist` | kısmen (iki iddia kaynağından fazla; okuma parametreleri şemada yok) |
| 2-C Tanımlama | §7, `work-type`, `question-tree`, `intake-summary` | karşılandı (tel kafes onay sırasıyla çelişiyor) |
| 2-D Soru politikası | §8, `decision`, `provisional-decision`, `config.policy` | kısmen (`review` kaçağı; `main_dimensions` işareti ve `max_questions_per_stage` şemada yok) |
| 2-E Rapor akışı | §9, `stream-event` | karşılandı |
| 2-F Mühendislik güvencesi | §10, `calculation`, `evidence`, `standard-item` | kısmen (bağımsızlık örneği tanıma aykırı; şema stdmap alanlarını, kanıtsız "karşılandı"yı, belirsizliği, üç bölgeyi zorlamıyor; hata kaydı şeması yok) |
| 3.1 Bağımlılık envanteri | §15, Ek A | karşılandı (sayılar ve örnek satırlar doğrulandı) |
| 3.2 Taşıma envanteri | §16, Ek B | karşılandı (küçük sayım hataları) |
| 3.3 JSON Schema | `schemas/v1` (17 şema, sürümlü) | karşılandı (zorlama boşlukları ORTA bulgularda) |
| 3.4 Eklenti arayüzü ve iki örnek paket | §11 | karşılandı (molding kimlik tutarsızlığı) |
| 3.5 Kurulum | §13 | karşılandı |
| 3.6 Mevcut çalışmaların taşınması | §14 | kısmen (zorunlu yeni alanların doldurulması ve tam alan eşlemesi tanımsız) |
| 3.7 Faz planı ve sayısal ölçütler | §17 | karşılandı (Faz 1 "yeni özellik" sınırı belirsiz) |
| 3.8 Lisans tablosu | §18, Araştırma D | karşılandı |
| 3.9 Riskler, ikinci sistem, dışarıda bırakılanlar | §19 | kısmen (boyut bütçesi kapsamı dar; şemalar erken donuyor; onay sahteciliği ve kanca riski yok) |
| 4 Kalite incelemesi | §22 | bu inceleme |

#### Kalite mühendisinin genel değerlendirmesi (inceleme anında)

Belge kapsamlı, sayıları büyük ölçüde doğrulanabilir ve dürüst tablolarla yazılmış; ama DUR ve "işi yapan onaylamaz" ilkelerinin zorlanması (`review` kaçağı, onay sahteciliği, tel kafesteki DUR sorusu), kesin karar 1'deki adlandırma, çekirdeğin alan bilmemesi ve dört araştırma iddiasının kaynağından fazla söylemesi giderilmeden baş mühendis onayına hazır değil.

### 22.3 İkinci tur: T-01 kararının işlenişi

İkinci tur 2026-11-06'da (07:35 UTC civarı), baş mühendisin T-01 kararı işlendikten sonra yapıldı. Kalite mühendisi temiz bağlamla ve dar kapsamla çalıştı: §1, §3.2, §4.9, §5, §13.2, §17, §18, §19.2, §20, Araştırma A §4a, ayar şeması, akış tel kafesi. Bulguları **4 YÜKSEK, 13 ORTA, 14 DÜŞÜK**, toplam 31. Araştırma A §4a'daki 13 alıntının 13'ünü belge metninde birebir buldu.

**Özet durum.** YÜKSEK 4/4 kapandı; KM2-1 yöntemi yeni açık karar T-17'ye bağlandı. ORTA 13/13 kapandı; KM2-15 yeni açık karar T-18'e bağlandı. DÜŞÜK 13 kapandı, 1 kısmen (KM2-30). Kapanışları proje mühendisi yazdı; doğruluğu baş mühendis incelemesinde ve Faz 1'in ilk kalite turunda denetlenir.

| No | Bulgu (kalite mühendisi, olduğu gibi) | Kapanış (proje mühendisi) |
| --- | --- | --- |
| KM2-01 | [YÜKSEK] docs/design/architecture.md:633 — "Onay güvenliği değişmez" eklenti kipinde dayanaksız. §4.6'daki ortam temizliği (SSH_AUTH_SOCK, GPG_AGENT_INFO, GIT_AUTHOR_*) ve sandbox, ajanı mekanik başlattığında uygulanabiliyordu. Eklenti kipinde oturumu kullanıcı kendisi açıyor (:490) ve eklenti ne sandbox ne de izin ayarı koyabiliyor. Baş mühendisle aynı işletim sistemi kullanıcısıyla çalışan ajan ssh-agent soketine, panelin CSRF sırrına ve `~/.config/mekanik` içindeki `identities.chief_signing_key`'e erişebilir. `PreToolUse` engel listesindeki 5 kalıp betik, python ya da base64 ile aşılabilir. 1.11 (:1631) yalnız 5 negatif test istiyor. — İşi yapan kendi işini onaylamaz (CLAUDE.md, el kitabı §1) — kanıt: plugins/components.md:181 "Only two keys take effect from a plugin, `agent` and `subagentStatusLine`; every other key is dropped"; architecture.md:376, :490, :612 | Kapandı. Eklenti kipinde onay güvencesi ajan yalıtımına değil, insan varlığı isteyen imzaya dayanır: donanım anahtarı, kullanım başına onay ya da onay başına parola (§4.6 madde 5, §5.4, §19.2). `PreToolUse` listesi kolaylık katmanı olarak işaretlendi. Yöntem seçimi yeni açık karar T-17. |
| KM2-02 | [YÜKSEK] docs/design/architecture.md:1742 — Kurum verisinin dışarı gitmesine karşı eklenti kipinde önerilen önlem belgeyle çelişiyor. Metin "`SessionStart` kancası … ajanın çalışma araçlarını kapatır" diyor, ama SessionStart hiçbir şeyi engelleyemez; üstelik oturum açılır açılmaz istem ve bağlam model sağlayıcısına gider. Başsız kipteki "ajan başlamaz" kapısının eklenti kipinde karşılığı yok. Sandbox ağ kısıtı da eklenti kipinde zorlanamıyor (ilk bulgu). — Hold: dışarıya veri gönderen her şey — kanıt: hooks.md:1181 "SessionStart … Context only … No blocking or decision control", hooks.md:1020 "SessionStart \| No"; engelleyebilen olaylar PreToolUse ve UserPromptSubmit (hooks.md:37, :832) | Kapandı. `SessionStart` yalnız uyarır. Kapı üç katmanlı: panel oturum açmaz, `UserPromptSubmit` istemi engeller, `PreToolUse` dosya erişimini reddeder (§5.4, §19.2; belge alıntısıyla). Kalan risk yazıldı. |
| KM2-03 | [YÜKSEK] docs/design/architecture.md:1841 — §20.4'teki T-02 kuralı ("öneri" etiketleri artık `karar` anlamına gelir) karardan sonra yazılan eşikleri de baş mühendis kararına çeviriyor. Bunlar: A10, A11 (≤ 1 500 token), A12 (p95 ≤ 5 s), 1.11 (5 negatif test) ve yeniden yazılan A1, A2, A5, A6, A8. Baş mühendis bu metinleri 07:20'de görmedi; hiçbirinin dayanağı yazılı değil. — Kaynaksız sayı yok; işi yapan onaylamaz; karar kaydında kararı veren rol yazılır — kanıt: architecture.md:690-700, :1631 `git diff`'te yeni satırlar; ileti 07:20, dosya değişikliği 07:24 UTC (stat) | Kapandı. Karardan sonra yazılan eşikler "öneri (T-01 sonrası; onay bekliyor)" diye işaretlendi; belge başı notu ve §20.4'te T-02'nin kapsamı yazıldı. |
| KM2-04 | [YÜKSEK] docs/design/architecture.md:1840 — §20.4'teki T-01 satırı, baş mühendisin söylediğinden fazlasını onun kararıymış gibi kaydediyor. "Başsız kip yalnız API anahtarıyla", "Agent SDK ikinci başsız adaptör" ve "eklenti birincil" proje mühendisinin çıkarımları; ilki maliyet etkisi taşıyor, çünkü T-01 önerisi abonelikti. G-10 metni karardan sonra değiştirildi, sonra da "G-01…G-22 onaylandı" (:1855) kapsamına alındı. Koşullu ileti ("edebilirsek") koşulsuz karar olarak yazıldı. Faz 1'e bırakılan yapılabilirlik açıkları (onay yalıtımı, masaüstünde oturum açma) koşul olarak kayda geçmedi. — Karar kaydında kararı hangi rolün verdiği yazılır (CLAUDE.md, Divan); kesin karar 7 (maliyet etkisi baş mühendisi durdurur) — kanıt: :1836'daki birebir ileti yalnız "skill/kütüphane gibi entegre" ve "lokalde açabilsinler" diyor; :1787, :1807 | Kapandı. §20.4 iki sütunlu: baş mühendisin söylediği ve proje mühendisinin uygulaması. Uygulama kararları (eklenti birincil, başsız kipte kimlik doğrulama, SDK) ve G-10 değişikliği onay bekliyor; koşullu ileti ve açık yapılabilirlik noktaları yazıldı. |
| KM2-05 | [ORTA] docs/design/architecture.md:624 — "Ubuntu'da masaüstü uygulaması olduğu için terminal gerekmez" cümlesi kaynağından fazlasını söylüyor. Linux masaüstü uygulaması terminalde `sudo curl` ve `sudo apt` ile kuruluyor. §13.1 (:1375) "kullanıcı düzeyi" kurucu diyor ve masaüstü yolunun sudo (Hold) istediğini yazmıyor. Araştırma A:146'nın satır başlığı da "Ubuntu'da terminalsiz". — Kesin karar 6; Hold: sudo — kanıt: desktop-linux.md:34 "Open a terminal and run the commands in each step", :41 "sudo apt install curl gnupg", ayrıca "sudo curl -fsSLo /usr/share/keyrings/…" | Kapandı. "Kurulumdan sonra günlük kullanımda terminal gerekmez; kurulum terminalde sudo ister (Hold)" (§5.4, §13.1, Araştırma A). |
| KM2-06 | [ORTA] docs/design/architecture.md:497 — Panelin "Oturumu aç" düğmesinin masaüstü uygulamasını ya da VS Code'u çalışma klasöründe `/mekanik:resume <kod>` istemiyle açabildiği belgede yok. Belgeli olanlar yalnız `claude-cli://open` (yeni bir terminal penceresi açar) ve masaüstü için SSH parametreli `claude://code/new`. A1 (:690) bunu sahte adaptörlü Playwright testiyle ölçemez; Araştırma A §4a bu konuyu kapsamıyor (doğrulanmadı). — Kesin karar 6 (panel kokpit, terminal isteğe bağlı) — kanıt: deep-links.md:9 "opens Claude Code in a new terminal window"; desktop.md:1566-1580 (parametreler yalnız `ssh_host`, `ssh_port`, `ssh_folder`, `q`) | Kapandı. Belgeli yol `claude-cli://open?cwd=…&q=…` (yeni terminal penceresi). Masaüstü ve VS Code'da klasörde istemle açma "doğrulanmadı, Faz 2"; o zamana kadar yol ve istem kopyalanabilir (§5.1). |
| KM2-07 | [ORTA] docs/design/architecture.md:597 — "Claude Code içinde iki komut" kurulumu masaüstü uygulamasında doğrulanmadı. Masaüstünde eklentiler `/plugin` komutuyla değil eklenti yöneticisi arayüzüyle yönetiliyor; terminal paneli açan komutlar Code sekmesinde farklı davranıyor. A10 (:692) "elle adım yalnız bu üç komut ve Claude girişi" diyor, oysa şunlar da elle yapılıyor: Claude Code'un kendi kurulumu, `/mekanik:setup`'ın her komut için istediği izin (:1388), `mekanik init` soruları ve gerekirse sudo adımı. Ölçüt bu hâliyle ölçülemez. — Kabul ölçütü ölçülebilir olmalı; kesin karar 6 — kanıt: desktop.md:2228 "Plugins \| `/plugin` command \| Plugin manager UI", desktop.md:2247 "Terminal-dialog commands … behave differently in the Code tab" | Kapandı. Masaüstünde eklenti yöneticisi arayüzü yazıldı; A10 bütün elle adımları sayar ve ölçülebilir. |
| KM2-08 | [ORTA] docs/design/architecture.md:613 — Talimat iletiminin dayandığı monitor eksik anlatılmış. Bildirimdeki anahtarı `experimental` altında, yani "manifest shape may still change". Masaüstü uygulamasında ve VS Code'da monitor'ün çalıştığı belgede yazmıyor; masaüstü belgesi eklenti bileşenlerini sayarken monitor'ü anmıyor. Channels önizlemede olduğu için reddedilirken monitor'ün deneysel durumu risk tablosuna girmemiş. A12 (:694) bütünüyle buna dayanıyor. — Kaynağından fazlasını söyleme; iç tutarlılık — kanıt: plugins-reference.md:156, :158; desktop.md:618 "add skills, agents, hooks, MCP servers, and LSP configurations"; research/a-agent-runtime.md:140 | Kapandı. Monitor'ün `experimental` olduğu, masaüstü ve VS Code'da doğrulanmadığı ve kanca yedeği §5.4, §19.2 ve A12'ye eklendi. |
| KM2-09 | [ORTA] docs/design/architecture.md:697 — Eklenti kipinde durdurma, modelin monitor bildirimine uymasına bağlı (A5: "bir sonraki araç adımı içinde"). Oysa `PreToolUse` kancası durdurma bayrağı varken araçları modelden bağımsız olarak reddedebilir; bu yol kullanılmamış. Sahte adaptörle bu kip sınanamaz. — Kontroller modelden bağımsız betiklerdir; kesin karar 6 — kanıt: hooks.md:37 "PreToolUse \| Before a tool call executes. Can block it"; architecture.md:498, :628 | Kapandı. Durdurma bayrağı `PreToolUse` ile modelden bağımsız uygulanır; A5 kanca birim testiyle ölçülür. |
| KM2-10 | [ORTA] docs/design/architecture.md:621 — "Kimlik doğrulama sorunu ortadan kalkar; belirsizlik bu kipte doğmaz" kaynaksız bir kesin iddia. Panelden gelen kutusuna, oradan monitor'e giden yol, abonelikli oturuma programla talimat itiyor; bu da otomasyon sayılabilir. §5.3:581'deki "yorum" etiketi ve alıntı 4 bu kipte de geçerli olabilir. Hiçbir kaynak eklenti kipinin şart belirsizliğini kaldırdığını söylemiyor. — Kaynaksız iddia; belge ile yorumun ayrılması — kanıt: research/a-agent-runtime.md:60 (Consumer Terms otomasyon maddesi), :62 (alıntı 4), :150 | Kapandı. "Büyük ölçüde azalır, yorum" diye düzeltildi; monitor iletiminin otomasyon sayılabileceği yazıldı (§5.4, Araştırma A §4a). |
| KM2-11 | [ORTA] docs/design/architecture.md:622 — "Başka ajanlar bağlanabilir" eklenti kipi için zayıf. Onay engeli, oturum kilidi, veri aktarım kapısı ve talimat iletimi Claude Code'a özgü kanca ve monitor'lerde duruyor; skill ve MCP ile bağlanan başka bir ajanda bu güvenceler olmaz. İnce arayüz (`AgentAdapter`) yalnız isteğe bağlı başsız kipte tanımlı. Eklenti kipinde ajan barındırıcısından neler beklendiğini (araç öncesi kapı, bildirim, oturum başı) sayan bir sözleşme yok. Skill'lerin taşınabilmesi için ön madde (frontmatter) alanlarının standarda sınırlanacağı da yazılmamış. — Kesin karar 3 — kanıt: skills.md:420 "Outside Claude Code, you can use only the fields in the Agent Skills spec", skills.md:435; architecture.md:612-614, :637 | Kapandı. "Barındırıcı sözleşmesi" ve skill ön maddesinin standarda sınırlanması eklendi; onay ve kapı güvencelerinin çekirdekte olduğu yazıldı. |
| KM2-12 | [ORTA] docs/design/architecture.md:1732 — "Tur ve bütçe sınırı" önlemi birincil kipte uygulanamıyor, çünkü `--max-turns` ve `--max-budget-usd` yalnız print kipinde çalışıyor. Buna karşın şema eklenti kipinde de `auth: api_key` için `max_budget_usd` zorunlu tutuyor (config.schema.json:225-241). Örnekteki `max_turns: 200` (examples/config.json:147) eklenti kipinde etkisiz. — Maliyet etkisi DUR kategorisi (kesin karar 7); iç tutarlılık — kanıt: cli-reference.md:105-106 "(print mode only)" | Kapandı. Şemada bütçe kuralı yalnız başsız kipte; örnekten `max_turns` kaldırıldı; eklenti kipinde tur/bütçe bayraklarının çalışmadığı yazıldı. |
| KM2-13 | [ORTA] docs/design/architecture.md:1409 — Kurulum sihirbazının soruları kararlar ve şemayla uyuşmuyor. Kip (`agent.mode`) sorulmuyor; sunulan "abonelik" seçeneği başsız kipte şemaya göre geçersiz. §5.5:663 sihirbazın `data_transfer.model_provider_allowed`'ı soracağını, §20.4'teki T-07 (:1845) maliyet eşiğinin "sihirbazda kurum başına sorulacağını" söylüyor; ikisi de soru listesinde yok. — İç tutarlılık; Hold (veri aktarımı); T-07 — kanıt: architecture.md:1403-1410; config.schema.json:210-221 | Kapandı. Sihirbaz soruları: ajan kipi, kurum başına maliyet eşiği ve veri aktarım kararı (§13.2). |
| KM2-14 | [ORTA] docs/design/architecture.md:1741 — Çalışma klasöründeki `.claude/` ve `.mcp.json` içeriğinin karşılaştırılması §5.4'e bağlanmış, oysa bu denetim yalnız §5.5'te (başsız kip) var. Birincil eklenti kipinde kullanıcı oturumu kurum reposunun worktree'sinde açıyor ve eşdeğer bir denetim tanımlı değil. KM-32'nin kapanışı eklenti kipinde açık kalıyor. — İç tutarlılık; Hold — kanıt: architecture.md:662 (yalnız başsız kip), :497 | Kapandı. Eklenti kipinde Claude Code'un güven sorusu + `SessionStart` uyarısı + `UserPromptSubmit` engeli (§5.4). |
| KM2-15 | [ORTA] docs/design/architecture.md:483 — "Panel tek pencerelik kokpittir" cümlesi :624'teki "Konuşma kullanıcının Claude Code penceresindedir" ile çelişiyor. T-01'in kesin karar 6'nın uygulanışını değiştirdiği §20.4'te kayda geçmemiş. — Kesin karar 6; iç tutarlılık — kanıt: architecture.md:483, :624, :1840 | Kapandı. §5.1 "panel kokpittir" olarak düzeltildi; konuşmanın Claude Code penceresinde olması yeni açık karar T-18. |
| KM2-16 | [ORTA] docs/design/architecture.md:617 — Alan paketi eklentilerinin `mekanik ^1` bağımlılığı, kaynağın koyduğu koşulları atlıyor. Sürüm aralığı yalnız `<eklenti>--v<sürüm>` biçimindeki git etiketleriyle çözülür; etiket atmak ve push etmek ajana kapalı (`git tag` engelli), yani baş mühendisin işi. Başka bir marketplace'teki paket, kök marketplace'te `allowCrossMarketplaceDependenciesOn` yoksa bağımlılığı kurmaz. `^1` aralığı 0.x sürümlerini kapsamaz. — Kaynağından eksik ya da fazla söyleme — kanıt: plugins/dependencies.md:51 "installs at the highest git tag that satisfies this range", :143 "Tag each release as `<plugin-name>--v<version>`", :87 "By default, Claude Code doesn't install a dependency from a different marketplace…"; research/a-agent-runtime.md:141 | Kapandı. Git etiketi biçimi, etiketi baş mühendisin atması, marketplace'ler arası izin ve 0.x aralığı yazıldı. |
| KM2-17 | [ORTA] docs/design/architecture.md:623 — "Repoyu kendi Claude'una tanıt, yerelde aç" isteği yalnız marketplace komutlarıyla karşılanıyor. İletinin en düz okuması, yani repoyu klonlayıp ya da adresini verip Claude'u içinde açmak, tasarlanmamış: repo kökünde Claude'a yönelik kurulum yönergesi de, `.claude/settings.json` ile `extraKnownMarketplaces`/`enabledPlugins` tanımı da yok. Repodan paylaşılan eklentide monitor yüklenmediği için o yolda talimat iletimi çalışmaz. Kullanıcı kapsamında kurulumun zorunlu olduğu da yazılmamış. — T-01'in eksiksiz karşılanması — kanıt: plugins/loading.md:80 "Background monitors do not load" (repoya konan eklentiler için), plugins/loading.md:30 `extraKnownMarketplaces`; architecture.md:597-604 | Kapandı. Repo kökünde `.claude/settings.json` (`extraKnownMarketplaces`, `enabledPlugins`), `CLAUDE.md` yönergesi ve README; depoyla gelen eklentide monitor yüklenmediği için kullanıcı kapsamı zorunlu (§5.4). |
| KM2-18 | [DÜŞÜK] docs/design/architecture.md:30 — Başlıktaki "öneri … onaylayana kadar geçicidir (açık karar T-02)", :1587'deki "Eşikler `öneri`dir (T-02)" ve :9'daki "Onaylayan: —" §20.4'teki T-02 ile çelişiyor. — İç tutarlılık — kanıt: architecture.md:1841 | Kapandı. Belge başı notu ve §17 cümlesi T-02 kararıyla uyumlu. |
| KM2-19 | [DÜŞÜK] docs/design/wireframes/flow.html:19 — Üst çubuk hâlâ "Terminalde aç: `cd … && claude --resume 6f1c2a…`" gösteriyor ve :17'deki "■ Durdur" düğmesinde yumuşak durdurma notu yok; oysa §5.1:504 `claude "/mekanik:resume <kod>"` diyor. :170'teki "3 çalıştırma · 41 tur" de başsız kip anlamında. — İç tutarlılık — kanıt: flow.html:17, :19, :146, :170 | Kapandı. Bütün tel kafeslerde "Terminalde aç" komutu `claude "/mekanik:resume …"`; Durdur düğmesine not; ajan kullanımı satırı eklenti kipine göre. |
| KM2-20 | [DÜŞÜK] docs/design/architecture.md:496 — `/mekanik:new` skill'i §5.4:610'daki skill listesinde yok. `mekanik agent send` (:499) §4.11 CLI tablosunda yok. `mekanik watch` §4.11:459'a göre Faz 1'de, §17:1637'ye göre Faz 2'de geliyor; hangisinin ne zaman geldiği belirsiz. — İç tutarlılık; faz ataması — kanıt: architecture.md:450, :459, :610, :1637 | Kapandı. `new` skill'i listede; `agent send/stop` CLI tablosunda; `mekanik watch` CLI Faz 1, monitor bağlaması Faz 2. |
| KM2-21 | [DÜŞÜK] docs/design/architecture.md:637 — "Yalnız API anahtarıyla" ifadesi (ayrıca :492, :1840, Araştırma A:153) şemayla uyuşmuyor: şemaya göre başsız kipte `provider` da geçerli. — İç tutarlılık — kanıt: config.schema.json:216-221 | Kapandı. "API anahtarı ya da bulut sağlayıcısı (abonelik değil)" olarak birleştirildi. |
| KM2-22 | [DÜŞÜK] docs/design/architecture.md:490 — Aynı paragrafta "mekanik başsız oturum açmaz" (:490) ile "başsız kip isteğe bağlıdır" (:492) çelişkili okunuyor; Araştırma A'da da durum aynı (:150 ve :153). — İç tutarlılık — kanıt: architecture.md:490, :492 | Kapandı. "Eklenti kipinde mekanik oturum açmaz" olarak düzeltildi. |
| KM2-23 | [DÜŞÜK] docs/design/architecture.md:611 — Eklenti ajanlarının "model adı ayardan gelir" denmiş, ama :430 bu dosyaların derlenip eklentiyle dağıtıldığını söylüyor; kurulu eklenti dosyaları sabittir. `${user_config.*}` değerinin ön madde alanında yerine konup konmadığı doğrulanmadı. Eklenti kipinde `roles.project_engineer.model` kullanıcının oturum modelini belirlemiyor. İş kökü için de iki ayrı kaynak var: `userConfig` (:615) ve `paths.works_root`. — İç tutarlılık — kanıt: plugins-reference.md:497 ("skill and agent content"), plugins/components.md:324 | Kapandı. Ajan modelinin derlemede takma adla yazıldığı, ayardaki rol eşlemesinin yalnız başsız kipte ve yeniden derlemede kullanıldığı, `${user_config.*}` yerine konmasının doğrulanmadığı ve iş kökünün tek kaynağının ayar olduğu yazıldı. |
| KM2-24 | [DÜŞÜK] docs/design/architecture.md:1847 — T-09'un uygulanışı "§5.4, §5.6" diye gösterilmiş, ama §5.4'te T-09 yok (§5.3:593'te var). T-01'in uygulanış listesi (:1840) de değişen §3.2, §4.9, §17, §18, §19.2'yi, şemayı ve flow.html'i saymıyor. — İç tutarlılık — kanıt: architecture.md:593, :1840, `git diff --stat` | Kapandı. T-09 başvurusu §5.3/§5.6; T-01 uygulanışı tablosu genişletildi. |
| KM2-25 | [DÜŞÜK] docs/design/architecture.md:1698 — §18'deki eklenti satırında "AGPL-3.0 durumu" sütunu boş ve sonucun kaynağı yok. Araştırma D, eklentinin tescilli barındırıcıyla ilişkisini (kanca ve MCP süreçleri, skill metni) incelemedi. — Kaynaksız sonuç yok — kanıt: architecture.md:1675 (kaynak yalnız Araştırma D §3) | Kapandı. Eklenti satırına durum ve "Araştırma D incelemedi: yorum" notu eklendi. |
| KM2-26 | [DÜŞÜK] docs/design/architecture.md:693 — A11 yalnız skill ve ajan açıklamalarını ölçüyor. Kaynak, MCP sunucusunun tur başına eklediğini ayrıca anıyor ve yalnız modelin kendiliğinden çağırabildiği skill'leri sayıyor. Kullanıcı kapsamında kurulum da bu maliyeti kullanıcının bütün projelerine yayıyor. — Ölçütün kapsamı — kanıt: plugins/overview.md:51 | Kapandı. A11 MCP araç payını kapsar; kullanıcı kapsamının maliyeti bütün projelere yaydığı yazıldı. |
| KM2-27 | [DÜŞÜK] docs/design/architecture.md:1743 — "Desteklenen Claude Code sürüm aralığı eklentide yazılı" denmiş, ama eklenti bildiriminde Claude Code sürümü için bir alan yok; aralık yalnız `mekanik doctor` ya da bir kancayla denetlenebilir. — Kaynağından fazlasını söyleme — kanıt: plugins-reference.md:140-160 (alan tablosu) | Kapandı. Sürüm aralığı bildirimde değil, `mekanik doctor` ve `SessionStart` kancasıyla denetlenir. |
| KM2-28 | [DÜŞÜK] docs/design/architecture.md:1631 — 1.11'deki "`/plugin` ile görünür" denetimi etkileşimli ve elle yapılıyor; ölçülebilir karşılığı (`claude plugin validate`, `claude plugin list`) yazılmamış. — Ölçülebilirlik — kanıt: discover-plugins.md:82 "run `claude plugin list`" | Kapandı. 1.11 `claude plugin validate` ve `claude plugin list` ile ölçülür. |
| KM2-29 | [DÜŞÜK] docs/design/architecture.md:1834 — Karar saati "07:20" saat dilimi olmadan yazılmış; sistem saati UTC'de (`date` 07:35 UTC). 07:20'nin hangi komutla alındığı doğrulanmadı. — Saat sistemden alınır; saat dilimli ISO 8601 (§4.13) — kanıt: architecture.md:475 | Kapandı. Saat "07:20 UTC" ve alındığı yol yazıldı. |
| KM2-30 | [DÜŞÜK] docs/design/schemas/v1/examples/config.json:147 — `max_turns: 200`, `max_open_provisional: 5` (:199), `revert_window: 10` (:206) ve `max_questions_per_stage: 5` (:207) kaynak etiketi taşımıyor; aynı dosyada `revert_rate_threshold` ve `cache_limit` etiketli. Bu satırlar daha önce de vardı, ama §20.4'teki T-06 bu örneği dayanak gösteriyor. — Kaynaksız sayı yok — kanıt: examples/config.json:147, :199-207 | Kısmen. T-06 değerleri `decision` (baş mühendis, 2026-11-06) kaynağıyla kayda geçti; örnek ayar dosyasındaki tamsayı alanlar şemada kaynaklı değer (quantity) değil. Faz 1'de ayar şemasında bu alanlar için kaynak notu alanı değerlendirilecek. |
| KM2-31 | [DÜŞÜK] docs/design/architecture.md:600 — Kurulum komutuna kişisel hesap adı sabit yazılmış (`tahatas013/mekanik`; ayrıca :1383). — Kişiden bağımsızlık ilkesi; §17 4.5 — kanıt: architecture.md:600, :1383, :1668 | Kapandı. Kurulum komutları `<owner>/mekanik` (şimdilik tahatas013) biçiminde. |

Genel değerlendirme (2026-11-06 07:35 UTC): Baş mühendisin kararının özü işlenmiş: eklenti/kütüphane, marketplace, yerel kurulum ve isteğe bağlı başsız kip yerinde. Araştırma A §4a'daki 13 alıntının 13'ü belge metninde birebir var (yalnız bağlantı biçimi çıkarılmış) ve `check_examples.py` `SONUÇ: TEMİZ` veriyor. Buna karşın eklenti kipinde onay ve veri güvencesi kaynakların izin verdiğinden fazla vaat ediliyor. Terminalsiz/masaüstü yolu ve monitor'ün masaüstü ile VS Code'da çalışması doğrulanmadı. §20.4, proje mühendisinin çıkarımlarını ve karardan sonra yazılan eşikleri baş mühendis kararıymış gibi kaydediyor; kayıtta neyi baş mühendisin, neyi proje mühendisinin kararlaştırdığı ayrılmamış.
