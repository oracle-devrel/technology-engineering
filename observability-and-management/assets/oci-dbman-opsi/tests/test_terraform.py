from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.terraform import render_tfvars, run_terraform, write_tfvars


def test_render_tfvars_includes_network_policy_and_targets() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        network=NetworkSelection(create_test_network=True),
        targets=(Target(kind="dbcs", name="db1", provision=True),),
    )

    tfvars = render_tfvars(config)

    assert tfvars["create_test_network"] is True
    assert tfvars["config_file_profile"] == "DEFAULT"
    assert tfvars["targets"] == [{"kind": "dbcs", "name": "db1", "resource_id": None, "provision": True, "management_type": "ADVANCED"}]
    assert "policy_statements" in tfvars


class FakeRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, args, cwd=None):
        self.calls.append((args, cwd))


def test_write_tfvars_and_run_terraform(tmp_path) -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", terraform_dir=str(tmp_path))
    runner = FakeRunner()

    path = write_tfvars(config)
    run_terraform(config, runner)  # type: ignore[arg-type]

    assert path.exists()
    assert [call[0][0] for call in runner.calls] == ["terraform", "terraform"]
