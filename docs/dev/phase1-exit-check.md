# Faz 1 çıkışı: baş mühendisin makinesinde denetim

Bu adımlar bulut kapsayıcısında yapılamadı: orada `ssh-keygen` ve `ssh-add` yok. Bu yüzden T-17 (b), yani SSH anahtarıyla kullanım başına onaylı imza, ancak senin Ubuntu makinende sınanabilir. Hiçbir adım gerçek atölye ayarına (`~/.config/mekanik`) ya da iş repolarına yazmaz; ayar geçici bir kopyadadır.

Toplam süre yaklaşık 10 dakika. `sudo` isteyen tek adım 3'tür.

## 1. Kodu al

```bash
git clone -b phase-1 https://github.com/tahatas013/Mekanik.git ~/mekanik-faz1
```

```bash
cd ~/mekanik-faz1 && uv sync
```

## 2. Testler (SSH testi burada atlanmamalı)

```bash
cd ~/mekanik-faz1 && MEKANIK_CONFIG_DIR=tests/fixtures/config uv run pytest tests -q -p no:warnings
```

Beklenen: hepsi geçer, **0 atlanan** (kapsayıcıda atlanan `test_ssh_signed_approval_valid` burada çalışır). Son satırı bana yaz.

## 3. Onay penceresi programı (sudo; sen çalıştır)

```bash
sudo apt install ssh-askpass
```

## 4. Onay anahtarı ve kullanım başına onay

Yeni bir anahtar üret (parola koyman önerilir):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mekanik_onay -C "mekanik onay"
```

Bu terminalde ayrı bir ssh-agent aç ve anahtarı `-c` ile ekle. `-c`, her imzada onay penceresi demektir:

```bash
eval "$(SSH_ASKPASS=/usr/bin/ssh-askpass ssh-agent -s)"
```

```bash
ssh-add -c ~/.ssh/mekanik_onay
```

Parmak izini al (`SHA256:` ile başlayan kısım):

```bash
ssh-keygen -lf ~/.ssh/mekanik_onay.pub
```

## 5. Geçici atölye ayarı

```bash
cp -r ~/mekanik-faz1/tests/fixtures/config ~/.cache/mekanik-faz1-config
```

`~/.cache/mekanik-faz1-config/config.yaml` dosyasında üç değeri değiştir:
- `identities.chief.name` ve `identities.chief.email`: `git config --global user.name` ve `user.email` ile aynı;
- `identities.chief_signing_key`: 4. adımdaki `SHA256:…` parmak izi.

## 6. doctor: onay penceresini REDDET

```bash
cd ~/mekanik-faz1 && MEKANIK_CONFIG_DIR=~/.cache/mekanik-faz1-config uv run mekanik doctor
```

doctor bir deneme imzası ister ve masaüstünde onay penceresi açılır. **Reddet.** Beklenen satır: kimlik grubunda imza anahtarı **yeşil** ("deneme imzası reddedilebildi"). Kırmızı çıkarsa, yani pencere açılmadan imza atıldıysa, ajanın onaysız imza atabildiği anlaşılır; o zaman Faz 1 çıkışı olmaz.

Not: GNOME'un kendi anahtar ajanı `-c`'yi desteklemeyebilir (Faz 0'da doğrulanmadı). Bu yüzden 4. adımda ayrı bir ssh-agent açıyoruz. Pencere hiç açılmazsa ya da hata çıkarsa çıktıyı bana yaz.

## 7. Bana dönüş

1. 2. adımın son satırı.
2. 6. adımın kimlik satırları.
3. Pencere açıldı mı, reddedince doctor ne dedi?

Bunlar beklendiği gibiyse Faz 1 çıkış raporu tamamlanır ve `phase-1` dalının `main`'e alınması için onayını isterim.

## Temizlik (isteğe bağlı)

```bash
rm -rf ~/mekanik-faz1 ~/.cache/mekanik-faz1-config
```

Anahtar (`~/.ssh/mekanik_onay`) kalabilir: v1'de onayların imza anahtarı olacak. Kalıcı ssh-agent kurulumu Faz 4'te (`mekanik init`).
