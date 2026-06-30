"""KMS / Vault reads: vaults, keys, secrets."""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class VaultCommands(_OciBase):
    def list_vaults(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["kms", "management", "vault", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def list_keys(self, compartment_id: str, management_endpoint: str) -> list[dict[str, Any]]:
        data = self.run_json([
            "kms",
            "management",
            "key",
            "list",
            "--compartment-id",
            compartment_id,
            "--endpoint",
            management_endpoint,
        ])
        return self._items(data)

    def list_secrets(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["vault", "secret", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_secret(self, secret_id: str) -> dict[str, Any]:
        return self._data(self.run_json(["vault", "secret", "get", "--secret-id", secret_id]))
