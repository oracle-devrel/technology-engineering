"""Terraform rendering and execution helpers."""

from __future__ import annotations

import json
from pathlib import Path

from dbman_opsi.config import EnablementConfig
from dbman_opsi.iam import terraform_policy_documents
from dbman_opsi.runner import CommandRunner


def render_tfvars(config: EnablementConfig) -> dict[str, object]:
    target_payload = [
        {
            "kind": target.kind,
            "name": target.name,
            "resource_id": target.resource_id,
            "provision": target.provision,
            "management_type": target.management_type,
        }
        for target in config.targets
    ]
    return {
        "tenancy_ocid": config.tenancy_id,
        "compartment_ocid": config.compartment_id,
        "region": config.region,
        "config_file_profile": config.profile,
        "create_test_network": config.network.create_test_network,
        "vcn_ocid": config.network.vcn_id,
        "subnet_ocid": config.network.subnet_id,
        "test_vcn_cidr": config.network.cidr_block,
        "test_subnet_cidr": config.network.subnet_cidr_block,
        "create_vault": config.vault.create_vault,
        "vault_ocid": config.vault.vault_id,
        "key_ocid": config.vault.key_id,
        "targets": target_payload,
        **terraform_policy_documents(config),
    }


def write_tfvars(config: EnablementConfig, terraform_dir: str | Path | None = None) -> Path:
    directory = Path(terraform_dir or config.terraform_dir)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "terraform.tfvars.json"
    destination.write_text(json.dumps(render_tfvars(config), indent=2, sort_keys=True), encoding="utf-8")
    return destination


def run_terraform(config: EnablementConfig, runner: CommandRunner) -> None:
    tf_dir = Path(config.terraform_dir)
    write_tfvars(config, tf_dir)
    runner.run(["terraform", "init"], cwd=tf_dir)
    runner.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir)
