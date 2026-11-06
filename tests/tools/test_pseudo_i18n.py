# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests are language-independent (guide §1 rule 4; KF1-11): the CLI and process tests run again in a subprocess with
a temporary pseudo-language catalog (every text in «…»; tests/tools/pseudo_i18n.py) and must all pass."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGETS = ["tests/cli", "tests/core/test_process.py", "tests/core/test_approval_attacks.py", "tests/flow",
           "tests/core/test_report.py", "tests/core/test_intake.py", "tests/core/test_stdmap.py", "tests/core/test_policy.py",
           "tests/core/test_policy_flow.py", "tests/core/test_approval_phase2.py", "tests/agent/test_review_capture.py",
           "tests/migrate/test_apply.py"]


def test_cli_and_process_tests_pass_in_a_pseudo_language():
    """new: KF1-11 — no CLI or process test reads Turkish text: all pass when every catalog text is changed"""
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(HERE), os.environ.get("PYTHONPATH")])),
           "MEKANIK_CONFIG_DIR": str(ROOT / "tests" / "fixtures" / "config")}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings", "-p", "no:cacheprovider", "-p",
                        "pseudo_i18n", *TARGETS], cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stdout[-6000:]
    assert " passed" in p.stdout.splitlines()[-1] and "failed" not in p.stdout.splitlines()[-1]
