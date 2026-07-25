from dbman_opsi.oci_cli import OciCli
from dbman_opsi.runner import CommandResult


class _QueueRunner:
    def __init__(self, *payloads: str) -> None:
        self.payloads = list(payloads)
        self.commands: list[list[str]] = []

    def run(self, args, cwd=None, check=True, retry_on_transient=False):
        self.commands.append(args)
        payload = self.payloads.pop(0) if self.payloads else "{}"
        return CommandResult(tuple(args), payload, "", 0)


def _oci(runner: _QueueRunner) -> OciCli:
    return OciCli("DEFAULT", "eu-frankfurt-1", runner)  # type: ignore[arg-type]


def test_create_named_credential_reuses_existing_id_without_create() -> None:
    runner = _QueueRunner('{"data": [{"name": "dbsnmp", "id": "credential-existing"}]}')

    credential_id = _oci(runner).create_named_credential(
        "compartment-id",
        "dbsnmp",
        "DBSNMP",
        "secret-id",
        "managed-db-id",
    )

    assert credential_id == "credential-existing"
    assert len(runner.commands) == 1
    assert runner.commands[0][5:8] == ["database-management", "named-credential", "list"]


def test_create_named_credential_returns_empty_string_when_response_has_no_id() -> None:
    runner = _QueueRunner('{"data": []}', '{"data": {}}')

    credential_id = _oci(runner).create_named_credential(
        "compartment-id",
        "dbsnmp",
        "DBSNMP",
        "secret-id",
        "managed-db-id",
    )

    assert credential_id == ""
    create_command = runner.commands[1]
    assert create_command[5:8] == [
        "database-management",
        "named-credential",
        "create-named-credential-basic-named-credential-content",
    ]
    assert "--content-password-secret-access-mode" in create_command
    assert "RESOURCE_PRINCIPAL" in create_command


def test_find_managed_database_id_matches_by_name_and_returns_none_when_absent() -> None:
    runner = _QueueRunner(
        '{"data": [{"name": "sales", "id": "managed-sales"}, {"name": "hr", "id": "managed-hr"}]}',
        '{"data": [{"name": "sales", "id": "managed-sales"}]}',
    )
    oci = _oci(runner)

    assert oci.find_managed_database_id("compartment-id", "hr") == "managed-hr"
    assert oci.find_managed_database_id("compartment-id", "missing") is None


def test_get_managed_database_status_returns_database_status() -> None:
    runner = _QueueRunner('{"data": {"database-status": "UP"}}')

    assert _oci(runner).get_managed_database_status("managed-db-id") == "UP"


def test_set_preferred_named_credential_uses_dedicated_update_verb() -> None:
    runner = _QueueRunner()

    _oci(runner).set_preferred_named_credential(
        "managed-db-id",
        "advanced-diagnostics",
        "credential-id",
    )

    command = runner.commands[0]
    assert command[5:8] == [
        "database-management",
        "preferred-credential",
        "update-preferred-credential-update-named-preferred-credential-details",
    ]
    assert "--named-credential-id" in command


def test_list_preferred_and_named_credentials_parse_items() -> None:
    runner = _QueueRunner(
        '{"data": {"items": [{"name": "preferred"}]}}',
        '{"data": {"items": [{"name": "named"}]}}',
    )
    oci = _oci(runner)

    assert oci.list_preferred_credentials("managed-db-id") == [{"name": "preferred"}]
    assert oci.list_named_credentials("compartment-id") == [{"name": "named"}]
