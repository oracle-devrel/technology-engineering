#!/bin/bash
# SPDX-License-Identifier: UPL-1.0
# Install the OCI Management Agent on Linux and register it with OCI.
#
# This is the Linux counterpart of the Windows agent install in
# Install-OCI-Prometheus.ps1. It lets ANY Linux host — including a VM in another
# cloud (GCP, AWS, on-prem) — push aggregated Prometheus metrics to OCI Monitoring
# via a Prometheus (/federate) data source. Pair it with a local Prometheus that
# scrapes your exporters; then add the data source with manage-oci-datasource.sh.
#
# The agent installer.sh takes the response file POSITIONALLY (same quirk as the
# Windows installer.bat — see KB-07). The Linux agent requires JDK 8 (>= 8u281)
# with JAVA_HOME set (KB-24); this script installs OpenJDK 8 if needed and exports
# JAVA_HOME before running the installer.
#
# USAGE:
#   sudo ./install-oci-agent-linux.sh --agent-zip <path|url> --rsp <input.rsp>
#
#   --agent-zip <path|url>  Linux agent ZIP. Fetch it (authenticated) on an OCI-CLI
#                           host with:
#     oci os object get --namespace <ns> --bucket-name agent_images \
#       --name Linux-x86_64/latest/oracle.mgmt_agent.zip --file oracle.mgmt_agent.zip
#     (namespace/object from: oci management-agent agent-image list -c <COMPARTMENT>)
#   --rsp <input.rsp>       Response file containing the install-key content plus a
#                           CredentialWalletPassword (>=16 chars, upper+lower+digit+
#                           special — KB-09). Create on an OCI-CLI host with:
#     oci management-agent install-key create -c <C> --display-name k --query 'data.id' --raw-output
#     oci management-agent install-key get-install-key-content --management-agent-install-key-id <KEY> --file input.rsp
#   --install-dir <dir>     Override agent install dir (default: agent default).

set -euo pipefail

AGENT_ZIP="" RSP="" INSTALL_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent-zip)   AGENT_ZIP="$2"; shift 2;;
    --rsp)         RSP="$2"; shift 2;;
    --install-dir) INSTALL_DIR="$2"; shift 2;;
    -h|--help)     sed -n '2,30p' "$0"; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

if [ "$EUID" -ne 0 ]; then echo "Please run as root (sudo)." >&2; exit 1; fi
[ -z "$AGENT_ZIP" ] && { echo "Provide --agent-zip <path|url>." >&2; exit 1; }
[ -z "$RSP" ] && { echo "Provide --rsp <input.rsp>." >&2; exit 1; }
[ -f "$RSP" ] || { echo "Response file not found: $RSP" >&2; exit 1; }

# At cloud first-boot, apt/dpkg is often locked by cloud-init / unattended-upgrades.
# Wait for the lock to clear and retry, so installs don't fail under `set -e` (KB-27).
wait_for_apt() {
  command -v apt-get >/dev/null 2>&1 || return 0
  for _ in $(seq 1 30); do
    if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 && \
       ! fuser /var/lib/apt/lists/lock >/dev/null 2>&1; then return 0; fi
    echo "  waiting for apt/dpkg lock to clear..."; sleep 10
  done
}
apt_install() { for i in 1 2 3; do apt-get install -y -qq "$@" && return 0; echo "  apt retry $i..."; sleep 15; done; return 1; }

command -v unzip >/dev/null 2>&1 || { echo "Installing unzip..."; { wait_for_apt; apt-get update -qq && apt_install unzip; } || yum install -y unzip || true; }

# The OCI Management Agent for Linux requires JDK 8 (>= 8u281) with JAVA_HOME set,
# and does NOT bundle a JRE (KB-24). Install OpenJDK 8 if a suitable Java is absent.
resolve_java8_home() {
  # Resolve a JDK-8 home from the current `java` if it is 1.8.
  if command -v java >/dev/null 2>&1 && java -version 2>&1 | grep -q '"1\.8'; then
    local jbin; jbin="$(readlink -f "$(command -v java)")"
    jbin="${jbin%/jre/bin/java}"; jbin="${jbin%/bin/java}"
    [ -x "$jbin/bin/java" ] && { echo "$jbin"; return; }
  fi
  # Otherwise look for a java-8 / 1.8 JVM directory.
  find /usr/lib/jvm /usr/java -maxdepth 1 -type d \( -name '*1.8*' -o -name 'java-8*' \) 2>/dev/null | head -1
}
ensure_java8() {
  local jhome; jhome="$(resolve_java8_home)"
  if [ -z "$jhome" ] || [ ! -x "$jhome/bin/java" ]; then
    echo "Installing OpenJDK 8..."
    if command -v apt-get >/dev/null 2>&1; then wait_for_apt; apt-get update -qq || true; apt_install openjdk-8-jdk-headless
    elif command -v dnf >/dev/null 2>&1; then dnf install -y java-1.8.0-openjdk-devel
    elif command -v yum >/dev/null 2>&1; then yum install -y java-1.8.0-openjdk-devel
    else echo "No supported package manager to install JDK 8; install it manually." >&2; exit 1
    fi
    jhome="$(resolve_java8_home)"
  fi
  [ -n "$jhome" ] && [ -x "$jhome/bin/java" ] || { echo "Could not resolve JDK 8 home; set JAVA_HOME and re-run." >&2; exit 1; }
  export JAVA_HOME="$jhome"
  export PATH="$JAVA_HOME/bin:$PATH"
  echo "JAVA_HOME=$JAVA_HOME"
}
ensure_java8

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
LOCAL_ZIP="$WORK/oracle.mgmt_agent.zip"

if [[ "$AGENT_ZIP" =~ ^https?:// ]]; then
  echo "Downloading agent ZIP..."
  curl -fL "$AGENT_ZIP" -o "$LOCAL_ZIP"
else
  cp "$AGENT_ZIP" "$LOCAL_ZIP"
fi

echo "Extracting agent ZIP..."
unzip -o -q "$LOCAL_ZIP" -d "$WORK/agent"
INSTALLER="$(find "$WORK/agent" -maxdepth 2 -name 'installer.sh' | head -1)"
[ -z "$INSTALLER" ] && { echo "installer.sh not found in agent ZIP." >&2; exit 1; }
chmod +x "$INSTALLER" 2>/dev/null || true

# Pass the response file POSITIONALLY (KB-07). Optionally honor a custom install dir.
RSP_ABS="$(cd "$(dirname "$RSP")" && pwd)/$(basename "$RSP")"
echo "Running agent installer: $INSTALLER $RSP_ABS"
if [ -n "$INSTALL_DIR" ]; then
  ( cd "$(dirname "$INSTALLER")" && AGENT_INSTALL_BASEDIR="$INSTALL_DIR" bash "$INSTALLER" "$RSP_ABS" )
else
  ( cd "$(dirname "$INSTALLER")" && bash "$INSTALLER" "$RSP_ABS" )
fi

echo "Verifying agent service..."
sleep 5
if systemctl list-unit-files 2>/dev/null | grep -q mgmt_agent; then
  systemctl is-active mgmt_agent >/dev/null 2>&1 && echo "mgmt_agent service: active" || { echo "Starting mgmt_agent..."; systemctl start mgmt_agent || true; }
  systemctl status mgmt_agent --no-pager 2>/dev/null | head -5 || true
else
  echo "NOTE: mgmt_agent service unit not found by name; check /opt/oracle/mgmt_agent for status (some versions name the service differently)."
fi

echo
echo "Agent install complete. It registers with OCI in ~1-2 min (status -> ACTIVE)."
echo "Next: add the Prometheus /federate data source so metrics reach OCI Monitoring, e.g.:"
echo "  ./manage-oci-datasource.sh create --agent-id <AGENT_OCID> --compartment-id <C> \\"
echo "      --name proxy_prometheus --namespace prometheus_proxy --profile <P>"
