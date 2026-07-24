"""Database reads: DB systems, databases, PDBs, Autonomous, Exadata infra."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class DatabaseCommands(_OciBase):
    def list_db_systems(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["db", "system", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def list_databases(self, compartment_id: str, db_system_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "db",
            "database",
            "list",
            "--compartment-id",
            compartment_id,
            "--db-system-id",
            db_system_id,
        ])
        return self._items(data)

    def get_database(self, database_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["db", "database", "get", "--database-id", database_id]))

    def get_db_system(self, db_system_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["db", "system", "get", "--db-system-id", db_system_id]))

    def list_pluggable_databases(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["db", "pluggable-database", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_pluggable_database(self, pluggable_database_id: str) -> dict[str, Any]:
        return self._data(self.run_json([
            "db",
            "pluggable-database",
            "get",
            "--pluggable-database-id",
            pluggable_database_id,
        ]))

    def list_autonomous_databases(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["db", "autonomous-database", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_autonomous_database(self, autonomous_database_id: str) -> dict[str, Any]:
        return self._data(self.run_json([
            "db",
            "autonomous-database",
            "get",
            "--autonomous-database-id",
            autonomous_database_id,
        ]))

    def list_exadata_infrastructure(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["db", "cloud-exa-infra", "list", "--compartment-id", compartment_id])
        return self._items(data)
