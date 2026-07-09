"""Command runner for OCI CLI and Terraform calls."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dbman_opsi.journal import RunJournal
from dbman_opsi.redact import redact_text

log = logging.getLogger(__name__)

CommandExecutor = Callable[[tuple[str, ...], str | None], subprocess.CompletedProcess[str]]


class OciError(RuntimeError):
    """Base error for failed OCI CLI commands."""


class OciAuthError(OciError):
    """Authentication or authorization failure from OCI."""


class OciNotFound(OciError):
    """Requested OCI resource was not found."""


class OciThrottled(OciError):
    """OCI throttled the request."""


class OciTransient(OciError):
    """Likely transient OCI or network failure."""


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int

    def json(self) -> Any:
        if not self.stdout.strip():
            return None
        return json.loads(self.stdout)


class CommandRunner:
    def __init__(
        self,
        dry_run: bool = True,
        *,
        journal: RunJournal | None = None,
        run_id: str | None = None,
        clock: Callable[[], float] = time.perf_counter,
        sleeper: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
        base_delay: float = 0.25,
        max_delay: float = 2.0,
        executor: CommandExecutor | None = None,
        verbose: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.journal = journal
        self.run_id = run_id
        self._clock = clock
        self._sleeper = sleeper
        self.max_attempts = max(1, max_attempts)
        self.base_delay = max(0.0, base_delay)
        self.max_delay = max(0.0, max_delay)
        self._executor = executor or _subprocess_executor
        self.verbose = verbose

    def run(
        self,
        args: list[str],
        cwd: str | Path | None = None,
        check: bool = True,
        retry_on_transient: bool = False,
    ) -> CommandResult:
        safe_args = tuple(args)
        if self.dry_run:
            start = self._clock()
            result = CommandResult(safe_args, "{}", "", 0)
            duration_ms = self._duration_ms(start)
            log.info(redact_text("+ " + " ".join(safe_args)))
            self._record(safe_args, result.returncode, duration_ms)
            self._log_timing(safe_args, result.returncode, duration_ms)
            return result

        attempts = self.max_attempts if check else 1
        cwd_value = str(cwd) if cwd else None
        for attempt in range(attempts):
            try:
                return self._run_once(safe_args, cwd_value, check)
            except OciError as exc:
                if not self._should_retry(exc, retry_on_transient, attempt, attempts):
                    raise
                self._sleeper(self._delay_for_attempt(attempt))
        raise RuntimeError("unreachable retry state")

    def _run_once(self, safe_args: tuple[str, ...], cwd: str | None, check: bool) -> CommandResult:
        start = self._clock()
        try:
            process = self._executor(safe_args, cwd)
        except OciError:
            duration_ms = self._duration_ms(start)
            self._record(safe_args, 1, duration_ms)
            self._log_timing(safe_args, 1, duration_ms)
            raise
        duration_ms = self._duration_ms(start)
        self._record(safe_args, process.returncode, duration_ms)
        self._log_timing(safe_args, process.returncode, duration_ms)
        # Return RAW stdout/stderr: callers parse OCIDs out of this for resource
        # joins (discovery's pillar matching, named-credential id lookup, etc.).
        # Redaction is a *display* concern and is applied at the print boundary
        # (CLI --json output, sanitized config). Redacting here silently collapses
        # every OCID to "<OCI_OCID>", which makes OCID-keyed joins match
        # everything-to-everything. Error messages are still redacted because they
        # are surfaced to the user as text.
        if check and process.returncode != 0:
            safe_command = redact_text(" ".join(safe_args))
            safe_stderr = redact_text(process.stderr)
            message = f"Command failed ({process.returncode}): {safe_command}\n{safe_stderr}"
            raise _classify_oci_error(safe_stderr, message)
        return CommandResult(safe_args, process.stdout, process.stderr, process.returncode)

    def _should_retry(
        self,
        exc: OciError,
        retry_on_transient: bool,
        attempt: int,
        attempts: int,
    ) -> bool:
        if attempt >= attempts - 1:
            return False
        if isinstance(exc, OciThrottled):
            return True
        if isinstance(exc, OciTransient):
            return retry_on_transient
        return False

    def _delay_for_attempt(self, attempt: int) -> float:
        return min(self.max_delay, self.base_delay * (2**attempt))

    def _duration_ms(self, start: float) -> int:
        return max(0, int(round((self._clock() - start) * 1000)))

    def _record(self, args: tuple[str, ...], returncode: int, duration_ms: int) -> None:
        if self.journal is None:
            return
        self.journal.record(
            argv=args,
            returncode=returncode,
            duration_ms=duration_ms,
            dry_run=self.dry_run,
        )

    def _log_timing(self, args: tuple[str, ...], returncode: int, duration_ms: int) -> None:
        if not self.verbose:
            return
        log.info(
            "command returncode=%s duration_ms=%s argv=%s",
            returncode,
            duration_ms,
            redact_text(" ".join(args)),
        )


def _classify_oci_error(stderr: str, message: str) -> OciError:
    normalized = stderr.lower()
    if any(marker in normalized for marker in ("notauthenticated", "forbidden", "not authorized", "notauthorized")):
        return OciAuthError(message)
    if "notfound" in normalized or "not found" in normalized or re.search(r"\b404\b", normalized):
        return OciNotFound(message)
    if "toomanyrequests" in normalized or "throttl" in normalized or re.search(r"\b429\b", normalized):
        return OciThrottled(message)
    if (
        re.search(r"\b5\d{2}\b", normalized)
        or "timeout" in normalized
        or "timed out" in normalized
        or "connection" in normalized
    ):
        return OciTransient(message)
    return OciError(message)


def _subprocess_executor(
    args: tuple[str, ...],
    cwd: str | None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
