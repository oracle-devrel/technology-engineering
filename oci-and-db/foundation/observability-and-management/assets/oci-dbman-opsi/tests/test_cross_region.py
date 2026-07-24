from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.cross_region import cross_region_plan, format_cross_region_plan, parse_regions


def test_parse_regions_trims_and_omits_empty_entries() -> None:
    assert parse_regions("eu-frankfurt-1, us-chicago-1,,") == ("eu-frankfurt-1", "us-chicago-1")


def test_cross_region_plan_groups_opsi_targets_by_selected_regions() -> None:
    config = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1", "us-chicago-1"),
        targets=(
            Target(kind="dbcs", name="frankfurt-cdb", service_name="cdb.example", services=("dbm", "opsi")),
            Target(
                kind="autonomous",
                name="chicago-adb",
                region="us-chicago-1",
                services=("dbm", "opsi"),
            ),
            Target(
                kind="autonomous",
                name="security-only",
                region="us-chicago-1",
                services=("datasafe",),
            ),
        ),
    )

    plan = cross_region_plan(config)

    assert plan.enabled is True
    assert plan.targets_by_region == (
        ("eu-frankfurt-1", ("frankfurt-cdb",)),
        ("us-chicago-1", ("chicago-adb",)),
    )
    assert plan.warnings == ()


def test_cross_region_plan_warns_when_target_region_not_selected() -> None:
    config = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        monitoring_regions=("eu-frankfurt-1",),
        targets=(Target(kind="autonomous", name="chicago-adb", region="us-chicago-1"),),
    )

    plan = cross_region_plan(config)

    assert plan.enabled is False
    assert plan.warnings == ("us-chicago-1 has OPSI targets but is not selected in monitoring_regions",)
    assert "Configuration and Capacity dashboards" in format_cross_region_plan(plan)
