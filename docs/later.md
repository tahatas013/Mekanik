# Sonraya kalanlar

Faz 1'de "yeni fikir koda değil buraya" kuralıyla (§19.1) ve Faz 1 ajan raporlarından toplananlar. Her madde hangi faza düştüğüyle; dayanağı yanında.

| Konu | Faz | Dayanak |
| --- | --- | --- |
| Baş mühendisin değer girişi (`chief.value`) `value_change` onay kaydı ve imzalı commit ile yazılsın; Faz 1'de eski gibi imzasız ama baş mühendis kimliğiyle | 2 (panel) | §4.6, D raporu |
| Kapanmış kararın görseli için model kodu da onay sürümünden alınsın (E-21); Faz 1'de yalnız parametreler | 2 | D raporu |
| `generate` model notu kartında `closed` durumunu korusun | 2 | D raporu |
| Seçenek çizimleri birbirinin aynıysa mech nedenini bildirsin | 3 | D raporu |
| agent-run şemasına isteğe bağlı `last_event {hook, at, message}` | 2 | E raporu |
| Oturum kilidi (A8), gelen kutusu, `mekanik agent send/stop`, Stop kancasının engellemesi | 2 | §5.4, §4.11 |
| Eklentinin öbür skill'leri (setup, resume, new, intake, gate), `userConfig`, simge | 2–4 | §5.4 |
| SSH imza yolunun (T-17 b) gerçek makinede sınanması: bu kapsayıcıda `ssh-keygen` yok; kod ve atlanan test hazır | Faz 1 çıkışı, baş mühendisin makinesi | A raporu |
| EN katalogları (çekirdek bölümleri ve paketler) | 4 | §4.12 |
| Gerçek taşımada eski taraf görüntüsü (`tests/migrate/old_probe.py`) ve V4 bilinen farklar listesinin test dışındaki yeri | 2 (`--apply`) | F, E2 raporları |
| Kanca çağrısı ~150–180 ms; ayarın her çağrıda doğrulanması önbelleğe alınabilir | 2 | E raporu |
| Şema sıkılığı listesinin boşaltılması (`stdlib/strictness/phase1.yaml`), şema 1.1 | 2 | G-27 |
| Monitor bağlaması (`plugin/monitors/monitors.json`: `mekanik watch` bildirimlerini oturuma iletir) | 2 | §17 2.1, KF1-15 |
| Kalite incelemesi kaydının alt ajan çıktısına bağlanması (`SubagentStop` kancasının yakaladığı çıktının özeti) | 2 | §4.8, KF1-16 |
| Atölye ayarının (özellikle `chief_signing_key`) değişikliğe karşı korunması: imzalı ayar ya da anahtarın ayrı yerde sabitlenmesi | 2 | §4.6 m.4, KF1-07 |
| v1'e özgü regresyon vakası S-002: APPROVAL-02, DECISION-02, CARD-01, QUALITY-01 için geçen ve kalan alt vakalar | 2 | KF1-17 |
| Testlerin sahte katalogla (pseudo-locale) bütün takımda koşması; EN kataloğunun tamamlanması | 2–4 | §3.1, KF1-11 |
| Taşınan çalışmanın eski kapı geçişleri: Faz 1'de APPROVAL-02 her `done` kapı için imzalı O-Gn onayı ister; `--apply` ile taşınan geçmiş kapılar MG-01'in imzalı onayıyla kapsanmalı (gate_status'ta taşındı işareti) | 2 (`--apply`) | QE2 |
| `trailers()` yalnız son paragrafı okur; gövdedeki `Card:` satırı kullanılmış numara sayılmaz (zararsız: en çok bir numara harcar) | 2 | QE2 (DÜŞÜK) |
