# Taşıma raporu · TST-SYN-02

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

## Taşıma eksikleri (migration_gap) (6)

- `work.yaml` · `done_criterion`
- `work.yaml` · `opened_at`
- `work.yaml` · `work_type`
- `work.yaml` · `packages` — öneri: `['mech', 'print3d']`
- `work.yaml` · `stdlib`
- `cards/MG-01.yaml` · `visuals`

## Eski kuralla türetilenler (4)

- `work.yaml` · `org` — çalışma kodundan (<KURUM>-<PROJE>-<nn>)
- `work.yaml` · `project` — çalışma kodundan (<KURUM>-<PROJE>-<nn>)
- `work.yaml` · `process/profile` — eski süreç (el kitabı §5–§6) = default@1
- `work.yaml` · `process/gates` — eski SINIF_KAPILARI kuralı: kapılar sınıftan

## Taşınmayan eski alanlar (0)

- —

## Eşlenmeyen değerler (0)

- —

## Bekleyen adımlar (0)

- —

> Sınama vakası: tests/migrate/build_cases.py ile üretildi; v1'de zorunlu olup eskide olmayan alanlar stdlib/strictness/phase1.yaml'a göre uyarıdır (G-27).
