"""Read `terraform output` and merge the created OCIDs back into the config.

After `provision` applies the stack, Terraform knows the real subnet, VCN,
Database Management private endpoint, and any provisioned database OCIDs. This
closes the loop so `enable`/`configure` pick them up without manual copy-paste.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from dbman_opsi.config import ConfigError, EnablementConfig, Target, validate_config
from dbman_opsi.runner import CommandRunner


def read_terraform_outputs(terraform_dir: str | Path, runner: CommandRunner) -> dict[str, Any]:
    result = runner.run(["terraform", "output", "-json"], cwd=Path(terraform_dir))
    data = result.json()
    return data if isinstance(data, dict) else {}


def _value(outputs: dict[str, Any], key: str) -> Any:
    entry = outputs.get(key)
    if isinstance(entry, dict):
        return entry.get("value")
    return None


def merge_outputs_into_config(config: EnablementConfig, outputs: dict[str, Any]) -> tuple[EnablementConfig, list[str]]:
    """Return a new config with Terraform-created OCIDs filled in, plus a change log."""

    changes: list[str] = []
    network = config.network
    subnet_id = _value(outputs, "subnet_ocid")
    vcn_id = _value(outputs, "vcn_ocid")
    if subnet_id and subnet_id != network.subnet_id:
        network = replace(network, subnet_id=subnet_id)
        changes.append("network.subnet_id")
    if vcn_id and vcn_id != network.vcn_id:
        network = replace(network, vcn_id=vcn_id)
        changes.append("network.vcn_id")

    pe_id = _value(outputs, "db_management_private_endpoint_ocid")
    dbcs_ids = _value(outputs, "provisioned_dbcs_ids") or {}
    adb_ids = _value(outputs, "provisioned_autonomous_database_ids") or {}

    new_targets: list[Target] = []
    for target in config.targets:
        updates: dict[str, Any] = {}
        if pe_id and target.kind in {"dbcs", "exadata"} and not target.private_endpoint_id:
            updates["private_endpoint_id"] = pe_id
        provisioned_id = dbcs_ids.get(target.name) if target.kind == "dbcs" else adb_ids.get(target.name)
        if target.provision and target.kind == "dbcs" and provisioned_id and not target.db_system_id:
            updates["db_system_id"] = provisioned_id
        if target.provision and target.kind != "dbcs" and provisioned_id and not target.resource_id:
            updates["resource_id"] = provisioned_id
        if updates:
            changes.append(f"target[{target.name}]: {', '.join(sorted(updates))}")
            target = replace(target, **updates)
        new_targets.append(target)

    merged = replace(config, network=network, targets=tuple(new_targets))
    return merged, changes


def validate_merged_config(config: EnablementConfig) -> None:
    """Raise ConfigError when imported Terraform values break config validation."""

    problems = validate_config(config)
    if problems:
        raise ConfigError(problems)
