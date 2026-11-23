#!/usr/bin/env python3
"""Prepare private Terraform variables from reviewed manifests and native secret references."""

import base64
import binascii
from copy import deepcopy
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from validate_adb_secrets import read_vault_json, trusted_scope, secret_references, validate_secret_metadata


# Authoritative placeholder grammar. Project GitOps intentionally performs no
# duplicate resource-specific validation, so this runtime check is the boundary
# that prevents unresolved tokens from reaching Terraform.
PLACEHOLDER_RE = re.compile(r"(?<![A-Za-z0-9_])(__[A-Za-z0-9_]+__)(?![A-Za-z0-9_])")
ALLOWED_ENVIRONMENTS = {"dev", "test", "uat", "prod"}
REGIONAL_SECRET_RE = re.compile(r"ocid1\.vaultsecret\.oc1\.([a-z0-9-]+)\.[A-Za-z0-9._-]+")


def find_placeholders(value: Any) -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            found.update(find_placeholders(key))
            found.update(find_placeholders(item))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(find_placeholders(item))
        return found
    if isinstance(value, str):
        return set(PLACEHOLDER_RE.findall(value))
    return set()



def resolve_azure_adb_secrets(data: Any, used: set[str], validated: set[str], vault_region: str) -> Any:
    """Translate the project-facing OCID contract into the Azure module input."""
    prepared = deepcopy(data)
    if not isinstance(prepared, dict) or "oracle_autonomous_databases" not in prepared:
        return prepared
    databases = prepared["oracle_autonomous_databases"]
    if not isinstance(databases, dict):
        raise ValueError("Azure ADB configuration must contain a database map")
    references = []
    for database in databases.values():
        if not isinstance(database, dict) or "admin_password" in database:
            raise ValueError("Azure ADB requires admin_password_secret_id; passwords and binding tokens are unsupported")
        secret_id = database.get("admin_password_secret_id")
        match = REGIONAL_SECRET_RE.fullmatch(secret_id) if isinstance(secret_id, str) else None
        if not match:
            raise ValueError("Azure ADB requires a regional OCI Vault secret OCID in admin_password_secret_id")
        if secret_id in used:
            raise ValueError("Each Azure ADB must use a distinct Vault secret OCID")
        used.add(secret_id)
        if secret_id not in validated:
            raise ValueError("Secret metadata must be validated before reading content")
        references.append((database, secret_id, vault_region))
    for database, secret_id, vault_region in references:
        bundle = read_vault_json(
            ["secrets", "secret-bundle", "get", "--secret-id", secret_id, "--stage", "CURRENT"], vault_region)
        try:
            content = bundle["secret-bundle-content"]
            if content["content-type"] != "BASE64":
                raise ValueError("Unsupported Vault content type")
            encoded = content["content"]
            value = base64.b64decode(encoded, validate=True).decode("utf-8")
            if not value.strip() or "\x00" in value or find_placeholders(value):
                raise ValueError("Vault content must be nonempty text without runtime tokens")
        except (KeyError, TypeError, UnicodeError, binascii.Error) as exc:
            raise ValueError("Cannot retrieve valid text from Vault") from exc
        mask_secret_values({"password": value, "encoded": encoded})
        del database["admin_password_secret_id"]
        database["admin_password"] = value
    return prepared


def mask_secret_values(secret_values: dict[str, str]) -> None:
    """Mask each JSON member before tools can print resolved values in Actions."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for value in sorted(set(secret_values.values())):
        # stdout is reserved for the caller's Terraform -var-file arguments.
        escaped = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::add-mask::{escaped}", file=sys.stderr)


def terraform_json_files(config_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in config_dir.rglob("*.json")
        if not {"ansible", "lifecycle_operations"}.intersection(path.relative_to(config_dir).parts)
    )


def prepare_file(source: Path, destination: Path, data: Any) -> None:
    placeholders = find_placeholders(data)
    if placeholders:
        raise ValueError(f"{source}: unresolved placeholders must be rendered before publication")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "Usage: prepare_var_files.py <config-dir> <output-dir> <environment> <cloud> <region>",
            file=sys.stderr,
        )
        return 2

    config_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    environment = sys.argv[3].lower()
    cloud, region = sys.argv[4:6]
    if environment not in ALLOWED_ENVIRONMENTS:
        print(f"Unsupported deployment environment: {environment}", file=sys.stderr)
        return 1
    if cloud not in {"oci", "azure", "gcp"} or not re.fullmatch(r"[A-Za-z0-9._-]+", region):
        print("Unsupported cloud or region", file=sys.stderr)
        return 1
    if output_dir == config_dir or output_dir in config_dir.parents or config_dir in output_dir.parents:
        print("Output directory must be separate from configuration", file=sys.stderr)
        return 1
    if not config_dir.is_dir():
        print(f"Config directory not found: {config_dir}", file=sys.stderr)
        return 1

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, mode=0o700)
    os.umask(0o077)

    prepared_files: list[Path] = []
    try:
        sources = terraform_json_files(config_dir)
        documents = {}
        used_secrets: set[str] = set()
        for source in sources:
            try:
                data = json.loads(source.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}: invalid JSON") from exc
            if find_placeholders(data):
                raise ValueError(f"{source}: unresolved placeholders must be rendered before publication")
            documents[source] = data
        references = [secret for data in documents.values() for secret in secret_references(data)]
        scope = None
        if references:
            scope = trusted_scope(config_dir, environment)
            if cloud == "oci" and region != scope["region"]:
                raise ValueError("OCI deployment region does not match the trusted handoff")
            validate_secret_metadata(references, scope)
        for source in sources:
            destination = output_dir / source.relative_to(config_dir)
            data = documents[source]
            if cloud == "azure":
                data = resolve_azure_adb_secrets(data, used_secrets, set(references), scope["region"] if scope else "")
            prepare_file(source, destination, data)
            prepared_files.append(destination)
    except (ValueError, OSError, UnicodeError) as exc:
        shutil.rmtree(output_dir)
        print(f"ERROR: {exc}" if isinstance(exc, ValueError) else "ERROR: Cannot prepare variable files", file=sys.stderr)
        return 1

    print(" ".join(f"-var-file {shlex.quote(str(path))}" for path in prepared_files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
