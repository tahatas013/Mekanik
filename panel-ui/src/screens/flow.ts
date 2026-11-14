// Flow (wireframe flow.html; architecture §9.1): every step a line — time, role, text, small figure, cards, check
// summary, commit; provisional decisions purple with "object", holds red; the stage strip with the chosen stage's
// last model (old Durum · Aşamalar, e2e 2); the instruction box (inbox, never the session terminal), stop and "open
// the session". Side panel: day summary, stage-end questions and measures | status (old Durum) | team (old Ekip).
import { fileUrl, get, post, W } from "../api";
import { type Ctx, go, reload, S } from "../main";
import { confirm, fail, mascot, toast } from "../ui";
import { clock, day, empty, h, name, num, own, role, sha, state, summary, t, u, when } from "../util";
import { mountViewer, type View } from "../viewer";

let mini: View | null = null;
const FILTERS: Record<string, (e: any, hold: Set<string>) => boolean> = {
  all: () => true, decisions: (e) => ["decision", "provisional_decision", "objection"].includes(e.type),
  hold: (e, hold) => e.type === "hold" || cards(e).some((c) => hold.has(c)), checks: (e) => !!e.check_summary,
  visuals: (e) => !!e.visuals?.length,
};
const cards = (e: any): string[] => (e.refs ?? []).filter((r: any) => r.kind === "card").map((r: any) => r.id);

function line(code: string, e: any, hold: Set<string>): string {
  const dec = (e.refs ?? []).find((r: any) => r.kind === "decision")?.id, cs = cards(e);
  const cls = e.type === "provisional_decision" ? "gecici" : FILTERS.hold(e, hold) ? "dur" : "";
  const act = cls === "gecici" && dec ? `<div class="alt-eylem"><span class="etiket-gecici">${h(u("flow.until", { gate: e.objection_until }))}</span>
      <button class="mini-dugme" data-object="${h(dec)}">${h(u("flow.object"))}</button><a class="mini-dugme" href="#/${h(code)}/cards?card=${h(dec)}">${h(u("flow.see"))}</a></div>`
    : cls === "dur" ? `<div class="alt-eylem"><span class="cip dur">${h(u("hold"))}</span><span class="etiket-dur">${h(u("flow.chief_needed"))}</span>
      ${cs.filter((c) => hold.has(c)).map((c) => `<a class="mini-dugme" href="#/${h(code)}/cards?card=${h(c)}">${h(u("flow.open_card"))} ${h(c)}</a>`).join("")}</div>` : "";
  return `<div class="satir-akis ${cls}" data-event="${h(e.id)}" data-type="${h(e.type)}"><span class="saat">${clock(e.at)}</span><span>${role(e.role)}</span>
    <div class="metin">${h(e.line)}${act}</div>
    <span>${e.visuals?.[0]?.path ? `<img class="kucuk-gorsel" src="${fileUrl(code, "images", e.visuals[0].path)}" alt="" loading="lazy">` : ""}</span>
    <span class="kart-bag">${cs.map((c) => `<a href="#/${h(code)}/cards?card=${h(c)}">${h(c)}</a>`).join(" ") || "—"}</span>
    <span>${e.check_summary ? summary(e.check_summary) : "—"}</span>
    ${e.commit ? `<a class="sha" href="#/${h(code)}/branches?sha=${h(e.commit)}">${sha(e.commit)}</a>` : "<span></span>"}</div>`;
}

function lines(code: string, evs: any[], hold: Set<string>, f: string, who: string): string {
  let last = "";
  return evs.filter((e) => FILTERS[f](e, hold) && (!who || e.role === who)).map((e) => {
    const d = e.at.slice(0, 10), head = d !== last ? `<div class="akis-gun">${h(day(e.at))}</div>` : "";
    last = d;
    return head + line(code, e, hold);
  }).join("") || empty("flow.none");
}

function stageDetail(c: Ctx, s: any): string {
  const done = s.status === "done";
  return `<section class="kart-kutu" data-stage-detail="${h(s.gate)}"><div class="kutu-bas"><span class="rozet koyu">${h(s.gate)}</span>
    <h2>${h(name("gate_status", s.status))}</h2><span class="ek">${when(s.started_at)}${s.finished_at ? ` → ${when(s.finished_at)}` : ""}${
    s.approver ? ` · ${h(u("approver"))} ${h(s.approver)}` : ""}${s.tag ? ` · <span class="mono">${h(s.tag)}</span>` : ""}</span></div>
    <div class="iki-kolon"><div class="goruntuleyici mini" id="mini-3d"><div class="bos">${h(u(s.model_commit ? "model.loading" : "model.none"))}</div></div>
    <div class="kutu-ic"><div class="kucuk ikincil">${h(u(done ? "flow.stage_last_model" : "flow.stage_now_model"))} · <span class="mono">${sha(s.model_commit)}</span></div>
    ${s.model_commit ? `<div class="dugme-sira"><a class="dugme birincil" data-open-model href="#/${h(c.code)}/model?commit=${h(s.model_commit)}">${h(u("flow.open_model"))}</a>
    ${done ? `<a class="dugme" href="#/${h(c.code)}/model?compare=${h(s.model_commit)}">${h(u("model.compare_now"))}</a>` : ""}</div>` : ""}
    ${done ? `<button class="dugme ret" data-gate-back="${h(s.gate)}">${h(u("flow.gate_back", { gate: s.gate }))}</button>` : ""}
    <div class="alt-baslik">${h(u("flow.steps"))} · ${s.steps.length}</div><ul class="liste">${s.steps.slice().reverse().map((x: any) =>
      `<li data-stage-step><span class="mono ikincil">${clock(x.at)}</span>${role(x.role)}<span>${h(x.line)}</span></li>`).join("") || `<li class="soluk">—</li>`}</ul>
    <div class="ozellik-izgara"><span class="ad">${h(u("flow.decisions"))}</span><span>${s.decisions.map((d: any) => `${h(d.id)} · ${h(d.title)} ${state(d.status)}${
      d.chosen ? ` · <b>${h(d.chosen)}</b>` : ""}`).join("<br>") || "—"}</span><span class="ad">${h(u("flow.checks"))}</span><span>${summary(s.summary)}</span></div></div></div></section>`;
}

async function showStage(c: Ctx, s: any) {
  mini?.close();
  mini = null;
  const at = c.main.querySelector<HTMLElement>("[data-stage-slot]")!;
  at.innerHTML = stageDetail(c, s);
  c.main.querySelectorAll("[data-gate]").forEach((b) => b.classList.toggle("secili", (b as HTMLElement).dataset.gate === s.gate));
  at.querySelector("[data-gate-back]")?.addEventListener("click", async () => {
    const why = await confirm({ title: u("flow.gate_back", { gate: s.gate }), text: u("flow.gate_back_text"), yes: u("flow.gate_back", { gate: s.gate }),
      field: { label: u("reason"), required: true } });
    if (why === null) return;
    try { await post(`${W(c.code)}/gates/${s.gate}/back`, { reason: why, viewed: c.work.commit.slice(0, 7), confirmed: true }); await reload(); } catch (x) { fail(x); }
  });
  if (!s.model_commit) return;
  const m = await get(`${W(c.code)}/model`, { commit: s.model_commit });
  const el = at.querySelector<HTMLElement>("#mini-3d");
  if (el && m.data) mini = await mountViewer(el, m.data, c.code, { now: m.commit }, { w: el.clientWidth - 2, h: 280, tree: 0 });
  else if (el) el.innerHTML = `<div class="bos">${h(u("model.none"))}</div>`;
}

const inboxList = (items: any[]) => items.slice().reverse().slice(0, 8).map((x) => `<li data-inbox="${h(x.state)}"><span class="mono ikincil">${clock(x.at)}</span>
  ${state(x.state === "pending" ? "open" : x.state === "read" ? "approved" : "awaiting_reply").replace(/>[^<]*</, `>${h(name("inbox", x.state))}<`)}
  <span>${x.kind === "instruction" ? "" : `<b>${h(name("inbox_kind", x.kind))}</b> `}${h(x.text)}</span></li>`).join("") || `<li class="soluk">${h(u("flow.inbox_empty"))}</li>`;

async function side(c: Ctx, tab: string) {
  const tabs = ["summary", "status", "team"].map((k) => `<a data-side-tab="${k}" class="${k === tab ? "secili" : ""}">${h(u(`flow.side.${k}`))}</a>`).join("");
  c.side.innerHTML = `<nav class="yan-sekme">${tabs}</nav><div data-side-body class="panel-govde"><span class="soluk">…</span></div>`;
  c.side.querySelectorAll<HTMLElement>("[data-side-tab]").forEach((a) => a.addEventListener("click", () => go(c.code, "flow", { ...c.q, side: a.dataset.sideTab })));
  const body = c.side.querySelector<HTMLElement>("[data-side-body]")!;
  const list = (k: string, xs: string[]) => `<div class="alt-baslik">${h(u(`flow.sum.${k}`))} <span class="say">${xs.length}</span></div>
    <ul class="liste" data-sum="${k}">${xs.map((x) => `<li>${h(x)}</li>`).join("") || `<li class="soluk">—</li>`}</ul>`;
  if (tab === "summary") {
    const [sum, pol, intake] = await Promise.all([get(`${W(c.code)}/summary`), get(`${W(c.code)}/policy`), get(`${W(c.code)}/intake`).catch(() => null)]);
    const nodes = new Map<string, any>((intake?.plan.nodes ?? []).map((x: any) => [x.key, x]));
    const m = pol.metrics;
    body.innerHTML = `<div class="kucuk ikincil">${h(u("flow.sum.draft"))}</div>${["decisions", "pending", "risks", "agents"].map((k) => list(k, sum.sections[k] ?? [])).join("")}
      <div class="panel-ayrac"></div><div class="alt-baslik">${h(u("flow.stage_end"))} <span class="say">${intake?.plan.stage_end.length ?? 0}</span></div>
      <ol class="adim-liste" data-stage-end>${(intake?.plan.stage_end ?? []).map((k: string) => `<li>${h(own(nodes.get(k)?.node.text) || k)}</li>`).join("")}</ol>
      <div class="ipucu">${h(u("flow.stage_end_note"))}</div><div class="panel-ayrac"></div>
      <div class="alt-baslik">${h(u("flow.measures", { gate: m.gate }))}</div><div class="olcu-izgara" data-measures>
      <div class="olcu-kutu"><span class="buyuk">${m.questions_asked}/${m.questions_limit}</span><span class="ad">${h(u("flow.m.questions"))}</span></div>
      <div class="olcu-kutu"><span class="buyuk mor">${m.provisional_made}</span><span class="ad">${h(u("flow.m.provisional"))}</span></div>
      <div class="olcu-kutu"><span class="buyuk">${m.provisional_reverted}</span><span class="ad">${h(u("flow.m.reverted"))}</span></div></div>`;
  } else if (tab === "status") {
    const s = await get(`${W(c.code)}/status`);
    const link = (x: any) => `<li><a class="mono" href="#/${h(c.code)}/cards?card=${h(x.id)}">${h(x.id)}</a> <span>${h(x.question)}</span>${x.level === "hold"
      ? ` <span class="cip dur">${h(u("hold"))}</span>` : ""}${x.comment ? ` <span class="ikincil">· ${h(x.comment)}</span>` : ""}</li>`;
    body.innerHTML = `<div class="top" data-ball="${h(s.ball.who ?? "none")}">${mascot(s.liveness.status, 40)}<b>${h(t(s.ball.key, s.ball.data))}</b></div>
      ${s.rows.map((r: any) => `<div class="durum-satir ${h(r.kind)}" data-row="${h(r.key)}">${h(t(r.key, r.data))}</div>`).join("")}
      <div class="alt-baslik">${h(u("flow.for_you"))}</div><ul class="liste">${s.chief_cards.map(link).join("") || `<li class="soluk">${h(u("flow.nothing"))}</li>`}</ul>
      <div class="alt-baslik">${h(u("flow.for_team"))}</div><ul class="liste">${s.team_cards.map(link).join("") || `<li class="soluk">${h(u("flow.nothing"))}</li>`}</ul>
      <div class="ozellik-izgara">${s.last ? `<span class="ad">${h(u("flow.last"))}</span><span>${when(s.last.at)} · ${h(s.last.who)} · ${h(s.last.title)}</span>` : ""}
      ${s.next ? `<span class="ad">${h(u("flow.next"))}</span><span>${h(typeof s.next === "string" ? s.next : s.next.text ?? JSON.stringify(s.next))}</span>` : ""}
      ${s.dirty.length ? `<span class="ad">${h(u("flow.dirty"))}</span><span class="mono kucuk">${s.dirty.map(h).join("<br>")}</span>` : ""}</div>`;
  } else {
    const [lv, st] = [S.live[c.code] ?? await get(`${W(c.code)}/liveness`), await get(`${W(c.code)}/stages`)];
    const l = lv.liveness;
    body.innerHTML = `<section class="ekip-ozet" data-team-state="${h(l.status)}">${mascot(l.status, 56)}<div><b>${h(t(`agent.liveness.${l.status}`))}</b>${l.role
      ? ` · ${role(l.role)}` : ""}${l.reason ? `<div data-team-reason="${h(l.reason)}">${h(t(`agent.liveness.${l.reason}`))}</div>` : ""}<div class="ikincil">${
      h(t(lv.ball.key, lv.ball.data))}</div><div class="kucuk ikincil">${l.minutes === null ? h(u("flow.no_pulse")) : h(u("minutes_ago", { n: l.minutes }))}${
      lv.lock ? ` · ${h(u("flow.lock", { at: when(lv.lock.at ?? lv.lock.since) }))}` : ""}${lv.stop ? ` · <b class="kirmizi">${h(u("flow.stop_flag"))}</b>` : ""}</div></div></section>
      <ul class="liste kucuk">${(l.log ?? []).slice(-8).reverse().map((x: any) => `<li><span class="mono ikincil">${clock(x.at)}</span>${role(x.role)}<span>${h(x.doing ?? x.text ?? x.status)}</span></li>`).join("")}</ul>
      <div class="alt-baslik">${h(u("team.title"))}</div><table class="tablo" data-team-roles><tbody>${["chief_engineer", "project_engineer", "design_engineer",
        "technician", "quality_engineer"].map((r) => `<tr class="${r === (lv.ball.who ?? l.role) ? "secili" : ""}"><td>${role(r)}</td><td><b>${h(name("role", r))}</b>
        <div class="kucuk ikincil">${h(u(`team.${r}`))}</div></td><td class="mono kucuk">${h(r === "chief_engineer" ? S.chief : S.roles[r]?.model ?? "—")}</td></tr>`).join("")}</tbody></table>
      <div class="alt-baslik">${h(u("flow.done_work"))}</div><div data-steps>${st.activity.map((a: any) => `<details class="adim-satir" data-step="${h(a.commit)}">
      <summary><span class="mono ikincil">${when(a.at)}</span>${role(a.role)}<span>${h(a.line)}</span></summary><div class="adim-govde soluk">…</div></details>`).join("") || empty("flow.none")}</div>`;
    body.querySelectorAll<HTMLDetailsElement>("details[data-step]").forEach((d) => d.addEventListener("toggle", async () => {
      if (!d.open || d.dataset.loaded) return;
      d.dataset.loaded = "1";
      d.querySelector(".adim-govde")!.innerHTML = stepDetail(c.code, await get(`${W(c.code)}/steps/${d.dataset.step}`).catch((e) => ({ error: e.message })));
    }));
  }
}

export function stepDetail(code: string, x: any): string {
  if (x.error) return `<div class="hata-kutu">${h(x.error)}</div>`;
  const v = (p: any) => (p ? `${num(p.value)} ${h(p.unit ?? "")}` : "—");
  const sec = (k: string, html: string) => `<div data-step-${k}><div class="alt-baslik">${h(u(`step.${k}`))}</div>${html}</div>`;
  return `<div class="adim-detay"><div class="kucuk ikincil">${when(x.at)} · ${h(x.author)} · <span class="mono">${sha(x.commit)}</span> · ${summary(x.summary)}</div>
    ${sec("text", `<div class="pre">${h(x.text)}</div>`)}
    ${x.params.length ? sec("params", `<table class="tablo"><tbody>${x.params.map((p: any) => `<tr><td class="mono">${h(p.name)}</td><td>${v(p.before)}</td><td>→</td>
      <td><b>${v(p.after)}</b></td><td class="ikincil">${h(p.after?.source ?? "")}</td></tr>`).join("")}</tbody></table>`) : ""}
    ${x.calcs.length ? sec("calcs", x.calcs.map((k: any) => `<div class="mono kucuk">${h(k.path)}</div>${k.results.map((r: any) => `<div>${h(r.name)}: ${num(r.before)} → <b>${
      num(r.after)}</b> ${h(r.unit ?? "")}</div>`).join("")}`).join("")) : ""}
    ${x.code_diff.length ? sec("diff", x.code_diff.map((d: any) => `<div class="mono kucuk">${h(d.path)}</div><pre class="kod-farki">${d.lines.map((l: string) =>
      `<span class="${l[0] === "+" ? "ek" : l[0] === "-" ? "sil" : ""}">${h(l)}</span>`).join("\n")}</pre>`).join("")) : ""}
    ${sec("files", `<ul class="liste mono kucuk">${x.files.map((f: any) => `<li>${h(f.path)} <span class="yesil">+${h(f.added)}</span> <span class="kirmizi">−${h(f.removed)}</span></li>`).join("")}</ul>`)}</div>`;
}

export async function flowScreen(c: Ctx) {
  mini?.close();
  mini = null;
  const [st, stages, inbox, status] = await Promise.all([get(`${W(c.code)}/stream`), get(`${W(c.code)}/stages`), get(`${W(c.code)}/inbox`),
    get(`${W(c.code)}/status`)]);
  const evs: any[] = st.events.slice().reverse(), f = c.q.filter ?? "all", who = c.q.role ?? "";
  const hold = new Set<string>(status.chief_cards.filter((x: any) => x.level === "hold").map((x: any) => x.id));
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.flow"))}</h1><p>${h(u("flow.lead"))}</p></div>
    <span class="canli"><span class="nokta yesil"></span>${h(u("flow.live", { at: clock(evs[0]?.at) || "—" }))}</span></div>
    <div class="asama-serit" data-stages>${stages.stages.filter((s: any) => s.planned).map((s: any) => `<button class="asama ${h(s.status)}" data-gate="${h(s.gate)}"
      data-status="${h(s.status)}" ${s.status === "pending" ? "disabled" : ""}><span class="mono">${h(s.gate)}</span><span>${h(name("gate_status", s.status))}</span></button>`).join("")}</div>
    <div data-stage-slot></div>
    <div class="akis-arac">${Object.keys(FILTERS).map((k) => `<a class="hap ${k === f ? "secili" : ""}" data-filter="${k}">${h(u(`flow.f.${k}`))}</a>`).join("")}
      <span class="bosluk"></span><select class="alan" data-role-filter><option value="">${h(u("flow.all_roles"))}</option>${[...new Set(evs.map((e) => e.role))].map((r) =>
      `<option value="${h(r)}" ${r === who ? "selected" : ""}>${h(name("role", r))}</option>`).join("")}</select></div>
    <div class="akis" data-stream>${lines(c.code, evs, hold, f, who)}</div>
    <div class="talimat"><div><textarea data-instruction rows="2" placeholder="${h(u("flow.instruction_ph"))}"></textarea>
      <span class="not">${h(u("flow.instruction_note"))}</span></div><div class="dugme-sira"><button class="dugme birincil" data-send>${h(u("send"))}</button>
      <button class="dugme ret" data-stop>■ ${h(u("stop"))}</button><button class="dugme" data-open-session>▶ ${h(u("open_session"))}</button></div></div>
    <div class="gelen"><div class="alt-baslik">${h(u("flow.inbox"))}</div><ul class="liste" data-inbox-list>${inboxList(inbox.items)}</ul></div>`;
  const m = c.main;
  m.querySelectorAll<HTMLElement>("[data-filter]").forEach((a) => a.addEventListener("click", () => go(c.code, "flow", { ...c.q, filter: a.dataset.filter })));
  m.querySelector<HTMLSelectElement>("[data-role-filter]")!.addEventListener("change", (e) => go(c.code, "flow", { ...c.q, role: (e.target as HTMLSelectElement).value }));
  m.querySelectorAll<HTMLElement>("[data-gate]").forEach((b) => b.addEventListener("click", () =>
    showStage(c, stages.stages.find((s: any) => s.gate === b.dataset.gate)).catch(fail)));
  m.querySelector("[data-stream]")!.addEventListener("click", async (e) => {
    const b = (e.target as HTMLElement).closest<HTMLElement>("[data-object]");
    if (!b) return;
    const why = await confirm({ title: u("flow.object_title", { id: b.dataset.object }), text: u("flow.object_text"), yes: u("flow.object"),
      field: { label: u("reason"), required: true } });
    if (why === null) return;
    try { await post(`${W(c.code)}/decisions/${b.dataset.object}/objection`, { reason: why, viewed: c.work.commit.slice(0, 7) }); toast(h(u("flow.objected")), "objection"); }
    catch (x) { fail(x); }
  });
  const box = m.querySelector<HTMLTextAreaElement>("[data-instruction]")!;
  m.querySelector("[data-send]")!.addEventListener("click", async () => {
    if (!box.value.trim()) return box.focus();
    try { await post(`${W(c.code)}/instructions`, { text: box.value }); box.value = ""; toast(h(u("flow.sent")), "instruction"); }
    catch (x) { fail(x); }
  });
  S.onStream = (e) => {
    evs.unshift(e);
    const s = m.querySelector("[data-stream]");
    if (s) s.innerHTML = lines(c.code, evs, hold, f, who);
  };
  S.onInbox = (ev) => { const l = m.querySelector("[data-inbox-list]"); if (l) l.innerHTML = inboxList(ev.items); };
  const sel = stages.stages.find((s: any) => s.gate === c.q.gate);
  if (sel) showStage(c, sel).catch(fail);
  await side(c, c.q.side ?? "summary");
}
