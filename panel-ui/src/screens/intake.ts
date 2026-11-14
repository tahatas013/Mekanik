// Intake (wireframe intake.html; architecture §7.1): the step bar, the work type, the questions asked now (why it
// matters, what happens unanswered, a hold marker) with the chief's answer (POST intake/answer), the question tree,
// findings and the understanding summary (approved through its T-01 card).
import { get, post, W } from "../api";
import type { Ctx } from "../main";
import { fail, toast } from "../ui";
import { chip, empty, h, name, own, state, u } from "../util";

const ICON: Record<string, string> = { answered: "✓", derived: "◆", defaulted: "○", pending: "□" };

function input(x: any): string {
  const a = x.node.answer ?? {}, k = h(x.key);
  if (a.type === "boolean") return `<div class="dugme-sira">${[true, false].map((v) => `<button class="dugme" data-answer-value="${v}" data-q="${k}">${h(u(v ? "yes" : "no"))}</button>`).join("")}</div>`;
  if (a.type === "choice") return `<div class="dugme-sira"><select class="alan" data-q-input="${k}">${(a.choices ?? []).map((c: any) =>
    `<option value="${h(JSON.stringify(c.value))}">${h(own(c.text) || c.value)}</option>`).join("")}</select><button class="dugme birincil" data-answer-send="${k}">${h(u("intake.answer"))}</button></div>`;
  return `<div class="dugme-sira"><input class="alan" data-q-input="${k}" ${a.type === "number" ? `type="number" step="any"` : ""}>${a.unit ? `<span>${h(a.unit)}</span>` : ""}
    <button class="dugme birincil" data-answer-send="${k}">${h(u("intake.answer"))}</button></div>`;
}

function question(x: any, n: number, all: number): string {
  const d = x.node.default_if_unanswered ?? {};
  return `<article class="soru-kart" data-question="${h(x.key)}"><header><div class="ust-satir"><span class="mono">${h(x.key)}</span>${x.hold
    ? `<span class="cip dur">${h(u("hold"))} · ${h(name("stop_cat", x.hold))}</span>` : ""}<span class="ikincil">${h(u("intake.q_n", { n, all }))}</span></div>
    <h2>${h(own(x.node.text))}</h2></header><div class="neden-kutu"><b>${h(u("intake.why"))}</b> ${h(own(x.node.why))}</div>
    <div class="varsayilan-kutu"><b>${h(u("intake.unanswered"))}</b> ${h(x.hold ? u("intake.hold_waits") : u("intake.default", { value: JSON.stringify(d.value), source: d.source }))}
    ${d.rationale ? ` ${h(own(d.rationale))}` : ""}</div>${input(x)}</article>`;
}

export async function intakeScreen(c: Ctx) {
  const v = await get(`${W(c.code)}/intake`);
  const nodes: any[] = v.plan.nodes, now = nodes.filter((x) => v.plan.now.includes(x.key)), done = nodes.filter((x) => x.state !== "pending").length;
  const type = v.types[v.work_type], s = v.summary;
  const step = (i: number, k: string, ok: boolean, cur: boolean, sub: string) => `<div class="adim ${ok ? "tamam" : cur ? "simdi" : ""}" data-intake-step="${k}">
    <span class="no">${ok ? "✓" : i}</span><span>${h(u(`intake.s.${k}`))}<small>${h(sub)}</small></span></div>`;
  c.main.innerHTML = `<div class="adimlar">${step(1, "type", !!type, !type, type ? own(type.title) : u("intake.none"))}
    ${step(2, "analysis", !!type, false, type ? u("intake.analyzers", { n: (type.analyzers ?? []).length }) : "—")}
    ${step(3, "questions", !!type && !v.plan.now.length, !!type && !!v.plan.now.length, `${done}/${nodes.length}`)}
    ${step(4, "summary", v.summary_status === "approved", ["draft", "submitted"].includes(v.summary_status), name("summary", v.summary_status))}</div>
    ${type ? "" : `<section class="kart-kutu"><div class="kutu-bas"><h2>${h(u("intake.s.type"))}</h2><span class="ek">${h(u("intake.type_team"))}</span></div>
      <div class="kutu-ic tur-kartlar">${Object.values(v.types).map((x: any) => `<div class="tur-kart"><b>${h(own(x.title))}</b><p>${h(own(x.description))}</p>
      <span class="mono soluk kucuk">${h(x.id)}</span></div>`).join("")}</div></section>`}
    <div class="bolum-bas"><h2>${h(u("intake.now"))}</h2><span class="ek">${h(u("intake.limit", { n: v.plan.asked_now, limit: v.plan.limit }))}</span></div>
    ${now.map((x, i) => question(x, i + 1, now.length)).join("") || empty("intake.no_questions")}
    <section class="kart-kutu" data-summary="${h(v.summary_status)}"><div class="kutu-bas"><h2>${h(u("intake.s.summary"))}</h2><span class="ek">${
      state(v.summary_status === "approved" ? "approved" : v.summary_status === "submitted" ? "open" : "closed").replace(/>[^<]*</, `>${h(name("summary", v.summary_status))}<`)}</span></div>
    <div class="kutu-ic">${s ? `<div class="kaydir"><table class="tablo"><thead><tr><th>${h(u("card.req"))}</th><th>${h(u("intake.req_text"))}</th><th>${h(u("intake.req_kind"))}</th></tr></thead>
      <tbody>${(s.requirements ?? []).map((r: any) => `<tr><td class="mono">${h(r.id ?? "")}</td><td>${h(own(r.text) ?? r)}</td><td>${h(name("req_kind", r.kind ?? ""))}</td></tr>`).join("")}</tbody></table></div>
      <div class="ozet-uclu"><div><div class="alt-baslik">${h(u("intake.method"))}</div><div>${h(own(s.method?.text ?? s.method) || "—")}</div></div>
      <div><div class="alt-baslik">${h(u("intake.packages"))}</div><div class="mono">${h((s.packages ?? []).map((p: any) => p.id ?? p).join(", ") || "—")}</div></div>
      <div><div class="alt-baslik">${h(u("nav.stdmap"))}</div><div>${h(u("intake.stdmap_n", { n: s.stdmap?.items ?? s.stdmap?.count ?? "—" }))} <a href="#/${h(c.code)}/stdmap">${h(u("intake.open_map"))}</a></div></div></div>`
      : empty("intake.no_summary")}<div class="bilgi-kutu"><span class="cip dur">${h(u("hold"))}</span>${h(u("intake.summary_note"))} <a href="#/${h(c.code)}/cards?card=T-01">T-01</a></div></div></section>`;
  const send = async (key: string, value: unknown) => {
    try { await post(`${W(c.code)}/intake/answer`, { key, value }); toast(h(u("intake.answered", { q: key })), "intake"); await intakeScreen(c); } catch (e) { fail(e); }
  };
  c.main.querySelectorAll<HTMLElement>("[data-answer-value]").forEach((b) => b.addEventListener("click", () => send(b.dataset.q!, b.dataset.answerValue === "true")));
  c.main.querySelectorAll<HTMLElement>("[data-answer-send]").forEach((b) => b.addEventListener("click", () => {
    const k = b.dataset.answerSend!, x = nodes.find((n) => n.key === k), el = c.main.querySelector<HTMLInputElement>(`[data-q-input="${CSS.escape(k)}"]`)!;
    const raw = el.value.trim();
    if (!raw) return el.focus();
    send(k, x?.node.answer?.type === "number" ? parseFloat(raw.replace(",", ".")) : x?.node.answer?.type === "choice" ? JSON.parse(raw) : raw);
  }));
  const trees = [...new Set(nodes.map((x) => x.tree))];
  c.side.innerHTML = `<div class="panel-baslik">${h(u("intake.tree"))} <span class="mono">${done}/${nodes.length}</span></div><div class="panel-govde">
    <div class="lejant kucuk">${Object.entries(ICON).map(([k, i]) => `<span>${i} ${h(name("q_state", k))}</span>`).join("")}<span><span class="cip dur">${h(u("hold"))}</span></span></div>
    <div class="soru-agac" data-qtree>${trees.map((t) => `<div class="grup mono">${h(t)}</div>${nodes.filter((x) => x.tree === t).map((x) => `<div class="dal ${x.bucket === "now" ? "simdi" : ""}"
      data-node="${h(x.key)}" data-state="${h(x.state)}"><span>${ICON[x.state] ?? "□"}</span><span>${h(own(x.node.text))}${x.answer !== null && x.answer !== undefined
      ? ` <b class="mono">${h(JSON.stringify(x.answer))}</b>` : ""}</span>${x.hold ? `<span class="cip dur">${h(u("hold"))}</span>` : ""}</div>`).join("")}`).join("") || empty("intake.no_tree")}</div></div>
    <div class="panel-ayrac"></div><div class="panel-baslik">${h(u("intake.findings"))} <span class="mono">${v.plan.findings.length}</span></div><div class="panel-govde">${
      v.plan.findings.map((f: any) => `<div class="bulgu ${h(f.kind)}" data-finding="${h(f.kind)}">${chip("uyari", name("finding", f.kind))} ${h(f.text)}</div>`).join("") || empty("intake.no_findings")}</div>`;
}
