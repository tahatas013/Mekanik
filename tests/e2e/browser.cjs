// SPDX-License-Identifier: AGPL-3.0-or-later
// The browser side of the panel's end-to-end tests: Node Playwright (panel-ui's pinned devDependency, else a global
// install) driven by pytest over stdin/stdout, one JSON line per call (tests/e2e/browser.py). No test logic here.
const path = require("path");
const { createRequire } = require("module");
let pw;
try { pw = createRequire(path.join(__dirname, "..", "..", "panel-ui", "package.json"))("playwright"); } catch { pw = require("playwright"); }

let browser = null;
const pages = {}, waits = {};
const plain = (r) => (r === undefined || (r && typeof r === "object" && !Array.isArray(r) && r.constructor?.name !== "Object") ? null : r);
const at = (name) => { if (!pages[name]) throw new Error(`no page ${name}`); return pages[name]; };
const ops = {
  async launch({ args }) { browser = await pw.chromium.launch({ args: args ?? [] }); return browser.version(); },
  async page({ name, viewport }) {
    if (pages[name]) await pages[name].context().close();
    const page = await (await browser.newContext({ viewport })).newPage();
    page.setDefaultTimeout(30000);
    page.log = [];
    page.on("console", (m) => page.log.push(`${m.type()}: ${m.text()}`));
    page.on("pageerror", (e) => page.log.push(`pageerror: ${e.message}`));
    page.on("dialog", (d) => d.dismiss());
    pages[name] = page;
    return true;
  },
  async call({ name, method, args }) { return plain(await at(name)[method](...(args ?? []))); },
  async locator({ name, sel, method, args }) { return plain(await at(name).locator(sel)[method](...(args ?? []))); },
  async input({ name, device, method, args }) { await at(name)[device][method](...(args ?? [])); return null; },
  async evaluate({ name, src, arg }) { return await at(name).evaluate(([s, a]) => (0, eval)(s)(a), [src, arg ?? null]); },
  async expect({ name, id, part, timeout }) {
    waits[id] = at(name).waitForResponse((r) => r.url().includes(part) && r.request().method() !== "GET", { timeout: timeout ?? 120000 });
    waits[id].catch(() => {});
    return true;
  },
  async response({ id }) {
    const r = await waits[id];
    delete waits[id];
    return { status: r.status(), url: r.url(), body: await r.text().catch(() => null) };   // gone if the page moved on
  },
  async screenshot({ name, path: p }) { await at(name).screenshot({ path: p, fullPage: false }); return p; },
  async png({ name }) { return (await at(name).screenshot()).toString("base64"); },
  async logs({ name }) { return at(name).log.slice(-50); },
  async cookies({ name }) { return await at(name).context().cookies(); },
  async close() { if (browser) await browser.close(); return true; },
};

const rl = require("readline").createInterface({ input: process.stdin });
let queue = Promise.resolve();
rl.on("line", (line) => {
  queue = queue.then(async () => {
    const m = JSON.parse(line);
    try { process.stdout.write(JSON.stringify({ ok: true, value: await ops[m.op](m) ?? null }) + "\n"); }
    catch (e) { process.stdout.write(JSON.stringify({ ok: false, error: String(e && e.message || e).slice(0, 4000) }) + "\n"); }
    if (m.op === "close") process.exit(0);
  });
});
