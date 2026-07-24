import sys
import subprocess

from dbman_opsi.doctor import DoctorCheck, check_environment, check_session, summarize_checks


def test_summarize_checks_reports_ready_when_required_tools_exist() -> None:
    checks = (
        DoctorCheck(name="python", ok=True, detail="3.11"),
        DoctorCheck(name="oci", ok=True, detail="3.81.1"),
        DoctorCheck(name="terraform", ok=True, detail="1.8.0"),
    )

    assert summarize_checks(checks) == "READY: python, oci, terraform"


def test_summarize_checks_reports_missing_tools() -> None:
    checks = (
        DoctorCheck(name="oci", ok=False, detail="not found"),
        DoctorCheck(name="terraform", ok=True, detail="1.8.0"),
    )

    assert summarize_checks(checks) == "NOT READY: missing oci"


def _fake_run(returncode: int, stdout: str = "", stderr: str = ""):
    def runner(command, check=False, capture_output=True, text=True):
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return runner


def test_check_session_ok_when_authenticated(monkeypatch) -> None:
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: "/usr/bin/oci")
    monkeypatch.setattr(subprocess, "run", _fake_run(0, stdout='[{"key": "FRA"}]'))

    check = check_session("cap", "eu-frankfurt-1")

    assert check.ok
    assert "cap" in check.detail


def test_check_session_fails_when_unauthenticated(monkeypatch) -> None:
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: "/usr/bin/oci")
    monkeypatch.setattr(subprocess, "run", _fake_run(1, stderr="NotAuthenticated: session expired"))

    check = check_session("cap")

    assert not check.ok
    assert "NotAuthenticated" in check.detail


def test_check_session_redacts_user_path(monkeypatch) -> None:
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: "/usr/bin/oci")
    monkeypatch.setattr(subprocess, "run", _fake_run(1, stderr="ERROR in /Users/someone/.oci/config"))

    check = check_session("cap")

    assert "/Users/someone" not in check.detail
    assert "/Users/<USER>" in check.detail


def test_check_session_missing_cli(monkeypatch) -> None:
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: None)

    assert not check_session("cap").ok


def test_check_environment_flags_old_oci_cli(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    def fake_run(command, check=False, capture_output=True, text=True):
        if command == ["oci", "--version"]:
            return subprocess.CompletedProcess(command, 0, "3.36.0\n", "")
        return subprocess.CompletedProcess(command, 0, "Terraform v1.8.0\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    oci_check = next(check for check in check_environment() if check.name == "oci")

    assert not oci_check.ok
    assert "3.36.0" in oci_check.detail


def test_check_environment_accepts_new_oci_cli(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))
    monkeypatch.setattr("dbman_opsi.doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    def fake_run(command, check=False, capture_output=True, text=True):
        if command == ["oci", "--version"]:
            return subprocess.CompletedProcess(command, 0, "3.37.0\n", "")
        return subprocess.CompletedProcess(command, 0, "Terraform v1.8.0\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    oci_check = next(check for check in check_environment() if check.name == "oci")

    assert oci_check.ok
    assert oci_check.detail == "3.37.0"
