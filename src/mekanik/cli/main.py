# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik` command (old `surec` CLI; architecture §4.11). A thin layer: each subcommand calls one module function
and prints catalog text (cli.*). Subcommands come from the COMMANDS table; modules are imported when a command runs,
so the hook commands stay quick.

Argument tokens: `name` positional, `name?` optional positional, `--name` option, `--name!` required, `--name*`
repeatable, `--name+` flag, `=a|b` choices (default: the first). Help text: cli.help.<command>, cli.arg.<dest>."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import tempfile
from pathlib import Path

from mekanik.core.errors import GitError, MekanikError
from mekanik.core.i18n import has, t

ROLES = "project_engineer|design_engineer|technician|quality_engineer"
TOKEN = re.compile(r"(--)?([\w-]+)([!*+?]?)(?:=(.+))?")


def _m(name: str):
    return importlib.import_module(f"mekanik.{name}")


def say(key: str, **kw) -> None:
    print(t(key, **kw))


def _json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _root(a) -> Path:
    """The work folder: --work (code or folder), else the work at or above the current folder (old isler.coz)."""
    return _m("core.store.works").resolve(getattr(a, "work", None))


def _mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def regress(a):
    subs = _m("core.checks.regress").run_all()
    for case in dict.fromkeys(s.case for s in subs):
        mine = [s for s in subs if s.case == case]
        say("cli.regress.case", case=case, ok=sum(s.passed for s in mine), n=len(mine))
        for s in mine:
            say("cli.regress.sub", mark=_mark(s.passed), id=s.id, text=s.description)
            for e in s.errors:
                say("cli.regress.error", error=e)
    return 0 if all(s.passed for s in subs) else 1


def check(a):
    """Checks of the working tree; nothing is written (old kontrol wrote check.json into the cache; §4.11)."""
    view, _, results, cards = _m("core.process.step").evaluate(_root(a))
    s = _m("core.checks.result").summary(results)
    if a.json:
        _json({"work": view.code, "stage": view.stage, "summary": s, "results": [r.as_dict() for r in results],
               "cards": cards})
        return 1 if s["block"] else 0
    say("cli.check.head", code=view.code, stage=view.stage, profile=(view.doc.get("profiles") or {}).get(
        "manufacturing") or "—", **s)
    for r in sorted(results, key=lambda r: ("block", "warn", "pass").index(r.status)):
        say("cli.check.row", status=t(f"status.{r.status}"), check=r.check, ref=r.ref or "", reason=r.reason)
    op = [c for c in cards if c.get("status") == "open"]
    say("cli.check.open", n=len(op), items=", ".join(f"{c['id']} ({', '.join(c.get('triggers') or [])})" for c in op))
    return 1 if s["block"] else 0


def work_new(a):
    w = _m("core.store.works")
    code = w.new_work(a.org, a.project, a.title, vars(a)["class"], a.purpose or "", a.done or "")
    say("cli.work.new", code=code, path=w.tree(code), branch=f"{code}/work/general")


def step(a):
    s = _m("core.process.step").step(_root(a), a.title, a.role, a.text or "", a.card or [], a.visual or [],
                                     next_step=a.next)
    say("cli.step", sha=s["commit"][:7], cards=", ".join(s["cards"]) or "—", **s["summary"])


def stage_finish(a):
    s = _m("core.process.gates").stage_finish(_root(a), a.gate)
    for x in s["items"]:
        say("cli.item", mark=_mark(x["ok"]), text=x["text"])
    say("cli.stage_finish", gate=a.gate)


def approve(a, card: str | None = None):
    """The chief only, from an interactive terminal: an agent's Bash tool gives no TTY, and typing the card id makes
    the approval deliberate. Identity and signature are the process module's (architecture §4.6)."""
    card, action = card or a.card, getattr(a, "action", "approve")
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print(t("cli.approve.tty"), file=sys.stderr)
        return 4
    print(t("cli.signing_key", fp=(cfg := _m("config").load_config()).signing_key), file=sys.stderr)   # KF1-07
    if input(t("cli.approve.confirm", card=card, action=t(f"cli.action.{action}"), who=cfg.chief[0])).strip() != card:
        print(t("cli.approve.cancelled"), file=sys.stderr)
        return 4
    if action == "undo" and not (a.note or "").strip():
        print(t("cli.approve.undo_note"), file=sys.stderr)
        return 4
    chief, rows = _m("core.process.chief"), getattr(a, "row", None)
    _json(chief.undo(_root(a), card, a.note, row=(rows or [None])[0]) if action == "undo" else chief.approve(
        _root(a), card, action, a.note or "", option=getattr(a, "option", None), rows=rows))


def reply(a):
    r = _m("core.process.chief").reply(_root(a), a.card, a.text, a.comment, a.role, a.commit)
    say("cli.reply", card=r["card"], at=r["comment_at"])


def pending(a):
    """Unanswered comments of the chief; --hook: Claude Code hook output (old `bekleyenler --kanca`), silent outside a
    work, on any error and in an organization whose data may not reach the model provider."""
    try:
        root = _root(a)
        if a.hook and not _m("agent.hook").org_allowed(_m("core.yamlio").read(root / "work.yaml")["code"][:3]):
            return 0
        items = _m("core.process.chief").pending(root)
        rows = [{"card": y["card"], "at": y["at"][:16].replace("T", " "), "text": y["text"]} for y in items]
        if a.hook and rows:
            event = {} if sys.stdin.isatty() else json.loads(sys.stdin.read() or "{}")
            text = "\n".join([t("cli.pending.hook"), *(t("cli.pending.hook_row", **y) for y in rows)])
            print(json.dumps({"hookSpecificOutput": {"hookEventName": event.get("hook_event_name", "SessionStart"),
                                                     "additionalContext": text}}, ensure_ascii=False))
    except Exception:  # a hook never stops the session
        if a.hook:
            return 0
        raise
    if not a.hook:
        for y in rows:
            say("cli.pending.row", **y)
        rows or say("cli.pending.none")


def decide(a):
    spec = _m("core.yamlio").read(Path(a.definition)) if a.definition else {}
    opts = spec.pop("options", None) or dict(x.split(":", 1) for x in a.option or [])
    if not opts:
        raise MekanikError(t("cli.decide.no_option"))
    s = _m("core.decisions").open_decision(_root(a), a.id, a.title, opts, a.rationale, dependents=a.dependent or [],
                                           branched=not a.plain, concept=a.concept, **spec)
    say("cli.decide.opened", id=a.id, options=", ".join(t("cli.decide.branch", id=o["id"], branch=o.get(
        "branch") or t("cli.decide.no_branch")) for o in s["decision"]["options"]))


def pulse(a):
    p = _m("agent.pulse")
    v = p.beat(a.work, a.stopped, a.role, "stopped") if a.stopped is not None else p.beat(a.work, a.doing or "", a.role)
    say("cli.pulse", work=v["work"], status=t(f"agent.liveness.{v['status']}"), doing=v["doing"], at=v["at"])


def review_record(a):
    q = _m("core.quality")
    path, rep = q.record(_root(a), a.subject or t("cli.default_subject"), sys.stdin.read())
    for f in rep["findings"]:
        say("cli.review.finding", no=f["no"], severity=t(f"cli.review.severity.{f['severity']}"),
            location=f["location"], problem=f["problem"])
    say("cli.review.recorded", name=path.name, n=len(rep["findings"]), high=len(q.open_high(rep)))


def review_close(a):
    f = _m("core.quality").close(_root(a), a.report, a.finding, a.note, a.case is not None, a.case or a.no_case or "",
                                 commit=a.commit)
    say("cli.review.closed", no=f["no"], note=f["closure"]["note"])


def migrate(a, config: bool):
    """Dry run into --out (else a temp folder), then V1–V8; the real migration (--apply) is phase 2 (§14.1)."""
    m, out = _m("migrate"), Path(a.out or tempfile.mkdtemp(prefix="mekanik-migrate-"))
    snap = json.loads(Path(a.snapshot).read_text(encoding="utf-8")) if not config and a.snapshot else None
    if config:
        log = m.surec_config(vars(a)["from"], out, dry_run=not a.apply)
        res = m.verify_config(out)
    else:
        cfg = _m("config").load_config()
        log = m.surec_work(a.old, out, cfg, dry_run=not a.apply, old=snap)
        res = m.verify(a.old, out, cfg, old=snap) if snap else {}
    for v, r in res.items():
        say("cli.migrate.row", v=v, status=t(f"migrate.status.{r['status']}"),
            detail="; ".join(map(str, r["details"]))[:200] or "—")
    say("cli.migrate.done", n=len(log.gaps), out=out)
    config or snap or say("cli.migrate.no_snapshot")
    return 1 if any(r["status"] == "fail" for r in res.values()) else 0


def verify(a):
    """APPROVAL-02 over every approval record of the work: signed by the chief's key, with the chief's identity."""
    res = _m("core.checks.builtin.approval").signature(_m("core.model.work").load_work(_root(a)))
    say("cli.signing_key", fp=_m("config").load_config().signing_key)   # the key the config pins (§4.6 m.4)
    for r in res:
        say("cli.verify.row", status=t(f"status.{r.status}"), card=r.args.get("card") or "—",
            action=r.args.get("action") or "", at=r.args.get("at") or "", reason=r.reason)
    say("cli.verify.summary", n=sum("card" in r.args for r in res), bad=sum(r.status == "block" for r in res))
    return 1 if any(r.status == "block" for r in res) else 0


COMMANDS = [
    ("doctor", "--json+", lambda a: _m("cli.doctor").run(a.json)),
    ("regress", "", regress),
    ("check", "work? --json+", check),
    ("work new", "--org! --project! --title! --class! --purpose --done", work_new),
    ("work open", "code", lambda a: say("cli.work.open", **_m("core.store.works").open_work(a.code))),
    ("work close", "code", lambda a: say("cli.work.close", code=a.code, n=len(
        _m("core.store.works").close_work(a.code)))),
    ("work attach", "code", lambda a: _m("core.store.works").attach_work(a.code)),
    ("work archive", "code --reason!", lambda a: _json(_m("core.store.works").archive_work(a.code, a.reason))),
    ("step", f"title --role!={ROLES} --text --card* --visual* --next --work", step),
    ("stage finish", "gate --work", stage_finish),
    ("release request", "--work", lambda a: say("cli.release", **_m("core.process.release").release_request(
        _root(a)))),
    ("gate pass", "gate --note --work", lambda a: approve(a, f"O-{a.gate}")),
    ("approve", "card --action!=approve|reject|comment|undo --note --option --row* --work", approve),
    ("reply", f"card --text! --comment --role={ROLES} --commit --work", reply),
    ("pending", "--hook+ --work", pending),
    ("decide", "id --title! --option* --rationale! --definition --dependent* --concept+ --plain+ --work", decide),
    ("agent hook", "event --work", lambda a: _m("agent.hook").run(a.event, a.work)),
    ("agent status", "", lambda a: [say("cli.status", work=r.get("work") or "—", at=at, id=r.get("id", ""), status=t(
        f"cli.run_status.{r.get('status')}")) for at, r in _m("agent.hook").runs()]),
    ("watch", "", lambda a: _m("agent.watch").watch()),
    ("pulse", f"work --doing --stopped --role={ROLES}", pulse),
    ("review prompt", "--subject --work", lambda a: print(_m("core.quality").prompt(
        _root(a), a.subject or t("cli.default_subject")))),
    ("review record", "--subject --work", review_record),
    ("review close", "report finding --note! --case --no-case --commit --work", review_close),
    ("migrate surec-config", "--from! --out --dry-run+ --apply+", lambda a: migrate(a, True)),
    ("migrate surec-work", "old --out --snapshot --dry-run+ --apply+", lambda a: migrate(a, False)),
    ("pkg list", "", lambda a: [say("cli.pkg", id=p.id, version=p.version, checks=len(p.checks))
                                for p in _m("plugins").registry().packages]),
    ("verify", "--work", verify),
]


def _arg(sp, tok: str, h) -> None:
    dash, name, mark, choices = TOKEN.fullmatch(tok).groups()
    kw = {"help": h(f"cli.arg.{name.replace('-', '_')}")}
    kw |= {"choices": choices.split("|"), "default": choices.split("|")[0]} if choices else {}
    if not dash:
        sp.add_argument(name, nargs="?" if mark == "?" else None, **kw)
        return
    kw |= {"!": {"required": True}, "*": {"action": "append"}, "+": {"action": "store_true"}}.get(mark, {})
    sp.add_argument(f"--{name}", **kw)


def parser(helps: bool = True) -> argparse.ArgumentParser:
    """`helps=False` leaves out the help text, so a hook command does not load the catalogs it does not need."""
    h = (lambda key: t(key) if has(key) else None) if helps else (lambda key: None)
    p = argparse.ArgumentParser(prog="mekanik", description=h("cli.description"))
    subs = {(): p.add_subparsers(dest="command", required=True)}
    for path, spec, fn in COMMANDS:
        words = tuple(path.split())
        for i in range(1, len(words)):   # command groups: work, stage, release, gate, agent, review, migrate, pkg
            if words[:i] not in subs:
                g = subs[words[:i - 1]].add_parser(words[i - 1], help=h(f"cli.help.{'_'.join(words[:i])}"))
                subs[words[:i]] = g.add_subparsers(dest="_".join(words[:i]), required=True)
        sp = subs[words[:-1]].add_parser(words[-1], help=h(f"cli.help.{'_'.join(words)}"))
        for tok in spec.split():
            _arg(sp, tok, h)
        sp.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    a = parser(not argv or bool({"-h", "--help"} & set(argv))).parse_args(argv)
    try:
        rc = a.fn(a)
    except (GitError, PermissionError) as e:
        print(t("cli.error", error=e), file=sys.stderr)
        return 3
    except MekanikError as e:   # schema errors and refused actions (old SemaHatasi)
        print(t("cli.error", error=e), file=sys.stderr)
        return 2
    return rc if isinstance(rc, int) else 0


if __name__ == "__main__":
    sys.exit(main())
