"""Environment readiness checks for local, Cloud Shell, and ORM workflows."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

from dbman_opsi.redact import redact_text

OCI_CLI_MIN_VERSION = (3, 37, 0)
OCI_CLI_MIN_VERSION_TEXT = ".".join(str(part) for part in OCI_CLI_MIN_VERSION)


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str


def summarize_checks(checks: tuple[DoctorCheck, ...]) -> str:
    missing = [check.name for check in checks if not check.ok]
    if missing:
        return f"NOT READY: missing {', '.join(missing)}"
    return f"READY: {', '.join(check.name for check in checks)}"


def _version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError as exc:
        return str(exc)
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0] if output else "installed"


def _parse_semver(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", text)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _oci_check(oci_path: str | None) -> DoctorCheck:
    if not oci_path:
        return DoctorCheck("oci", False, "not found")
    version = _version(["oci", "--version"])
    parsed = _parse_semver(version)
    if parsed is not None and parsed < OCI_CLI_MIN_VERSION:
        detail = f"{version} (minimum {OCI_CLI_MIN_VERSION_TEXT})"
        return DoctorCheck("oci", False, detail)
    return DoctorCheck("oci", True, version)


def check_environment() -> tuple[DoctorCheck, ...]:
    python_ok = sys.version_info >= (3, 11)
    oci_path = shutil.which("oci")
    terraform_path = shutil.which("terraform")
    return (
        DoctorCheck("python", python_ok, sys.version.split()[0]),
        _oci_check(oci_path),
        DoctorCheck(
            "terraform",
            bool(terraform_path),
            _version(["terraform", "-version"]) if terraform_path else "not found",
        ),
    )


def check_session(profile: str, region: str | None = None) -> DoctorCheck:
    """Confirm the OCI session is actually authenticated, not just installed.

    Runs a global, read-only call (`iam region list`) so an installed-but-expired
    CLI is reported as a failure instead of passing doctor and failing later.
    """

    if not shutil.which("oci"):
        return DoctorCheck("session", False, "oci CLI not found")
    command = ["oci", "--profile", profile]
    if region:
        command += ["--region", region]
    command += ["iam", "region", "list", "--output", "json"]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError as exc:
        return DoctorCheck("session", False, redact_text(str(exc)))
    if result.returncode == 0 and result.stdout.strip():
        return DoctorCheck("session", True, f"authenticated (profile {profile})")
    output = (result.stderr or result.stdout).strip()
    detail = redact_text(output.splitlines()[0]) if output else "no response"
    return DoctorCheck("session", False, detail)
