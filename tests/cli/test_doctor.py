# SPDX-License-Identifier: AGPL-3.0-or-later
"""`mekanik doctor` (old `ortam.py`): free space, the approval signature check (T-17 (b)), versions."""

from types import SimpleNamespace

from mekanik.cli import doctor

GB = 1024**3


def _free(findings):
    return next(f for f in findings if f.name == "free_space").status


def test_doctor_low_free_space_warns(monkeypatch, tmp_path):
    """old: test_onbellek::doktor_bos_alan_azsa_uyari"""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr(doctor.shutil, "disk_usage", lambda _: SimpleNamespace(free=9 * GB))
    assert _free(doctor.disk()) == "warn"
    monkeypatch.setattr(doctor.shutil, "disk_usage", lambda _: SimpleNamespace(free=11 * GB))
    assert _free(doctor.disk()) == "ok"


def test_signing_check_without_ssh_tools_is_unchecked(monkeypatch):
    """new: architecture §4.6 madde 5, T-17 (b) — no ssh-add/ssh-keygen: 'could not be checked' (yellow), not green;
    a GPG key cannot carry the per-use confirmation (red, KF1-08); a key missing from the agent is red"""
    real = doctor.shutil.which
    monkeypatch.setattr(doctor.shutil, "which", lambda n: None if n.startswith("ssh-") else real(n))
    assert doctor.signing("SHA256:abc").status == "warn"
    assert doctor.signing("0123456789ABCDEF0123").status == "error"
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/usr/bin/" + n)
    monkeypatch.setattr(doctor, "_run", lambda *cmd, stdin=None: (0, "256 SHA256:other user (ED25519)"))
    assert doctor.signing("SHA256:abc").status == "error"


def test_signing_trial_signature_must_be_refusable(monkeypatch, tmp_path):
    """new: T-17 (b) — the trial signature is refused in the confirmation window → ok; signed anyway → red"""
    key = "SHA256:abc"
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/usr/bin/" + n)
    for rc, want in ((1, "ok"), (0, "error")):
        answers = {"-l": f"256 {key} chief (ED25519)", "-L": "ssh-ed25519 AAAA chief", "-lf": f"256 {key} chief"}
        monkeypatch.setattr(doctor, "_run", lambda *cmd, stdin=None, rc=rc: (
            rc, "") if "-Y" in cmd else (0, answers[cmd[1]]))
        assert doctor.signing(key).status == want


def test_tools_check_python_and_claude_versions(monkeypatch):
    """new: architecture §13.1 — Python 3.12 and a supported Claude Code; optional tools never turn it red"""
    monkeypatch.setattr(doctor, "_tool", lambda n, *a, required=True: doctor.Finding(
        "tool", n, "ok" if required else "pending", "1.9.0 (Claude Code)" if n == "claude" else "x"))
    found = {f.name: f.status for f in doctor.tools()}
    assert found["python"] == "ok" and found["claude"] == "error"
    assert {found[n] for n, _ in doctor.OPTIONAL} == {"pending"}


def test_tool_version_command_must_print_a_version(monkeypatch):
    """new: docs/later.md (Faz 2) — a version command that prints an error and exits 0 (freecad under Wayland) is not
    ok: red for a required tool, yellow for an optional one; a version line anywhere in the output is ok"""
    from mekanik.core.i18n import t

    wayland = "qt.qpa.plugin: Could not find the Qt platform plugin \"wayland\" in \"\""
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/usr/bin/" + n)
    for out, required, want in ((wayland, False, "warn"), (wayland, True, "error"),
                                (f"{wayland}\nFreeCAD 0.21.2, Libs: 0.21.2R33771", False, "ok"),
                                ("git version 2.43.0", True, "ok"), ("tmux next-3.5", False, "ok"),
                                ("libQt5Core.so.5.15 missing", False, "warn")):
        monkeypatch.setattr(doctor, "_run", lambda *cmd, stdin=None, out=out: (0, out))
        f = doctor._tool("freecad", "--version", required=required)
        assert f.status == want, out
        assert f.detail == (t("cli.doctor.no_version", out=out.splitlines()[0]) if want != "ok" else next(
            x for x in out.splitlines() if doctor.VERSION.search(x)))
    monkeypatch.setattr(doctor, "_run", lambda *cmd, stdin=None: (1, "boom"))
    assert doctor._tool("freecad", "--version", required=False).status == "error"
