# Regresyon vakaları (`tests/cases/`)

Her klasör dondurulmuş bir v1 çalışmasıdır ve `mekanik.core.checks.regress`in girdisidir (el kitabı §10, eski
`surec_cekirdek/regresyon.py`). `S-001` ve `H-001`, eski biçimdeki sentetik vakalardan (`tests/fixtures/surec/`)
taşıma betiğiyle (`mekanik.migrate.surec_work`, kuru çalıştırma) üretilir; elle düzeltilmez:

```bash
MEKANIK_CONFIG_DIR=tests/fixtures/config uv run python tests/migrate/build_cases.py
```

Vaka klasöründe taşımanın bütün çıktısı durur: `work.yaml`, `params.yaml`, `fits.yaml`, `decisions.yaml`,
`approvals.yaml`, `replies.yaml`, `cards/MG-01.yaml` (taşıma eksikleri kartı), `model/`, `records/calcs/`,
`records/migration.yaml` (eksikler, türetilenler, taşınmayanlar) ve `records/migration-report.md` (V1–V8).

Not (Faz 1): taşınan çalışmada v1'de zorunlu, eskide karşılıksız alanlar eksiktir (taşıma eksikleri). Bunların bir
kısmı `stdlib/strictness/phase1.yaml` listesinde yok (`work`: `purpose`, `done_criterion`, `opened_at`; `decision`:
`chosen`, `approved_version` ve iç içe `basis/<n>/at`); liste genişleyene kadar `load_work` bu vakaları yüklemez.
`build_cases.py` vakaları bu eki taklit ederek üretir ve raporun sonuna bunu yazar.

## `expected.yaml`

Eski `beklenen.yaml`ın v1 karşılığı. Alanlar İngilizce; açıklama metni kayıt dilinde (Türkçe) kalır.

```yaml
code: TST-SYN-01                 # vaka çalışmasının kodu (work.yaml code)
subcases:
  - id: kaynaksiz                # eski alt vaka no (etiket)
    description: "etiketsiz x_et kalır, kumpas ölçüsü geçer"
    expect:                      # her biri: o kontrolün o ref için sonuçları
      - {check: source, ref: x_et, result: block}
      - {check: mech.fit_clearance, ref: G-01, result: pass, value: 0.3}
      - {check: uncertainty, ref: G-01, param: a_delik_cap, result: pass}
    cards:                       # üretilen kartlarda bu anahtar açılmış olmalı
      - {key: "uncertainty:caliper", trigger: borderline}
```

| Alan | Anlamı (eski regresyonla aynı) |
| --- | --- |
| `check` | v1 kontrol kimliği (`Result.check`; guide §2.3: `kaynaksiz → source`, `gecme_boslugu → mech.fit_clearance` …) |
| `ref` | `Result.ref` (param adı, geçme/esneme/karar no, parça çifti `C-D`, kart no); `null` olabilir |
| `param` | isteğe bağlı: yalnız `Result.extra["param"]` bu olan sonuçlar sayılır (eski `ek.param`, UNCERT-01) |
| `result` | `block`: en az bir ENGEL · `fail`: en az bir ENGEL ya da UYARI (eski `KALDI`) · `pass`: o kontrolün o ref için sonucu var ve hepsi GEÇTİ |
| `value` | isteğe bağlı: sonuçlardan birinin `Result.value` değeri bununla 1e-9 içinde aynı |
| `cards[].key` | v1 kart anahtarı (`fit:G-04`, `flex:E-01`, `assumption:<param>`, `measured:<param>`, `uncertainty:<alet>`, `consistency:<büyüklük>`, `basis:K-04`) |
| `cards[].trigger` | isteğe bağlı: kartın `triggers` listesinde bu olmalı (`assumption`, `borderline`, `assembly_flex` …) |

Sonuç yoksa (`ref` için hiç sonuç üretilmemişse) beklenti kalır. "Hep ENGEL" ve "hep GEÇTİ" sahte kontrolleri
her vakada en az bir beklentiden kalır (her kontrol için hem geçen hem kalan durum vardır).
