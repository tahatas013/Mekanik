# surec (eski sistem) · bağımlılık envanteri → v1 katmanları

Üretildi: 2026-11-06 06:08 (sistem saati) · repo `/home/user/surec`, HEAD `d26af89` (2026-10-27) · yalnız okundu, hiçbir dosya değiştirilmedi.
Kapsam: git'teki 138 dosyanın metin olanları (uv.lock, package-lock.json, *.png, .git/ hariç). İzlenmeyen dosya yok.

**Hedef katman kısaltmaları**

| Kısaltma | Katman |
| --- | --- |
| **Ç** | (1) çekirdek: süreç motoru, CLI, panel, ajan rolleri |
| **Ç-i18n** | (1) çekirdeğin ileti kataloğu (tr varsayılan, öteki diller dosyayla) |
| **AP:fdm · AP:cad · AP:aero · AP:fea** | (2) alan paketi (eklenti) |
| **SK** | (3) standart kütüphanesi: madde, kural, dayanak |
| **AT** | (4) atölye ayarı: `~/.config/<ad>/` (kişi, git kimliği, makine, ölçüm aleti, kurum, yol) |
| **ÇV** | (5) çalışma verisi: kurum başına ayrı repo |
| **PA** | platform adaptörü (Ubuntu, systemd, tmux, Tailscale, XDG yolları) |
| **AA** | ajan adaptörü: Claude Code (ajan arayüzünün arkasında) |
| **KALDIR** | v1'de yeri yok |

Yöntem: kategori başına grep; şüpheli eşleşmede satırın bağlamı okundu. Yanlış eşleşmeler §11'de. Bitişik satırlar tek satırda aralıkla verildi. "Yer" = tablodaki bir satır (tek satır ya da bitişik blok).

## Özet

| Kategori | Yer sayısı (kayit/ dışı) | kayit/ içinde eşleşen satır (yaklaşık) | Baskın hedef katman |
| --- | --- | --- | --- |
| 1. Kişi | 45 | 36 | AT |
| 2. Makine ve yollar | 46 | 52 | AT (yollar, port) · PA (XDG) |
| 3. Ubuntu ve işletim sistemi | 13 | 38 | PA |
| 4. tmux · Tailscale · Remote Control | 32 | 31 | PA (Remote Control: AA) |
| 5. Üstteknik | 22 | 41 | ÇV · KALDIR (geçiş) |
| 6. Belirli alan (FDM 41, CAD 15, aero 11, tarama 14, FEA 3) | 84 | 78 | AP:fdm · AP:cad (tarama: AT + SK) |
| 7. Claude Code'a özgü | 30 | 27 | AA |
| 8. Kurum kodları ve sabit çalışma kodları | 23 | 46 | AT (kod) · Ç (örnek nötrleşir) |
| 9. Türkçe'ye sabit arayüz metinleri | 56 dosya/grup satırı (≈1320 metin satırı) + 18 anahtar/biçim yeri | — | Ç-i18n |

Kategori 9'da asıl ölçü metin satırıdır: kod dosyalarında ≈1085, testlerde ≈237 satır; ayrıca 4 belge grubu (el kitabı, ajan istemleri, kural kataloğu, profil/kurum yorumları).

---

## 1. Kişi (Taha, Taha Ataş, tahatas013, e-posta, baş mühendis ↔ kişi)

"Baş mühendis" rolünün kendisi çekirdekte kalır; sorun rolün kişi adına, makinenin git kimliğine ya da kişisel hesaba bağlandığı yerlerdir.

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `CLAUDE.md:7` | Baş mühendis: **Taha**. Tek onay yetkilisi. | rol ↔ kişi | AT | dosyanın kendisi AA (§7) |
| `CLAUDE.md:39` | Dur noktaları (Hold): mutlaka Taha'ya sor | kişi adı | AT | Hold listesi "onay yetkilisi"ne |
| `CLAUDE.md:44` | `sudo` gerektiren her kurulum (komutu yaz, Taha çalıştırır) | kişi adı | AT | |
| `CLAUDE.md:59` | `surec-ekip <ekip@surec.local>` … `Taha Ataş` kimliği yalnız panelden… | git kimliği, e-posta | AT | ekip kimliği de ayar |
| `el-kitabi.md:3` | Sürüm 0.2 (onaylayan Taha; …) · @Taha | belge onaylayanı | AT | belge meta verisinde rol yazılır |
| `el-kitabi.md:76` | \| Baş mühendis \| Taha \| Onay, ret, müdahale… | rol ↔ kişi | AT | |
| `kurumlar/bag/kurum.yaml:4` | onay_yetkilisi: Taha | kurum → kişi | AT | `onay.py:107` okur |
| `kurumlar/ust/kurum.yaml:4` | onay_yetkilisi: Taha | kurum → kişi | AT | |
| `kurumlar/ust/kurum.yaml:5` | repo: tahatas013/ustteknik-arge | kişisel GitHub hesabı | AT | |
| `kurallar/katalog.yaml:5` | onaylayan: Taha | kütüphane onaylayanı | SK | adı atölyeden, kütüphanede sürüm |
| `kurallar/katalog.yaml:66` | sinir: "çap farkı < 3 mm (karar: Taha, PROMPT §3.1)…" | dayanak = kişi | SK | dayanak karar numarası olmalı |
| `profiller/olcum/iphone-lidar-kiri.yaml:6` | onaylayan: Taha | profil onaylayanı | AT | |
| `profiller/olcum/kumpas.yaml:6` | onaylayan: Taha | profil onaylayanı | AT | |
| `profiller/uretim/fdm-bambu-a1-pla.yaml:11` | onaylayan: Taha | profil onaylayanı | AT | |
| `profiller/uretim/fdm-cr10se-pla.yaml:13` | onaylayan: null # baş mühendis onaylayınca adı yazılır | rol → ad alanı | AT | |
| `cekirdek/surec_cekirdek/git.py:3-4` | …verdiği kararlar git'in genel kimliğiyle (Taha) atılır. | belge | Ç | yorum temizlenir |
| `git.py:16` | EKIP = ("surec-ekip", "ekip@surec.local") | sabit ekip kimliği, e-posta | AT | Ç'de varsayılan, ayardan ezilir |
| `git.py:37-43` | def bas_muhendis_kimligi(): … git config --global user.name | onaylayan = makinenin git kimliği | AT | rol ↔ kişi makineye gömülü (§12 #2) |
| `onay.py:103-112` | yaml_oku(…)["onay_yetkilisi"] … kim.split()[0].casefold() == … | kurum → kişi adı; ilk ad eşleşmesi | Ç + AT | "Taha Test" de yetkili sayılıyor (§12 #3) |
| `akis.py:795-796, 873, 910, 1036` | kimlik = g.bas_muhendis_kimligi() | git genel kimliği | Ç → AT | onay, değer, geri alma, model notu |
| `kartlar.py:1` | Kart üretici (el kitabı §7 ve kart standardı, Taha 2026-10-26). | yorum | Ç | |
| `kontroller/kayitsiz_gecme.py:14` | CAP_FARKI_SINIRI = 3.0 # mm; karar: Taha (PROMPT §3.1) | sayı kaynağı kişi | SK · AP:cad | |
| `onbellek.py:15-16` | # karar: Taha, 2026-10-26 … UST_SINIR_BAYT = 5 * 1024**3 | sayı kaynağı kişi | AT | |
| `ortam.py:5` | BEKLIYOR — … (ör. Taha'nın yapacağı Hold işi) | yorum | Ç | |
| `ortam.py:23` | BOS_ALAN_ALT_SINIR = 10 * 1024**3 # karar: Taha, 2026-10-26 | sayı kaynağı kişi | AT | |
| `ortam.py:79` | not_="kurulu değil; K3'ten önce Taha kurar (Hold)" | arayüz metni | PA | |
| `gecis.py:128` | if "brief" in k or "taha" in k: | kişi adı mantıkta | KALDIR | etiket → `karar` |
| `gecis.py:354` | Klonun salt okunur kipi kaldırılır (yalnız yerel; Taha onayıyla). | kişi adı | KALDIR | |
| `cli/surec_cli/ana.py:157` | …kaydı Taha kimliğiyle yazılacak. Onaylamak için kart numarasını yaz | arayüz metni | Ç-i18n + AT | ad ayardan |
| `panel/backend/surec_panel/uygulama.py:3-5` | …git genel kimliğiyle (Taha) commit atılır. | belge | Ç | |
| `uygulama.py:109` | "kimlik": g.bas_muhendis_kimligi()[0] | git genel kimliği | Ç → AT | panel başlığındaki ad |
| `veriler.py:719-724` | ad, _ = g.bas_muhendis_kimligi() … f"--author={ad}" | yazar adına göre süzme | Ç | `Rol: bas-muhendis` ekiyle süzülmeli |
| `gozcu.py:38, 84` | f"--author={ad}" / ad, _ = g.bas_muhendis_kimligi() | yazar adına göre süzme | Ç | aynı |
| `panel/frontend/src/ekranlar/ekip.ts:11` | { rol: "bas-muhendis", model: "Taha", … } | rol ↔ kişi | AT | |
| `panel/frontend/src/main.ts:80` | (durum.sekmeler.kimlik ?? "Taha").split(" ")[0] | yedek ad | AT | |
| `panel/frontend/src/yardim.ts:37` | "bas-muhendis": ["T", "#1E2530", "#FFFFFF"] | rozet = adın baş harfi | AT | öteki roller PM/TM/TK/KM |
| `panel/frontend/src/ekranlar/ortak.ts:51` | href="https://github.com/tahatas013/surec/blob/main/el-kitabi.md" | kişisel GitHub hesabı | AT | belge adresi ayardan |
| `panel/frontend/src/stil.css:149` | seçilmiyordu (Taha 2026-10-26). | yorum | Ç | |
| `testler/test_akis.py:7, 57, 292-293` | ("Taha Test", "taha-test@surec.local") | test kimliği, e-posta | Ç (test) | nötr "Onaylayan Test" |
| `testler/test_panel_e2e.py:2, 71, 77, 151` | name = Taha Test … email = taha-test@surec.local; "k@l" | test kimliği, e-posta | Ç (test) | |
| `testler/test_cekirdek.py:85, 112-113, 145, 253, 264, 273, 293` | onay.kaydet(c, "G-01", …, "onay", "Taha", commit=…) | `kurum.yaml`'daki "Taha"ya bağlı | Ç (test) | fikstür kurumu gerekir |
| `testler/vakalar/S-001/onaylar.yaml:3` | kim: Taha | sabit kimlik | Ç (test) | |
| `testler/vakalar/H-001/KAYNAK.md:3, 17, 26` | `tahatas013/ustteknik-arge` … (Taha'nın onayına) … "v3 (Taha, …)" | kişi, hesap | ÇV | |
| `testler/vakalar/H-001/beklenen.yaml:1` | …2026-10-26'da Taha'nın kararıyla 7a/7b'ye bölündü | kişi adı | ÇV | |
| `.claude/settings.json:7, 39-43, 57-59, 62` | "Edit(//home/tahatas013/surec/**)" (10 satır) | kullanıcı adı | AA + AT | ayrıntı §2 |

## 2. Makine ve yollar (/home/tahatas013, ~/is, ~/.local, ~/.cache/surec, %h, port, RAM/GPU)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `.claude/settings.json:7, 39-43, 62` | "Edit(//home/tahatas013/surec/el-kitabi.md)" | mutlak ev dizini | AA + AT | adaptör atölye yollarından üretmeli |
| `.claude/settings.json:57-59` | "Edit(//home/tahatas013/is/ustteknik-arge/**)", ".ssh", ".config/gh" | ev dizini, kurum reposu | AA + AT | |
| `CLAUDE.md:72` | Python yalnız `uv` ile … Sistem Python'una (3.14) paket kurulmaz. | makinenin Python'u | PA | |
| `CLAUDE.md:73` | Node `~/.local/opt` altında, sürüm sabit | yol | PA | |
| `CLAUDE.md:74` | Model önbelleği `~/.cache/surec/<commit>/`; üst sınır 5 GB | yol, disk sınırı | AT | |
| `cekirdek/surec_cekirdek/veri.py:18` | SUREC_KOK = Path(__file__).resolve().parents[2] | kod reposu kökü | Ç | atölye ve kütüphane verisi buradan okunuyor (§12 #1) |
| `veri.py:318` | yol = SUREC_KOK / "profiller" / tur / f"{ad}.yaml" | profiller kod reposunda | AT (+ şema AP) | |
| `onay.py:104` | yol = SUREC_KOK / "kurumlar" / c.kod[:3].lower() / "kurum.yaml" | kurumlar kod reposunda | AT | `SUREC_KURUM_KOKU`'yu yok sayar (`isler.py:49` ile tutarsız) |
| `isler.py:49, 53` | SUREC_KURUM_KOKU … f"SUREC_KURUM_{kod.upper()}_YEREL" | kurum yolu | AT | |
| `panel/backend/surec_panel/veriler.py:35, 37` | (SUREC_KOK / "kurumlar").glob("*/kurum.yaml") | kurumlar kod reposunda | AT | `SUREC_KURUM_KOKU` kullanılmıyor |
| `gozcu.py:24` | Path(os.environ.get("SUREC_KURUM_KOKU", SUREC_KOK / "kurumlar")) | kurum yolu | AT | |
| `isler.py:3-8` | ör. ~/is/ust-deneme … ~/is/calisma/<kod>/ | yol | AT | belge |
| `isler.py:27` | CALISMA_KOKU = … Path.home() / "is" / "calisma" | ~/is | AT | |
| `isler.py:286` | ARSIV_KOKU = … Path.home() / "is" / "arsiv" | ~/is | AT | |
| `kurumlar/bag/kurum.yaml:6, 11` | yerel: ~/is/bag … (repo ~/is/arsiv/bag-deneme) | yol | AT | |
| `kurumlar/ust/kurum.yaml:6-7` | yerel: ~/is/arsiv/ust-deneme … hedef_yerel: ~/is/ustteknik-arge | yol | AT | |
| `onbellek.py:1, 21-23` | os.environ.get("XDG_CACHE_HOME") or … ".cache" … / "surec" | ~/.cache/surec | PA + AT | uygulama adı "surec" sabit |
| `onbellek.py:16` | UST_SINIR_BAYT = 5 * 1024**3 | disk sınırı | AT | |
| `durum.py:4, 16` | ~/.local/state/surec/durum/<kod>.json | XDG state | PA | |
| `durum.py:34` | shutil.which("surec") or … ".local" / "bin" / "surec" | ~/.local/bin | PA | |
| `nabiz.py:7, 18` | Dosya: ~/.local/state/surec/nabiz/<kod>.json | XDG state | PA | |
| `gozcu.py:56, 62, 77` | (~/.local/state/surec/gozcu.json) | XDG state | PA | |
| `akis.py:484-487` | XDG_DATA_HOME or … ".local" / "share") / "surec" / "baski" | ~/.local/share | PA (+ AP:fdm adı) | |
| `veriler.py:5, 27, 68` | (`~/.cache/surec/dallar/<kod>/<dal>`) … okundu.json | XDG cache/state | PA | |
| `model_servisi.py:3` | (`~/.cache/surec/<commit>/tessellation.json`) | yol | PA | belge |
| `model_servisi.py:34` | BELLEKTE_EN_COK = 6 # … (16 GB RAM için ölçülü) | RAM | AT | |
| `ortam.py:21-22` | PYTHON_SURUM = (3, 12) · NODE_SURUM = "v24.22.1" # ~/.local/opt | sabit sürüm, yol | PA | |
| `ortam.py:23` | BOS_ALAN_ALT_SINIR = 10 * 1024**3 | disk sınırı | AT | |
| `ortam.py:91-96` | nvidia-smi … prime-select query … Bulgu("donanım", "nvidia", …) | GPU (NVIDIA) | PA | |
| `ortam.py:102-104` | olcu_yeri = k if k.exists() else Path.home() | ev dizini | PA | |
| `kalite.py:100, 105` | SUREC_KOK / "ajanlar" / "kalite-muhendisi.md" … "el-kitabi.md" | kod reposu yolu | AA · Ç | |
| `regresyon.py:20` | VAKALAR = SUREC_KOK / "testler" / "vakalar" | kod reposu yolu | Ç | vakalar paket başına |
| `gecis.py:29` | VARSAYILAN_GIRDI = Path.home() / "is" / "ust-gecis" / "girdi.yaml" | ~/is | KALDIR | |
| `cli/surec_cli/ana.py:275, 433` | PANEL_PORTU = 8765 # karar K-21 (kurulum): yalnız 127.0.0.1 | sabit port | AT | |
| `ana.py:332` | …worktree ~/is/arsiv/'a; silmez | yol (yardım metni) | AT | |
| `ana.py:428` | (varsayılan ~/is/ust-gecis/girdi.yaml; kurum verisi, surec dışında) | ~/is | KALDIR | |
| `uygulama.py:412-415` | uvicorn.run(app, host="127.0.0.1", port=port, …) | bağlanma adresi | AT | |
| `uygulama.py:47` | IZINLI_HOST = {"127.0.0.1", "localhost", *…SUREC_PANEL_HOSTS…} | host listesi | AT | |
| `uygulama.py:25` | DIST = SUREC_KOK / "panel" / "frontend" / "dist" | kod reposu yolu | Ç | sorun değil, kurulum paketinde |
| `panel/frontend/vite.config.ts:3, 5` | proxy: { "/api": "http://127.0.0.1:8765" } | sabit port | AT | geliştirme |
| `panel/sistem/surec-panel.service:2, 4, 9` | 127.0.0.1:8765 … --port 8765 | sabit port | PA + AT | |
| `panel/sistem/surec-panel.service:8-9, 11` | WorkingDirectory=%h/surec · %h/.local/bin/surec | %h, yol | PA | |
| `el-kitabi.md:322` | Ubuntu makinesi … Sürekli açık, uyku kapalı | makine | PA · AT | |
| `el-kitabi.md:370` | Ubuntu makinesi: 16 GB RAM, RTX 3060. | RAM, GPU | AT | |
| `testler/test_akis.py:52-56`, `test_onbellek.py:44` | monkeypatch.setenv("XDG_CACHE_HOME", …) | ortam değişkeni | Ç (test) | testler yalıtılmış |
| `testler/test_panel_e2e.py:85-88` | SUREC_KURUM_BAG_YEREL … SUREC_CALISMA_KOKU … GIT_CONFIG_GLOBAL | ortam değişkenleri | Ç (test) | v1'de tek "atölye kökü" değişkeni yeter |

Çekirdekte okunan ortam değişkenleri (hepsi AT ya da PA'ya): `SUREC_KURUM_KOKU`, `SUREC_KURUM_<KOD>_YEREL`, `SUREC_CALISMA_KOKU`, `SUREC_ARSIV_KOKU`, `SUREC_TMUX_SOKET` (PA), `SUREC_PANEL_HOSTS`, `SUREC_PANEL_VAKALAR`, `SUREC_KALITE_KOMUTU` (AA), `XDG_CACHE_HOME`/`XDG_STATE_HOME`/`XDG_DATA_HOME` (PA), `TMUX` (PA).

## 3. Ubuntu ve işletim sistemi (systemd, apt, xdg-open, gsettings, nmcli, Linux'a özgü komutlar)

`xdg-open` hiçbir dosyada yok; `apt`, `loginctl`, `journalctl`, `ss`, AppImage yalnız `kayit/` içinde (§10).

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `.claude/settings.json:24, 33, 35-38` | "Bash(sudo *)", "Bash(systemctl *)", "Bash(nmcli *)", "Bash(gsettings *)" … | Linux/Ubuntu komutları | AA + PA | ayrıca `ip`, `ufw` (36-37); izin listesi adaptörde |
| `CLAUDE.md:43-44` | sistem ayarları, servisler (systemd), ağ ve Tailscale; `sudo`… | systemd, sudo | AT (Hold listesi) | |
| `panel/sistem/surec-panel.service:1-17` | # surec paneli · systemd KULLANICI servisi … WantedBy=default.target | systemd | PA | bütün dosya |
| `ortam.py:58-65` | _arac("git"), ("gh"), ("tmux"), ("uv"), ("npm") | araç listesi | PA | `surec doktor` platforma göre |
| `ortam.py:85-88` | _calistir("gh", "auth", "status") | GitHub CLI | PA | forge (GitHub) adaptörü |
| `ortam.py:92-93` | _calistir("nvidia-smi", …) · _calistir("prime-select", "query") | Ubuntu NVIDIA prime | PA | |
| `isler.py:92` | g.git("config", "merge.surec-kart.driver", "true", cwd=repo) | POSIX `true` komutu | PA | Windows'ta yok |
| `isler.py:281` | os.execvp("tmux", _tmux("attach-session", "-t", kod)) | POSIX exec | PA | |
| `el-kitabi.md:322, 359, 370` | Ubuntu makinesi … 2. Ubuntu kurulumu: … Ubuntu sürümü bekleniyor | Ubuntu | PA (belge) | |
| `panel/frontend/index.html:7-9` | href="https://fonts.googleapis.com/css2?family=Geist…" | dış ağa istek | Ç (panel) | yerel font gömülmeli; "dışarıya veri" Hold'una takılır |
| `testler/test_akis.py:58` | "sh -c 'cat >/dev/null; echo Bulgu yok.'" | POSIX kabuk | Ç (test) | |
| `testler/test_panel_e2e.py:87` | "SUREC_KALITE_KOMUTU": "sh -c 'cat >/dev/null; …'" | POSIX kabuk | Ç (test) | |
| `testler/test_panel_e2e.py:113` | p.chromium.launch(args=["--use-gl=swiftshader", …]) | Chromium | Ç (test) | |

## 4. tmux · Tailscale · Remote Control

### tmux

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `isler.py:1` | Çalışma yönetimi: kod verme, klasör ve dallar, worktree, tmux | belge | PA | |
| `isler.py:31-34` | def _tmux(…): SUREC_TMUX_SOKET … ["tmux", *(["-L", soket]…)] | tmux | PA | "oturum yöneticisi" arayüzü |
| `isler.py:219-221` | def tmux_oturumlari(): … "list-sessions", "-F", "#{session_name}" | tmux | PA | |
| `isler.py:229-231` | aktif = tmux_oturumlari() … EN_COK_AKTIF | kural sayımı tmux'tan | Ç → PA | kural Ç'de, sayım arayüzden |
| `isler.py:241-245` | _tmux("new-session", "-d", "-s", kod, …) · komut.append("claude") | tmux + Claude | PA + AA | |
| `isler.py:269-281` | "kill-session" … "switch-client" … "attach-session" | tmux | PA | |
| `isler.py:301, 323` | …tmux oturumu kapanır… · kapat(kod) | tmux | PA | arşivleme |
| `durum.py:60-68` | if os.environ.get("TMUX"): … "tmux", "display-message", "-p", "#S" | tmux | PA | |
| `nabiz.py:75-76` | tmux dışında çalışan oturum (tmux listesinde yok) taze kancasıyla… | tmux | PA | |
| `ortam.py:62` | _arac("tmux", "-V") | tmux | PA | |
| `cli/surec_cli/ana.py:95, 103, 271` | · tmux oturumu '{args.kod}' (bağlanmak için: surec gec …) | arayüz metni | PA + Ç-i18n | |
| `ana.py:326, 328, 337, 340` | help="worktree'yi hazırlar ve adı kod olan tmux oturumu açar (en çok 3)" | arayüz metni | PA | |
| `uygulama.py:99-101` | Açık çalışmalar (tmux oturumu olanlar; en çok 3) … isler.tmux_oturumlari() | panel sekmeleri tmux'a bağlı | Ç → PA | |
| `veriler.py:647, 659, 714` | oturum = kod in isler.tmux_oturumlari() · "tmux": ajan … | durum ekranı | Ç → PA | |
| `panel/frontend/src/main.ts:83, 196` | "tmux oturumu yok" … · tmux <span …>${h(bekleyen.tmux)} | arayüz metni | Ç-i18n + PA | |
| `panel/sistem/surec-panel.service:10` | # git, tmux ve uv yolları; panel tmux oturumlarını … okur | tmux | PA | |
| `el-kitabi.md:323` | …Abonelik gerekir; terminal tmux içinde çalışır | tmux | PA (belge) | |
| `testler/test_akis.py:56, 60, 181, 183, 378, 381` · `test_panel_e2e.py:8, 88, 246` | SUREC_TMUX_SOKET … isler._tmux("kill-server") | tmux | PA (test) | |

### Tailscale

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `CLAUDE.md:43` | sistem ayarları, servisler (systemd), ağ ve Tailscale; | Tailscale | AT (Hold) | |
| `.claude/settings.json:34` | "Bash(tailscale *)" | Tailscale | AA + PA | |
| `ortam.py:78-79` | _arac("tailscale", "version", zorunlu=False, …) | Tailscale | PA | |
| `ana.py:275` | …Tailscale serve bu porta yönlendirir | Tailscale | PA | |
| `uygulama.py:1, 5` | …dışarı yalnız Tailscale ile açılır. … Tailscale ile bağlanan cihazlar | Tailscale | PA | belge |
| `uygulama.py:46-52` | return ad in IZINLI_HOST or ad.endswith(".ts.net") | Tailscale alan adı | PA ("uzaktan erişim") + AT | §12 #12 |
| `ekranlar/dallar.ts:161` · `dosya.ts:80` · `kartlar.ts:343` · `model.ts:78` | altCubuk([… "\|", "yerel · Tailscale", …]) | arayüz sabiti | Ç-i18n + PA | erişim kanalının adı adaptörden |
| `panel/sistem/surec-panel.service:2` | # Yalnız 127.0.0.1:8765'i dinler; dışarı Tailscale serve ile açılır. | Tailscale | PA | |
| `el-kitabi.md:325` | \| Tailscale \| Panele yalnız baş mühendisin cihazları erişir \| | Tailscale | PA (belge) | |
| `el-kitabi.md:359` | 2. Ubuntu kurulumu: Claude Code, Remote Control, Tailscale, … | Tailscale | PA (belge) | |

### Remote Control (kodda hiç yok; yalnız belge ve kayit/)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `el-kitabi.md:298` | Ajan penceresi … bunun için [Claude Code Remote Control](…) kullanılır | Claude Remote Control | AA (belge) | |
| `el-kitabi.md:323` | \| Claude Code + Remote Control \| Ajan penceresi; telefondan izleme… | Claude Remote Control | AA | |
| `el-kitabi.md:359` | Claude Code, Remote Control, Tailscale, araçlar, izin listesi | Claude Remote Control | AA | |
| `el-kitabi.md:386` | - [Claude Code Remote Control](https://seawork.ai/en/blogs/…) | Claude Remote Control | AA | |

## 5. Üstteknik (UST, ustteknik-arge, Üstteknik, bisiklet/motosiklet, dizlik, KLB, DZL)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `CLAUDE.md:32` | `<KURUM>-<PROJE>-<nn>` (ör. `UST-DZL-01`) | örnek kod | Ç | nötr örnek |
| `CLAUDE.md:42` | `ustteknik-arge` reposunda herhangi bir dosyayı değiştirmek; | kurum reposu | AT (Hold) | |
| `.claude/settings.json:57` | "Edit(//home/tahatas013/is/ustteknik-arge/**)" (deny) | kurum reposu | AA + AT | |
| `el-kitabi.md:7` | …İlk uygulayıcı Üstteknik'tir. | kurum | ÇV · AT | |
| `el-kitabi.md:27` | Magnete dizlik kadar süreç uygulanmaz. | ürün örneği | Ç | nötr örnek |
| `el-kitabi.md:52` | \| Ürüne özel (dizlik) \| EN 1621-1 \| Dizlik istek listesi \| | ürün standardı | SK (+ ÇV) | |
| `el-kitabi.md:66` | Kayıtlar her kurumun kendi iş reposundadır; Üstteknik için `ustteknik-arge`. | kurum reposu | AT | |
| `el-kitabi.md:97` | Dizlik, fren parçası, enjeksiyon kalıplı ürün | ürün örneği | Ç | |
| `el-kitabi.md:170-172` | Üstteknik · Bağımsız \| `UST` · `BAG` … Dizlik \| `UST-DZL` | örnek | Ç | nötr örnek |
| `el-kitabi.md:178-182` | `UST-DZL-01/is/mentese` … `UST-DZL-01-G1` … `UST-DZL-01-baski-01` | örnek | Ç | |
| `el-kitabi.md:187` | Mevcut işler: P1-N1 → `UST-DZL-01` Numune N1 · P0 → `UST-DZL-02` … | iş listesi | ÇV | |
| `el-kitabi.md:337-352, 362` | H-001 — P1-N1 menteşesi oturmadı … 5. Pilot: P1-N1, sonra toka… | kurum hatası | ÇV (+ SK dayanak) | |
| `hata-kayitlari/H-001.md:1-54` | \| Proje ve sürüm \| Üstteknik · Dizlik · P1-N1 (yeni kod `UST-DZL-01`) | bütün dosya | ÇV | kural dayanağı SK'de numarayla anılır |
| `kurumlar/ust/kurum.yaml:1-13` | ad: Üstteknik · aciklama: Bisiklet ve motosiklet yedek parça… | bütün dosya | AT (kurumlar) | projeler DZL, KLB |
| `profiller/uretim/fdm-bambu-a1-pla.yaml:2` | …kalibrasyon baskısına (UST-KLB-01) kadar geçerlidir. | kalibrasyon işi | AT | |
| `cekirdek/surec_cekirdek/gecis.py:1-406` | "# K4 · ustteknik-arge geçiş planı"; origin/p1-n1; DIZLIK; UST-DZL-03 | bütün modül | KALDIR | özellikle 321-340, 348-398 |
| `cli/surec_cli/ana.py:285-299, 427-430` | alt.add_parser("gecis-plani", help="K4: ustteknik-arge geçiş planı …") | geçiş komutu | KALDIR | |
| `panel/backend/surec_panel/veriler.py:200-206` | k["kod"] == "UST": … setdefault("DZL", {…, "ad": "Dizlik", …}) | kurum/proje kodu sabit | Ç (genelleştir) | vaka kendi kurum kaydıyla |
| `testler/test_gecis.py:69-76` | {"UST-DZL-01", "UST-DZL-02", "UST-DZL-03"} · "dizlik/p1n1/toka.py" | geçiş testi | KALDIR | |
| `testler/vakalar/H-001/KAYNAK.md:1-27` | `tahatas013/ustteknik-arge`, dal `p1-n1`, commit `a9688e6…` | kurum verisi | ÇV → AP:cad vakası (anonim) | |
| `testler/vakalar/H-001/calisma.yaml:1-2` · `params.yaml:1-12` | kod: UST-DZL-01 · not: "P1N1.K_hole_d" | kurum verisi | ÇV → AP:cad vakası | |
| `regresyon.py:20` | VAKALAR = SUREC_KOK / "testler" / "vakalar" | H-001'i çekirdek regresyonuna bağlar | Ç | vakalar paket başına |

## 6. Belirli alan

### 6a. FDM / 3B baskı (Bambu, A1, CR-10, PLA, OrcaSlicer, baskı, tabla, filament)

Not: `nozul` hiçbir dosyada yok. Çekirdekte "baskı" iki anlamda geçiyor: (i) FDM'e özgü işler (tabla, filament, STL) ve (ii) genel "üretime çıkış" Hold'u (`B-` kartı, `<kod>-baski-<no>` etiketi). (ii) çekirdekte genel adla kalmalı.

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `akis.py:1-5` | …baskı isteği ve çıkışı … Kapı geçişi ve baskı her zaman … onayıyla | belge | Ç | "çıkış (release)" genel adı |
| `akis.py:482-487` | def baski_klasoru(…): … ".local" / "share") / "surec" / "baski" | FDM çıkış dosyası | AP:fdm (+ PA yol) | |
| `akis.py:494-517` | TEMAS_ARALIGI = 0.5 … def tabla_temasi_kusuru(model) | tabla, ilk katman | AP:fdm | |
| `akis.py:520-534` | def baski(…): … kopuk katı (ör. kıymık) baskıda ayrı düşer | baskı Hold'u + FDM ön koşulu | Ç (genel Hold) + AP:fdm | |
| `akis.py:543-546` | disari.step(…) · stl = disari.stl(model, gecici / "stl") | STL | AP:fdm | STEP AP:cad |
| `akis.py:548-565` | "Basmak geri alınmaz (malzeme ve yazıcı süresi)… filament tahmini…" | kart metni | AP:fdm | |
| `akis.py:586-623` | def _baski_hazir_mi … def baski_cik … f"{c.kod}-baski-{no}" | çıkış etiketi | Ç (genel) + AP:fdm | etiket adı "baski" sabit |
| `akis.py:797-805, 851-854` | kart_no.startswith(("O-G", "B-")) … baski_cik(kok, …) | `B-` öneki = baskı | Ç | önek kayıtlı türlerden gelmeli |
| `akis.py:961-980` | def istek_geri_cek: "yalnız baskı istekleri (B-nn) geri çekilir" | baskı isteği | Ç + AP:fdm | |
| `kart_gorsel.py:547-566` | # varsayim: … OrcaSlicer CLI … PLA yoğunluğu 1,24 g/cm³ … debi 8–12 | malzeme, dilimleyici | AP:fdm | |
| `kart_gorsel.py:569-576` | def tabla_olcusu(c): … "tabla_x" … "yazici_tabla" | yazıcı tablası (param adları sabit) | AP:fdm | |
| `kart_gorsel.py:579-614` | yerlesim_bul … baslik="TABLA YERLEŞİMİ · ÜSTTEN" … baski_yonu | tabla, baskı yönü | AP:fdm | |
| `kart_gorsel.py:262-305, 360-364` | gorunus(…, tabla=…, zemin=…) … >tabla</text> | genel görünüşte tabla | AP:fdm · AP:cad | |
| `kart_gorsel.py:7, 780-790, 900-906` | if tur == "baski": … baski_tahmini(m) … "filament_g" | baskı kartı görseli | AP:fdm | |
| `kartlar.py:4-6, 164-186, 422-426` | B baskı … _baski_etiketleri: f"{c.kod}-baski-*" | çıkış kartı | Ç (genel) | |
| `kartlar.py:303-304` | …iş G2'yi geçemez ve baskı istenemez (ENGEL). | kart metni | Ç-i18n | "çıkış istenemez" |
| `veri.py:22` | (ör. Bambu A1 tablası 256 mm) | yorum örneği | Ç | |
| `veri.py:281-299` | _uretim_profili_dogrula … ("model_duzeltme_payi", "baski_yonu") | FDM profil şeması | AP:fdm | boşluk görevleri §6b |
| `veri.py:342` | """'fdm-bambu-a1-pla@v0' → (ad, sürüm)…""" | yorum örneği | Ç | |
| `isler.py:28` | VARSAYILAN_PROFILLER = {"uretim": "fdm-bambu-a1-pla@v0", "olcum": ["kumpas"]} | yazıcı + ölçüm aleti | AT | §12 #4 |
| `disari.py:1, 13-15, 44-54` | STL_TOLERANSI … baskı profili kalibre edilince … def stl | STL | AP:fdm | |
| `ortam.py:81` | _arac("orca-slicer", "--help", zorunlu=False, …) | dilimleyici | AP:fdm | |
| `onay.py:74` | for alan in ("kapi", "baski", "commit", "karar", "secenek"): | konu anahtarı | Ç | genel "cikis" |
| `kalite.py:1-6, 43` | …her kapı ve baskı isteğinde … baskıyı etkileyen tutarsızlık | çıkış isteği | Ç | |
| `cli/surec_cli/ana.py:140-145, 359-361` | def baski … help="baskı Hold'u: dosyaları hazırlar, kart açar…" | CLI komutu | Ç (genel) + AP:fdm | `ana.py:144` `s['onbellek']` okuyor, `akis.baski` bu anahtarı dönmüyor (KeyError) |
| `uygulama.py:286-288` | Karar (K-nn) ve Hold (kapı O-, baskı B-) kartlarında tek tıkla… | `B-` öneki | Ç | |
| `veriler.py:586-607` | cikti/<kod>-baski-NN (onaylanan baskı dosyaları…) … "tur": "baski" | çıkış klasörü | Ç (genel) | |
| `panel/frontend/src/ekranlar/ciktilar.ts:1-2, 15-19, 45-58` | stl: "dilimleyici için" … "onaylı baskı" | arayüz | AP:fdm (panel eklentisi) | |
| `ekranlar/kartlar.ts:31, 76-89, 150, 162, 262` | <span class="ad">Filament</span> … "Basılmasını onayla" | arayüz | AP:fdm (panel eklentisi) | |
| `ekranlar/dallar.ts:98, 108, 111, 161` | /baski/.test(e) … "Kapılar ve baskılar" | etiket deseni + arayüz | Ç | |
| `ekranlar/dosya.ts:9, 46` | kontroller: ["kapı", "baskı"] … "Kapılar ve baskılar" | günlük türü | Ç | |
| `profiller/uretim/fdm-bambu-a1-pla.yaml:1-38` | yazici: Bambu Lab A1 · malzeme: PLA · baski_yonu: … | bütün dosya | AT (örnek) + AP:fdm (şema) | |
| `profiller/uretim/fdm-cr10se-pla.yaml:1-39` | yazici: Creality CR-10 SE · malzeme: PLA | bütün dosya | AT | |
| `el-kitabi.md:62, 233, 239, 255, 326, 360` | \| FDM (makine + malzeme + baskı yönü) \| … OrcaSlicer komut satırı | FDM | AP:fdm (belge) | |
| `el-kitabi.md:371` | Yazıcı ve malzeme: Bambu Lab A1, PLA. İlk profil `fdm-bambu-a1-pla` | makine | AT | |
| `el-kitabi.md:13, 104, 129, 137, 181, 201` | …üretime ya da baskıya çıkış … `<kod>-baski-<no>` | çıkış = baskı | Ç | genel "çıkış" adı |
| `CLAUDE.md:34, 47` | Kapı · baskı etiketi … baskıya ya da üretime göndermek | çıkış = baskı | Ç | |
| `talimatlar/README.md:3` | …FDM baskı, tarama, baskıya dosya hazırlama… | FDM talimatı | AP:fdm | |
| `testler/test_akis.py:194-204, 300, 348-354, 463-479, 640-658, 697-714` | akis.baski(d) … f"{kod}-baski-01" | baskı akışı testi | AP:fdm (test) + Ç | |
| `testler/test_cekirdek.py:13, 196, 328, 388-417` | "uretici:bambu-a1" … test_tabla_yerlesimi… test_tabla_temasi_kusuru | FDM testi | AP:fdm (test) | |
| `testler/vakalar/H-001/calisma.yaml:8` · `S-001/calisma.yaml:8` · `H-001/params.yaml:6, 12` | uretim: fdm-bambu-a1-pla@v0 · "[varsayım: FDM payları]" | gerçek yazıcı profili | Ç (test, sentetik profil) | |

### 6b. Mekanik CAD ve geçme (istenmedi ama çekirdekte bir alanı adıyla tanıyor; öneri için eklendi)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `veri.py:20, 203-267` | GOREVLER = {"ortalama", "donme", "kayma", "siki", …} · class Gecme | geçme modeli | AP:cad | |
| `veri.py:284-296` | b = _sozluk(_gerekli(p, "bosluk", yer)…) … "vida_gecisi" … "tablo" | profil boşluk şeması | AP:cad | |
| `veri.py:421-430` | for alan in ("kod", "ad", "sinif", "asama", "profiller") … uretim zorunlu | her çalışmaya üretim profili | Ç | grafik iş için de zorunlu (§12 #5) |
| `veri.py:97` | BIRIMLER = {"mm", "m", "derece", "adet", …, "m/s"} | birim listesi | Ç (paket genişletir) | |
| `kontroller/__init__.py:6-11` | SIRA = [kaynaksiz, bagimsiz_sayi, gecme_boslugu, olcme_belirsizligi, …] | mekanik kontroller her işte | Ç (kayıt) + AP:cad | §12 #7 |
| `kontroller/bagimsiz_sayi.py` · `gecme_boslugu.py` · `girisim.py` · `kayitsiz_gecme.py` · `montaj.py` · `olcme_belirsizligi.py` | GECME-01/02, VIDA-01 (ISO 273), KATI/GIRISIM-01 (manifold3d)… | mekanik | AP:cad (+ SK kurallar) | `kaynaksiz`, `onay_durumu`, `hesap_tutarliligi` Ç'de |
| `akis.py:90-94` | import cadquery as cq … BoundingBox() | CadQuery | AP:cad | |
| `akis.py:272-276` | m("Her geçmenin görevi ve boşluk sınırı var"…) m("Üretim profili seçildi"…) | G2 maddeleri alana bağlı | Ç (madde kaydı) + AP:cad | |
| `modelci.py:30-71` | CadQuery Shape … version(p) for p in ("cadquery", "cadquery-ocp", …) | CadQuery | AP:cad | Ç'de "model üretici" arayüzü |
| `gorsel.py:1-146` · `kart_gorsel.py:1-40, 255-470` | import cadquery as cq | CadQuery | AP:cad | |
| `isler.py:178-188` | MODEL_SABLONU … import cadquery as cq | CadQuery | AP:cad | |
| `ortam.py:25-28, 124-162` | PAKETLER = ["cadquery", "cadquery-ocp", "trimesh", …] · duman_testi | CadQuery | AP:cad | |
| `panel/backend/surec_panel/model_servisi.py:1-313` · `panel/frontend/package.json:12` | from OCP.BRepAdaptor import … · "three-cad-viewer": "5.1.3" | CAD görüntüleyici | AP:cad (panel eklentisi) | |
| `kartlar.py:30-31, 310-353` | GOREV_ADI = {"siki": "sıkı", …} … "Ölçü kumpas ya da mastarla yeniden alınır." | geçme kartı metni | AP:cad | |
| `kurallar/katalog.yaml:15-68` | GECME-01 … VIDA-01 … KATI-01 … KAYITSIZ-01 | mekanik kurallar | SK (mekanik bölümü) | |

### 6c. Aero (planör, kanat, AeroSandbox, NeuralFoil, VLM, Reynolds)

`NeuralFoil` ve `Reynolds` yalnız `kayit/kurulum/plu-eksikleri.md:40, 46` içinde; kodda AeroSandbox import edilmiyor (yalnız bağımlılık listesinde).

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `hesap.py:4-8` | b = h.girdi("kanat_acikligi") … h.grafik("Süzülme oranı – hız", …) | docstring örneği aero | Ç (nötr örnek) | |
| `hesap.py:12-16` | (rüzgâr tüneli benzeri aerodinamik tarama, çakılma ve iniş…) | docstring örneği | Ç | |
| `hesap.py:93-95, 102` | (ör. kararlilik_payi, denge_cl, … suzulme_orani) … (VLM, FEA) | docstring örneği | Ç | doğruluk 1/2/3 mekanizması alan bağımsız |
| `akis.py:499-500` | (PLU B-01: … kanat alt yüzünün 0,17 mm altına iniyordu) | yorum | Ç | |
| `kart_gorsel.py:470` | (ör. kanat kalınlığı) | yorum | Ç | |
| `pyproject.toml:7` | "aerosandbox>=4.2.10", | bağımlılık | AP:aero | NeuralFoil bunun içinden |
| `panel/frontend/src/ekranlar/hesaplar.ts:95` | …(aerodinamik tarama, çakılma ve iniş…); her biri bir riske… | arayüz metni | Ç-i18n | nötr örnek |
| `kurumlar/bag/kurum.yaml:12` | PLU: {ad: Planör, klasor: planor} | proje | AT · ÇV | |
| `profiller/uretim/fdm-cr10se-pla.yaml:2, 15` | …ilk iş BAG-PLU-01 (planör) … Planör tek parça ve montajsız | proje adı | AT | |
| `testler/test_akis.py:621, 726` | K-03'te kanat inceldi … h.buyukluk("x", X, "-", 2, "VLM") | test | Ç (test) | |
| `testler/vakalar/S-001/kayit/hesaplar/h_vlm.json:26, 29, 33` · `h_elle.json:29` · `S-001/beklenen.yaml:47, 50` | "yontem": "VLM" · "ad": "denge_cl" | test fikstürü | Ç (test) | nötr adlandırılmalı |

### 6d. Tarama ve ölçüm aletleri (iPhone, LiDAR, KIRI, kumpas, mastar)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `veri.py:21` | KAYNAK_DESENI = re.compile(r"^(olcu:(kumpas\|mastar\|tarama)\|…") | alet sınıfları kodda | Ç (genel `olcu:<alet>`) + AT | §12 #5 |
| `veri.py:302-305` | re.fullmatch(r"olcu:(kumpas\|mastar\|tarama)", …) | alet sınıfları kodda | Ç + AT | |
| `CLAUDE.md:22` | Her değerin kaynağı: `olcu:kumpas\|mastar\|tarama`, `standart:…` | alet sınıfları | Ç | |
| `kurallar/katalog.yaml:10` | kaynak ∈ {olcu:kumpas, olcu:mastar, olcu:tarama, standart:*, …} | alet sınıfları | SK | |
| `kurallar/katalog.yaml:39-43` | OLCU-02 · metin: iPhone LiDAR taraması kritik geçme ölçüsü için… | cihaz adı kuralda | SK (genel "tarayıcı") + AT (cihaz) | |
| `profiller/olcum/iphone-lidar-kiri.yaml:1-18` | # Ölçüm profili: iPhone 17 Pro Max · KIRI Engine · LiDAR modu | bütün dosya | AT (ölçüm aleti) | dayanak (VDI/VDE 2634, Yanchuk) SK |
| `profiller/olcum/kumpas.yaml:1-12` | # Ölçüm profili: kumpas · belirsizlik … 0.05 | bütün dosya | AT (ölçüm aleti) | |
| `el-kitabi.md:48, 217` | Optik tarayıcı doğruluğu \| VDI/VDE 2634 … \| `olcu:tarama` \| 3B taramadan | tarama standardı | SK | |
| `el-kitabi.md:352, 372` | Tarama iPhone LiDAR ile yapıldı … iPhone 17 Pro Max, KIRI Engine | cihaz | ÇV (352) · AT (372) | |
| `hata-kayitlari/H-001.md:14, 34, 41, 47, 51` | Tarama iPhone LiDAR ile yapıldı. … LiDAR kritik geçmede geçersiz | cihaz | ÇV | |
| `kartlar.py:344, 352` | "Ölçü daha hassas bir aletle (mastar) yeniden alınır." | alet adı metinde | Ç-i18n · AT | |
| `gecis.py:124-127, 295, 379` | return "olcu:tarama", "iphone-lidar-kiri", not_ | cihaz profili | KALDIR | |
| `testler/test_cekirdek.py:13, 243` · `test_gecis.py:33, 61-62` | "olcum": ["kumpas", "iphone-lidar-kiri"] | cihaz profili | Ç (test) · KALDIR | |
| `testler/vakalar/H-001/params.yaml:2, 4, 8-9` · `H-001/calisma.yaml:9` · `S-001/params.yaml:7` · `S-001/calisma.yaml:9` | olcum_profili: iphone-lidar-kiri | cihaz profili | Ç (test fikstürü) | |

### 6e. FEA (TetGen, scikit-fem)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `cekirdek/surec_cekirdek/fea.py:1-66` | katı model → TetGen dörtyüzlü ağ → scikit-fem … import tetgen | bütün modül | AP:fea | `disari.temiz_ag`'e bağlı (AP:cad) |
| `pyproject.toml:11, 14-15` | "meshio>=5.3.5", "scikit-fem>=12.0.2", "tetgen>=0.8.4" | bağımlılık | AP:fea | meshio kodda kullanılmıyor |
| `hesap.py:94` | dogruluk: 1 elle formül · 2 sayısal yöntem (VLM, FEA) · 3 ölçüm | yorum | Ç | |

### 6f. Karar önerisi: alan paketi mi, çekirdek mi?

| Alan | Öneri | Çekirdekte kalan genel kavram | Gerekçe |
| --- | --- | --- | --- |
| FDM / 3B baskı | **AP:fdm** (profil şeması, tabla/temas kontrolü, STL, baskı tahmini, OrcaSlicer, panel baskı kartı) | "Üretime çıkış" Hold'u: istek kartı, dosya özeti (SHA-256), donmuş çıktı klasörü, etiket | Tabla, filament, PLA yoğunluğu yalnız FDM'de anlamlı; kalıp ya da sac işinde de aynı Hold gerekir |
| Mekanik CAD, geçme | **AP:cad** (CadQuery model üretici, geçme kaydı ve 6 kontrol, kesit/izometrik, three-cad-viewer) | Kaynak etiketi, kontrol kaydı (ENGEL/UYARI/GEÇTİ), kart üretimi, model üretici arayüzü | Grafik iş (el kitabı §14 genellik sınaması) bugün CadQuery ve geçme kontrolü olmadan açılamıyor |
| Aero | **AP:aero** (AeroSandbox/NeuralFoil hesap şablonları, büyüklük adları) | `Hesap` kaydı, analiz `BAGLANTI` zorunluluğu, doğruluk sınıfıyla hesaplar arası tutarlılık | Kod zaten alan bağımsız; yalnız örnekler ve bağımlılık aero |
| Tarama | **Alan paketi değil**: cihaz = AT (ölçüm aleti profili), belirsizlik kuralı (1/4, ISO 14253-1, VDI/VDE 2634) = SK | `olcu:<alet>` etiketi ve belirsizlik kontrolü mekanizması | Ölçüm aleti atölyenin envanteridir; sınıf adı (`tarama`) kod deseninden çıkmalı |
| FEA | **AP:fea** (yapısal analiz; AP:cad'e bağımlı) | Hesap ve analiz kaydı | TetGen ve scikit-fem ağır bağımlılık; yalnız gereken kurulumda |

## 7. Claude Code'a özgü (`claude -p`, `.claude/`, kancalar, model adları, ortam değişkenleri)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `kalite.py:7-9` | İnceleyici: `claude -p` ile kalite-muhendisi ajanı … SUREC_KALITE_KOMUTU | Claude CLI | AA | |
| `kalite.py:87-91` | ["claude", "-p", "--model", "opus", "--allowedTools", "Read Grep Glob", …] | Claude CLI + model adı | AA | §12 #8 |
| `kalite.py:100` | (SUREC_KOK / "ajanlar" / "kalite-muhendisi.md")….split("---", 2)[-1] | Claude alt ajan ön bilgi biçimi | AA | |
| `kalite.py:109` | …inceleyici komutu yok ({e.filename}); SUREC_KALITE_KOMUTU | ortam değişkeni | AA | |
| `durum.py:1-5` | Ajan durumu: Claude Code kancaları (hooks) her oturumun durumunu … | Claude kancaları | AA | |
| `durum.py:18-26` | OLAY_DURUM = {"SessionStart": …, "Notification": "bekliyor", …} | Claude olay adları | AA | |
| `durum.py:29-49` | yol = wt / ".claude" / "settings.json" … hooks[olay] = [giris] | `.claude/settings.json` | AA | §12 #9 |
| `durum.py:52-59` | girdi.get("hook_event_name") … "permission" in tur | Claude kanca girdisi | AA | |
| `durum.py:90-108` | def kancadan(kod): … json.load(sys.stdin) | Claude kanca girdisi | AA | |
| `isler.py:224, 238-246` | def ac(kod, claude: bool = False, claude_ayarlari: bool = False) … "claude" | Claude başlatma | AA | |
| `isler.py:249-266` | hedef = wt / ".claude" / "agents" … f.write("\n.claude/\n") | `.claude/agents` | AA | |
| `nabiz.py:3, 73-80` | Kancalar … kendi Claude oturumunda … "terminalde izin/cevap bekliyor" | Claude izin isteme | AA | nabız mekanizması Ç |
| `gozcu.py:5` | Ekip oturumu bunu arka planda çalıştırır (Claude Code Monitor) | Claude Monitor | AA | |
| `gunluk.py:12-18` | "proje-muhendisi": "Proje mühendisi · Opus", … "Tekniker · Haiku" | model adları kalıcı kayıtta | AA (+ Ç-i18n) | §12 #10 |
| `cli/surec_cli/ana.py:94` | isler.ac(args.kod, claude=args.claude, claude_ayarlari=…) | Claude başlatma | AA | |
| `ana.py:187-209` | {"hookSpecificOutput": {"hookEventName": olay, "additionalContext": …}} | Claude kanca çıktısı | AA | |
| `ana.py:228-231, 400-402` | help="Claude Code kancası: oturum durumunu yazar (stdin JSON)" | Claude kanca | AA | |
| `ana.py:328-330, 382` | --claude · --claude-ayarlari · --kanca | Claude seçenekleri | AA | |
| `veriler.py:679` | " Ekibi başlatmak için: surec ac " + kod + " --claude-ayarlari" | arayüz metni | AA | |
| `ajanlar/README.md:3, 7-9` | `.claude/agents/` … \| sonnet \| … \| haiku \| … \| opus \| | Claude alt ajan, model | AA | rol tanımı Ç |
| `ajanlar/kalite-muhendisi.md:1-6` | model: opus · tools: Read, Grep, Glob, Bash | Claude alt ajan biçimi | AA | gövde (rol talimatı) Ç |
| `ajanlar/tasarim-muhendisi.md:1-6` | model: sonnet · …tek yön çizer (CadQuery) | Claude alt ajan, CAD | AA (+ AP:cad) | |
| `ajanlar/tekniker.md:1-6` | model: haiku | Claude alt ajan | AA | |
| `panel/frontend/src/ekranlar/ekip.ts:12-15` | model: "Opus 5.5 · ana oturum" … "Sonnet" … "Haiku" … "Opus · temiz bağlam" | model adları | AA | |
| `el-kitabi.md:77-80, 84` | Opus 5.5 (ana oturum) … Sonnet … Haiku … Tasarım kararı Haiku'ya verilmez | model adları | AA (belge) | Ç'de yetenek sınıfı (üst/orta/alt) |
| `el-kitabi.md:298, 322-323, 359, 386` | Claude Code + Remote Control … Ubuntu makinesi \| Claude Code, araçlar | Claude Code | AA | |
| `CLAUDE.md:1-74` | # surec — kalıcı kurallar (Claude Code proje belleği) · :51 Haiku'ya | bütün dosya | AA | içerik Ç ve AT'ye dağılır |
| `.claude/settings.json:1-65` | "permissions": { "allow": … "ask": … "deny": … } | Claude izinleri | AA (+ AT yollar) | |
| `.gitignore:21` | .claude/settings.local.json | Claude yerel ayarı | AA | |
| `testler/test_akis.py:58, 176-179, 215-233, 706, 713` · `test_panel_e2e.py:87, 244-246` | "Claude needs your permission to use Bash" · SUREC_KALITE_KOMUTU | Claude kanca biçimi | AA (test) | |

## 8. Kurum kodları (BAG, PLU, TST) ve sabit çalışma kodları (UST-DZL-01, BAG-PLU-01, UST-KLB-01)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `kurumlar/bag/kurum.yaml:1, 11-12` | kod: BAG … TST: {ad: Sistem sınaması…} · PLU: {ad: Planör…} | kurum, proje kodu | AT | |
| `el-kitabi.md:17, 170` | Bir kuruma bağlı olmayan işler **Bağımsız** (`BAG`) altında açılır | kurumsuz iş kodu | Ç (kavram) + AT (kod) | |
| `panel/frontend/src/ekranlar/ortak.ts:42` | ${k.kod === "BAG" ? IKON.bagimsiz : IKON.kurum} | kod sabit | Ç | `kurum.yaml`'da `tur: bagimsiz` |
| `gozcu.py:1, 4` | (PLU E-14) … BAG-PLU-01 · 23:20 · O-G1 onaylandı · 9d6afd4 | örnek | Ç | nötr örnek |
| `nabiz.py:5-6` | surec nabiz BAG-PLU-01 --rol proje-muhendisi --is "…" | örnek | Ç | |
| `akis.py:499, 529, 591, 660` | (PLU B-01 …) · (PLU E-28) · (PLU E-24) · (PLU E-17) | iş kaydı numarası | Ç | hata kaydı numarasıyla anılmalı |
| `disari.py:31` | (PLU, radyüslü burun bloğu) | iş kaydı | AP:cad | |
| `kart_gorsel.py:469, 471, 551` | (PLU E-17) … (PLU E-21) … (PLU E-23) | iş kaydı | AP:cad · AP:fdm | |
| `profiller/uretim/fdm-bambu-a1-pla.yaml:2` | kalibrasyon baskısına (UST-KLB-01) kadar | çalışma kodu | AT | |
| `profiller/uretim/fdm-cr10se-pla.yaml:2` | → ilk iş BAG-PLU-01 (planör), 2026-10-26. | çalışma kodu | AT | |
| `CLAUDE.md:32` | (ör. `UST-DZL-01`) | örnek | Ç | |
| `el-kitabi.md:172, 178-182` | `UST-DZL-01` … `UST-DZL-01/karar/K-07-a` | örnek | Ç | nötr örnek |
| `el-kitabi.md:187` | P1-N1 → `UST-DZL-01` · P0 → `UST-DZL-02` · … `UST-DZL-03` | iş listesi | ÇV | |
| `hata-kayitlari/H-001.md:7` | (yeni kod `UST-DZL-01`), v0.4 | çalışma kodu | ÇV | |
| `gecis.py:361, 398` | `UST-DZL-03/model/params.py` … (UST-DZL-01) | çalışma kodu | KALDIR | |
| `veriler.py:201, 204` | k["kod"] == "UST" … setdefault("DZL", …) | kurum, proje kodu | Ç | |
| `isler.py:25` · `gozcu.py:20` | KOD_DESENI = re.compile(r"^([A-Z]{3})-([A-Z]{3})-(\d{2})$") | kod biçimi | Ç (kural) | kurum adı değil, el kitabı §8 biçimi |
| `onay.py:104` | c.kod[:3].lower() | kurum = kodun ilk 3 harfi | Ç | kurum kaydından çözülmeli |
| `testler/vakalar/H-001/calisma.yaml:2` · `S-001/calisma.yaml:3` | kod: UST-DZL-01 · kod: BAG-TST-01 | çalışma kodu | Ç (test fikstürü) | |
| `testler/test_akis.py:48, 81-82, 125, 142, 174, 195, 208, 225-233, 239, 372, 416, 646, 702` | isler.yeni_calisma("BAG", "TST", …) · "BAG-TST-09" | sınama kurumu | Ç (test) | nötr fikstür kurumu |
| `testler/test_akis.py:595, 604, 621, 641` | """Hata (BAG-PLU-01, 16:53): … | iş kaydı | Ç (test) | |
| `testler/test_panel_e2e.py:37, 62, 78-85, 131-502 (≈35 satır)` | "BAG-TST-01" · SUREC_KURUM_BAG_YEREL · SUREC_KURUM_UST_YEREL | sınama kurumu | Ç (test) | |
| `testler/test_cekirdek.py:12, 389, 403, 421, 450` | "kod": "BAG-TST-01" · """PLU: 230 mm açıklık 220 mm tablaya … | sınama, iş kaydı | Ç · AP:fdm (test) | |

## 9. Türkçe'ye sabit arayüz metinleri (i18n)

Sayım yaklaşıktır: .py dosyalarında docstring dışındaki dize belirteçleri, .ts dosyalarında yorum dışı tırnak ve şablon içleri; Türkçe harf ya da sık Türkçe sözcük içeren satır sayıldı. Durum anahtarı gibi birkaç kimlik değeri de sayıma girmiş olabilir.

### 9a. Dosya başına

| dosya | ≈ satır | örnek 1 (satır · alıntı) | örnek 2 (satır · alıntı) | v1 hedef |
| --- | --- | --- | --- | --- |
| `cekirdek/surec_cekirdek/akis.py` | 205 | 130 · "ana hatta (<kod>/ana) doğrudan yazılmaz; bir iş ya da karar dalında çalış" | 383 · f"{c.kod} {kapi} kapısını geçsin mi?" | Ç-i18n |
| `cekirdek/surec_cekirdek/kartlar.py` | 108 | 273 · f"{p.ad} {_deger(p)} olsun mu?" | 302 · f"{p.ad} için kaynak ne?" | Ç-i18n |
| `panel/frontend/src/ekranlar/kartlar.ts` | 102 | 12 · hold: ["Hold", …], gecici: ["Geçici", …], inceleme: ["İnceleme", …] | 150 · "Basılmasını onayla" : "Onayla" | Ç-i18n |
| `cli/surec_cli/ana.py` | 71 | 136 · "O-{kapi} kartı açıldı; geçiş baş mühendis onayını bekliyor (Hold)." | 306 · help="ortamı denetler: araçlar, sürümler, kimlik doğrulamalar" | Ç-i18n |
| `cekirdek/surec_cekirdek/gecis.py` | 68 | 117 · "etiketsiz → varsayim (K4 kuralı)" | 348 · "# K4 · ustteknik-arge geçiş planı (kuru çalıştırma)" | KALDIR |
| `cekirdek/surec_cekirdek/veri.py` | 47 | 27 · "Bu üründeki bir hata bir kişiye zarar verebilir mi?" | 162 · f"{yer}: ad ASCII küçük harf, rakam ve _ olmalı" | Ç-i18n |
| `panel/backend/surec_panel/veriler.py` | 47 | 23 · KAPI_ADLARI = {"G0": ("Talep", "İstek listesi, risk sınıfı"), …} | 670 · f"Top sende: {len(sende)} kart onayını bekliyor" | Ç-i18n |
| `panel/frontend/src/ekranlar/ekip.ts` | 39 | 11 · yetki: "Kartları ve kapıları onaylar", is: "Karar verir, yorum yazar" | 103 · bekliyor: "Top sende: senin kararın ya da cevabın olmadan…" | Ç-i18n |
| `cekirdek/surec_cekirdek/kart_gorsel.py` | 34 | 610 · baslik="TABLA YERLEŞİMİ · ÜSTTEN" | 914 · "seçenek çizimleri birbirinin aynı: seçenekler modelde ayrışmıyor…" | Ç-i18n · AP:fdm |
| `cekirdek/surec_cekirdek/isler.py` | 33 | 51 · f"kurum yok: {kod}" | 70 · f"çalışma kodu '{kod}' biçimi <KUR>-<PRJ>-<nn> olmalı" | Ç-i18n |
| `panel/frontend/src/ekranlar/model.ts` | 25 | 16 · `<span>Parçalar</span>…` | 78 · "yerel · Tailscale" | Ç-i18n |
| `panel/frontend/src/ekranlar/asamalar.ts` | 24 | 20 · `…">✓ tamamlandı</span>` | 21 · `…<span class="nokta" …></span>sürüyor</span>` | Ç-i18n |
| `panel/backend/surec_panel/uygulama.py` | 23 | 58 · {"hata": "izinsiz Host"} | 87 · f"{kod} dondurulmuş regresyon vakası; salt okunur" | Ç-i18n |
| `panel/frontend/src/ekranlar/dallar.ts` | 22 | 18 · `<span class="rozet mavi">şu an</span>` | 111 · ["kapilar", "Kapılar ve baskılar"], ["acik", "Açık dallar"] | Ç-i18n |
| `cekirdek/surec_cekirdek/ortam.py` | 19 | 52 · not_ or "kurulu değil" | 79 · "kurulu değil; K3'ten önce Taha kurar (Hold)" | Ç-i18n · PA |
| `panel/frontend/src/ekranlar/hesaplar.ts` | 17 | 59 · `<b …>Ne için?</b>` | 95 · "Bu çalışmada henüz analiz yok. Analizler gerçek hayat…" | Ç-i18n |
| `panel/frontend/src/ekranlar/durum.ts` | 15 | 16 · return "az önce"; | 17 · return `${dk} dk önce`; | Ç-i18n |
| `panel/frontend/src/main.ts` | 15 | 31 · ["durum", "Durum"], … ["dosya", "Tasarım dosyası"] | 196 · `<b>Ajan bekliyor</b> · … "izin istiyor" : "cevap bekliyor"` | Ç-i18n |
| `panel/frontend/src/ekranlar/dosya.ts` | 14 | 42 · ["yeni", "Son okumandan beri"], ["bugun", "Bugün"] | 73 · `<span>Baş mühendis onayı</span>` | Ç-i18n |
| `cekirdek/surec_cekirdek/hesap.py` | 13 | 59 · f"hesap {self.ad}: '{ad}' params.yaml'da yok" | 173 · f"analiz {h.ad}: BAGLANTI boş — hangi risk, gözlem…" | Ç-i18n |
| `cekirdek/surec_cekirdek/onay.py` | 12 | 106 · f"{c.kod}: kurum dosyası yok, onay yetkilisi bilinmiyor" | 153 · f"{kim}: onay ya da ret yalnız onay yetkilisinin (…) işidir" | Ç-i18n |
| `panel/frontend/src/ekranlar/ciktilar.ts` | 12 | 15 · step: "3B model (CAD)", stl: "dilimleyici için" | 53 · "Onaylanan baskıların dosyaları ve deney belgeleri…" | Ç-i18n · AP:fdm |
| `cekirdek/surec_cekirdek/kalite.py` | 11 | 36-44 · ISTEM = "İnceleme konusu: … Çıktı biçimi: önem sırasıyla…" | 136 · f"kalite incelemesinde {…} açık YÜKSEK bulgu var" | Ç-i18n · AA (istem) |
| `panel/frontend/src/isaretle.ts` | 9 | 67 · "Notun yerini sürükleyerek seç · Esc: vazgeç" | 111 · alt="işaretli alan" | Ç-i18n |
| `cekirdek/surec_cekirdek/kontroller/gecme_boslugu.py` | 8 | 20 · f"{g.no}: görev tanımsız, sınır yok" | 35 · "…; ISO 273 ince seri Ø{…}'ün dışında" | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/git.py` | 7 | 18 · EK_ANAHTARLARI = ["Adım", "Rol", "Kart", "Görsel"] | 42 · "git genel kimliği (user.name / user.email) tanımlı değil" | Ç (protokol, §9b) |
| `cekirdek/surec_cekirdek/gunluk.py` | 7 | 13 · "proje-muhendisi": "Proje mühendisi · Opus" | 30 · f"# Günlük · {kod} · {z:%Y-%m-%d}" | Ç-i18n · AA |
| `cekirdek/surec_cekirdek/regresyon.py` | 7 | 38 · f"{etiket}: sonuç yok, beklenen {b}" | 42 · f"{etiket}: beklenen KALDI, alınan GEÇTİ" | Ç-i18n |
| `cekirdek/surec_cekirdek/kontroller/bagimsiz_sayi.py` | 6 | 34 · "nominal var ama boşluk tanımsız; iki taraf tek kayıttan üretilemez" | 44 · "delik {d} = … ve mil {m} = … birbirinden bağımsız iki sayı" | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/kontroller/hesap_tutarliligi.py` | 6 | 24 · f"{ad}: hesaplar arasında fark %10 içinde" | 51 · f"{kr['no']} kararının dayanağı değişti: " | Ç-i18n |
| `panel/frontend/src/goruntuleyici.ts` | 6 | 33 · console.warn("ölçüm:", e) | 62 · eskiG.name = "önceki"; eskiG.id = "/Karşılaştırma/onceki"; | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/kontroller/girisim.py` | 5 | 32 · "model yüklenmedi; katı model ve girişim kontrolü çalışmadı" | 47 · f"{a} ↔ {b}: {h:.3f} mm³ girişim" | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/kontroller/olcme_belirsizligi.py` | 5 | 33 · "'{prof['ad']}' kritik geçme ölçüsü için geçersiz (OLCU-02)" | 47 · "sınırda (eşit)" | Ç-i18n |
| `cekirdek/surec_cekirdek/kontroller/onay_durumu.py` | 5 | 25 · f"{k['no']}: reddedildi, düzeltilmedi" | 27 · "açık Hold" if … else "kart kapanmadı" | Ç-i18n |
| `panel/frontend/src/maskot.ts` | 5 | 6 · calisiyor: "Ekip çalışıyor", sessiz: "Ekipten ses yok", … | 42 · " · az önce" : ` · ${c.dakika} dk önce` | Ç-i18n |
| `panel/frontend/src/yardim.ts` | 5 | 29 · `<b>Bugün</b> · ${uzun}` : … `<b>Dün</b>` | 40-41 · "Proje mühendisi", … "Baş mühendis" | Ç-i18n |
| `cekirdek/surec_cekirdek/kontroller/kayitsiz_gecme.py` | 4 | 57 · "model yüklenmedi; tarama çalışmadı" | 70 · f"{metin}: eş eksenli, geçme kaydında yok" | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/kontroller/kaynaksiz.py` | 4 | 18 · f"{p.ad} = {mm(p.deger)} {p.birim}: kaynak etiketi yok" | 20 · f"{p.ad}: kaynak '{p.kaynak}' ama değer yok" | Ç-i18n |
| `cekirdek/surec_cekirdek/kontroller/montaj.py` | 4 | 22 · {"yok": "onay yok", "dustu": "onay düştü (değer değişti)", …} | 23 · f"{metin}; onaysız montaj esnemesi ({ek})" | Ç-i18n · AP:cad |
| `panel/frontend/src/ekranlar/ortak.ts` | 3 | 39 · `AĞAÇ<span class="mono">${acik} çalışma</span>` | 54 · "Kural kataloğu · hata kayıtları" | Ç-i18n |
| `cekirdek/surec_cekirdek/gorsel.py` | 2 | 92 · "kesit boş: düzlem parçaları kesmiyor" | 114 · `KESİT {ad} · ÖLÇEK {…}` | Ç-i18n · AP:cad |
| `cekirdek/surec_cekirdek/gozcu.py` | 2 | 47 · baslik.startswith("Günlük:") | 88 · f"gözcü başladı · {len(repolar)} repo · {ad}" | Ç-i18n |
| `cekirdek/surec_cekirdek/nabiz.py` | 2 | 79 · ("terminalde " + ("izin" … else "cevap") | 80 · + " bekliyor" | Ç-i18n · AA |
| `panel/backend/surec_panel/izleyici.py` | 2 | 82 · "önceden üretim başarısız (%s):\n%s" | 125 · f"izleyici: {e}" | Ç-i18n |
| `panel/frontend/src/genislet.ts` | 2 | 33 · "Sürükleyerek genişlet (çift tık: varsayılan)" | 8 · ["aside.sol", "sol-ağaç", "sag"] (anahtar) | Ç-i18n |
| `panel/frontend/src/api.ts` | 2 | 34 · `/api/calisma/${kod}/kart/${no}` | 36 · `…/geri-al` | — (yol adı, metin değil) |
| `cekirdek/surec_cekirdek/durum.py` | 1 | 23 · "Notification": "bekliyor" | — | — (durum kimliği) |
| `testler/test_akis.py` | 126 | 22 · METIN = {"soru": "Hangisi?", "aciklama": "sınama kararı", …} | 23 · "blok yazıcıya sığar (değişmez)" | Ç (test); Türkçe metne assert eder |
| `testler/test_panel_e2e.py` | 71 | 68 · pytest.skip("frontend derlenmemiş") | 84 · "TST: {ad: Sistem sınaması, klasor: sinama}" | Ç (test); görünen metne bakar |
| `testler/test_cekirdek.py` | 30 | 96 · "yeniden açıldı" in k2["not"] | 85 · onay.kaydet(…, "onay", "Taha", …) | Ç (test) |
| `testler/test_gecis.py` | 7 | 35 · "bölüm başlığında [tarama]" in n | 37 · etiket_esle("[ölçü]") | KALDIR |
| `testler/test_onbellek.py` · `test_regresyon.py` | 2 · 1 | test_onbellek.py:46 · b.ad == "boş alan" | test_regresyon.py:32 · f"{ad} hep {durum} dönünce regresyon yine geçti" | Ç (test) |
| `el-kitabi.md` | 386 (tamamı) | 1 · # Tasarım ve Mühendislik Süreç El Kitabı | 76 · \| Baş mühendis \| Taha \| … | Ç belge (tr asıl) |
| `ajanlar/*.md` (4 dosya) | ≈58 | kalite-muhendisi.md:8 · Sen kalite mühendisisin. İşi **görmemiş biri olarak**… | tekniker.md:15 · Çıktı: tek satır `GEÇTİ` ya da `KALDI: <neden>` | Ç (rol istemi, dil başına) |
| `kurallar/katalog.yaml` | ≈35 (11 kuralın metin/sınır/dayanak alanı) | 9 · metin: Her ölçünün bir kaynak etiketi vardır; etiketsiz değer… | 40 · metin: iPhone LiDAR taraması kritik geçme ölçüsü için… | SK (çok dilli alan) |
| `profiller/**/*.yaml` · `kurumlar/*/kurum.yaml` | ≈25 (yorum, not, ad) | kurum.yaml:3 · aciklama: Bisiklet ve motosiklet yedek parça… | fdm-cr10se-pla.yaml:3 · # Bu yazıcıda kalibrasyon yapılmadı… | AT |

### 9b. Görünen metni mantık anahtarı olarak kullanan yerler (çeviri mantığı kırar)

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `akis.py:292-293, 418-419` | ZORUNLU_KAPI_MADDELERI = {"G3": {"ENGEL sayısı sıfır"}, "G5": {"Sıfır ENGEL"…}} | görünen madde adı = anahtar | Ç | madde kimliği (ör. G3-01) gerek (§12 #15) |
| `onay_durumu.py:28` · `akis.py:287` · `kartlar.py:208, 241` | k.get("not", "").startswith("onaylı değer değişti") | not metni = durum bayrağı | Ç | ayrı bayrak alanı |
| `git.py:18, 52-57, 63-80` | EK_ANAHTARLARI = ["Adım", "Rol", "Kart", "Görsel"] · _EK = …[…ÇĞİÖŞÜçğıöşü-]… | commit ekleri Türkçe | Ç (protokol, çevrilmez) | ASCII anahtar + eski okuma |
| `akis.py:180, 194, 767, 848, 957, 979, 1085` · `gozcu.py:47` · `veriler.py:726` | f"Günlük: {baslik}" · baslik.startswith("Günlük:") | commit başlığı öneki = anahtar | Ç | ekle işaretlenmeli |
| `gunluk.py:30-31, 56-61` | f"### {z:%H:%M} · {ROL_ADI.get(rol, rol)} · {tur}" … s[4:].split("·") | görünen rol adı kayda yazılıp geri ayrıştırılıyor | Ç | rol kimliği yazılmalı |
| `veriler.py:449` | if "Baş mühendis" not in k["rol"] | görünen rol adına göre süzme | Ç | |
| `akis.py:122, 361, 574, 703, 895` · `dosya.ts:9` | tur="adım" / "kapı" / "baskı" / "karar" / "müdahale" · ["kapı", "baskı"] | günlük türü Türkçe sözcük | Ç | ASCII tür kimliği |
| `kalite.py:32-33` | ONEMLER = {"YÜKSEK": "YUKSEK", … "DÜŞÜK": "DUSUK"} · SATIR = …(YÜKSEK\|…) | ajan çıktısının Türkçe anahtarı | Ç · AA | |
| `kart_gorsel.py:740, 911` | baslik=f"SEÇENEK {ad.upper()} · …" · re.sub(r"<text[^>]*>SEÇENEK[^<]*</text>"…) | görsel başlığı karşılaştırmada | Ç | |

### 9c. Biçim ve yerel ayar sabitleri

| dosya:satır | kısa alıntı | neye bağlı | v1 hedef | not |
| --- | --- | --- | --- | --- |
| `kontroller/sonuc.py:33-40` | def mm(x): """Türkçe sayı yazımı… 3.0 → '3,0'""" … .replace(".", ",") | ondalık virgül | Ç-i18n | bütün kontrol iletileri kullanır |
| `akis.py:94` | f"Model: … mm (koddan ölçüldü)".replace(".", ",") | ondalık virgül | Ç-i18n | |
| `kart_gorsel.py:565` | str(KABUK_MM).replace('.', ',') | ondalık virgül | AP:fdm | |
| `panel/frontend/src/yardim.ts:5-29` | t.replace(".", ",") · toLocaleTimeString("tr-TR", …) | yerel ayar tr-TR | Ç-i18n | |
| `ekranlar/kartlar.ts:176` | Number(x.deger).toLocaleString("tr-TR", { maximumSignificantDigits: 3 }) | yerel ayar | Ç-i18n | |
| `ekranlar/dallar.ts:27, 35` | toLocaleLowerCase("tr") | Türkçe küçük harf | Ç-i18n | |
| `ekranlar/ciktilar.ts:12-13` | (b / 1024 / 1024).toFixed(1).replace(".", ",") MB | ondalık virgül | Ç-i18n | |
| `panel/frontend/index.html:2` | <html lang="tr"> | dil | Ç-i18n | |
| `akis.py:75-77` · `gecis.py:133-135` | str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU") | Türkçe harf → ASCII (dal/dosya adı) | Ç | dile bağlı çevirme tablosu |

## 10. kayit/ (çalışma verisi; taşınmaz) — dosya başına satır aralığı ve sayı

Bütün dosyalar `kayit/kurulum/` altında; v1 hedefi hepsi için **ÇV** (kurulum kaydı). Sayılar tarayıcının ham eşleşmesidir (yanlış eşleşme ayıklanmadı).

| dosya | eşleşen satır aralığı | kategori: satır sayısı (aralık) |
| --- | --- | --- |
| `gunluk/2026-10-26.md` (208 satır) | 5-206 | kişi 14 (12-205) · makine/yol 29 (9-206) · OS 9 (10-157) · tmux/Tailscale/RC 11 (7-205) · Üstteknik 15 (5-195) · FDM 10 (10-182) · tarama 1 (105) · Claude 7 (8-156) · kurum kodu 12 (19-196) |
| `kararlar.yaml` (283 satır) | 5-279 | kişi 2 (182-231) · makine/yol 5 (5-279) · OS 1 (7) · tmux/Tailscale 5 (186-272) · Üstteknik 13 (124-279) · FDM 13 (84-255) · tarama 1 (224) · Claude 3 (104-106) · kurum kodu 10 (124-272) |
| `kurulum-notlari.md` (106 satır) | 10-106 | kişi 5 (51-106; `loginctl enable-linger tahatas013` 96) · makine/yol 15 (14-100) · OS 26 (10-104; apt, systemctl, journalctl, ss, AppImage) · tmux/Tailscale 12 (21-105) · FDM 3 (45-49, OrcaSlicer) |
| `plu-eksikleri.md` (48 satır) | 1-48 | kişi 8 (15-34) · aero 11 (1-46; NeuralFoil 40, 46; Re 46) · FDM 14 (8-48) · FEA 1 (43) · Claude 4 (18-41) · kurum kodu 8 (1-45) |
| `el-kitabi-onerileri.md` (34 satır) | 11-33 | aero 2 (24-33) · FDM 11 (11-29; Bambu A1 18) · FEA 1 (25) · kurum kodu 5 (22-26) |
| `son-rapor.md` (36 satır) | 4-36 | OS 2 (4-33) · tmux/Tailscale 1 (32) · Üstteknik 4 (5-27) · FDM 1 (36) · Claude 2 (4-24) · kurum kodu 4 (5-27) |
| `izin-onerileri.md` (18 satır) | 1-18 | kişi 1 (3) · FDM 1 (17) · Claude 3 (1-18) |
| `kalite/K1.md` (27 satır) | 3-11 | tarama 1 (11) · Claude 1 (3) |
| `kalite/K2.md` (24 satır) | 3-24 | kişi 3 (7-16) · tmux/Tailscale 1 (18) · Üstteknik 2 (14-24) · FDM 1 (17) · Claude 2 (3-7) · kurum kodu 2 (14-24) |
| `kalite/K3.md` (24 satır) | 3-21 | kişi 2 (7-21) · tmux/Tailscale 1 (13) · Claude 2 (3-21) |
| `kalite/K4.md` (19 satır) | 3-18 | makine/yol 1 (14) · Üstteknik 2 (8-18) · tarama 1 (9) · Claude 1 (3) · kurum kodu 2 (8-18) |
| `kalite/KS.md` (19 satır) | 3-12 | Üstteknik 1 (11) · FDM 2 (8-12) · Claude 1 (3) · kurum kodu 1 (11) |
| `kalite/P2.md` (24 satır) | 3-24 | kişi 1 (18) · makine/yol 2 (21-23) · Üstteknik 4 (12-24) · FDM 3 (18-23) · Claude 1 (3) · kurum kodu 2 (12-13) |
| `hiz-olcumleri.txt` (15 satır) | — | eşleşme yok |

Toplam (yaklaşık): kişi 36 · makine/yol 52 · OS 38 · tmux/Tailscale/RC 31 · Üstteknik 41 · alan 78 (FDM 59, aero 13, tarama 4, FEA 2) · Claude 27 · kurum kodu 46.
Not: `kurulum-notlari.md` bir kayıt olsa da içeriği platform kurulum belgesidir (systemd birimi kurma, Tailscale serve); v1'de PA belgesine kaynak olur.

## 11. Elenen yanlış eşleşmeler

| dosya:satır | eşleşen | neden elendi |
| --- | --- | --- |
| `kart_gorsel.py:361-363` | `a1` | çizim koordinat değişkeni (`(a1, _) = P(x1, 0)`) |
| `hesap.py:108` | `a1` | hesap dosyası adı örneği ("a1 → a3") |
| `kayit/kurulum/plu-eksikleri.md:42` | `A1` | "G3, A1" analiz numarası |
| `akis.py:728` · `gecis.py:339-340` | `%h` | git `--format=%h`, systemd `%h` değil |
| `gorsel.py:3, 109, 118` | `tarama` | kesit taraması (hatching), 3B tarama değil |
| `kontroller/kayitsiz_gecme.py:57` · `katalog.yaml:67` · `H-001.md:35` · `el-kitabi.md:349` | `tarama` | "kayıtsız geçme taraması" (yüzey çifti arama) |
| `hesap.py:12` | `tarama` | "aerodinamik tarama" (aero süpürme; §6c'de) |
| `veriler.py:335` · `kartlar.ts:135` · `yardim.ts:14, 19` | `"T"` | ISO zaman ayırıcı |
| `api.ts:34, 36` | Türkçe sözcük | API yolu, metin değil |

## 12. Çekirdekte kalırsa ilkeyi bozacak en önemli 15 yer

1. **`veri.py:18, 318` · `onay.py:104` · `isler.py:49` · `veriler.py:35` · `gozcu.py:24`** — `SUREC_KOK` (kod reposunun kökü) altındaki `kurumlar/` ve `profiller/` okunuyor: kurum, makine ve ölçüm aleti kod reposunun içinde. → AT (`~/.config/<ad>/kurumlar`, `makineler`, `olcum`). `onay.py:104` `SUREC_KURUM_KOKU`'yu da yok sayıyor.
2. **`git.py:37-43`** (`akis.py:795, 873, 910, 1036`, `uygulama.py:109`, `gozcu.py:84`, `veriler.py:721`) — onay yetkilisi = makinenin `git config --global user.name`'i. Rol ↔ kişi eşlemesi makineye gömülü. → AT'de açık `onay_yetkilisi: {ad, eposta}`.
3. **`onay.py:103-112`** + `kurumlar/*/kurum.yaml:4` — yetki kişi adıyla (`onay_yetkilisi: Taha`), yalnız ilk ad karşılaştırılarak veriliyor; "Taha Test" de yetkili sayılır. → Ç'de kimlik eşleşmesi (e-posta ya da anahtar), değer AT'de.
4. **`isler.py:28`** — `VARSAYILAN_PROFILLER = {"uretim": "fdm-bambu-a1-pla@v0", "olcum": ["kumpas"]}`: her yeni çalışma belirli bir yazıcıya ve alete bağlanıyor. → AT varsayılanı.
5. **`veri.py:21, 302-305, 421-430`** — kaynak deseni `olcu:(kumpas|mastar|tarama)` ile aletler kodda sabit; her çalışmaya üretim profili zorunlu. → Ç'de genel `olcu:<alet>` ve isteğe bağlı profil; alet listesi AT'den.
6. **`akis.py:482-623, 797-805, 851-854, 961-980`** + **`kart_gorsel.py:547-614, 780-790, 900-906`** — süreç motorunda FDM: tabla teması, STL, filament ve süre tahmini, PLA 1,24 g/cm³, OrcaSlicer, `~/.local/share/surec/baski`. → Ç'de genel "üretime çıkış" Hold'u; geri kalanı AP:fdm.
7. **`kontroller/__init__.py:6-11`** + `akis.py:272-276` — mekanik geçme kontrolleri (GECME, VIDA, KATI, GIRISIM, KAYITSIZ, MONTAJ) her çalışmada koşulsuz çalışıyor, G2 maddeleri geçmeye bağlı. → kontrol kaydı Ç'de, kontroller AP:cad'den kayıtla.
8. **`kalite.py:87-91`** — bağımsız inceleme `claude -p --model opus --allowedTools "Read Grep Glob"` komutuna sabit. → ajan arayüzü Ç'de, komut ve model AA'da (`SUREC_KALITE_KOMUTU` adaptör ayarına).
9. **`durum.py:18-75`** + `isler.py:238-266` + `ana.py:187-209` — Claude Code kancaları: olay adları, `.claude/settings.json`, `.claude/agents`, `hookSpecificOutput`. → AA; Ç'de yalnız "ajan durumu" olayı.
10. **`gunluk.py:12-18`** + `ajanlar/*.md:4` + `ekip.ts:12-15` — model adları (Opus, Sonnet, Haiku) kalıcı günlüğe yazılıyor ve rol şablonlarında sabit. → Ç'de rol ve yetenek sınıfı, model eşlemesi AA'da.
11. **`isler.py:31-34, 219-281`** + `uygulama.py:99-101` + `veriler.py:647, 714` — tmux oturum yöneticisi olarak çekirdekte; "en çok 3 aktif çalışma" kuralı ve panel sekmeleri tmux oturumlarından sayılıyor. → PA (oturum yöneticisi arayüzü).
12. **`uygulama.py:46-52, 412-415`** + `ana.py:275` + `surec-panel.service` — `*.ts.net` (Tailscale) host izni, `127.0.0.1:8765` sabit, systemd birimi. → AT (adres, port, izinli host) ve PA (uzaktan erişim, servis).
13. **`gecis.py:1-406`** + `ana.py:285-299, 427-430` + `test_gecis.py` — ustteknik-arge'ye özgü tek seferlik geçiş: "taha" etiket kuralı (`gecis.py:128`), UST-DZL kodları, CR-10 SE, iPhone profili. → KALDIR.
14. **`veriler.py:200-206`** · `ortak.ts:42` · `ortak.ts:51` · `ekip.ts:11` · `yardim.ts:37` · `main.ts:80` — panelde kurum ve kişi sabitleri: `"UST"`/`"DZL"`/"Dizlik", `"BAG"` simgesi, `github.com/tahatas013`, "Taha", rozet harfi "T". → AT'den okunmalı.
15. **`akis.py:292-293`** · `onay_durumu.py:28` · `akis.py:287` · `git.py:18, 63` · `gozcu.py:47` · `gunluk.py:56-61` · `veriler.py:449` — Türkçe görünen metin mantık anahtarı olarak kullanılıyor (kapı madde adı, "onaylı değer değişti", "Adım/Görsel" ekleri, "Günlük:" öneki, "Baş mühendis" rol adı). Çeviri yapılınca kapı denetimi ve kayıt okuma bozulur. → Ç'de dil bağımsız kimlik + Ç-i18n.
