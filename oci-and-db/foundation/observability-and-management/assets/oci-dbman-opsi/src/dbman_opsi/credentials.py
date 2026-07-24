"""Set Database Management preferred (advanced diagnostics) credentials.

After Database Management is enabled, the managed database still needs an
"Advanced diagnostics preferred credential" before on-demand tasks (Performance
Hub, AWR Explorer, ADDM, SQL Tuning) can run — otherwise the Console shows
"Credential required to perform Database Management tasks is not set".

This module wires a managed database's ``PC_READ``/``PC_WRITE`` preferred
credentials to a Vault-backed Named Credential, all via the OCI API so the stack
is reproducible from scripts and Resource Manager.
"""

from __future__ import annotations

from dataclasses import dataclass

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.remediation import remediation_for

# OCI seeds every managed database with these three preferred-credential slots.
# MONITORING is set at enable time; PC_READ/PC_WRITE gate advanced diagnostics.
PREFERRED_CREDENTIAL_NAMES = ("PC_READ", "PC_WRITE")


def _slug(value: str) -> str:
    """Sanitise a value into an OCI named-credential-safe token (alnum + underscore)."""

    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "DB"


@dataclass(frozen=True)
class CredentialDecision:
    target: str
    status: str  # "set" | "skipped" | "blocked"
    detail: str


class CredentialService:
    def __init__(self, oci: OciCli) -> None:
        self.oci = oci

    def set_all(self, config: EnablementConfig) -> list[CredentialDecision]:
        return [self.set_for_target(target, config) for target in config.targets]

    def set_for_target(self, target: Target, config: EnablementConfig) -> CredentialDecision:
        if target.kind not in {"dbcs", "exadata"}:
            return CredentialDecision(target.name, "skipped", "not an OCI-managed database target")

        compartment = target.compartment_id or config.compartment_id or ""
        required = {
            "resource_id": target.resource_id,
            "password_secret_id": target.password_secret_id,
            "monitoring_user": target.monitoring_user,
            "compartment_id": compartment,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            return CredentialDecision(target.name, "blocked", f"missing required fields: {', '.join(missing)}")

        # For OCI-native DBCS/Exadata the Managed Database OCID is the database
        # (or pluggable database) OCID itself, so use it directly — avoids a flaky
        # managed-database list call and any duplicate-display-name ambiguity.
        managed_id = target.resource_id or ""
        # db_name is cosmetic (the named-credential's name); fall back to the
        # target name if the lookup is unavailable so a flaky read never blocks.
        db_name = self._database_name(target) or _slug(target.name)

        if self._already_set(managed_id):
            return CredentialDecision(
                target.name,
                "set",
                f"{', '.join(PREFERRED_CREDENTIAL_NAMES)} already configured for {db_name}",
            )

        try:
            self._apply_with_retry(target, compartment, db_name, managed_id)
        except RuntimeError as exc:
            return CredentialDecision(target.name, "blocked", self._blocked_detail(exc))

        return CredentialDecision(
            target.name,
            "set",
            f"{', '.join(PREFERRED_CREDENTIAL_NAMES)} -> Vault named credential for {db_name}",
        )

    def _already_set(self, managed_id: str) -> bool:
        """True when PC_READ and PC_WRITE are already SET (idempotent short-circuit).

        Reading current state avoids a redundant write — useful when the dbmgmt
        write endpoint is flapping but the credentials are in fact configured.
        """

        # The dbmgmt control plane flaps call-to-call; retry the read a few times
        # so a single transient 404 does not force an unnecessary (also-flaky) write.
        for _ in range(3):
            try:
                statuses = {
                    cred.get("credential-name"): cred.get("status")
                    for cred in self.oci.list_preferred_credentials(managed_id)
                }
            except RuntimeError:
                continue
            return all(statuses.get(name) == "SET" for name in PREFERRED_CREDENTIAL_NAMES)
        return False

    def _apply_with_retry(self, target: Target, compartment: str, db_name: str, managed_id: str) -> None:
        # The cap dbmgmt control plane intermittently returns NotAuthorizedOrNotFound
        # (404); retry the whole credential set once before surfacing the error.
        last_error: RuntimeError | None = None
        for _ in range(2):
            try:
                named_credential_id = self.oci.create_named_credential(
                    compartment_id=compartment,
                    name=f"{db_name}_{target.monitoring_user}_NORMAL",
                    user_name=target.monitoring_user or "DBSNMP",
                    password_secret_id=target.password_secret_id or "",
                    associated_resource=managed_id,
                )
                for credential_name in PREFERRED_CREDENTIAL_NAMES:
                    self.oci.set_preferred_named_credential(managed_id, credential_name, named_credential_id)
                return
            except RuntimeError as exc:
                last_error = exc
        raise last_error  # type: ignore[misc]

    @staticmethod
    def _blocked_detail(exc: RuntimeError) -> str:
        remediation = remediation_for(str(exc))
        if remediation is None:
            return f"credential set failed: {str(exc).splitlines()[0][:160]}"
        return (
            f"credential set failed ({remediation.signature}). "
            f"Solution: {remediation.solution} Manual step: {remediation.manual_step}"
        )

    def _database_name(self, target: Target) -> str | None:
        if not target.resource_id:
            return None
        try:
            if target.database_role == "PDB":
                return self.oci.get_pluggable_database(target.resource_id).get("pdb-name")
            return self.oci.get_database(target.resource_id).get("db-name")
        except RuntimeError:
            return None
