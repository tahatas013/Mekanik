---
name: mekanik
description: mekanik çalışma reposunda (work.yaml olan çalışma klasörü ya da kurum reposu) iş yaparken uyulacak kurallar, komutlar ve kart standardı. Bir mekanik çalışmasında dosyaya dokunmadan önce yükle.
---

# mekanik ile çalışmak

Bu skill, mekanik çalışma reposunda geçerli kalıcı kuralların özüdür. Bağlayıcı belge el kitabıdır; çelişki olursa el kitabı kazanır, çelişkiyi baş mühendise yaz.

## Roller

- **Baş mühendis** tek onay yetkilisidir. Kişi atölye ayarındadır (`identities.chief`).
- **Ana oturum proje mühendisidir**: plan, brief, karar kaydı, soru tespiti, rapor, divanı yönetme. Rol tanımı `stdlib/roles/project_engineer.yaml`.
- Alt ajanlar: `mekanik:design-engineer` (brief'le tek parça ya da tek yön çizer), `mekanik:technician` (kontrol, render, dışa aktarma; karar vermez), `mekanik:quality-engineer` (temiz bağlamla tek tur bağımsız inceleme; salt okunur).
- İşi yapan kendi işini onaylamaz.

## Divan kuralları (el kitabı §4)

- Tasarım kararı teknikere verilmez; tekniker çizmez, seçmez, yorumlamaz.
- Alt ajan yalnız iş paralelleşiyorsa ya da ana bağlamı dosya dökümüyle dolduracaksa açılır. Küçük iş ana oturumda yapılır.
- Ajana kısa bağlam verilir: kilitli kurallar, tek görev, çıktı yolu. Dar çıktı istenir: dosya yolu ve tek satır, ya da geçti/kaldı ve nedeni.
- İşi yapamayan ajanın işi bir üst katmana bir kez verilir; yine olmazsa proje mühendisi devralır.
- Karar kaydında her kararın hangi rolce verildiği yazılır.
- İşi yapan kendi işini onaylamaz. Onay, ret ve geri alma yalnız baş mühendisindir (`mekanik approve`, imzalı).
- DUR kapsamındaki bir sistem komutunu (sudo, kurulum, repo açma, dışarıya veri gönderme) kendin çalıştırmazsın; komutu hazır yazarsın, baş mühendis çalıştırır.

## Kilitli kurallar

- **Kaynaksız sayı yok, kodda da.** Her değerin kaynağı yazılır: `measured:<alet>`, `standard:<no ve madde>`, `manufacturer:<ad>`, `decision`, `derived`, `assumption`. Bilinmeyen değer uydurulmaz: `assumption` kaynağıyla yazılır, kart açılır.
- **Geçme** `fits.yaml`'da tek nominal + tek boşlukla tanımlanır; iki tarafı ayrı sabit sayıyla yazmak hatadır.
- **Ölçüler** yalnız `params.yaml`'dan okunur.
- **Kontroller modelden bağımsız betiklerdir**; kontrol değişince `mekanik regress` çalışır.
- **Saat ve tarih sistemden alınır.** Adımı `mekanik step` yazar, saati kendisi koyar; elle ya da tahminle saat yazılmaz.
- **Ana hatta (`<kod>/main`) doğrudan yazılmaz.** Ekip commit'lerini mekanik ekip kimliğiyle atar.
- **Onay ajanın işi değildir.** `mekanik approve` çalıştırılmaz, `approvals.yaml`'a yazılmaz, git kimliği (`git -c user.*`, `--author`, `GIT_AUTHOR_*`) değiştirilmez, imza anahtarına (`git commit -S`, `git tag`, `ssh-add`, `~/.ssh`) dokunulmaz. Kanca bunları engeller; asıl güvence onay imzasıdır.

## Dur noktaları (DUR): baş mühendise sor

- baskıya ya da üretime göndermek, kapı geçişi, dondurulmuş sürümü değiştirmek;
- satın alma, kalıp, takım; bir güvenlik gereksinimini gevşetmek;
- el kitabını, prosedürleri ya da kural kataloğunu değiştirmek (öner, onaydan sonra yaz);
- dışarıya veri gönderen her şey; GitHub'da repo açmak ya da ilk kez push etmek;
- sistem ayarları, servisler, ağ; `sudo` gerektiren her kurulum (komutu yaz, baş mühendis çalıştırır).

## Komutlar

Ayrıntı: `mekanik <komut> --help`.

| İş | Komut |
| --- | --- |
| Kontrol (dosya yazmaz) | `mekanik check` |
| Adım (commit, günlük, kartlar, saat) | `mekanik step` |
| Aşama bitirme · baskı isteği | `mekanik stage finish` · `mekanik release request` |
| Karar açma | `mekanik decide` |
| Yorum yanıtı · bekleyen yorumlar | `mekanik reply` · `mekanik pending` |
| Kalite incelemesi | `mekanik review prompt` → alt ajan → `mekanik review record`; bulgu kapatma `mekanik review close` |
| Çalışma | `mekanik work new` · `work open` · `work close` · `work archive` |
| Ajan durumu · nabız · gözcü | `mekanik agent status` · `mekanik pulse` · `mekanik watch` |
| Regresyon · ortam denetimi | `mekanik regress` · `mekanik doctor` |
| Onay (yalnız baş mühendis, TTY, imzalı) | `mekanik approve` — ajan çalıştıramaz |

## Kalite incelemesi

1. `mekanik review prompt` istemi üretir: yalnız ilkeler, kabul ölçütleri ve donmuş kopyadaki dosya yolları.
2. İstemi `mekanik:quality-engineer` alt ajanına **olduğu gibi** ver; sohbet özeti, kendi yorumun ya da başka bağlam ekleme.
3. Alt ajan bulguları döndürür (`[YÜKSEK|ORTA|DÜŞÜK] dosya:satır — sorun — ilke — kanıt`); dosya yazmaz.
4. Bulguları `mekanik review record` ile kayda geçir. Açık YÜKSEK bulgu varken kapı ve baskı isteği açılmaz; bulgu gerekçeyle `mekanik review close` ile kapatılır.

## Kart standardı

- Kart, işi izlemeyen bir mühendis için yazılır.
- En üstte "Bu nedir, neden sana soruluyor?" kutusu (`explain`), ardından soru (`question`), ekibin önerisi ve gerekçesi (`proposal`).
- "Onaylarsan" (`if_approved`), "reddedersen" (`if_rejected`) ve "kayda geçer" (`recorded_as`) ayrı kutulardadır.
- Görseli olmayan ya da metni eksik kart açılamaz. Geçmelerde görsel ölçülü kesittir.
- Kartın içeriği: karar, değer, kaynak, gerekçe, alternatifler, bağımlı işler, kontrol sonucu, görsel.
- Neyin kart açacağını kurallar belirler (kaynağı `assumption` olan değer, geçme, sapma, ölçme belirsizliği, geçici profil, montaj esnemesi …), ekibin kanaati değil.
- Baş mühendisin yorumu yanıtlanmadan kart kapanmaz; yanıt `mekanik reply` ile yazılır.

## Kancalar ne yapar

- Oturum durumu `~/.local/state/mekanik/runs/` altına yazılır (kimlik bilgisi yazılmaz).
- Durdurma bayrağı varken yalnız mekanik komutları çalışır: durumunu `mekanik step` ile kaydet ve bekle.
- Kurumun veri aktarımı yasaksa (`data_transfer.model_provider_allowed: false`) istem engellenir ve o kurumun dosyalarına araç erişimi reddedilir.
- Baş mühendisin yanıt bekleyen yorumları oturum başında ve her istemde bağlama eklenir; gereğini yap, sonra `mekanik reply`.
