// Cards (wireframe card.html; old kartlar.ts): the review queue, the card standard (question, "what is this, why are
// you asked", type body and figures, the team's proposal, if you approve / reject / what is recorded), the approval
// log. A hold, decision, gate or release card and every undo pass the confirmation window (Ö-14, Ö-15); assumption
// list rows are approved one by one without it (V-01); the chief's own value; a past version is read-only.
import { fileUrl, get, post, W } from "../api";
import { type Ctx, go, reload } from "../main";
import { confirm, fail, toast } from "../ui";
import { chip, h, name, num, own, role, sha, state, u, when } from "../util";

const CONFIRM = ["gate", "release", "decision", "provisional_decision"];
export const needsConfirm = (k: any) => k.level === "hold" || CONFIRM.includes(k.type);
const LEVEL: Record<string, string> = { hold: "dur", provisional: "mor", witness: "gri" };
const level = (k: any) => (k.level ? chip(LEVEL[k.level] ?? "gri", name("level", k.level), `data-level="${h(k.level)}"`) : "");
const kind = (k: any) => (k.level === "hold" ? "hold" : k.level === "provisional" ? "provisional" : "question");
const img = (c: Ctx, path: string, alt: string) => `<img src="${fileUrl(c.code, "images", path, { branch: c.q.branch })}" alt="${h(alt)}" loading="lazy">`;
const optVisual = (k: any, o: any) => o.visual?.path ?? (k.visuals ?? []).find((v: any) => v.id === o.id)?.path;
/** The option the team proposes: `proposal.option`, or a `choice` that names an option. */
const proposed = (k: any) => k.proposal?.option ?? ((k.options ?? []).some((o: any) => o.id === k.proposal?.choice) ? k.proposal.choice : undefined);

function figures(c: Ctx, k: any): string {
  const ids = new Set((k.options ?? []).flatMap((o: any) => [o.id, optVisual(k, o)]));
  const v = (k.visuals ?? []).filter((x: any) => !ids.has(x.id) && !ids.has(x.path) && x.path);
  return v.length ? `<div class="figurler">${v.map((x: any) => `<figure>${img(c, x.path, x.id ?? "")}<figcaption>${h(x.id ?? "")}</figcaption></figure>`).join("")}</div>` : "";
}

function options(c: Ctx, k: any, chosen?: string): string {
  const open = ["open", "awaiting_reply"].includes(k.status);
  return `<div class="bolum-baslik"><b>${h(u("card.n_options", { n: k.options.length }))}</b><span>${h(u("card.options_note"))}</span></div>
  <div class="secenekler">${k.options.map((o: any) => `<label class="secenek ${o.id === chosen ? "secili" : ""}" data-option="${h(o.id)}">
    <div class="s-bas"><input type="radio" name="opt-${h(k.id)}" value="${h(o.id)}" ${o.id === chosen ? "checked" : ""} ${open ? "" : "disabled"}>
      <b>${h(o.id.toUpperCase())} · ${h(o.title)}</b>${proposed(k) === o.id ? `<span class="rozet-oneri">${h(u("card.proposed"))}</span>` : ""}</div>
    ${optVisual(k, o) ? `<div class="cizim">${img(c, optVisual(k, o), u("card.option_fig", { o: o.id }))}</div>` : ""}
    <div class="izgara2">${o.summary ? `<span class="ad">${h(u("card.what"))}</span><span>${h(o.summary)}</span>` : ""}
      ${(o.pros ?? []).length ? `<span class="ad arti">${h(u("card.pros"))}</span><span>${o.pros.map(h).join("; ")}</span>` : ""}
      ${(o.cons ?? []).length ? `<span class="ad eksi">${h(u("card.cons"))}</span><span>${o.cons.map(h).join("; ")}</span>` : ""}
      ${(o.values ?? []).map((v: any) => `<span class="ad mono">${h(v.name)}</span><span class="mono">${num(v.quantity?.value ?? v.value)} ${h(v.quantity?.unit ?? v.unit ?? "")}</span>`).join("")}</div></label>`).join("")}</div>`;
}

function rows(c: Ctx, k: any): string {
  const open = k.status !== "closed";
  return `<table class="tablo"><thead><tr><th></th><th>${h(u("card.param"))}</th><th>${h(u("card.value"))}</th><th>${h(u("card.what_for"))}</th>
    <th>${h(u("card.why_value"))}</th><th></th></tr></thead><tbody>${(k.rows ?? []).map((r: any) => `<tr data-row="${h(r.param)}">
    <td>${r.status === "approved" ? `<span class="yesil">✓</span>` : `<input type="checkbox" data-row-pick="${h(r.param)}" ${open ? "checked" : "disabled"}>`}</td>
    <td class="mono">${h(r.param)}</td><td class="mono">${num(r.value)} ${h(r.unit ?? "")}</td><td>${h(r.description ?? "")}</td>
    <td>${h(r.rationale ?? "")}${r.note ? `<br><span class="sari">${h(r.note)}</span>` : ""}</td><td><a data-change="${h(r.param)}">${h(u("card.change"))}</a>${
      r.status === "approved" ? `<br><a data-row-undo="${h(r.param)}">${h(u("card.undo_row"))}</a>` : ""}</td></tr>`).join("")}
    ${(k.info_rows ?? []).map((r: any) => `<tr class="gri"><td></td><td class="mono">${h(r.param)}</td><td class="mono">${num(r.value)} ${h(r.unit ?? "")}</td>
    <td>${h(r.description ?? "")}</td><td>${h(u("card.info_row", { source: r.source }))}</td><td></td></tr>`).join("")}</tbody></table>`;
}

function body(c: Ctx, kv: any, k: any, chosen?: string): string {
  const params = (k.subject?.params ?? []).filter((p: string) => kv.params[p]);
  const table = (head: string[], body: string) => `<div class="kaydir"><table class="tablo"><thead><tr>${head.map((x) => `<th>${h(u(x))}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
  return [k.options?.length ? options(c, k, chosen) : "", k.type === "assumption_list" ? rows(c, k) : "", figures(c, k),
    k.requirement_table?.length ? `<div class="bolum-baslik" data-requirements><b>${h(u("card.req_status"))}</b></div>` + table(["card.req", "card.state", "card.evidence"],
      k.requirement_table.map((r: any) => `<tr><td class="mono">${h(r.requirement)}</td><td>${state(r.status)}</td><td class="kucuk">${(r.evidence ?? []).map((e: any) =>
        `${h(e.kind)}: <span class="mono">${h(e.id ?? e.path ?? "")}</span>`).join("<br>") || "—"}</td></tr>`).join("")) : "",
    params.length && k.type !== "assumption_list" ? table(["card.param", "card.value", "card.source"], params.map((p: string) =>
      `<tr><td class="mono">${h(p)}</td><td class="mono">${num(kv.params[p].value)} ${h(kv.params[p].unit ?? "")}</td><td class="${kv.params[p].source ? "" : "kirmizi"}">${
        h(kv.params[p].source ?? u("card.no_source"))}</td></tr>`).join("")) : "",
    k.checks?.length ? `<ul class="liste" data-checks>${k.checks.map((x: any) => `<li>${x.result === "pass" ? `<span class="yesil">✓</span>` : x.result === "warn"
      ? `<span class="sari">▲</span>` : `<span class="kirmizi">✗</span>`}<span>${h(x.message ?? x.rule)} <span class="soluk mono kucuk">${h(x.rule)}</span></span></li>`).join("")}</ul>` : "",
    k.requirement_effects?.length ? `<div class="bolum-baslik"><b>${h(u("card.effects"))}</b></div>` + table(["card.req", "card.effect"],
      k.requirement_effects.map((x: any) => `<tr><td class="mono">${h(x.requirement)}</td><td>${h(x.effect)}</td></tr>`).join("")) : "",
    k.basis?.length ? `<div class="alt-baslik">${h(u("card.basis"))}</div><ul class="liste">${k.basis.map((b: any) => `<li>∑ <b>${h(b.calculation)}</b>
      <span class="sha">${h(b.result_hash)}</span> ${b.status ? chip(b.status === "current" ? "ok" : "uyari", name("basis", b.status)) : ""}</li>`).join("")}</ul>` : "",
    k.observations?.length ? `<div class="alt-baslik">${h(u("card.observations"))}</div><ul class="liste">${k.observations.map((o: any) => `<li>◉ ${h(o.text)}
      <span class="rozet ${o.measured ? "yesil" : "kesik"}">${h(u(o.measured ? "card.measured" : "card.unmeasured"))}</span></li>`).join("")}</ul>` : ""].join("");
}

function thread(k: any): string {
  if (!k.thread?.length) return "";
  return `<section data-thread><div class="bolum-baslik"><b>${h(u("card.thread"))}</b><span>${h(u(k.status === "awaiting_reply" ? "card.awaiting_reply" : "card.replied"))}</span></div>
    ${k.thread.map((x: any) => `<div class="yorum ${x.kind === "reply" ? "yanit" : ""}">${role(x.role)} <span class="soluk kucuk">${when(x.at)} · ${h(name("thread", x.kind ?? "comment"))}${
      x.row ? ` · ${h(x.row)}` : ""}</span><div>${h(x.text)}</div></div>`).join("")}</section>`;
}

function footer(c: Ctx, kv: any, k: any, chosen?: string): string {
  if (kv.past) return `<div class="bilgi-kutu" data-past>${h(u("card.past", { commit: kv.commit.slice(0, 7) }))}</div>`;
  const open = ["open", "awaiting_reply"].includes(k.status), comment = `<textarea data-comment rows="2" placeholder="${h(u("card.comment_ph"))}"></textarea>`;
  const undo = ["approved", "rejected"].includes(k.status) && !["gate", "release", "assumption_list"].includes(k.type);
  if (k.type === "model_note") return open ? `${comment}<div class="dugmeler"><button class="dugme" data-act="comment">${h(u("card.comment_more"))}</button></div>` : "";
  if (!open) return undo ? `<div class="dugmeler"><button class="dugme" data-act="undo">${h(u("card.undo"))}</button><span class="soluk kucuk">${h(u("card.undo_note"))}</span></div>` : "";
  const label = k.options?.length ? (chosen ? u("card.approve_option", { o: chosen.toUpperCase() }) : u("card.pick_option"))
    : k.type === "assumption_list" ? u("card.approve_rows", { n: (k.rows ?? []).filter((r: any) => r.status !== "approved").length })
    : k.type === "gate" ? u("card.approve_gate", { gate: k.subject?.gate }) : k.type === "release" ? u("card.approve_release") : u("card.approve");
  const params = (k.subject?.params ?? []).filter((p: string) => kv.params[p]);
  return `${comment}<div class="dugmeler"><button class="dugme birincil" data-act="approve" ${k.options?.length && !chosen ? "disabled" : ""}>${h(label)}</button>
    ${k.type === "assumption_list" ? "" : `<button class="dugme ret" data-act="reject">${h(u(k.options?.length ? "card.reject_all" : "card.reject"))}</button>`}
    <button class="dugme" data-act="comment">${h(u("card.comment_only"))}</button>${params.length && k.type !== "assumption_list"
      ? `<button class="dugme" data-value-open>${h(u("card.own_value"))}</button>` : ""}<span class="bosluk"></span><a href="#/${h(c.code)}/branches">${h(u("card.on_map"))}</a></div>
    ${params.length ? `<div class="dugme-sira" data-value-form hidden><select class="alan" data-value-param>${params.map((p: string) => `<option>${h(p)}</option>`).join("")}</select>
      <input class="alan" data-value-input type="number" step="any" placeholder="${h(u("card.new_value"))}"><button class="dugme birincil" data-value-send>${h(u("card.save_value"))}</button></div>` : ""}
    ${needsConfirm(k) ? `<div class="teyit-not">ⓘ ${h(u("card.confirm_note", { commit: kv.commit.slice(0, 7) }))}</div>` : ""}`;
}

export function cardView(c: Ctx, kv: any, k: any, chosen?: string): string {
  chosen = chosen ?? (k.options?.length ? kv.decisions?.find((d: any) => d.id === k.subject?.decision)?.chosen ?? proposed(k) : undefined);
  return `<article class="kart-std" data-card-std="${h(k.id)}"><header><div class="ust-satir"><span class="mono">${h(c.code)}:${h(k.id)}</span>
    <span class="hap" data-card-status="${h(k.status)}">${h(name("card_type", k.type))} · ${h(name("status", k.status))}</span>${level(k)}
    <span>${h(u("card.opened_by", { who: name("role", k.opened_by), at: when(k.opened_at) }))}</span></div>
    <h1>${h(k.question ?? k.title)}</h1><div class="neden"><span><b>${h(u("card.why_asked"))}</b> ${h(own(k.explain))}</span></div>
    ${k.note ? `<div class="bilgi-kutu" data-note>${h(k.note)}</div>` : ""}${k.warning ? `<div class="hata-kutu"><b>${h(u("card.warning"))}</b> ${h(k.warning)}</div>` : ""}</header>
    <section>${body(c, kv, k, chosen)}</section>
    ${k.proposal || k.if_approved ? `<section><div class="oneri-kutu"><span class="etiket">${h(u("card.team_proposal"))}${proposed(k) ? ` · ${h(proposed(k).toUpperCase())}`
      : k.proposal?.choice ? ` · ${h(k.proposal.choice)}` : ""}</span><span>${h(k.proposal?.rationale ?? k.proposal?.text ?? "")}</span></div>
      <div class="uc-kutu"><div><span class="etiket">${h(u("card.if_approved"))}</span><span>${h(k.if_approved ?? "")}</span></div>
      <div><span class="etiket">${h(u("card.if_rejected"))}</span><span>${h(k.if_rejected ?? "")}</span></div>
      <div><span class="etiket">${h(u("card.recorded_as"))}</span><span>${h(k.recorded_as ?? "")}</span></div></div></section>` : ""}
    ${thread(k)}<footer>${footer(c, kv, k, chosen)}</footer></article>`;
}

/** The card's buttons; `after` redraws (the cards screen or the model screen). */
export function bindCard(c: Ctx, el: HTMLElement, kv: any, k: any, after: () => void) {
  const base = { viewed: kv.commit.slice(0, 7), branch: c.q.branch };
  const comment = () => el.querySelector<HTMLTextAreaElement>("[data-comment]")?.value.trim() ?? "";
  const send = async (url: string, b: any, msg: string) => {
    try { const r = await post(`${W(c.code)}/cards/${k.id}/${url}`, { ...base, ...b }); toast(h(msg) + (r.gate?.tag ? ` · <span class="mono">${h(r.gate.tag)}</span>` : ""), "card"); await reload(); after(); }
    catch (e) { fail(e); }
  };
  el.querySelectorAll<HTMLElement>("[data-option]").forEach((o) => o.addEventListener("click", (e) => {
    if (o.querySelector<HTMLInputElement>("input")?.disabled) return;
    e.preventDefault();
    const text = comment(), art = el.querySelector<HTMLElement>(`[data-card-std="${k.id}"]`)!;
    art.outerHTML = cardView(c, kv, k, o.dataset.option);
    const ta = el.querySelector<HTMLTextAreaElement>("[data-comment]");
    if (ta) ta.value = text;
    bindCard(c, el, kv, k, after);
  }));
  el.querySelectorAll("[data-row-pick]").forEach((x) => x.addEventListener("change", () => {
    const b = el.querySelector<HTMLButtonElement>("[data-act=approve]"), n = el.querySelectorAll("[data-row-pick]:checked").length;
    if (b) { b.textContent = u("card.approve_rows", { n }); b.disabled = !n; }
  }));
  el.querySelectorAll<HTMLButtonElement>("[data-act]").forEach((b) => b.addEventListener("click", async () => {
    const act = b.dataset.act!, id = `${c.code}:${k.id}`;
    if (act === "undo") {
      const why = await confirm({ title: u("card.undo_title", { id }), text: u("card.undo_text"), yes: u("card.undo_yes"), field: { label: u("reason"), required: true } });
      return why === null ? undefined : send("revert", { reason: why, confirmed: true }, u("card.undone", { id: k.id }));
    }
    if (act === "comment") return comment() ? send("decision", { action: "comment", reason: comment() }, u("card.commented", { id: k.id })) : toast(h(u("card.write_first")), "card");
    const option = el.querySelector<HTMLInputElement>(`input[name="opt-${k.id}"]:checked`)?.value;
    const picked = [...el.querySelectorAll<HTMLInputElement>("[data-row-pick]:checked")].map((x) => x.dataset.rowPick!);
    const b2: any = { action: act, reason: comment(), option: act === "approve" ? option : undefined, rows: k.type === "assumption_list" ? picked : undefined };
    if (needsConfirm(k)) {
      const reqs = [...new Set([...(k.requirement_effects ?? []), ...(k.requirement_table ?? [])].map((r: any) => r.requirement))].join(", ") || "—";
      const ok = await confirm({ title: u(act === "approve" ? (option ? "card.confirm_option" : "card.confirm_approve") : "card.confirm_reject", { id, o: option?.toUpperCase() }),
        text: `${act === "approve" ? k.if_approved ?? "" : k.if_rejected ?? ""} ${u("card.confirm_text", { commit: kv.commit.slice(0, 7), reqs })}`,
        yes: u(act === "approve" ? "card.yes_approve" : "card.yes_reject") });
      if (ok === null) return;
      b2.confirmed = true;
    }
    b.disabled = true;
    await send("decision", b2, u(act === "approve" ? "card.approved" : "card.rejected", { id: k.id }));
    b.disabled = false;
  }));
  el.querySelectorAll<HTMLElement>("[data-row-undo]").forEach((a) => a.addEventListener("click", async () => {
    const why = await confirm({ title: u("card.undo_title", { id: `${k.id}/${a.dataset.rowUndo}` }), text: u("card.undo_text"), yes: u("card.undo_yes"),
      field: { label: u("reason"), required: true } });
    if (why !== null) await send("revert", { reason: why, row: a.dataset.rowUndo, confirmed: true }, u("card.undone", { id: a.dataset.rowUndo }));
  }));
  const value = async (param: string, raw: string) => {
    const v = parseFloat(raw.replace(",", "."));
    if (Number.isNaN(v)) return toast(h(u("card.number")), "card");
    try { await post(`${W(c.code)}/values`, { ...base, param, value: v, reason: comment(), card: k.id }); toast(h(u("card.value_saved", { param, value: num(v) })), "card"); await reload(); after(); }
    catch (e) { fail(e); }
  };
  el.querySelector("[data-value-open]")?.addEventListener("click", () => { const f = el.querySelector<HTMLElement>("[data-value-form]")!; f.hidden = !f.hidden; });
  el.querySelector("[data-value-send]")?.addEventListener("click", () =>
    value(el.querySelector<HTMLSelectElement>("[data-value-param]")!.value, el.querySelector<HTMLInputElement>("[data-value-input]")!.value));
  el.querySelectorAll<HTMLElement>("[data-change]").forEach((a) => a.addEventListener("click", async () => {
    const v = await confirm({ title: u("card.change_title", { param: a.dataset.change }), text: u("card.change_text"), yes: u("card.save_value"),
      field: { label: u("card.new_value"), required: true } });
    if (v !== null) await value(a.dataset.change!, v);
  }));
}

function sideOf(c: Ctx, k: any, all: any[]): string {
  const per: Record<string, [string, number]> = {};
  for (const x of all) per[x.work] = [x.work_title, (per[x.work]?.[1] ?? 0) + 1];
  return `<div class="panel-baslik">${h(u("card.side"))} <span class="mono">${h(k?.id ?? "")}</span></div>${k ? `<div class="panel-govde"><div class="ozellik-izgara">
    <span class="ad">${h(u("card.code"))}</span><span class="mono">${h(c.code)}:${h(k.id)}</span><span class="ad">${h(u("card.type"))}</span><span>${h(name("card_type", k.type))}</span>
    <span class="ad">${h(u("card.state"))}</span><span>${state(k.status)}</span><span class="ad">${h(u("card.level"))}</span><span>${level(k) || "—"}</span>
    <span class="ad">${h(u("card.opener"))}</span><span>${role(k.opened_by)}</span><span class="ad">${h(u("card.decider"))}</span><span>${role("chief_engineer")}</span>
    ${k.stop_category ? `<span class="ad">${h(u("card.stop_category"))}</span><span>${h(name("stop_cat", k.stop_category))}</span>` : ""}
    ${k.triggers?.length ? `<span class="ad">${h(u("card.triggers"))}</span><span class="mono kucuk">${k.triggers.map(h).join(" · ")}</span>` : ""}</div></div>` : ""}
    <div class="panel-ayrac"></div><div class="panel-baslik">${h(u("card.all_works"))}</div><div class="panel-govde"><ul class="liste">${Object.entries(per).map(([w, [t, n]]) =>
      `<li><a class="mono" href="#/${h(w)}/cards">${h(w)}</a><span class="ikincil">${h(t)}</span><span class="mono">${n}</span></li>`).join("") || `<li class="soluk">—</li>`}</ul></div>`;
}

export async function cardsScreen(c: Ctx) {
  const [kv, all] = await Promise.all([get(`${W(c.code)}/cards`, { branch: c.q.branch, commit: c.q.commit }), get("/api/cards").catch(() => [])]);
  const f = c.q.kind ?? "all", open = kv.cards.filter((k: any) => ["open", "awaiting_reply"].includes(k.status));
  const shown = kv.cards.filter((k: any) => f === "all" || kind(k) === f).sort((a: any, b: any) =>
    Number(!["open", "awaiting_reply"].includes(a.status)) - Number(!["open", "awaiting_reply"].includes(b.status)));
  const k = kv.cards.find((x: any) => x.id === c.q.card) ?? open[0] ?? kv.cards[0];
  c.main.innerHTML = `<div class="kart-yerlesim"><section class="kuyruk"><div class="bolum-baslik"><b>${h(u("card.queue"))}</b><span>${h(u("card.n_waiting", { n: open.length }))}</span></div>
    <div class="akis-arac">${["all", "hold", "provisional", "question"].map((x) => `<a class="hap ${x === f ? "secili" : ""}" data-kind="${x}">${h(u(`card.k.${x}`))} ${
      x === "all" ? open.length : open.filter((y: any) => kind(y) === x).length}</a>`).join("")}</div>
    <div class="kart-kutu kaydir"><table class="tablo"><tbody>${shown.map((x: any) => `<tr class="tik ${x === k ? "secili" : ""}" data-card="${h(x.id)}"><td class="mono">${h(x.id)}</td>
      <td>${h(x.question ?? x.title)}</td><td>${level(x)} ${state(x.status)}</td></tr>`).join("") || `<tr><td class="soluk">${h(u("card.none"))}</td></tr>`}</tbody></table></div>
    <div class="bolum-baslik"><b>${h(u("card.log"))}</b></div><div class="kart-kutu kaydir"><table class="tablo" data-approvals><tbody>${kv.approvals.slice(0, 30).map((a: any) =>
      `<tr title="${h(a.channel ?? "")} · ${h(a.commit ?? "")}"><td class="mono">${when(a.at)}</td><td class="mono">${h(a.card)}${a.row ? `/${h(a.row)}` : ""}</td><td>${h(name("action", a.action))}</td>
      <td class="ikincil">${h(a.reason ?? "")}</td></tr>`).join("") || `<tr><td class="soluk">—</td></tr>`}</tbody></table></div></section>
    <section id="card-area">${k ? cardView(c, kv, k) : `<div class="bilgi-kutu">${h(u("card.none"))}</div>`}</section></div>`;
  c.main.querySelectorAll<HTMLElement>("[data-kind]").forEach((a) => a.addEventListener("click", () => go(c.code, "cards", { ...c.q, kind: a.dataset.kind })));
  c.main.querySelectorAll<HTMLElement>("tr[data-card]").forEach((r) => r.addEventListener("click", () => go(c.code, "cards", { ...c.q, card: r.dataset.card })));
  if (k) bindCard(c, c.main.querySelector("#card-area")!, kv, k, () => {});
  c.side.innerHTML = sideOf(c, k, all);
  const right = document.querySelector("[data-nav-right]");
  if (right) right.innerHTML = branchSelect(c) + (kv.past ? ` <span class="rozet">${h(u("card.past_badge", { commit: sha(kv.commit) }))}</span>` : "");
  bindBranchSelect(c);
}

export function branchSelect(c: Ctx): string {
  const bs = (c.work.branches ?? []).filter((b: string) => !b.endsWith("/main"));
  return bs.length > 1 ? `<select class="dal-sec" data-branch-select>${bs.map((b: string) => `<option ${b === (c.q.branch ?? c.work.branch) ? "selected" : ""}>${h(b)}</option>`).join("")}</select>`
    : `<span class="mono">${h(c.work.branch)}</span>`;
}
export function bindBranchSelect(c: Ctx) {
  document.querySelector<HTMLSelectElement>("[data-branch-select]")?.addEventListener("change", (e) =>
    go(c.code, c.screen, { branch: (e.target as HTMLSelectElement).value }));
}
