// Design file (old dosya.ts; architecture §9.3 "since you last read"): what the team did since the chief's last
// reading, what was found, what waits for him, the checks by group, the log's day files; "I have read it".
import { fileUrl, get, post, W } from "../api";
import type { Ctx } from "../main";
import { fail, toast } from "../ui";
import { clock, empty, h, role, state, summary, u, when } from "../util";

export async function designScreen(c: Ctx) {
  const v = await get(`${W(c.code)}/design-file`, { branch: c.q.branch });
  const list = (k: string, xs: string[]) => `<section class="kart-kutu" data-design="${k}"><div class="kutu-bas"><h2>${h(u(`design.${k}`))}</h2><span class="ek">${xs.length}</span></div>
    <div class="kutu-ic"><ul class="liste">${xs.map((x) => `<li>${h(x)}</li>`).join("") || `<li class="soluk">—</li>`}</ul></div></section>`;
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.design"))}</h1><p>${h(v.last_read ? u("design.since", { at: when(v.last_read), n: v.new }) : u("design.never", { n: v.new }))}</p></div>
    <div class="sag">${summary(v.summary)}<button class="dugme birincil" data-read>${h(u("design.read"))}</button></div></div>
    <div class="iki-kolon">${list("done", v.done)}${list("found", v.found)}</div>${list("waiting", v.waiting)}
    <section class="kart-kutu"><div class="kutu-bas"><h2>${h(u("design.checks"))}</h2></div><div class="kaydir"><table class="tablo" data-check-groups><tbody>${v.checks.map((g: any) =>
      `<tr><td class="mono">${h(g.check)}</td><td>${state(g.status)}</td><td class="mono">${g.open}/${g.total}</td></tr>`).join("")}</tbody></table></div></section>
    <section class="kart-kutu"><div class="kutu-bas"><h2>${h(u("design.events"))}</h2></div><div class="kutu-ic"><ul class="liste">${v.events.map((e: any) =>
      `<li><span class="mono ikincil">${clock(e.at)}</span>${role(e.role)}<span>${h(e.line)}</span></li>`).join("") || `<li class="soluk">—</li>`}</ul></div></section>`;
  c.main.querySelector("[data-read]")!.addEventListener("click", async () => {
    try { await post(`${W(c.code)}/read-mark`); toast(h(u("design.marked")), "read"); await designScreen(c); } catch (e) { fail(e); }
  });
  c.side.innerHTML = `<div class="panel-baslik">${h(u("design.log"))}</div><div class="panel-govde"><ul class="liste">${v.log.map((n: string) =>
    `<li><a class="mono" target="_blank" rel="noopener" href="${fileUrl(c.code, "images", `records/log/${n}`)}">${h(n)}</a></li>`).join("") || `<li class="soluk">—</li>`}</ul>
    ${v.log.length ? "" : empty("design.no_log")}</div>`;
}
