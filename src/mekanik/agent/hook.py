# SPDX-License-Identifier: AGPL-3.0-or-later
"""Claude Code hook handler (old `durum.py`; architecture §5.4); `mekanik agent hook <event>` calls `run`. Each event
updates the session's agent-run record (listed payload fields only, never the environment or a credential); PreToolUse
denies (data gate, block list in claude_code.yaml, stop flag), UserPromptSubmit blocks and SessionStart warns."""

import hashlib
import json
import os
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path

from mekanik.config import load_config, state_dir
from mekanik.core import clock, yamlio
from mekanik.core.i18n import t

SPEC = yamlio.read(Path(__file__).with_name("claude_code.yaml"))
BLOCK = [(key, re.compile("|".join(rx), re.I)) for key, rx in SPEC["block"].items()]
WORK_CODE = re.compile(r"\b([A-Z]{3})-[A-Z]{3}-\d{2}\b")
STATUS = {"SessionStart": "waiting_input", "Stop": "waiting_input", "SessionEnd": "finished"}  # others: running


def work_of(cwd: Path) -> str | None:
    """Work code: the name of `cwd` or of a parent folder (old durum.kancadan)."""
    p = Path(cwd).resolve()
    return next((d.name for d in (p, *p.parents) if WORK_CODE.fullmatch(d.name)), None)


def stop_flag(work: str) -> Path:
    """Soft stop: while this file exists PreToolUse denies every non-mekanik tool (`mekanik agent stop`, phase 2)."""
    return state_dir() / "stop" / work


def runs(work: str | None = None) -> list[tuple[str, dict]]:
    """(last update = file mtime, record) pairs, oldest first (old durum.oku)."""
    files = sorted((state_dir() / "runs").glob("run-*.json"), key=lambda p: p.stat().st_mtime)
    pairs = [(datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat("T", "seconds"), yamlio.read(p, {}))
             for p in files]
    return [(at, r) for at, r in pairs if work in (None, r.get("work"))]


def record(work: str, event: str, payload: dict) -> dict:
    """Update, or start, the agent-run record of the payload's session (old durum.yaz)."""
    sid, now, cwd = str(payload.get("session_id") or ""), clock.now(), str(payload.get("cwd") or os.getcwd())
    tag = hashlib.sha1(sid.encode()).hexdigest()[:4]
    path, rec = next(((p, r) for p in (state_dir() / "runs").glob(f"run-*-{tag}.json")
                      if (r := yamlio.read(p, {})).get("adapter", {}).get("session_id", "") == sid), (None, None))
    resume = f" --resume {shlex.quote(sid)}" if sid else ""
    rec = rec or {"kind": "agent_run", "schema_version": "1.0", "work": work, "role": "project_engineer",
                  "id": f"run-{datetime.fromisoformat(now):%Y%m%d-%H%M%S}-{tag}", "started_at": now, "cwd": cwd,
                  "terminal_command": f"cd {shlex.quote(cwd)} && claude{resume}",
                  "adapter": {"name": "claude_code", "version": os.environ.get("CLAUDE_CODE_VERSION", "unknown"),
                              **({"session_id": sid} if sid else {})}}
    rec = {k: v for k, v in rec.items() if k not in ("ended_at", "end_reason")}  # a resumed session is open again
    note = f"{payload.get('notification_type') or ''} {payload.get('message') or ''}".lower()
    rec["status"] = ("waiting_permission" if "permission" in note else "waiting_input") if event == "Notification" \
        else STATUS.get(event, "running")
    rec.update({"ended_at": now, "end_reason": "completed"} if event == "SessionEnd" else {})
    yamlio.write_text(path or state_dir() / "runs" / f"{rec['id']}.json", json.dumps(rec, ensure_ascii=False))
    return rec


def org_allowed(org: str) -> bool:
    """data_transfer.model_provider_allowed of the organization; unknown or unreadable → False (Hold)."""
    try:
        return load_config().org(org)["data_transfer"]["model_provider_allowed"] is True
    except Exception:
        return False


def _data_gate(inp: dict, cwd: Path, work: str | None) -> str | None:
    """The session's work, or a path or work code in the tool input, belongs to a forbidden organization."""
    if work and not org_allowed(work[:3]):
        return t("agent.deny.data", org=work[:3])
    try:
        orgs = [o for o in load_config().lists["organizations"]
                if o["data_transfer"]["model_provider_allowed"] is not True]
    except Exception:
        return None
    text = " ".join([str(cwd), *(v for v in inp.values() if isinstance(v, str))])
    for o in orgs:
        repos = {o["repo"].rstrip("/"), os.path.expanduser(o["repo"]).rstrip("/")}
        if o["code"] in {m.group(1) for m in WORK_CODE.finditer(text)} or any(
                re.search(re.escape(r) + r"(?![^/\s'\"])", text) for r in repos):
            return t("agent.deny.data", org=o["code"])
    return None


def _blocked(tool: str, inp: dict) -> str | None:
    if tool == "Bash":
        return next((t(f"agent.deny.{key}") for key, rx in BLOCK if rx.search(str(inp.get("command") or ""))), None)
    rules = SPEC["paths"] + (SPEC["write_paths"] if tool in SPEC["write_tools"] else [])
    paths = "\n".join(str(inp.get(k) or "") for k in ("file_path", "notebook_path", "path", "pattern"))
    return next((t(f"agent.deny.{key}") for key, rx in rules if re.search(rx, paths, re.I | re.M)), None)


def handle(event: str, payload: dict, work: str | None = None) -> dict:
    """One hook event → Claude Code hook output ({} when there is nothing to say; PreToolUse never says 'allow')."""
    if work := work or work_of(Path(payload.get("cwd") or ".")):
        try:
            record(work, event, payload)
        except OSError:
            pass
    if event == "PreToolUse":
        tool, inp = str(payload.get("tool_name") or ""), payload.get("tool_input") or {}
        own = tool.startswith("mcp__plugin_mekanik_") or (
            tool == "Bash" and re.match(SPEC["mekanik_command"], str(inp.get("command"))))
        why = _data_gate(inp, Path(payload.get("cwd") or "."), work) or _blocked(tool, inp) or (
            t("agent.deny.stop", work=work) if work and not own and stop_flag(work).exists() else None)
        return {"hookSpecificOutput": {"hookEventName": event, "permissionDecision": "deny",
                                       "permissionDecisionReason": why}} if why else {}
    if work and event in ("UserPromptSubmit", "SessionStart") and not org_allowed(org := work[:3]):
        return {"decision": "block", "reason": t("agent.block.data", org=org)} if event == "UserPromptSubmit" else {
            "hookSpecificOutput": {"hookEventName": event, "additionalContext": t("agent.context.data", org=org)}}
    return {}


def run(event: str, work: str | None = None, stdin=None, stdout=None) -> int:
    """Hook command: stdin JSON in, hook JSON out; always exit 0, a hook never breaks the session (old kancadan)."""
    try:
        payload = json.load(stdin or sys.stdin)
        out = handle(event, payload if isinstance(payload, dict) else {}, work)
    except Exception:  # an unreadable payload or a bug: say nothing
        out = {}
    if out:
        print(json.dumps(out, ensure_ascii=False), file=stdout or sys.stdout)
    return 0
