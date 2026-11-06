# Araştırma A — Panelin ajanı arka planda çalıştırması

Belge: mekanik v1 · Faz 0 · araştırma notu A
Yazan rol: proje-muhendisi · Tarih: 2026-11-06 (sistem saati) · Durum: inceleme bekliyor
Erişim tarihi (bütün kaynaklar): 2026-11-06. Sayfalar `curl` ile indirilip metinden okundu; alıntılar birebir İngilizcedir.

## 1. Soru

Panel (FastAPI arka uç, tek kullanıcı, kullanıcının kendi Ubuntu makinesi) Claude Code ajanını arka planda başlatacak, durduracak, ona talimat gönderecek ve çıktısını canlı akış olarak gösterecek. İki yol:

1. **Claude Code CLI, headless** (`claude -p`). Kullanıcı Claude aboneliğiyle ya da kendi API anahtarıyla giriş yapar.
2. **Claude Agent SDK** (Python `claude-agent-sdk`, TypeScript `@anthropic-ai/claude-agent-sdk`), API anahtarıyla.

Karşılaştırma ölçütleri: kimlik doğrulama, maliyet, kullanım şartları, teknik uygunluk (akış, kesme, sürdürme, izin).

## 2. Bulgular (doğrulama durumu: hepsi `metin_elde`)

### 2.1 Agent SDK, Claude Code ikilisinin üstünde bir kütüphanedir

- Agent SDK tanımı: "A library that runs the Claude Code binary, with Claude Code's capabilities, such as built-in tools, permissions, sessions, and hooks." ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview))
- Python ve TypeScript dışından aynı döngüyü sürmek için: "run the CLI as a subprocess with the `-p` flag and `--output-format json`." (aynı sayfa)
- Sonuç: iki yolda da aynı motor (Claude Code ikilisi) çalışır. Fark, kütüphanenin sağladığı Python API'si ile kimlik doğrulama ve şartlardadır.

### 2.2 Kimlik doğrulama

| Yöntem | CLI `-p` | Agent SDK | Kaynak |
| --- | --- | --- | --- |
| Abonelik girişi (`/login`, Pro/Max/Ultra) | Evet: "Subscription OAuth credentials from `/login`. This is the default for Claude Pro, Max, Ultra, Team, and Enterprise users." | Üçüncü taraf ürünlerde **izin yok** (aşağıda §2.4) | [Authentication](https://code.claude.com/docs/en/authentication) |
| Uzun ömürlü token (`claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`) | Evet: "For CI pipelines, scripts, or other environments where interactive browser login isn't available, generate a one-year OAuth token". Token "authenticates with your Claude subscription and requires a Pro, Max, Ultra, Team, or Enterprise plan." | Aynı kısıt | [Authentication](https://code.claude.com/docs/en/authentication) |
| `ANTHROPIC_API_KEY` | Evet: "In non-interactive mode (`-p`), the key is always used when present." | Evet (önerilen yol) | [Authentication](https://code.claude.com/docs/en/authentication), [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) |
| `--bare` kipi | Abonelik kullanmaz: "In bare mode, Claude Code never reads OAuth credentials or the system keychain." | — | [Headless](https://code.claude.com/docs/en/headless) |

Not: Kimlik bilgisinin öncelik sırası belgede tanımlıdır. `ANTHROPIC_API_KEY` tanımlıysa abonelik girişinin önüne geçer: "If you have an active Claude subscription but also have `ANTHROPIC_API_KEY` set in your environment, Claude Code uses the API key once you approve it." Panel, ajanı başlatırken ortam değişkenlerini bilinçli seçmelidir.

### 2.3 Maliyet

**Abonelik** ([claude.com/pricing](https://claude.com/pricing), 2026-11-06):

| Plan | Fiyat | Kullanım | Not |
| --- | --- | --- | --- |
| Pro | aylık 20 USD (yıllık ödemede ayda 17 USD) | Free'den fazla; 5 saatlik ve haftalık sınır | Claude Code dahil |
| Max | aylık 100 USD | "5x Pro usage every 5 hours and every week" | "$100 a month in API credits to build on the Claude Platform" (dipnot metni okunamadı: `ikincil_kaynak`) |
| Ultra | aylık 200 USD | "No 5-hour limit", "10x Pro usage every week" | "$200 a month in API credits" |

**API**, 1M token başına ([platform.claude.com pricing](https://platform.claude.com/docs/en/about-claude/pricing)):

| Model | Girdi | Önbellek okuma | Çıktı |
| --- | --- | --- | --- |
| Claude Opus 5.5 | 4 USD | 0,20 USD | 20 USD |
| Claude Sonnet 5.5 | 2 USD | 0,10 USD | 10 USD |
| Claude Haiku 5.5 (100 000 token'a kadar istem) | 0,10 USD | 0,01 USD | 0,50 USD |

Büyüklük sırası için tek resmî veri: "Across enterprise deployments, the average cost is around $13 per developer per active day and $150-250 per developer per month, with costs remaining below $30 per active day for 90% of users." ([Costs](https://code.claude.com/docs/en/costs)). Bu, kurumsal geliştiricilerin ortalamasıdır; bizim kullanımımızın ölçüsü değildir. Gerçek değer Faz 1'de ölçülecek (`--output-format json` çıktısındaki `total_cost_usd`).

Bütçe sınırı: `--max-budget-usd` "Stop the run once estimated spend on API calls reaches this amount (print mode only)." ([CLI reference](https://code.claude.com/docs/en/cli-reference))

### 2.4 Kullanım şartları

1. **Hangi şart geçerli:** "Your use of Claude Code is subject to: Commercial Terms of Service - for Team, Enterprise, and Claude API users; Consumer Terms of Service - for Free, Pro, Max, and Ultra users" ([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance))
2. **Consumer Terms, otomasyon maddesi** (yürürlük 8 Ekim 2025). Yasak davranışlar arasında: "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it, to access the Services through automated or non-human means, whether through a bot, script, or otherwise." ([Consumer Terms](https://www.anthropic.com/legal/consumer-terms))
3. **OAuth'un amacı:** "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Ultra, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications." ([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance))
4. **Geliştiriciler ve Agent SDK:** "Developers building products or services that interact with Claude's capabilities, including those using the Agent SDK, should use API key authentication through Claude Console or a supported cloud provider. Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens — sign-in to a Claude account must complete through Anthropic's own flow." (aynı sayfa)
5. **Kendi aboneliğiyle değiştirilmemiş ikili:** "Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription, including where a platform hosts Claude Code as described under *Can customers offer Claude Code in their products?* above." (aynı sayfa)
6. **Agent SDK notu:** "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Use the API key authentication methods described in the Quickstart instead." ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview))
7. **Kullanım sınırı varsayımı:** "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage of Claude Code and the Agent SDK." ([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance))
8. **Ürüne gömme koşulları:** "The Claude Code binary must not be modified." ve "Customers may not pay for, resell, or intermediate Claude usage on their end users' behalf. Each end user must authenticate with their own Anthropic API key, Claude subscription plan credentials, or 3P inference provider credential" (aynı sayfa)
9. **Ad ve logo:** "you can't use the Claude Code or Anthropic names or logos as part of your own product, feature, or company name" (aynı sayfa)

### 2.5 Lisanslar

| Bileşen | Lisans | Kaynak |
| --- | --- | --- |
| `claude-agent-sdk` (Python) 0.2.178 | MIT ("Copyright (c) 2025 Anthropic, PBC") | [LICENSE](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/LICENSE), PyPI sınıflandırıcısı |
| `@anthropic-ai/claude-agent-sdk` (TS) 0.3.318 | "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service." | [LICENSE.md](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-typescript/main/LICENSE.md), npm `license: SEE LICENSE IN README.md` |
| Claude Code CLI (`@anthropic-ai/claude-code` 2.1.318) | Tescilli; npm `license: SEE LICENSE IN README.md` | npm kayıt bilgisi |
| Agent SDK kullanımı | "Use of the Claude Agent SDK is governed by Anthropic's Commercial Terms of Service … except to the extent a specific component or dependency is covered by a different license" | [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) |

Python SDK paketi platforma özgü tekerlek (wheel) olarak yayımlanıyor (`manylinux_2_17_x86_64` vb.). Bu, Claude Code ikilisini içerdiği izlenimini veriyor ama tekerleğin içine bakılmadı (`dogrulanmadi`). AGPL açısından sonuç: tescilli Claude Code ikilisi mekanik ile **birlikte dağıtılmaz**. Kullanıcı onu kendisi kurar, mekanik onu ayrı bir süreç olarak çağırır. Ayrıntı lisans tablosundadır.

### 2.6 Teknik uygunluk (headless CLI)

| İhtiyaç | CLI karşılığı | Kaynak |
| --- | --- | --- |
| Canlı akış | `--output-format stream-json --verbose --include-partial-messages` ("newline-delimited JSON for real-time streaming") | [Headless](https://code.claude.com/docs/en/headless) |
| Çok turlu talimat | `--input-format stream-json` (stdin'den satır satır JSON ileti) | [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Turu durdurma | "To end the turn instead, send SIGINT, or call the Agent SDK's `interrupt()`, before you stop the process." SIGTERM'de: "Claude Code exits with code 143. Claude Code leaves the turn that was in progress unfinished and records no result for it." | [Headless](https://code.claude.com/docs/en/headless) |
| Sürdürme | `--resume <session-id>`; `--session-id <uuid>` ile kimliği baştan vermek; `--fork-session` | [Headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Kayıt yeri | "`~/.claude/projects/<project>/<session-id>.jsonl`"; varsayılan saklama 30 gün (`cleanupPeriodDays`) | [Sessions](https://code.claude.com/docs/en/sessions) |
| Paneldeki onay | `--permission-prompt-tool mcp__<server>__<tool>`: "Specify an MCP tool to handle permission prompts in non-interactive mode" (ya da `PermissionRequest` kancası) | [CLI reference](https://code.claude.com/docs/en/cli-reference), [Headless](https://code.claude.com/docs/en/headless) |
| İzin kipi | `--permission-mode` (`default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`); "With Claude Code v2.1.302 or later, `claude -p` runs start in Manual mode when nothing sets a permission mode." | [Headless](https://code.claude.com/docs/en/headless) |
| Maliyet izleme | `json` çıktısında `total_cost_usd` ve model başına döküm; "client-side estimates" | [Headless](https://code.claude.com/docs/en/headless) |
| Güvenlik uyarısı | "Without `--bare`, a `-p` session runs the hooks in a project's `.claude/settings.json` and connects the servers in its `.mcp.json`, even in a folder you've never trusted." | [Headless](https://code.claude.com/docs/en/headless) |
| Sürüm algılama | `system/init` olayındaki `capabilities` dizisi (ör. `interrupt_receipt_v1`): "Check it to feature-detect instead of comparing version strings" | [Headless](https://code.claude.com/docs/en/headless) |
| Hata türleri | `authentication_failed`, `rate_limit`, `billing_error`, `overloaded` … | [Headless](https://code.claude.com/docs/en/headless) |

Agent SDK bunların hepsini bir Python API'siyle verir: `ClaudeSDKClient`, `interrupt()`, `can_use_tool` geri çağrısı, kancalar. Altta yine aynı ikiliyi çalıştırır.

## 3. Karşılaştırma

| Ölçüt | CLI headless (`claude -p`, kullanıcının kendi girişi) | Agent SDK (API anahtarı) |
| --- | --- | --- |
| Kimlik doğrulama | Kullanıcının abonelik girişi ya da kendi API anahtarı; panel kimlik bilgisine dokunmaz | Kullanıcının API anahtarı (abonelik girişi üçüncü taraf üründe izinli değil) |
| Maliyet | Abonelikte sabit aylık (sınırlar içinde); API anahtarıyla token başına | Token başına (API fiyatı) |
| Şart durumu, kişisel kullanım | Belgelenmiş kullanım (`-p`, `setup-token` "for … scripts"); sınırlar "ordinary, individual usage" varsayımıyla | Açıkça önerilen yol |
| Şart durumu, açık kaynak dağıtım | Her kullanıcı kendi değiştirilmemiş ikilisine kendi hesabıyla girer; mekanik giriş sunmaz, token saklamaz | Her kullanıcı kendi API anahtarını kullanır |
| Akış / kesme / sürdürme | stream-json, SIGINT, `--resume` | `ClaudeSDKClient`, `interrupt()`, `resume` |
| Panelde onay | `--permission-prompt-tool` (MCP) ya da kanca | `can_use_tool` |
| Bağımlılık | Sistemde kurulu `claude`; sürüm kayması riski | Python paketi (MIT); altta yine ikili |
| Başka ajan bağlama | Adaptör arayüzü olayları normalleştirir | Aynı |

## 4. Sonuç ve öneri (yorum; karar baş mühendisin)

**Öneri: ince bir `AgentAdapter` arayüzü ve onun ilk uygulaması olarak Claude Code CLI headless.**

1. Panel `claude -p --input-format stream-json --output-format stream-json --verbose` sürecini çalışma klasöründe başlatır. Olayları normalleştirip akışa basar. Turu SIGINT ile keser, `--resume` ile sürdürür. Onay isteklerini `--permission-prompt-tool` ile panele taşır.
2. Kimlik doğrulamayı mekanik yapmaz. Kullanıcı `claude` içinde `/login` ile kendi hesabına girer ya da `ANTHROPIC_API_KEY`'i kendisi tanımlar. Mekanik hiçbir token okumaz, saklamaz, iletmez. Bu, alıntı 4'teki yasakların ("offer Claude.ai login", "collect, store, or intermediate") dışında kalmanın en temiz yoludur. Alıntı 5 de kullanıcının kendi aboneliğiyle değiştirilmemiş ikiliye girmesini açıkça engellemiyor.
3. Ayar dosyasında `agent.auth: subscription | api_key` seçimi bulunur. `api_key` seçilirse `--max-budget-usd` zorunlu olur.
4. Agent SDK ikinci adaptör olarak eklenebilir (Python, MIT). Abonelikle kullanılmaz.

**Gerekçe:** Agent SDK zaten aynı ikiliyi çalıştırıyor. Kişisel kullanımda abonelik ancak CLI yoluyla şartlara uygun biçimde kullanılabiliyor. Açık kaynak dağıtımda iki yol da "her kullanıcı kendi hesabı" ilkesine uyuyor.

**Açık risk (yorum):** Consumer Terms'teki otomasyon yasağının istisnası "where we otherwise explicitly permit it". `-p` kipinin ve `setup-token`'ın ("for CI pipelines, scripts") belgelenmiş olması bu istisnaya giriyor diye okunabilir, ama bu bir yorumdur. Sınırların "ordinary, individual usage" varsayımı da gözetimsiz, uzun süren döngülerin abonelikle çalıştırılmasını sınırlar. Bu yüzden mekanik ajanı yalnız baş mühendisin başlattığı çalışmalarda ve tur/bütçe sınırıyla çalıştırır. Kendiliğinden yeni oturum açmaz (eski sistemdeki E-14 sorusunun cevabı da budur). Kesin hukuki yorum için Anthropic satış ekibine sorulabilir ("contact sales" bağlantısı).

**Baş mühendisin kararı gereken nokta (maliyet etkisi):** Varsayılan kimlik doğrulama abonelik mi, API anahtarı mı? Bkz. ana belge "Açık kararlar" T-01.

## 5. Kaynaklar

| URL | Doğrulama |
| --- | --- |
| https://code.claude.com/docs/en/headless | metin_elde |
| https://code.claude.com/docs/en/cli-reference | metin_elde |
| https://code.claude.com/docs/en/authentication | metin_elde |
| https://code.claude.com/docs/en/legal-and-compliance | metin_elde |
| https://code.claude.com/docs/en/agent-sdk/overview | metin_elde |
| https://code.claude.com/docs/en/sessions | metin_elde |
| https://code.claude.com/docs/en/costs | metin_elde |
| https://www.anthropic.com/legal/consumer-terms | metin_elde (yürürlük 8 Ekim 2025) |
| https://claude.com/pricing | metin_elde (Max/Ultra API kredisi dipnotu okunamadı) |
| https://platform.claude.com/docs/en/about-claude/pricing | metin_elde |
| https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/LICENSE | metin_elde |
| https://raw.githubusercontent.com/anthropics/claude-agent-sdk-typescript/main/LICENSE.md | metin_elde |
| https://pypi.org/pypi/claude-agent-sdk/json, https://registry.npmjs.org/@anthropic-ai/claude-code/latest | metin_elde |
