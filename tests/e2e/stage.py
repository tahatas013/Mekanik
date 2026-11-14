# SPDX-License-Identifier: AGPL-3.0-or-later
"""Staging of the panel's end-to-end tests (old test_panel_e2e HAZIRLA): the works they use, and the panel on a real
port in this process (restartable: the session tab's resume test stops and starts it). `python tests/e2e/stage.py`
opens a demo panel on these works in a temporary workshop, for looking at the screens by hand."""

from __future__ import annotations

import shutil
import socket
import threading
import time
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.process import gates
from mekanik.core.process.step import step
from mekanik.core.store import git

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "panel-ui" / "dist" / "index.html"
MODEL = '''import cadquery as cq


def parts(p):
    a = cq.Workplane().box(p.blok, p.blok, p.kalinlik).faces(">Z").workplane().hole(p.delik_cap).val()
    b = cq.Workplane().circle(p.mil_cap / 2).extrude(p.pim_boy).translate((0, 0, -p.pim_boy / 2)).val()
    return {"A": a, "B": b}
'''
PARAMS = {"delik_cap": {"value": 10.0, "unit": "mm", "source": "decision"},
          "g01_bosluk": {"value": 0.3, "unit": "mm", "source": "decision"},
          "mil_cap": {"value": None, "unit": "mm", "source": "derived", "formula": "delik_cap - g01_bosluk"},
          "blok": {"value": 30.0, "unit": "mm", "source": "decision"},
          "kalinlik": {"value": 10.0, "unit": "mm", "source": "decision"},
          "pim_boy": {"value": 20.0, "unit": "mm", "source": "decision"},
          "blok_en": {"value": 30.0, "unit": "mm", "source": "decision"}}
FITS = {"fits": [{"id": "G-01", "parts": ["A", "B"], "task": "centering", "nominal": "delik_cap",
                  "clearance": "g01_bosluk"}], "flexes": []}
CALC = '''ID = "alan"
TITLE = "Blok alanı"
PURPOSE = "sınama"


def calculate(h, model):
    b = h.input("blok")
    a = h.step("Alan", "A = b²", b * b, "mm2", "derived")
    h.result("alan", a, "mm2")
    h.chart("Alan – kenar", [1, 2, 3], [1, 4, 9], "kenar", "alan")
'''


def pinned(new, prepare, review, title: str = "Panel sınaması", params: dict | None = None) -> tuple[str, Path]:
    """A block with a hole and a pin through it (the old e2e work), stepped and its G0 gate requested."""
    code, d = new(title=title)
    prepare(d, params=params or PARAMS, model=MODEL)
    yamlio.write(d / "fits.yaml", FITS)
    step(d, "hazırlık: blok ve pim", "design_engineer")
    review(d)
    gates.stage_finish(d, "G0")
    return code, d


def rich(new, prepare, review) -> tuple[str, Path]:
    """The pinned work with an assumed value (V-01), a calculation and a decision of two options (K-01)."""
    from mekanik.core.decisions import open_decision

    params = {**PARAMS, "pim_boy": {"value": 20.0, "unit": "mm", "source": "assumption", "description": "Pimin boyu.",
                                    "rationale": "Bloktan iki yana taşsın, elle tutulsun."}}
    code, d = pinned(new, prepare, review, "Karar sınaması", params)
    (d / "calcs").mkdir(exist_ok=True)
    (d / "calcs" / "alan.py").write_text(CALC)
    step(d, "hesap eklendi", "design_engineer", "Ne yaptı: blok alanı hesabı")
    open_decision(d, "K-01", "Boşluk", {"a": {"title": "0,2 mm", "values": {"g01_bosluk": 0.2}, "pros": ["daha az boşluk"],
                                               "cons": ["sıkışabilir"]},
                                         "b": {"title": "0,4 mm", "values": {"g01_bosluk": 0.4}, "pros": ["rahat takılır"],
                                               "cons": ["boşluk"]}},
                  "sınama", branched=False, question="Pim boşluğu ne olsun?", explain="Sınama kararı.", proposal="a",
                  proposal_rationale="Ortalama geçmenin alt sınırına yakın.",
                  requirement_effects=[{"requirement": "R-01", "effect": "değişmez"}])
    return code, d


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Panel:
    """The panel (create_app with its watcher) on 127.0.0.1:<port> in a thread; stop() ends it as a restart would."""

    def __init__(self, port: int | None = None):
        self.port = port or free_port()
        self.url, self.server, self.thread = f"http://127.0.0.1:{self.port}", None, None

    def start(self) -> "Panel":
        import uvicorn

        from mekanik.panel.app import create_app

        self.server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=self.port, log_level="warning",
                                                    timeout_graceful_shutdown=1))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(250):
            if self.server.started:
                return self
            time.sleep(0.02)
        raise RuntimeError("panel did not start")

    def stop(self) -> None:
        """A graceful stop, as Ctrl-C on `mekanik panel`: open streams are cut after 1 s, then the app's shutdown runs
        (its terminals end)."""
        self.server.should_exit = True
        self.thread.join(15)

    def login(self) -> str:
        from mekanik.panel import auth

        return f"{self.url}/login?token={auth.secret()}"


def g0_passed(d: Path) -> None:
    """G0 approved (as the chief would at the terminal) unless a test already did it from the panel."""
    from mekanik.core.process import chief

    code = yamlio.read(d / "work.yaml")["code"]
    if f"{code}-G0" not in git.git("tag", "--list", cwd=d).split():
        chief.approve(d, "O-G0")


if __name__ == "__main__":   # a demo panel on the staged works (temporary workshop; Ctrl-C ends it)
    import os
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, str(ROOT / "tests" / "core"))
    tmp = Path(tempfile.mkdtemp(prefix="mekanik-demo-"))
    home = tmp / "gnupg"
    home.mkdir(mode=0o700)
    env = {**os.environ, "GNUPGHOME": str(home)}
    subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key",
                    "Test Mühendis <test@example.org>", "ed25519", "sign", "never"], env=env, check=True, capture_output=True)
    out = subprocess.run(["gpg", "--with-colons", "--list-secret-keys", "test@example.org"], env=env, check=True,
                         capture_output=True, text=True).stdout
    from conftest import workshop   # noqa: E402 — the tests' own workshop

    workshop(tmp, os.environ.__setitem__, next(x.split(":")[9] for x in out.splitlines() if x.startswith("fpr:")), home)
    from test_store import new, prepare, review  # noqa: E402

    pinned(new, prepare, review)
    rich(new, prepare, review)
    p = Panel(int(sys.argv[1]) if len(sys.argv) > 1 else 8765).start()
    print(p.login(), flush=True)
    try:
        p.thread.join()
    except KeyboardInterrupt:
        p.stop()
    shutil.rmtree(tmp, ignore_errors=True)
