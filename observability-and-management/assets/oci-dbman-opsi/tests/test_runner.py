import json
import logging
import subprocess
from pathlib import Path

import pytest

from dbman_opsi.journal import RunJournal
from dbman_opsi.runner import (
    CommandRunner,
    CommandResult,
    OciAuthError,
    OciError,
    OciNotFound,
    OciThrottled,
    OciTransient,
)


def _completed(
    args: tuple[str, ...],
    stderr: str,
    returncode: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout="", stderr=stderr)


def test_dry_run_runner_logs_redacted_command(caplog) -> None:
    runner = CommandRunner(dry_run=True)
    caplog.set_level(logging.INFO, logger="dbman_opsi.runner")

    result = runner.run(["oci", "db", "get", "--database-id", "ocid1" + ".database.oc1..example"])

    assert result.returncode == 0
    assert result.json() == {}
    assert "ocid1" + "." not in caplog.text
    assert "+ oci db get" in caplog.text


def test_runner_raises_on_failed_command() -> None:
    runner = CommandRunner(dry_run=False)

    try:
        runner.run(["python3", "-c", "import sys; sys.stderr.write('boom'); sys.exit(7)"])
    except RuntimeError as exc:
        assert "boom" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_runner_returns_raw_ocids_for_logic() -> None:
    # The data path must NOT redact OCIDs: discovery/credential joins parse real
    # OCIDs out of command output. Redacting here would collapse every OCID to the
    # same token and make OCID-keyed joins match everything-to-everything.
    runner = CommandRunner(dry_run=False)
    ocid = "ocid1" + ".database.oc1..realexample"

    result = runner.run(["python3", "-c", f"print('{{\"data\": {{\"id\": \"{ocid}\"}}}}')"])

    assert result.json()["data"]["id"] == ocid


def test_runner_redacts_failed_command() -> None:
    runner = CommandRunner(dry_run=False)

    try:
        runner.run(["python3", "-c", "import sys; sys.exit(7)", "ocid1" + ".database.oc1..example"])
    except RuntimeError as exc:
        assert "ocid1" + "." not in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


@pytest.mark.parametrize(
    ("stderr", "error_type"),
    [
        ("ServiceError: NotAuthenticated: session expired", OciAuthError),
        ("ServiceError: Forbidden: missing policy", OciAuthError),
        ("ServiceError: NotFound: target database not found", OciNotFound),
        ("ServiceError: 404: target not found", OciNotFound),
        ("ServiceError: TooManyRequests: retry later", OciThrottled),
        ("ServiceError: 429: request throttled", OciThrottled),
        ("ServiceError: 503 Service Unavailable", OciTransient),
        ("connection timeout while calling OCI", OciTransient),
        ("ServiceError: Unknown failure", OciError),
    ],
)
def test_runner_classifies_oci_errors(stderr: str, error_type: type[OciError]) -> None:
    runner = CommandRunner(dry_run=False)

    with pytest.raises(error_type):
        runner.run(["python3", "-c", f"import sys; sys.stderr.write({stderr!r}); sys.exit(7)"])


def test_runner_retries_throttled_command_then_succeeds(tmp_path: Path) -> None:
    attempts: list[tuple[str, ...]] = []

    def executor(args: tuple[str, ...], cwd: str | None) -> subprocess.CompletedProcess[str]:
        attempts.append(args)
        if len(attempts) < 3:
            raise OciThrottled("ServiceError: 429: request throttled")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout='{"ok": true}', stderr="")

    sleeps: list[float] = []
    ticks = iter((0.0, 0.01, 0.02, 0.03, 0.04, 0.05))
    journal = RunJournal(run_id="retry", profile="p", region="r", root=tmp_path / "runs")
    runner = CommandRunner(
        dry_run=False,
        executor=executor,
        journal=journal,
        clock=lambda: next(ticks),
        sleeper=sleeps.append,
        max_attempts=3,
        base_delay=0.5,
    )

    result = runner.run(["oci", "db", "get"])

    assert result == CommandResult(("oci", "db", "get"), '{"ok": true}', "", 0)
    assert len(attempts) == 3
    assert sleeps == [0.5, 1.0]
    entries = [json.loads(line) for line in journal.path.read_text(encoding="utf-8").splitlines()]
    assert [entry["returncode"] for entry in entries] == [1, 1, 0]


def test_runner_retries_transient_read_when_enabled() -> None:
    attempts = 0

    def executor(args: tuple[str, ...], cwd: str | None) -> subprocess.CompletedProcess[str]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return _completed(args, "ServiceError: 503 Service Unavailable", 1)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="{}", stderr="")

    runner = CommandRunner(dry_run=False, executor=executor, sleeper=lambda delay: None)

    result = runner.run(["oci", "db", "list"], retry_on_transient=True)

    assert result.returncode == 0
    assert attempts == 2


def test_runner_does_not_retry_auth_error() -> None:
    attempts = 0

    def executor(args: tuple[str, ...], cwd: str | None) -> subprocess.CompletedProcess[str]:
        nonlocal attempts
        attempts += 1
        return _completed(args, "ServiceError: NotAuthenticated: session expired", 1)

    runner = CommandRunner(dry_run=False, executor=executor, sleeper=lambda delay: None)

    with pytest.raises(OciAuthError):
        runner.run(["oci", "db", "get"], retry_on_transient=True)

    assert attempts == 1


def test_runner_does_not_retry_not_found_error() -> None:
    attempts = 0

    def executor(args: tuple[str, ...], cwd: str | None) -> subprocess.CompletedProcess[str]:
        nonlocal attempts
        attempts += 1
        return _completed(args, "ServiceError: NotFound: target database not found", 1)

    runner = CommandRunner(dry_run=False, executor=executor, sleeper=lambda delay: None)

    with pytest.raises(OciNotFound):
        runner.run(["oci", "db", "get"], retry_on_transient=True)

    assert attempts == 1


def test_runner_does_not_retry_mutating_transient_by_default() -> None:
    attempts = 0

    def executor(args: tuple[str, ...], cwd: str | None) -> subprocess.CompletedProcess[str]:
        nonlocal attempts
        attempts += 1
        return _completed(args, "connection timeout while calling OCI", 1)

    runner = CommandRunner(dry_run=False, executor=executor, sleeper=lambda delay: None)

    with pytest.raises(OciTransient):
        runner.run(["oci", "db", "update"])

    assert attempts == 1
