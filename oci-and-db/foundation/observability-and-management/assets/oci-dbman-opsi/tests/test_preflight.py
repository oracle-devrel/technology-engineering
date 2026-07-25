from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.db_check import DbUserCheck
from dbman_opsi.preflight import PreflightService, location_for


def _checks_by_name(checks):
    return {check.name: check for check in checks}


class FakeOci:
    """Healthy-by-default OCI facade; override attributes per test."""

    def __init__(self, **overrides):
        self.policies = overrides.get(
            "policies",
            [{"statements": [
                "Allow service database-management to use virtual-network-family in tenancy",
                "Allow service operations-insights to use virtual-network-family in tenancy",
                "Allow service dpd to read secret-family in tenancy",
            ]}],
        )
        self.subnet = overrides.get(
            "subnet",
            {
                "lifecycle-state": "AVAILABLE",
                "vcn-id": "vcn-id",
                "compartment-id": "compartment-id",
                "route-table-id": "rt-id",
                "security-list-ids": ["sl-id"],
                "prohibit-public-ip-on-vnic": True,
            },
        )
        self.service_gateways = overrides.get("service_gateways", [{"lifecycle-state": "AVAILABLE", "id": "sgw-id"}])
        self.route_table = overrides.get(
            "route_table",
            {"route-rules": [
                {"destination-type": "SERVICE_CIDR_BLOCK", "network-entity-id": "ocid1.servicegateway.oc1..xxx"}
            ]},
        )
        self.security_list = overrides.get(
            "security_list",
            {"ingress-security-rules": [{"protocol": "6", "tcp-options": {"destination-port-range": {"min": 1521, "max": 1522}}}]},
        )
        self.database = overrides.get("database", {"lifecycle-state": "AVAILABLE", "database-management-config": None})
        self.pluggable = overrides.get("pluggable", {"lifecycle-state": "AVAILABLE", "pluggable-database-management-config": None})
        self.autonomous = overrides.get("autonomous", {"lifecycle-state": "AVAILABLE"})
        self.dbm_pe = overrides.get("dbm_pe", {"lifecycle-state": "ACTIVE"})
        self.opsi_pe = overrides.get("opsi_pe", {"lifecycle-state": "ACTIVE"})
        self.secret = overrides.get("secret", {"lifecycle-state": "ACTIVE"})
        self.agents = overrides.get("agents", [])
        self.agent = overrides.get("agent", {})

    def list_policies(self, compartment_id):
        return self.policies

    def get_subnet(self, subnet_id):
        return self.subnet

    def list_service_gateways(self, compartment_id, vcn_id):
        return self.service_gateways

    def get_route_table(self, route_table_id):
        return self.route_table

    def get_security_list(self, security_list_id):
        return self.security_list

    def get_database(self, database_id):
        return self.database

    def get_pluggable_database(self, pluggable_database_id):
        return self.pluggable

    def get_autonomous_database(self, autonomous_database_id):
        return self.autonomous

    def get_db_management_private_endpoint(self, endpoint_id):
        return self.dbm_pe

    def get_opsi_private_endpoint(self, endpoint_id):
        return self.opsi_pe

    def get_secret(self, secret_id):
        return self.secret

    def list_management_agents(self, compartment_id):
        return self.agents

    def get_management_agent(self, agent_id):
        return self.agent


def _native_config(**target_kwargs):
    target = Target(
        kind="dbcs",
        name="cloud db",
        compartment_id="compartment-id",
        resource_id="db-id",
        service_name="PDB1",
        monitoring_user="DBSNMP",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-pe-id",
        opsi_private_endpoint_id="opsi-pe-id",
        **target_kwargs,
    )
    return EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
        targets=(target,),
    )


def test_location_classification() -> None:
    assert location_for("dbcs") == "oci-native"
    assert location_for("autonomous") == "oci-native"
    assert location_for("external-db") == "management-agent"
    assert location_for("external-exadata") == "management-agent"


def test_healthy_native_target_passes_all_gates() -> None:
    report = PreflightService(FakeOci()).run(_native_config())  # type: ignore[arg-type]

    assert report.ok
    network = _checks_by_name(report.network_checks)
    assert network["network.service_gateway"].status == "pass"
    assert network["network.route"].status == "pass"
    target = report.targets[0]
    assert target.location == "oci-native"
    checks = _checks_by_name(target.checks)
    assert checks["target.resource"].status == "pass"
    assert checks["target.monitoring_user"].status == "manual"


def test_missing_service_gateway_blocks() -> None:
    report = PreflightService(FakeOci(service_gateways=[])).run(_native_config())  # type: ignore[arg-type]

    network = _checks_by_name(report.network_checks)
    assert network["network.service_gateway"].status == "fail"
    assert not report.ok


def test_missing_route_to_services_blocks() -> None:
    report = PreflightService(FakeOci(route_table={"route-rules": []})).run(_native_config())  # type: ignore[arg-type]

    assert _checks_by_name(report.network_checks)["network.route"].status == "fail"
    assert not report.ok


def test_missing_iam_policies_fail() -> None:
    report = PreflightService(FakeOci(policies=[])).run(_native_config())  # type: ignore[arg-type]

    assert _checks_by_name(report.tenancy_checks)["iam.policies"].status == "fail"


def test_partial_iam_policies_warn() -> None:
    oci = FakeOci(policies=[{"statements": ["Allow service dpd to read secret-family in tenancy"]}])
    report = PreflightService(oci).run(_native_config())  # type: ignore[arg-type]

    iam = _checks_by_name(report.tenancy_checks)["iam.policies"]
    assert iam.status == "warn"
    assert "operations insights" in iam.detail.lower()


def test_inactive_secret_blocks() -> None:
    report = PreflightService(FakeOci(secret={"lifecycle-state": "DELETED"})).run(_native_config())  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.vault_secret"].status == "fail"


def test_external_target_missing_agent_blocks() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        targets=(Target(kind="external-db", name="salesdb", compartment_id="compartment-id"),),
    )
    report = PreflightService(FakeOci(agents=[])).run(config)  # type: ignore[arg-type]

    target = report.targets[0]
    assert target.location == "management-agent"
    assert _checks_by_name(target.checks)["target.management_agent"].status == "fail"


def test_external_target_with_running_plugins_passes() -> None:
    agents = [{
        "display-name": "salesdb-agent",
        "availability-status": "ACTIVE",
        "plugin-list": [
            {"plugin-name": "dbmgmt", "plugin-status": "RUNNING"},
            {"plugin-name": "opsi", "plugin-status": "RUNNING"},
        ],
    }]
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        targets=(Target(kind="external-db", name="salesdb", compartment_id="compartment-id"),),
    )
    report = PreflightService(FakeOci(agents=agents)).run(config)  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.management_agent"].status == "pass"


def test_no_subnet_skips_network() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        targets=(Target(kind="autonomous", name="adb", resource_id="adb-id"),),
    )
    report = PreflightService(FakeOci()).run(config)  # type: ignore[arg-type]

    assert _checks_by_name(report.network_checks)["network.subnet"].status == "skip"
    autonomous_checks = _checks_by_name(report.targets[0].checks)
    assert autonomous_checks["target.vault_secret"].status == "skip"
    assert autonomous_checks["target.monitoring_user"].status == "skip"


def _pdb_config(parent_cdb_id="cdb-id"):
    target = Target(
        kind="dbcs",
        name="pdb1",
        compartment_id="compartment-id",
        resource_id="pdb-id",
        service_name="PDB1",
        monitoring_user="DBSNMP",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-pe-id",
        opsi_private_endpoint_id="opsi-pe-id",
        database_role="PDB",
        parent_cdb_id=parent_cdb_id,
    )
    return EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
        targets=(target,),
    )


def test_pdb_parent_enabled_passes_gate() -> None:
    oci = FakeOci(database={"lifecycle-state": "AVAILABLE", "database-management-config": {"management-status": "ENABLED"}})
    report = PreflightService(oci).run(_pdb_config())  # type: ignore[arg-type]

    checks = _checks_by_name(report.targets[0].checks)
    assert checks["target.parent_cdb"].status == "pass"
    assert checks["target.resource"].detail.startswith("PDB")


def test_pdb_parent_not_enabled_blocks() -> None:
    report = PreflightService(FakeOci()).run(_pdb_config())  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.parent_cdb"].status == "fail"
    assert not report.ok


def test_pdb_without_parent_id_warns() -> None:
    report = PreflightService(FakeOci()).run(_pdb_config(parent_cdb_id=None))  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.parent_cdb"].status == "warn"


def test_monitoring_user_check_passes_with_db_check() -> None:
    db_check = DbUserCheck(account_open=True, found=("CREATE SESSION", "SELECT ANY DICTIONARY"), missing=())
    report = PreflightService(FakeOci()).run(_native_config(), db_check=db_check)  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.monitoring_user"].status == "pass"


def test_monitoring_user_check_fails_with_missing_grants() -> None:
    db_check = DbUserCheck(account_open=True, found=("CREATE SESSION",), missing=("SELECT ANY DICTIONARY",))
    report = PreflightService(FakeOci()).run(_native_config(), db_check=db_check)  # type: ignore[arg-type]

    check = _checks_by_name(report.targets[0].checks)["target.monitoring_user"]
    assert check.status == "fail"
    assert "SELECT ANY DICTIONARY" in check.detail


def test_monitoring_user_defaults_to_manual_without_db_check() -> None:
    report = PreflightService(FakeOci()).run(_native_config())  # type: ignore[arg-type]

    assert _checks_by_name(report.targets[0].checks)["target.monitoring_user"].status == "manual"


def test_read_error_surfaces_as_failure() -> None:
    class Boom(FakeOci):
        def get_subnet(self, subnet_id):
            raise RuntimeError("denied")

    report = PreflightService(Boom()).run(_native_config())  # type: ignore[arg-type]
    assert _checks_by_name(report.network_checks)["network.subnet"].status == "fail"
