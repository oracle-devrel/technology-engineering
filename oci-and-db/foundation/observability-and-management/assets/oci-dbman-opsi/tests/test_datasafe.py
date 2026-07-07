import json
from pathlib import Path

from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.datasafe import DataSafeService, data_safe_database_details


class FakeOci:
    def __init__(self, existing_targets=None, existing_pes=None):
        self._targets = existing_targets or []
        self._pes = existing_pes or []
        self.created_targets: list[dict] = []
        self.created_pes: list[dict] = []

    def list_data_safe_targets(self, compartment_id):
        return self._targets

    def list_data_safe_private_endpoints(self, compartment_id):
        return self._pes

    def create_data_safe_private_endpoint(self, compartment_id, display_name, vcn_id, subnet_id):
        self.created_pes.append({"display-name": display_name, "subnet": subnet_id})
        return "ocid1.datasafeprivateendpoint.oc1..created"

    def create_data_safe_target(
        self, compartment_id, display_name, database_details_file,
        connection_option_file=None, credentials_file=None,
    ):
        # Capture the payload contents so the test can assert on them before the
        # service deletes the temp files.
        self.created_targets.append({
            "display_name": display_name,
            "database_details": json.loads(Path(database_details_file).read_text()),
            "connection_option": json.loads(Path(connection_option_file).read_text()) if connection_option_file else None,
            "credentials": json.loads(Path(credentials_file).read_text()) if credentials_file else None,
        })
        return "ocid1.datasafetargetdatabase.oc1..registered"


def _config(**network):
    return EnablementConfig(
        profile="cap", region="eu-frankfurt-1", compartment_id="cmpt-1",
        network=NetworkSelection(**network),
    )


def test_database_details_cloud_service_uses_db_system_and_service() -> None:
    target = Target(kind="dbcs", name="cdb", db_system_id="sys-1", service_name="PDB1")
    details = data_safe_database_details(target)
    assert details["databaseType"] == "DATABASE_CLOUD_SERVICE"
    assert details["dbSystemId"] == "sys-1"
    assert details["serviceName"] == "PDB1"


def test_database_details_autonomous_uses_adb_id() -> None:
    details = data_safe_database_details(Target(kind="autonomous", name="adb", resource_id="adb-1"))
    assert details["databaseType"] == "AUTONOMOUS_DATABASE"
    assert details["autonomousDatabaseId"] == "adb-1"


def test_enable_target_registers_with_payloads_and_creds() -> None:
    oci = FakeOci()
    target = Target(
        kind="dbcs", name="dbmopsi", compartment_id="cmpt-1",
        db_system_id="sys-1", service_name="PDB1",
        data_safe_private_endpoint_id="dspe-1",
        services=("dbm", "opsi", "datasafe"),
    )
    service = DataSafeService(oci, credential_provider=lambda t: ("DBSNMP", "s3cret"))

    decision = service.enable_target(target, _config())

    assert decision.status == "enabled"
    assert decision.target_id == "ocid1.datasafetargetdatabase.oc1..registered"
    created = oci.created_targets[0]
    assert created["connection_option"]["datasafePrivateEndpointId"] == "dspe-1"
    assert created["credentials"] == {"userName": "DBSNMP", "password": "s3cret"}


def test_enable_target_creates_private_endpoint_when_missing() -> None:
    oci = FakeOci()
    target = Target(
        kind="dbcs", name="dbmopsi", compartment_id="cmpt-1",
        db_system_id="sys-1", service_name="PDB1",
        services=("dbm", "opsi", "datasafe"),
    )
    service = DataSafeService(oci, credential_provider=lambda t: ("DBSNMP", "pw"))

    decision = service.enable_target(target, _config(vcn_id="vcn-1", subnet_id="subnet-1"))

    assert oci.created_pes and oci.created_pes[0]["subnet"] == "subnet-1"
    assert decision.status == "enabled"


def test_enable_target_blocked_when_registration_fields_missing() -> None:
    oci = FakeOci()
    target = Target(kind="dbcs", name="dbmopsi", compartment_id="cmpt-1",
                    services=("dbm", "opsi", "datasafe"))
    # No db_system_id / service_name / PE and no subnet to create one.
    decision = DataSafeService(oci).enable_target(target, _config())
    assert decision.status == "blocked"
    assert "db_system_id" in decision.detail


def test_enable_target_skips_unsupported_kind() -> None:
    decision = DataSafeService(FakeOci()).enable_target(
        Target(kind="external-db", name="ext", services=("datasafe",)), _config()
    )
    assert decision.status == "skipped"


def test_enable_all_only_processes_opted_in_targets() -> None:
    oci = FakeOci()
    config = EnablementConfig(
        profile="cap", region="eu-frankfurt-1", compartment_id="cmpt-1",
        targets=(
            Target(kind="dbcs", name="ds", compartment_id="cmpt-1", db_system_id="sys-1",
                   service_name="PDB1", data_safe_private_endpoint_id="pe-1",
                   services=("dbm", "opsi", "datasafe")),
            Target(kind="dbcs", name="no-ds", services=("dbm", "opsi")),
        ),
    )
    decisions = DataSafeService(oci, credential_provider=lambda t: ("DBSNMP", "pw")).enable_all(config)
    assert [d.target for d in decisions] == ["ds"]


def test_register_cleans_up_credential_temp_files(tmp_path) -> None:
    oci = FakeOci()
    target = Target(kind="dbcs", name="dbmopsi", compartment_id="cmpt-1", db_system_id="sys-1",
                    service_name="PDB1", data_safe_private_endpoint_id="pe-1",
                    services=("dbm", "opsi", "datasafe"))
    DataSafeService(oci, credential_provider=lambda t: ("DBSNMP", "pw")).enable_target(target, _config())
    # No dbman-datasafe-* temp dirs should remain.
    import tempfile as _tf
    leftovers = list(Path(_tf.gettempdir()).glob("dbman-datasafe-*"))
    assert leftovers == []
