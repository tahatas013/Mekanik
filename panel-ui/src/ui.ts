// Shared pieces: the notice (toast), the confirmation window (Ö-14: a hold, decision, gate or release card and every
// undo go through it; it also asks a reason or a name where one is needed), copy buttons and the mascot "Top".
import { ApiError } from "./api";
import { h, u } from "./util";

export function toast(html: string, kind = "info", action?: { text: string; run: () => void }) {
  document.querySelector(`.bildirim[data-toast="${kind}"]`)?.remove();
  const b = document.createElement("div");
  b.className = "bildirim";
  b.dataset.toast = kind;
  b.innerHTML = `<span>${html}</span>${action ? `<button data-toast-act>${h(action.text)}</button>` : ""}`
    + `<button class="kapat" aria-label="${h(u("close"))}">✕</button>`;
  b.querySelector("[data-toast-act]")?.addEventListener("click", () => { b.remove(); action!.run(); });
  b.querySelector(".kapat")!.addEventListener("click", () => b.remove());
  document.body.appendChild(b);
}
export const fail = (e: unknown) =>
  toast(`<span class="hata" data-error="${h(e instanceof ApiError ? e.key : "error")}">${h((e as Error).message ?? e)}</span>`, "error");

export interface Ask { title: string; text: string; yes: string; field?: { label: string; value?: string; required?: boolean } }

/** The confirmation window; resolves to the typed value ("" without a field) or null when cancelled. */
export function confirm(a: Ask): Promise<string | null> {
  return new Promise((done) => {
    const dl = document.createElement("dialog");
    dl.className = "teyit";
    dl.dataset.confirm = "";
    dl.innerHTML = `<h2>${h(a.title)}</h2><p>${h(a.text)}</p>${a.field ? `<label class="alan-etiket">${h(a.field.label)}
      <textarea rows="2" data-field>${h(a.field.value ?? "")}</textarea></label>` : ""}
      <div class="dugme-sira sag"><button class="dugme" data-answer="no">${h(u("cancel"))}</button>
      <button class="dugme birincil" data-answer="yes">${h(a.yes)}</button></div>`;
    document.body.appendChild(dl);
    const end = (v: string | null) => { dl.close(); dl.remove(); done(v); };
    const field = dl.querySelector<HTMLTextAreaElement>("[data-field]");
    dl.querySelector("[data-answer=no]")!.addEventListener("click", () => end(null));
    dl.querySelector("[data-answer=yes]")!.addEventListener("click", () => {
      if (field && a.field!.required && !field.value.trim()) return field.focus();
      end(field ? field.value.trim() : "");
    });
    dl.addEventListener("cancel", () => end(null));
    dl.showModal();
  });
}

export const copyButton = (text: string) =>
  `<button class="kopyala" data-copy="${h(text)}" title="${h(u("copy"))}" aria-label="${h(u("copy"))}">⧉</button>`;
document.addEventListener("click", (e) => {
  const b = (e.target as HTMLElement).closest<HTMLElement>("[data-copy]");
  if (b) navigator.clipboard?.writeText(b.dataset.copy!).then(() => toast(h(u("copied")), "copy"), () => {});
});

const MASCOT: Record<string, [string, string]> = {   // [body, dark]
  working: ["#3E9B63", "#2E6B46"], quiet: ["#E0A63A", "#8A5A00"], waiting: ["#E0A63A", "#8A5A00"], stopped: ["#AEB6BF", "#5F6873"],
};
/** "Top": who has the ball. Jumps while the team works, looks at you when it waits, looks around when silent, sleeps. */
export function mascot(st: string, px = 22): string {
  const [b, d] = MASCOT[st] ?? MASCOT.stopped;
  const eye = (x: number, y: number, dx = 0) => `<circle cx="${x}" cy="${y}" r="3.2" fill="#fff"/><circle class="goz" cx="${x + dx}" cy="${y}" r="1.6" fill="#1B1F24"/>`;
  const eyes = st === "stopped" ? `<path d="M12 21q3 2.5 6 0M22 21q3 2.5 6 0" fill="none" stroke="${d}" stroke-width="1.8"/>`
    : eye(15, st === "waiting" ? 17 : 19, st === "quiet" ? 1.4 : 1) + eye(25, st === "waiting" ? 17 : 19, st === "quiet" ? 1.4 : 1);
  const extra = st === "stopped" ? `<text class="z" x="31" y="9" font-size="8" font-weight="700" fill="${d}">z</text>`
    : st === "waiting" ? `<text x="33" y="10" font-size="11" font-weight="800" fill="#B3261E">!</text>`
    : st === "quiet" ? `<text x="32" y="10" font-size="10" font-weight="800" fill="${d}">?</text>` : "";
  return `<svg class="maskot maskot-${h(st)}" width="${px}" height="${px * 1.1}" viewBox="0 -2 40 44" role="img"
    aria-label="${h(u(`live.${st}`))}"><ellipse cx="20" cy="40" rx="11" ry="2" fill="#1B1F24" opacity=".12"/>
    <g class="govde-m"><circle cx="20" cy="21" r="15" fill="${b}" stroke="${d}" stroke-width="1.4"/>${eyes}</g>${extra}</svg>`;
}
