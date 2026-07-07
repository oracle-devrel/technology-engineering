from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.credentials import CredentialService


class FakeOci:
    def __init__(self, managed=None, db_name="DBMOPSI", pdb_name="PDB1", nc_id="named-credential-id",
                 set_failures=0, fail_text="NotAuthorizedOrNotFound"):
        self.managed = {"DBMOPSI": "managed-cdb-id", "PDB1": "managed-pdb-id"} if managed is None else managed
        self.db_name = db_name
        self.pdb_name = pdb_name
        self.nc_id = nc_id
        self.created: list[dict] = []
        self.preferred: list[tuple] = []
        self.set_failures = set_failures
        self.fail_text = fail_text
        self.set_calls = 0

    def get_database(self, database_id):
        return {"db-name": self.db_name}

    def get_pluggable_database(self, pluggable_database_id):
        return {"pdb-name": self.pdb_name}

    def find_managed_database_id(self, compartment_id, name):
        return self.managed.get(name)

    def list_preferred_credentials(self, managed_database_id):
        status = "SET" if getattr(self, "preferred_set", False) else "NOT_SET"
        return [
            {"credential-name": "PC_READ", "status": status},
            {"credential-name": "PC_WRITE", "status": status},
            {"credential-name": "MONITORING", "status": "SET"},
        ]

    def create_named_credential(self, **kwargs):
        self.created.append(kwargs)
        return self.nc_id

    def set_preferred_named_credential(self, managed_database_id, credential_name, named_credential_id):
        self.set_calls += 1
        if self.set_calls <= self.set_failures:
            raise RuntimeError(f"Command failed (1): ...\nServiceError {self.fail_text}")
        self.preferred.append((managed_database_id, credential_name, named_credential_id))


def _cdb_target(**overrides):
    base = dict(
        kind="dbcs",
        name="dbman-opsi-dbcs-cdb",
        resource_id="database-id",
        compartment_id="compartment-id",
        password_secret_id="secret-id",
        monitoring_user="DBSNMP",
    )
    base.update(overrides)
    return Target(**base)


def _config(*targets):
    return EnablementConfig(profile="cap", region="eu-frankfurt-1", compartment_id="compartment-id", targets=targets)


def test_set_credentials_creates_named_cred_and_sets_both_preferred_slots() -> None:
    oci = FakeOci()
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(_cdb_target(), _config())

    assert decision.status == "set"
    assert len(oci.created) == 1
    assert oci.created[0]["name"] == "DBMOPSI_DBSNMP_NORMAL"
    assert oci.created[0]["associated_resource"] == "database-id"  # managed id == db OCID
    assert [c[1] for c in oci.preferred] == ["PC_READ", "PC_WRITE"]
    assert all(c[0] == "database-id" for c in oci.preferred)
    assert all(c[2] == "named-credential-id" for c in oci.preferred)


def test_set_credentials_pdb_uses_pdb_name() -> None:
    oci = FakeOci()
    service = CredentialService(oci)  # type: ignore[arg-type]
    target = _cdb_target(name="dbman-opsi-dbcs-pdb1", resource_id="pluggable-database-id", database_role="PDB")

    decision = service.set_for_target(target, _config())

    assert decision.status == "set"
    assert oci.created[0]["name"] == "PDB1_DBSNMP_NORMAL"
    assert oci.created[0]["associated_resource"] == "pluggable-database-id"


def test_set_credentials_blocked_when_fields_missing() -> None:
    oci = FakeOci()
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(_cdb_target(password_secret_id=None), _config())

    assert decision.status == "blocked"
    assert "password_secret_id" in decision.detail


def test_set_credentials_skips_non_cloud_targets() -> None:
    oci = FakeOci()
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(Target(kind="external-db", name="ext"), _config())

    assert decision.status == "skipped"
    assert oci.created == []


def test_set_credentials_short_circuits_when_already_set() -> None:
    oci = FakeOci()
    oci.preferred_set = True  # PC_READ/PC_WRITE already SET
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(_cdb_target(), _config())

    assert decision.status == "set"
    assert "already configured" in decision.detail
    assert oci.created == []  # no write attempted


def test_set_credentials_retries_once_on_transient_404() -> None:
    oci = FakeOci(set_failures=1)  # first set attempt fails, retry succeeds
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(_cdb_target(), _config())

    assert decision.status == "set"
    assert [c[1] for c in oci.preferred] == ["PC_READ", "PC_WRITE"]


def test_set_credentials_blocked_with_remediation_on_persistent_failure() -> None:
    oci = FakeOci(set_failures=99, fail_text="NotAuthorizedOrNotFound")
    service = CredentialService(oci)  # type: ignore[arg-type]

    decision = service.set_for_target(_cdb_target(), _config())

    assert decision.status == "blocked"
    assert "Solution:" in decision.detail
    assert "Manual step:" in decision.detail


def test_set_all_returns_one_decision_per_target() -> None:
    oci = FakeOci()
    service = CredentialService(oci)  # type: ignore[arg-type]
    config = _config(
        _cdb_target(),
        _cdb_target(name="dbman-opsi-dbcs-pdb1", resource_id="pluggable-database-id", database_role="PDB"),
    )

    decisions = service.set_all(config)

    assert [d.status for d in decisions] == ["set", "set"]
