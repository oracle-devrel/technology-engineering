from pathlib import Path

from dbman_opsi.agent_scripts import generate_agent_scripts, render_agent_script
from dbman_opsi.config import EnablementConfig, Target


def test_render_linux_agent_script_includes_required_plugins() -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", compartment_id="compartment-id")
    target = Target(kind="external-db", name="extdb", external_os="linux")

    script = render_agent_script(target, config)

    assert "Service.plugin.dbmgmt.download=true" in script
    assert "Service.plugin.opsi.download=true" in script
    assert "INSTALL_KEY" in script


def test_generate_agent_scripts_only_for_external_targets(tmp_path: Path) -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(
            Target(kind="external-db", name="external db", external_os="linux"),
            Target(kind="dbcs", name="cloud db"),
        ),
    )

    paths = generate_agent_scripts(config, tmp_path)

    assert [path.name for path in paths] == ["external-db-agent.sh"]
    assert paths[0].exists()


def test_render_windows_and_generic_agent_scripts() -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", compartment_id="compartment-id")

    windows = render_agent_script(Target(kind="external-db", name="win", external_os="windows"), config)
    solaris = render_agent_script(Target(kind="external-db", name="sol", external_os="solaris"), config)

    assert "setup.bat" in windows
    assert "Required plugins: dbmgmt and opsi" in solaris
