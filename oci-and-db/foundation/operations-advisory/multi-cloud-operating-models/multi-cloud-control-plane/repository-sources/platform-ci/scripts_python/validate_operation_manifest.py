#!/usr/bin/env python3
"""Fail-closed validation of one lifecycle operation manifest.

Project teams author these files, and Ansible loads them as extra variables,
which outrank inventory and play variables. Only the keys an operation defines
may appear, so a manifest cannot set platform variables such as the resolved
OCID or the execution mode.
"""

import json
import re
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

# These values are exposed to the platform-owned deploy-agent playbook. Keep
# agent_type safe for its marker filename and agent_version safe for logs and
# marker content; neither value may select a command, URL, playbook, or path.
AGENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
AGENT_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


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

    if operation_type == "deploy-agent":
        agent_type = document.get("agent_type")
        if not isinstance(agent_type, str) or not AGENT_TYPE_RE.fullmatch(agent_type):
            fail(
                "agent_type must be a 1-63 character lowercase identifier "
                "using letters, digits, and hyphens"
            )
        agent_version = document.get("agent_version")
        if not isinstance(agent_version, str) or not AGENT_VERSION_RE.fullmatch(agent_version):
            fail(
                "agent_version must be a 1-64 character identifier using "
                "letters, digits, dots, underscores, pluses, and hyphens"
            )

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
