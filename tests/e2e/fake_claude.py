# SPDX-License-Identifier: AGPL-3.0-or-later
"""A stand-in for `claude` in the session tab's tests (A13; no real agent runs): prints its arguments, then echoes
each typed line; every start and line goes to $FAKE_CLAUDE_LOG (JSON lines) for the test to read."""

import json
import os
import sys


def note(**kw):
    if path := os.environ.get("FAKE_CLAUDE_LOG"):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kw, ensure_ascii=False) + "\n")


note(event="start", args=sys.argv[1:], cwd=os.getcwd(), tty=os.isatty(0), pid=os.getpid())
print("FAKE-CLAUDE " + " ".join(sys.argv[1:]), flush=True)
for line in sys.stdin:
    note(event="line", text=line.rstrip("\n"))
    print("echo: " + line.rstrip("\n"), flush=True)
note(event="end")
