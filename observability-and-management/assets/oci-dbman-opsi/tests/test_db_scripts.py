from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.db_scripts import (
    advanced_grants_sql,
    data_safe_privileges_sql,
    generate_db_scripts,
    monitoring_user_sql,
    performance_hub_sql,
    validation_sql,
)


def test_monitoring_user_sql_prompts_for_password_and_container() -> None:
    target = Target(kind="dbcs", name="db1", service_name="PDB1", monitoring_user="DBSNMP")

    sql = monitoring_user_sql(target)

    assert "accept monitoring_password char hide" in sql
    assert "alter session set container" in sql
    assert '"&monitoring_password"' not in sql


def test_validation_sql_checks_expected_grants() -> None:
    sql = validation_sql(Target(kind="exadata", name="exa", monitoring_user="DBSNMP"))

    assert "SELECT ANY DICTIONARY" in sql
    assert "SELECT_CATALOG_ROLE" in sql
    assert "DBMS_MONITOR" in sql


def test_advanced_grants_include_performance_hub_privileges() -> None:
    # The OCI Console "Performance Hub requires granting of appropriate user
    # privileges" prompt maps to exactly these grants for the monitoring user.
    sql = advanced_grants_sql(Target(kind="dbcs", name="db1", monitoring_user="DBSNMP")).lower()

    assert "grant create procedure to &monitoring_user" in sql
    assert "grant alter system to &monitoring_user" in sql
    assert "grant advisor to &monitoring_user" in sql
    assert "grant execute on sys.dbms_workload_repository to &monitoring_user" in sql
    assert "grant select any dictionary to &monitoring_user" in sql
    assert "grant select_catalog_role to &monitoring_user" in sql


def test_advanced_grants_include_sql_tuning_set_privilege() -> None:
    # ORA-13750: creating a SQL Tuning Set from Performance Hub needs this grant.
    sql = advanced_grants_sql(Target(kind="dbcs", name="db1", monitoring_user="DBSNMP")).lower()
    assert "grant administer sql tuning set to &monitoring_user" in sql
    assert "grant administer any sql tuning set to &monitoring_user" in sql


def test_performance_hub_sql_enables_awr_autoflush_for_cdb() -> None:
    # CDB target: set the instance master switch; no PDB snapshot-interval call.
    sql = performance_hub_sql(Target(kind="dbcs", name="cdb", database_role="CDB")).lower()
    assert "alter system set awr_pdb_autoflush_enabled = true scope = both" in sql
    assert "modify_snapshot_settings" not in sql


def test_performance_hub_sql_sets_pdb_snapshot_interval_and_seeds() -> None:
    # PDB target: autoflush + non-zero snapshot interval + an initial snapshot,
    # so ADDM Spotlight / AWR Explorer have PDB-level data.
    sql = performance_hub_sql(
        Target(kind="dbcs", name="pdb1", database_role="PDB", service_name="PDB1")
    ).lower()
    assert "awr_pdb_autoflush_enabled = true" in sql
    assert "modify_snapshot_settings(interval => 60, retention => 11520)" in sql
    assert "create_snapshot" in sql


def test_generate_db_scripts_includes_performance_hub_script(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="DEFAULT", region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="cdb", database_role="CDB"),),
    )
    paths = generate_db_scripts(config, tmp_path)
    assert any(p.name == "05-enable-performance-hub.sql" for p in paths)


def test_validation_sql_checks_performance_hub_privileges() -> None:
    sql = validation_sql(Target(kind="dbcs", name="db1", monitoring_user="DBSNMP"))

    assert "CREATE PROCEDURE" in sql
    assert "ALTER SYSTEM" in sql
    assert "ADVISOR" in sql
    assert "DBMS_WORKLOAD_REPOSITORY" in sql


def test_data_safe_privileges_sql_creates_account_and_grants() -> None:
    sql = data_safe_privileges_sql(
        Target(kind="dbcs", name="db1", monitoring_user="DBSNMP", services=("dbm", "opsi", "datasafe"))
    ).lower()
    assert "data safe service account" in sql
    # Reusing an existing account must not reset its password when blank.
    assert "blank to keep existing" in sql
    assert "grant create session to &ds_user" in sql
    assert "grant select_catalog_role to &ds_user" in sql
    assert "grant audit_viewer to &ds_user" in sql
    assert "grant audit_admin to &ds_user" in sql


def test_generate_db_scripts_emits_data_safe_only_when_opted_in(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="DEFAULT", region="eu-frankfurt-1",
        targets=(
            Target(kind="dbcs", name="with-ds", services=("dbm", "opsi", "datasafe")),
            Target(kind="dbcs", name="without-ds", services=("dbm", "opsi")),
        ),
    )
    paths = generate_db_scripts(config, tmp_path)
    names = {str(p) for p in paths}
    assert any(p.name == "06-enable-data-safe.sql" and p.parent.name == "with-ds" for p in paths)
    assert not (tmp_path / "without-ds" / "06-enable-data-safe.sql").exists()
    # README reflects the pillar opt-in.
    assert "06-enable-data-safe.sql" in (tmp_path / "with-ds" / "README.md").read_text()


def test_generate_db_scripts_for_dbcs_and_exadata_only(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(
            Target(kind="dbcs", name="cloud db"),
            Target(kind="exadata", name="exa db"),
            Target(kind="autonomous", name="adb"),
        ),
    )

    paths = generate_db_scripts(config, tmp_path)

    names = {path.name for path in paths}
    assert "01-create-monitoring-user.sql" in names
    assert "04-validate-monitoring-user.sql" in names
    assert (tmp_path / "cloud-db").exists()
    assert (tmp_path / "exa-db").exists()
    assert not (tmp_path / "adb").exists()
