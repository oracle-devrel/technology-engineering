#!/usr/bin/env python3
"""Fail-closed, read-only validation of one governed project repository change."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import ipaddress
import json
import math
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NoReturn, Sequence

try:
    import resource
except ImportError:  # pragma: no cover - resource is available on supported POSIX runners.
    resource = None


MAX_JSON_BYTES, MAX_DIFF_BYTES, MAX_GIT_OUTPUT_BYTES = 1_048_576, 32_768, 1_048_576
MAX_HANDOFF_BYTES, MAX_DEPTH, MAX_COLLECTION_ITEMS = 65_536, 20, 1_000
MAX_STRING_LENGTH, GIT_TIMEOUT_SECONDS = 4_096, 10
MAX_ADB_MUTATIONS = 3

PROJECT_PATTERN = re.compile(r"^(?:nonprod|prod)-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
BRANCH_PATTERN = re.compile(
    r"^agent/(?:adb|vm|nsg)-[a-z0-9](?:[a-z0-9-]{0,62})$"
)
PATH_PATTERN = re.compile(
    r"^oci/(?P<environment>dev|test|uat|prod)/"
    r"(?P<region>[a-z]{2}-[a-z]+-[0-9]+)/(?P<kind>database/database\.json|"
    r"compute/compute\.json|network/project-nsgs\.json|"
    r"lifecycle_operations/adb-lifecycle\.json)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BASE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_ORIGIN_RES = tuple(re.compile(
    rf"^{prefix}__CUSTOMER_ORG__/(?P<project>{PROJECT_PATTERN.pattern[1:-1]})(?:\.git)?$"
) for prefix in (r"https://github\.com/", r"git@github\.com:", r"ssh://git@github\.com/"))
_EXECUTABLE_GIT_CONFIG_PATTERN = re.compile(
    r"^(?:diff\..+\.(?:command|textconv)|"
    r"filter\..+\.(?:clean|smudge|process))$")
_SAFE_COMMAND_CONFIG_KEYS = frozenset({"core.fsmonitor", "core.hookspath", "core.pager"})
ADB_VALIDATIONS = ("repository", "one-file-diff", "strict-json", "governed-adb-change",
                   "secret-placeholder")
LIFECYCLE_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "declared-adb-targets", "start-stop-only")
COMPUTE_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "governed-vm-change",
    "declared-nsg-references",
)
NSG_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "additive-nsg", "existing-vcn-only",
)
LIFECYCLE_ROOT_KEYS = frozenset({"operation_type", "targets"})
TARGET_KEYS = frozenset({"display_name", "action"})
ADB_FIELDS = frozenset(
    "db_name display_name compartment_id cpu_core_count "
    "data_storage_size_in_tbs compute_model db_workload db_version "
    "is_auto_scaling_enabled is_auto_scaling_for_storage_enabled license_model "
    "admin_password is_mtls_connection_required subnet_id nsg_ids kms_key_id".split())
MAX_NSG_IDS = 5
ADB_STRING_PATTERNS = {
    "db_name": re.compile(r"^[A-Za-z][A-Za-z0-9]{0,29}$"),
    "display_name": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$"),
    "db_version": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")}
ADB_KEY_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,127}$")
ADB_NSG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
ADB_PASSWORD_RE = re.compile(r"^__[A-Z][A-Z0-9_]{2,99}__$")
RESOURCE_KEY_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,127}$")
RESOURCE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
SHAPE_RE = re.compile(r"^VM\.[A-Za-z0-9][A-Za-z0-9.]{1,126}$")
GENERIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FIXED_SSH_PUBLIC_KEY_PATH = "/home/opc/.ssh/oci_vm_key.pub"
COMPUTE_ROOT_KEYS = frozenset(
    {"default_compartment_id", "default_ssh_public_key_path", "instances"}
)
VM_FIELDS = frozenset(
    {
        "compartment_id", "cis_level", "name", "shape", "flex_shape_settings",
        "platform_image", "placement", "boot_volume", "networking",
    }
)
NSG_FIELDS = frozenset(
    {
        "compartment_id", "display_name", "defined_tags", "freeform_tags",
        "ingress_rules", "egress_rules",
    }
)
NSG_TAG_KEYS = frozenset({"Project", "Tier", "ManagedBy"})
RULE_COMMON_KEYS = frozenset(
    {
        "description", "protocol", "stateless", "dst_port_min", "dst_port_max",
        "src_port_min", "src_port_max", "icmp_type", "icmp_code",
    }
)
OCID_SUFFIX = r"[A-Za-z0-9][A-Za-z0-9_-]{0,254}"
_UNRESOLVED_TOKEN_RE = re.compile(r"__[A-Za-z0-9_]+__")
_GITHUB_TOKEN_RE = re.compile(
    r"(?:github_pat_[A-Za-z0-9_]{8,}|gh[pousr]_[A-Za-z0-9_]{10,})", re.IGNORECASE)
_GIT_ENV = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
_GIT_PREFIX = ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
               "-c", "core.pager=cat"]
_SENSITIVE_VALUE_MARKERS = ("authorization", "client_secret", "api_key", "credential")


class ValidationFailure(Exception):
    """A stable, public validation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


@dataclass(frozen=True, slots=True)
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


def _failure(code: str, message: str) -> NoReturn:
    raise ValidationFailure(code, message)


def validate_manifest_scope(environment: str, kind: str) -> None:
    """Reject operations that are not enabled for the repository environment."""
    if environment == "prod" and kind.startswith("lifecycle_operations/"):
        _failure(
            "UNSUPPORTED_PRODUCTION_DAY2",
            "Production lifecycle operations are not available in this release.",
        )


def _decode_text(content: bytes, code: str, message: str) -> str:
    try:
        return content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationFailure(code, message) from exc


def sanitize_text(text: str) -> str:
    """Return bounded single-line ASCII suitable for the public error channel."""
    ascii_text = " ".join(text.split()).encode("ascii", "replace").decode("ascii")
    ascii_text = "".join(
        character if 32 <= ord(character) <= 126 else "?" for character in ascii_text)
    return ascii_text[:256] or "Validation failed."


def emit_error(error: ValidationFailure) -> int:
    """Emit exactly one stable JSON error document to stdout."""
    code = error.code if re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", error.code) else "VALIDATION_ERROR"
    document = {"ok": False, "error": {"code": code, "message": sanitize_text(error.message)}}
    sys.stdout.write(json.dumps(document, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 2


def _limit_git_output_file_size() -> None:
    if resource is not None:
        limit = MAX_GIT_OUTPUT_BYTES + 1
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))


def run_git(repo: Path, *args: str) -> bytes:
    """Run one fixed-argument Git command with bounded captured output."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(_GIT_ENV)
    command = [*_GIT_PREFIX, *args]
    preexec_fn = _limit_git_output_file_size if os.name == "posix" and resource else None
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout_file, \
                tempfile.TemporaryFile(mode="w+b") as stderr_file:
            result = subprocess.run(
                command, cwd=repo, env=environment, stdin=subprocess.DEVNULL,
                stdout=stdout_file, stderr=stderr_file, shell=False,
                timeout=GIT_TIMEOUT_SECONDS, check=False, preexec_fn=preexec_fn)
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(MAX_GIT_OUTPUT_BYTES + 1)
            stderr = stderr_file.read(MAX_GIT_OUTPUT_BYTES + 1)
            output_signal = getattr(signal, "SIGXFSZ", None)
            if (len(stdout) > MAX_GIT_OUTPUT_BYTES or len(stderr) > MAX_GIT_OUTPUT_BYTES
                    or (output_signal is not None and result.returncode == -output_signal)):
                _failure("GIT_OUTPUT_LIMIT", "Git validation output exceeded its limit.")
            if result.returncode != 0:
                _failure("GIT_FAILED", "Git validation failed.")
            return stdout
    except subprocess.TimeoutExpired as exc:
        raise ValidationFailure("GIT_TIMEOUT", "Git validation timed out.") from exc
    except ValidationFailure:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValidationFailure("GIT_FAILED", "Git validation failed.") from exc


def validate_bounds(value: object, *, depth: int = 0) -> None:
    """Recursively enforce JSON depth, collection, and string limits."""
    if depth > MAX_DEPTH:
        _failure("JSON_DEPTH_LIMIT", "JSON nesting exceeded its limit.")
    if isinstance(value, float) and not math.isfinite(value):
        _failure("JSON_NONFINITE_NUMBER", "JSON contains a non-finite number.")
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            _failure("JSON_STRING_LIMIT", "A JSON string exceeded its limit.")
        return
    if isinstance(value, (list, dict)):
        if len(value) > MAX_COLLECTION_ITEMS:
            _failure("JSON_COLLECTION_LIMIT", "A JSON collection exceeded its limit.")
        if isinstance(value, dict) and any(
            isinstance(key, str) and len(key) > MAX_STRING_LENGTH for key in value
        ):
            _failure("JSON_STRING_LIMIT", "A JSON string exceeded its limit.")
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            validate_bounds(item, depth=depth + 1)


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            _failure("JSON_DUPLICATE_KEY", "JSON contains a duplicate object key.")
        document[key] = value
    return document


def strict_json(content: bytes) -> Any:
    """Decode and parse bounded, unambiguous UTF-8 JSON."""
    if len(content) > MAX_JSON_BYTES:
        _failure("JSON_SIZE_LIMIT", "JSON content exceeded its size limit.")
    text = _decode_text(content, "INVALID_UTF8", "JSON must be valid UTF-8.")
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


def validate_adb_declaration(
    adb_key: object,
    adb: object,
    *,
    project: str,
    environment: str,
    region: str,
) -> None:
    """Validate one created or updated ADB declaration."""
    if (not isinstance(adb_key, str) or ADB_KEY_RE.fullmatch(adb_key) is None
            or not isinstance(adb, dict) or set(adb) != ADB_FIELDS):
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    invalid = any(type(adb[field]) is not str or pattern.fullmatch(adb[field]) is None
                  for field, pattern in ADB_STRING_PATTERNS.items())
    invalid |= any(type(adb[field]) is not bool for field in (
        "is_auto_scaling_enabled", "is_auto_scaling_for_storage_enabled",
        "is_mtls_connection_required",
    ))
    invalid |= type(adb["cpu_core_count"]) is not int or not 1 <= adb["cpu_core_count"] <= 512
    invalid |= (type(adb["data_storage_size_in_tbs"]) is not int
                or not 1 <= adb["data_storage_size_in_tbs"] <= 384)
    for field, allowed in {
        "compute_model": {"ECPU", "OCPU"}, "db_workload": {"OLTP", "DW"},
        "license_model": {"BRING_YOUR_OWN_LICENSE", "LICENSE_INCLUDED"},
    }.items():
        invalid |= type(adb[field]) is not str or adb[field] not in allowed
    invalid |= not _valid_ocid(adb["compartment_id"], "compartment", nullable=True)
    invalid |= not _valid_ocid(adb["subnet_id"], "subnet", region)
    invalid |= not _valid_ocid(adb["kms_key_id"], "key", region, nullable=True)
    nsg_ids = adb["nsg_ids"]
    invalid |= (type(nsg_ids) is not list or not 1 <= len(nsg_ids) <= MAX_NSG_IDS
                or any(type(item) is not str or ADB_NSG_RE.fullmatch(item) is None
                       for item in nsg_ids) or len(set(nsg_ids)) != len(nsg_ids))
    if invalid:
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    password = adb["admin_password"]
    project_match = re.search(r"project(?P<number>[0-9]+)$", project)
    project_token = f"PROJ{project_match.group('number')}" if project_match else ""
    if type(password) is not str:
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    inner_secret_name = password[2:-2]
    environment_prefix = f"{environment.upper()}_"
    if (not project_token or ADB_PASSWORD_RE.fullmatch(password) is None
            or "__" in inner_secret_name
            or not inner_secret_name.startswith(environment_prefix)
            or project_token not in inner_secret_name.split("_")):
        _failure("INVALID_SECRET_PLACEHOLDER",
                 "The ADB administrator secret placeholder is invalid.")


def _valid_ocid(value: object, kind: str, region: str | None = None,
                *, nullable: bool = False) -> bool:
    if value is None:
        return nullable
    location = re.escape(region) if region is not None else ""
    pattern = rf"ocid1\.{kind}\.oc1\.{location}\.{OCID_SUFFIX}"
    return type(value) is str and re.fullmatch(pattern, value) is not None


def _has_sensitive_value(value: object, *, allow_password: bool = False) -> bool:
    if isinstance(value, str):
        folded = value.casefold()
        return (("-----begin " in folded and "private key-----" in folded)
                or _GITHUB_TOKEN_RE.search(value) is not None
                or any(marker in folded for marker in _SENSITIVE_VALUE_MARKERS)
                or (not allow_password and _UNRESOLVED_TOKEN_RE.search(value) is not None))
    if isinstance(value, list):
        return any(_has_sensitive_value(item) for item in value)
    if isinstance(value, dict):
        return any(
            _has_sensitive_value(key)
            or _has_sensitive_value(item, allow_password=key == "admin_password")
            for key, item in value.items()
        )
    return False


def _adb_configuration(document: object) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(document, dict) or set(document) != {"autonomous_databases_configuration"}:
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    configuration = document.get("autonomous_databases_configuration")
    databases = configuration.get("autonomous_databases") if isinstance(configuration, dict) else None
    if not isinstance(configuration, dict) or not isinstance(databases, dict):
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    return configuration, databases


def _adb_aggregate(document: object, *, allow_empty: bool) -> tuple[str | None, dict[str, Any]]:
    if allow_empty and document == {}:
        return None, {}
    configuration, databases = _adb_configuration(document)
    if (set(configuration) != {"default_compartment_id", "autonomous_databases"}
            or not _valid_ocid(configuration.get("default_compartment_id"), "compartment")):
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    return configuration["default_compartment_id"], databases


def _adb_summary(
    adb_key: str,
    adb: object,
    *,
    action: str,
    region: str,
    default_compartment_id: str | None,
    changed_fields: Sequence[str] = (),
) -> dict[str, object]:
    """Build a secret-safe summary for one ADB mutation."""
    entry = adb if isinstance(adb, dict) else {}
    summary: dict[str, object] = {
        "resource_type": "oci-adb",
        "action": action,
        "key": adb_key,
        "display_name": entry.get("display_name", adb_key),
        "db_name": entry.get("db_name"),
        "region": region,
    }
    if action == "delete":
        summary["destructive"] = True
        return summary
    summary.update({
        "compartment_id": entry.get("compartment_id") or default_compartment_id,
        "compute_model": entry.get("compute_model"),
        "cpu_core_count": entry.get("cpu_core_count"),
        "data_storage_size_in_tbs": entry.get("data_storage_size_in_tbs"),
        "db_workload": entry.get("db_workload"),
        "db_version": entry.get("db_version"),
        "license_model": entry.get("license_model"),
        "compute_auto_scaling": entry.get("is_auto_scaling_enabled"),
        "storage_auto_scaling": entry.get("is_auto_scaling_for_storage_enabled"),
        "mtls_required": entry.get("is_mtls_connection_required"),
        "subnet_id": entry.get("subnet_id"),
        "nsg_keys": entry.get("nsg_ids"),
        "kms_key_id": entry.get("kms_key_id"),
    })
    password = entry.get("admin_password")
    if isinstance(password, str) and ADB_PASSWORD_RE.fullmatch(password):
        summary["admin_password_secret_name"] = password[2:-2]
    if changed_fields:
        summary["changed_fields"] = list(changed_fields)
        summary["replacement_possible"] = True
    return summary


def validate_adb_change(change: RepositoryChange) -> dict[str, object]:
    """Validate one to three governed ADB creates, updates, or deletions."""
    base_document = strict_json(change.base_content)
    candidate_document = strict_json(change.candidate_content)
    base_default, base_databases = _adb_aggregate(base_document, allow_empty=True)
    candidate_default, candidate_databases = _adb_aggregate(candidate_document, allow_empty=False)
    added_keys = candidate_databases.keys() - base_databases.keys()
    removed_keys = base_databases.keys() - candidate_databases.keys()
    modified_keys = {
        key for key in base_databases.keys() & candidate_databases.keys()
        if base_databases[key] != candidate_databases[key]
    }
    mutation_count = len(added_keys) + len(removed_keys) + len(modified_keys)
    if (not 1 <= mutation_count <= MAX_ADB_MUTATIONS
            or (base_default is not None and base_default != candidate_default)):
        _failure(
            "INVALID_ADB_CHANGE",
            "Between one and three ADBs must be created, updated, or deleted.",
        )

    for field in ("db_name", "display_name", "admin_password"):
        identities = [
            value[field].casefold()
            for value in candidate_databases.values()
            if isinstance(value, dict) and type(value.get(field)) is str
        ]
        if len(identities) != len(set(identities)):
            _failure("INVALID_ADB_CHANGE", "ADB identities and secret names must be unique.")

    resource_summaries: list[dict[str, object]] = []

    for adb_key in sorted(added_keys):
        new_adb = candidate_databases[adb_key]
        if _has_sensitive_value(new_adb):
            _failure("INVALID_SECRET_VALUE", "The ADB manifest contains a rejected value.")
        validate_adb_declaration(
            adb_key,
            new_adb,
            project=change.project,
            environment=change.environment,
            region=change.region,
        )
        resource_summaries.append(_adb_summary(
            adb_key, new_adb, action="create", region=change.region,
            default_compartment_id=candidate_default,
        ))

    for adb_key in sorted(modified_keys):
        updated_adb = candidate_databases[adb_key]
        if _has_sensitive_value(updated_adb):
            _failure("INVALID_SECRET_VALUE", "The ADB manifest contains a rejected value.")
        validate_adb_declaration(
            adb_key,
            updated_adb,
            project=change.project,
            environment=change.environment,
            region=change.region,
        )
        previous_adb = base_databases[adb_key]
        changed_fields = sorted(
            field for field in ADB_FIELDS
            if not isinstance(previous_adb, dict)
            or previous_adb.get(field) != updated_adb.get(field)
        )
        resource_summaries.append(_adb_summary(
            adb_key, updated_adb, action="update", region=change.region,
            default_compartment_id=candidate_default, changed_fields=changed_fields,
        ))

    for adb_key in sorted(removed_keys):
        resource_summaries.append(_adb_summary(
            adb_key, base_databases[adb_key], action="delete", region=change.region,
            default_compartment_id=base_default,
        ))

    summary: dict[str, object]
    if len(resource_summaries) == 1:
        summary = resource_summaries[0]
    else:
        actions = {resource["action"] for resource in resource_summaries}
        summary = {
            "resource_type": "oci-adb-batch",
            "action": next(iter(actions)) if len(actions) == 1 else "mixed",
            "resource_count": len(resource_summaries),
            "region": change.region,
            "destructive": any(resource.get("destructive") is True
                               for resource in resource_summaries),
            "resources": resource_summaries,
        }
    operation = f"adb-{summary['action']}" if summary["action"] != "mixed" else "adb-change"
    return _success_document(change, operation, ADB_VALIDATIONS, summary)


def _decimal_string(value: object, minimum: int, maximum: int) -> bool:
    return (
        type(value) is str
        and re.fullmatch(r"[1-9][0-9]*", value) is not None
        and minimum <= int(value) <= maximum
    )


def _compute_aggregate(
    document: object, *, allow_empty: bool
) -> tuple[str | None, str | None, dict[str, Any]]:
    if allow_empty and document == {}:
        return None, None, {}
    if not isinstance(document, dict) or set(document) != {"instances_configuration"}:
        _failure("INVALID_COMPUTE_CHANGE", "The Compute manifest is invalid.")
    configuration = document.get("instances_configuration")
    if not isinstance(configuration, dict) or set(configuration) != COMPUTE_ROOT_KEYS:
        _failure("INVALID_COMPUTE_CHANGE", "The Compute manifest is invalid.")
    compartment_id = configuration.get("default_compartment_id")
    ssh_path = configuration.get("default_ssh_public_key_path")
    instances = configuration.get("instances")
    if (
        not _valid_ocid(compartment_id, "compartment")
        or ssh_path != FIXED_SSH_PUBLIC_KEY_PATH
        or not isinstance(instances, dict)
    ):
        _failure("INVALID_COMPUTE_CHANGE", "The Compute manifest is invalid.")
    return compartment_id, ssh_path, instances


def _validate_vm_declaration(
    vm_key: object, vm: object, *, region: str
) -> tuple[str, str, set[str]]:
    if (
        not isinstance(vm_key, str)
        or RESOURCE_KEY_RE.fullmatch(vm_key) is None
        or not isinstance(vm, dict)
        or set(vm) != VM_FIELDS
    ):
        _failure("INVALID_COMPUTE_CHANGE", "The VM declaration is invalid.")
    name = vm.get("name")
    shape = vm.get("shape")
    flex = vm.get("flex_shape_settings")
    image = vm.get("platform_image")
    placement = vm.get("placement")
    boot = vm.get("boot_volume")
    networking = vm.get("networking")
    invalid = not _valid_ocid(vm.get("compartment_id"), "compartment")
    invalid |= vm.get("cis_level") not in ("1", "2")
    invalid |= type(name) is not str or RESOURCE_NAME_RE.fullmatch(name) is None
    invalid |= type(shape) is not str or SHAPE_RE.fullmatch(shape) is None
    invalid |= not isinstance(flex, dict) or set(flex) != {"ocpus", "memory"}
    if isinstance(flex, dict):
        invalid |= not _decimal_string(flex.get("ocpus"), 1, 128)
        invalid |= not _decimal_string(flex.get("memory"), 1, 2048)
    invalid |= not isinstance(image, dict) or set(image) != {"ocid"}
    if isinstance(image, dict):
        invalid |= not _valid_ocid(image.get("ocid"), "image", region)
    invalid |= (
        not isinstance(placement, dict)
        or set(placement) != {"availability_domain", "fault_domain"}
    )
    if isinstance(placement, dict):
        invalid |= not _decimal_string(placement.get("availability_domain"), 1, 3)
        invalid |= not _decimal_string(placement.get("fault_domain"), 1, 3)
    invalid |= (
        not isinstance(boot, dict)
        or set(boot) != {"size", "preserve_on_instance_deletion"}
    )
    if isinstance(boot, dict):
        invalid |= not _decimal_string(boot.get("size"), 50, 32_768)
        invalid |= boot.get("preserve_on_instance_deletion") not in ("true", "false")
    invalid |= (
        not isinstance(networking, dict)
        or set(networking) != {"hostname", "subnet_id", "network_security_groups"}
    )
    hostname: object = None
    nsg_keys: object = None
    if isinstance(networking, dict):
        hostname = networking.get("hostname")
        nsg_keys = networking.get("network_security_groups")
        invalid |= (
            type(hostname) is not str
            or RESOURCE_NAME_RE.fullmatch(hostname) is None
            or hostname != name
            or not _valid_ocid(networking.get("subnet_id"), "subnet", region)
            or type(nsg_keys) is not list
            or not 1 <= len(nsg_keys) <= MAX_NSG_IDS
            or any(
                type(key) is not str or RESOURCE_KEY_RE.fullmatch(key) is None
                for key in nsg_keys
            )
            or len(set(nsg_keys)) != len(nsg_keys)
        )
    if invalid:
        _failure("INVALID_COMPUTE_CHANGE", "The VM declaration is invalid.")
    assert isinstance(name, str) and isinstance(hostname, str) and isinstance(nsg_keys, list)
    return name, hostname, set(nsg_keys)


def _vm_summary(
    vm_key: str,
    vm: object,
    *,
    action: str,
    region: str,
    changed_fields: Sequence[str] = (),
) -> dict[str, object]:
    """Build a safe summary for one VM mutation."""
    entry = vm if isinstance(vm, dict) else {}
    summary: dict[str, object] = {
        "resource_type": "oci-vm",
        "action": action,
        "key": vm_key,
        "name": entry.get("name", vm_key),
        "region": region,
    }
    boot = entry.get("boot_volume") if isinstance(entry.get("boot_volume"), dict) else {}
    if action == "delete":
        summary.update({
            "destructive": True,
            "preserve_boot_volume": boot.get("preserve_on_instance_deletion"),
        })
        return summary
    flex = entry.get("flex_shape_settings") if isinstance(
        entry.get("flex_shape_settings"), dict) else {}
    image = entry.get("platform_image") if isinstance(
        entry.get("platform_image"), dict) else {}
    placement = entry.get("placement") if isinstance(entry.get("placement"), dict) else {}
    networking = entry.get("networking") if isinstance(entry.get("networking"), dict) else {}
    summary.update({
        "compartment_id": entry.get("compartment_id"),
        "shape": entry.get("shape"),
        "ocpus": flex.get("ocpus"),
        "memory_gbs": flex.get("memory"),
        "image_ocid": image.get("ocid"),
        "availability_domain": placement.get("availability_domain"),
        "fault_domain": placement.get("fault_domain"),
        "boot_volume_size_gbs": boot.get("size"),
        "preserve_boot_volume": boot.get("preserve_on_instance_deletion"),
        "hostname": networking.get("hostname"),
        "subnet_id": networking.get("subnet_id"),
        "nsg_keys": networking.get("network_security_groups"),
    })
    if changed_fields:
        summary["changed_fields"] = list(changed_fields)
        summary["replacement_possible"] = True
    return summary


def validate_compute_change(change: RepositoryChange) -> dict[str, object]:
    """Validate one governed VM create, update, replacement, or deletion."""
    base_document = strict_json(change.base_content)
    candidate_document = strict_json(change.candidate_content)
    if _has_sensitive_value(candidate_document):
        _failure("INVALID_SECRET_VALUE", "The Compute manifest contains a rejected value.")
    base_compartment, base_ssh_path, base_instances = _compute_aggregate(
        base_document, allow_empty=True
    )
    candidate_compartment, candidate_ssh_path, candidate_instances = _compute_aggregate(
        candidate_document, allow_empty=False
    )
    added_keys = candidate_instances.keys() - base_instances.keys()
    removed_keys = base_instances.keys() - candidate_instances.keys()
    modified_keys = {
        key for key in base_instances.keys() & candidate_instances.keys()
        if base_instances[key] != candidate_instances[key]
    }
    is_replacement = len(added_keys) == 1 and len(removed_keys) == 1 and not modified_keys
    mutation_count = len(added_keys) + len(removed_keys) + len(modified_keys)
    if (
        (mutation_count != 1 and not is_replacement)
        or (
            base_compartment is not None
            and (
                base_compartment != candidate_compartment
                or base_ssh_path != candidate_ssh_path
            )
        )
    ):
        _failure(
            "INVALID_COMPUTE_CHANGE",
            "Exactly one VM must be created, updated, replaced, or deleted.",
        )

    declared_nsgs = (
        _declared_nsg_keys_at_base(
            change.repo, change.base_sha, change.environment, change.region
        )
        if added_keys or modified_keys
        else frozenset()
    )
    candidate_identities: list[tuple[str, str]] = []
    for vm_key, vm in candidate_instances.items():
        if vm_key not in added_keys and vm_key not in modified_keys:
            if isinstance(vm, dict):
                networking = vm.get("networking")
                name = vm.get("name")
                hostname = networking.get("hostname") if isinstance(networking, dict) else None
                if isinstance(name, str) and isinstance(hostname, str):
                    candidate_identities.append((name, hostname))
            continue
        name, hostname, referenced_nsgs = _validate_vm_declaration(
            vm_key, vm, region=change.region
        )
        if not referenced_nsgs.issubset(declared_nsgs):
            _failure("UNDECLARED_NSG_REFERENCE", "A VM references an undeclared NSG.")
        candidate_identities.append((name, hostname))
    names = [name for name, _hostname in candidate_identities]
    hostnames = [hostname for _name, hostname in candidate_identities]
    if len(names) != len(set(names)) or len(hostnames) != len(set(hostnames)):
        _failure("INVALID_COMPUTE_CHANGE", "VM identities must be unique.")

    if modified_keys:
        vm_key = next(iter(modified_keys))
        updated_vm = candidate_instances[vm_key]
        previous_vm = base_instances[vm_key]
        changed_fields = sorted(
            field for field in VM_FIELDS
            if not isinstance(previous_vm, dict)
            or previous_vm.get(field) != updated_vm.get(field)
        )
        summary = _vm_summary(
            vm_key, updated_vm, action="update", region=change.region,
            changed_fields=changed_fields,
        )
        operation = "vm-update"
    elif is_replacement:
        old_key = next(iter(removed_keys))
        new_key = next(iter(added_keys))
        summary = {
            "resource_type": "oci-vm-replacement",
            "action": "replace",
            "destructive": True,
            "region": change.region,
            "old": _vm_summary(
                old_key, base_instances[old_key], action="delete", region=change.region
            ),
            "new": _vm_summary(
                new_key, candidate_instances[new_key], action="create", region=change.region
            ),
        }
        operation = "vm-replace"
    elif added_keys:
        vm_key = next(iter(added_keys))
        summary = _vm_summary(
            vm_key, candidate_instances[vm_key], action="create", region=change.region
        )
        operation = "vm-create"
    else:
        vm_key = next(iter(removed_keys))
        summary = _vm_summary(
            vm_key, base_instances[vm_key], action="delete", region=change.region
        )
        operation = "vm-delete"
    return _success_document(change, operation, COMPUTE_VALIDATIONS, summary)


def _network_path(environment: str, region: str) -> str:
    if environment not in {"dev", "test", "uat", "prod"}:
        _failure("INVALID_ENVIRONMENT", "The manifest environment is invalid.")
    if REGION_PATTERN.fullmatch(region) is None:
        _failure("INVALID_REGION", "The manifest region is invalid.")
    return f"oci/{environment}/{region}/network/project-nsgs.json"


def _network_aggregate(
    document: object, *, allow_empty: bool, region: str
) -> tuple[bool | None, tuple[tuple[str, str, str], ...], dict[tuple[str, str, str], Any]]:
    if allow_empty and document == {}:
        return None, (), {}
    if not isinstance(document, dict) or set(document) != {"network_configuration"}:
        _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
    configuration = document.get("network_configuration")
    if (
        not isinstance(configuration, dict)
        or set(configuration)
        != {"default_enable_cis_checks", "network_configuration_categories"}
        or type(configuration.get("default_enable_cis_checks")) is not bool
    ):
        _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
    categories = configuration.get("network_configuration_categories")
    if not isinstance(categories, dict) or not 1 <= len(categories) <= 100:
        _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
    skeleton: list[tuple[str, str, str]] = []
    entries: dict[tuple[str, str, str], Any] = {}
    global_nsg_keys: set[str] = set()
    for category_key, category in categories.items():
        if (
            not isinstance(category_key, str)
            or GENERIC_KEY_RE.fullmatch(category_key) is None
            or not isinstance(category, dict)
            or set(category) != {"inject_into_existing_vcns"}
        ):
            _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
        vcns = category.get("inject_into_existing_vcns")
        if not isinstance(vcns, dict) or not 1 <= len(vcns) <= 100:
            _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
        for vcn_key, vcn in vcns.items():
            if (
                not isinstance(vcn_key, str)
                or RESOURCE_KEY_RE.fullmatch(vcn_key) is None
                or not isinstance(vcn, dict)
                or set(vcn) != {"vcn_id", "network_security_groups"}
                or not _valid_ocid(vcn.get("vcn_id"), "vcn", region)
            ):
                _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
            nsgs = vcn.get("network_security_groups")
            if not isinstance(nsgs, dict) or len(nsgs) > 100:
                _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
            skeleton.append((category_key, vcn_key, vcn["vcn_id"]))
            for nsg_key, nsg in nsgs.items():
                if (
                    not isinstance(nsg_key, str)
                    or RESOURCE_KEY_RE.fullmatch(nsg_key) is None
                    or nsg_key in global_nsg_keys
                ):
                    _failure("INVALID_NSG_CHANGE", "The NSG manifest is invalid.")
                global_nsg_keys.add(nsg_key)
                entries[(category_key, vcn_key, nsg_key)] = nsg
    return (
        configuration["default_enable_cis_checks"],
        tuple(sorted(skeleton)),
        entries,
    )


def _declared_nsg_keys_at_base(
    repo: Path, base_sha: str, environment: str, region: str
) -> frozenset[str]:
    path = _network_path(environment, region)
    entry = run_git(repo, "ls-tree", base_sha, "--", path)
    expected = rb"(?:100644|100755) blob [0-9a-f]{40}\t" + re.escape(path.encode()) + rb"\n"
    if re.fullmatch(expected, entry) is None:
        _failure("INVALID_NSG_MANIFEST", "The NSG manifest is invalid.")
    _default, _skeleton, entries = _network_aggregate(
        strict_json(run_git(repo, "show", f"{base_sha}:{path}")),
        allow_empty=True,
        region=region,
    )
    return frozenset(key[-1] for key in entries)


def _valid_port(value: object) -> bool:
    return type(value) is int and 1 <= value <= 65_535


def _validate_rule_ports(rule: dict[str, Any], protocol: object) -> bool:
    destination = (rule.get("dst_port_min"), rule.get("dst_port_max"))
    source = (rule.get("src_port_min"), rule.get("src_port_max"))
    icmp = (rule.get("icmp_type"), rule.get("icmp_code"))
    if protocol in ("TCP", "UDP"):
        if not all(_valid_port(value) for value in destination):
            return False
        if destination[0] > destination[1]:
            return False
        source_valid = source == (None, None) or (
            all(_valid_port(value) for value in source) and source[0] <= source[1]
        )
        return source_valid and icmp == (None, None)
    if protocol == "ICMP":
        icmp_type, icmp_code = icmp
        icmp_valid = (
            icmp_type is None
            or (type(icmp_type) is int and 0 <= icmp_type <= 255)
        )
        code_valid = (
            icmp_code is None
            or (
                type(icmp_code) is int
                and 0 <= icmp_code <= 255
                and icmp_type is not None
            )
        )
        return destination == (None, None) and source == (None, None) and icmp_valid and code_valid
    return destination == (None, None) and source == (None, None) and icmp == (None, None)


def _validate_nsg_rule(
    rule_key: object,
    rule: object,
    *,
    direction: str,
    declared_nsgs: frozenset[str],
) -> None:
    endpoint = "src" if direction == "ingress" else "dst"
    endpoint_type = f"{endpoint}_type"
    expected_keys = RULE_COMMON_KEYS | {endpoint, endpoint_type}
    if (
        not isinstance(rule_key, str)
        or GENERIC_KEY_RE.fullmatch(rule_key) is None
        or not isinstance(rule, dict)
        or set(rule) != expected_keys
    ):
        _failure("INVALID_NSG_CHANGE", "An NSG rule is invalid.")
    description = rule.get("description")
    protocol = rule.get("protocol")
    value = rule.get(endpoint)
    kind = rule.get(endpoint_type)
    invalid = (
        type(description) is not str
        or not 1 <= len(description) <= 255
        or any(ord(character) < 32 for character in description)
        or protocol not in ("TCP", "UDP", "ICMP", "ALL")
        or type(rule.get("stateless")) is not bool
        or not _validate_rule_ports(rule, protocol)
        or type(value) is not str
    )
    if invalid:
        _failure("INVALID_NSG_CHANGE", "An NSG rule is invalid.")
    if kind == "CIDR_BLOCK":
        try:
            network = ipaddress.ip_network(value, strict=True)
        except ValueError as exc:
            raise ValidationFailure("INVALID_NSG_CHANGE", "An NSG rule is invalid.") from exc
        if str(network) != value:
            _failure("INVALID_NSG_CHANGE", "An NSG rule is invalid.")
    elif kind == "NETWORK_SECURITY_GROUP":
        if RESOURCE_KEY_RE.fullmatch(value) is None or value not in declared_nsgs:
            _failure("UNDECLARED_NSG_REFERENCE", "An NSG rule references an undeclared NSG.")
    elif kind == "SERVICE_CIDR_BLOCK":
        if direction != "egress" or value != "all-services":
            _failure("INVALID_NSG_CHANGE", "An NSG rule is invalid.")
    else:
        _failure("INVALID_NSG_CHANGE", "An NSG rule is invalid.")


def _validate_new_nsg(
    nsg_key: object,
    nsg: object,
    *,
    project: str,
    declared_nsgs: frozenset[str],
) -> str:
    if (
        not isinstance(nsg_key, str)
        or RESOURCE_KEY_RE.fullmatch(nsg_key) is None
        or not isinstance(nsg, dict)
        or set(nsg) != NSG_FIELDS
    ):
        _failure("INVALID_NSG_CHANGE", "The new NSG declaration is invalid.")
    display_name = nsg.get("display_name")
    tags = nsg.get("freeform_tags")
    project_match = re.search(r"project(?P<number>[0-9]+)$", project)
    expected_project = f"proj{project_match.group('number')}" if project_match else ""
    invalid = not _valid_ocid(nsg.get("compartment_id"), "compartment")
    invalid |= (
        type(display_name) is not str
        or RESOURCE_NAME_RE.fullmatch(display_name) is None
        or nsg.get("defined_tags") is not None
        or not isinstance(tags, dict)
        or set(tags) != NSG_TAG_KEYS
    )
    if isinstance(tags, dict):
        invalid |= tags.get("Project") != expected_project
        invalid |= tags.get("Tier") not in ("web", "app", "database", "infra")
        invalid |= tags.get("ManagedBy") != "platform-ci"
    ingress = nsg.get("ingress_rules")
    egress = nsg.get("egress_rules")
    invalid |= not isinstance(ingress, dict) or len(ingress) > 50
    invalid |= not isinstance(egress, dict) or len(egress) > 50
    if invalid:
        _failure("INVALID_NSG_CHANGE", "The new NSG declaration is invalid.")
    assert isinstance(ingress, dict) and isinstance(egress, dict)
    for rule_key, rule in ingress.items():
        _validate_nsg_rule(
            rule_key, rule, direction="ingress", declared_nsgs=declared_nsgs
        )
    for rule_key, rule in egress.items():
        _validate_nsg_rule(
            rule_key, rule, direction="egress", declared_nsgs=declared_nsgs
        )
    assert isinstance(display_name, str)
    return display_name


def validate_nsg_change(change: RepositoryChange) -> dict[str, object]:
    """Validate one additive project NSG change in an existing landing-zone VCN."""
    base_document = strict_json(change.base_content)
    candidate_document = strict_json(change.candidate_content)
    if _has_sensitive_value(candidate_document):
        _failure("INVALID_SECRET_VALUE", "The NSG manifest contains a rejected value.")
    base_default, base_skeleton, base_entries = _network_aggregate(
        base_document, allow_empty=True, region=change.region
    )
    candidate_default, candidate_skeleton, candidate_entries = _network_aggregate(
        candidate_document, allow_empty=False, region=change.region
    )
    added_keys = candidate_entries.keys() - base_entries.keys()
    invalid_change = (
        len(added_keys) != 1
        or any(candidate_entries.get(key) != value for key, value in base_entries.items())
    )
    if base_default is None:
        invalid_change |= len(candidate_skeleton) != 1
    else:
        invalid_change |= (
            base_default != candidate_default or base_skeleton != candidate_skeleton
        )
    if invalid_change:
        _failure("INVALID_NSG_CHANGE", "Exactly one NSG must be added.")
    added_key = next(iter(added_keys))
    declared_nsgs = frozenset(key[-1] for key in candidate_entries)
    new_nsg = candidate_entries[added_key]
    display_name = _validate_new_nsg(
        added_key[-1],
        new_nsg,
        project=change.project,
        declared_nsgs=declared_nsgs,
    )
    if any(
        isinstance(existing, dict) and existing.get("display_name") == display_name
        for existing in base_entries.values()
    ):
        _failure("INVALID_NSG_CHANGE", "NSG identities must be unique.")
    category_key, vcn_key, nsg_key = added_key
    vcn_id = next(
        item[2]
        for item in candidate_skeleton
        if item[0] == category_key and item[1] == vcn_key
    )
    summary = {
        "resource_type": "oci-nsg",
        "action": "create",
        "key": nsg_key,
        "display_name": display_name,
        "region": change.region,
        "compartment_id": new_nsg["compartment_id"],
        "category_key": category_key,
        "vcn_key": vcn_key,
        "vcn_id": vcn_id,
        "tags": new_nsg["freeform_tags"],
        "ingress_rule_count": len(new_nsg["ingress_rules"]),
        "egress_rule_count": len(new_nsg["egress_rules"]),
        "ingress_rules": _summarize_nsg_rules(new_nsg["ingress_rules"], "ingress"),
        "egress_rules": _summarize_nsg_rules(new_nsg["egress_rules"], "egress"),
    }
    return _success_document(change, "nsg-create", NSG_VALIDATIONS, summary)


def _summarize_nsg_rules(rules: dict[str, Any], direction: str) -> list[dict[str, Any]]:
    endpoint = "src" if direction == "ingress" else "dst"
    endpoint_label = "source" if direction == "ingress" else "destination"
    summaries: list[dict[str, Any]] = []
    for name, rule in sorted(rules.items()):
        destination_ports = None
        if rule["dst_port_min"] is not None:
            destination_ports = [rule["dst_port_min"], rule["dst_port_max"]]
        source_ports = None
        if rule["src_port_min"] is not None:
            source_ports = [rule["src_port_min"], rule["src_port_max"]]
        summaries.append(
            {
                "name": name,
                "description": rule["description"],
                "protocol": rule["protocol"],
                "stateless": rule["stateless"],
                endpoint_label: rule[endpoint],
                f"{endpoint_label}_type": rule[f"{endpoint}_type"],
                "destination_ports": destination_ports,
                "source_ports": source_ports,
                "icmp_type": rule["icmp_type"],
                "icmp_code": rule["icmp_code"],
            }
        )
    return summaries


def _success_document(
    change: RepositoryChange,
    operation: str,
    validations: Sequence[str],
    summary: dict[str, object],
) -> dict[str, object]:
    return {"ok": True, "project": change.project, "operation": operation,
        "branch": change.branch, "environment": change.environment,
        "region": change.region,
        "base_sha": change.base_sha, "path": change.path,
        "content_sha256": hashlib.sha256(change.candidate_content).hexdigest(),
        "validations": list(validations), "summary": summary, "diff": change.diff}


def _database_path(environment: str, region: str) -> str:
    if environment not in {"dev", "test", "uat", "prod"}:
        _failure("INVALID_ENVIRONMENT", "The manifest environment is invalid.")
    if REGION_PATTERN.fullmatch(region) is None:
        _failure("INVALID_REGION", "The manifest region is invalid.")
    return f"oci/{environment}/{region}/database/database.json"


def _declared_adb_names(content: bytes) -> frozenset[str]:
    configuration, databases = _adb_configuration(strict_json(content))
    if set(configuration) not in (
            {"autonomous_databases"}, {"default_compartment_id", "autonomous_databases"}):
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    pattern = ADB_STRING_PATTERNS["display_name"]
    names = [entry["display_name"] for entry in databases.values()
             if isinstance(entry, dict) and type(entry.get("display_name")) is str
             and pattern.fullmatch(entry["display_name"]) is not None]
    folded_names = [name.casefold() for name in names]
    if len(folded_names) != len(set(folded_names)):
        _failure("AMBIGUOUS_ADB_DATABASE", "ADB display names are ambiguous.")
    return frozenset(names)


def declared_adb_names(repo: Path, environment: str, region: str) -> frozenset[str]:
    """Read valid ADB display names from the same-region canonical aggregate."""
    path = _database_path(environment, region)
    return _declared_adb_names(_safe_file(repo, path, size_limit=MAX_JSON_BYTES))


def _declared_adb_names_at_base(
    repo: Path, base_sha: str, environment: str, region: str
) -> frozenset[str]:
    path = _database_path(environment, region)
    entry = run_git(repo, "ls-tree", base_sha, "--", path)
    if re.fullmatch(rb"(?:100644|100755) blob [0-9a-f]{40}\t" + re.escape(path.encode()) + rb"\n", entry) is None:
        _failure("INVALID_DATABASE_MANIFEST", "The database manifest is invalid.")
    return _declared_adb_names(run_git(repo, "show", f"{base_sha}:{path}"))


def _validate_lifecycle_change(
    candidate: object, declared_names: frozenset[str]
) -> Sequence[str]:
    if _has_sensitive_value(candidate):
        _failure("INVALID_SECRET_VALUE", "The lifecycle manifest contains a rejected value.")
    if not isinstance(candidate, dict) or set(candidate) != LIFECYCLE_ROOT_KEYS:
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    targets = candidate.get("targets")
    if (candidate.get("operation_type") != "adb-lifecycle"
            or not isinstance(targets, list) or not 1 <= len(targets) <= 20
            or any(not isinstance(target, dict) or set(target) != TARGET_KEYS
                   for target in targets)):
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    names = [target["display_name"] for target in targets]
    folded_names = [name.casefold() for name in names if type(name) is str]
    pattern = ADB_STRING_PATTERNS["display_name"]
    if (any(type(name) is not str or pattern.fullmatch(name) is None for name in names)
            or any(target["action"] not in ("start", "stop") for target in targets)
            or len(set(folded_names)) != len(names)):
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    if not set(names).issubset(declared_names):
        _failure("UNDECLARED_ADB_TARGET", "A lifecycle target is not a declared ADB.")
    return LIFECYCLE_VALIDATIONS


def validate_lifecycle_change(
    repo: Path, candidate: object, environment: str, region: str
) -> Sequence[str]:
    """Validate one bounded start/stop request against declared same-region ADBs."""
    return _validate_lifecycle_change(
        candidate, declared_adb_names(repo, environment, region)
    )


def _render_diff(path: str, base_content: bytes, candidate_content: bytes) -> str:
    base_text = _decode_text(base_content, "INVALID_UTF8", "JSON must be valid UTF-8.")
    candidate_text = _decode_text(
        candidate_content, "INVALID_UTF8", "JSON must be valid UTF-8."
    )
    generated_lines = difflib.unified_diff(
        base_text.splitlines(keepends=True), candidate_text.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}")
    rendered_lines: list[str] = []
    in_hunk = False
    for line in generated_lines:
        if line.startswith("@@"):
            in_hunk = True
        if in_hunk and line[:1] in (" ", "-", "+") and not line.endswith(("\n", "\r")):
            rendered_lines.append(line + "\n")
            rendered_lines.append("\\ No newline at end of file\n")
        else:
            rendered_lines.append(line)
    diff = "".join(rendered_lines)
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        _failure("DIFF_SIZE_LIMIT", "The manifest diff exceeded its size limit.")
    return diff


def parse_origin(value: str) -> tuple[str, str]:
    """Extract the fixed organization and project from an exact GitHub origin."""
    for pattern in _ORIGIN_RES:
        match = pattern.fullmatch(value)
        if match is not None:
            return "__CUSTOMER_ORG__", match.group("project")
    _failure("INVALID_ORIGIN", "The origin repository is not allowed.")


def _safe_file(repo: Path, relative_path: str, *, size_limit: int) -> bytes:
    relative = Path(relative_path)
    if (relative.is_absolute() or not relative.parts or ".." in relative.parts
            or size_limit < 0):
        _failure("INVALID_PATH", "A repository path is invalid.")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    directory_descriptors: list[int] = []
    file_descriptor: int | None = None
    try:
        directory_descriptors.append(os.open(repo, directory_flags))
        for component in relative.parts[:-1]:
            directory_descriptors.append(
                os.open(component, directory_flags, dir_fd=directory_descriptors[-1]))
        file_descriptor = os.open(
            relative.parts[-1], file_flags, dir_fd=directory_descriptors[-1])
        stat_result = os.fstat(file_descriptor)
        if not stat.S_ISREG(stat_result.st_mode):
            _failure("INVALID_PATH", "A repository file is invalid.")
        if stat_result.st_size > size_limit:
            _failure("FILE_SIZE_LIMIT", "A repository file exceeded its size limit.")
        chunks: list[bytes] = []
        remaining = size_limit + 1
        while remaining:
            chunk = os.read(file_descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > size_limit:
            _failure("FILE_SIZE_LIMIT", "A repository file exceeded its size limit.")
        return content
    except ValidationFailure:
        raise
    except (OSError, ValueError) as exc:
        raise ValidationFailure("INVALID_PATH", "A repository file is invalid.") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        for descriptor in reversed(directory_descriptors):
            os.close(descriptor)


def validate_handoff(repo: Path, project: str, environment: str) -> None:
    """Validate the human-only project handoff marker without parsing it as input."""
    layout = project.split("-", 1)[0]
    if (
        (layout == "prod" and environment != "prod")
        or (layout == "nonprod" and environment not in {"dev", "test", "uat"})
    ):
        _failure("INVALID_HANDOFF", "Project environment does not match its repository.")
    content = _safe_file(
        repo,
        f"environments/{environment}/environment_information.md",
        size_limit=MAX_HANDOFF_BYTES,
    )
    text = _decode_text(content, "INVALID_HANDOFF", "Project handoff is invalid.")
    if "<fill during handoff>" in text.casefold():
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    rows: dict[str, list[list[str]]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if not cells or all(re.fullmatch(r"-+", cell) is not None for cell in cells):
            continue
        rows.setdefault(cells[0], []).append(cells[1:])

    def one_row(label: str, length: int) -> list[str] | None:
        matches = rows.get(label, [])
        if len(matches) != 1 or len(matches[0]) != length:
            return None
        return matches[0]

    project_match = re.search(r"project(?P<number>[0-9]+)$", project)
    project_key = project.rsplit("-", 1)[-1]
    short_project = f"proj{project_match.group('number')}" if project_match else ""
    project_row = one_row("Project", 1)
    environment_row = one_row("Environment", 1)
    region_row = one_row("OCI region", 1)
    if (
        project_row is None
        or project_row[0] not in (short_project, project_key, project)
        or environment_row != [environment]
        or region_row is None
        or REGION_PATTERN.fullmatch(region_row[0]) is None
    ):
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    region = region_row[0]
    compartment_ocids = []
    for label in ("App compartment", "DB compartment", "Infra compartment"):
        row = one_row(label, 2)
        if row is None or not _valid_ocid(row[-1], "compartment"):
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
        compartment_ocids.append(row[-1])
    if len(set(compartment_ocids)) != 1:
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    for label, kind in (
        ("Projects VCN", "vcn"),
        ("Web subnet", "subnet"),
        ("App subnet", "subnet"),
        ("DB subnet", "subnet"),
        ("Infra subnet", "subnet"),
    ):
        row = one_row(label, 4)
        if row is None or not _valid_ocid(row[-1], kind, region):
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
        try:
            network = ipaddress.ip_network(row[-2], strict=True)
        except ValueError as exc:
            raise ValidationFailure(
                "INVALID_HANDOFF", "Project handoff is incomplete or invalid."
            ) from exc
        if str(network) != row[-2]:
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")


def _decode_git(output: bytes) -> str:
    return _decode_text(output, "INVALID_GIT_OUTPUT", "Git returned invalid text.")


def _validated_repository(repo: str | os.PathLike[str]) -> Path:
    absolute = Path(os.path.abspath(os.fspath(Path(repo))))
    try:
        resolved = absolute.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ValidationFailure("INVALID_REPOSITORY", "Repository worktree is invalid.") from exc
    if resolved != absolute or not absolute.is_dir():
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    if (absolute / ".git").is_symlink():
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    top_level = _decode_git(run_git(absolute, "rev-parse", "--show-toplevel")).strip()
    if not top_level or Path(os.path.abspath(top_level)) != absolute:
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    return absolute


def _validate_base_ref(base_ref: str) -> None:
    if (BASE_REF_RE.fullmatch(base_ref) is None or ".." in base_ref
            or "//" in base_ref or base_ref.endswith("/")):
        _failure("INVALID_BASE_REF", "The base reference is invalid.")


def _resolve_base_sha(repository: Path, base_ref: str) -> str:
    _validate_base_ref(base_ref)
    base_sha = _decode_git(run_git(repository, "rev-parse", f"{base_ref}^{{commit}}")).strip()
    if SHA_RE.fullmatch(base_sha) is None:
        _failure("INVALID_BASE_SHA", "The base commit is invalid.")
    return base_sha


def _porcelain_path(status_output: bytes) -> str:
    records = status_output.split(b"\0")
    if records[-1] != b"":
        _failure("INVALID_CHANGE", "The repository change is invalid.")
    records = records[:-1]
    if len(records) != 1:
        _failure("INVALID_CHANGE", "Exactly one manifest must be modified.")
    record = records[0]
    if len(record) < 4 or record[2:3] != b" " or record[:2] not in (b" M", b"M ", b"MM"):
        _failure("INVALID_CHANGE", "The manifest must be an existing modified file.")
    try:
        return record[3:].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationFailure("INVALID_CHANGE", "The repository change is invalid.") from exc


def _validate_effective_git_config(repository: Path) -> None:
    output = _decode_git(run_git(repository, "config", "--includes", "--show-scope",
                                 "--name-only", "--list"))
    for raw_record in output.splitlines():
        try:
            raw_scope, raw_key = raw_record.split("\t", 1)
        except ValueError as exc:
            raise ValidationFailure("INVALID_GIT_OUTPUT",
                                    "Git returned invalid configuration data.") from exc
        normalized_scope = raw_scope.strip().casefold()
        normalized_key = raw_key.strip().casefold()
        if normalized_scope == "command" and normalized_key in _SAFE_COMMAND_CONFIG_KEYS:
            continue
        if _EXECUTABLE_GIT_CONFIG_PATTERN.fullmatch(normalized_key):
            _failure("UNSAFE_GIT_CONFIG",
                     "Executable repository Git configuration is not allowed.")


def _validate_preview(change: RepositoryChange, expect_base_sha: str | None,
                      expect_content_sha256: str | None) -> None:
    if expect_base_sha is None:
        return
    if (SHA_RE.fullmatch(expect_base_sha) is None
            or SHA256_RE.fullmatch(expect_content_sha256 or "") is None
            or expect_base_sha != change.base_sha
            or expect_content_sha256
            != hashlib.sha256(change.candidate_content).hexdigest()):
        _failure("PREVIEW_DRIFT", "The expected preview no longer matches.")


def _validate_expected_base(expected_base_sha: str, current_base_sha: str) -> None:
    if SHA_RE.fullmatch(expected_base_sha) is None or expected_base_sha != current_base_sha:
        _failure("PREVIEW_DRIFT", "The expected preview no longer matches.")


def _finalize_change(change: RepositoryChange) -> RepositoryChange:
    strict_json(change.base_content)
    strict_json(change.candidate_content)
    return replace(change, diff=_render_diff(change.path, change.base_content, change.candidate_content))


def collect_change(repo: str | os.PathLike[str], base_ref: str = "origin/main") -> RepositoryChange:
    """Collect one stable read-only canonical manifest modification."""
    repository = _validated_repository(repo)
    origin = _decode_git(run_git(repository, "remote", "get-url", "origin")).strip()
    _organization, project = parse_origin(origin)
    branch = _decode_git(run_git(repository, "branch", "--show-current")).strip()
    if branch == "main" or BRANCH_PATTERN.fullmatch(branch) is None:
        _failure("INVALID_BRANCH", "The current branch is not allowed.")
    base_sha = _resolve_base_sha(repository, base_ref)
    _validate_effective_git_config(repository)
    path = _porcelain_path(run_git(repository, "status", "--porcelain=v1", "-z"))
    path_match = PATH_PATTERN.fullmatch(path)
    if path_match is None:
        _failure("INVALID_MANIFEST_PATH", "The modified manifest path is not allowed.")
    environment = path_match.group("environment")
    validate_handoff(repository, project, environment)
    kind = path_match.group("kind")
    validate_manifest_scope(environment, kind)
    expected_resource = {
        "database/database.json": "adb",
        "compute/compute.json": "vm",
        "network/project-nsgs.json": "nsg",
        "lifecycle_operations/adb-lifecycle.json": "adb",
    }[kind]
    if not branch.startswith(f"agent/{expected_resource}-"):
        _failure("INVALID_BRANCH", "The current branch does not match the manifest resource.")
    candidate_content = _safe_file(repository, path, size_limit=MAX_JSON_BYTES)
    name_status = _decode_git(run_git(
        repository, "diff", "--name-status", "--no-renames", base_sha))
    if name_status != f"M\t{path}\n":
        _failure("INVALID_CHANGE", "Exactly one existing manifest must be modified.")
    run_git(repository, "diff", "--check", base_sha)
    inspection_diff = run_git(repository, "diff", "--no-ext-diff", "--no-textconv",
                              "--no-color", base_sha, "--", path)
    verified_candidate_content = _safe_file(repository, path, size_limit=MAX_JSON_BYTES)
    if verified_candidate_content != candidate_content:
        _failure("WORKTREE_CHANGED", "The worktree changed during validation.")
    if any(
        line == b"GIT binary patch"
        or (line.startswith(b"Binary files ") and line.endswith(b" differ"))
        for line in inspection_diff.splitlines()
    ):
        _failure("BINARY_DIFF", "Binary manifest diffs are not allowed.")
    base_content = run_git(repository, "show", f"{base_sha}:{path}")
    region = path_match.group("region")
    return RepositoryChange(
        repo=repository, project=project, branch=branch, base_ref=base_ref,
        base_sha=base_sha, path=path, environment=environment, region=region,
        kind=kind,
        base_content=base_content, candidate_content=candidate_content, diff="")


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> NoReturn:
        _failure("INVALID_ARGUMENTS", "Command arguments are invalid.")


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--expect-base-sha")
    parser.add_argument("--expect-content-sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        if (arguments.expect_base_sha is None) != (arguments.expect_content_sha256 is None):
            _failure("INVALID_EXPECTATION", "Expected hashes must be provided together.")
        collection_repo: str | os.PathLike[str] = arguments.repo
        collection_base_ref = arguments.base_ref
        if arguments.expect_base_sha is not None:
            repository = _validated_repository(arguments.repo)
            current_base_sha = _resolve_base_sha(repository, arguments.base_ref)
            _validate_expected_base(arguments.expect_base_sha, current_base_sha)
            collection_repo = repository
            collection_base_ref = arguments.expect_base_sha
        change = collect_change(collection_repo, collection_base_ref)
        _validate_preview(change, arguments.expect_base_sha,
                          arguments.expect_content_sha256)
        change = _finalize_change(change)
        if change.kind == "database/database.json":
            document = validate_adb_change(change)
        elif change.kind == "compute/compute.json":
            document = validate_compute_change(change)
        elif change.kind == "network/project-nsgs.json":
            document = validate_nsg_change(change)
        elif change.kind == "lifecycle_operations/adb-lifecycle.json":
            declared_names = _declared_adb_names_at_base(
                change.repo,
                change.base_sha,
                change.environment,
                change.region,
            )
            candidate = strict_json(change.candidate_content)
            validations = _validate_lifecycle_change(
                candidate, declared_names
            )
            summary = {
                "resource_type": "oci-adb",
                "action": "lifecycle",
                "environment": change.environment,
                "region": change.region,
                "targets": candidate["targets"],
            }
            document = _success_document(
                change, "adb-lifecycle", validations, summary
            )
        else:
            _failure("UNSUPPORTED_MANIFEST", "Manifest semantics are not available.")
        sys.stdout.write(json.dumps(document, ensure_ascii=True, separators=(",", ":")) + "\n")
        return 0
    except ValidationFailure as error:
        return emit_error(error)
    except Exception:
        return emit_error(ValidationFailure("INTERNAL_ERROR", "Validation failed safely."))


if __name__ == "__main__":
    raise SystemExit(main())
