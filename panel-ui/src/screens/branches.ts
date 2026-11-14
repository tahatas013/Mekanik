// Branch map (old dallar.ts): main, work and decision branches as lanes, each step a node (gate tags as diamonds),
// fork and merge curves; the chosen step in the side panel with "open a branch here" (nothing is deleted or moved,
// e2e 5), "open the model" and "compare with now".
import { get, post, W } from "../api";
import { type Ctx, go, reload } from "../main";
import { confirm, fail, toast } from "../ui";
import { clock, day, h, name, role, u, when } from "../util";

const ROW = 44, HEAD = 32, LANE = 24;
const COLOR = (b: any, i: number) => (b?.kind === "main" ? "#1E2530" : b?.kind === "decision" ? (["rejected", "not_chosen"].includes(b.status) ? "#C2C9D0"
  : i % 2 ? "#B9A7EE" : "#8B6FE0") : b?.status === "merged" && !b.current ? "#9AA6B2" : "#2F6FDE");

export async function branchesScreen(c: Ctx) {
  const v = await get(`${W(c.code)}/branches`);
  const f = c.q.filter ?? "all", find = (q: string) => (c.q.find ?? "").toLocaleLowerCase(u("locale")) && !q.toLocaleLowerCase(u("locale")).includes(c.q.find!.toLocaleLowerCase(u("locale")));
  const lanes = [...v.branches].sort((a, b) => ["main", "work", "decision"].indexOf(a.kind) - ["main", "work", "decision"].indexOf(b.kind));
  const dec: Record<string, number> = {};
  lanes.filter((b) => b.kind === "decision").forEach((b, i) => { dec[b.name] = i; });
  const br = (n: string) => lanes.find((b) => b.name === n), lane = (n: string) => Math.max(0, lanes.findIndex((b) => b.name === n)), x = (i: number) => 24 + i * LANE;
  let commits: any[] = v.commits;
  if (f === "gates") commits = commits.filter((k) => k.tags.length);
  if (f === "open") commits = commits.filter((k) => { const b = br(k.branch); return b && b.kind !== "main" && !["merged", "rejected"].includes(b.status); });
  commits = commits.filter((k) => !find(`${k.title} ${k.branch}`));
  const rows: ({ day: string } | { k: any })[] = [], y: Record<string, number> = {};
  let last = "", yy = 4;
  for (const k of commits) {
    if (k.at.slice(0, 10) !== last) { rows.push({ day: k.at }); last = k.at.slice(0, 10); yy += HEAD; }
    rows.push({ k });
    y[k.sha] = yy + ROW / 2;
    yy += ROW;
  }
  const paths: string[] = [];
  for (const b of lanes) {
    const own = commits.filter((k) => k.branch === b.name), xi = x(lane(b.name)), col = COLOR(b, dec[b.name] ?? 0);
    if (!own.length) continue;
    const ys = own.map((k) => y[k.sha]), dash = ["rejected", "not_chosen"].includes(b.status) ? ` stroke-dasharray="4 4"` : "";
    paths.push(`<path d="M${xi} ${Math.min(...ys)} L${xi} ${Math.max(...ys)}" stroke="${col}" stroke-width="${b.current ? 2.5 : 2}" fill="none"${dash}/>`);
    const first = own[own.length - 1], par = commits.find((k) => k.sha === first.visible_parents?.[0]);
    if (par && par.branch !== b.name) { const xe = x(lane(par.branch)), ye = y[par.sha], yb = y[first.sha];
      paths.push(`<path d="M${xe} ${ye} C${xe} ${ye - 16} ${xi} ${yb + 16} ${xi} ${yb}" stroke="${col}" stroke-width="2" fill="none"${dash}/>`); }
  }
  for (const k of commits) {
    const second = commits.find((z) => z.sha === k.visible_parents?.[1]);
    if (second) paths.push(`<path d="M${x(lane(second.branch))} ${y[second.sha]} C${x(lane(second.branch))} ${y[second.sha] - 18} ${x(lane(k.branch))} ${y[k.sha] + 18} ${x(lane(k.branch))} ${y[k.sha]}" stroke="#9AA6B2" stroke-width="2" fill="none"/>`);
  }
  const sel = commits.find((k) => k.sha === c.q.sha) ?? commits[0], now = lanes.find((b) => b.current);
  const nodes = commits.map((k) => { const xi = x(lane(k.branch)), yi = y[k.sha], col = COLOR(br(k.branch), dec[k.branch] ?? 0);
    return k.tags.some((t: string) => /-G\d$/.test(t)) ? `<path d="M${xi} ${yi - 9} L${xi + 9} ${yi} L${xi} ${yi + 9} L${xi - 9} ${yi}z" fill="#1E2530" stroke="#fff" stroke-width="2"/>`
      : `<circle cx="${xi}" cy="${yi}" r="5" fill="${k === sel ? "#fff" : col}" stroke="${col}" stroke-width="2"/>`; });
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.branches"))}</h1><p>${h(u("br.lead", { n: v.commits.length, open: lanes.filter((b) => b.kind !== "main"
    && b.status === "open").length, folded: v.folded }))}</p></div><div class="sag">${["all", "gates", "open"].map((k) => `<a class="hap ${k === f ? "secili" : ""}" data-filter="${k}">${h(u(`br.f.${k}`))}</a>`).join("")}
    <input class="alan" data-find placeholder="${h(u("br.find"))}" value="${h(c.q.find ?? "")}"></div></div>
    <div class="serit-lejant">${lanes.map((b) => `<span class="hap ${b.current ? "secili-acik" : ""}"><span class="cizgi" style="background:${COLOR(b, dec[b.name] ?? 0)}"></span>
      <span class="mono">${h(b.short)}</span> <span class="soluk">${h(u("br.steps", { n: b.steps }))} · ${h(name("branch_status", b.status))}</span></span>`).join("")}</div>
    <div class="kart-kutu dal-harita"><svg width="${24 + lanes.length * LANE + 12}" height="${yy + 8}" role="img" aria-label="${h(u("nav.branches"))}">${paths.join("")}${nodes.join("")}</svg>
    <div class="dal-satirlar">${rows.map((r) => "day" in r ? `<div class="gun" style="height:${HEAD}px">${h(day(r.day))}</div>` : `<div class="dal-satir ${r.k === sel ? "secili" : ""}"
      data-sha="${h(r.k.sha)}" style="height:${ROW}px"><span class="ad"><span class="${r.k.tags.length ? "kalin" : ""}">${h(r.k.title)}</span><span class="mono soluk kucuk">${h(r.k.branch?.slice(c.code.length + 1) ?? "")}${
      r.k.cards.length ? ` · ${h(r.k.cards.join(", "))}` : ""}</span></span>${r.k.tags.map((t: string) => `<span class="rozet koyu">${h(t.slice(c.code.length + 1))}</span>`).join("")}
      ${role(r.k.role)}<span class="mono soluk kucuk">${clock(r.k.at)}</span></div>`).join("") || `<div class="soluk">—</div>`}</div></div>`;
  c.main.querySelectorAll<HTMLElement>("[data-filter]").forEach((a) => a.addEventListener("click", () => go(c.code, "branches", { ...c.q, filter: a.dataset.filter })));
  c.main.querySelector<HTMLInputElement>("[data-find]")!.addEventListener("change", (e) => go(c.code, "branches", { ...c.q, find: (e.target as HTMLInputElement).value }));
  c.main.querySelectorAll<HTMLElement>("[data-sha]").forEach((r) => r.addEventListener("click", () => go(c.code, "branches", { ...c.q, sha: r.dataset.sha })));
  c.side.innerHTML = `<div class="panel-baslik">${h(u("br.selected"))}</div>${sel ? `<div class="panel-govde" data-selected-step="${h(sel.sha)}"><b>${h(sel.title)}</b>
    <div class="kucuk ikincil">${h(sel.author)} · ${h(name("role", sel.role))} · ${when(sel.at)}</div><div class="ozellik-izgara"><span class="ad">${h(u("br.commit"))}</span><span class="mono">${h(sel.sha.slice(0, 12))}</span>
    ${sel.tags.length ? `<span class="ad">${h(u("br.tag"))}</span><span class="mono">${sel.tags.map(h).join("<br>")}</span>` : ""}${sel.cards.length ? `<span class="ad">${h(u("nav.cards"))}</span><span>${sel.cards.map(h).join(", ")}</span>` : ""}
    <span class="ad">${h(u("branch"))}</span><span class="mono kucuk">${h(sel.branch ?? "")}</span></div>
    <button class="dugme birincil genis" data-branch-here>${h(u("br.open_here"))}</button><div class="dugme-sira"><a class="dugme" href="#/${h(c.code)}/model?commit=${h(sel.sha)}">${h(u("br.model"))}</a>
    <a class="dugme" href="#/${h(c.code)}/model?commit=${h(now?.head ?? "")}&compare=${h(sel.sha)}">${h(u("br.compare"))}</a></div><div class="bilgi-kutu">${h(u("br.nothing_deleted"))}</div></div>` : ""}`;
  c.side.querySelector("[data-branch-here]")?.addEventListener("click", async () => {
    const n = await confirm({ title: u("br.open_title", { sha: sel.sha.slice(0, 7) }), text: u("br.open_text"), yes: u("br.open_yes"),
      field: { label: u("br.name"), value: u("br.default_name"), required: true } });
    if (n === null) return;
    try { const r = await post(`${W(c.code)}/branches`, { commit: sel.sha, name: n }); toast(h(u("br.opened", { branch: r.branch })), "branch"); await reload(); }
    catch (e) { fail(e); }
  });
}
