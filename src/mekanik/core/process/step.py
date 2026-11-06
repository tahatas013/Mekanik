# SPDX-License-Identifier: AGPL-3.0-or-later
"""Step (old `akis.adim`): calcs, checks, cards with figures (here the model-free ones, old kart_gorsel._metin_gorseli,
_tutarlilik_gorseli, ozet_gorseli), one commit with Step/Role/Card/Visual trailers, the model cache, a log commit."""

import hashlib
import importlib.util
import inspect
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path

from mekanik.config import load_config
from mekanik.plugins import registry

from .. import cards as cardmod, clock, yamlio
from ..cards import approval
from ..checks import runner
from ..checks.builtin import cards as cardchecks
from ..checks.result import BLOCK, summary
from ..evidence import cache, calc
from ..i18n import num, t
from ..model.work import load_work
from ..report import figures, stream
from ..store import git, log
from ..store.works import dirty
from . import Refused, refuse

RECORDS = ["work.yaml", "cards", "decisions.yaml", "approvals.yaml", "replies.yaml", "out", "records"]
CARD_VISUALS, OPEN = "records/visuals/cards", ("open", "awaiting_reply")
FIXED = ("model_note", "release", "intake_summary")   # figures made once, when the card is opened
_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
W, INK, MUTED = 440, "#1B1F24", "#5F6873"   # source: assumption — drawing frame (px) and colours, not engineering
STREAM = {"step": "step", "gate": "gate", "release": "release", "decision": "decision", "approval": "decision"}


def text_svg(title: str, rows: list[tuple[str, str]]) -> str:
    """Label–text rows on the frame of the model figures."""
    body = [f'<text x="12" y="{42 + 18 * i}" font-size="9" fill="{MUTED}">{escape(a)}</text><text x="96" y="'
            f'{42 + 18 * i}" font-size="11" fill="{INK}">{escape(str(b))[:70]}</text>' for i, (a, b) in enumerate(rows)]
    return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {40 + 18 * len(rows)}" font-family='
                      f'"Geist, sans-serif"><rect width="100%" height="100%" fill="#FAFBFC"/><text x="12" y="20" '
                      f'font-size="10" fill="{MUTED}">{escape(title)}</text>', *body, "</svg>"])


def core_figures(card: dict, model, results) -> list | None:
    """[(title, svg)] of the cards the core draws (consistency, basis changed, gate without a model); else None."""
    typ, s, v = card.get("type"), card.get("subject") or {}, lambda k: t(f"process.visual.{k}")
    if typ == "consistency":
        d = next((r.extra["consistency"] for r in results if (r.extra.get("consistency") or {}).get("name")
                  == s.get("magnitude")), None)
        return [(v("consistency"), text_svg(v("consistency_title").format(name=d["name"]), [
            (f"{x['calc']} · {x.get('method', '')}"[:14], num(x["value"], 4) + (v("base") if x is d["base"] else ""))
            for x in [d["base"], *d["diffs"]]]))] if d else []
    if typ == "basis_changed":
        rows = [(v("decision"), s.get("decision", ""))] + [(v(k), a) for k in ("changed", "superseded")
                                                            for a in s.get(k) or []]
        return [(v("basis"), text_svg(v("basis_title"), rows))]
    if typ == "gate" and not model:
        m = (card.get("values") or {}).get("summary") or {}
        rows = [(v("work"), f"{m.get('title', '')} · {m.get('risk_class', '')}")] + [
            (v("requirement"), x) for x in m.get("requirements") or [v("none")]] + [
            (v("check"), ("✓ " if c["result"] == "pass" else "✗ ") + c.get("message", "")) for c in card.get(
                "checks") or []]
        return [(v("summary"), text_svg(v("summary_title"), rows + [(v("model"), v("no_model"))]))]
    return None


def used_cards(root) -> tuple[str, ...]:
    """Card ids in the commit trailers of every branch: an id is never given again (handbook §8)."""
    bodies = git.git("log", "--all", "--format=%B%x1e", cwd=root).split("\x1e")
    return tuple(sorted({c for b in bodies for c in git.trailers(b).get("Card", [])}))


def evaluate(root, view=None) -> tuple:
    """(view, model, results, cards) of the working tree; nothing is written."""
    view = view or load_work(root)
    model = (hooks := registry().model_hooks()) and hooks.build(view)
    results = runner.run(view, model)
    return view, model, results, cardmod.generate(view, results, used_cards(root))


def _figures(view, card, model, results, hooks, base: list) -> tuple:
    """Core figures, else the model hooks' (cached by design inputs, drawing code and card content)."""
    from ..decisions import option_values

    if (figs := core_figures(card, model, results)) is not None or not hooks:
        return figs or [], []
    dec = next((d for d in view.decisions if d.get("id") == (card.get("subject") or {}).get("decision")), None)
    args = (option_values(view, dec) if dec else None, base[-1])
    key = json.dumps([base, args, [card.get(k) for k in ("type", "subject", "options", "visual_selection")]],
                     sort_keys=True, default=str)
    if (path := cache.entry(hashlib.sha1(key.encode()).hexdigest()) / "card-visuals.json").exists():
        return tuple(json.loads(path.read_text(encoding="utf-8")))
    got = hooks.card_visuals(view, card, model, *args) or ([], [])
    yamlio.write_text(path, json.dumps([[list(f) for f in got[0]], list(got[1])], ensure_ascii=False))
    return got


def _attach(view, model, cards: list[dict], results, txn) -> dict[str, str]:
    """Figures of the open cards → records/visuals/cards/<id>[-n|-<option>].svg; → drawing errors by card."""
    hooks, errors = registry().model_hooks(), {}
    base = [approval.design_hash(view.root), *([hooks.producer_version(), hashlib.sha1(Path(inspect.getsourcefile(
        hooks.card_visuals)).read_bytes()).hexdigest()] if hooks else []), calc.param_users(view.root)]
    for c in (c for c in cards if c.get("status") in OPEN and c.get("type") not in FIXED):
        try:
            figs, untraced = _figures(view, c, model, results, hooks, base)
        except Exception as e:   # noqa: BLE001 — any drawing error
            figs, untraced, errors[c["id"]] = [], [], f"{type(e).__name__}: {e}"[:300]
        c.pop("untraced", None)
        c.update({"untraced": list(untraced)} if untraced else {})
        opts, c["visuals"] = {o["id"]: o for o in c.get("options") or []}, []
        for o in opts.values():
            o.pop("visual", None)
        for i, (title, svg) in enumerate(figs):
            rel = f"{CARD_VISUALS}/{c['id']}{f'-{title}' if title in opts else f'-{i + 1}' if i else ''}.svg"
            if not (view.root / rel).exists() or (view.root / rel).read_text(encoding="utf-8") != svg:
                txn.write_text(view.root / rel, svg)
            c["visuals"].append({"kind": "model_view", "path": rel, "id": t("process.visual.option", id=title)
                                 if title in opts else title})
            opts.get(title, {})["visual"] = c["visuals"][-1]
    return errors


def step(root, title: str, role: str, text: str = "", cards=(), visuals=(), *, kind: str = "step",
         paths: list[str] | None = None, isometric: bool = True, chief: bool = False, check_cards: bool = True,
         trailers: dict | None = None, txn: yamlio.Txn | None = None, next_step: str | None = None) -> dict:
    """`mekanik step`; `paths` limits the commit (system steps: RECORDS), `txn` holds the caller's writes to undo;
    `next_step` is the panel's next job in work.yaml (old adim --sonraki)."""
    root, txn, hooks = Path(root), txn or yamlio.Txn(), registry().model_hooks()
    try:
        refuse((branch := git.branch(root)).endswith("/main"), "process.step.on_main", branch=branch)
        stream.check(root)   # E5: a rewritten records/events.jsonl is not committed
        if role == "chief_engineer" and not chief:
            raise PermissionError(t("process.step.chief_role"))
        if next_step is not None:
            txn.write(root / "work.yaml", yamlio.read(root / "work.yaml") | {"next_step": {
                "text": next_step, "at": clock.now(), "role": role}})
        view = load_work(root)
        model = hooks.build(view) if hooks else None
        calc.write(view, recs := calc.run(view, model))
        made = cardmod.generate(view, results := runner.run(view, model), used_cards(root))
        errors = _attach(view, model, made, results, txn)
        if bad := [r for r in cardchecks.standard(view, model, made, opened_only=False) + cardchecks.effects(
                view, model, made) if r.status == BLOCK] if check_cards else []:
            raise Refused("process.step.card_standard", results=bad, items="; ".join(
                f"{r.ref}: {', '.join(r.extra.get('missing') or ['requirement_effects'])}"
                + (f" ({errors[r.ref]})" if r.ref in errors else "") for r in bad))
        ids, vis = list(dict.fromkeys([*cards, *cardmod.sync(view, made, txn)])), list(visuals)
        figs, event = figures.step_figures(root, model, hooks, isometric) if model else {}, {}
        slug = re.sub(r"[^a-z0-9]+", "-", title.translate(_ASCII).lower()).strip("-")[:40] or "step"
        stem = f"records/visuals/{datetime.fromisoformat(clock.now()):%Y%m%d-%H%M%S}-{slug}"
        for name, end in (("isometric", ""), ("before_after", "-before-after")):   # cached by model (E2, E3)
            if figs.get(name) and len(vis) < log.MAX_VISUALS:
                txn.write_text(root / (path := f"{stem}{end}.svg"), figs[name])
                vis.append(path)
                event.update({"visuals": [path]} if name == "before_after" else {})
        event.update({"refs": [{"kind": "model", "id": "model", "hash": figs["key"]}]} if figs else {})
        notes = [x for x in (text.strip(), model and hooks.summary(model), recs and t(
            "process.step.calcs", n=len(recs), failed=", ".join(r["title"] for r in recs if r.get("error")) or "—"))
                 if x]
        sha = git.commit(root, git.message(title, title, role, ids, vis, trailers), [
            *([str(root)] if paths is None else [str(root / p) for p in paths if (root / p).exists()]),
            *(str(p) for p in txn.paths if p.exists()), *(str(root / v) for v in visuals)], _who(chief),
            allow_empty=True)
    except BaseException:
        txn.rollback()
        raise
    if not dirty(root):   # the cache holds this commit's model only when the tree is that commit
        yamlio.write_text(cache.entry(sha) / "check.json", json.dumps(
            {"summary": summary(results), "results": [r.as_dict() for r in results]}, ensure_ascii=False, default=str))
        if model and hooks.has("write_cache"):
            hooks.write_cache(model, cache.entry(hooks.signature(root, sha)))
    cache.prune(keep=sha)
    ev = log_commit(root, view.code, role, kind, title, "\n\n".join(notes), vis, summary(results), ids, sha, chief,
                    event)
    if importlib.util.find_spec("mekanik.agent"):   # the agent layer is optional for the core
        importlib.import_module("mekanik.agent.pulse").touch(view.code, title, role)
    return {"commit": sha, "summary": summary(results), "cards": ids, "visuals": vis, "results": results, "event": ev}


def _who(chief: bool) -> tuple[str, str]:
    return load_config().chief if chief else load_config().team


def log_commit(root, code: str, role: str, kind: str, title: str, text: str = "", visuals=(), checks=None, cards=(),
               sha: str | None = None, chief: bool = False, event: dict | None = None) -> dict:
    """The log entry of a commit and its stream line (E1; `event`: more fields), committed on their own (the panel
    folds these); → the stream event."""
    path = log.write(root, code, role, kind, title, text, visuals, checks, cards, sha := sha or git.head(root),
                     git.branch(root))
    ev = stream.emit(root, STREAM.get(kind, "notice"), role=role, line=title, commit=sha, cards=list(cards),
                     check_summary=checks, **{"visuals": list(visuals)[:1], **(event or {})})
    git.commit(root, git.message(t("process.step.log_title", title=title), None, role, extra={
        "Log": f"{log.FOLDER}/{path.name}"}), [str(path), str(Path(root) / stream.FILE)], _who(chief))
    return ev


def commit_logged(root, code: str, role: str, kind: str, title: str, text: str, paths: list[str], cards=(),
                  chief: bool = False, sign: bool = False) -> str:
    """A system commit of `paths` (the chief's, signed when `sign`) and its log entry."""
    sha = git.commit(root, git.message(title, f"{title}: {text}" if text else title, role, list(cards)), paths,
                     _who(chief), sign=sign)
    log_commit(root, code, role, kind, title, text, cards=cards, sha=sha, chief=chief)
    return sha
