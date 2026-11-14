// The panel's REST contract (docs/dev/panel-api.md). Writes carry the CSRF token and JSON; a refusal is
// {"error": {key, text, data}} and is thrown as ApiError (the page shows `text`, tests read `key`).
let csrf = "";
export const setCsrf = (c: string) => { csrf = c; };

export class ApiError extends Error {
  constructor(public status: number, public key: string, text: string, public data: any = {}) { super(text); }
}

const qs = (q: Record<string, string | undefined | null> = {}) => {
  const s = new URLSearchParams(Object.entries(q).filter(([, v]) => v) as [string, string][]).toString();
  return s ? `?${s}` : "";
};

async function req<T = any>(method: string, path: string, body?: unknown, raw?: Blob): Promise<T> {
  const headers: Record<string, string> = method === "GET" ? {} : {
    "X-CSRF-Token": csrf, "Content-Type": raw ? "application/octet-stream" : "application/json" };
  const r = await fetch(path, { method, headers, body: raw ?? (method === "GET" ? undefined : JSON.stringify(body ?? {})) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) {
    const e = j.error ?? { key: "panel.error", text: j.detail ? JSON.stringify(j.detail) : `${r.status}` };
    throw new ApiError(r.status, e.key, e.text, e.data);
  }
  return j as T;
}

export const get = <T = any>(path: string, q?: Record<string, string | undefined | null>) => req<T>("GET", path + qs(q));
export const post = <T = any>(path: string, body: unknown = {}) => req<T>("POST", path, body);
export const put = (path: string, file: Blob) => req("PUT", path, undefined, file);
export const W = (code: string) => `/api/works/${encodeURIComponent(code)}`;
export const fileUrl = (code: string, kind: "download" | "images", path: string, q?: Record<string, string | undefined>) =>
  `${W(code)}/${kind}/${path.split("/").map(encodeURIComponent).join("/")}${qs(q)}`;
