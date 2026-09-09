"""Shared data types for fail-closed Project GitOps validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
from typing import Any, NoReturn, Sequence


OCID_SUFFIX = r"[A-Za-z0-9][A-Za-z0-9_-]{0,254}"
MAX_JSON_BYTES, MAX_DEPTH, MAX_COLLECTION_ITEMS = 1_048_576, 20, 1_000
MAX_STRING_LENGTH = 4_096
MAX_DIFF_BYTES = 32_768
MAX_GIT_OUTPUT_BYTES, GIT_TIMEOUT_SECONDS = 1_048_576, 10
GIT_ENV = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
GIT_PREFIX = ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
              "-c", "core.pager=cat"]

try:
    import resource
except ImportError:  # pragma: no cover - resource is available on supported POSIX runners.
    resource = None
UNRESOLVED_TOKEN_RE = re.compile(r"__[A-Za-z0-9_]+__")
GITHUB_TOKEN_RE = re.compile(
    r"(?:github_pat_[A-Za-z0-9_]{8,}|gh[pousr]_[A-Za-z0-9_]{10,})", re.IGNORECASE)
SENSITIVE_VALUE_MARKERS = ("authorization", "client_secret", "api_key", "credential")
PROJECT_PATTERN = re.compile(r"^(?:nonprod|prod)-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
ORG_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
BRANCH_PATTERN = re.compile(r"^agent/(?:adb|vm|nsg)-[a-z0-9](?:[a-z0-9-]{0,62})$")
PATH_PATTERN = re.compile(
    r"^(?P<cloud>oci|azure|gcp)/(?P<environment>dev|test|uat|prod)/"
    r"(?P<region>[a-z0-9-]+)/(?P<kind>database/database\.json|"
    r"compute/compute\.json|network/project-nsgs\.json|"
    r"workloads/adb\.json|lifecycle_operations/adb-lifecycle\.json)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BASE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
EXECUTABLE_GIT_CONFIG_PATTERN = re.compile(
    r"^(?:diff\..+\.(?:command|textconv)|filter\..+\.(?:clean|smudge|process))$")
SAFE_COMMAND_CONFIG_KEYS = frozenset({"core.fsmonitor", "core.hookspath", "core.pager"})
MAX_HANDOFF_BYTES = 65_536
MAX_ADB_MUTATIONS, MAX_NSG_IDS = 3, 5
ADB_VALIDATIONS = ("repository", "one-file-diff", "strict-json", "governed-adb-change",
                   "secret-placeholder")
ADB_FIELDS = frozenset(
    "db_name display_name is_dedicated ecpu_count non_dw_storage_size_in_gbs "
    "db_workload license_model enable_cpu_auto_scaling "
    "enable_storage_auto_scaling admin_password networking".split())
ADB_STRING_PATTERNS = {
    "db_name": re.compile(r"^[A-Za-z][A-Za-z0-9]{0,29}$"),
    "display_name": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")}
ADB_KEY_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,127}$")
ADB_NSG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
ADB_PASSWORD_RE = re.compile(r"^__[A-Z][A-Z0-9_]{2,99}__$")


class ValidationFailure(Exception):
    """A stable, public validation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def failure(code: str, message: str) -> NoReturn:
    """Raise one stable validation failure."""
    raise ValidationFailure(code, message)


def decode_text(content: bytes, code: str, message: str) -> str:
    """Decode UTF-8 content through the stable error contract."""
    try:
        return content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationFailure(code, message) from exc


def sanitize_text(text: str) -> str:
    """Return bounded single-line ASCII for the public error channel."""
    ascii_text = " ".join(text.split()).encode("ascii", "replace").decode("ascii")
    ascii_text = "".join(
        character if 32 <= ord(character) <= 126 else "?" for character in ascii_text)
    return ascii_text[:256] or "Validation failed."


def valid_ocid(value: object, kind: str, region: str | None = None,
               *, nullable: bool = False) -> bool:
    """Return whether a value is an OCID with the required type and region."""
    if value is None:
        return nullable
    location = re.escape(region) if region is not None else ""
    pattern = rf"ocid1\.{kind}\.oc1\.{location}\.{OCID_SUFFIX}"
    return type(value) is str and re.fullmatch(pattern, value) is not None


def has_sensitive_value(value: object, *, allow_password: bool = False) -> bool:
    """Reject credentials and unresolved values outside administrator passwords."""
    if isinstance(value, str):
        folded = value.casefold()
        return (("-----begin " in folded and "private key-----" in folded)
                or GITHUB_TOKEN_RE.search(value) is not None
                or any(marker in folded for marker in SENSITIVE_VALUE_MARKERS)
                or (not allow_password and UNRESOLVED_TOKEN_RE.search(value) is not None))
    if isinstance(value, list):
        return any(has_sensitive_value(item) for item in value)
    if isinstance(value, dict):
        return any(
            has_sensitive_value(key)
            or has_sensitive_value(item, allow_password=key == "admin_password")
            for key, item in value.items()
        )
    return False


def validate_workload_compartment(compartments: dict[str, str], role: str,
                                  compartment_id: object) -> None:
    """Require an OCI workload to use its TBAC handoff target."""
    expected = compartments.get(role)
    if expected is None or compartment_id != expected:
        failure("INVALID_WORKLOAD_COMPARTMENT",
                f"The OCI workload must use the {role} TBAC compartment.")


def success_document(change: RepositoryChange, operation: str, validations: Sequence[str],
                     summary: dict[str, object]) -> dict[str, object]:
    """Build the stable success document returned by the validator."""
    return {"ok": True, "project": change.project, "operation": operation,
            "branch": change.branch, "environment": change.environment,
            "region": change.region, "base_sha": change.base_sha, "path": change.path,
            "content_sha256": hashlib.sha256(change.candidate_content).hexdigest(),
            "validations": list(validations), "summary": summary, "diff": change.diff}


def validate_bounds(value: object, *, depth: int = 0) -> None:
    """Recursively enforce JSON depth, collection, and string limits."""
    if depth > MAX_DEPTH:
        failure("JSON_DEPTH_LIMIT", "JSON nesting exceeded its limit.")
    if isinstance(value, float) and not math.isfinite(value):
        failure("JSON_NONFINITE_NUMBER", "JSON contains a non-finite number.")
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            failure("JSON_STRING_LIMIT", "A JSON string exceeded its limit.")
        return
    if isinstance(value, (list, dict)):
        if len(value) > MAX_COLLECTION_ITEMS:
            failure("JSON_COLLECTION_LIMIT", "A JSON collection exceeded its limit.")
        if isinstance(value, dict) and any(
            isinstance(key, str) and len(key) > MAX_STRING_LENGTH for key in value
        ):
            failure("JSON_STRING_LIMIT", "A JSON string exceeded its limit.")
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            validate_bounds(item, depth=depth + 1)


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            failure("JSON_DUPLICATE_KEY", "JSON contains a duplicate object key.")
        document[key] = value
    return document


def strict_json(content: bytes) -> Any:
    """Decode and parse bounded, unambiguous UTF-8 JSON."""
    if len(content) > MAX_JSON_BYTES:
        failure("JSON_SIZE_LIMIT", "JSON content exceeded its size limit.")
    text = decode_text(content, "INVALID_UTF8", "JSON must be valid UTF-8.")
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicates)
    except ValidationFailure:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValidationFailure("INVALID_JSON", "JSON content is invalid.") from exc
    try:
        validate_bounds(value)
    except RecursionError as exc:
        raise ValidationFailure("JSON_DEPTH_LIMIT", "JSON nesting exceeded its limit.") from exc
    return value


def _limit_git_output_file_size() -> None:
    if resource is not None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_GIT_OUTPUT_BYTES + 1,) * 2)


def run_git(repo: Path, *args: str) -> bytes:
    """Run one fixed-argument Git command with bounded captured output."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_ENV)
    preexec_fn = _limit_git_output_file_size if os.name == "posix" and resource else None
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout_file, \
                tempfile.TemporaryFile(mode="w+b") as stderr_file:
            result = subprocess.run(
                [*GIT_PREFIX, *args], cwd=repo, env=environment, stdin=subprocess.DEVNULL,
                stdout=stdout_file, stderr=stderr_file, shell=False, timeout=GIT_TIMEOUT_SECONDS,
                check=False, preexec_fn=preexec_fn)
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(MAX_GIT_OUTPUT_BYTES + 1)
            stderr = stderr_file.read(MAX_GIT_OUTPUT_BYTES + 1)
            output_signal = getattr(signal, "SIGXFSZ", None)
            if (len(stdout) > MAX_GIT_OUTPUT_BYTES or len(stderr) > MAX_GIT_OUTPUT_BYTES
                    or (output_signal is not None and result.returncode == -output_signal)):
                failure("GIT_OUTPUT_LIMIT", "Git validation output exceeded its limit.")
            if result.returncode != 0:
                failure("GIT_FAILED", "Git validation failed.")
            return stdout
    except subprocess.TimeoutExpired as exc:
        raise ValidationFailure("GIT_TIMEOUT", "Git validation timed out.") from exc
    except ValidationFailure:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValidationFailure("GIT_FAILED", "Git validation failed.") from exc


@dataclass(frozen=True)
class RepositoryChange:
    """One validated manifest modification relative to an immutable base commit."""

    repo: Path
    project: str
    branch: str
    base_ref: str
    base_sha: str
    path: str
    environment: str
    region: str
    kind: str
    base_content: bytes
    candidate_content: bytes
    diff: str
    workload_compartments: dict[str, str]
    organization: str = ""
