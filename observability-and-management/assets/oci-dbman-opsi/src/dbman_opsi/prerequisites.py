"""OCI-side prerequisite provisioning for service enablement."""

from __future__ import annotations

import base64
import logging
import os

from dbman_opsi.config import EnablementConfig
from dbman_opsi.oci_cli import OciCli

log = logging.getLogger(__name__)

# A list-first idempotency check can miss an existing resource when the OCI
# control plane returns a flaky empty/partial list (the same non-determinism that
# bites OPSI reads). So creates also tolerate the server-side name conflict: if the
# resource really exists, the 409 is an idempotent no-op rather than a crash.
_CREATE_CONFLICT_MARKERS = (
    "already exists",
    "already in use",
    "already used",
    "AlreadyExists",
    "name is already",
)


class PrerequisiteService:
    def __init__(self, oci: OciCli) -> None:
        self.oci = oci

    def _create_tolerant(self, args: list[str], what: str) -> None:
        """Run a create, absorbing an 'already exists' conflict as a no-op.

        Belt-and-suspenders to the list-first guard above each call site: if that
        list flaked empty and missed the existing resource, the create's name
        conflict is tolerated instead of aborting the whole prepare run.
        """

        if not self.oci.run_tolerating(args, tolerated=_CREATE_CONFLICT_MARKERS):
            log.info("%s already exists (create returned a name conflict); treated as a no-op.", what)

    def prepare(self, config: EnablementConfig, password_env: str | None = None) -> None:
        if config.network.subnet_id:
            self._create_db_management_private_endpoint(config)
            self._create_opsi_private_endpoint(config)
        else:
            log.info("Skipping private endpoints; config.network.subnet_id is missing.")
        if config.vault.create_vault and not config.vault.vault_id:
            log.info(
                "Vault creation is supported by OCI CLI, but config must be refreshed "
                "with the created vault endpoint before key creation."
            )
        if password_env:
            self._create_password_secrets(config, password_env)

    def _create_db_management_private_endpoint(self, config: EnablementConfig) -> None:
        existing = self.oci.list_db_management_private_endpoints(config.compartment_id or "")
        if any(item.get("name") == "dbman_opsi_dbmgmt_pe" for item in existing):
            log.info("Database Management private endpoint dbman_opsi_dbmgmt_pe already exists; skipping create.")
            return
        self._create_tolerant([
            "database-management",
            "private-endpoint",
            "create",
            "--name",
            "dbman_opsi_dbmgmt_pe",
            "--compartment-id",
            config.compartment_id or "",
            "--subnet-id",
            config.network.subnet_id or "",
            "--is-cluster",
            "false",
            "--is-dns-resolution-enabled",
            "false",
            "--description",
            "Created by dbman-opsi for Database Management enablement.",
        ], "Database Management private endpoint dbman_opsi_dbmgmt_pe")

    def _create_opsi_private_endpoint(self, config: EnablementConfig) -> None:
        existing = self.oci.list_opsi_private_endpoints(config.compartment_id or "")
        if any(item.get("display-name") == "dbman_opsi_opsi_pe" for item in existing):
            log.info("Ops Insights private endpoint dbman_opsi_opsi_pe already exists; skipping create.")
            return
        self._create_tolerant([
            "opsi",
            "opsi-private-endpoint",
            "create",
            "--display-name",
            "dbman_opsi_opsi_pe",
            "--compartment-id",
            config.compartment_id or "",
            "--vcn-id",
            config.network.vcn_id or "",
            "--subnet-id",
            config.network.subnet_id or "",
            "--is-used-for-rac-dbs",
            "false",
            "--description",
            "Created by dbman-opsi for Ops Insights enablement.",
        ], "Ops Insights private endpoint dbman_opsi_opsi_pe")

    def _create_password_secrets(self, config: EnablementConfig, password_env: str) -> None:
        if not config.vault.vault_id or not config.vault.key_id:
            log.info("Skipping password secret creation; vault_id and key_id are required.")
            return
        password = os.environ.get(password_env)
        if not password:
            log.info("Skipping password secret creation; environment variable %s is not set.", password_env)
            return
        encoded = base64.b64encode(password.encode("utf-8")).decode("ascii")
        for target in config.targets:
            if target.password_secret_id:
                continue
            if target.kind not in {"dbcs", "exadata", "external-db", "external-exadata"}:
                continue
            secret_name = f"dbman-opsi-{target.name.replace(' ', '-').lower()}-password"
            self._create_tolerant([
                "vault",
                "secret",
                "create-base64",
                "--compartment-id",
                target.compartment_id or config.compartment_id or "",
                "--vault-id",
                config.vault.vault_id,
                "--key-id",
                config.vault.key_id,
                "--secret-name",
                secret_name,
                "--secret-content-content",
                encoded,
                "--description",
                "Database monitoring user password for dbman-opsi.",
            ], f"Vault secret {secret_name}")
