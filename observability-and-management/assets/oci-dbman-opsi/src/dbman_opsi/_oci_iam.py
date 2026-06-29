"""IAM reads: compartments, policies, groups."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class IamCommands(_OciBase):
    def list_compartments(self, tenancy_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "iam",
            "compartment",
            "list",
            "--compartment-id",
            tenancy_id,
            "--compartment-id-in-subtree",
            "true",
            "--access-level",
            "ACCESSIBLE",
        ])
        return self._items(data)

    def list_policies(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["iam", "policy", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_group(self, group_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["iam", "group", "get", "--group-id", group_id]))
