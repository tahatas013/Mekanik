# SPDX-License-Identifier: AGPL-3.0-or-later
"""python -m mekanik.agent hook <event> [<work>] | watch | build [<out>] (until the CLI wires the mekanik names)."""

import sys
from pathlib import Path

from . import build, hook, watch

cmd, *rest = sys.argv[1:] or [""]
run = {"hook": lambda: hook.run(*rest[:2]), "watch": watch.watch,
       "build": lambda: not build.build(Path(rest[0]) if rest else Path(__file__).parents[3] / "plugin" / "agents")}
sys.exit(run[cmd]() if cmd in run and (rest or cmd != "hook") else __doc__)
