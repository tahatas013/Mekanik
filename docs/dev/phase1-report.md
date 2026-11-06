# Faz 1 çıkış raporu

Yazan rol: proje-muhendisi · tarih: 2026-11-06 (sistem saati) · dal `phase-1` · ölçüm commit'i `1552c85`

Faz 1 kapsamı: çekirdek, `mech`, `print3d`, `analysis`, CLI, atölye ayarı, Claude Code eklenti iskeleti, taşıma betikleri (kuru çalıştırma). Kural: eşitlik, yani eski sistemin yaptığını yapmak, yeni özellik eklememek (architecture §17).

## 1. Kabul ölçütleri

| # | Ölçüt | Eşik | Sonuç | Kanıt |
| --- | --- | --- | --- | --- |
| 1.1 | Eski CLI işlevlerinin v1 karşılığı | %100, duman testli | **Geçti.** 21 eski komut ve `step --next`, `reply --commit` karşılıklı; `gate pass`, `verify`, `migrate`, `pkg list` eklendi | `tests/cli/test_commands.py::test_every_phase1_command_is_registered`; ikinci kalite incelemesi |
| 1.2 | Eski testlerin taşınması | 86 test | **Geçti.** 86/86 (docstring `old:` ile eşleşme) | eski `testler/` ile karşılaştırma betiği |
| 1.3 | Testsiz parçalara yeni test | Ek B §14 madde 1–12 için ≥ 12 | **Geçti.** 12 maddenin hepsinde test var; toplam 138 yeni test | docstring `new:` |
| 1.4 | Regresyon | 18/18; hep ENGEL / hep GEÇTİ sahte kontrol kalır | **Geçti.** S-001 10/10, H-001 8/8; vakaların kapsadığı her kontrolün sahte sürümü kalıyor | `tests/cases/test_cases.py` |
| 1.5 | Çekirdek temizliği | yasak sözcük 0, import ihlali 0, CLI'da katalog dışı Türkçe dize 0 | **Geçti** | `test_cleanliness.py`, `lint-imports` (2 sözleşme, 0 ihlal), `test_catalog_scan.py` |
| 1.6 | Şemalar | Faz 1 alt kümesi kesinleşir, örnek denetimi temiz | **Geçti.** 13 şema kesinleşti; 22 şema, 21 geçen örnek, 50 kalan bozuk örnek | `schemas/README.md`, `tests/core/schema_examples.py` |
| 1.7 | Taşıma | S-001 ve H-001 V1–V8 | **Geçti.** Gerçek `mekanik migrate surec-work --snapshot` komutuyla iki vaka V1–V8, çıkış 0 | `tests/migrate/`, ikinci kalite incelemesi |
| 1.8 | Bilinen hatalar | ilk ad yetkisi, `baski` KeyError, onay imzası testli | **Geçti.** İki eski hata testle kapalı; APPROVAL-02 GPG ile ve 9 saldırı testiyle sınandı. SSH yolu (T-17 b) baş mühendisin makinesinde sınandı: test takımı 352 geçti, 0 atlandı; `doctor` "onay imzası: deneme imzası onaysız atılamadı (kullanım başına onay var)" | `test_approval.py`, `test_approval_attacks.py`, `tests/flow/test_cli_release.py`, `docs/dev/phase1-exit-check.md` |
| 1.9 | Boyut bütçesi | `src/` + `packages/` ≤ 6 560 satır | **Geçti.** 6 558 | `find src packages -name '*.py' \| xargs wc -l` |
| 1.10 | Çekirdek testleri OCCT'siz | ≤ 60 s | **Geçti.** 120 geçti, 2 atlandı, 15 s | `UV_PROJECT_ENVIRONMENT=.venv-core uv run --no-group pkgs pytest tests/core` |
| 1.11 | Eklenti iskeleti | validate hatasız, yüklenir, kanca testleri, 5 negatif PreToolUse testi | **Geçti.** `claude plugin validate --strict` geçti; `--plugin-dir` ile yüklendi; 39 negatif durum | `tests/agent/` |

Bütün test takımı: **351 geçti, 1 atlandı**, hem TR hem EN katalogla. Atlanan test SSH imza testidir (kapsayıcıda `ssh-keygen` yok). Testler sahte katalogla da koşuyor (`tests/tools/test_pseudo_i18n.py`), yani metne değil anahtara bakıyor.

## 2. Kalite incelemesi

İşi yapan kendi işini onaylamaz; iki bağımsız kalite incelemesi yapıldı.

- **Birinci inceleme (temiz bağlam):** 25 bulgu verdi, 5'i YÜKSEK. YÜKSEK olanların hepsi onay güvenliğiyle ilgiliydi: aynı kullanıcıyla çalışan ajan, imza denetimini sahte `gpg` programıyla, ilgisiz bir imzalı commit'le, baş mühendisin kaydını silerek ya da git kancasıyla atlatabiliyordu; G0–G2 kapıları da geçersiz onayla geçiyordu. Hepsi düzeltildi. Her biri, önce eski kodda kalan sonra düzeltmeyle geçen bir saldırı testine dönüştü. Ölçütlerden 1.1, 1.7 ve 1.8 kalmıştı; üçü de kapandı.
- **İkinci inceleme (temiz bağlam, düzeltmeler üzerine):** 1.1, 1.7 ve 1.8 geçti; 1 ORTA, 3 DÜŞÜK bulgu verdi.
  - ORTA bulgu kapandı: geçilmiş kapı ve çıkmış baskı artık imzalı onay olmadan geçerli görünmüyor.
  - DÜŞÜK bulgulardan veri kapısının iç içe girdileri taraması kapandı.
  - Kalan iki DÜŞÜK bulgu `docs/later.md`'de: değer girişi commit'inin imzasız olması ve trailer ayrıştırıcısının yalnız son paragrafı okuması.

Bulguların tamamı ve her birinin kapanışı commit mesajlarında (`f1f000e`, `c4bd189`, `1552c85`).

## 3. Eski davranıştan bilerek ayrılan yerler

Hepsi `docs/dev/phase1-guide.md` §3 (G-24…G-31) ve §9.2'de gerekçesiyle yazılı. Senin göreceğin başlıcaları:

- Kaynaksız parametre artık şemada da tanınır. Eskisi gibi yükleme durmaz, SOURCE-01 ENGEL verir (G-25).
- Onay isteyen bütün kartlar "DUR" seviyesindedir. Geçici karara dönüşmeleri Faz 2'nin politika motorundadır (G-31).
- Onay yalnız ad ve e-postanın tam eşleşmesiyle ve imzayla geçerlidir. Kapı geçişi ve karar sonucu senin imzalı onay commit'ine girer.
- G0 kapı kartı `work new`'da değil `stage finish G0`'da açılır.
- Tabla ölçüsü makine profilinden okunur. Baskı tahmini değerleri bir veri dosyasındadır; makine profilinde değer varsa o kullanılır.
- Ölçme aletinin sürüm sabitlemesi kalktı. Onay özetine aletin belirsizliği girer; alet değeri değişince onay yine düşer.

## 4. Kalan riskler (bilinerek kabul; mimari belgede yazılı)

- **Atölye ayarı:** eklenti kipinde aynı kullanıcıyla çalışan ajan atölye ayarını değiştirebilir (§4.6 m.4). Önlemler: engel listesi, `gate pass` ve `verify`'ın imza anahtarı parmak izini sana göstermesi, GPG anahtarında `doctor`'un kırmızı vermesi.
- **Kalite raporu:** kayıt ana oturumdan gelir; ana ajan "bulgu yok" yazabilir (§4.8). Eski sistemde de ajan rapor dosyasını yazabiliyordu. Faz 2'de rapor alt ajanın çıktısına bağlanacak.
- **SSH imza yolu:** kapsayıcıda sınanamadı. Senin makinende sınanacak.

## 5. Baş mühendisin makinesindeki denetim (2026-11-06)

`docs/dev/phase1-exit-check.md` adımlarıyla, Ubuntu masaüstünde:

- `pytest tests`: **352 passed** (0 atlanan; kapsayıcıda atlanan SSH imza testi burada çalıştı).
- `mekanik doctor`: **YEŞİL · 0 HATA · 0 UYARI · 1 BEKLİYOR**. Onay penceresi masaüstünde açıldı ve baş mühendis reddetti (T-24). Onay imzası satırı: "deneme imzası onaysız atılamadı (kullanım başına onay var)". Bekleyen tek madde isteğe bağlı orca-slicer.
- Not: freecad satırı sürüm yerine bir Wayland hata metni gösterdi ama TAMAM saydı. doctor'ın sürüm ayrıştırması düzeltilecek (`docs/later.md`).

## 6. Faz 1 çıkışı için kalan

1. ~~Senin makinende denetim~~: yapıldı (§5).
2. ~~Senin onayın~~: verildi (2026-11-06 16:09 UTC, T-24): onay penceresi açıldı ve reddedildi; `phase-1` `main`'e birleşti.

Faz 2'ye kalanlar `docs/later.md`'de.
