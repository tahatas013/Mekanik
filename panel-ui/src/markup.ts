// A note on the model (old isaretle.ts, e2e 17): the chief drags an area on the 3D view and writes a note; sent are
// the screenshot (area framed red), the part and the 3D point under the area's centre (ray cast), the camera. The
// server opens card N-nn; the team replies and applies it. Open notes are pinned on the model.
import { post, W } from "./api";
import { fail } from "./ui";
import { h, num, sha, u } from "./util";
import { pins, type View } from "./viewer";

const MAX_W = 1600;   // source: assumption — old EN_GENIS: widest screenshot sent (px); larger ones are scaled down

function scene(v: View) {
  const cv: HTMLCanvasElement | undefined = v.viewer.renderer?.domElement;
  const cam = v.viewer.rendered?.camera?.getCamera?.() ?? v.viewer.camera?.getCamera?.(), sc = v.viewer.rendered?.scene;
  return cv && cam && sc ? { cv, cam, sc } : null;
}

/** The first visible model face under (nx, ny): its part and point (clip helpers and caps are not targets). */
function cast(v: View, nx: number, ny: number): { part: string | null; point: number[] | null } {
  const s = scene(v);
  if (!s) return { part: null, point: null };
  const r = new v.three.Raycaster();
  r.setFromCamera(new v.three.Vector2(nx * 2 - 1, -(ny * 2 - 1)), s.cam);
  const shown = (o: any) => { for (let x = o; x; x = x.parent) if (!x.visible) return false; return true; };
  const path = (o: any): string | null => {
    if (/^(frontStencil|backStencil|StencilPlane)/.test(o.name || "")) return null;
    for (let x = o.parent; x; x = x.parent) if (typeof x.name === "string" && x.name.startsWith("|") && x.name.split("|").length > 2) return x.name;
    return null;
  };
  const hit = r.intersectObjects(s.sc.children, true).find((x: any) => x.object.isMesh && x.face && shown(x.object) && path(x.object));
  if (!hit) return { part: null, point: null };
  return { part: path(hit.object)!.split("|").filter(Boolean).pop() ?? null, point: hit.point.toArray().map((x: number) => Math.round(x * 100) / 100) };
}

function shot(v: View, box: number[]): string | null {
  const s = scene(v);
  if (!s) return null;
  v.viewer.renderer.render(s.sc, s.cam);   // the drawing buffer is not kept: draw and read at once
  const k = Math.min(1, MAX_W / s.cv.width), c = document.createElement("canvas");
  c.width = Math.round(s.cv.width * k);
  c.height = Math.round(s.cv.height * k);
  const g = c.getContext("2d")!;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, c.width, c.height);
  g.drawImage(s.cv, 0, 0, c.width, c.height);
  const [x0, y0, x1, y1] = [box[0] * c.width, box[1] * c.height, box[2] * c.width, box[3] * c.height];
  g.fillStyle = "rgba(179,38,30,0.10)";
  g.fillRect(x0, y0, x1 - x0, y1 - y0);
  g.strokeStyle = "#B3261E";
  g.lineWidth = Math.max(2, 3 * k);
  g.strokeRect(x0, y0, x1 - x0, y1 - y0);
  return c.toDataURL("image/png");
}

export function startMarking(v: View, host: HTMLElement, code: string, commit: string, sent: (id: string) => void) {
  const s = scene(v);
  if (!s) return;
  const cr = s.cv.getBoundingClientRect(), hr = host.getBoundingClientRect();
  const lay = document.createElement("div");
  lay.className = "isaretleme";
  lay.dataset.marking = "";
  Object.assign(lay.style, { left: `${cr.left - hr.left}px`, top: `${cr.top - hr.top}px`, width: `${cr.width}px`, height: `${cr.height}px` });
  lay.innerHTML = `<div class="isaretleme-ipucu">${h(u("note.hint"))}</div><div class="isaretleme-kutu" hidden></div>`;
  host.appendChild(lay);
  const frame = lay.querySelector<HTMLElement>(".isaretleme-kutu")!;
  let a: [number, number] | null = null;
  const done = () => { lay.remove(); document.removeEventListener("keydown", esc); };
  const esc = (e: KeyboardEvent) => e.key === "Escape" && done();
  document.addEventListener("keydown", esc);
  const at = (e: PointerEvent): [number, number] => {
    const r = lay.getBoundingClientRect();
    return [Math.min(Math.max(e.clientX - r.left, 0), r.width), Math.min(Math.max(e.clientY - r.top, 0), r.height)];
  };
  lay.addEventListener("pointerdown", (e) => { a = at(e); lay.setPointerCapture(e.pointerId); });
  lay.addEventListener("pointermove", (e) => {
    if (!a) return;
    const [x, y] = at(e);
    frame.hidden = false;
    Object.assign(frame.style, { left: `${Math.min(x, a[0])}px`, top: `${Math.min(y, a[1])}px`, width: `${Math.abs(x - a[0])}px`, height: `${Math.abs(y - a[1])}px` });
  });
  lay.addEventListener("pointerup", (e) => {
    if (!a) return;
    const [x, y] = at(e), Wd = lay.clientWidth, Hd = lay.clientHeight;
    let box = [Math.min(x, a[0]) / Wd, Math.min(y, a[1]) / Hd, Math.max(x, a[0]) / Wd, Math.max(y, a[1]) / Hd];
    if ((box[2] - box[0]) * Wd < 6 || (box[3] - box[1]) * Hd < 6) {   // a click: a small area around it
      const cx = x / Wd, cy = y / Hd, d = 0.04;
      box = [Math.max(cx - d, 0), Math.max(cy - d, 0), Math.min(cx + d, 1), Math.min(cy + d, 1)];
    }
    a = null;
    const png = shot(v, box), { part, point } = cast(v, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2), cam = scene(v)!.cam;
    const target = v.viewer.controls?.target;
    done();
    form(host, code, { png, part, point, box, commit, camera: { position: cam.position.toArray().map((q: number) => Math.round(q * 10) / 10),
      target: target?.toArray?.().map((q: number) => Math.round(q * 10) / 10) } }, sent);
  });
}

function form(host: HTMLElement, code: string, n: any, sent: (id: string) => void) {
  const f = document.createElement("div");
  f.className = "not-formu";
  f.dataset.noteForm = "";
  f.innerHTML = `<div class="not-formu-ic"><b>${h(u("note.title"))}</b>${n.png ? `<img src="${n.png}" alt="${h(u("note.area"))}">` : `<div class="hata-kutu">${h(u("note.no_image"))}</div>`}
    <div class="ikincil kucuk">${n.part ? `${h(u("note.part"))}: <span class="mono">${h(n.part)}</span>` : h(u("note.no_part"))}${n.point ? ` · ${h(u("note.point"))}
    <span class="mono">(${n.point.map((x: number) => num(x, 1)).join("; ")}) mm</span>` : ""} · ${h(u("note.version"))} <span class="mono">${sha(n.commit)}</span></div>
    <textarea rows="4" placeholder="${h(u("note.ph"))}"></textarea><div class="dugme-sira sag"><button class="dugme" data-cancel>${h(u("cancel"))}</button>
    <button class="dugme birincil" data-send>${h(u("send"))}</button></div><span class="ikincil kucuk">${h(u("note.after"))}</span></div>`;
  host.appendChild(f);
  const ta = f.querySelector("textarea")!;
  ta.focus();
  f.querySelector("[data-cancel]")!.addEventListener("click", () => f.remove());
  f.querySelector<HTMLButtonElement>("[data-send]")!.addEventListener("click", async (e) => {
    const b = e.currentTarget as HTMLButtonElement;
    if (!ta.value.trim()) return ta.focus();
    b.disabled = true;
    try {
      const r = await post(`${W(code)}/model-notes`, { text: ta.value, png: n.png ?? "", part: n.part, point: n.point, camera: n.camera, box: n.box, commit: n.commit });
      f.remove();
      sent(r.card);
    } catch (x) { b.disabled = false; fail(x); }
  });
}

export const noteMarkers = (v: View, host: HTMLElement, notes: any[], open: (id: string) => void) =>
  pins(v, host, notes.filter((n) => n.subject?.point).map((n) => ({ pos: n.subject.point, cls: "not-isareti", html: h(n.id), click: () => open(n.id),
    attrs: { "data-note-marker": n.id, title: `${n.id} · ${n.question ?? ""}` } })));
