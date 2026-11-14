// Standard map (wireframe stdmap.html; architecture §10.8): items from regulation to literature with acceptance,
// evidence, verification and status; a tick only with evidence and a quality review; the purchase list (paid texts)
// and the source priority. Filters by type and status; the chosen item in the side panel.
import { get, W } from "../api";
import { type Ctx, go } from "../main";
import { chip, empty, h, name, state, u } from "../util";

const TYPES = ["regulation", "customer_spec", "standard", "guideline", "literature"];
const cite = (i: any) => [i.citation?.document, i.citation?.clause].filter(Boolean).join(" · ");

export async function stdmapScreen(c: Ctx) {
  const v = await get(`${W(c.code)}/stdmap`);
  const items: any[] = v.items, ft = c.q.type ?? "", fs = c.q.status ?? "";
  const shown = items.filter((i) => (!ft || i.type === ft) && (!fs || i.status === fs));
  const sel = items.find((i) => i.id === c.q.item) ?? shown[0];
  const pill = (k: string, val: string, cur: string, n: number) => `<a class="hap ${val === cur ? "secili" : ""}" data-f="${k}" data-v="${h(val)}">${h(val ? name(k === "type" ? "std_type" : "status", val) : u("all"))} ${n}</a>`;
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.stdmap"))}</h1><p>${h(u("std.lead"))}</p></div></div>
    <div class="suzgec-sira"><span class="ikincil">${h(u("std.type"))}</span>${pill("type", "", ft, items.length)}${TYPES.map((x) => pill("type", x, ft, items.filter((i) => i.type === x).length)).join("")}
    <span class="ikincil">${h(u("card.state"))}</span>${pill("status", "", fs, items.length)}${["met", "not_met", "awaiting_evidence"].map((x) => pill("status", x, fs, items.filter((i) => i.status === x).length)).join("")}</div>
    ${items.length ? `<div class="kart-kutu kaydir"><table class="tablo std" data-stdmap><thead><tr>${["std.no", "std.item", "std.type", "std.purpose", "std.why", "std.method",
      "std.acceptance", "std.evidence", "std.verification", "card.state", "std.tick"].map((k) => `<th>${h(u(k))}</th>`).join("")}</tr></thead><tbody>${shown.map((i) =>
      `<tr class="tik ${i.tick?.checked ? "" : "gri"} ${i === sel ? "secili" : ""}" data-item="${h(i.id)}"><td class="mono">${h(i.id)}${i.mandatory ? " !" : ""}</td>
      <td><div class="baslik">${h(i.title)}</div><div class="atif mono">${h(cite(i))}</div></td><td>${h(name("std_type", i.type))}</td><td>${h(i.purpose)}</td>
      <td>${h(i.why_here ?? "")}</td><td>${h(i.test_method ?? "")}</td><td>${h(i.acceptance?.text ?? "")}</td><td>${(i.evidence ?? []).map((e: any) => `<span class="mono">${h(e.id ?? e.path)}</span>`).join(", ") || "—"}</td>
      <td>${chip(i.shown_status === "text_in_hand" ? "ok" : i.shown_status === "unverified" ? "engel" : "uyari", name("verification", i.shown_status))}</td>
      <td>${state(i.status)}</td><td>${i.tick?.checked ? "✓" : ""}</td></tr>`).join("")}</tbody></table></div>` : empty("std.none")}
    <div class="lejant kucuk">${h(u("std.legend"))}</div>`;
  c.main.querySelectorAll<HTMLElement>("[data-f]").forEach((a) => a.addEventListener("click", () => go(c.code, "stdmap", { ...c.q, [a.dataset.f!]: a.dataset.v })));
  c.main.querySelectorAll<HTMLElement>("[data-item]").forEach((r) => r.addEventListener("click", () => go(c.code, "stdmap", { ...c.q, item: r.dataset.item })));
  const paid = items.filter((i) => i.access === "paid");
  c.side.innerHTML = `<div class="panel-baslik">${h(u("std.selected"))} <span class="mono">${h(sel?.id ?? "")}</span></div><div class="panel-govde">${sel ? `
    <div><b>${h(sel.title)}</b><div class="mono kucuk ikincil">${h(cite(sel))} · ${h(name("std_type", sel.type))}</div></div><div class="ozellik-izgara" data-item-detail="${h(sel.id)}">
    <span class="ad">${h(u("std.verification"))}</span><span>${h(name("verification", sel.shown_status))}</span><span class="ad">${h(u("card.req"))}</span><span class="mono">${h(sel.acceptance?.requirement ?? "—")}</span>
    <span class="ad">${h(u("std.acceptance"))}</span><span>${h(sel.acceptance?.text ?? "")}</span><span class="ad">${h(u("std.evidence"))}</span><span>${(sel.evidence ?? []).map((e: any) => h(`${e.kind}: ${e.id ?? e.path}`)).join("<br>") || "—"}</span>
    <span class="ad">${h(u("std.quality"))}</span><span>${sel.tick?.quality_review ? h(sel.tick.quality_review.id ?? sel.tick.quality_review.path) : h(u("std.no_tick"))}</span>
    <span class="ad">${h(u("std.priority"))}</span><span>${sel.priority}</span></div>` : empty("std.none")}</div>
    <div class="panel-ayrac"></div><div class="panel-baslik">${h(u("std.purchase"))} <span class="mono">${paid.length}</span></div><div class="panel-govde">
    <div class="ipucu">${h(u("std.purchase_note"))}</div>${paid.map((i) => `<div class="oge"><b class="mono">${h(i.citation?.document)}</b> ${h(i.procurement?.justification ?? "")}
    <div class="kucuk ikincil">${h(i.open_equivalent?.searched ? (i.open_equivalent.found ? u("std.open_found", { x: i.open_equivalent.found }) : u("std.open_none")) : u("std.open_unsearched"))}</div></div>`).join("")}
    <div class="bilgi-kutu"><span class="cip dur">${h(u("hold"))}</span>${h(u("std.purchase_hold"))}</div></div>
    <div class="panel-ayrac"></div><div class="panel-baslik">${h(u("std.priority_title"))}</div><div class="panel-govde"><ol class="oncelik">${[1, 2, 3, 4, 5].map((p) =>
      `<li class="${sel?.priority === p ? "secili" : ""}">${h(u(`std.p${p}`))}</li>`).join("")}</ol><div class="ipucu">${h(u("std.priority_note"))}</div></div>`;
}
