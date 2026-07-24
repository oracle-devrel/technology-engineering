"""Operations Insights JSON payload generation."""

from __future__ import annotations

import json
from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target


def credential_details(target: Target) -> dict[str, object]:
    if not target.password_secret_id:
        return {
            "credentialType": "CREDENTIALS_BY_SOURCE",
            "credentialSourceName": target.name,
        }
    payload: dict[str, object] = {
        "credentialType": "CREDENTIALS_BY_VAULT",
        "credentialSourceName": target.name,
        "userName": target.monitoring_user or "DBSNMP",
        "passwordSecretId": target.password_secret_id,
        "role": "NORMAL",
    }
    if target.wallet_secret_id:
        payload = {**payload, "walletSecretId": target.wallet_secret_id}
    return payload


def connection_details(target: Target) -> dict[str, object]:
    return {
        "hosts": [
            {
                "hostIp": target.external_host or "<DATABASE_HOST_OR_SCAN_IP>",
                "port": 1521,
            }
        ],
        "protocol": "TCP",
        "serviceName": target.service_name or "ORCLPDB1",
    }


def generate_opsi_payloads(config: EnablementConfig, output_dir: str | Path) -> list[Path]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for target in config.targets:
        if target.kind not in {"dbcs", "exadata", "external-db", "external-exadata", "autonomous"}:
            continue
        target_dir = base_dir / target.name.replace(" ", "-").lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        payloads = {
            "credential-details.json": credential_details(target),
            "connection-details.json": connection_details(target),
        }
        for filename, payload in payloads.items():
            path = target_dir / filename
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            paths.append(path)
    return paths
