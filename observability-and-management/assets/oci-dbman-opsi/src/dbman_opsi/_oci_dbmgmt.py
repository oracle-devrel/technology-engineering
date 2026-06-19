"""Database Management: private endpoints, managed databases, named/preferred credentials."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class DatabaseManagementCommands(_OciBase):
    def list_db_management_private_endpoints(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["database-management", "private-endpoint", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_db_management_private_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        return self._data(self.run_json([
            "database-management",
            "private-endpoint",
            "get",
            "--private-endpoint-id",
            endpoint_id,
        ]))

    def list_managed_databases(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "database-management", "managed-database", "list",
            "--compartment-id", compartment_id, "--all",
        ])
        return self._items(data)

    def find_managed_database_id(self, compartment_id: str, name: str) -> str | None:
        for managed in self.list_managed_databases(compartment_id):
            if managed.get("name") == name:
                return managed.get("id")
        return None

    def get_managed_database_status(self, managed_database_id: str) -> str | None:
        """Return the managed database's monitoring status (e.g. UP / DOWN / UNKNOWN)."""

        data = self.run_json([
            "database-management", "managed-database", "get",
            "--managed-database-id", managed_database_id,
        ])
        return self._data(data).get("database-status")

    def list_named_credentials(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "database-management", "named-credential", "list",
            "--compartment-id", compartment_id, "--all",
        ])
        return self._items(data)

    def create_named_credential(
        self,
        compartment_id: str,
        name: str,
        user_name: str,
        password_secret_id: str,
        associated_resource: str,
        role: str = "NORMAL",
        access_mode: str = "RESOURCE_PRINCIPAL",
    ) -> str:
        """Create a RESOURCE_PRINCIPAL named credential and return its OCID.

        Idempotent: if a named credential with ``name`` already exists in the
        compartment, its OCID is returned instead of creating a duplicate.
        """

        for existing in self.list_named_credentials(compartment_id):
            if existing.get("name") == name:
                return str(existing.get("id") or "")
        data = self.run_json([
            "database-management", "named-credential",
            "create-named-credential-basic-named-credential-content",
            "--compartment-id", compartment_id,
            "--name", name,
            "--scope", "RESOURCE",
            "--type", "ORACLE_DB",
            "--content-user-name", user_name,
            "--content-role", role,
            "--content-password-secret-id", password_secret_id,
            "--content-password-secret-access-mode", access_mode,
            "--associated-resource", associated_resource,
        ])
        # Empty string (not "None") when no id is returned, matching the Data Safe
        # create helpers — callers test truthiness to mean "created/exists".
        return str(self._data(data).get("id") or "")

    def list_preferred_credentials(self, managed_database_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "database-management", "preferred-credential", "list",
            "--managed-database-id", managed_database_id,
        ])
        return self._items(data)

    def set_preferred_named_credential(
        self, managed_database_id: str, credential_name: str, named_credential_id: str
    ) -> None:
        """Point a managed database's preferred credential at a named credential.

        Uses the dedicated ``update-preferred-credential-update-named-preferred-credential-details``
        verb; the generic ``preferred-credential update --type NAMED_CREDENTIAL``
        mis-maps the body and fails with RelatedResourceNotAuthorizedOrNotFound.
        """

        self.run([
            "database-management", "preferred-credential",
            "update-preferred-credential-update-named-preferred-credential-details",
            "--managed-database-id", managed_database_id,
            "--credential-name", credential_name,
            "--named-credential-id", named_credential_id,
        ])
