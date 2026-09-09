#!/usr/bin/env python3
"""Fail-closed, read-only validation of one governed project repository change."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, NoReturn, Sequence


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

MAX_HANDOFF_BYTES = 65_536

BRANCH_PATTERN = re.compile(
    r"^agent/(?:adb|vm|nsg)-[a-z0-9](?:[a-z0-9-]{0,62})$"
)
PATH_PATTERN = re.compile(
    r"^(?P<cloud>oci|azure|gcp)/(?P<environment>dev|test|uat|prod)/"
    r"(?P<region>[a-z0-9-]+)/(?P<kind>database/database\.json|"
    r"compute/compute\.json|network/project-nsgs\.json|"
    r"workloads/adb\.json|lifecycle_operations/adb-lifecycle\.json)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BASE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_EXECUTABLE_GIT_CONFIG_PATTERN = re.compile(
    r"^(?:diff\..+\.(?:command|textconv)|"
    r"filter\..+\.(?:clean|smudge|process))$")
_SAFE_COMMAND_CONFIG_KEYS = frozenset({"core.fsmonitor", "core.hookspath", "core.pager"})
LIFECYCLE_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "state-backed-target", "start-stop-only")
LIFECYCLE_CLEAR_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "clear-lifecycle")
COMPUTE_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "governed-vm-change",
    "declared-nsg-references",
)
NSG_VALIDATIONS = (
    "repository", "one-file-diff", "strict-json", "governed-nsg-change", "existing-vcn-only",
)
LIFECYCLE_ROOT_KEYS = frozenset(
    {"operation_type", "database_compartment_id", "targets"}
)
TARGET_KEYS = frozenset(
    {"display_name", "action", "wait_for_state", "timeout_minutes"}
)
REQUIRED_TARGET_KEYS = frozenset({"display_name", "action"})
RESOURCE_KEY_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,127}$")
RESOURCE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
SHAPE_RE = re.compile(r"^VM\.[A-Za-z0-9][A-Za-z0-9.]{1,126}$")
GENERIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FIXED_SSH_PUBLIC_KEY_PATH = "/home/github-runner/.ssh/oci_vm_key.pub"
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


from validation.common import (
    RepositoryChange,
    ValidationFailure,
    MAX_JSON_BYTES,
    MAX_NSG_IDS,
    ADB_STRING_PATTERNS,
    PROJECT_PATTERN,
    REGION_PATTERN,
    decode_text as _decode_text,
    failure as _failure,
    has_sensitive_value as _has_sensitive_value,
    run_git,
    sanitize_text,
    strict_json,
    valid_ocid as _valid_ocid,
)


def validate_workload_compartment(
    compartments: dict[str, str],
    role: str,
    compartment_id: object,
) -> None:
    """Require an OCI workload to use its TBAC handoff target."""
    expected = compartments.get(role)
    if expected is None or compartment_id != expected:
        _failure(
            "INVALID_WORKLOAD_COMPARTMENT",
            f"The OCI workload must use the {role} TBAC compartment.",
        )


def validate_manifest_scope(environment: str, kind: str) -> None:
    """Keep lifecycle scope aligned with the canonical V2 manifest paths."""
    _ = environment, kind


def emit_error(error: ValidationFailure) -> int:
    """Emit exactly one stable JSON error document to stdout."""
    code = error.code if re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", error.code) else "VALIDATION_ERROR"
    document = {"ok": False, "error": {"code": code, "message": sanitize_text(error.message)}}
    sys.stdout.write(json.dumps(document, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 2


from validation.external import validate_external_change


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
        candidate_document, allow_empty=True
    )
    for compartment_id in (base_compartment, candidate_compartment):
        if compartment_id is not None:
            validate_workload_compartment(
                change.workload_compartments, "application", compartment_id
            )
    for instance in candidate_instances.values():
        if isinstance(instance, dict):
            validate_workload_compartment(
                change.workload_compartments,
                "application",
                instance.get("compartment_id"),
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
            candidate_compartment is not None
            and base_compartment is not None
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
    expected_project = project.split("-", 1)[1]
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
    """Validate one project NSG creation or deletion in an existing VCN."""
    base_document = strict_json(change.base_content)
    candidate_document = strict_json(change.candidate_content)
    if _has_sensitive_value(candidate_document):
        _failure("INVALID_SECRET_VALUE", "The NSG manifest contains a rejected value.")
    base_default, base_skeleton, base_entries = _network_aggregate(
        base_document, allow_empty=True, region=change.region
    )
    candidate_default, candidate_skeleton, candidate_entries = _network_aggregate(
        candidate_document, allow_empty=True, region=change.region
    )
    for entry in [*base_entries.values(), *candidate_entries.values()]:
        if isinstance(entry, dict):
            validate_workload_compartment(
                change.workload_compartments,
                "infrastructure",
                entry.get("compartment_id"),
            )
    added_keys = candidate_entries.keys() - base_entries.keys()
    removed_keys = base_entries.keys() - candidate_entries.keys()
    invalid_change = (
        len(added_keys) + len(removed_keys) != 1
        or any(
            candidate_entries[key] != base_entries[key]
            for key in base_entries.keys() & candidate_entries.keys()
        )
    )
    if candidate_default is None:
        invalid_change |= len(removed_keys) != 1
    elif base_default is None:
        invalid_change |= len(candidate_skeleton) != 1
    else:
        invalid_change |= (
            base_default != candidate_default or base_skeleton != candidate_skeleton
        )
    if invalid_change:
        _failure("INVALID_NSG_CHANGE", "Exactly one NSG must be added or deleted.")

    if removed_keys:
        removed_key = next(iter(removed_keys))
        removed_nsg = base_entries[removed_key]
        display_name = (
            removed_nsg.get("display_name", removed_key[-1])
            if isinstance(removed_nsg, dict)
            else removed_key[-1]
        )
        return _success_document(
            change,
            "nsg-delete",
            NSG_VALIDATIONS,
            {
                "resource_type": "oci-nsg",
                "action": "delete",
                "key": removed_key[-1],
                "display_name": display_name,
                "region": change.region,
                "destructive": True,
            },
        )

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


from validation.oci_adb import validate_adb_change


def _database_path(environment: str, region: str) -> str:
    if environment not in {"dev", "test", "uat", "prod"}:
        _failure("INVALID_ENVIRONMENT", "The manifest environment is invalid.")
    if REGION_PATTERN.fullmatch(region) is None:
        _failure("INVALID_REGION", "The manifest region is invalid.")
    return f"oci/{environment}/{region}/database/database.json"


def _validate_lifecycle_change(candidate: object) -> Sequence[str]:
    if _has_sensitive_value(candidate):
        _failure("INVALID_SECRET_VALUE", "The lifecycle manifest contains a rejected value.")
    if candidate == {}:
        return LIFECYCLE_CLEAR_VALIDATIONS
    if not isinstance(candidate, dict) or set(candidate) != LIFECYCLE_ROOT_KEYS:
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    targets = candidate.get("targets")
    if (candidate.get("operation_type") != "adb-lifecycle"
            or not isinstance(targets, list) or not 1 <= len(targets) <= 20
            or any(not isinstance(target, dict)
                   or not REQUIRED_TARGET_KEYS <= set(target) <= TARGET_KEYS
                   for target in targets)):
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    names = [target["display_name"] for target in targets]
    folded_names = [name.casefold() for name in names if type(name) is str]
    pattern = ADB_STRING_PATTERNS["display_name"]
    if (any(type(name) is not str or pattern.fullmatch(name) is None for name in names)
            or any(target["action"] not in ("start", "stop") for target in targets)
            or any("wait_for_state" in target
                   and type(target["wait_for_state"]) is not bool for target in targets)
            or any("timeout_minutes" in target
                   and (type(target["timeout_minutes"]) is not int
                        or target["timeout_minutes"] < 1) for target in targets)
            or len(set(folded_names)) != len(names)):
        _failure("INVALID_LIFECYCLE_CHANGE", "The lifecycle manifest is invalid.")
    return LIFECYCLE_VALIDATIONS


from validation.preview import render_diff as _render_diff


from validation.handoff import safe_file as _safe_file, validate_handoff


from validation.repository import (
    collect_change,
    finalize_change as _finalize_change,
    resolve_base_sha as _resolve_base_sha,
    validate_expected_base as _validate_expected_base,
    validate_preview as _validate_preview,
    validated_repository as _validated_repository,
)


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
        cloud = change.path.split("/", 1)[0]
        if cloud in {"azure", "gcp"}:
            workload_kind = "compute" if change.kind == "compute/compute.json" else "adb"
            handoff_content = _safe_file(
                change.repo,
                f"environments/{change.environment}/environment_information.md",
                size_limit=MAX_HANDOFF_BYTES,
            )
            action = validate_external_change(
                cloud,
                workload_kind,
                change.environment,
                strict_json(change.base_content),
                strict_json(change.candidate_content),
                _decode_text(handoff_content, "INVALID_HANDOFF", "Project handoff is invalid."),
            )
            document = _success_document(
                change,
                f"{cloud}-{workload_kind}",
                ("repository", "one-file-diff", "one-resource-change", "strict-json", "selected-cloud-handoff", "private-only"),
                {"resource_type": f"{cloud}-{workload_kind}", "action": action,
                 "environment": change.environment, "region": change.region},
            )
        elif change.kind == "database/database.json":
            document = validate_adb_change(change)
        elif change.kind == "compute/compute.json":
            document = validate_compute_change(change)
        elif change.kind == "network/project-nsgs.json":
            document = validate_nsg_change(change)
        elif change.kind == "lifecycle_operations/adb-lifecycle.json":
            candidate = strict_json(change.candidate_content)
            validations = _validate_lifecycle_change(candidate)
            if candidate == {}:
                summary = {
                    "resource_type": "oci-adb",
                    "action": "clear-lifecycle",
                    "environment": change.environment,
                    "region": change.region,
                }
            else:
                validate_workload_compartment(
                    change.workload_compartments,
                    "database",
                    candidate["database_compartment_id"],
                )
                summary = {
                    "resource_type": "oci-adb",
                    "action": "lifecycle",
                    "environment": change.environment,
                    "region": change.region,
                    "compartment_id": candidate["database_compartment_id"],
                    "targets": candidate["targets"],
                }
            document = _success_document(
                change, "adb-lifecycle", validations, summary
            )
        else:
            _failure("UNSUPPORTED_MANIFEST", "Manifest semantics are not available.")
        document["catalog"] = {
            "repository": f"{change.organization}/gitops-templates",
            "revision": "main",
        }
        sys.stdout.write(json.dumps(document, ensure_ascii=True, separators=(",", ":")) + "\n")
        return 0
    except ValidationFailure as error:
        return emit_error(error)
    except Exception:
        return emit_error(ValidationFailure("INTERNAL_ERROR", "Validation failed safely."))


if __name__ == "__main__":
    raise SystemExit(main())
