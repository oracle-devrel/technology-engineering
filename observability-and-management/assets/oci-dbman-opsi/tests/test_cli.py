import json
import os
import uuid
from pathlib import Path

import pytest

from dbman_opsi.checks import PreflightReport, fail, ok
from dbman_opsi.cli import main
from dbman_opsi.config import ConfigError, EnablementConfig, NetworkSelection, Target, load_config, save_config
from dbman_opsi.orchestrator import ConfigureReport, TargetDecision


def _ocid(resource_type: str, suffix: str = "a") -> str:
    return "ocid1" + f".{resource_type}.oc1.." + (suffix * 16)


TENANCY_ID = _ocid("tenancy", "a")
COMPARTMENT_ID = _ocid("compartment", "b")
DATABASE_ID = _ocid("database", "c")
SECRET_ID = _ocid("secret", "d")
SUBNET_ID = _ocid("subnet", "e")
VCN_ID = _ocid("vcn", "f")
PRIVATE_ENDPOINT_ID = _ocid("privateendpoint", "a")
DB_SYSTEM_ID = _ocid("dbsystem", "b")
DATA_SAFE_PRIVATE_ENDPOINT_ID = _ocid("datasafeprivateendpoint", "c")


def test_cli_generate_agent_scripts(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    output_dir = tmp_path / "agents"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            targets=(Target(kind="external-db", name="external", service_name="external", external_os="linux"),),
        ),
    )

    assert main(["generate-agent-scripts", "--config", str(config_path), "--output", str(output_dir)]) == 0
    assert (output_dir / "external-agent.sh").exists()


def test_cli_provision_render_only(tmp_path: Path) -> None:
    terraform_dir = tmp_path / "tf"
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            terraform_dir=str(terraform_dir),
        ),
    )

    assert main(["provision", "--config", str(config_path), "--render-only"]) == 0
    assert (terraform_dir / "terraform.tfvars.json").exists()


def test_cli_loads_dotenv_before_provision(tmp_path: Path, monkeypatch) -> None:
    terraform_dir = tmp_path / "tf"
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            terraform_dir=str(terraform_dir),
        ),
    )
    tmp_path.joinpath(".env.local").write_text("DBMAN_OPSI_TEST_LOADED=yes\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DBMAN_OPSI_TEST_LOADED", raising=False)

    assert main(["provision", "--config", str(config_path), "--render-only"]) == 0

    assert os.environ["DBMAN_OPSI_TEST_LOADED"] == "yes"


def test_cli_init_region_writes_chicago_provisioning_config(tmp_path: Path, capsys) -> None:
    base_config = tmp_path / "base.yaml"
    output_config = tmp_path / "chicago.yaml"
    terraform_dir = tmp_path / "zero-start-poc"
    terraform_dir.mkdir()
    terraform_dir.joinpath("main.tf").write_text("terraform {}\n", encoding="utf-8")
    save_config(
        base_config,
        EnablementConfig(
            profile="cap",
            region="eu-frankfurt-1",
            tenancy_id=TENANCY_ID,
            compartment_id=COMPARTMENT_ID,
            terraform_dir=str(terraform_dir),
        ),
    )

    assert main(
        [
            "init-region",
            "--config",
            str(base_config),
            "--output",
            str(output_config),
            "--target-kind",
            "autonomous",
        ]
    ) == 0

    generated = load_config(output_config)
    assert generated.profile == "cap"
    assert generated.region == "us-chicago-1"
    assert generated.network.create_test_network is True
    assert generated.terraform_dir == str(tmp_path / "zero-start-poc-us-chicago-1")
    assert (tmp_path / "zero-start-poc-us-chicago-1" / "main.tf").exists()
    assert generated.targets[0].kind == "autonomous"
    assert generated.targets[0].provision is True
    assert "dbman-opsi provision --config" in capsys.readouterr().out


def test_cli_init_region_requires_complete_existing_network(tmp_path: Path) -> None:
    base_config = tmp_path / "base.yaml"
    save_config(base_config, EnablementConfig(profile="cap", region="eu-frankfurt-1"))

    with pytest.raises(SystemExit, match="--vcn-id and --subnet-id"):
        main(["init-region", "--config", str(base_config), "--vcn-id", VCN_ID])


def test_cli_threads_single_run_id_into_journaled_runners(tmp_path: Path, monkeypatch) -> None:
    terraform_dir = tmp_path / "tf"
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            terraform_dir=str(terraform_dir),
            dry_run=True,
        ),
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dbman_opsi.cli.uuid.uuid4", lambda: uuid.UUID("12345678-1234-5678-1234-567812345678"))

    assert main(["provision", "--config", str(config_path)]) == 0

    journal_path = tmp_path / "runs" / "12345678-1234-5678-1234-567812345678.jsonl"
    entries = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
    assert entries
    assert {entry["run_id"] for entry in entries} == {"12345678-1234-5678-1234-567812345678"}
    assert {entry["profile"] for entry in entries} == {"DEFAULT"}
    assert {entry["region"] for entry in entries} == {"eu-frankfurt-1"}
    assert all(entry["dry_run"] is True for entry in entries)


def test_cli_journal_last_json_round_trips_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    older = runs / "older.jsonl"
    newer = runs / "newer.jsonl"
    older.write_text(json.dumps({"returncode": 0, "duration_ms": 99}) + "\n", encoding="utf-8")
    newer.write_text(
        json.dumps({"argv_redacted": ["oci", "ok"], "returncode": 0, "duration_ms": 7}) + "\n"
        + json.dumps({"argv_redacted": ["oci", "fail"], "returncode": 1, "duration_ms": 5}) + "\n",
        encoding="utf-8",
    )
    # Explicit, distinct mtimes so `--last` is unambiguous. A double touch() can
    # land in the same mtime tick on coarse-resolution filesystems (e.g. CI),
    # making the "newest" pick a flaky tie.
    os.utime(older, (1_000_000, 1_000_000))
    os.utime(newer, (2_000_000, 2_000_000))
    monkeypatch.chdir(tmp_path)

    assert main(["journal", "--last", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "command_count": 2,
        "total_duration_ms": 12,
        "failures": [{"argv_redacted": ["oci", "fail"], "returncode": 1, "duration_ms": 5}],
    }


def test_cli_journal_by_run_id_human_summary_redacts_ocids(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    runs.joinpath("run-human.jsonl").write_text(
        json.dumps(
            {
                "argv_redacted": ["oci", "db", "get", "--database-id", "<OCI_OCID>"],
                "returncode": 3,
                "duration_ms": 21,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert main(["journal", "run-human"]) == 0

    output = capsys.readouterr().out
    assert "Commands: 1" in output
    assert "Total duration: 21 ms" in output
    assert "Failing commands:" in output
    assert "<OCI_OCID>" in output
    assert "ocid1" + "." not in output


def test_cli_journal_missing_run_id_errors_cleanly(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="journal requires RUN_ID or --last"):
        main(["journal"])


def test_cli_verbose_surfaces_command_timing(tmp_path: Path, monkeypatch, capsys) -> None:
    terraform_dir = tmp_path / "tf"
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            terraform_dir=str(terraform_dir),
            dry_run=True,
        ),
    )
    monkeypatch.chdir(tmp_path)

    assert main(["provision", "--verbose", "--config", str(config_path)]) == 0

    assert "duration_ms=" in capsys.readouterr().out


def test_cli_generate_db_scripts(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    output_dir = tmp_path / "db-scripts"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            targets=(Target(kind="dbcs", name="cloud db", service_name="PDB1", monitoring_user="DBSNMP"),),
        ),
    )

    assert main(["generate-db-scripts", "--config", str(config_path), "--output", str(output_dir)]) == 0
    assert (output_dir / "cloud-db" / "02-grant-basic-monitoring.sql").exists()


def test_cli_generate_opsi_payloads(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    output_dir = tmp_path / "opsi"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            targets=(Target(kind="dbcs", name="cloud db", service_name="PDB1", password_secret_id=SECRET_ID),),
        ),
    )

    assert main(["generate-opsi-payloads", "--config", str(config_path), "--output", str(output_dir)]) == 0
    assert (output_dir / "cloud-db" / "credential-details.json").exists()


def test_cli_cross_region_updates_config_and_prints_poc_steps(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="cap",
            region="eu-frankfurt-1",
            targets=(
                Target(kind="dbcs", name="frankfurt-cdb", service_name="cdb.example"),
                Target(kind="autonomous", name="chicago-adb", region="us-chicago-1"),
            ),
        ),
    )

    assert main(
        [
            "cross-region",
            "--config",
            str(config_path),
            "--regions",
            "eu-frankfurt-1,us-chicago-1",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "OPSI cross-region monitoring: enabled" in output
    assert "Data Object Explorer" in output
    assert load_config(config_path).monitoring_regions == ("eu-frankfurt-1", "us-chicago-1")


def test_cli_prepare_prereqs_dry_run(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            network=NetworkSelection(vcn_id=VCN_ID, subnet_id=SUBNET_ID),
        ),
    )

    assert main(["prepare-prereqs", "--config", str(config_path), "--dry-run"]) == 0
    assert "database-management private-endpoint create" in capsys.readouterr().out


def test_cli_accepts_apply_flag_for_prepare_prereqs(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            dry_run=True,
        ),
    )

    assert main(["prepare-prereqs", "--config", str(config_path), "--apply"]) == 0
    assert "Skipping private endpoints" in capsys.readouterr().out


def _save_basic_config(config_path: Path) -> None:
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            tenancy_id=TENANCY_ID,
            compartment_id=COMPARTMENT_ID,
            targets=(Target(kind="dbcs", name="cloud db", resource_id=DATABASE_ID, service_name="PDB1"),),
        ),
    )


def test_cli_preflight_json_reports_ok(tmp_path: Path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)

    class FakePreflight:
        def __init__(self, oci) -> None:
            pass

        def run(self, config, db_check=None):
            return PreflightReport(tenancy_checks=(ok("iam.policies", "present"),))

    monkeypatch.setattr("dbman_opsi.cli.PreflightService", FakePreflight)

    assert main(["preflight", "--config", str(config_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_cli_preflight_returns_nonzero_when_not_ready(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)

    class FakePreflight:
        def __init__(self, oci) -> None:
            pass

        def run(self, config, db_check=None):
            return PreflightReport(network_checks=(fail("network.service_gateway", "missing", "create"),))

    monkeypatch.setattr("dbman_opsi.cli.PreflightService", FakePreflight)

    assert main(["preflight", "--config", str(config_path)]) == 1


def test_cli_preflight_ingests_db_check_file(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)
    spool = tmp_path / "validate.out"
    spool.write_text("USERNAME ACCOUNT_STATUS\nDBSNMP OPEN\nCREATE SESSION\nSELECT ANY DICTIONARY\n", encoding="utf-8")
    captured: dict[str, object] = {}

    class FakePreflight:
        def __init__(self, oci) -> None:
            pass

        def run(self, config, db_check=None):
            captured["db_check"] = db_check
            return PreflightReport(tenancy_checks=(ok("iam.policies", "present"),))

    monkeypatch.setattr("dbman_opsi.cli.PreflightService", FakePreflight)

    assert main(["preflight", "--config", str(config_path), "--db-check-file", str(spool)]) == 0
    assert captured["db_check"] is not None
    assert captured["db_check"].ok  # type: ignore[union-attr]


def test_cli_configure_db_side_only_uses_handoff_mode(tmp_path: Path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)
    captured: dict[str, object] = {}

    class FakeConfigure:
        def __init__(self, oci, enablement=None, datasafe=None) -> None:
            pass

        def configure(self, config, mode="plan", handoff_dir="x", force=False):
            captured["mode"] = mode
            return ConfigureReport(
                mode=mode,
                preflight=PreflightReport(),
                decisions=(TargetDecision("cloud db", "dbcs", "oci-native", "handoff", "packet"),),
            )

    monkeypatch.setattr("dbman_opsi.cli.ConfigureService", FakeConfigure)

    assert main(["configure", "--config", str(config_path), "--db-side-only"]) == 0
    assert captured["mode"] == "db-side-only"
    assert "[HANDOFF] cloud db" in capsys.readouterr().out


def test_cli_configure_apply_sets_preferred_credentials(tmp_path: Path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)
    captured: dict[str, object] = {}

    class FakeConfigure:
        def __init__(self, oci, enablement=None, datasafe=None) -> None:
            pass

        def configure(self, config, mode="plan", handoff_dir="x", force=False):
            return ConfigureReport(
                mode=mode,
                preflight=PreflightReport(),
                decisions=(TargetDecision("cloud db", "dbcs", "oci-native", "enabled", "done"),),
            )

    class FakeCredentialService:
        def __init__(self, oci) -> None:
            pass

        def set_all(self, config):
            captured["credential_config"] = config
            from dbman_opsi.credentials import CredentialDecision

            return [CredentialDecision("cloud db", "set", "PC_READ, PC_WRITE configured")]

    monkeypatch.setattr("dbman_opsi.cli.ConfigureService", FakeConfigure)
    monkeypatch.setattr("dbman_opsi.cli.CredentialService", FakeCredentialService)

    assert main(["configure", "--config", str(config_path), "--apply"]) == 0

    assert captured["credential_config"] is not None
    assert "credentials cloud db: set" in capsys.readouterr().out


def test_cli_configure_apply_can_skip_preferred_credentials(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)
    captured = {"credentials_called": False}

    class FakeConfigure:
        def __init__(self, oci, enablement=None, datasafe=None) -> None:
            pass

        def configure(self, config, mode="plan", handoff_dir="x", force=False):
            return ConfigureReport(
                mode=mode,
                preflight=PreflightReport(),
                decisions=(TargetDecision("cloud db", "dbcs", "oci-native", "enabled", "done"),),
            )

    class FakeCredentialService:
        def __init__(self, oci) -> None:
            pass

        def set_all(self, config):
            captured["credentials_called"] = True
            return []

    monkeypatch.setattr("dbman_opsi.cli.ConfigureService", FakeConfigure)
    monkeypatch.setattr("dbman_opsi.cli.CredentialService", FakeCredentialService)

    assert main(["configure", "--config", str(config_path), "--apply", "--skip-credentials"]) == 0

    assert captured["credentials_called"] is False


def test_cli_import_tf_outputs_merges_and_writes(tmp_path: Path, monkeypatch) -> None:
    from dbman_opsi.config import load_config

    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            network=NetworkSelection(create_test_network=True),
            targets=(Target(kind="dbcs", name="cloud db", resource_id=DATABASE_ID, service_name="PDB1"),),
        ),
    )

    monkeypatch.setattr(
        "dbman_opsi.cli.read_terraform_outputs",
        lambda terraform_dir, runner: {
            "subnet_ocid": {"value": SUBNET_ID},
            "db_management_private_endpoint_ocid": {"value": PRIVATE_ENDPOINT_ID},
        },
    )

    assert main(["import-tf-outputs", "--config", str(config_path)]) == 0
    reloaded = load_config(config_path)
    assert reloaded.network.subnet_id == SUBNET_ID
    assert reloaded.targets[0].private_endpoint_id == PRIVATE_ENDPOINT_ID


def test_cli_import_tf_outputs_resolves_provisioned_dbcs_database_id(tmp_path: Path, monkeypatch) -> None:
    from dbman_opsi.config import load_config

    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            targets=(Target(kind="dbcs", name="cloud db", provision=True),),
        ),
    )

    monkeypatch.setattr(
        "dbman_opsi.cli.read_terraform_outputs",
        lambda terraform_dir, runner: {
            "provisioned_dbcs_ids": {"value": {"cloud db": DB_SYSTEM_ID}},
            "provisioned_autonomous_database_ids": {"value": {}},
        },
    )

    class FakeOci:
        def __init__(self, profile, region, runner) -> None:
            pass

        def list_databases(self, compartment_id: str, db_system_id: str):
            assert compartment_id == COMPARTMENT_ID
            assert db_system_id == DB_SYSTEM_ID
            return [{"id": DATABASE_ID, "db-name": "CDB1"}]

    monkeypatch.setattr("dbman_opsi.cli.OciCli", FakeOci)

    assert main(["import-tf-outputs", "--config", str(config_path)]) == 0

    reloaded = load_config(config_path)
    assert reloaded.targets[0].db_system_id == DB_SYSTEM_ID
    assert reloaded.targets[0].resource_id == DATABASE_ID
    assert reloaded.targets[0].service_name == "CDB1"


def test_cli_import_tf_outputs_dry_run_does_not_write(tmp_path: Path, monkeypatch, capsys) -> None:
    from dbman_opsi.config import load_config

    config_path = tmp_path / "config.yaml"
    save_config(config_path, EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1",
                                              network=NetworkSelection(create_test_network=True)))
    monkeypatch.setattr("dbman_opsi.cli.read_terraform_outputs",
                        lambda terraform_dir, runner: {"subnet_ocid": {"value": "subnet-from-tf"}})

    assert main(["import-tf-outputs", "--config", str(config_path), "--dry-run"]) == 0
    assert "Dry run" in capsys.readouterr().out
    assert load_config(config_path).network.subnet_id is None


def test_cli_import_tf_outputs_rejects_invalid_merged_config(tmp_path: Path, monkeypatch) -> None:
    from dbman_opsi.config import load_config

    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            network=NetworkSelection(create_test_network=True),
        ),
    )
    before = config_path.read_text(encoding="utf-8")
    monkeypatch.setattr(
        "dbman_opsi.cli.read_terraform_outputs",
        lambda terraform_dir, runner: {"subnet_ocid": {"value": "not-an-ocid"}},
    )

    with pytest.raises(ConfigError, match="network.subnet_id"):
        main(["import-tf-outputs", "--config", str(config_path)])

    assert config_path.read_text(encoding="utf-8") == before
    assert load_config(config_path).network.subnet_id is None


def test_cli_configure_blocked_returns_nonzero(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    _save_basic_config(config_path)

    class FakeConfigure:
        def __init__(self, oci, enablement=None, datasafe=None) -> None:
            pass

        def configure(self, config, mode="plan", handoff_dir="x", force=False):
            return ConfigureReport(
                mode=mode,
                preflight=PreflightReport(),
                decisions=(TargetDecision("cloud db", "dbcs", "oci-native", "blocked", "no SGW"),),
            )

    monkeypatch.setattr("dbman_opsi.cli.ConfigureService", FakeConfigure)

    assert main(["configure", "--config", str(config_path)]) == 1


def test_cli_data_safe_dry_run_reports_ready(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            targets=(
                Target(
                    kind="dbcs",
                    name="dbmopsi",
                    compartment_id=COMPARTMENT_ID,
                    db_system_id=DB_SYSTEM_ID,
                    service_name="PDB1",
                    data_safe_private_endpoint_id=DATA_SAFE_PRIVATE_ENDPOINT_ID,
                    services=("dbm", "opsi", "datasafe"),
                ),
                Target(kind="dbcs", name="no-ds", service_name="PDB2", services=("dbm", "opsi")),
            ),
        ),
    )

    # Dry-run: no live registration, exit 0; only the opted-in target is processed.
    assert main(["data-safe", "--config", str(config_path)]) == 0
    out = capsys.readouterr().out
    assert "data-safe dbmopsi" in out
    assert "no-ds" not in out


def test_cli_data_safe_blocked_returns_nonzero(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="DEFAULT",
            region="eu-frankfurt-1",
            compartment_id=COMPARTMENT_ID,
            # Missing db_system_id / PE and no subnet to create one.
            targets=(Target(kind="dbcs", name="dbmopsi", compartment_id=COMPARTMENT_ID,
                            service_name="PDB1",
                            services=("dbm", "opsi", "datasafe")),),
        ),
    )

    assert main(["data-safe", "--config", str(config_path)]) == 1


def test_cli_db_exec_plan_non_prod(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="cap",
            region="eu-frankfurt-1",
            targets=(Target(kind="dbcs", name="dbmopsi", service_name="PDB1"),),
        ),
    )
    assert main(["db-exec", "--config", str(config_path), "--scripts-dir", str(tmp_path / "s")]) == 0
    out = capsys.readouterr().out
    assert "db-exec dbmopsi: executed" in out
    # Scripts were generated.
    assert (tmp_path / "s" / "dbmopsi" / "01-create-monitoring-user.sql").exists()


def test_cli_db_exec_plan_production_hands_off(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yaml"
    save_config(
        config_path,
        EnablementConfig(
            profile="emdemo",
            region="us-phoenix-1",
            targets=(Target(kind="dbcs", name="dbmopsi", service_name="PDB1"),),
        ),
    )
    assert main(["db-exec", "--config", str(config_path), "--scripts-dir", str(tmp_path / "s")]) == 0
    assert "db-exec dbmopsi: handoff" in capsys.readouterr().out
