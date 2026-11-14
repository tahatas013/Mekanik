// The shell (old main.ts and ortak.ts): top bar (place, the agent's liveness and "Top", stop, open the session,
// TR/EN), work tabs (at most 3 open), the organization › project › work tree, screen navigation, the properties
// panel, the status bar; routing by hash (#/<code>/<screen>?…), live events (SSE), notices.
import "./style.css";
import { ApiError, get, post, setCsrf, W } from "./api";
import { h, lang, setCatalog, sha, store, t, u } from "./util";
import { confirm, copyButton, fail, mascot, toast } from "./ui";
import { flowScreen } from "./screens/flow";
import { cardsScreen } from "./screens/cards";
import { modelScreen } from "./screens/model";
import { intakeScreen } from "./screens/intake";
import { stdmapScreen } from "./screens/stdmap";
import { calcsScreen, filesScreen } from "./screens/files";
import { branchesScreen } from "./screens/branches";
import { designScreen } from "./screens/design";
import { newWorkScreen } from "./screens/newwork";
import { sessionScreen } from "./screens/session";

export interface Ctx { code: string; screen: string; q: Record<string, string>; work: any; main: HTMLElement; side: HTMLElement }
type Screen = (c: Ctx) => Promise<void>;
const SCREENS: Record<string, Screen> = { flow: flowScreen, intake: intakeScreen, cards: cardsScreen, model: modelScreen,
  stdmap: stdmapScreen, files: filesScreen, calcs: calcsScreen, analyses: calcsScreen, branches: branchesScreen,
  design: designScreen, session: sessionScreen };
const NAV = ["flow", "intake", "cards", "model", "stdmap", "files", "branches", "design", "session"];
const POLL_MS = 15000;   // source: assumption — old NABIZ_ARALIGI_MS; SSE `status` lines refresh it at once

export const S = { tree: [] as any[], tabs: { tabs: [] as any[], max: 3 }, code: "", screen: "flow", q: {} as Record<string, string>,
  live: {} as Record<string, any>, work: null as any, chief: "", roles: {} as Record<string, any>, onStream: null as null | ((e: any) => void),
  onInbox: null as null | ((e: any) => void), leave: null as null | (() => void), times: [] as { screen: string; ms: number }[] };
(window as any).__mekanik = S;
const app = document.getElementById("app")!;

export function go(code: string, screen = "flow", q: Record<string, string | undefined> = {}) {
  const s = new URLSearchParams(Object.entries(q).filter(([, v]) => v) as [string, string][]).toString();
  location.hash = `#/${code}/${screen}${s ? "?" + s : ""}`;
}
function route() {
  const [path, query] = location.hash.replace(/^#\/?/, "").split("?");
  const [code, screen] = path.split("/");
  Object.assign(S, { code: code || "", screen: code === "new" ? "new" : screen || "flow", q: Object.fromEntries(new URLSearchParams(query ?? "")) });
}
const works = () => S.tree.flatMap((o) => o.projects.flatMap((p: any) => p.works.map((w: any) => ({ ...w, org: o, project: p }))));
const COLOR: Record<string, string> = { red: "#B3261E", yellow: "#8A5A00", green: "#2E6B46" };
const LIVE: Record<string, string> = { working: "#2F6FDE", quiet: "#8A5A00", waiting: "#8A5A00", stopped: "#9AA6B2" };

function liveBadge(code: string): string {
  const v = S.live[code];
  if (!v) return "";
  const st = v.liveness.status, ago = v.liveness.minutes;
  return `<a class="ajan ${st === "waiting" ? "bekliyor" : ""}" data-live="${h(st)}" href="#/${h(code)}/flow?side=team"
    title="${h(t(v.ball.key, v.ball.data))}">${mascot(st)}<span>${h(u("agent"))}: <b>${h(t(`agent.liveness.${st}`))}</b>
    ${v.liveness.reason ? `· ${h(t(`agent.liveness.${v.liveness.reason}`))}` : ""}${ago !== null ? ` · <span class="sure">${
    h(u("minutes_ago", { n: ago }))}</span>` : ""}</span></a>${v.stop
    ? `<button class="mini-dugme" data-resume>${h(u("resume"))}</button>` : `<button class="mini-dugme ret" data-stop>■ ${h(u("stop"))}</button>`}`;
}

function shell(): string {
  const w = works().find((x) => x.code === S.code);
  const nav = S.code === "new" ? "" : NAV.map((k) => `<a href="#/${h(S.code)}/${k}" data-nav="${k}" class="${(k === "files" &&
    ["calcs", "analyses"].includes(S.screen)) || k === S.screen ? "secili" : ""}">${h(u(`nav.${k}`))}${k === "cards" && w?.open_cards
    ? ` <span class="sayi">${w.open_cards}</span>` : ""}</a>`).join("");
  return `<div class="kabuk">
<header class="ust"><button class="mini-dugme gezgin-ac" data-toggle-tree aria-label="${h(u("tree"))}">☰</button>
  <span class="marka">MEKANIK</span><span class="ayrac"></span>
  <nav class="konum">${w ? `<span>${h(w.org.name)}</span><span class="ok">›</span><span>${h(w.project.name)}</span><span class="ok">›</span>
    <b class="mono">${h(w.code)}</b><span class="soluk">${h(w.title)}</span>` : `<b>${h(u(S.code === "new" ? "new.title" : "no_work"))}</b>`}</nav>
  <span class="bosluk"></span><span data-live-slot>${w ? liveBadge(w.code) : ""}</span>
  ${w ? `<button class="mini-dugme" data-open-session>▶ ${h(u("open_session"))}</button>` : ""}
  <span class="dil" title="${h(u("ui_lang"))}">${["tr", "en"].map((l) => `<a data-lang="${l}" class="${lang() === l ? "secili" : ""}">${l.toUpperCase()}</a>`).join("")}</span>
</header>
${tabsBar(w)}
<div class="govde"><aside class="sol" aria-label="${h(u("tree"))}">${tree()}</aside>
  <main class="orta">${nav ? `<nav class="ekranlar">${nav}<div class="sag" data-nav-right></div></nav>` : ""}<div class="icerik" id="main"></div></main>
  <aside class="sag" id="side" aria-label="${h(u("properties"))}"></aside></div>
<footer class="alt" id="foot">${foot()}</footer></div>`;
}

function tabsBar(w = works().find((x) => x.code === S.code)): string {
  const open = S.tabs.tabs.map((x: any) => x.code);
  const tabs = [...S.tabs.tabs, ...(w && !open.includes(w.code) ? [{ code: w.code, title: w.title, faded: true }] : [])];
  return `<div class="sekmeler">${tabs.map((x: any) => `<a class="sekme ${x.code === S.code ? "secili" : ""} ${x.faded ? "soluk-sekme" : ""}"
  href="#/${h(x.code)}/${S.code === "new" ? "flow" : h(S.screen)}" data-tab="${h(x.code)}"><span class="kare" style="background:${
  LIVE[x.liveness?.status ?? "stopped"]}"></span><span class="mono">${h(x.code)}</span> <span class="ad">${h(x.title)}</span></a>`).join("")}
  <button class="sekme-ekle" data-pick title="${h(u("pick"))}">+</button><span class="not">${h(u("tabs_open", { n: S.tabs.tabs.length, max: S.tabs.max }))}</span>
  <div class="secici" data-picker hidden>${works().map((x) => `<a href="#/${h(x.code)}/flow"><span class="kare" style="background:${
    COLOR[x.color] ?? "#9AA6B2"}"></span><span class="mono">${h(x.code)}</span> ${h(x.title)}</a>`).join("")}
    <a href="#/new" data-new-work>+ ${h(u("new.title"))}</a></div></div>`;
}

function tree(): string {
  const sub = (k: string, n: string | number) => `<a class="agac-satir alt-satir ${S.screen === k ? "secili" : ""}" href="#/${h(S.code)}/${k}"
    data-tree="${k}"><span class="ad">${h(u(`nav.${k}`))}</span><span class="sag-bilgi">${h(n)}</span></a>`;
  const v = S.live[S.code];
  return `<div class="panel-baslik">${h(u("tree"))} <span class="normal soluk kucuk">${h(u("tree_hint"))}</span></div><div class="agac">${
    S.tree.map((o) => `<div class="agac-satir"><span class="ac">▾</span><span class="ad"><b>${h(o.name)}</b></span><span class="sag-bilgi">${h(o.code)}</span></div>
    ${o.projects.map((p: any) => `<div class="agac-satir g1"><span class="ac">▾</span><span class="ad">${h(p.name)}</span><span class="sag-bilgi">${h(p.code)}</span></div>
      ${p.works.map((x: any) => `<a class="agac-satir g2 ${x.code === S.code ? "secili" : ""}" href="#/${h(x.code)}/${S.code === "new" ? "flow"
        : h(S.screen)}" data-work="${h(x.code)}"><span class="kare" style="background:${COLOR[x.color] ?? "#9AA6B2"}"></span><span class="ad">
        <span class="mono">${h(x.code.slice(-2))}</span> ${h(x.title)}</span><span class="sag-bilgi">${h(x.error ? "!" : `${x.risk_class} · ${x.stage}`)}</span></a>
        ${x.code === S.code ? `<div id="tree-extra"></div>${sub("calcs", x.calcs ?? 0)}${sub("analyses", x.analyses ?? 0)}${sub("files", "↓")}` : ""}`).join("")}`).join("")}`).join("")}
  <a class="agac-satir yeni" href="#/new" data-new-work>+ ${h(u("new.title"))}</a></div>
  <div class="sol-alt"><div class="etiket-baslik">${h(u("waiting_here"))}</div>${v ? `<div class="satir">${h(u("for_chief"))}<span class="mono">${v.chief}</span></div>
    <div class="satir">${h(u("for_team"))}<span class="mono">${v.team}</span></div><div class="satir">${h(u("inbox_pending"))}<span class="mono">${v.inbox}</span></div>`
    : `<span class="soluk kucuk">${h(u("no_work"))}</span>`}</div>`;
}

function foot(): string {
  const w = S.work;
  return `${w ? `<span>${h(u("branch"))} ${h(w.branch)}</span><span data-foot-commit>${sha(S.q.commit ?? w.commit)}</span>
    <span class="say-engel">${h(t("status.block"))} <b>${w.summary.block}</b></span><span class="say-uyari">${h(t("status.warn"))} <b>${w.summary.warn}</b></span>
    <span>${h(u("stage"))} ${h(w.stage)}</span>` : ""}<span class="bosluk"></span><span data-clock>${new Date().toLocaleString(u("locale"), {
    dateStyle: "short", timeStyle: "short" })}</span>`;
}
setInterval(() => { const c = document.querySelector("[data-clock]"); if (c) c.textContent = new Date().toLocaleString(u("locale"), {
  dateStyle: "short", timeStyle: "short" }); }, 20000);

async function liveness(code = S.code) {
  if (!code || code === "new" || document.hidden) return;
  try {
    const v = await get(`${W(code)}/liveness`);
    const was = S.live[code]?.liveness.status;
    S.live[code] = v;
    if (code !== S.code) return;
    const slot = document.querySelector("[data-live-slot]");
    if (slot) slot.innerHTML = liveBadge(code);
    if (v.liveness.status === "waiting" && was !== "waiting")
      toast(`<b>${h(u("agent_waiting"))}</b> · ${h(t(v.ball.key, v.ball.data))} · <span class="mono">${h(code)}</span>`, "waiting");
  } catch { /* the panel may be restarting; next round */ }
}
setInterval(liveness, POLL_MS);

let drawn = 0;
export async function render() {
  const n = ++drawn, t0 = performance.now();
  route();
  if (!S.code) { const first = S.tabs.tabs[0]?.code ?? works()[0]?.code; return first ? go(first) : go("new"); }
  if (S.code !== "new" && !works().some((w) => w.code === S.code)) await refreshData().catch(() => {});   // a work opened since
  if (n !== drawn) return;
  S.onStream = S.onInbox = null;
  S.leave?.();
  S.leave = null;
  [S.work] = S.code === "new" ? [null] : await Promise.all([get(W(S.code), { branch: S.q.branch }).catch((e) => e), S.live[S.code] ? null : liveness()]);
  if (n !== drawn) return;
  const err = S.work instanceof ApiError ? S.work : null;
  if (err) S.work = null;
  app.innerHTML = shell();
  resizable();
  const main = app.querySelector<HTMLElement>("#main")!, side = app.querySelector<HTMLElement>("#side")!;
  try {
    if (err) throw err;
    await (S.code === "new" ? newWorkScreen : SCREENS[S.screen] ?? flowScreen)({ code: S.code, screen: S.screen, q: S.q, work: S.work, main, side });
    if (n === drawn) { S.times.push({ screen: S.screen, ms: performance.now() - t0 }); main.dataset.shown = S.screen; }
  } catch (e: any) {
    if (n === drawn) main.innerHTML = `<div class="hata-kutu" data-error="${h(e.key ?? "error")}">${h(e.message ?? e)}</div>`;
  }
}

const MIN_COL = 160;   // source: assumption — old genislet EN_AZ: the narrowest column (px), a layout value
/** The side columns widen by dragging their inner edge (old genislet.ts, E-09); double click resets; kept per browser. */
function resizable() {
  const g = app.querySelector<HTMLElement>(".govde");
  for (const [side, edge] of [["sol", "right"], ["sag", "left"]] as const) {
    const a = g?.querySelector<HTMLElement>(`aside.${side}`), k = `mekanik.width.${side}`;
    if (!g || !a) continue;
    if (store.get(k)) g.style.setProperty(`--${side}`, `${store.get(k)}px`);
    const t = Object.assign(document.createElement("div"), { className: `tutamac ${edge}`, title: u("resize") });
    t.dataset.resize = side;
    a.appendChild(t);
    t.addEventListener("dblclick", () => { store.set(k, null); g.style.removeProperty(`--${side}`); });
    t.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      t.setPointerCapture(e.pointerId);
      const x0 = e.clientX, w0 = a.getBoundingClientRect().width;
      const move = (m: PointerEvent) => g.style.setProperty(`--${side}`, `${Math.max(MIN_COL, w0 + (edge === "right" ? m.clientX - x0 : x0 - m.clientX))}px`);
      const up = () => { store.set(k, String(Math.round(a.getBoundingClientRect().width))); t.removeEventListener("pointermove", move); t.removeEventListener("pointerup", up); };
      t.addEventListener("pointermove", move);
      t.addEventListener("pointerup", up);
    });
  }
}

export async function refreshData() {
  [S.tree, S.tabs] = await Promise.all([get("/api/tree"), get("/api/tabs")]);
}
export async function reload() {
  await refreshData();
  await render();
}

export async function openSession(code: string) {
  try {
    const s = await post(`${W(code)}/session`);
    const dl = document.createElement("dialog");
    dl.className = "teyit";
    dl.dataset.session = "";
    dl.innerHTML = `<h2>${h(u("session.title", { code }))}</h2><p>${h(u("session.text"))}</p>
      <div class="dugme-sira"><a class="dugme birincil" data-deep-link href="${h(s.link)}">${h(u("session.link"))}</a>
      <a class="dugme" href="#/${h(code)}/session" data-close>${h(u("session.tab"))}</a></div>
      <div class="alt-baslik">${h(u("session.terminal"))}</div><div class="cli"><code data-command>${h(`${s.command} "${s.prompt}"`)}</code>${copyButton(`${s.command} "${s.prompt}"`)}</div>
      <div class="alt-baslik">${h(u("session.desktop"))}</div><div class="ozellik-izgara"><span class="ad">${h(u("session.folder"))}</span>
      <span class="mono kucuk">${h(s.path)} ${copyButton(s.path)}</span><span class="ad">${h(u("session.prompt"))}</span><span class="mono kucuk">${h(s.prompt)} ${copyButton(s.prompt)}</span></div>
      <div class="dugme-sira sag"><button class="dugme" data-close>${h(u("close"))}</button></div>`;
    document.body.appendChild(dl);
    dl.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => { dl.close(); dl.remove(); }));
    dl.showModal();
  } catch (e) { fail(e); }
}

export async function stopAgent(code: string) {
  const why = await confirm({ title: u("stop_title", { code }), text: u("stop_text"), yes: u("stop"), field: { label: u("stop_reason") } });
  if (why === null) return;
  try { await post(`${W(code)}/stop`, { text: why }); toast(h(u("stopped", { code })), "stop"); await liveness(code); } catch (e) { fail(e); }
}

app.addEventListener("click", async (e) => {
  const el = e.target as HTMLElement;
  if (el.closest("[data-stop]")) return stopAgent(S.code);
  if (el.closest("[data-resume]")) {
    try { await post(`${W(S.code)}/resume`); await liveness(); } catch (x) { fail(x); }
    return;
  }
  if (el.closest("[data-open-session]")) return openSession(S.code);
  if (el.closest("[data-toggle-tree]")) return document.body.classList.toggle("gezgin-acik");
  const l = el.closest<HTMLElement>("[data-lang]");
  if (l) { store.set("mekanik.lang", l.dataset.lang!); setCatalog(await get("/api/catalog", { lang: l.dataset.lang })); return render(); }
  if (el.closest("[data-pick]")) { const p = app.querySelector<HTMLElement>("[data-picker]")!; p.hidden = !p.hidden; }
});

// Live: a new version is announced, the open model never changes by itself (the user loads it, old e2e 6).
function events() {
  const src = new EventSource("/api/events");
  let lost = false;
  src.onerror = () => { lost = true; };
  src.addEventListener("ready", async () => {
    if (!lost || !S.work) return;
    lost = false;
    const w = await get(W(S.code)).catch(() => null);
    if (w && w.commit !== S.work.commit) toast(`<b>${h(u("new_version"))}</b> · ${h(u("while_offline"))}`, "new_version", { text: u("load"), run: () => reload() });
  });
  src.onmessage = (m) => {
    const ev = JSON.parse(m.data);
    if (ev.type === "new_version") {
      get("/api/tree").then((x) => { S.tree = x; }, () => {});
      if (ev.work === S.code) toast(`<b>${h(u("new_version"))}</b> · ${h(ev.line)} · <span class="mono">${sha(ev.commit)}</span>`, "new_version",
        { text: u("load"), run: () => { if (S.q.commit) go(S.code, S.screen); else reload(); } });
      else toast(`${h(ev.work)}: ${h(ev.line)}`, "other");
    } else if (ev.type === "status") {
      get("/api/tabs").then((x) => { S.tabs = x; const b = app.querySelector(".sekmeler"); if (b) b.outerHTML = tabsBar(); }, () => {});
      liveness();
    } else if (ev.type === "stream" && ev.work === S.code) S.onStream?.(ev.event);
    else if (ev.type === "inbox" && ev.work === S.code) { S.onInbox?.(ev); liveness(); }
    else if (ev.type === "signing") toast(h(u("signing", { card: ev.card })), "signing");
    else if (ev.type === "signed") document.querySelector('.bildirim[data-toast="signing"]')?.remove();
  };
}

async function start() {
  try {
    const s = await get("/api/session");
    setCsrf(s.csrf);
    S.chief = s.chief;
    S.roles = s.roles ?? {};
    setCatalog(await get("/api/catalog", { lang: store.get("mekanik.lang") || s.lang }));
    document.documentElement.lang = lang();
  } catch (e: any) {
    app.innerHTML = `<div class="giris" data-login-needed><span class="marka">MEKANIK</span><p>${h(e.message)}</p><code>mekanik panel</code></div>`;
    return;
  }
  window.addEventListener("hashchange", () => render());
  events();
  await reload();
  document.addEventListener("visibilitychange", () => liveness());
}
start();
