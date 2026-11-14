// Project / work opening (wireframe project-new.html; A1): organization and project from the config, title, purpose,
// "done" criterion, risk class, work type (installed types), input files (uploaded after the work exists: inputs/,
// SHA-256 in work.yaml), the suggested package; the CLI equivalent. The code is given by the store when it opens.
import { get, post } from "../api";
import { go, refreshData } from "../main";
import type { Ctx } from "../main";
import { fail, toast } from "../ui";
import { h, own, size, u } from "../util";
import { dropZone, upload } from "./files";

const quote = (s: string) => (/^[\w./:@-]+$/.test(s) ? s : `'${s.replace(/'/g, `'\\''`)}'`);

export async function newWorkScreen(c: Ctx) {
  const [o, s] = await Promise.all([get("/api/new-work"), get("/api/session")]);
  const files: File[] = [], types = Object.values(o.work_types) as any[];
  const field = (k: string, html: string, hint = "") => `<label>${h(u(`new.${k}`))}</label><div>${html}${hint ? `<div class="ipucu">${h(hint)}</div>` : ""}</div>`;
  const dz = dropZone((fs) => { files.push(...fs); draw(); });
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("new.title"))}</h1><p>${h(u("new.lead"))}</p></div></div>
    <section class="kart-kutu"><div class="kutu-bas"><span class="bolum-no">1</span><h2>${h(u("new.where"))}</h2></div><div class="kutu-ic form-izgara">
    ${field("org", `<select class="alan" data-in="org">${o.organizations.map((x: any) => `<option value="${h(x.code)}">${h(x.name)} · ${h(x.code)}</option>`).join("")}</select>`, u("new.org_hint"))}
    ${field("project", `<select class="alan" data-in="project"></select>`, u("new.project_hint"))}
    ${field("work_title", `<input class="alan" data-in="title" required>`)}${field("purpose", `<textarea rows="2" data-in="purpose"></textarea>`)}
    ${field("done", `<textarea rows="2" data-in="done"></textarea>`, u("new.done_hint"))}
    ${field("class", `<select class="alan" data-in="risk">${o.classes.map((x: string) => `<option ${x === "C" ? "selected" : ""}>${h(x)}</option>`).join("")}</select>`, u("new.class_hint"))}</div></section>
    <section class="kart-kutu"><div class="kutu-bas"><span class="bolum-no">2</span><h2>${h(u("new.type"))}</h2><span class="ek">${h(u("new.type_hint"))}</span></div>
    <div class="kutu-ic tur-kartlar">${types.map((t) => `<label class="tur-kart" data-type="${h(t.id)}"><input type="radio" name="type" value="${h(t.id)}"><b>${h(own(t.title))}</b>
      <p>${h(own(t.description))}</p><span class="kucuk ikincil">${h((t.required_inputs ?? []).map((i: any) => `${i.id} (${(i.accept ?? []).join(" ")})`).join(" · "))}</span></label>`).join("")}</div></section>
    <section class="kart-kutu"><div class="kutu-bas"><span class="bolum-no">3</span><h2>${h(u("new.inputs"))}</h2><span class="ek">${h(u("new.inputs_hint"))}</span></div>
    <div class="kutu-ic">${dz.html}<div data-queue></div></div></section>
    <section class="kart-kutu"><div class="kutu-bas"><span class="bolum-no">4</span><h2>${h(u("new.package"))}</h2></div><div class="kutu-ic" data-packages></div></section>`;
  dz.bind(c.main);
  const val = (k: string) => (c.main.querySelector<HTMLInputElement>(`[data-in="${k}"]`)?.value ?? "").trim();
  const type = () => c.main.querySelector<HTMLInputElement>("input[name=type]:checked")?.value;
  function draw() {
    const org = o.organizations.find((x: any) => x.code === val("org")), t = o.work_types[type() ?? ""];
    const pr = c.main.querySelector<HTMLSelectElement>("[data-in=project]")!;
    if (pr.dataset.org !== org?.code) { pr.dataset.org = org?.code; pr.innerHTML = (org?.projects ?? []).map((p: any) => `<option value="${h(p.code)}">${h(p.name)} · ${h(p.code)}</option>`).join(""); }
    c.main.querySelectorAll<HTMLElement>("[data-type]").forEach((x) => x.classList.toggle("secili", x.dataset.type === type()));
    c.main.querySelector("[data-queue]")!.innerHTML = files.length ? `<table class="tablo"><tbody>${files.map((f, i) => `<tr data-queued="${h(f.name)}"><td class="mono">${h(f.name)}</td>
      <td class="mono sag-hiza">${size(f.size)}</td><td>${h(u("new.after_open"))}</td><td><a data-unqueue="${i}">×</a></td></tr>`).join("")}</tbody></table>` : "";
    c.main.querySelectorAll<HTMLElement>("[data-unqueue]").forEach((a) => a.addEventListener("click", () => { files.splice(+a.dataset.unqueue!, 1); draw(); }));
    c.main.querySelector("[data-packages]")!.innerHTML = `${(t?.default_packages ?? []).map((p: string) => `<div class="secim-kutu secili"><span class="mono">${h(p)}</span>
      <span class="rozet mavi">${h(u(o.packages.includes(p) ? "new.suggested" : "new.not_installed"))}</span></div>`).join("") || `<div class="ipucu">${h(u("new.pick_type"))}</div>`}
      <div class="ipucu">${h(u("new.installed", { list: o.packages.join(", ") }))}</div>`;
    const cli = ["mekanik", "work", "new", "--org", val("org"), "--project", val("project") || pr.value, "--title", val("title") || "…", "--class", val("risk"),
      ...(val("purpose") ? ["--purpose", val("purpose")] : []), ...(val("done") ? ["--done", val("done")] : [])].map(quote).join(" ");
    c.side.innerHTML = `<div class="panel-baslik">${h(u("new.to_open"))}</div><div class="panel-govde"><div class="ozellik-izgara">
      <span class="ad">${h(u("new.code"))}</span><span>${h(u("new.code_given"))}</span><span class="ad">${h(u("new.branches"))}</span><span class="mono kucuk">&lt;${h(u("new.code"))}&gt;/main · /work/general</span>
      <span class="ad">${h(u("new.first_gate"))}</span><span class="mono kucuk">G0</span><span class="ad">${h(u("new.type"))}</span><span>${h(t ? own(t.title) : "—")}</span></div>
      ${org && !org.data_allowed ? `<div class="hata-kutu">${h(u("new.data_forbidden", { org: org.code }))}</div>` : ""}
      <div class="bilgi-kutu"><span class="cip dur">${h(u("hold"))}</span>${h(u("new.hold_note"))}</div>
      <button class="dugme birincil genis" data-create>${h(u("new.create"))}</button>
      <div class="alt-baslik">${h(u("new.cli"))}</div><div class="cli"><code data-cli>${h(cli)}${t ? `<br>mekanik intake choose ${h(t.id)}` : ""}</code></div></div>`;
    c.side.querySelector("[data-create]")!.addEventListener("click", create);
  }
  async function create(e: Event) {
    const b = e.currentTarget as HTMLButtonElement;
    if (!val("title")) return c.main.querySelector<HTMLInputElement>("[data-in=title]")!.focus();
    b.disabled = true;
    try {
      const r = await post("/api/works", { org: val("org"), project: val("project"), title: val("title"), risk_class: val("risk"), purpose: val("purpose"),
        done_criterion: val("done"), work_type: type() || null });
      const n = files.length ? await upload(r.code, files, s.upload_limit) : 0;
      toast(h(u("new.opened", { code: r.code, n })), "new_work");
      await refreshData();
      go(r.code, "flow");
    } catch (x) { b.disabled = false; fail(x); }
  }
  c.main.addEventListener("input", draw);
  c.main.addEventListener("change", draw);
  draw();
}
