// Files (old ciktilar.ts; architecture §5.6): what can be downloaded (out/ releases with their report's SHA check,
// records/, inputs/; a file as it is, a folder as zip) and dropping inputs (STEP, STL, PDF, images → inputs/, SHA-256
// in work.yaml, one commit). Calculations and analyses (old hesaplar.ts): results, steps, inputs, charts, notes.
import { fileUrl, get, put, W } from "../api";
import { type Ctx, go, reload } from "../main";
import { fail, toast } from "../ui";
import { chip, empty, h, name, num, size, sha, u, when } from "../util";

export async function upload(code: string, files: File[], limit: number): Promise<number> {
  let n = 0;
  for (const f of files) {
    if (f.size > limit) { toast(h(u("files.too_large", { name: f.name })), "upload"); continue; }
    try { await put(`${W(code)}/inputs/${encodeURIComponent(f.name)}`, f); n++; } catch (e) { fail(e); }
  }
  return n;
}

export function dropZone(onFiles: (f: File[]) => void): { html: string; bind: (el: HTMLElement) => void } {
  return {
    html: `<label class="birak" data-drop><span>⇪</span><div><b>${h(u("files.drop"))}</b><div class="kucuk">${h(u("files.drop_hint"))}</div></div>
      <input type="file" multiple hidden data-file-input></label>`,
    bind: (el) => {
      const z = el.querySelector<HTMLElement>("[data-drop]")!;
      z.addEventListener("dragover", (e) => { e.preventDefault(); z.classList.add("uzerinde"); });
      z.addEventListener("dragleave", () => z.classList.remove("uzerinde"));
      z.addEventListener("drop", (e) => { e.preventDefault(); z.classList.remove("uzerinde"); onFiles([...(e.dataTransfer?.files ?? [])]); });
      z.querySelector<HTMLInputElement>("[data-file-input]")!.addEventListener("change", (e) => onFiles([...((e.target as HTMLInputElement).files ?? [])]));
    },
  };
}

export async function filesScreen(c: Ctx) {
  const [v, s] = await Promise.all([get(`${W(c.code)}/files`), get("/api/session")]);
  const dz = dropZone(async (fs) => { if (await upload(c.code, fs, s.upload_limit)) { toast(h(u("files.added", { n: fs.length })), "upload"); await reload(); } });
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.files"))}</h1><p>${h(u("files.lead"))}</p></div></div>${dz.html}
    ${v.folders.map((k: any) => `<section class="kart-kutu" data-folder="${h(k.path)}"><div class="kutu-bas"><h2 class="mono">${h(k.path)}</h2>${chip(k.kind === "release" ? "ok" : "gri", name("folder", k.kind))}
      <span class="ek"><a class="dugme" href="${fileUrl(c.code, "download", k.path)}" download data-zip>${h(u("files.zip"))}</a></span></div><div class="kaydir"><table class="tablo">
      <thead><tr><th>${h(u("files.file"))}</th><th class="sag-hiza">${h(u("files.size"))}</th><th>SHA-256</th><th></th></tr></thead><tbody>${k.files.map((f: any) =>
      `<tr data-file="${h(f.path)}"><td class="mono">${h(f.name)}</td><td class="sag-hiza mono">${size(f.size)}</td><td class="sha" title="${h(f.sha256)}">${h(f.sha256.slice(0, 12))}…
      ${f.matches === true ? chip("ok", u("files.matches")) : f.matches === false ? chip("engel", u("files.changed")) : ""}</td>
      <td class="sag-hiza"><a class="mini-dugme" href="${fileUrl(c.code, "download", f.path)}" download>${h(u("files.download"))}</a></td></tr>`).join("")}</tbody></table></div></section>`).join("") || empty("files.none")}`;
  dz.bind(c.main);
  c.side.innerHTML = `<div class="panel-baslik">${h(u("nav.files"))}</div><div class="panel-govde"><div class="ipucu">${h(u("files.side"))}</div>
    <div class="ozellik-izgara">${(c.work.inputs ?? []).map((i: any) => `<span class="ad mono kucuk">${h(i.path)}</span><span class="sha">${h(i.sha256.slice(0, 12))}… · ${when(i.added_at)}</span>`).join("")}</div></div>`;
}

const COLORS = ["#2F6FDE", "#C26A1B", "#2E6B46", "#8B6FE0"];
function chart(g: any): string {
  const Wd = 640, Hd = 300, l = 64, b = 40, tp = 16, r = 20, xs: number[] = g.x, ser = Object.entries(g.series ?? {}) as [string, number[]][];
  const ys = ser.flatMap(([, v]) => v).filter((v) => v !== null);
  if (!xs.length || !ys.length) return "";
  const [x0, x1] = [Math.min(...xs), Math.max(...xs)];
  let [y0, y1] = [Math.min(...ys), Math.max(...ys)];
  if (y0 === y1) { y0 -= 1; y1 += 1; }
  const px = (x: number) => l + ((x - x0) / (x1 - x0 || 1)) * (Wd - l - r), py = (y: number) => Hd - b - ((y - y0) / (y1 - y0)) * (Hd - b - tp);
  const grid = [0, 0.5, 1].map((q) => { const yv = y0 + q * (y1 - y0), xv = x0 + q * (x1 - x0);
    return `<line x1="${l}" x2="${Wd - r}" y1="${py(yv)}" y2="${py(yv)}" stroke="#EEF0F2"/><text x="${l - 6}" y="${py(yv) + 3}" font-size="12" text-anchor="end" fill="#5F6873">${num(yv, 1)}</text>
      <text x="${px(xv)}" y="${Hd - b + 14}" font-size="12" text-anchor="middle" fill="#5F6873">${num(xv, 1)}</text>`; }).join("");
  const lines = ser.map(([, v], i) => `<path fill="none" stroke="${COLORS[i % 4]}" stroke-width="2" d="${xs.map((x, j) => (v[j] === null ? "" : `${j ? "L" : "M"}${px(x).toFixed(1)},${py(v[j]).toFixed(1)}`)).join(" ")}"/>`).join("");
  const mk = g.marker ? `<circle cx="${px(g.marker[0])}" cy="${py(g.marker[1])}" r="4" fill="#B3261E"/><text x="${px(g.marker[0]) + 7}" y="${py(g.marker[1]) - 7}" font-size="13" fill="#B3261E">${h(g.marker[2] ?? "")}</text>` : "";
  return `<figure class="grafik" data-chart><b>${h(g.title)}</b><svg viewBox="0 0 ${Wd} ${Hd}">${grid}<line x1="${l}" x2="${Wd - r}" y1="${Hd - b}" y2="${Hd - b}" stroke="#8B939C"/>
    <line x1="${l}" x2="${l}" y1="${tp}" y2="${Hd - b}" stroke="#8B939C"/>${lines}${mk}<text x="${(Wd + l) / 2}" y="${Hd - 4}" font-size="13" text-anchor="middle" fill="#3B434C">${h(g.x_label)}</text>
    <text x="14" y="${(Hd - b) / 2}" font-size="13" text-anchor="middle" fill="#3B434C" transform="rotate(-90 12 ${(Hd - b) / 2})">${h(g.y_label)}</text></svg>
    ${ser.length > 1 ? `<div class="lejant kucuk">${ser.map(([n], i) => `<span><span class="cizgi" style="background:${COLORS[i % 4]}"></span>${h(n)}</span>`).join("")}</div>` : ""}</figure>`;
}

const q = (x: any) => `${num(x.quantity?.value ?? x.value)} <span class="soluk">${h(x.quantity?.unit ?? x.unit ?? "")}</span>`;
const RESULT: Record<string, string> = { ok: "ok", good: "ok", limit: "uyari", bad: "engel", unreliable: "gri" };

function calcView(c: Ctx, x: any): string {
  return `<article class="kart-std" data-calc="${h(x.id)}"><header><div class="ust-satir"><span class="mono">${h(x.code?.path ?? x.id)}</span>${chip(x.error ? "engel" : "ok", u(x.error ? "calc.error" : "calc.done"))}
    <span>${when(x.ran_at)} · ${h(x.method?.name ?? "")}</span><span class="mono soluk">${sha(x.result_hash)}</span></div><h1>${h(x.title ?? x.id)}</h1>
    ${x.purpose ? `<div class="neden"><span><b>${h(u("calc.purpose"))}</b> ${h(x.purpose)}</span></div>` : ""}${x.error ? `<div class="hata-kutu">${h(x.error)}</div>` : ""}</header>
    ${x.results?.length ? `<section><div class="bolum-baslik"><b>${h(u("calc.results"))}</b></div><div class="sonuclar">${x.results.map((r: any) => `<div class="sonuc ${RESULT[r.status] ?? ""}">
      <span class="ikincil kucuk">${h(r.name)}</span><span class="buyuk">${num(r.value)} <span class="soluk">${h(r.unit)}</span></span>${r.uncertainty_note ? `<span class="kucuk">${h(r.uncertainty_note)}</span>` : ""}</div>`).join("")}</div></section>` : ""}
    ${(x.visuals ?? []).length ? `<section><div class="figurler">${x.visuals.map((v: any) => `<figure><img src="${fileUrl(c.code, "images", v.path)}" alt="${h(v.id ?? "")}"></figure>`).join("")}</div></section>` : ""}
    ${(x.charts ?? []).length ? `<section><div class="bolum-baslik"><b>${h(u("calc.charts"))}</b></div><div class="grafikler">${x.charts.map(chart).join("")}</div></section>` : ""}
    <section data-calc-steps><div class="bolum-baslik"><b>${h(u("calc.steps"))}</b><span>${h(u("calc.steps_note"))}</span></div><div class="kaydir"><table class="tablo"><tbody>${(x.steps ?? []).map((s: any, i: number) =>
      `<tr><td class="soluk">${i + 1}</td><td>${h(s.title)}</td><td class="mono">${h(s.formula)}</td><td class="mono sag-hiza">${num(s.value)} ${h(s.unit)}</td><td class="ikincil">${h(s.source ?? "")}</td></tr>`).join("")
      || `<tr><td class="soluk">—</td></tr>`}</tbody></table></div></section>
    <section><div class="bolum-baslik"><b>${h(u("calc.inputs"))}</b></div><div class="kaydir"><table class="tablo"><tbody>${[...(x.inputs ?? []), ...(x.constants ?? [])].map((i: any) =>
      `<tr><td class="mono">${h(i.name)}</td><td class="mono">${q(i)}</td><td class="${i.quantity?.source ? "ikincil" : "kirmizi"}">${h(i.quantity?.source ?? u("card.no_source"))}</td></tr>`).join("")
      || `<tr><td class="soluk">—</td></tr>`}</tbody></table></div></section>
    ${(x.notes ?? []).length ? `<section><div class="bolum-baslik"><b>${h(u("calc.notes"))}</b></div><ul class="liste">${x.notes.map((n: string) => `<li>${h(n)}</li>`).join("")}</ul></section>` : ""}</article>`;
}

export async function calcsScreen(c: Ctx) {
  const v = await get(`${W(c.code)}/calcs`, { branch: c.q.branch });
  const kind = c.screen === "analyses" ? "analysis" : "calculation", list = v.calcs.filter((x: any) => (x.type ?? "calculation") === kind);
  const sel = list.find((x: any) => x.id === c.q.calc) ?? list[0];
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u(`nav.${c.screen}`))}</h1><p>${h(u(`calc.lead_${c.screen}`))}</p></div></div>
    ${sel ? calcView(c, sel) : empty(`calc.none_${c.screen}`)}${v.unrecorded.length ? `<div class="bilgi-kutu">${h(u("calc.unrecorded", { ids: v.unrecorded.join(", ") }))}</div>` : ""}`;
  const extra = document.getElementById("tree-extra");
  if (extra) extra.innerHTML = list.map((x: any) => `<a class="agac-satir g4 ${x === sel ? "secili" : ""}" data-calc-link="${h(x.id)}"><span class="kare" style="background:${
    x.error ? "#B3261E" : "#2E6B46"}"></span><span class="ad">${h(x.title ?? x.id)}</span></a>`).join("");
  extra?.querySelectorAll<HTMLElement>("[data-calc-link]").forEach((a) => a.addEventListener("click", () => go(c.code, c.screen, { calc: a.dataset.calcLink })));
  c.side.innerHTML = `<div class="panel-baslik">${h(u(`nav.${c.screen}`))} <span class="mono">${list.length}</span></div><div class="panel-govde"><ul class="liste">${list.map((x: any) =>
    `<li><a data-calc-link="${h(x.id)}" href="#/${h(c.code)}/${c.screen}?calc=${h(x.id)}">${h(x.title ?? x.id)}</a>${x.critical ? chip("uyari", u("calc.critical")) : ""}</li>`).join("") || `<li class="soluk">—</li>`}</ul></div>`;
}
