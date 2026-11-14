// three-cad-viewer, loaded only when a model is shown (A3: text screens stay light). Measurements use the panel's
// exact-solid back end (POST /api/measure): the viewer reports the selected shapes, the answer comes back to it.
// Two versions in one scene for "compare" (old grey and see-through); fit markers coloured by state (old e2e 10).
import { post } from "./api";
import { h, name } from "./util";

export interface View { viewer: any; three: any; close: () => void }

export async function mountViewer(el: HTMLElement, data: any, code: string, commits: { now: string; before?: string },
                                  size: { w: number; h: number; tree: number }): Promise<View> {
  const [{ Display, Viewer }, three] = await Promise.all([import("three-cad-viewer"), import("three"), import("three-cad-viewer/css")]);
  el.innerHTML = "";
  let tool = "PropertiesMeasurement";
  let viewer: any;
  const notify = (ch: any) => {
    if (ch.activeTool) tool = String(ch.activeTool.new ?? ch.activeTool).toLowerCase().includes("distance") ? "DistanceMeasurement" : "PropertiesMeasurement";
    const sel = ch.selectedShapeIDs?.new ?? ch.selectedShapeIDs;
    if (!Array.isArray(sel) || !sel.length) return;
    const paths = sel.filter((x: unknown) => typeof x === "string");
    if (!paths.length) return;
    const before = commits.before && paths.every((p: string) => p.includes("/before/"));
    post("/api/measure", { work: code, commit: before ? commits.before : commits.now, tool, paths, center: sel[sel.length - 1] === true })
      .then((r) => viewer?.handleBackendResponse(r), (e) => console.warn("measure:", e));
  };
  const display = new Display(el, { cadWidth: size.w, height: size.h, treeWidth: size.tree || 160, theme: "light", glass: true,
    tools: size.tree !== 0, measureTools: true, externalMeasurementBackend: true, explodeTool: true, selectTool: true, pinning: false,
    keymap: { shift: "shiftKey", ctrl: "ctrlKey", meta: "metaKey", alt: "altKey" } } as any);
  viewer = new Viewer(display, { target: [0, 0, 0], up: "Z" } as any, notify as any);
  viewer.render(data, { ambientIntensity: 1.0, directIntensity: 1.1, metalness: 0.3, roughness: 0.65, edgeColor: 0x707070,
    defaultOpacity: 0.5, normalLen: 0 } as any, { target: [0, 0, 0], up: "Z" } as any);
  (window as any).__mekanikViewer = viewer;   // end-to-end tests drive the clip planes and the camera
  performance.mark("model-shown");
  return { viewer, three, close: () => { try { viewer.dispose(); } catch { /* gone */ } el.innerHTML = ""; } };
}

// glass: the tree lies over the canvas (collapsible), so the canvas takes the element's whole width
/** Both versions in one scene: the older one grey and see-through, the current one as it is. */
export function compareData(old: any, cur: any): any {
  const shift = old.instances.length;
  const copy = (s: any, off: number, tag: string, color?: string, alpha?: number): any => {
    const x = { ...s, id: s.id ? s.id.replace(/^\/[^/]+/, `/Compare/${tag}`) : s.id };
    if (s.shape && typeof s.shape.ref === "number") x.shape = { ref: s.shape.ref + off };
    if (color) Object.assign(x, { color, alpha });
    if (s.parts) x.parts = s.parts.map((p: any) => copy(p, off, tag, color, alpha));
    return x;
  };
  const a = { ...copy(old.shapes, 0, "before", "#9AA6B2", 0.35), name: "before", id: "/Compare/before" };
  const b = { ...copy(cur.shapes, shift, "now"), name: "now", id: "/Compare/now" };
  return { instances: [...old.instances, ...cur.instances], shapes: { ...cur.shapes, name: "Compare", id: "/Compare", parts: [a, b] } };
}

/** Overlay buttons kept at the projection of 3D points after every frame (fit markers, note markers). */
export function pins(v: View, host: HTMLElement, items: { pos: number[]; html: string; attrs: Record<string, string>; cls: string; click: () => void }[]) {
  host.style.position = "relative";
  const layer = document.createElement("div");
  layer.className = "pin-katman";
  host.appendChild(layer);
  const els = items.map((it) => {
    const b = document.createElement("button");
    b.className = it.cls;
    b.innerHTML = it.html;
    for (const [k, val] of Object.entries(it.attrs)) b.setAttribute(k, val);
    b.addEventListener("click", (e) => { e.stopPropagation(); it.click(); });
    layer.appendChild(b);
    return { b, p: new v.three.Vector3(...it.pos) };
  });
  const place = () => {
    const cam = v.viewer.camera?.getCamera?.(), cv: HTMLCanvasElement | undefined = v.viewer.renderer?.domElement;
    if (!cam || !cv) return;
    const r = cv.getBoundingClientRect(), k = host.getBoundingClientRect();
    for (const { b, p } of els) {
      const q = p.clone().project(cam);
      b.style.display = q.z < 1 && Math.abs(q.x) <= 1 && Math.abs(q.y) <= 1 ? "flex" : "none";
      b.style.left = `${r.left - k.left + ((q.x + 1) / 2) * r.width}px`;
      b.style.top = `${r.top - k.top + ((1 - q.y) / 2) * r.height}px`;
    }
  };
  const prev = v.viewer.onAfterRender;
  v.viewer.onAfterRender = () => { prev?.(); place(); };
  requestAnimationFrame(place);
  setTimeout(place, 300);
}

export const FIT_COLOR: Record<string, string> = { pass: "#2E6B46", fail: "#B3261E", review: "#8A5A00" };
export function fitMarkers(v: View, host: HTMLElement, marks: any[], chosen: string | undefined, pick: (id: string) => void) {
  pins(v, host, marks.filter((m) => m.position).map((m) => {
    const c = FIT_COLOR[m.status] ?? "#5F6873";
    return { pos: m.position, cls: `isaret ${m.id === chosen ? "secili" : ""}`, click: () => pick(m.id), html: `<span class="nokta"></span>${h(m.id)}`,
      attrs: { "data-fit-marker": m.id, "data-state": m.status, style: `color:${c};border-color:${c}`,
               title: `${m.id} · ${name("fit_state", m.status)}${m.reasons?.length ? " · " + m.reasons.join("; ") : ""}` } };
  }));
}
