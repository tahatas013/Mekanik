// Model (wireframe model.html; old model.ts): the viewer of a commit (text first, the 3D data after it, A4), the
// parts and fits in the tree, the fit table and markers (state from the checks and the cards, e2e 10), exact
// cylinder diameters (e2e 3), a fit's card beside it, "mark and write a note" (e2e 17), comparing two versions.
import { get, W } from "../api";
import { type Ctx, go, reload, S } from "../main";
import { noteMarkers, startMarking } from "../markup";
import { toast } from "../ui";
import { h, name, num, sha, state, summary, u } from "../util";
import { compareData, fitMarkers, FIT_COLOR, mountViewer, type View } from "../viewer";
import { bindBranchSelect, bindCard, branchSelect, cardView } from "./cards";

let view: View | null = null;

function fitSide(c: Ctx, kv: any, fits: any[], marks: any[], id?: string) {
  const f = fits.find((x) => x.id === id), m = marks.find((x) => x.id === id);
  const card = f && kv.cards.find((k: any) => Object.values(k.subject ?? {}).includes(f.id));
  const p = (n: string) => (kv.params[n] ? `${h(n)} = <span class="mono">${num(kv.params[n].value)} ${h(kv.params[n].unit ?? "")}</span>` : h(n ?? "—"));
  c.side.innerHTML = f ? `<div class="panel-baslik">${h(u("model.fit"))} <span class="mono">${h(f.id)}</span></div><div class="panel-govde" data-fit-detail="${h(f.id)}">
    <div class="fit-bas"><b>${h(f.id)} · ${h(name("fit_task", f.task))}</b>${m ? `<span style="color:${FIT_COLOR[m.status]}" data-state="${h(m.status)}">${h(name("fit_state", m.status))}</span>` : ""}</div>
    <div class="ozellik-izgara"><span class="ad">${h(u("model.parts"))}</span><span>${h(f.parts.join(" ↔ "))}</span><span class="ad">${h(u("model.nominal"))}</span><span>${p(f.nominal)}</span>
    <span class="ad">${h(u("model.clearance"))}</span><span>${p(f.clearance)}</span><span class="ad">${h(u("model.critical"))}</span><span>${h(u(f.critical ? "yes" : "no"))}</span></div>
    ${m?.reasons?.length ? `<div class="hata-kutu">${m.reasons.map(h).join("<br>")}</div>` : ""}</div>${card ? `<div class="panel-govde dar-kart" data-card-slot>${cardView(c, kv, card)}</div>` : ""}`
    : `<div class="panel-baslik">${h(u("properties"))} <span class="mono">${h(c.code)}</span></div><div class="panel-govde"><div class="ozellik-izgara">
    <span class="ad">${h(u("model.checks"))}</span><span>${summary(kv.summary)}</span><span class="ad">${h(u("model.open_cards"))}</span><span>${c.work.open_cards}</span>
    <span class="ad">${h(u("model.version"))}</span><span class="mono">${sha(kv.commit)}</span></div></div>`;
  c.side.insertAdjacentHTML("beforeend", `<div class="panel-govde" data-cylinders></div>`);
  if (card) bindCard(c, c.side.querySelector("[data-card-slot]")!, kv, card, () => {});
}

export async function modelScreen(c: Ctx) {
  view?.close();
  view = null;
  const commit = c.q.commit ?? c.work.commit, compare = c.q.compare;
  const kv = await get(`${W(c.code)}/cards`, { branch: c.q.branch, commit: c.q.commit });
  const fits: any[] = Object.values(kv.records ?? {}).flatMap((r: any) => r.fits ?? []);
  const res = (id: string) => kv.results.filter((r: any) => r.ref === id && r.status !== "pass");
  const worst = (id: string) => (res(id).some((r: any) => r.status === "block") ? "block" : res(id).length ? "warn" : "pass");
  c.main.innerHTML = `<div class="arac-cubugu"><button class="isaretle-dugme" data-mark disabled>✎ ${h(u("model.mark"))}</button>
    <span class="mono kucuk" data-model-label>${compare ? h(u("model.comparing", { a: compare.slice(0, 7), b: commit.slice(0, 7) })) : `${h(kv.branch)} · ${sha(commit)}`}</span>
    ${kv.past ? `<span class="rozet">${h(u("card.past_badge", { commit: sha(commit) }))}</span>` : ""}${!compare && commit !== c.work.commit
      ? `<a class="dugme" href="#/${h(c.code)}/model?compare=${h(commit)}">${h(u("model.compare_now"))}</a>` : ""}</div>
    <section class="goruntuleyici buyuk" id="viewer"><div class="bos">${h(u("model.loading"))}</div></section>
    <div class="kart-kutu kaydir">${fits.length ? `<table class="tablo" data-fits><thead><tr><th>${h(u("model.fit"))}</th><th>${h(u("model.parts"))}</th><th>${h(u("model.task"))}</th>
      <th>${h(u("model.nominal"))}</th><th>${h(u("model.clearance"))}</th><th>${h(u("card.state"))}</th></tr></thead><tbody>${fits.map((f) => `<tr class="tik" data-fit="${h(f.id)}">
      <td class="mono">${h(f.id)}</td><td>${h(f.parts.join(" ↔ "))}</td><td>${h(name("fit_task", f.task))}</td><td class="mono">${num(kv.params[f.nominal]?.value)}</td>
      <td class="mono">${num(kv.params[f.clearance]?.value, 2)}</td><td>${state(worst(f.id))}</td></tr>`).join("")}</tbody></table>`
      : `<div class="bilgi-kutu">${h(u("model.no_fits"))}</div>`}</div>`;
  const right = document.querySelector("[data-nav-right]");
  if (right) right.innerHTML = branchSelect(c);
  bindBranchSelect(c);
  let marks: any[] = [];
  const pick = (id: string) => { fitSide(c, kv, fits, marks, id); cylinders(); };
  c.main.querySelectorAll<HTMLElement>("[data-fit]").forEach((r) => r.addEventListener("click", () => pick(r.dataset.fit!)));
  let cyl: any[] = [];
  const cylinders = () => {
    const el = c.side.querySelector("[data-cylinders]");
    const by: Record<string, Set<string>> = {};
    for (const x of cyl) (by[x.part] ??= new Set()).add(num(x.diameter, 3));
    if (el && cyl.length) el.innerHTML = `<div class="etiket-baslik">${h(u("model.cylinders"))}</div>${Object.entries(by).map(([p, ds]) =>
      `<div class="kucuk"><span class="mono">${h(p)}</span>: ${[...ds].map((d) => `Ø${d}`).join(" · ")}</div>`).join("")}<div class="ipucu">${h(u("model.measure_hint"))}</div>`;
  };
  fitSide(c, kv, fits, marks, c.q.fit);
  const m = await get(`${W(c.code)}/model`, { commit, branch: c.q.branch });
  const el = c.main.querySelector<HTMLElement>("#viewer");
  if (!el || S.screen !== "model") return;
  if (!m.data) { el.innerHTML = `<div class="bos">${h(u("model.none"))}</div>`; return; }
  const extra = document.getElementById("tree-extra"), parts: string[] = (m.data.shapes.parts ?? []).map((p: any) => p.name);
  if (extra) extra.innerHTML = `<div class="agac-satir alt-satir"><span class="ad">${h(u("model.parts"))}</span><span class="sag-bilgi">${parts.length}</span></div>
    ${parts.map((p) => `<div class="agac-satir g4 mono">${h(p)}</div>`).join("")}<div class="agac-satir alt-satir"><span class="ad">${h(u("model.fits"))}</span>
    <span class="sag-bilgi">${fits.length}</span></div>${fits.map((f) => `<a class="agac-satir g4" data-fit="${h(f.id)}"><span class="kare" style="background:${
      { block: "#B3261E", warn: "#8A5A00", pass: "#2E6B46" }[worst(f.id)]}"></span><span class="mono">${h(f.id)}</span> <span class="ikincil">${h(f.parts.join(" ↔ "))}</span></a>`).join("")}`;
  extra?.querySelectorAll<HTMLElement>("[data-fit]").forEach((r) => r.addEventListener("click", () => pick(r.dataset.fit!)));
  const data = compare ? compareData((await get(`${W(c.code)}/model`, { commit: compare })).data ?? m.data, m.data) : m.data;
  S.leave = () => { view?.close(); view = null; };
  view = await mountViewer(el, data, c.code, { now: m.commit, before: compare }, { w: el.clientWidth - 2, h: el.clientWidth < 700 ? 360 : Math.max(420, innerHeight - 300), tree: el.clientWidth < 700 ? 160 : 220 });
  get(`${W(c.code)}/cylinders`, { commit: m.commit }).then((x) => { cyl = x; cylinders(); }, () => {});
  if (compare) return;
  const btn = c.main.querySelector<HTMLButtonElement>("[data-mark]")!;
  btn.disabled = false;
  btn.addEventListener("click", () => startMarking(view!, el, c.code, m.commit, (id) => {
    toast(h(u("note.sent", { id })), "note", { text: u("flow.open_card"), run: () => go(c.code, "cards", { card: id }) });
    reload();
  }));
  noteMarkers(view, el, kv.cards.filter((k: any) => k.type === "model_note" && ["open", "awaiting_reply"].includes(k.status)), (id) => go(c.code, "cards", { card: id }));
  if (fits.length) {
    marks = await get(`${W(c.code)}/fit-markers`, { commit: m.commit, branch: c.q.branch }).catch(() => []);
    fitMarkers(view, el, marks, c.q.fit, pick);
  }
}
