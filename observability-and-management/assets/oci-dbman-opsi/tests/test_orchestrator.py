from pathlib import Path

from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.enablement import EnablementService
from dbman_opsi.orchestrator import ConfigureService
from test_preflight import FakeOci, _native_config


class RecordingEnableOci(FakeOci):
    def __init__(self, **overrides):
        super().__init__(**overrides)
        self.commands: list[list[str]] = []

    def run(self, args):
        self.commands.append(args)

    def run_tolerating(self, args, tolerated):
        self.run(args)
        return True


def _service(read_oci, write_oci):
    return ConfigureService(read_oci, EnablementService(write_oci))


def test_plan_mode_marks_ready_without_enabling() -> None:
    write = RecordingEnableOci()
    report = _service(FakeOci(), write).configure(_native_config(), mode="plan")  # type: ignore[arg-type]

    assert report.ok
    assert report.decisions[0].action == "ready"
    assert write.commands == []


def test_apply_mode_enables_when_ready() -> None:
    write = RecordingEnableOci()
    report = _service(FakeOci(), write).configure(_native_config(), mode="apply")  # type: ignore[arg-type]

    assert report.decisions[0].action == "enabled"
    assert write.commands[0][:3] == ["db", "database", "enable-database-management"]


def test_already_enabled_is_skipped() -> None:
    read = FakeOci(database={"lifecycle-state": "AVAILABLE", "database-management-config": {"management-status": "ENABLED"}})
    write = RecordingEnableOci()
    report = _service(read, write).configure(_native_config(), mode="apply")  # type: ignore[arg-type]

    assert report.decisions[0].action == "skip-enabled"
    assert write.commands == []


def test_already_dbm_enabled_target_can_still_create_opsi() -> None:
    read = FakeOci(database={"lifecycle-state": "AVAILABLE", "database-management-config": {"management-status": "ENABLED"}})
    write = RecordingEnableOci()
    config = _native_config(opsi_credential_details_file="credential-details.json")
    report = _service(read, write).configure(config, mode="apply")  # type: ignore[arg-type]

    assert report.decisions[0].action == "enabled"
    assert "Ops Insights" in report.decisions[0].reason
    assert write.commands[0][:3] == ["opsi", "database-insights", "create-pe-comanged-database"]


def test_blocked_when_service_gateway_missing() -> None:
    read = FakeOci(service_gateways=[])
    write = RecordingEnableOci()
    report = _service(read, write).configure(_native_config(), mode="apply")  # type: ignore[arg-type]

    assert report.decisions[0].action == "blocked"
    assert "network" in report.decisions[0].reason
    assert write.commands == []
    assert not report.ok


def test_force_bypasses_blockers() -> None:
    read = FakeOci(service_gateways=[])
    write = RecordingEnableOci()
    report = _service(read, write).configure(_native_config(), mode="apply", force=True)  # type: ignore[arg-type]

    assert report.decisions[0].action == "enabled"
    assert write.commands


def test_db_side_only_generates_handoff(tmp_path: Path) -> None:
    write = RecordingEnableOci()
    report = _service(FakeOci(), write).configure(  # type: ignore[arg-type]
        _native_config(), mode="db-side-only", handoff_dir=tmp_path
    )

    assert report.decisions[0].action == "handoff"
    assert write.commands == []
    assert (tmp_path / "cloud-db" / "HANDOFF.md").exists()
    assert report.handoff_paths


def test_cdb_is_ordered_before_pdb() -> None:
    pdb = Target(kind="dbcs", name="pdb1", compartment_id="compartment-id", resource_id="pdb-id",
                 database_role="PDB", parent_cdb_id="cdb-id")
    cdb = Target(kind="dbcs", name="cdb1", compartment_id="compartment-id", resource_id="cdb-id")
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
        targets=(pdb, cdb),  # PDB listed first on purpose
    )
    report = _service(FakeOci(), RecordingEnableOci()).configure(config, mode="plan")  # type: ignore[arg-type]

    assert [decision.name for decision in report.decisions] == ["cdb1", "pdb1"]


def test_apply_enables_cdb_then_pdb_when_parent_is_in_same_config() -> None:
    pdb = Target(
        kind="dbcs",
        name="pdb1",
        compartment_id="compartment-id",
        resource_id="pdb-id",
        database_role="PDB",
        parent_cdb_id="cdb-id",
        service_name="PDB1",
        monitoring_user="DBSNMP",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-pe-id",
        opsi_private_endpoint_id="opsi-pe-id",
    )
    cdb = Target(
        kind="dbcs",
        name="cdb1",
        compartment_id="compartment-id",
        resource_id="cdb-id",
        service_name="CDB1",
        monitoring_user="DBSNMP",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-pe-id",
        opsi_private_endpoint_id="opsi-pe-id",
    )
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        tenancy_id="tenancy-id",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
        targets=(pdb, cdb),  # PDB listed first on purpose
    )
    write = RecordingEnableOci()

    report = _service(FakeOci(), write).configure(config, mode="apply")  # type: ignore[arg-type]

    assert [decision.action for decision in report.decisions] == ["enabled", "enabled"]
    assert write.commands[0][:3] == ["db", "database", "enable-database-management"]
    assert write.commands[1][:3] == ["db", "pluggable-database", "enable-pluggable-database-management"]


def test_db_side_only_hands_off_even_when_oci_blocked(tmp_path) -> None:
    read = FakeOci(service_gateways=[])  # OCI-side network blocker
    report = _service(read, RecordingEnableOci()).configure(  # type: ignore[arg-type]
        _native_config(), mode="db-side-only", handoff_dir=tmp_path
    )

    assert report.decisions[0].action == "handoff"
    assert (tmp_path / "cloud-db" / "HANDOFF.md").exists()


def test_report_to_dict_round_trips() -> None:
    report = _service(FakeOci(), RecordingEnableOci()).configure(_native_config(), mode="plan")  # type: ignore[arg-type]
    data = report.to_dict()

    assert data["mode"] == "plan"
    assert data["ok"] is True
    assert data["decisions"][0]["action"] == "ready"
    assert "preflight" in data


def test_configure_apply_runs_data_safe_for_opted_in_targets() -> None:
    from dbman_opsi.datasafe import DataSafeDecision

    class FakeDataSafe:
        def __init__(self):
            self.called_with = None

        def enable_all(self, config):
            self.called_with = config
            return [DataSafeDecision("cloud db", "enabled", "Data Safe target registered", "dst-1")]

    write = RecordingEnableOci()
    ds = FakeDataSafe()
    service = ConfigureService(FakeOci(), EnablementService(write), datasafe=ds)  # type: ignore[arg-type]
    report = service.configure(_native_config(), mode="apply")

    assert ds.called_with is not None  # Data Safe ran in apply mode
    assert len(report.data_safe) == 1
    assert report.data_safe[0].status == "enabled"
    assert "data_safe" in report.to_dict()


def test_configure_plan_mode_does_not_run_data_safe() -> None:
    class FakeDataSafe:
        def __init__(self):
            self.called = False

        def enable_all(self, config):
            self.called = True
            return []

    ds = FakeDataSafe()
    service = ConfigureService(FakeOci(), EnablementService(RecordingEnableOci()), datasafe=ds)  # type: ignore[arg-type]
    report = service.configure(_native_config(), mode="plan")

    assert ds.called is False
    assert report.data_safe == ()
