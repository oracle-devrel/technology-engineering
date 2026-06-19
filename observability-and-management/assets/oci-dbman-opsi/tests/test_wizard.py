import builtins

from dbman_opsi.wizard import _plan_identity, _safe_discover, _select, run_wizard


class FakeOci:
    def list_compartments(self, tenancy_id):
        return [
            {"id": "deleted-compartment-id", "name": "Old", "lifecycle-state": "DELETED"},
            {"id": "compartment-id", "name": "PoC", "lifecycle-state": "ACTIVE"},
        ]

    def list_vcns(self, compartment_id):
        return [{"id": "vcn-id", "display-name": "vcn"}]

    def list_subnets(self, compartment_id, vcn_id):
        return [{"id": "subnet-id", "display-name": "private"}]

    def list_autonomous_databases(self, compartment_id):
        return [{"id": "adb-id", "display-name": "adb"}]

    def list_vaults(self, compartment_id):
        return [{"id": "vault-id", "display-name": "vault", "management-endpoint": "https://vault"}]

    def list_keys(self, compartment_id, management_endpoint):
        return [{"id": "key-id", "display-name": "key"}]

    def list_secrets(self, compartment_id):
        return [{"id": "secret-id", "secret-name": "dbsnmp"}]

    def list_db_management_private_endpoints(self, compartment_id):
        return [{"id": "dbm-pe-id", "name": "dbm-pe"}]

    def list_opsi_private_endpoints(self, compartment_id):
        return [{"id": "opsi-pe-id", "display-name": "opsi-pe"}]

    def list_data_safe_private_endpoints(self, compartment_id):
        return [{"id": "datasafe-pe-id", "display-name": "datasafe-pe"}]

    def list_policies(self, compartment_id):
        return [
            {
                "statements": [
                    "Allow group db-admins to manage database-family in tenancy",
                    "Allow service dpd to read secret-family in tenancy",
                    "Allow service operations-insights to read secret-family in tenancy",
                ]
            }
        ]


def test_plan_identity_uses_profile_tenancy_and_policy_group(monkeypatch) -> None:
    answers = iter(["1"])
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    tenancy_id, compartment_id, search_compartments, policy_group = _plan_identity(ProfileTenancyOci())  # type: ignore[arg-type]

    assert tenancy_id == "profile-tenancy-id"
    assert compartment_id == "compartment-id"
    assert [compartment["id"] for compartment in search_compartments] == ["compartment-id"]
    assert policy_group == "db-admins"


def test_wizard_discovers_and_selects_resources(monkeypatch) -> None:
    answers = iter(
        [
            "tenancy-id",
            "1",
            "no",
            "1",
            "1",
            "yes",
            "",
            "autonomous",
            "no",
            "1",
            "",
            "",
            "",
            "",  # pillars (defaults to dbm,opsi)
            "no",
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("DEFAULT", "eu-frankfurt-1", FakeOci())  # type: ignore[arg-type]

    assert config.compartment_id == "compartment-id"
    assert config.network.vcn_id == "vcn-id"
    assert config.network.subnet_id == "subnet-id"
    assert config.vault.create_vault is True
    assert config.targets[0].resource_id == "adb-id"
    assert config.targets[0].services == ("dbm", "opsi")


class DbcsOci(FakeOci):
    def list_db_systems(self, compartment_id):
        return [{"id": "dbsys-1", "display-name": "dbmopsi"}]

    def list_databases(self, compartment_id, db_system_id):
        return [
            {
                "id": "database-1",
                "db-name": "DBMOPSI",
                "lifecycle-state": "AVAILABLE",
                "connection-strings": {"cdb-default": "host/DBMOPSI_fra.example.com"},
            }
        ]

    def list_pluggable_databases(self, compartment_id):
        return []


class DbcsWithPdbOci(FakeOci):
    def list_db_systems(self, compartment_id):
        return [{"id": "dbsys-1", "display-name": "db-system"}]

    def list_databases(self, compartment_id, db_system_id):
        return [
            {
                "id": "cdb-1",
                "display-name": "DB0424",
                "db-name": "test",
                "lifecycle-state": "AVAILABLE",
                "connection-strings": {"cdb-default": "host/DB0424.example.com"},
            }
        ]

    def list_pluggable_databases(self, compartment_id):
        return [
            {"id": "pdb-1", "pdb-name": "PDB1", "lifecycle-state": "AVAILABLE", "container-database-id": "cdb-1"},
            {"id": "pdb-2", "pdb-name": "OTHER", "lifecycle-state": "AVAILABLE", "container-database-id": "other-cdb"},
        ]


def test_wizard_defaults_dbcs_target_name_to_display_name_and_filters_pdbs(monkeypatch) -> None:
    answers = iter(
        [
            "tenancy-id",
            "1",          # compartment
            "no",         # create network? no
            "1",          # vcn
            "1",          # subnet
            "yes",        # create vault
            "",           # add target
            "dbcs",       # kind
            "no",         # provision
            "1",          # select database
            "",           # target name default should be DB0424
            "",           # service name default
            "",           # monitoring user
            "1",          # password secret
            "1",          # dbm pe
            "1",          # opsi pe
            "",           # pillars
            "yes",        # discover PDBs
            "",           # add PDB1 default yes
            "no",         # add another target
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("cap", "eu-frankfurt-1", DbcsWithPdbOci())  # type: ignore[arg-type]

    assert config.targets[0].name == "DB0424"
    assert config.targets[1].name == "DB0424-PDB1"
    assert len(config.targets) == 2


def test_wizard_captures_data_safe_selection_for_dbcs(monkeypatch) -> None:
    answers = iter(
        [
            "tenancy-id",
            "1",          # compartment
            "no",         # create network? no
            "1",          # vcn
            "1",          # subnet
            "no",         # create vault? no
            "1",          # vault
            "1",          # key
            "",           # add a target? (default yes)
            "dbcs",       # kind
            "no",         # provision? no
            "1",          # select database
            "",           # target name default
            "",           # service name default
            "",           # monitoring user
            "1",          # password secret
            "1",          # dbm private endpoint
            "1",          # opsi private endpoint
            "dbm,opsi,datasafe",  # pillars
            "1",          # data safe private endpoint
            "no",         # discover PDBs? no
            "no",         # add another target? no
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("cap", "eu-frankfurt-1", DbcsOci())  # type: ignore[arg-type]

    target = config.targets[0]
    assert target.name == "DBMOPSI"
    assert target.resource_id == "database-1"
    assert target.service_name == "DBMOPSI_fra.example.com"
    assert target.password_secret_id == "secret-id"
    assert target.private_endpoint_id == "dbm-pe-id"
    assert target.opsi_private_endpoint_id == "opsi-pe-id"
    assert target.services == ("dbm", "opsi", "datasafe")
    assert target.wants("datasafe") is True
    # db_system_id captured from the selected DB system (needed for DS registration).
    assert target.db_system_id == "dbsys-1"
    assert target.data_safe_private_endpoint_id == "datasafe-pe-id"


def test_wizard_falls_back_when_discovery_fails(monkeypatch) -> None:
    class BrokenOci:
        def list_compartments(self, tenancy_id):
            raise RuntimeError("not configured")

    answers = iter(
        [
            "tenancy-id",
            "compartment-id",
            "yes",
            "no",
            "vault-id",
            "key-id",
            "no",
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("DEFAULT", "eu-frankfurt-1", BrokenOci())  # type: ignore[arg-type]

    assert config.compartment_id == "compartment-id"
    assert config.network.create_test_network is True
    assert config.targets == ()


def test_select_accepts_accidentally_escaped_number(monkeypatch) -> None:
    monkeypatch.setattr(builtins, "input", lambda prompt: "\\2")

    selected = _select(
        "Pick one:",
        [
            {"id": "first", "display-name": "first"},
            {"id": "second", "display-name": "second"},
        ],
    )

    assert selected == {"id": "second", "display-name": "second"}


def test_safe_discover_retries_once_before_fallback(capsys) -> None:
    calls = 0

    def flaky() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary")
        return [{"id": "ok"}]

    assert _safe_discover("targets", flaky) == [{"id": "ok"}]
    assert calls == 2
    assert capsys.readouterr().out == ""


def test_safe_discover_prints_after_retries_exhausted(capsys) -> None:
    calls = 0

    def broken() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        raise RuntimeError("still down")

    assert _safe_discover("targets", broken) == []
    assert calls == 2
    assert "Could not discover targets: still down" in capsys.readouterr().out


class SplitCompartmentOci(FakeOci):
    def list_compartments(self, tenancy_id):
        return [
            {"id": "target-compartment", "name": "demo-observability", "lifecycle-state": "ACTIVE"},
            {"id": "security-compartment", "name": "demo-security", "lifecycle-state": "ACTIVE"},
        ]

    def list_vaults(self, compartment_id):
        if compartment_id == "security-compartment":
            return [{"id": "vault-id", "display-name": "shared-vault", "management-endpoint": "https://vault"}]
        return []

    def list_keys(self, compartment_id, management_endpoint):
        assert compartment_id == "security-compartment"
        return [{"id": "key-id", "display-name": "shared-key"}]


def test_wizard_finds_vaults_in_sibling_compartments(monkeypatch) -> None:
    answers = iter(
        [
            "tenancy-id",
            "1",    # select target compartment with no vault
            "yes",  # create network
            "no",   # do not create vault
            "1",    # select vault discovered in sibling compartment
            "1",    # select key from the vault's compartment
            "no",   # no targets
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("cap", "eu-frankfurt-1", SplitCompartmentOci())  # type: ignore[arg-type]

    assert config.compartment_id == "target-compartment"
    assert config.vault.vault_id == "vault-id"
    assert config.vault.key_id == "key-id"


class ProfileTenancyOci(FakeOci):
    def profile_tenancy(self):
        return "profile-tenancy-id"


def test_wizard_defaults_tenancy_from_profile_and_policy_group(monkeypatch) -> None:
    answers = iter(
        [
            "1",   # compartment
            "",    # existing VCNs discovered, default is no/create_network false
            "1",   # vcn
            "1",   # subnet
            "yes", # create vault
            "no",  # no targets
        ]
    )
    prompts: list[str] = []

    def answer(prompt):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(builtins, "input", answer)

    config = run_wizard("cap", "eu-frankfurt-1", ProfileTenancyOci())  # type: ignore[arg-type]

    assert config.tenancy_id == "profile-tenancy-id"
    assert config.network.create_test_network is False
    assert config.network.vcn_id == "vcn-id"
    assert config.policy_group_name == "db-admins"
    assert all("Tenancy OCID" not in prompt for prompt in prompts)


class IdentityDomainPolicyOci(ProfileTenancyOci):
    def list_policies(self, compartment_id):
        return [
            {
                "statements": [
                    "Allow group 'Default'/'All Domain Users' to read all-resources in tenancy",
                    "Allow service dpd to read secret-family in tenancy",
                    "Allow service operations-insights to read secret-family in tenancy",
                ]
            }
        ]


def test_wizard_ignores_identity_domain_groups_for_policy_group_default(monkeypatch, capsys) -> None:
    answers = iter(
        [
            "1",   # compartment
            "",    # reuse existing vcn
            "1",   # vcn
            "1",   # subnet
            "yes", # create vault
            "no",  # no targets
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("cap", "eu-frankfurt-1", IdentityDomainPolicyOci())  # type: ignore[arg-type]

    assert config.policy_group_name == "dbman-opsi-admins"
    assert "IAM policy groups discovered" not in capsys.readouterr().out


class GroupIdPolicyOci(ProfileTenancyOci):
    def list_policies(self, compartment_id):
        return [
            {
                "statements": [
                    "Allow group id ocid1.group.oc1..aaaaexample to manage database-family in tenancy",
                    "Allow service dpd to read secret-family in tenancy",
                    "Allow service operations-insights to read secret-family in tenancy",
                ]
            }
        ]

    def get_group(self, group_id):
        assert group_id == "ocid1.group.oc1..aaaaexample"
        return {"name": "oci-demo-service-group"}


def test_wizard_resolves_policy_group_ocids(monkeypatch, capsys) -> None:
    answers = iter(
        [
            "1",   # compartment
            "",    # reuse existing vcn
            "1",   # vcn
            "1",   # subnet
            "yes", # create vault
            "no",  # no targets
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))

    config = run_wizard("cap", "eu-frankfurt-1", GroupIdPolicyOci())  # type: ignore[arg-type]

    assert config.policy_group_name == "oci-demo-service-group"
    out = capsys.readouterr().out
    assert "oci-demo-service-group" in out
    assert "ocid1.group" not in out
