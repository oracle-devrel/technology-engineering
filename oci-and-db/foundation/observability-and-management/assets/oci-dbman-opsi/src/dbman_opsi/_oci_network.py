"""Networking reads: VCNs, subnets, route tables, security lists, gateways."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class NetworkCommands(_OciBase):
    def list_vcns(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["network", "vcn", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def list_subnets(self, compartment_id: str, vcn_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["network", "subnet", "list", "--compartment-id", compartment_id, "--vcn-id", vcn_id, "--all"])
        return self._items(data)

    def list_service_gateways(self, compartment_id: str, vcn_id: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "network",
            "service-gateway",
            "list",
            "--compartment-id",
            compartment_id,
            "--vcn-id",
            vcn_id,
            "--all",
        ])
        return self._items(data)

    def get_subnet(self, subnet_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["network", "subnet", "get", "--subnet-id", subnet_id]))

    def get_vcn(self, vcn_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["network", "vcn", "get", "--vcn-id", vcn_id]))

    def get_route_table(self, route_table_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["network", "route-table", "get", "--rt-id", route_table_id]))

    def get_security_list(self, security_list_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["network", "security-list", "get", "--security-list-id", security_list_id]))
