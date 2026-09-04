#!/usr/bin/env python3
"""Fail-closed validation of one lifecycle operation manifest.

Project teams author these files, and Ansible loads them as extra variables,
which outrank inventory and play variables. Only the keys an operation defines
may appear, so a manifest cannot set platform variables such as the resolved
OCID or the execution mode.
"""

import json
import sys
from pathlib import Path

# Extension point: a new operation adds its entry to both maps here, alongside
# the catalog template, the allow-listed playbook, and the inventory builder.
ALLOWED_KEYS = {
    "adb-lifecycle": {"operation_type", "database_compartment_id", "targets"},
    "deploy-agent": {"operation_type", "agent_type", "agent_version", "targets"},
}

ALLOWED_TARGET_KEYS = {
    "adb-lifecycle": {"display_name", "action", "wait_for_state", "timeout_minutes"},
    "deploy-agent": {"display_name"},
}


def fail(message: str) -> "NoReturn":
    print(f"❌ Operation manifest rejected: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate(document: object) -> str:
    if not isinstance(document, dict):
        fail("the manifest must be a JSON object")
    operation_type = document.get("operation_type")
    if operation_type not in ALLOWED_KEYS:
        fail(f"unsupported operation_type: {operation_type!r}")

    unknown = sorted(set(document) - ALLOWED_KEYS[operation_type])
    if unknown:
        fail(
            f"{operation_type} does not accept {', '.join(unknown)}. "
            "Only the fields documented for this operation are allowed."
        )

    targets = document.get("targets")
    if not isinstance(targets, list) or not targets:
        fail("targets must be a non-empty list")

    allowed_target_keys = ALLOWED_TARGET_KEYS[operation_type]
    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            fail(f"targets[{index}] must be an object")
        unknown = sorted(set(target) - allowed_target_keys)
        if unknown:
            fail(f"targets[{index}] does not accept {', '.join(unknown)}")
        if not isinstance(target.get("display_name"), str) or not target["display_name"]:
            fail(f"targets[{index}].display_name must be a non-empty string")

    if operation_type == "adb-lifecycle":
        for index, target in enumerate(targets):
            if target.get("action") not in {"start", "stop"}:
                fail(f"targets[{index}].action must be start or stop")

    return operation_type


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_operation_manifest.py <operation-file>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    operation_type = validate(document)
    print(f"✅ {operation_type} manifest accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
