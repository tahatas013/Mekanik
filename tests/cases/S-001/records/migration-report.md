# Taşıma raporu · TST-SYN-01

Kuru çalıştırma (Faz 1). Eski kayıtlar değiştirilmedi; yeni dosyalar bu klasörde. Gerçek taşıma (--apply) Faz 2'dedir ve V1–V8 geçmeden çalışmaz (architecture §14.3).

| V | Durum | Ayrıntı |
| --- | --- | --- |
| V1 | GEÇTİ | — |
| V2 | GEÇTİ | — |
| V3 | GEÇTİ | — |
| V4 | GEÇTİ | — |
| V5 | GEÇTİ | — |
| V6 | GEÇTİ | — |
| V7 | GEÇTİ | — |
| V8 | GEÇTİ | — |

## Taşıma eksikleri (migration_gap) (48)

- `work.yaml` · `purpose`
- `work.yaml` · `done_criterion`
- `work.yaml` · `opened_at`
- `work.yaml` · `work_type` — öneri: `new_part`
- `work.yaml` · `packages` — öneri: `['mech', 'print3d']`
- `work.yaml` · `stdlib`
- `decisions.yaml` · `0/category`
- `decisions.yaml` · `0/options`
- `decisions.yaml` · `0/rationale`
- `decisions.yaml` · `0/opened_at`
- `decisions.yaml` · `1/category`
- `decisions.yaml` · `1/options`
- `decisions.yaml` · `1/rationale`
- `decisions.yaml` · `1/opened_at`
- `decisions.yaml` · `1/chosen`
- `decisions.yaml` · `1/approved_version`
- `decisions.yaml` · `2/basis/0/at`
- `decisions.yaml` · `2/category`
- `decisions.yaml` · `2/options`
- `decisions.yaml` · `2/rationale`
- `decisions.yaml` · `2/opened_at`
- `decisions.yaml` · `2/chosen`
- `decisions.yaml` · `2/approved_version`
- `decisions.yaml` · `3/basis/0/at`
- `decisions.yaml` · `3/category`
- `decisions.yaml` · `3/options`
- `decisions.yaml` · `3/rationale`
- `decisions.yaml` · `3/opened_at`
- `decisions.yaml` · `3/chosen`
- `decisions.yaml` · `3/approved_version`
- `approvals.yaml` · `0/commit`
- `approvals.yaml` · `0/signature`
- `approvals.yaml` · `0/channel`
- `records/calcs/h_elle.json` · `purpose`
- `records/calcs/h_elle.json` · `method` — öneri: `{'name': 'elle', 'level': 1}`
- `records/calcs/h_elle.json` · `validity`
- `records/calcs/h_elle.json` · `input_hash`
- `records/calcs/h_elle.json` · `ran_at`
- `records/calcs/h_elle.json` · `code`
- `records/calcs/h_elle.json` · `results/0/uncertainty_note`
- `records/calcs/h_vlm.json` · `purpose`
- `records/calcs/h_vlm.json` · `method` — öneri: `{'name': 'VLM', 'level': 2}`
- `records/calcs/h_vlm.json` · `validity`
- `records/calcs/h_vlm.json` · `input_hash`
- `records/calcs/h_vlm.json` · `ran_at`
- `records/calcs/h_vlm.json` · `code`
- `records/calcs/h_vlm.json` · `results/0/uncertainty_note`
- `cards/MG-01.yaml` · `visuals`

## Eski kuralla türetilenler (18)

- `work.yaml` · `org` — çalışma kodundan (<KURUM>-<PROJE>-<nn>)
- `work.yaml` · `project` — çalışma kodundan (<KURUM>-<PROJE>-<nn>)
- `work.yaml` · `process/profile` — eski süreç (el kitabı §5–§6) = default@1
- `work.yaml` · `process/gates` — eski SINIF_KAPILARI kuralı: kapılar sınıftan
- `work.yaml` · `model` — model/model.py var: parametrik model
- `decisions.yaml` · `0/mode` — eski karar baş mühendis incelemesi ister: Dur (hold)
- `decisions.yaml` · `0/requirement_effects` — istek listesi yok: etkilenen istek yok (boş liste)
- `decisions.yaml` · `1/mode` — eski karar baş mühendis incelemesi ister: Dur (hold)
- `decisions.yaml` · `1/requirement_effects` — istek listesi yok: etkilenen istek yok (boş liste)
- `decisions.yaml` · `2/mode` — eski karar baş mühendis incelemesi ister: Dur (hold)
- `decisions.yaml` · `2/requirement_effects` — istek listesi yok: etkilenen istek yok (boş liste)
- `decisions.yaml` · `3/mode` — eski karar baş mühendis incelemesi ister: Dur (hold)
- `decisions.yaml` · `3/requirement_effects` — istek listesi yok: etkilenen istek yok (boş liste)
- `decisions.yaml` · `3/basis/0/result_hash` — eski değer v1 desenine uymuyor; SHA-256 özetiyle yazıldı (eski: eski-sonuc-ozeti)
- `approvals.yaml` · `0/role` — eski onay yetkilisi baş mühendis
- `approvals.yaml` · `0/identity` — kim → atölye ayarındaki baş mühendis kimliği (§14.2)
- `records/calcs/h_elle.json` · `result_hash` — eski hesap.ozet_metinden kuralıyla kayıttan (B5)
- `records/calcs/h_vlm.json` · `result_hash` — eski hesap.ozet_metinden kuralıyla kayıttan (B5)

## Taşınmayan eski alanlar (0)

- —

## Eşlenmeyen değerler (0)

- —

## Bekleyen adımlar (0)

- —

> Sınama vakası: tests/migrate/build_cases.py ile üretildi; v1'de zorunlu olup eskide olmayan alanlar stdlib/strictness/phase1.yaml'a göre uyarıdır (G-27).
