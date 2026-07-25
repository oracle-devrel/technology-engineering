from dbman_opsi.config import EnablementConfig, NetworkSelection, Target, VaultSelection
from dbman_opsi.prerequisites import PrerequisiteService


class FakeOci:
    def __init__(self, fail_text: str | None = None) -> None:
        self.commands = []
        self.fail_text = fail_text

    def run(self, args):
        self.commands.append(args)
        if self.fail_text is not None:
            raise RuntimeError(self.fail_text)

    def run_tolerating(self, args, tolerated):
        try:
            self.run(args)
            return True
        except RuntimeError as exc:
            if any(marker in str(exc) for marker in tolerated):
                return False
            raise

    def list_db_management_private_endpoints(self, compartment_id):
        return []

    def list_opsi_private_endpoints(self, compartment_id):
        return []


def test_prepare_creates_private_endpoint_commands() -> None:
    oci = FakeOci()
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
    )

    PrerequisiteService(oci).prepare(config)  # type: ignore[arg-type]

    assert oci.commands[0][:3] == ["database-management", "private-endpoint", "create"]
    assert oci.commands[0][oci.commands[0].index("--is-dns-resolution-enabled") + 1] == "false"
    assert oci.commands[1][:3] == ["opsi", "opsi-private-endpoint", "create"]


def test_prepare_skips_existing_private_endpoints() -> None:
    class ExistingOci(FakeOci):
        def list_db_management_private_endpoints(self, compartment_id):
            return [{"name": "dbman_opsi_dbmgmt_pe"}]

        def list_opsi_private_endpoints(self, compartment_id):
            return [{"display-name": "dbman_opsi_opsi_pe"}]

    oci = ExistingOci()
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
    )

    PrerequisiteService(oci).prepare(config)  # type: ignore[arg-type]

    assert oci.commands == []


def test_prepare_tolerates_create_conflict_when_list_missed_existing_pe() -> None:
    # If the (flaky) list-first check returns empty but the resource really
    # exists, the create's 'already exists' conflict must be an idempotent no-op,
    # not a crash that aborts the whole prepare run.
    oci = FakeOci(fail_text="The private endpoint name is already in use")
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
    )

    # Does not raise; both creates were attempted and tolerated.
    PrerequisiteService(oci).prepare(config)  # type: ignore[arg-type]

    assert oci.commands[0][:3] == ["database-management", "private-endpoint", "create"]
    assert oci.commands[1][:3] == ["opsi", "opsi-private-endpoint", "create"]


def test_prepare_reraises_non_conflict_create_error() -> None:
    # A real failure (not a name conflict) must still propagate.
    oci = FakeOci(fail_text="InvalidParameter: subnet not found")
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        network=NetworkSelection(vcn_id="vcn-id", subnet_id="subnet-id"),
    )

    try:
        PrerequisiteService(oci).prepare(config)  # type: ignore[arg-type]
    except RuntimeError as exc:
        assert "subnet not found" in str(exc)
    else:
        raise AssertionError("Expected the non-conflict create error to propagate")


def test_prepare_creates_secret_when_password_env_is_set(monkeypatch) -> None:
    oci = FakeOci()
    monkeypatch.setenv("DBMAN_PASSWORD", "secret-password")
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        vault=VaultSelection(vault_id="vault-id", key_id="key-id"),
        targets=(Target(kind="dbcs", name="db1"),),
    )

    PrerequisiteService(oci).prepare(config, "DBMAN_PASSWORD")  # type: ignore[arg-type]

    assert oci.commands[0][:3] == ["vault", "secret", "create-base64"]
    assert "secret-password" not in oci.commands[0]
