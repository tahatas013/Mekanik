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
