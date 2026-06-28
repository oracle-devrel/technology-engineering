import logging

from dbman_opsi.config import Target
from dbman_opsi.enablement import EnablementService


class FakeOci:
    def __init__(self, fail_on_index: int | None = None, fail_text: str = "", insights=None,
                 db_status: str = "DOWN") -> None:
        self.commands: list[list[str]] = []
        self.fail_on_index = fail_on_index
        self.fail_text = fail_text
        self.insights = insights or []
        self.db_status = db_status

    def list_opsi_database_insights(self, compartment_id):
        return self.insights

    def get_managed_database_status(self, managed_database_id):
        return self.db_status

    def run(self, args: list[str]) -> None:
        index = len(self.commands)
        self.commands.append(args)
        if self.fail_on_index is not None and index == self.fail_on_index:
            raise RuntimeError(self.fail_text)

    def run_tolerating(self, args: list[str], tolerated: tuple[str, ...]) -> bool:
        try:
            self.run(args)
            return True
        except RuntimeError as exc:
            if any(marker in str(exc) for marker in tolerated):
                return False
            raise


def test_enable_cloud_database_requires_connection_fields() -> None:
    service = EnablementService(FakeOci())  # type: ignore[arg-type]
    target = Target(kind="dbcs", name="db1", resource_id="database-id")

    try:
        service.enable_target(target)
    except ValueError as exc:
        assert "password_secret_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_enable_autonomous_invokes_opsi_command() -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(kind="autonomous", name="adb", resource_id="autonomous-database-id")

    service.enable_target(target)

    assert oci.commands[0][:3] == ["db", "autonomous-database", "enable-autonomous-database-management"]


def test_enable_autonomous_invokes_database_management_when_configured() -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="autonomous",
        name="adb",
        resource_id="autonomous-database-id",
        opsi_database_insight_id="database-insight-id",
    )

    service.enable_target(target)

    assert len(oci.commands) == 2
    assert oci.commands[1][:3] == ["opsi", "database-insights", "enable-autonomous-database"]


def test_enable_cloud_database_invokes_dbmgmt_and_opsi_commands() -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_database_insight_id="database-insight-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    assert oci.commands[0][:3] == ["db", "database", "enable-database-management"]
    assert "--private-end-point-id" in oci.commands[0]
    assert oci.commands[1][:3] == ["opsi", "database-insights", "enable-pe-comanaged-database"]
    assert "file://credential-details.json" in oci.commands[1]


def test_enable_cloud_database_creates_opsi_insight_when_missing_id() -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    assert oci.commands[1][:3] == ["opsi", "database-insights", "create-pe-comanged-database"]
    assert "--database-id" in oci.commands[1]
    assert "--opsi-private-endpoint-id" in oci.commands[1]
    assert "--dbm-private-endpoint-id" not in oci.commands[1]
    assert "--database-resource-type" in oci.commands[1]
    assert "--wait-for-state" in oci.commands[1]
    assert "SUCCEEDED" in oci.commands[1]
    assert "file://credential-details.json" in oci.commands[1]


def test_enable_cloud_database_tolerates_dbm_already_enabled(caplog) -> None:
    # Database Management enable returns 409 "already enabled"; the run must
    # swallow it and still issue the Ops Insights create (idempotent re-run).
    oci = FakeOci(
        fail_on_index=0,
        fail_text=(
            "Command failed (1): ... IncorrectState ... "
            "Either DatabaseManagement is already enabled or request to enable it is already created."
        ),
    )
    service = EnablementService(oci)  # type: ignore[arg-type]
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    # already-enabled DBM -> reconcile via modify, then still create the OPSI insight
    assert oci.commands[0][:3] == ["db", "database", "enable-database-management"]
    assert oci.commands[1][:3] == ["db", "database", "modify-database-management"]
    assert "--service-name" in oci.commands[1]
    assert oci.commands[2][:3] == ["opsi", "database-insights", "create-pe-comanged-database"]
    assert "already enabled" in caplog.text


def _already_enabled_cdb_oci(db_status: str) -> FakeOci:
    return FakeOci(
        fail_on_index=0,
        fail_text="IncorrectState: Either DatabaseManagement is already enabled or request to enable it is already created.",
        insights=[{"database-id": "database-id", "lifecycle-state": "ACTIVE"}],  # skip OPSI create noise
        db_status=db_status,
    )


def _cdb_already_enabled_target() -> Target:
    return Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )


def test_enable_skips_reconcile_when_monitoring_healthy(caplog) -> None:
    oci = _already_enabled_cdb_oci(db_status="UP")
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")
    EnablementService(oci).enable_target(_cdb_already_enabled_target())  # type: ignore[arg-type]

    # DBM already enabled + healthy -> no modify reconcile.
    assert not any("modify-database-management" in c for c in oci.commands)
    assert "skipping reconcile" in caplog.text


def test_enable_reconciles_when_monitoring_not_healthy() -> None:
    oci = _already_enabled_cdb_oci(db_status="DOWN")
    EnablementService(oci).enable_target(_cdb_already_enabled_target())  # type: ignore[arg-type]

    assert any("modify-database-management" in c for c in oci.commands)


def test_enable_force_reconcile_modifies_even_when_healthy() -> None:
    oci = _already_enabled_cdb_oci(db_status="UP")
    EnablementService(oci).enable_target(_cdb_already_enabled_target(), force_reconcile=True)  # type: ignore[arg-type]

    assert any("modify-database-management" in c for c in oci.commands)


def test_reconcile_pdb_uses_pluggable_modify_verb() -> None:
    oci = FakeOci(
        fail_on_index=0,
        fail_text="IncorrectState: Either DatabaseManagement is already enabled or request to enable it is already created.",
    )
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs",
        name="pdb1",
        resource_id="pluggable-database-id",
        database_role="PDB",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="pdb1.example.com",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    assert oci.commands[1][:3] == ["db", "pluggable-database", "modify-pluggable-database-management"]
    assert "--pluggable-database-id" in oci.commands[1]
    assert "--management-type" not in oci.commands[1]
    assert "pdb1.example.com" in oci.commands[1]


def test_enable_cloud_database_reraises_untolerated_error() -> None:
    oci = FakeOci(fail_on_index=0, fail_text="ServiceError: LimitExceeded quota reached")
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    try:
        service.enable_target(target)
    except RuntimeError as exc:
        assert "LimitExceeded" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError to propagate")


def test_enable_skips_opsi_create_when_insight_already_active(caplog) -> None:
    oci = FakeOci(insights=[{"database-id": "database-id", "lifecycle-state": "ACTIVE"}])
    service = EnablementService(oci)  # type: ignore[arg-type]
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    # DBM enable runs; OPSI create is skipped because an ACTIVE insight exists.
    assert oci.commands[0][:3] == ["db", "database", "enable-database-management"]
    assert not any("create-pe-comanged-database" in c for c in oci.commands)
    assert "already ACTIVE" in caplog.text


def test_enable_active_check_uses_reliable_get_when_insight_ocid_known(caplog) -> None:
    # When the insight OCID is configured, the active-check reads it via the
    # reliable GET and never consults the flaky list — so a partial list that
    # dropped the insight cannot drive an unnecessary create.
    class FakeOciGet(FakeOci):
        def __init__(self, detail):
            super().__init__(insights=[])  # list would say "no insight"
            self.detail = detail
            self.list_calls = 0

        def list_opsi_database_insights(self, compartment_id):
            self.list_calls += 1
            return self.insights

        def get_opsi_database_insight(self, insight_id):
            return self.detail

    oci = FakeOciGet({"lifecycle-state": "ACTIVE"})
    service = EnablementService(oci)  # type: ignore[arg-type]
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        private_endpoint_id="dbm-private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
        opsi_private_endpoint_id="opsi-private-endpoint-id",
        opsi_database_insight_id="insight-ocid",
        opsi_credential_details_file="credential-details.json",
        opsi_connection_details_file="connection-details.json",
    )

    service.enable_target(target)

    assert not any("create-pe-comanged-database" in c for c in oci.commands)
    assert oci.list_calls == 0  # reliable GET used, flaky list never touched
    assert "already ACTIVE" in caplog.text


def test_enable_cloud_database_skips_opsi_when_payloads_missing(caplog) -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")
    target = Target(
        kind="dbcs",
        name="db1",
        resource_id="database-id",
        password_secret_id="secret-id",
        private_endpoint_id="private-endpoint-id",
        service_name="ORCLPDB1",
        monitoring_user="DBSNMP",
    )

    service.enable_target(target)

    assert len(oci.commands) == 1
    assert "Skipping Ops Insights" in caplog.text


def test_enable_pdb_uses_pluggable_verb_without_management_type() -> None:
    oci = FakeOci()
    service = EnablementService(oci)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs",
        name="pdb1",
        resource_id="pluggable-database-id",
        database_role="PDB",
        parent_cdb_id="cdb-id",
        password_secret_id="secret-id",
        private_endpoint_id="private-endpoint-id",
        service_name="PDB1",
        monitoring_user="DBSNMP",
    )

    service.enable_target(target)

    command = oci.commands[0]
    assert command[:3] == ["db", "pluggable-database", "enable-pluggable-database-management"]
    assert "--pluggable-database-id" in command
    assert "pluggable-database-id" not in [c for c in command if c == "--database-id"]
    assert "--management-type" not in command


def test_enable_external_logs_next_step(caplog) -> None:
    service = EnablementService(FakeOci())  # type: ignore[arg-type]
    caplog.set_level(logging.INFO, logger="dbman_opsi.enablement")

    service.enable_target(Target(kind="external-db", name="external"))

    assert "run generated Management Agent script" in caplog.text


def test_enable_rejects_unknown_target_kind() -> None:
    service = EnablementService(FakeOci())  # type: ignore[arg-type]

    try:
        service.enable_target(Target(kind="bad", name="bad"))  # type: ignore[arg-type]
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


class _OpsiCreateOci:
    """Fake whose OPSI create raises a propagation error N times, then succeeds."""

    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.create_calls = 0

    def get_opsi_database_insight(self, insight_id):  # not used (no insight id)
        return {}

    def list_opsi_database_insights(self, compartment_id):
        return []

    def run(self, args):
        return None

    def run_tolerating(self, args, tolerated):
        # Only the OPSI create-pe path reaches here in this test.
        self.create_calls += 1
        if self.create_calls <= self.fail_times:
            raise RuntimeError("400-MissingParameter, Provided database resource details were missing.")
        return True


def test_opsi_create_retries_on_propagation_then_succeeds() -> None:
    from dbman_opsi.config import Target

    oci = _OpsiCreateOci(fail_times=2)
    sleeps: list[float] = []
    service = EnablementService(
        oci, opsi_create_attempts=5, opsi_create_delay=0.0, sleeper=lambda d: sleeps.append(d)
    )  # type: ignore[arg-type]
    target = Target(
        kind="dbcs", name="cdb", compartment_id="cmpt", resource_id="db-1",
        service_name="svc", private_endpoint_id="dbmpe", opsi_private_endpoint_id="opsipe",
        opsi_credential_details_file="cred.json", database_resource_type="database",
    )

    # Should retry past the 2 propagation failures and succeed on the 3rd attempt.
    service._create_opsi_pe_comanaged(target)
    assert oci.create_calls == 3
    assert len(sleeps) == 2


def test_opsi_create_raises_after_exhausting_propagation_retries() -> None:
    from dbman_opsi.config import Target

    oci = _OpsiCreateOci(fail_times=99)
    service = EnablementService(oci, opsi_create_attempts=3, opsi_create_delay=0.0, sleeper=lambda d: None)  # type: ignore[arg-type]
    target = Target(
        kind="dbcs", name="cdb", compartment_id="cmpt", resource_id="db-1",
        service_name="svc", private_endpoint_id="dbmpe", opsi_private_endpoint_id="opsipe",
        opsi_credential_details_file="cred.json", database_resource_type="database",
    )
    try:
        service._create_opsi_pe_comanaged(target)
    except RuntimeError as exc:
        assert "database resource" in str(exc)
    else:
        raise AssertionError("expected RuntimeError after retries exhausted")
    assert oci.create_calls == 3


class _DbmWaitOci:
    """Fake whose DBM status reads ENABLING then ENABLED after a poll."""

    def __init__(self, statuses):
        self._statuses = list(statuses)
        self.get_calls = 0

    def get_database(self, database_id):
        self.get_calls += 1
        st = self._statuses[min(self.get_calls - 1, len(self._statuses) - 1)]
        return {"database-management-config": {"management-status": st}}


def test_wait_dbm_enabled_polls_until_enabled() -> None:
    from dbman_opsi.config import Target

    oci = _DbmWaitOci(["ENABLING", "ENABLING", "ENABLED"])
    sleeps: list[float] = []
    service = EnablementService(oci, sleeper=lambda d: sleeps.append(d))  # type: ignore[arg-type]
    service.dbm_wait_attempts = 5
    service.dbm_wait_delay = 0.0
    target = Target(kind="dbcs", name="cdb", resource_id="db-1", database_role="CDB")

    service._wait_dbm_enabled(target)
    assert oci.get_calls == 3          # polled until ENABLED
    assert len(sleeps) == 2            # slept between the two ENABLING reads


def test_wait_dbm_enabled_is_best_effort_when_unreadable() -> None:
    from dbman_opsi.config import Target

    class _Blind:
        pass  # no get_database -> AttributeError, wait returns immediately

    service = EnablementService(_Blind(), sleeper=lambda d: None)  # type: ignore[arg-type]
    service._wait_dbm_enabled(Target(kind="dbcs", name="cdb", resource_id="db-1"))  # must not raise
