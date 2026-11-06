# Panel API sözleşmesi (v1, dalga 2.2)

Durum: çalışma belgesi · yazan rol: tasarım mühendisi (ajan B) · okuyan: ön yüz (ajan U, dalga 2.3) · kod: `src/mekanik/panel/`

Bu belge panel arka ucunun ön yüze verdiği sözleşmedir. Uç noktalar `src/mekanik/panel/app.py`'de, veri işleri `reads.py` (okuma) ve `writes.py` (yazma), canlı olaylar `events.py`, model `model.py`, erişim `auth.py`'dedir. Çelişki olursa kod kazanır ve bu belge düzeltilir. Makinece okunur şema: `GET /api/openapi.json` (oturumla).

## 1. Çalıştırma

- `mekanik panel` (CLI bağlaması W'nin) → `mekanik.panel.serve(host=None, port=None, rotate=False)`. Varsayılan adres atölye ayarındaki `panel.host` / `panel.port` (127.0.0.1:8765). Yalnız `127.0.0.1`, `::1`, `localhost` dinlenir; başka adres `Refused("panel.serve.loopback")`. Dışarı açmak platform adaptörünün işidir (`MEKANIK_PANEL_HOSTS` ortam değişkeni izinli Host adlarını ekler, ör. bir Tailscale adı).
- Açılışta terminale bir kez giriş bağlantısı yazılır: `http://127.0.0.1:8765/login?token=<sır>`. Sır `~/.local/state/mekanik/panel.secret` dosyasındadır (mod 600, yeniden başlatmada korunur; `rotate=True` yeniler). Ajan bu dosyayı okuyamaz, `mekanik panel` çalıştıramaz (PreToolUse engel listesi `panel`).
- Ön yüz derlemesi `src/mekanik/panel/static/` (tekerlekte) ya da geliştirmede `panel-ui/dist/` altından sunulur; `/api` dışındaki her yol `index.html`'e düşer (tek sayfa). Derleme yoksa 503 `panel.front.missing`.
- Uygulama fabrikası: `mekanik.panel.app.create_app(watch=True)` (testler ve gömülü kullanım için).

## 2. Erişim ve güvenlik (her istek)

Sıra: istemci → Host → oturum → (yazmada) Origin → CSRF → JSON. Ret gövdesi her zaman `{"error": {"key", "text", "data"}}`; ön yüz `key`'e bakar, `text`'i gösterir.

| Kural | Ret | Anahtar |
| --- | --- | --- |
| İstemci 127.0.0.1 ya da ::1 değil | 403 | `panel.auth.client` |
| `Host` yerel ad (127.0.0.1, localhost, ::1) ya da `MEKANIK_PANEL_HOSTS` değil | 403 | `panel.auth.host` |
| `/api/*` isteğinde `mekanik_session` çerezi yok ya da yanlış | 401 | `panel.auth.session` |
| Yazmada (GET/HEAD/OPTIONS dışı) `Origin` (yoksa `Referer`) yok ya da `Host`'tan farklı | 403 | `panel.auth.origin` |
| Yazmada `X-CSRF-Token` başlığı `GET /api/session`'daki `csrf` değil | 403 | `panel.auth.csrf` |
| Yazmada `Content-Type` `application/json` değil (yalnız `PUT …/inputs/{ad}` ham dosya alır) | 415 | `panel.auth.json` |

- Giriş: `GET /login?token=<sır>&next=/` → 303, çerez `mekanik_session` (HttpOnly, SameSite=Strict, Path=/; değeri sırrın HMAC'idir, sırrın kendisi değil). Yanlış belirteç 401.
- Gövdesiz POST'lar da `{}` JSON gönderir (`Content-Type: application/json`).
- Hata kodları: 400/422 giriş biçimi (FastAPI doğrulaması `{"detail": …}`), 401/403/415 erişim, 404 bilinmeyen çalışma, dosya, commit (`panel.error` ya da ilgili anahtar), 409 süreç reddi (`Refused`: anahtar süreç modülünündür, ör. `process.ready.dirty`, `process.ready.stale`, `panel.confirm.required`, `panel.branch.not_work`), 503 ön yüz yok.
- Sunulan dosyalar (indirme, görsel, kesit SVG) `Content-Security-Policy: default-src 'none'; …; sandbox` ve `X-Content-Type-Options: nosniff` ile gelir: tek başına açılan SVG betik çalıştırmaz. Ön yüz kart görsellerini `<img>` ile göstermelidir.

## 3. Onay kanalı (§4.6) ve teyit (Ö-14)

- Paneldeki her baş mühendis yazması süreç modülünden geçer: imzalı commit, Ö-07 (kirli klasöre ve eski sürüme yazılmaz: ekranda görülen commit `viewed` alanında gönderilir), APPROVAL-02. Kayıtta `channel: panel_confirmed`.
- Teyit penceresi zorunlu olanlar: seviyesi `hold` (DUR) olan kart, `decision`/`provisional_decision`/`gate`/`release` türü kartın onay ya da reti, her geri alma (`revert`), kapıya geri dönüş. İstekte `confirmed: true` yoksa 409 `panel.confirm.required` ve hiçbir şey yazılmaz. Varsayım listesi (V-01) gibi DUR olmayan kartlar tek tıkla onaylanır (eski davranış).
- İmza: baş mühendisin anahtarı `ssh-add -c` ile ekliyse her imzada masaüstü onay penceresi çıkar (T-17 b). Panel imzalı commit'ten önce ve sonra olay akışına `signing` / `signed` yollar; ön yüz "imza bekleniyor: <kart>" gösterir ve `GET /api/session`'daki `signing_key` parmak izini gösterebilir.
- Aynı çalışmaya aynı anda tek yazma yapılır (çalışma başına kilit).

## 4. Okuma uçları (GET)

`W` = `/api/works/{code}` (kod `AAA-BBB-nn`). `branch` sorgusu yalnız bu çalışmanın iş ya da karar dalıdır (`{code}/work/…`, `{code}/decision/…`); SHA, `HEAD`, ana hat ya da uydurma ad 409 `panel.branch.not_work`. Başka dal panelin yardımcı worktree'sinde okunur (`<önbellek>/branches/…`), ajanın worktree'sine dokunulmaz. Kontrol sonuçları ve kartlar kaydedilmiş HEAD'indir (HEAD + süreç imzasıyla önbellekli); klasör kirliyse (ajan çalışıyor) HEAD gösterilir. Git okumaları `GIT_OPTIONAL_LOCKS=0` ile yapılır (§4.10).

| Yol | Sorgu | Çıktı (özet) | Ekran |
| --- | --- | --- | --- |
| `/api/session` | — | `{csrf, chief, signing_key, lang, upload_limit}` | kabuk |
| `/api/catalog` | `lang` | düz sözlük: `panel.*`, `status.*`, `agent.liveness.*`, `num.*` (eksik EN anahtarı TR'ye düşer) | kabuk (çeviri) |
| `/api/tree` | — | `[{code, name, data_allowed, projects: [{code, name, works: [{code, title, risk_class, opened_at, stage, work_type, color: red|yellow|green, open_cards, hold, calcs, analyses} | {…, error}]}]}]` | sol ağaç |
| `/api/tabs` | — | `{tabs: [{code, title, liveness}], max: 3, chief, runs: [agent-run + updated_at]}` (açık oturumu olan çalışmalar) | sekmeler |
| `/api/cards` | — | bütün çalışmaların açık kartları (`work_title` ekli) | kartlar "hepsi" |
| `/api/new-work` | — | `{organizations: [{code, name, data_allowed, projects}], classes, work_types, packages}` | proje açma |
| `W` | `branch` | `{code, title, org, data_allowed, purpose, done_criterion, work_type, profiles, next_step, inputs, risk_class, opened_at, stage, gates, passed, branch, commit, summary: {block, warn, pass}, color, open_cards, hold, calcs, analyses, dirty, branches}` | üst satır |
| `W/stages` | — | `{stage, stages: [{gate, status: done|in_progress|pending|not_applicable, planned, started_at, finished_at, tag, approver, commit, model_commit, summary, steps: [{at, role, line, commit}], decisions: [{id, title, status, chosen, mode, options}]}], activity}` | aşamalar (e2e 2) |
| `W/status` | — | `liveness` alanları + `{title, purpose, stage, gates, summary, rows: [{kind: chief|team|idle, key, data, text}], chief_cards, team_cards, run, last: {at, who, title}, steps, next, dirty}` | durum, akış sağ paneli |
| `W/liveness` | — | `{liveness: {status: working|quiet|waiting|stopped, reason, minutes, role, doing, log}, ball: {who, kind, key, data, text}, chief, team, stop, lock, inbox}` — birkaç saniyede bir sorulur | üst çubuk rozeti (e2e 7) |
| `W/cards` | `branch`, `commit` | `{branch, commit, past, head, summary, results: [{check, rule, status, msg, args, ref, value, extra, reason}], cards, params (params.yaml), records (paket kayıtları, ör. mech `fits`), approvals (yeniden eskiye), decisions, requirements}`; `commit` geçmiş sürümü geçici worktree'de okur | kart, model yanı |
| `W/calcs` | `branch` | `{commit, calcs: [records/calcs/*.json], unrecorded}` | hesaplar (e2e 14) |
| `W/files` | — | `{folders: [{path, kind: release|records|inputs, files: [{path, name, size, sha256, matches}]}]}`; `matches` baskı raporundaki özetle karşılaştırmadır | dosyalar (e2e 16) |
| `W/download/{path}` | — | dosya olduğu gibi, klasör zip; yalnız `out/`, `records/`, `inputs/` altı; dışı 404 | dosyalar |
| `W/images/{path}` | `branch` | çalışma klasörü içindeki `.svg .png .jpg .jpeg .md .step .stl`; dışı 404 | kart görselleri |
| `W/branches` | — | `{branches: [{name, short, kind: main|work|decision, head, status, current, steps}], folded, commits: [{sha, parents, visible_parents, author, at, title, step, role, cards, branch, tags}]}` | dal haritası (e2e 5) |
| `W/steps/{sha}` | — | `{commit, parents, author, at, title, text, trailers, files: [{path, added, removed}], params: [{name, before, after}], code_diff: [{path, lines}], calcs: [{path, results}], summary, first}` | ekip, adım ayrıntısı (e2e 15) |
| `W/design-file` | `branch` | `{last_read, new, events, done, found, waiting, checks: [{check, status, open, total}], log: [gün dosyaları], summary}` | tasarım dosyası |
| `W/stream` | `offset` | `{events: [stream-event], offset}` — bayt ofseti; ilk yükleme `offset=0`, sonrası SSE | akış |
| `W/inbox` | — | `{items: [{id, kind: instruction|stop|resume, at, by, via, text, state: pending|delivered|read, receipts}]}` | akış altındaki talimat kutusu |
| `W/summary` | `day` | `{day, sections: {decisions, pending, risks, agents}}` (taslak, gün sonu özeti) | akış sağ paneli |
| `W/policy` | — | `{metrics: {gate, questions_asked, questions_limit, provisional_made, provisional_reverted, revert_rate, time_to_answer}, line}` | "ölçüler bu aşamada" |
| `W/intake` | — | `{work_type, types, plan: {nodes, limit, asked_now, findings, now, stage_end}, answers, summary, summary_status}` | tanımlama |
| `W/stdmap` | — | `{items: [madde + shown_status, priority, mandatory], counts}` | standart haritası |
| `W/model` | `commit`, `branch` | `{"commit": sha, "data": <three-cad-viewer tessellation> | null}` (önbellekten olduğu gibi) | model (A4) |
| `W/cylinders` | `commit` | `[{part, face, path, diameter}]` (tam geometriden) | model ölçüm listesi (e2e 3) |
| `W/fit-markers` | `commit`, `branch` | `[{id, status: pass|fail|review, position, axis, card, reasons}]` (paketin konumlu kayıtları; mech'te geçmeler) | model işaretleri (e2e 10) |
| `W/sections/{ref}` | `commit`, `branch` | ölçülü kesit SVG; eksen yoksa 404 | geçme kartı (e2e 9) |

## 5. Yazma uçları

Hepsi oturum çerezi, aynı köken `Origin`, `X-CSRF-Token` ister; gövde JSON'dur.

| Yöntem ve yol | Gövde | Çıktı | Not |
| --- | --- | --- | --- |
| `POST /api/works` | `{org, project, title, risk_class, purpose?, done_criterion?, work_type?}` | `{code, path, branch, cli}` (`cli`: CLI eşdeğeri) | proje/çalışma açma (A1) |
| `POST W/session` | `{}` | `{path, prompt, command, link}`; `link` = `claude-cli://open?cwd=…&q=/mekanik:resume <kod>` | "Oturumu aç": panel hiçbir şey başlatmaz (T-09); veri aktarımı yasak kurumda 409 `panel.session.data_forbidden`; en çok 3 etkin çalışma (409 `store.open.limit`) |
| `POST W/instructions` | `{text}` | gelen kutusu kaydı | ajana talimat (A1, A12); boş metin 409 `panel.inbox.empty` |
| `POST W/stop` | `{text?}` | gelen kutusu kaydı | durdurma bayrağı + bildirim (A5) |
| `POST W/resume` | `{}` | gelen kutusu kaydı | bayrak kalkar |
| `POST W/cards/{id}/decision` | `{action: approve|reject|comment, reason?, option?, rows?, viewed?, branch?, confirmed?}` | süreç çıktısı (`commit`, kapıda `gate: {tag, merge, next}`, kararda `decision`, `merge`) | onay, ret, yorum; karar kartında `option`, V-01'de `rows`; yorum boşsa 409 `panel.confirm.comment_empty` |
| `POST W/cards/{id}/revert` | `{reason, row?, viewed?, branch?, confirmed: true}` | `{card, undone, commit}` | geri alma (Ö-15); nedensiz 409 `panel.confirm.undo_reason`; kapı/baskı geri alınmaz (`process.undo.gate_release`) |
| `POST W/values` | `{param, value, reason?, card, viewed?, branch?}` | değer adımı (`commit`, `value_commit` …) | baş mühendisin değeri (`value_change` imzalı) |
| `POST W/model-notes` | `{text, png: "data:image/png;base64,…", commit?, part?, point?, camera?, box?}` | `{card: N-nn, visual, commit}` | modelde not (e2e 17); bozuk görüntü 409 `process.note.bad_image` |
| `POST W/decisions/{id}/objection` | `{reason, viewed?}` | süreç çıktısı | geçici karara itiraz (§8.1) |
| `POST W/gates/{G}/back` | `{reason, viewed?, confirmed: true}` | `{gate, from, tag, commit}` | kapıya geri dönüş (Ö-17) |
| `POST W/branches` | `{commit, name}` | `{branch}` | geçmiş bir noktadan iş dalı; hiçbir şey silinmez (e2e 5); ad `[a-z0-9-]` (409 `panel.branch.bad_name`, `panel.branch.exists`) |
| `POST W/read-mark` | `{}` | `{last_read}` | tasarım dosyası "okudum" |
| `POST W/intake/answer` | `{key, value}` | cevap kaydı | baş mühendisin tanımlama cevabı (kayıt dosyası yazılır, commit'i ekip adımı atar) |
| `PUT W/inputs/{name}` | ham dosya (`application/octet-stream`) | `{path, sha256, added_at, commit}` | dosya ekleme (A1): `inputs/<ad>`, SHA-256 `work.yaml` `inputs`'a, tek commit; klasör temiz olmalı (Ö-07); var olan girdi üzerine yazılmaz (409 `panel.upload.exists`); ad `[\w.() -]`, klasörsüz (409 `panel.upload.bad_name`); sınır `panel.upload_limit` (yoksa 512 MB; 409 `panel.upload.too_large`) |
| `POST /api/measure` | `{work, commit, tool: PropertiesMeasurement|DistanceMeasurement, paths, center?}` | three-cad-viewer `backend_response`/`tool_response` (alanlar İngilizce; kaynak `source: exact`) | ölçüm (e2e 3) |

## 6. Canlı olaylar: `GET /api/events` (SSE)

Her satır `data: <JSON>`; bağlanınca `event: ready`, 15 s'de bir `: alive` yorumu. Olay türleri (`type`):

| `type` | Alanlar | Kaynak |
| --- | --- | --- |
| `stream` | `work`, `event` (stream-event şeması) | çalışmanın `records/events.jsonl`'ine eklenen her satır (başka süreçler dahil; 0,2 s'de bir okunur); panelin kendi sürecindeki kalıcı olmayan olaylar `report.stream.LISTENERS`'tan |
| `new_version` | `work`, `kind`, `commit`, `line`, `role`, `at` | commit'li akış satırı (adım, kapı, onay …): açık model kendiliğinden değişmez, kullanıcı yükler (e2e 6) |
| `status` | `runs` (son 20 agent-run + `updated_at`) | oturum kayıtları, nabız, durdurma bayrağı, kilit değişince (e2e 7) |
| `inbox` | `work`, `items` | gelen kutusu değişince (talimat, iletildi, okundu) |
| `signing` / `signed` | `work`, `card` | imzalı commit'ten önce / sonra |
| `error` | `text` | izleyici iş parçacığının hatası |

Ölçü (A2): olay → SSE satırı p95 0,20 s; kanca → `status` p95 0,23 s (100 olay, `tests/panel/test_live.py`). Yeni açılan bir çalışma izleyiciye en geç 5 s içinde girer.

## 7. Oturum sekmesi (A13, dalga 2.3): `WS W/pty`

İskelet hazır: yalnız 127.0.0.1 istemci, izinli Host, oturum çerezi ve aynı köken `Origin`; eksikse bağlantı kabul edilmeden 4401 ile kapanır. Yetkili bağlantı şimdilik `{"error": {"key": "panel.pty.later"}}` yollayıp 4501 ile kapanır; terminal (PTY + xterm.js) dalga 2.3'te bu uca gelir. Talimat kutusu bu terminale yazmaz (§5.4 T-18a). Not: uvicorn'un gerçek WebSocket sunması için `websockets` ya da `wsproto` paketi gerekir; şu an kurulu değil (bağımlılık kararı proje mühendisinin).

## 8. Ajan tarafı (eklenti)

- Gelen kutusu `~/.local/state/mekanik/inbox/<kod>.jsonl` (yalnız eklenir): `mekanik.agent.inbox.send(code, text, by="chief_engineer", via="panel")`, `stop(code, reason="", …)` (durdurma bayrağı `state/stop/<kod>` + bildirim), `resume(code, …)`, `items(code)`, `take(code, via, session="")` (bekleyenleri iletildi işaretler), `mark_read(code, ids, via="mcp")`, `line(item)`.
- Monitor `plugin/monitors/monitors.json` → `mekanik watch`: oturum açılınca önce bekleyen iletileri, sonra 0,5 s'de bir yenilerini ve baş mühendis commit'lerini basar. Masaüstü/VS Code'da monitor doğrulanana kadar yedek yol kancalardır: `UserPromptSubmit` bağlama ekler, `Stop` bekleyen varken durmayı engeller (yalnız kilit sahibi oturum alır).
- Oturum kilidi (A8) `~/.local/state/mekanik/locks/<kod>.json`: ilk oturum alır; ikinci oturum `SessionStart`'ta uyarı alır ve yazan araçları reddedilir (okuma, `git status|log|diff|show`, `mekanik check|pending|agent status`, MCP `work_status|pending|panel_url` geçer). Sahibin `SessionEnd`'i ya da 30 dk sessizliği kilidi bırakır. Panelde `liveness.lock`.
- Engel listesi (`claude_code.yaml`): ajan `mekanik panel`, `mekanik agent send|stop` çalıştıramaz, `~/.local/state/mekanik` ve `panel.secret`'e dokunamaz; baş mühendisin TTY komutları (`approve`, `value`, `object`, `gate pass|back`, `verify --pin`) reddedilir; `org.yaml`, `.claude/agents|hooks`, `.claude/settings*.json`, `.mcp.json` yazılamaz.
- MCP sunucusu `plugin/.mcp.json` → `mekanik mcp` → `mekanik.agent.mcp.serve()`: araçlar `work_status`, `pending`, `inbox`, `note`, `panel_url`. Onay, imza, kapı ya da sır aracı yoktur.
