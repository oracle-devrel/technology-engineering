"""Data Safe (security pillar): target databases and private endpoints."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class DataSafeCommands(_OciBase):
    def list_data_safe_targets(self, compartment_id: str) -> list[dict[str, Any]]:
        """List registered Data Safe target databases in a compartment.

        Data Safe registration is a standalone ``target-database`` resource, not
        a status field on the DB, so detection means listing these and matching
        each back to a discovered database by OCID.
        """

        data = self.run_json([
            "data-safe", "target-database", "list",
            "--compartment-id", compartment_id, "--all",
        ])
        return self._items(data)

    def get_data_safe_target(self, target_database_id: str) -> dict[str, Any]:
        return self._data(self.run_json([
            "data-safe", "target-database", "get",
            "--target-database-id", target_database_id,
        ]))

    def list_data_safe_private_endpoints(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "data-safe", "private-endpoint", "list",
            "--compartment-id", compartment_id, "--all",
        ])
        return self._items(data)

    def create_data_safe_private_endpoint(
        self,
        compartment_id: str,
        display_name: str,
        vcn_id: str,
        subnet_id: str,
    ) -> str:
        """Create (or reuse) a Data Safe private endpoint in the DB subnet.

        Idempotent by display name. Waits for the endpoint to go ACTIVE so the
        returned OCID is immediately usable for target registration.
        """

        for existing in self.list_data_safe_private_endpoints(compartment_id):
            if existing.get("display-name") == display_name:
                return str(existing.get("id"))
        # ``private-endpoint create`` returns a WORK REQUEST, so --wait-for-state
        # takes work-request states (SUCCEEDED), not resource states (ACTIVE). Wait
        # on the work request, then re-list to resolve the new PE's OCID.
        self.run([
            "data-safe", "private-endpoint", "create",
            "--compartment-id", compartment_id,
            "--display-name", display_name,
            "--vcn-id", vcn_id,
            "--subnet-id", subnet_id,
            "--wait-for-state", "SUCCEEDED",
            "--max-wait-seconds", "1200",
            "--wait-interval-seconds", "30",
        ])
        for created in self.list_data_safe_private_endpoints(compartment_id):
            if created.get("display-name") == display_name:
                return str(created.get("id"))
        return ""

    def create_data_safe_target(
        self,
        compartment_id: str,
        display_name: str,
        database_details_file: str,
        connection_option_file: str | None = None,
        credentials_file: str | None = None,
    ) -> str:
        """Register a Data Safe target database, returning its OCID.

        ``*_file`` arguments are paths to JSON payloads (passed as ``file://``)
        so secrets never appear on the command line. Idempotent: if a target with
        ``display_name`` already exists in the compartment, its OCID is returned.
        """

        for existing in self.list_data_safe_targets(compartment_id):
            if existing.get("display-name") == display_name:
                return str(existing.get("id"))
        args = [
            "data-safe", "target-database", "create",
            "--compartment-id", compartment_id,
            "--display-name", display_name,
            "--database-details", f"file://{database_details_file}",
        ]
        if connection_option_file:
            args.extend(["--connection-option", f"file://{connection_option_file}"])
        if credentials_file:
            args.extend(["--credentials", f"file://{credentials_file}"])
        # Empty string (not "None") when no id is returned — e.g. a dry-run runner
        # stubs the response to {} — so callers treat it as "not registered".
        return str(self._data(self.run_json(args)).get("id") or "")
