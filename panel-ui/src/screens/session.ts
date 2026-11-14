// The session tab (A13, T-18a): the user's own interactive Claude Code in a terminal inside the panel (xterm.js over
// the WebSocket W/pty, a PTY under the panel). Started or continued (--resume) here, it ends with the panel; only
// what is typed here reaches it — the instruction box writes to the inbox, never to this terminal.
import type { Ctx } from "../main";
import { S } from "../main";
import { h, u } from "../util";

let ws: WebSocket | null = null;
let term: any = null;

export async function sessionScreen(c: Ctx) {
  ws?.close();
  term?.dispose();
  c.main.innerHTML = `<div class="sayfa-bas"><div><h1>${h(u("nav.session"))}</h1><p>${h(u("pty.lead"))}</p></div>
    <div class="sag" data-pty-buttons></div></div><div class="bilgi-kutu">${h(u("pty.note"))}</div>
    <div class="terminal-kap" data-terminal><div class="bos">${h(u("pty.connecting"))}</div></div><div class="kucuk ikincil" data-pty-state></div>`;
  c.side.innerHTML = `<div class="panel-baslik">${h(u("nav.session"))}</div><div class="panel-govde"><div class="ipucu">${h(u("pty.side"))}</div></div>`;
  const [{ Terminal }, { FitAddon }] = await Promise.all([import("@xterm/xterm"), import("@xterm/addon-fit"), import("@xterm/xterm/css/xterm.css")]);
  const box = c.main.querySelector<HTMLElement>("[data-terminal]")!, btns = c.main.querySelector<HTMLElement>("[data-pty-buttons]")!;
  const say = (k: string, d?: Record<string, unknown>) => { const e = c.main.querySelector("[data-pty-state]"); if (e) e.textContent = u(k, d); };
  const sock = ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/works/${encodeURIComponent(c.code)}/pty`);
  sock.binaryType = "arraybuffer";
  const fit = new FitAddon();
  const start = (mode: string) => {
    box.innerHTML = "";
    term = new Terminal({ fontFamily: "Geist Mono, ui-monospace, monospace", fontSize: 13, convertEol: false, cursorBlink: true, theme: { background: "#1B1F24" } });
    term.loadAddon(fit);
    term.open(box);
    fit.fit();
    term.onData((d: string) => sock.readyState === WebSocket.OPEN && sock.send(JSON.stringify({ type: "input", data: d })));
    term.onResize(({ cols, rows }: any) => sock.readyState === WebSocket.OPEN && sock.send(JSON.stringify({ type: "resize", cols, rows })));
    sock.send(JSON.stringify({ type: "start", mode, cols: term.cols, rows: term.rows }));
    term.focus();
  };
  const offer = (known: string | null) => {
    btns.innerHTML = `${known ? `<button class="dugme birincil" data-pty="resume">${h(u("pty.resume"))}</button>` : ""}
      <button class="dugme ${known ? "" : "birincil"}" data-pty="new">${h(u("pty.new"))}</button>`;
    btns.querySelectorAll<HTMLElement>("[data-pty]").forEach((b) => b.addEventListener("click", () => start(b.dataset.pty!)));
    box.innerHTML = `<div class="bos">${h(u(known ? "pty.can_resume" : "pty.can_start"))}</div>`;
  };
  sock.onmessage = (m) => {
    if (typeof m.data !== "string") return term?.write(new Uint8Array(m.data));
    const x = JSON.parse(m.data);
    if (x.error) { box.innerHTML = `<div class="hata-kutu" data-error="${h(x.error.key)}">${h(x.error.text)}</div>`; return; }
    if (x.type === "ready") return x.running ? start("resume") : offer(x.session);
    if (x.type === "started") {
      box.dataset.session = x.session;
      say(x.resumed ? "pty.resumed" : "pty.started", { id: x.session.slice(0, 8) });
      btns.innerHTML = `<button class="dugme ret" data-pty-close>${h(u("pty.close"))}</button>`;
      btns.querySelector("[data-pty-close]")!.addEventListener("click", () => sock.send(JSON.stringify({ type: "close" })));
    }
    if (x.type === "exit") { say("pty.ended", { code: x.code ?? "—" }); offer(box.dataset.session ?? null); }
  };
  sock.onclose = (e) => { if (S.screen === "session" && ws === sock) say(e.code === 4401 ? "pty.denied" : "pty.closed"); };
  const onResize = () => term && fit.fit();
  window.addEventListener("resize", onResize);
  S.leave = () => { window.removeEventListener("resize", onResize); sock.close(); term?.dispose(); term = null; };
}
