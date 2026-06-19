import json
from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.opsi_payloads import connection_details, credential_details, generate_opsi_payloads


def test_credential_details_uses_vault_reference_when_present() -> None:
    target = Target(kind="dbcs", name="db", monitoring_user="DBSNMP", password_secret_id="secret-id")

    payload = credential_details(target)

    assert payload["credentialType"] == "CREDENTIALS_BY_VAULT"
    assert payload["passwordSecretId"] == "secret-id"
    assert payload["role"] == "NORMAL"


def test_credential_details_uses_source_when_secret_missing() -> None:
    target = Target(kind="dbcs", name="db", monitoring_user="DBSNMP")

    payload = credential_details(target)

    assert payload == {
        "credentialType": "CREDENTIALS_BY_SOURCE",
        "credentialSourceName": "db",
    }


def test_connection_details_defaults_service_and_host_placeholder() -> None:
    payload = connection_details(Target(kind="dbcs", name="db"))

    assert payload["serviceName"] == "ORCLPDB1"
    assert payload["hosts"][0]["port"] == 1521


def test_generate_opsi_payloads_writes_json(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="cloud db", password_secret_id="secret-id"),),
    )

    paths = generate_opsi_payloads(config, tmp_path)

    assert len(paths) == 2
    data = json.loads((tmp_path / "cloud-db" / "credential-details.json").read_text(encoding="utf-8"))
    assert data["passwordSecretId"] == "secret-id"
