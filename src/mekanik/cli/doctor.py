# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik doctor` (old `ortam.py`; architecture §13.1, §13.2 step 7): tools and versions, identities and the
per-use confirmed approval signature (T-17 (b)), disk and model cache, packages, a model smoke test.

Statuses: ok · pending (not required now) · warn (works but needs care; the result stays green) · error (something
required is missing or broken; the result is red and the exit code 1)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple
from pathlib import Path

from mekanik.core.i18n import has, t

Finding = namedtuple("Finding", "group name status detail")
PYTHON = (3, 12)          # source: pyproject.toml requires-python ">=3.12,<3.13" (old ortam.PYTHON_SURUM)
CLAUDE_MIN = (2, 1)       # source: assumption — the plugin was validated and loaded with Claude Code 2.1 (wave 2 · E)
MIN_FREE = 10 * 1024**3   # source: decision — chief engineer, 2026-10-26 (pre-K1 addition 3; old BOS_ALAN_ALT_SINIR)
OPTIONAL = (("tmux", "-V"), ("freecad", "--version"), ("orca-slicer", "--help"))   # suggested, never installed (§13.1)
CUBE, NOISE = 10.0, 1e-6  # source: assumption — old duman_testi: 10 mm cube; floating-point noise of its volume
SMOKE = "def parts(p):\n    import cadquery as cq\n    return {'cube': cq.Workplane().box(p.a, p.a, p.a)}\n"
COLOR = {"ok": "\033[32m", "pending": "\033[33m", "warn": "\033[33m", "error": "\033[31m"}
GB = 1024**3


def _run(*cmd: str, stdin: str | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, input=stdin)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, str(e)
    return p.returncode, (p.stdout + p.stderr).strip()


def _tool(name: str, *args: str, required: bool = True) -> Finding:
    if shutil.which(name) is None:
        return Finding("tool", name, "error" if required else "pending",
                       t("cli.doctor.not_installed" if required else "cli.doctor.optional"))
    code, out = _run(name, *args)
    return Finding("tool", name, "ok" if code == 0 else "error", (out.splitlines() or [""])[0])


def tools() -> list[Finding]:
    v = sys.version_info
    out = [Finding("tool", "python", "ok" if v[:2] == PYTHON else "error", f"{v.major}.{v.minor}.{v.micro} · "
                   f"{sys.executable}"), _tool("git", "--version"), _tool("uv", "--version")]
    c = _tool("claude", "--version")
    if c.status == "ok" and not ((m := re.search(r"(\d+)\.(\d+)", c.detail)) and tuple(map(int, m.groups()))
                                 >= CLAUDE_MIN):
        c = c._replace(status="error", detail=t("cli.doctor.too_old", found=c.detail, need="%d.%d" % CLAUDE_MIN))
    return [*out, c, *(_tool(n, a, required=False) for n, a in OPTIONAL)]


def signing(key: str) -> Finding:
    """T-17 (b): the chief's SSH key sits in ssh-agent added with `ssh-add -c`; a trial signature must be refusable.
    The chief refuses the confirmation window: a signature made anyway means the agent signs unconfirmed (red). A GPG
    key is red: gpg-agent has no per-use confirmation, so an agent of the same user could sign unseen (§4.6 m.4)."""
    f = lambda st, k: Finding("identity", "signing_key", st, t(f"cli.doctor.{k}", fp=key))  # noqa: E731
    if not key.startswith("SHA256:"):
        return f("error", "gpg_key")
    if not (shutil.which("ssh-add") and shutil.which("ssh-keygen")):
        return f("warn", "unchecked")
    if key not in _run("ssh-add", "-l")[1]:
        return f("error", "not_in_agent")
    with tempfile.TemporaryDirectory() as d:
        for i, line in enumerate(_run("ssh-add", "-L")[1].splitlines()):
            (pub := Path(d) / f"{i}.pub").write_text(line + "\n", encoding="utf-8")
            if key in _run("ssh-keygen", "-lf", str(pub))[1]:
                print(t("cli.doctor.trial"), file=sys.stderr, flush=True)
                rc = _run("ssh-keygen", "-Y", "sign", "-U", "-n", "mekanik-doctor", "-f", str(pub), stdin="x")[0]
                return f("ok", "trial_refused") if rc else f("error", "trial_signed")
    return f("error", "no_pub")


def identities() -> list[Finding]:
    from mekanik.config import load_config
    from mekanik.core.errors import MekanikError

    try:
        cfg = load_config()
    except MekanikError as e:
        return [Finding("identity", "config", "error", str(e))]
    return [Finding("identity", "config", "ok", str(cfg.root)),
            Finding("identity", "chief", "ok", "{} <{}>".format(*cfg.chief)),
            Finding("identity", "team", "ok", "{} <{}>".format(*cfg.team)), signing(cfg.signing_key)]


def disk() -> list[Finding]:
    from mekanik.core.evidence import cache

    root, cap = cache.root(), cache.limit()
    free = shutil.disk_usage(next(p for p in (root, *root.parents) if p.exists())).free   # the cache's file system
    n, used = cache.status()
    return [Finding("disk", "free_space", "ok" if free >= MIN_FREE else "warn",
                    t("cli.doctor.free", free=free / GB, min=MIN_FREE / GB)),
            Finding("disk", "model_cache", "ok" if used <= cap else "warn",
                    t("cli.doctor.cache", n=n, used=used / GB, limit=cap / GB, root=root))]


def packages() -> list[Finding]:
    from mekanik.plugins import registry

    try:
        return [Finding("package", p.id, "ok", p.version) for p in registry().packages]
    except Exception as e:  # noqa: BLE001 — a package that does not load is a finding, not a crash
        return [Finding("package", "registry", "error", repr(e))]


def smoke() -> list[Finding]:
    """A cube through the model hooks: build, volume and faces, STEP export, tessellation (old duman_testi)."""
    from mekanik.plugins import registry

    try:
        if not getattr(hooks := registry().model_hooks(), "has", lambda n: False)("build_path"):
            return [Finding("smoke", "model", "pending", t("cli.doctor.no_model"))]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "model.py").write_text(SMOKE, encoding="utf-8")
            parts = hooks.build_path(Path(d) / "model.py", {"a": CUBE})
            m, size = hooks.metrics(parts)["cube"], hooks.step(parts, Path(d) / "cube.step").stat().st_size
            hooks.tessellation(parts)
    except Exception as e:  # noqa: BLE001 — any OCCT failure is the finding
        return [Finding("smoke", "model", "error", repr(e)[:300])]
    ok = abs(m["volume"] - CUBE**3) < NOISE and m["faces"] == 6 and size > 0
    return [Finding("smoke", "model", "ok" if ok else "error",
                    t("cli.doctor.smoke", volume=m["volume"], faces=m["faces"], size=size))]


def run(as_json: bool = False) -> int:
    found = tools() + identities() + disk() + packages() + smoke()
    n = {s: sum(f.status == s for f in found) for s in COLOR}
    if as_json:
        print(json.dumps([f._asdict() for f in found], ensure_ascii=False, indent=2))
        return 1 if n["error"] else 0
    tty = sys.stdout.isatty()
    for f in found:
        st = f"{t('cli.doctor.status.' + f.status):<8}"
        print(t("cli.doctor.row", status=f"{COLOR[f.status]}{st}\033[0m" if tty else st, group=t(
            f"cli.doctor.group.{f.group}"), name=t(k) if has(k := f"cli.doctor.item.{f.name}") else f.name,
                detail=f.detail))
    print(t("cli.doctor.result", verdict=t("cli.doctor.red" if n["error"] else "cli.doctor.green"), **n))
    return 1 if n["error"] else 0
