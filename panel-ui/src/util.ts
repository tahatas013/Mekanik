// Small helpers: catalog text (GET /api/catalog; every visible text is a key), safe HTML, numbers, times from the
// system clock (the browser's), role badges, state chips.
let CAT: Record<string, string> = {};
export const setCatalog = (c: Record<string, string>) => { CAT = c; };
/** This browser's own memory (language, column widths); a private window may refuse it: then nothing is kept. */
export const store = {
  get: (k: string) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k: string, v: string | null) => { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* not kept */ } },
};
export const lang = () => store.get("mekanik.lang") || CAT["panel.ui.lang"] || "tr";

export function t(key: string, d: Record<string, unknown> = {}): string {
  return (CAT[key] ?? key).replace(/\{(\w+)\}/g, (m, k) => (k in d ? String(d[k] ?? "—") : m));
}
export const u = (k: string, d?: Record<string, unknown>) => t("panel.ui." + k, d);
/** A record's own text in the UI language ({tr, en} or a plain string; recorded text is never translated). */
export const own = (x: any): string => (x && typeof x === "object" ? x[lang()] ?? x.tr ?? Object.values(x)[0] : x) ?? "";
/** Catalog text of an enumerated value; the value itself when the catalog has no entry. */
export const name = (group: string, v: unknown) => {
  const k = `panel.ui.${group}.${String(v ?? "").replace(/[:.]/g, "_")}`;
  return k in CAT ? t(k) : String(v ?? "—");
};
export const h = (s: unknown): string =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

export function num(x: unknown, digits = 3): string {
  if (typeof x !== "number" || Number.isNaN(x)) return x === null || x === undefined ? "—" : h(x);
  let s = x.toFixed(digits).replace(/0+$/, "");
  if (s.endsWith(".")) s += "0";
  return s.replace(".", CAT["num.decimal"] ?? ",");
}
const loc = () => u("locale");
const date = (iso?: string | null) => (iso ? new Date(iso) : null);
export const clock = (iso?: string | null) => date(iso)?.toLocaleTimeString(loc(), { hour: "2-digit", minute: "2-digit" }) ?? "";
export const when = (iso?: string | null) =>
  iso ? `${date(iso)!.toLocaleDateString(loc(), { day: "2-digit", month: "2-digit" })} · ${clock(iso)}` : "";
export const day = (iso: string) => date(iso)!.toLocaleDateString(loc(), { day: "numeric", month: "long", weekday: "long" });
export const sha = (s?: string | null) => h((s ?? "").slice(0, 7));
export const size = (b: number) => (b < 1024 ? `${b} B` : b < 2 ** 20 ? `${num(b / 1024, 1)} KB` : `${num(b / 2 ** 20, 1)} MB`);

export const role = (r?: string | null) =>
  `<span class="rol r-${h(r ?? "x")}" title="${h(name("role", r))}">${h(name("role_short", r))}</span>`;
export const chip = (cls: string, text: string, attr = "") => `<span class="cip ${cls}" ${attr}>${h(text)}</span>`;
export const STATUS_CLS: Record<string, string> = {
  open: "bekliyor", awaiting_reply: "bekliyor", approved: "ok", rejected: "engel", closed: "gri", superseded: "gri",
  withdrawn: "gri", block: "engel", warn: "uyari", pass: "ok", met: "ok", not_met: "engel", awaiting_evidence: "bekliyor",
};
export const state = (s: string) => chip(STATUS_CLS[s] ?? "gri", name("status", s), `data-status="${h(s)}"`);
export function summary(s?: { block?: number; warn?: number } | null): string {
  if (!s) return `<span class="soluk">—</span>`;
  return s.block ? chip("engel", `${t("status.block")} ${s.block}`) : s.warn ? chip("uyari", `${t("status.warn")} ${s.warn}`)
    : chip("ok", `✓ ${t("status.pass")}`);
}
export const box = (cls: string, html: string) => `<div class="${cls}">${html}</div>`;
export const empty = (k: string) => box("bilgi-kutu", h(u(k)));
