"""Management Agent script generation for external databases and Exadata."""

from __future__ import annotations

from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target


def _linux_script(target: Target, config: EnablementConfig) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

AGENT_RPM="${{AGENT_RPM:?Set AGENT_RPM to the downloaded OCI Management Agent RPM path}}"
INSTALL_KEY="${{INSTALL_KEY:?Set INSTALL_KEY to the OCI Management Agent install key}}"

cat >/tmp/dbman-opsi-agent.rsp <<EOF
ManagementAgentInstallKey=${{INSTALL_KEY}}
CredentialWalletPassword=
Service.plugin.dbmgmt.download=true
Service.plugin.opsi.download=true
Region={config.region}
CompartmentId={config.compartment_id or ""}
DisplayName={target.name}
EOF

sudo rpm -Uvh "$AGENT_RPM"
sudo /opt/oracle/mgmt_agent/agent_inst/bin/setup.sh opts=/tmp/dbman-opsi-agent.rsp
sudo systemctl enable mgmt_agent || true
sudo systemctl restart mgmt_agent || sudo /opt/oracle/mgmt_agent/agent_inst/bin/agentctl start
"""


def _windows_script(target: Target, config: EnablementConfig) -> str:
    return f"""$ErrorActionPreference = "Stop"
$AgentZip = $env:AGENT_ZIP
$InstallKey = $env:INSTALL_KEY
if (-not $AgentZip) {{ throw "Set AGENT_ZIP to the downloaded OCI Management Agent zip" }}
if (-not $InstallKey) {{ throw "Set INSTALL_KEY to the OCI Management Agent install key" }}

Expand-Archive -Path $AgentZip -DestinationPath C:\\oci-mgmt-agent -Force
@"
ManagementAgentInstallKey=$InstallKey
Service.plugin.dbmgmt.download=true
Service.plugin.opsi.download=true
Region={config.region}
CompartmentId={config.compartment_id or ""}
DisplayName={target.name}
"@ | Out-File -Encoding ascii C:\\oci-mgmt-agent\\dbman-opsi-agent.rsp

& C:\\oci-mgmt-agent\\setup.bat opts=C:\\oci-mgmt-agent\\dbman-opsi-agent.rsp
"""


def _generic_unix_script(target: Target, config: EnablementConfig) -> str:
    return f"""#!/usr/bin/env sh
set -eu

echo "Install OCI Management Agent using the platform package for {target.external_os}."
echo "Use install key from OCI Management Agent service; do not write it into repo files."
echo "Required plugins: dbmgmt and opsi"
echo "Region: {config.region}"
echo "Compartment: {config.compartment_id or ''}"
echo "Display name: {target.name}"
"""


def render_agent_script(target: Target, config: EnablementConfig) -> str:
    if target.external_os == "windows":
        return _windows_script(target, config)
    if target.external_os == "linux" or target.external_os is None:
        return _linux_script(target, config)
    return _generic_unix_script(target, config)


def generate_agent_scripts(config: EnablementConfig, output_dir: str | Path) -> list[Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for target in config.targets:
        if target.kind not in {"external-db", "external-exadata"}:
            continue
        suffix = "ps1" if target.external_os == "windows" else "sh"
        path = destination / f"{target.name.replace(' ', '-').lower()}-agent.{suffix}"
        path.write_text(render_agent_script(target, config), encoding="utf-8")
        if suffix == "sh":
            path.chmod(0o750)
        paths.append(path)
    return paths
