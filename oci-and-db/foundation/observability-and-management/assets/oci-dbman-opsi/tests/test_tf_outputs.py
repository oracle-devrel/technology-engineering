from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.tf_outputs import merge_outputs_into_config

OUTPUTS = {
    "subnet_ocid": {"value": "subnet-from-tf"},
    "vcn_ocid": {"value": "vcn-from-tf"},
    "db_management_private_endpoint_ocid": {"value": "pe-from-tf"},
    "provisioned_dbcs_ids": {"value": {"new db": "dbcs-from-tf"}},
    "provisioned_autonomous_database_ids": {"value": {}},
}


def test_merge_fills_network_and_private_endpoint() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        network=NetworkSelection(create_test_network=True),
        targets=(Target(kind="dbcs", name="existing", resource_id="db-id"),),
    )

    merged, changes = merge_outputs_into_config(config, OUTPUTS)

    assert merged.network.subnet_id == "subnet-from-tf"
    assert merged.network.vcn_id == "vcn-from-tf"
    assert merged.targets[0].private_endpoint_id == "pe-from-tf"
    assert "network.subnet_id" in changes


def test_merge_sets_db_system_id_for_provisioned_dbcs_target() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="new db", provision=True),),
    )

    merged, _ = merge_outputs_into_config(config, OUTPUTS)

    assert merged.targets[0].db_system_id == "dbcs-from-tf"
    assert merged.targets[0].resource_id is None


def test_merge_preserves_existing_private_endpoint() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="existing", resource_id="db-id", private_endpoint_id="keep-me"),),
    )

    merged, _ = merge_outputs_into_config(config, OUTPUTS)

    assert merged.targets[0].private_endpoint_id == "keep-me"


def test_merge_with_empty_outputs_is_noop() -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1")

    merged, changes = merge_outputs_into_config(config, {})

    assert changes == []
    assert merged == config
