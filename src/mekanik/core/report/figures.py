# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stream figures from the model (architecture §9.2): the step's isometric view and the before–after (changed faces
in colour), drawn by the model package (`hooks.isometric_svg`, `face_signatures`, `diff_svg`) and cached by a key of the
model inputs and the drawing code (E2): the same model, e.g. of the same commit, is never drawn twice.

The before–after compares this model's face signatures with those of the model on the last stream line that names
one (its `model` ref), i.e. of the previous step on this branch (§9.2 mech.diff: face signature difference of two
commits). Without that model's signatures in the cache (pruned) there is no before–after."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

from mekanik.plugins import registry

from .. import yamlio
from ..evidence import cache
from ..i18n import lang, t
from . import stream


def model_key(root, hooks) -> str:
    """SHA-1 of the model inputs (model/, params.yaml, the packages' design files) and of the drawing code."""
    root, h = Path(root), hashlib.sha1()
    files = sorted(p for p in (root / "model").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for f in files + [root / n for n in ("params.yaml", *registry().design_files)]:
        if f.is_file():
            h.update(f.relative_to(root).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    for name in ("isometric_svg", "face_signatures", "diff_svg"):
        if hooks.has(name):
            h.update(Path(inspect.getsourcefile(getattr(hooks, name))).read_bytes())
    h.update((hooks.producer_version() if hooks.has("producer_version") else "").encode())
    return h.hexdigest()


def cached(key: str, name: str, make) -> str:
    """Text `name` of cache entry `key`, made by `make()` when missing."""
    if (path := cache.entry(key) / name).exists():
        return path.read_text(encoding="utf-8")
    yamlio.write_text(path, text := make())
    return text


def last_model(root) -> str | None:
    """Model key of the last stream line that names a model."""
    for ev in reversed(stream.read(root)):
        if key := next((r.get("hash") for r in ev.get("refs") or [] if r.get("kind") == "model"), None):
            return key
    return None


def step_figures(root, model, hooks, isometric: bool = True) -> dict:
    """{key, isometric, before_after, changed} for a step: the svgs (None when not drawn), the model key for the
    stream line and the changed faces {part: face indices}."""
    key, out = model_key(root, hooks), {"isometric": None, "before_after": None, "changed": {}}
    out["key"] = key
    if isometric and hooks.has("isometric_svg"):
        out["isometric"] = cached(key, "isometric.svg", lambda: hooks.isometric_svg(model))
    if not (hooks.has("face_signatures") and hooks.has("diff_svg")):
        return out
    cached(key, "faces.json", lambda: json.dumps(hooks.face_signatures(model)))
    if (prev := last_model(root)) and prev != key and (old := cache.root() / prev / "faces.json").is_file():
        pair = hashlib.sha1(f"{prev} {key} {lang()}".encode()).hexdigest()   # the title is catalog text
        svg, changed = json.loads(cached(pair, "before-after.json", lambda: json.dumps(hooks.diff_svg(
            model, json.loads(old.read_text(encoding="utf-8")), t("report.visual.before_after")))))
        out.update(before_after=svg if changed else None, changed=changed)
    return out
