from pathlib import Path

import pytest

from dbman_opsi.config import (
    ConfigError,
    EnablementConfig,
    Target,
    load_config,
    save_config,
    validate_config,
)


def _ocid(resource_type: str, suffix: str = "a") -> str:
    return "ocid1" + f".{resource_type}.oc1.." + (suffix * 16)


def test_config_round_trip_preserves_local_references(tmp_path: Path) -> None:
    tenancy_id = "ocid1" + ".tenancy.oc1..aaaaaaaaexample"
    compartment_id = "ocid1" + ".compartment.oc1..bbbbbbbbexample"
    adb_id = "ocid1" + ".autonomousdatabase.oc1..ccccccccexample"
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1", "us-chicago-1"),
        tenancy_id=tenancy_id,
        compartment_id=compartment_id,
        targets=(Target(kind="autonomous", name="adb", region="us-chicago-1", resource_id=adb_id),),
    )
    path = tmp_path / "config.yaml"

    save_config(path, config)

    loaded = load_config(path)
    assert loaded.profile == "DEFAULT"
    assert loaded.monitoring_regions == ("eu-frankfurt-1", "us-chicago-1")
    assert loaded.tenancy_id == tenancy_id
    assert loaded.targets[0].region == "us-chicago-1"
    assert loaded.targets[0].kind == "autonomous"


def test_config_round_trip_preserves_data_safe_and_services(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        targets=(
            Target(
                kind="dbcs",
                name="dbmopsi",
                service_name="db_high",
                services=("dbm", "opsi", "datasafe"),
                data_safe_target_id="ocid1" + ".datasafetargetdatabase.oc1..ddddexample",
                data_safe_private_endpoint_id="ocid1" + ".datasafeprivateendpoint.oc1..eeeeexample",
            ),
        ),
    )
    path = tmp_path / "config.yaml"

    save_config(path, config)
    loaded = load_config(path)

    target = loaded.targets[0]
    # services must round-trip back to a tuple (YAML stores it as a list).
    assert target.services == ("dbm", "opsi", "datasafe")
    assert target.wants("datasafe") is True
    assert target.data_safe_target_id.endswith("ddddexample")
    assert target.data_safe_private_endpoint_id.endswith("eeeeexample")


def test_target_defaults_to_dbm_and_opsi_only() -> None:
    target = Target(kind="dbcs", name="legacy")
    assert target.services == ("dbm", "opsi")
    assert target.wants("datasafe") is False


def test_config_sanitized_view_redacts_sensitive_shapes() -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", tenancy_id="ocid1" + ".tenancy.oc1..x")

    assert config.sanitized()["tenancy_id"] == "<OCI_OCID>"


def test_validate_config_reports_bad_target_kind() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="mysql", name="bad-kind"),),  # type: ignore[arg-type]
    )

    problems = validate_config(config)

    assert (
        "targets[0] bad-kind: kind must be one of autonomous, dbcs, exadata, external-db, external-exadata"
        in problems
    )


def test_validate_config_requires_service_name_for_dbcs() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="dbcs"),),
    )

    assert validate_config(config) == ["targets[0] dbcs: service_name is required for dbcs targets"]


def test_validate_config_allows_provisioned_dbcs_without_service_name() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="dbcs", provision=True),),
    )

    assert validate_config(config) == []


def test_validate_config_reports_malformed_id_field() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(
            Target(
                kind="autonomous",
                name="adb",
                resource_id="not-an-ocid",
            ),
        ),
    )

    assert validate_config(config) == ["targets[0] adb: resource_id must look like an OCI OCID"]


def test_validate_config_reports_overlong_ocid_field() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(
            Target(
                kind="autonomous",
                name="adb",
                resource_id="ocid1" + ".database.oc1.." + ("a" * 300),
            ),
        ),
    )

    assert validate_config(config) == ["targets[0] adb: resource_id must look like an OCI OCID"]


def test_load_config_reports_all_validation_problems(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        "\n".join(
            [
                "profile: DEFAULT",
                "region: eu-frankfurt-1",
                "tenancy_id: invalid-tenancy",
                "targets:",
                "  - kind: mysql",
                "    name: broken",
                "    resource_id: also-invalid",
                "    services: [dbm, metrics]",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as error:
        load_config(path)

    message = str(error.value)
    assert "tenancy_id" in message
    assert "kind" in message
    assert "resource_id" in message
    assert "services" in message


def test_validate_config_reports_bad_region_selection() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1", "bad-region", "bad-region"),
        targets=(Target(kind="autonomous", name="adb", region="bad target"),),
    )

    problems = validate_config(config)

    assert "monitoring_regions contains invalid OCI region identifiers: bad-region, bad-region" in problems
    assert "targets[0] adb: region must look like an OCI region identifier" in problems


def test_validate_config_reports_duplicate_monitoring_regions() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1", "us-chicago-1", "us-chicago-1"),
    )

    assert validate_config(config) == ["monitoring_regions contains duplicate regions: us-chicago-1"]


def test_load_config_rejects_dbcs_without_service_name(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        "\n".join(
            [
                "profile: DEFAULT",
                "region: eu-frankfurt-1",
                "targets:",
                "  - kind: dbcs",
                "    name: dbcs",
                f"    resource_id: {_ocid('database')}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="service_name"):
        load_config(path)


def test_load_config_keeps_valid_config_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "valid.yaml"
    path.write_text(
        "\n".join(
            [
                "profile: DEFAULT",
                "region: eu-frankfurt-1",
                f"tenancy_id: {_ocid('tenancy')}",
                "network:",
                f"  vcn_id: {_ocid('vcn', 'b')}",
                "targets:",
                "  - kind: dbcs",
                "    name: dbcs",
                f"    resource_id: {_ocid('database', 'c')}",
                "    service_name: db_high",
                "    services: [dbm, opsi]",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_config(path)

    assert loaded.profile == "DEFAULT"
    assert loaded.tenancy_id == _ocid("tenancy")
    assert loaded.network.vcn_id == _ocid("vcn", "b")
    assert loaded.targets[0] == Target(
        kind="dbcs",
        name="dbcs",
        resource_id=_ocid("database", "c"),
        service_name="db_high",
        services=("dbm", "opsi"),
    )
