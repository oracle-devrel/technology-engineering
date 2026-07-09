"""Enable the Data Safe (security) pillar for configured targets.

Unlike Database Management and Ops Insights, Data Safe registration is a separate
``target-database`` resource that connects to the database through a Data Safe
private endpoint using a database service account. This module:

1. ensures a Data Safe private endpoint exists in the DB subnet,
2. builds the registration payloads (database details, connection option,
   credentials) as ``file://`` JSON so the password never appears on argv, and
3. registers the target database, returning its OCID.

Credentials are supplied at call time by a provider callback (the CLI prompts for
them; tests inject a fake) and are written only to a 0600 temp file that is
deleted in a ``finally`` block — they are never persisted to the config.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.oci_cli import OciCli

# (user_name, password) for the Data Safe service account on a given target.
CredentialProvider = Callable[[Target], "tuple[str, str]"]

DATA_SAFE_KINDS = {"dbcs", "exadata", "autonomous"}


@dataclass(frozen=True)
class DataSafeDecision:
    target: str
    status: str  # enabled | ready | skipped | blocked
    detail: str
    target_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "status": self.status, "detail": self.detail, "target_id": self.target_id}


def data_safe_database_details(target: Target) -> dict[str, Any]:
    """Build the ``databaseDetails`` payload for a target's database type."""

    if target.kind == "autonomous":
        return {
            "databaseType": "AUTONOMOUS_DATABASE",
            "infrastructureType": "ORACLE_CLOUD",
            "autonomousDatabaseId": target.resource_id,
        }
    # Base Database / Exadata cloud service: registered against the DB system and
    # the (PDB) service name; the service name distinguishes a PDB target.
    return {
        "databaseType": "DATABASE_CLOUD_SERVICE",
        "infrastructureType": "ORACLE_CLOUD",
        "dbSystemId": target.db_system_id,
        "serviceName": target.service_name,
        "listenerPort": 1521,
    }


def _connection_option(target: Target) -> dict[str, Any]:
    return {
        "connectionType": "PRIVATE_ENDPOINT",
        "datasafePrivateEndpointId": target.data_safe_private_endpoint_id,
    }


def _missing_registration_fields(target: Target) -> list[str]:
    if target.kind == "autonomous":
        required = {"resource_id": target.resource_id}
    else:
        required = {
            "db_system_id": target.db_system_id,
            "service_name": target.service_name,
            "data_safe_private_endpoint_id": target.data_safe_private_endpoint_id,
        }
    return [name for name, value in required.items() if not value]


class DataSafeService:
    def __init__(self, oci: OciCli, credential_provider: CredentialProvider | None = None) -> None:
        self.oci = oci
        self.credential_provider = credential_provider

    def enable_all(self, config: EnablementConfig) -> list[DataSafeDecision]:
        decisions: list[DataSafeDecision] = []
        for target in config.targets:
            if not target.wants("datasafe"):
                continue
            decisions.append(self.enable_target(target, config))
        return decisions

    def ensure_private_endpoint(self, target: Target, config: EnablementConfig) -> str | None:
        """Return a Data Safe PE OCID, creating one in the DB subnet if needed."""

        if target.data_safe_private_endpoint_id:
            return target.data_safe_private_endpoint_id
        subnet_id = config.network.subnet_id
        vcn_id = config.network.vcn_id
        compartment = target.compartment_id or config.compartment_id
        if not (subnet_id and vcn_id and compartment):
            return None
        return self.oci.create_data_safe_private_endpoint(
            compartment_id=compartment,
            display_name=f"{target.name}-datasafe-pe",
            vcn_id=vcn_id,
            subnet_id=subnet_id,
        )

    def enable_target(self, target: Target, config: EnablementConfig) -> DataSafeDecision:
        if target.kind not in DATA_SAFE_KINDS:
            return DataSafeDecision(target.name, "skipped", f"Data Safe not supported for kind {target.kind}")
        compartment = target.compartment_id or config.compartment_id
        if not compartment:
            return DataSafeDecision(target.name, "blocked", "missing compartment_id")

        # Resolve (or create) the Data Safe private endpoint for non-autonomous targets.
        pe_id = target.data_safe_private_endpoint_id
        if target.kind != "autonomous" and not pe_id:
            pe_id = self.ensure_private_endpoint(target, config)
            if pe_id:
                target = _with_pe(target, pe_id)

        missing = _missing_registration_fields(target)
        if missing:
            return DataSafeDecision(
                target.name,
                "blocked",
                f"missing for Data Safe registration: {', '.join(missing)} (run prepare-prereqs / discover)",
            )

        user, password = self._credentials(target)
        target_id = self._register(target, compartment, user, password)
        if target_id:
            return DataSafeDecision(target.name, "enabled", "Data Safe target registered", target_id)
        return DataSafeDecision(target.name, "ready", "Data Safe registration prepared (dry-run or no OCID returned)")

    def _credentials(self, target: Target) -> tuple[str, str]:
        if self.credential_provider is not None:
            return self.credential_provider(target)
        # Default: reuse the monitoring user with no password (registration will
        # fail loudly if a password is actually required) — callers should inject
        # a provider for live runs.
        return (target.monitoring_user or "DBSNMP", "")

    def _register(self, target: Target, compartment: str, user: str, password: str) -> str | None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="dbman-datasafe-"))
        try:
            os.chmod(tmp_dir, 0o700)
            details_file = _write_json(tmp_dir / "database-details.json", data_safe_database_details(target))
            conn_file = (
                _write_json(tmp_dir / "connection-option.json", _connection_option(target))
                if target.kind != "autonomous"
                else None
            )
            creds_file = _write_json(tmp_dir / "credentials.json", {"userName": user, "password": password})
            return self.oci.create_data_safe_target(
                compartment_id=compartment,
                display_name=target.name,
                database_details_file=str(details_file),
                connection_option_file=str(conn_file) if conn_file else None,
                credentials_file=str(creds_file),
            )
        finally:
            # Best-effort secure cleanup: remove the credential file contents then
            # the temp directory, so the plaintext password does not linger.
            for child in tmp_dir.glob("*"):
                try:
                    child.unlink()
                except OSError:
                    pass
            try:
                tmp_dir.rmdir()
            except OSError:
                pass


def _with_pe(target: Target, pe_id: str) -> Target:
    from dataclasses import replace

    return replace(target, data_safe_private_endpoint_id=pe_id)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(path, 0o600)
    return path
