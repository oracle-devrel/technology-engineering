import pytest

from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.regional_provisioning import (
    CHICAGO_REGION,
    RegionalProvisioningRequest,
    build_regional_provisioning_config,
    default_regional_output,
    prepare_regional_terraform_dir,
)


def test_builds_default_chicago_dbcs_provisioning_config() -> None:
    base = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1",),
        network=NetworkSelection(cidr_block="10.55.0.0/16", subnet_cidr_block="10.55.10.0/24"),
    )

    config = build_regional_provisioning_config(base, RegionalProvisioningRequest())

    assert config.profile == "cap"
    assert config.region == CHICAGO_REGION
    assert config.monitoring_regions == ("eu-frankfurt-1", CHICAGO_REGION)
    assert config.network.create_test_network is True
    assert config.network.cidr_block == "10.55.0.0/16"
    assert config.terraform_dir.endswith(f"zero-start-poc-{CHICAGO_REGION}")
    assert config.targets == (
        Target(
            kind="dbcs",
            name="dbman-opsi-chicago-dbcs",
            provision=True,
            services=("dbm", "opsi"),
            region=CHICAGO_REGION,
        ),
    )


def test_builds_chicago_autonomous_config_with_existing_network() -> None:
    base = EnablementConfig(profile="cap", region="eu-frankfurt-1")
    subnet_id = "ocid1" + ".subnet.oc1..existing"

    config = build_regional_provisioning_config(
        base,
        RegionalProvisioningRequest(
            target_kind="autonomous",
            vcn_id="ocid1.vcn.oc1..existing",
            subnet_id=subnet_id,
        ),
    )

    assert config.targets[0].kind == "autonomous"
    assert config.targets[0].name == "dbman-opsi-chicago-adb"
    assert config.network.create_test_network is False
    assert config.network.vcn_id == "ocid1.vcn.oc1..existing"
    assert config.network.subnet_id == subnet_id


def test_upserts_existing_regional_target_without_dropping_service_name() -> None:
    base = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        targets=(
            Target(
                kind="dbcs",
                name="dbman-opsi-chicago-dbcs",
                region=CHICAGO_REGION,
                resource_id="ocid1.database.oc1..existing",
                service_name="pdb.example",
                provision=False,
            ),
        ),
    )

    config = build_regional_provisioning_config(base, RegionalProvisioningRequest())

    assert len(config.targets) == 1
    assert config.targets[0].provision is True
    assert config.targets[0].resource_id == "ocid1.database.oc1..existing"
    assert config.targets[0].service_name == "pdb.example"


def test_rejects_partial_existing_network() -> None:
    base = EnablementConfig(profile="cap", region="eu-frankfurt-1")

    with pytest.raises(ValueError, match="--vcn-id and --subnet-id"):
        build_regional_provisioning_config(
            base,
            RegionalProvisioningRequest(vcn_id="ocid1.vcn.oc1..existing"),
        )


def test_default_regional_output_uses_region_name() -> None:
    assert default_regional_output(CHICAGO_REGION) == "dbman-opsi.us-chicago-1.local.yaml"


def test_prepare_regional_terraform_dir_copies_stack_files(tmp_path) -> None:
    source = tmp_path / "zero-start-poc"
    destination = tmp_path / "zero-start-poc-us-chicago-1"
    source.mkdir()
    source.joinpath("main.tf").write_text("resource x\n", encoding="utf-8")
    source.joinpath("variables.tf").write_text("variable x {}\n", encoding="utf-8")
    source.joinpath("terraform.tfvars.json").write_text("ignored\n", encoding="utf-8")

    copied = prepare_regional_terraform_dir(source, destination)

    assert sorted(path.name for path in copied) == ["main.tf", "variables.tf"]
    assert destination.joinpath("main.tf").read_text(encoding="utf-8") == "resource x\n"
    assert not destination.joinpath("terraform.tfvars.json").exists()
