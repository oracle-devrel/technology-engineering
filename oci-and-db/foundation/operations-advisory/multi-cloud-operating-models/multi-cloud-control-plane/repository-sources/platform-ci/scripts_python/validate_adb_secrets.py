#!/usr/bin/env python3
"""Validate all ADB secret metadata against the trusted environment handoff.

This scopes the governed workflow. The shared runner retains its IAM identity
across runs; this check does not create IAM isolation between projects.
"""
import json
import os
import re
import subprocess
from pathlib import Path

def read_vault_json(arguments: list[str], region: str) -> dict:
    """Keep all OCI responses and diagnostics out of published output."""
    try:
        response = subprocess.run(
            ["oci", *arguments, "--region", region, "--auth", "instance_principal",
             "--output", "json", "--connection-timeout", "10", "--read-timeout", "20", "--max-retries", "3"],
            capture_output=True, text=True, timeout=150, check=False,
        )
        if response.returncode != 0:
            raise ValueError("Cannot read the approved Vault secret using Instance Principal")
        data = json.loads(response.stdout)["data"]
        if not isinstance(data, dict):
            raise ValueError("Invalid Vault response")
        return data
    except (OSError, subprocess.TimeoutExpired, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot read the approved Vault secret using Instance Principal") from exc



def regional_ocid(value, kind, region):
    aliases = json.loads(Path(__file__).with_name("oci-region-codes.json").read_text())
    match = re.fullmatch(rf"ocid1\.{kind}\.oc1\.([a-z0-9-]+)\.[A-Za-z0-9_.-]+", str(value))
    if match is None or aliases.get(match[1], match[1]) != region:
        raise ValueError("A secret scope reference does not match the OCI handoff region")


def parse_handoff(text, environment, repository):
    rows = {}
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            rows.setdefault(cells[0], []).append(cells)
    def row(label, count):
        found = rows.get(label, [])
        if len(found) != 1 or len(found[0]) != count:
            raise ValueError("The trusted handoff is incomplete or ambiguous")
        return found[0]
    project = repository.split("/")[-1]
    prefix = "prod-" if environment == "prod" else "nonprod-"
    if not project.startswith(prefix):
        raise ValueError("The handoff repository does not match its environment")
    name = project[len(prefix):]
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", name):
        raise ValueError("Invalid handoff project")
    if (row("Handoff schema", 2)[1] != "5" or row("Environment", 2)[1] != environment
        or row("Project", 2)[1] != name):
        raise ValueError("Handoff 5 for this project and environment is required; legacy handoffs are unsupported")
    region = row("OCI region", 2)[1]
    if not re.fullmatch(r"[a-z]{2}-[a-z]+-[0-9]+", region):
        raise ValueError("Invalid OCI handoff region")
    token = f"LZ-{environment.upper()}-{name.upper()}"
    expected = {"Vault": f"VLT-LZ-{environment.upper()}-WORKLOADS-KEY",
                "Vault key": f"KMS-{token}-KEY", "Secrets compartment": f"CMP-{token}-DB-KEY",
                "DB compartment": f"CMP-{token}-DB-KEY"}
    values = {}
    for label, key in expected.items():
        item = row(label, 3)
        if item[1] != key:
            raise ValueError("The handoff logical reference does not match its project scope")
        values[label] = item[2]
    if (values["DB compartment"] != values["Secrets compartment"]
        or not re.fullmatch(r"ocid1\.compartment\.oc1\.\.[A-Za-z0-9_.-]+", values["Secrets compartment"])):
        raise ValueError("Secrets must belong to the project Database compartment")
    regional_ocid(values["Vault"], "vault", region)
    regional_ocid(values["Vault key"], "key", region)
    return {"region": region, "vault": values["Vault"], "vault_key": values["Vault key"],
            "secrets_compartment": values["Secrets compartment"]}


def trusted_scope(config_dir, environment):
    revision = os.environ.get("MCCP_HANDOFF_REF", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("A trusted immutable handoff revision and project repository are required")
    try:
        result = subprocess.run(["git", "-C", str(config_dir), "show",
            f"{revision}:environments/{environment}/environment_information.md"],
            capture_output=True, text=True, timeout=20, check=False)
        if result.returncode:
            raise ValueError("Cannot read the trusted environment handoff")
        return parse_handoff(result.stdout, environment, repository)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("Cannot read the trusted environment handoff") from exc


def secret_references(value):
    references = []
    if isinstance(value, dict):
        if "admin_password_secret_id" in value:
            secret = value["admin_password_secret_id"]
            if not isinstance(secret, str):
                raise ValueError("ADB requires a native OCI Vault secret OCID")
            references.append(secret)
        for item in value.values():
            references.extend(secret_references(item))
    elif isinstance(value, list):
        for item in value:
            references.extend(secret_references(item))
    return references


def validate_secret_metadata(references, scope):
    if len(set(references)) != len(references):
        raise ValueError("Each ADB must use a distinct Vault secret OCID")
    # Validate every OCID before querying, then every metadata response before
    # any caller may retrieve a CURRENT bundle or initialize Terraform.
    for secret in references:
        regional_ocid(secret, "vaultsecret", scope["region"])
    for secret in references:
        data = read_vault_json(["vault", "secret", "get", "--secret-id", secret], scope["region"])
        expected = {"id": secret, "compartment-id": scope["secrets_compartment"],
                    "vault-id": scope["vault"], "key-id": scope["vault_key"], "lifecycle-state": "ACTIVE"}
        if any(data.get(field) != value for field, value in expected.items()):
            raise ValueError("ADB secret metadata does not match the approved project scope or usable state")
