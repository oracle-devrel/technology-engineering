from dbman_opsi.oci_cli import OciCli
from dbman_opsi.runner import CommandResult, OciError


class FakeRunner:
    def __init__(self, payload):
        self.payload = payload
        self.commands = []
        self.retry_flags = []

    def run(self, args, cwd=None, check=True, retry_on_transient=False):
        self.commands.append(args)
        self.retry_flags.append(retry_on_transient)
        return CommandResult(tuple(args), self.payload, "", 0)


def test_oci_cli_adds_profile_region_and_json_output() -> None:
    runner = FakeRunner('{"data": [{"id": "vcn-id"}]}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    vcns = oci.list_vcns("compartment-id")

    assert vcns == [{"id": "vcn-id"}]
    assert runner.commands[0][:5] == ["oci", "--profile", "DEFAULT", "--region", "eu-frankfurt-1"]
    assert runner.commands[0][-2:] == ["--output", "json"]
    assert runner.retry_flags == [True]


def test_oci_cli_reads_profile_tenancy_from_config(tmp_path, monkeypatch) -> None:
    config = tmp_path / "oci-config"
    config.write_text("[cap]\ntenancy = tenancy-id\n", encoding="utf-8")
    monkeypatch.setenv("OCI_CONFIG_FILE", str(config))
    oci = OciCli("cap", "eu-frankfurt-1", FakeRunner("{}"))  # type: ignore[arg-type]

    assert oci.profile_tenancy() == "tenancy-id"


def test_oci_cli_lists_known_resource_types() -> None:
    runner = FakeRunner('{"data": []}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.list_compartments("tenancy-id") == []
    assert oci.list_subnets("compartment-id", "vcn-id") == []
    assert oci.list_db_systems("compartment-id") == []
    assert oci.list_databases("compartment-id", "db-system-id") == []
    assert oci.get_database("database-id") == {}
    assert oci.list_autonomous_databases("compartment-id") == []
    assert oci.get_autonomous_database("autonomous-database-id") == {}
    assert oci.list_exadata_infrastructure("compartment-id") == []
    assert oci.list_management_agents("compartment-id") == []
    assert oci.list_vaults("compartment-id") == []
    assert oci.list_secrets("compartment-id") == []
    assert oci.list_db_management_private_endpoints("compartment-id") == []
    assert oci.list_opsi_private_endpoints("compartment-id") == []


def test_oci_cli_database_list_does_not_use_unsupported_all_flag() -> None:
    runner = FakeRunner('{"data": []}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.list_databases("compartment-id", "db-system-id") == []

    command = runner.commands[0]
    assert command[5:8] == ["db", "database", "list"]
    assert "--all" not in command


def test_oci_cli_extracts_nested_items_response() -> None:
    runner = FakeRunner('{"data": {"items": [{"name": "pe"}]}}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.list_db_management_private_endpoints("compartment-id") == [{"name": "pe"}]


def test_oci_cli_get_methods_unwrap_data() -> None:
    runner = FakeRunner('{"data": {"lifecycle-state": "ACTIVE"}}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.get_subnet("subnet-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_vcn("vcn-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_route_table("rt-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_security_list("sl-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_db_system("db-system-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_db_management_private_endpoint("pe-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_opsi_private_endpoint("pe-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_secret("secret-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_group("group-id") == {"lifecycle-state": "ACTIVE"}
    assert oci.get_management_agent("agent-id") == {"lifecycle-state": "ACTIVE"}


def test_oci_cli_list_methods_use_expected_verbs() -> None:
    runner = FakeRunner('{"data": []}')
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.list_service_gateways("compartment-id", "vcn-id") == []
    assert oci.list_policies("compartment-id") == []
    assert oci.list_secrets("compartment-id") == []
    assert runner.commands[0][5:8] == ["network", "service-gateway", "list"]
    assert runner.commands[1][5:8] == ["iam", "policy", "list"]
    assert runner.commands[2][5:8] == ["vault", "secret", "list"]


class _StateRunner:
    """Returns a per-lifecycle-state payload; optionally fails on one state.

    Models the OPSI list facade querying one state per call: the multi-state +
    --all combination flaps on the live control plane, so the facade unions
    single-state calls instead.
    """

    def __init__(self, by_state, fail_state=None):
        self.by_state = by_state
        self.fail_state = fail_state
        self.commands = []

    def run(self, args, cwd=None, check=True, retry_on_transient=False):
        self.commands.append(args)
        state = args[args.index("--lifecycle-state") + 1]
        if state == self.fail_state:
            raise RuntimeError("NotAuthorizedOrNotFound")
        return CommandResult(tuple(args), self.by_state.get(state, '{"data": []}'), "", 0)


def test_list_opsi_insights_queries_each_state_and_unions_by_id() -> None:
    runner = _StateRunner({
        "ACTIVE": '{"data": [{"id": "ins-1", "database-id": "db-a", "lifecycle-state": "ACTIVE"}]}',
        "FAILED": '{"data": [{"id": "ins-2", "database-id": "db-b", "lifecycle-state": "FAILED"}]}',
        # ins-1 reappears under another state filter; the union must dedup by OCID.
        "NEEDS_ATTENTION": '{"data": [{"id": "ins-1", "database-id": "db-a", "lifecycle-state": "ACTIVE"}]}',
    })
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    insights = oci.list_opsi_database_insights("compartment-id")

    ids = sorted(i["id"] for i in insights)
    assert ids == ["ins-1", "ins-2"]
    # One call per lifecycle state, each carrying exactly one --lifecycle-state.
    assert len(runner.commands) == len(OciCli.OPSI_INSIGHT_STATES)
    assert all(cmd.count("--lifecycle-state") == 1 for cmd in runner.commands)


def test_list_opsi_insights_tolerates_a_failing_state_call() -> None:
    # A transient failure on one state must not discard the insights gathered
    # from the others (never a false "no insights")...
    runner = _StateRunner(
        {"FAILED": '{"data": [{"id": "ins-2", "database-id": "db-b", "lifecycle-state": "FAILED"}]}'},
        fail_state="ACTIVE",
    )
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    insights, complete = oci.list_opsi_database_insights_complete("compartment-id")

    assert [i["id"] for i in insights] == ["ins-2"]
    # ...but the union is flagged incomplete so callers don't trust it for absence.
    assert complete is False


def test_list_opsi_insights_complete_flag_true_when_all_states_answer() -> None:
    runner = _StateRunner({
        "ACTIVE": '{"data": [{"id": "ins-1", "database-id": "db-a", "lifecycle-state": "ACTIVE"}]}',
    })
    oci = OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    insights, complete = oci.list_opsi_database_insights_complete("compartment-id")

    assert [i["id"] for i in insights] == ["ins-1"]
    assert complete is True


def test_oci_cli_data_safe_list_and_get_command_shapes() -> None:
    runner = FakeRunner('{"data": []}')
    oci = OciCli("cap", "eu-frankfurt-1", runner)  # type: ignore[arg-type]

    assert oci.list_data_safe_targets("compartment-id") == []
    assert oci.list_data_safe_private_endpoints("compartment-id") == []

    runner_get = FakeRunner('{"data": {"id": "dst-1"}}')
    oci_get = OciCli("cap", "eu-frankfurt-1", runner_get)  # type: ignore[arg-type]
    assert oci_get.get_data_safe_target("dst-1") == {"id": "dst-1"}
    cmd = runner_get.commands[0]
    assert cmd[5:9] == ["data-safe", "target-database", "get", "--target-database-id"]


class _FailingRunner:
    def __init__(self, error: RuntimeError):
        self.error = error

    def run(self, args, cwd=None, check=True, retry_on_transient=False):
        raise self.error


def test_run_tolerating_handles_typed_oci_error() -> None:
    oci = OciCli(
        "cap",
        "eu-frankfurt-1",
        _FailingRunner(OciError("already enabled")),
    )  # type: ignore[arg-type]

    assert oci.run_tolerating(["db", "enable"], tolerated=("already enabled",)) is False


def test_run_tolerating_does_not_swallow_plain_runtime_error() -> None:
    oci = OciCli(
        "cap",
        "eu-frankfurt-1",
        _FailingRunner(RuntimeError("already enabled")),
    )  # type: ignore[arg-type]

    try:
        oci.run_tolerating(["db", "enable"], tolerated=("already enabled",))
    except RuntimeError as exc:
        assert "already enabled" in str(exc)
    else:
        raise AssertionError("Expected plain RuntimeError to propagate")


def test_oci_cli_create_data_safe_target_is_idempotent_by_name(tmp_path) -> None:
    runner = FakeRunner('{"data": [{"id": "existing", "display-name": "dbmopsi"}]}')
    oci = OciCli("cap", "eu-frankfurt-1", runner)  # type: ignore[arg-type]
    details = tmp_path / "d.json"
    details.write_text("{}")

    # An existing target with the same display name short-circuits creation.
    target_id = oci.create_data_safe_target("compartment-id", "dbmopsi", str(details))
    assert target_id == "existing"
    # Only the list call happened, no create.
    assert all("create" not in cmd for cmd in runner.commands)


def test_oci_cli_create_data_safe_target_builds_create_command(tmp_path) -> None:
    runner = FakeRunner('{"data": {"id": "new-target"}}')
    oci = OciCli("cap", "eu-frankfurt-1", runner)  # type: ignore[arg-type]
    details = tmp_path / "d.json"
    conn = tmp_path / "c.json"
    creds = tmp_path / "cr.json"
    for f in (details, conn, creds):
        f.write_text("{}")

    target_id = oci.create_data_safe_target(
        "compartment-id", "newdb", str(details), str(conn), str(creds)
    )
    assert target_id == "new-target"
    create_cmd = runner.commands[-1]
    assert create_cmd[5:8] == ["data-safe", "target-database", "create"]
    assert f"file://{details}" in create_cmd
    assert f"file://{conn}" in create_cmd
    assert f"file://{creds}" in create_cmd


def test_oci_cli_create_data_safe_private_endpoint_idempotent() -> None:
    runner = FakeRunner('{"data": [{"id": "pe-existing", "display-name": "dbmopsi-datasafe-pe"}]}')
    oci = OciCli("cap", "eu-frankfurt-1", runner)  # type: ignore[arg-type]
    pe = oci.create_data_safe_private_endpoint(
        "compartment-id", "dbmopsi-datasafe-pe", "vcn-1", "subnet-1"
    )
    assert pe == "pe-existing"
    assert all("create" not in cmd for cmd in runner.commands)
