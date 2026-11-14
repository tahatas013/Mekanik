# SPDX-License-Identifier: AGPL-3.0-or-later
"""pytest's handle on the browser: a Node Playwright process (browser.cjs) answering one JSON line per call. Node
Playwright is panel-ui's pinned devDependency (`npm ci` in panel-ui; browsers by `npx playwright install chromium`);
here the container's own Chromium is used. Pages are named so a test can hold two (e.g. one without the session)."""

from __future__ import annotations

import contextlib
import itertools
import json
import shutil
import subprocess
from pathlib import Path

BRIDGE = Path(__file__).with_name("browser.cjs")
GL = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]   # WebGL without a GPU


class BrowserError(AssertionError):
    pass


class Browser:
    def __init__(self):
        if not shutil.which("node"):
            raise FileNotFoundError("node")
        self.p = subprocess.Popen(["node", str(BRIDGE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                  bufsize=1)
        self.ids = itertools.count()
        self.version = self.call("launch", args=GL)

    def call(self, op: str, **kw):
        self.p.stdin.write(json.dumps({"op": op, **kw}) + "\n")
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise BrowserError(f"browser bridge ended ({op})")
        r = json.loads(line)
        if not r["ok"]:
            raise BrowserError(f"{op} {kw}: {r['error']}")
        return r["value"]

    def page(self, name: str = "main", width: int = 1440, height: int = 900) -> "Page":
        self.call("page", name=name, viewport={"width": width, "height": height})
        return Page(self, name)

    def close(self):
        with contextlib.suppress(Exception):
            self.call("close")
        self.p.wait(10)


class Page:
    def __init__(self, b: Browser, name: str):
        self.b, self.name = b, name

    def _c(self, method, *args):
        return self.b.call("call", name=self.name, method=method, args=list(args))

    def _l(self, sel, method, *args):
        return self.b.call("locator", name=self.name, sel=sel, method=method, args=list(args))

    def url(self) -> str:
        return self._c("url")

    def reload(self):
        self._c("reload")
        self._c("waitForLoadState", "networkidle")

    def goto(self, url: str):
        self._c("goto", url)
        self._c("waitForLoadState", "networkidle")

    def wait(self, sel: str, timeout: int = 30000, state: str = "visible"):
        self._c("waitForSelector", sel, {"timeout": timeout, "state": state})

    def shown(self, screen: str, timeout: int = 30000):
        """The router finished drawing `screen` (main[data-shown])."""
        self.wait(f"main #main[data-shown='{screen}']", timeout, "attached")

    def click(self, sel: str):
        self._c("click", sel)

    def fill(self, sel: str, text: str):
        self._c("fill", sel, text)

    def text(self, sel: str) -> str:
        return self._c("innerText", sel)

    def attr(self, sel: str, name: str):
        return self._c("getAttribute", sel, name)

    def count(self, sel: str) -> int:
        return self._l(sel, "count")

    def visible(self, sel: str) -> bool:
        return self._c("isVisible", sel)

    def box(self, sel: str) -> dict:
        return self._l(sel, "boundingBox")

    def eval(self, src: str, arg=None):
        """`src` is a JavaScript function source, called in the page with `arg`."""
        return self.b.call("evaluate", name=self.name, src=src, arg=arg)

    def mouse(self, method: str, *args):
        self.b.call("input", name=self.name, device="mouse", method=method, args=list(args))

    def keyboard(self, method: str, *args):
        self.b.call("input", name=self.name, device="keyboard", method=method, args=list(args))

    @contextlib.contextmanager
    def response(self, part: str, timeout: int = 120000):
        """The first non-GET response whose URL contains `part`, after the block's action → {status, url, body}."""
        rid, got = f"r{next(self.b.ids)}", {}
        self.b.call("expect", name=self.name, id=rid, part=part, timeout=timeout)
        yield got
        got.update(self.b.call("response", id=rid))

    def png(self) -> bytes:
        import base64

        return base64.b64decode(self.b.call("png", name=self.name))

    def screenshot(self, path) -> None:
        self.b.call("screenshot", name=self.name, path=str(path))

    def logs(self) -> list[str]:
        return self.b.call("logs", name=self.name)
