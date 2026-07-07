from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.handoff import generate_handoff, handoff_text


def _config(target: Target) -> EnablementConfig:
    return EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", targets=(target,))


def test_handoff_includes_enable_command_for_ready_cloud_target() -> None:
    target = Target(
        kind="dbcs",
        name="cloud db",
        resource_id="db-id",
        service_name="PDB1",
        monitoring_user="DBSNMP",
        password_secret_id="secret-id",
        private_endpoint_id="pe-id",
    )
    text = handoff_text(target, _config(target))

    assert "enable-database-management" in text
    assert "--database-id db-id" in text
    assert "NOTE: still missing" not in text


def test_handoff_flags_missing_fields() -> None:
    target = Target(kind="dbcs", name="cloud db", resource_id="db-id")
    text = handoff_text(target, _config(target))

    assert "NOTE: still missing" in text
    assert "password_secret_id" in text


def test_handoff_external_target_points_at_agent_script() -> None:
    target = Target(kind="external-db", name="salesdb", external_host="db.internal")
    text = handoff_text(target, _config(target))

    assert "Management Agent script" in text
    assert "enable-database-management" not in text


def test_generate_handoff_writes_scripts_and_doc(tmp_path: Path) -> None:
    target = Target(kind="dbcs", name="cloud db", service_name="PDB1", monitoring_user="DBSNMP")
    paths = generate_handoff(_config(target), tmp_path)

    assert (tmp_path / "cloud-db" / "HANDOFF.md").exists()
    assert (tmp_path / "cloud-db" / "01-create-monitoring-user.sql").exists()
    assert any(path.name == "HANDOFF.md" for path in paths)


def test_generate_handoff_skips_autonomous(tmp_path: Path) -> None:
    target = Target(kind="autonomous", name="adb", resource_id="adb-id")
    paths = generate_handoff(_config(target), tmp_path)

    assert paths == []
    assert not (tmp_path / "adb").exists()
