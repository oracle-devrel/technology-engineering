#!/usr/bin/env bash
set -euo pipefail

# Installs the standalone Oracle Cloud Infrastructure Management Agent on Linux.
# Oracle install flow:
# https://docs.oracle.com/en-us/iaas/management-agents/doc/install-management-agent-chapter.html

INSTALL_KEY="${OCI_MGMT_AGENT_INSTALL_KEY:-}"
INSTALL_KEY_FILE="${OCI_MGMT_AGENT_INSTALL_KEY_FILE:-}"
WALLET_PASSWORD="${OCI_MGMT_AGENT_WALLET_PASSWORD:-}"
WALLET_PASSWORD_FILE="${OCI_MGMT_AGENT_WALLET_PASSWORD_FILE:-}"
RESPONSE_FILE_SOURCE="${OCI_MGMT_AGENT_RESPONSE_FILE:-}"
PACKAGE_PATH="${OCI_MGMT_AGENT_PACKAGE:-}"
PACKAGE_URL="${OCI_MGMT_AGENT_PACKAGE_URL:-}"
OBJECT_NAMESPACE="${OCI_MGMT_AGENT_OBJECT_NAMESPACE:-}"
OBJECT_BUCKET="${OCI_MGMT_AGENT_OBJECT_BUCKET:-}"
OBJECT_NAME="${OCI_MGMT_AGENT_OBJECT_NAME:-}"
AGENT_DISPLAY_NAME="${OCI_MGMT_AGENT_DISPLAY_NAME:-}"
WORK_DIR="${OCI_MGMT_AGENT_WORK_DIR:-/tmp/oci-management-agent-install}"
DOWNLOAD_DIR="${OCI_MGMT_AGENT_DOWNLOAD_DIR:-}"
GATEWAY_HOST="${OCI_MGMT_AGENT_GATEWAY_HOST:-}"
GATEWAY_PORT="${OCI_MGMT_AGENT_GATEWAY_PORT:-}"
ADDITIONAL_GROUPS="${OCI_MGMT_AGENT_ADDITIONAL_GROUPS:-}"
EXTERNAL_VOLUME_TARGET="${OCI_MGMT_AGENT_EXTERNAL_VOLUME_TARGET:-}"
SERVICE_IDENTIFIER="${OCI_MGMT_AGENT_SERVICE_IDENTIFIER:-}"
AUTO_INSTALL_JAVA="${OCI_MGMT_AGENT_AUTO_INSTALL_JAVA:-true}"
JAVA_HOME_OVERRIDE="${OCI_MGMT_AGENT_JAVA_HOME:-}"
JAVA_TARBALL="${OCI_MGMT_AGENT_JAVA_TARBALL:-}"
JAVA_URL="${OCI_MGMT_AGENT_JAVA_URL:-}"
JAVA_INSTALL_DIR="${OCI_MGMT_AGENT_JAVA_INSTALL_DIR:-/opt/oci-management-agent-java}"
JAVA_INSTALL_MODE="${OCI_MGMT_AGENT_JAVA_INSTALL_MODE:-standalone}"
JAVA_PACKAGE="${OCI_MGMT_AGENT_JAVA_PACKAGE:-java-1.8.0-openjdk-headless}"
ENABLE_LOG_ANALYTICS_PLUGIN="${OCI_MGMT_AGENT_ENABLE_LOG_ANALYTICS_PLUGIN:-false}"
KEEP_RESPONSE_FILE="${OCI_MGMT_AGENT_KEEP_RESPONSE_FILE:-false}"
RESTART_SERVICE="${OCI_MGMT_AGENT_RESTART_SERVICE:-true}"
FORCE="${OCI_MGMT_AGENT_FORCE:-false}"
DRY_RUN=false

usage() {
  cat <<'USAGE'
Usage:
  sudo bash scripts/install_oci_management_agent.sh [options]

Install the standalone OCI Management Agent on a Linux VM using an Oracle
Management Agent RPM or ZIP package and an install key.

Package source options, choose one:
  --package PATH                 Local oracle.mgmt_agent RPM or ZIP file.
  --package-url URL              Download the package with curl.
  --object-namespace NAME        Object Storage namespace from the OCI download URL.
  --object-bucket NAME           Object Storage bucket from the OCI download URL.
  --object-name NAME             Object name, for example Linux-x86_64/latest/oracle.mgmt_agent.rpm.
  --download-dir DIR             Folder where downloaded agent software is saved.
                                  Env: OCI_MGMT_AGENT_DOWNLOAD_DIR. Default: work dir.

Secret options:
  --response-file PATH           Existing input.rsp downloaded or prepared from the install key.
  --install-key VALUE            Management Agent install key. Prefer --install-key-file.
  --install-key-file PATH        File containing the Management Agent install key.
  --wallet-password VALUE        OCI_MGMT_AGENT_WALLET_PASSWORD value. Prefer --wallet-password-file.
  --wallet-password-file PATH    File containing OCI_MGMT_AGENT_WALLET_PASSWORD or CredentialWalletPassword.

Agent options:
  --agent-display-name NAME      Optional display name to add to input.rsp.
  --enable-log-analytics-plugin  Add Service.plugin.logan.download=true.
  --gateway-host HOST            Optional Management Gateway host.
  --gateway-port PORT            Optional Management Gateway port.
  --additional-groups LIST       Comma-separated groups to add mgmt_agent to.
  --external-volume-target DIR   Create /opt/oracle/mgmt_agent symlink to DIR and set OPT_ORACLE_SYMLINK=true.
  --service-identifier VALUE     Optional second argument for multi-agent ZIP installs.

Control options:
  --java-home DIR                Use this Java 8 home for the agent install only.
  --java-tarball PATH            Extract a standalone Java 8 tarball for the agent install.
  --java-url URL                 Download a standalone Java 8 tarball for the agent install.
  --java-install-dir DIR         Standalone Java install dir. Default: /opt/oci-management-agent-java.
  --java-install-mode MODE       standalone or package. Default: standalone.
  --java-package NAME            Java 8 OS package for package mode. Default: java-1.8.0-openjdk-headless.
  --skip-java-install            Do not install Java if no supported runtime is found.
  --work-dir DIR                 Working directory. Default: /tmp/oci-management-agent-install.
  --keep-response-file           Keep generated input.rsp after install. Default removes it.
  --skip-service-restart         Do not restart mgmt_agent after install.
  --force                        Continue even if mgmt_agent already appears active.
  --dry-run                      Print planned steps without changing the host.
  --help                         Show this help.

Examples:
  sudo OCI_MGMT_AGENT_INSTALL_KEY_FILE=/secure/install-key.txt \
    OCI_MGMT_AGENT_WALLET_PASSWORD_FILE=/secure/wallet-password.txt \
    OCI_MGMT_AGENT_PACKAGE=/tmp/oracle.mgmt_agent.rpm \
    bash scripts/install_oci_management_agent.sh

  sudo bash scripts/install_oci_management_agent.sh \
    --object-namespace mynamespace \
    --object-bucket mybucket \
    --object-name Linux-x86_64/latest/oracle.mgmt_agent.rpm \
    --download-dir /tmp/oci-management-agent-downloads \
    --response-file /secure/input.rsp \
    --enable-log-analytics-plugin
USAGE
}

log() {
  printf '[oci-mgmt-agent] %s\n' "$*"
}

warn() {
  printf '[oci-mgmt-agent] WARN: %s\n' "$*" >&2
}

die() {
  printf '[oci-mgmt-agent] ERROR: %s\n' "$*" >&2
  exit 1
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    printf '+'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi

  "$@"
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

read_value_file() {
  local path="$1"
  local expected_key="$2"
  local line=""
  local key=""
  local value=""

  [[ -f "${path}" ]] || die "Secret file not found: ${path}"

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="$(trim "${line}")"
    [[ -z "${line}" || "${line}" == \#* ]] && continue

    if [[ -n "${expected_key}" && "${line}" == *"="* ]]; then
      key="$(trim "${line%%=*}")"
      if [[ "${key}" == "${expected_key}" ]]; then
        value="$(trim "${line#*=}")"
        printf '%s' "${value}"
        return 0
      fi

      case "${key}" in
        managementAgentInstallKey|CredentialWalletPassword|AgentDisplayName|GatewayServerHost|GatewayServerPort|Service.plugin.*)
          continue
          ;;
      esac
    fi

    printf '%s' "${line}"
    return 0
  done < "${path}"

  die "No ${expected_key:-secret} value found in ${path}."
}

prompt_secret_if_missing() {
  local var_name="$1"
  local prompt="$2"
  local current_value="$3"

  if [[ -n "${current_value}" || "${DRY_RUN}" == "true" ]]; then
    printf '%s' "${current_value}"
    return 0
  fi

  [[ -t 0 ]] || die "${var_name} is required. Use an environment variable, file option, or CLI option."
  read -r -s -p "${prompt}: " current_value
  printf '\n' >&2
  printf '%s' "${current_value}"
}

prompt_optional_secret_if_missing() {
  local var_name="$1"
  local prompt="$2"
  local current_value="$3"

  if [[ -n "${current_value}" || "${DRY_RUN}" == "true" ]]; then
    printf '%s' "${current_value}"
    return 0
  fi

  [[ -t 0 ]] || return 0
  read -r -s -p "${var_name} - ${prompt} (press Enter to omit): " current_value
  printf '\n' >&2
  printf '%s' "${current_value}"
}

prompt_text_with_default() {
  local var_name="$1"
  local prompt="$2"
  local current_value="$3"
  local default_value="$4"

  if [[ -n "${current_value}" ]]; then
    printf '%s' "${current_value}"
    return 0
  fi

  if [[ "${DRY_RUN}" == "true" || ! -t 0 ]]; then
    printf '%s' "${default_value}"
    return 0
  fi

  read -r -p "${var_name} - ${prompt} [${default_value}]: " current_value
  printf '%s' "${current_value:-${default_value}}"
}

wallet_password_valid() {
  local value="$1"
  [[ "${#value}" -ge 16 ]] || return 1
  [[ "${value}" =~ [a-z] ]] || return 1
  [[ "${value}" =~ [A-Z] ]] || return 1
  [[ "${value}" =~ [0-9] ]] || return 1
  [[ "${value}" =~ [\!\@\#\%\^\&\*] ]] || return 1
  [[ ! "${value}" =~ [^a-zA-Z0-9\!\@\#\%\^\&\*] ]] || return 1
}

wallet_password_rules() {
  printf 'at least 16 characters with lowercase, uppercase, numeric, and one special character from !@#%%^&*; do not use other special characters'
}

validate_wallet_password_if_present() {
  [[ -z "${WALLET_PASSWORD}" || "${DRY_RUN}" == "true" ]] && return 0

  while ! wallet_password_valid "${WALLET_PASSWORD}"; do
    warn "OCI_MGMT_AGENT_WALLET_PASSWORD must be $(wallet_password_rules)."
    [[ -t 0 ]] || die "Set a compliant OCI_MGMT_AGENT_WALLET_PASSWORD and rerun."
    read -r -s -p "OCI_MGMT_AGENT_WALLET_PASSWORD - agent credential wallet password (press Enter to omit): " WALLET_PASSWORD
    printf '\n' >&2
    [[ -z "${WALLET_PASSWORD}" ]] && return 0
  done
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --package)
        PACKAGE_PATH="${2:-}"
        shift 2
        ;;
      --package-url)
        PACKAGE_URL="${2:-}"
        shift 2
        ;;
      --object-namespace)
        OBJECT_NAMESPACE="${2:-}"
        shift 2
        ;;
      --object-bucket)
        OBJECT_BUCKET="${2:-}"
        shift 2
        ;;
      --object-name)
        OBJECT_NAME="${2:-}"
        shift 2
        ;;
      --download-dir)
        DOWNLOAD_DIR="${2:-}"
        shift 2
        ;;
      --install-key)
        INSTALL_KEY="${2:-}"
        shift 2
        ;;
      --response-file)
        RESPONSE_FILE_SOURCE="${2:-}"
        shift 2
        ;;
      --install-key-file)
        INSTALL_KEY_FILE="${2:-}"
        shift 2
        ;;
      --wallet-password)
        WALLET_PASSWORD="${2:-}"
        shift 2
        ;;
      --wallet-password-file)
        WALLET_PASSWORD_FILE="${2:-}"
        shift 2
        ;;
      --agent-display-name)
        AGENT_DISPLAY_NAME="${2:-}"
        shift 2
        ;;
      --enable-log-analytics-plugin)
        ENABLE_LOG_ANALYTICS_PLUGIN=true
        shift
        ;;
      --gateway-host)
        GATEWAY_HOST="${2:-}"
        shift 2
        ;;
      --gateway-port)
        GATEWAY_PORT="${2:-}"
        shift 2
        ;;
      --additional-groups)
        ADDITIONAL_GROUPS="${2:-}"
        shift 2
        ;;
      --external-volume-target)
        EXTERNAL_VOLUME_TARGET="${2:-}"
        shift 2
        ;;
      --service-identifier)
        SERVICE_IDENTIFIER="${2:-}"
        shift 2
        ;;
      --java-home)
        JAVA_HOME_OVERRIDE="${2:-}"
        shift 2
        ;;
      --java-tarball)
        JAVA_TARBALL="${2:-}"
        JAVA_INSTALL_MODE=standalone
        shift 2
        ;;
      --java-url)
        JAVA_URL="${2:-}"
        JAVA_INSTALL_MODE=standalone
        shift 2
        ;;
      --java-install-dir)
        JAVA_INSTALL_DIR="${2:-}"
        shift 2
        ;;
      --java-install-mode)
        JAVA_INSTALL_MODE="${2:-}"
        shift 2
        ;;
      --java-package)
        JAVA_PACKAGE="${2:-}"
        shift 2
        ;;
      --skip-java-install)
        AUTO_INSTALL_JAVA=false
        shift
        ;;
      --work-dir)
        WORK_DIR="${2:-}"
        shift 2
        ;;
      --keep-response-file)
        KEEP_RESPONSE_FILE=true
        shift
        ;;
      --skip-service-restart)
        RESTART_SERVICE=false
        shift
        ;;
      --force)
        FORCE=true
        shift
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        usage >&2
        die "Unknown option: $1"
        ;;
    esac
  done
}

load_secret_files() {
  if [[ -n "${RESPONSE_FILE_SOURCE}" ]]; then
    return 0
  fi

  if [[ -n "${INSTALL_KEY_FILE}" ]]; then
    INSTALL_KEY="$(read_value_file "${INSTALL_KEY_FILE}" "managementAgentInstallKey")"
  fi

  if [[ -n "${WALLET_PASSWORD_FILE}" ]]; then
    WALLET_PASSWORD="$(read_value_file "${WALLET_PASSWORD_FILE}" "CredentialWalletPassword")"
  fi

  INSTALL_KEY="$(prompt_secret_if_missing "OCI_MGMT_AGENT_INSTALL_KEY" "Management Agent install key" "${INSTALL_KEY}")"
  WALLET_PASSWORD="$(prompt_optional_secret_if_missing "OCI_MGMT_AGENT_WALLET_PASSWORD" "agent credential wallet password" "${WALLET_PASSWORD}")"
  validate_wallet_password_if_present
}

validate_root() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    return 0
  fi

  [[ "${EUID}" -eq 0 ]] || die "Run as root, for example with sudo."
}

validate_host() {
  [[ "$(uname -s)" == "Linux" ]] || die "This installer supports Linux only."

  local arch
  arch="$(uname -m)"
  case "${arch}" in
    x86_64|aarch64)
      ;;
    *)
      warn "Host architecture ${arch} is not one of the common OCI Management Agent Linux architectures."
      ;;
  esac

  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    log "Detected OS: ${PRETTY_NAME:-${ID:-unknown}}"
  fi
}

validate_inputs() {
  local source_count=0
  [[ -n "${PACKAGE_PATH}" ]] && source_count=$((source_count + 1))
  [[ -n "${PACKAGE_URL}" ]] && source_count=$((source_count + 1))
  if [[ -n "${OBJECT_NAMESPACE}" || -n "${OBJECT_BUCKET}" || -n "${OBJECT_NAME}" ]]; then
    source_count=$((source_count + 1))
    [[ -n "${OBJECT_NAMESPACE}" && -n "${OBJECT_BUCKET}" && -n "${OBJECT_NAME}" ]] \
      || die "Object Storage package source requires --object-namespace, --object-bucket, and --object-name."
  fi

  [[ "${source_count}" -eq 1 ]] || die "Choose exactly one package source: --package, --package-url, or Object Storage options."

  if [[ -n "${RESPONSE_FILE_SOURCE}" ]]; then
    [[ "${DRY_RUN}" == "true" || -f "${RESPONSE_FILE_SOURCE}" ]] || die "Response file not found: ${RESPONSE_FILE_SOURCE}"
    return 0
  fi

  if [[ "${DRY_RUN}" != "true" ]]; then
    [[ -n "${INSTALL_KEY}" ]] || die "Management Agent install key is required."
  fi
}

already_active() {
  have_command systemctl || return 1
  systemctl is-active --quiet mgmt_agent >/dev/null 2>&1
}

check_existing_agent() {
  if already_active && [[ "${FORCE}" != "true" ]]; then
    log "mgmt_agent is already active. Use --force to reinstall or reconfigure."
    verify_agent
    exit 0
  fi
}

prepare_work_dir() {
  run mkdir -p "${WORK_DIR}"
}

java_binary_supported() {
  local java_bin="$1"
  local java_output
  [[ -x "${java_bin}" ]] || return 1
  java_output="$("${java_bin}" -version 2>&1 || true)"
  [[ "${java_output}" =~ version[[:space:]]\"1\.8\.0_([0-9]+) ]] || return 1
  [[ "${BASH_REMATCH[1]}" -ge 281 ]]
}

java_home_supported() {
  local java_home="$1"
  [[ -n "${java_home}" ]] || return 1
  java_binary_supported "${java_home}/bin/java"
}

system_java_supported() {
  local java_bin
  java_bin="$(command -v java 2>/dev/null || true)"
  [[ -n "${java_bin}" ]] || return 1
  java_binary_supported "${java_bin}"
}

use_agent_java_home() {
  local java_home="$1"
  export JAVA_HOME="${java_home}"
  log "Using standalone JAVA_HOME=${JAVA_HOME} for the Management Agent install only."
}

download_java_tarball() {
  have_command curl || die "curl is required for --java-url."

  local file_name
  file_name="${JAVA_URL%%\?*}"
  file_name="${file_name##*/}"
  [[ -n "${file_name}" ]] || file_name="java8.tar.gz"
  JAVA_TARBALL="${WORK_DIR}/${file_name}"

  log "Downloading standalone Java runtime"
  run curl --fail --location --retry 3 --output "${JAVA_TARBALL}" "${JAVA_URL}"
}

install_standalone_java() {
  if [[ -z "${JAVA_TARBALL}" && -n "${JAVA_URL}" ]]; then
    download_java_tarball
  fi

  [[ -n "${JAVA_TARBALL}" ]] \
    || die "No supported Java 8 runtime found. Provide --java-home, --java-tarball, --java-url, or explicitly use --java-install-mode package."
  [[ "${DRY_RUN}" == "true" || -f "${JAVA_TARBALL}" ]] || die "Java tarball not found: ${JAVA_TARBALL}"
  have_command tar || die "tar is required to extract standalone Java."

  log "Installing standalone Java runtime into ${JAVA_INSTALL_DIR}"
  run mkdir -p "${JAVA_INSTALL_DIR}"
  run tar -xf "${JAVA_TARBALL}" -C "${JAVA_INSTALL_DIR}" --strip-components=1
  use_agent_java_home "${JAVA_INSTALL_DIR}"

  if [[ "${DRY_RUN}" != "true" ]]; then
    java_home_supported "${JAVA_HOME}" || die "Standalone Java at ${JAVA_HOME} is not Java 8u281 or newer."
  fi
}

install_java_package() {
  log "Installing Java prerequisite package ${JAVA_PACKAGE}"
  if have_command dnf; then
    run dnf install -y "${JAVA_PACKAGE}"
  elif have_command yum; then
    run yum install -y "${JAVA_PACKAGE}"
  elif have_command apt-get; then
    run apt-get update
    run apt-get install -y openjdk-8-jre-headless
  else
    die "No supported package manager found. Install Java 8u281 or newer and rerun."
  fi

  if [[ "${DRY_RUN}" != "true" ]]; then
    system_java_supported || die "Java 8u281 or newer is still not available after package installation."
  fi
}

prepare_java_prerequisite() {
  if [[ -n "${JAVA_HOME_OVERRIDE}" ]]; then
    java_home_supported "${JAVA_HOME_OVERRIDE}" \
      || die "--java-home must point to Java 8u281 or newer: ${JAVA_HOME_OVERRIDE}"
    use_agent_java_home "${JAVA_HOME_OVERRIDE}"
    return 0
  fi

  if [[ -n "${JAVA_HOME:-}" ]]; then
    if java_home_supported "${JAVA_HOME}"; then
      log "Using existing JAVA_HOME=${JAVA_HOME} for the Management Agent install."
      return 0
    fi
  fi

  if system_java_supported; then
    if [[ -n "${JAVA_HOME:-}" ]]; then
      warn "Ignoring unsupported JAVA_HOME=${JAVA_HOME} for this install only; supported Java is available on PATH."
      unset JAVA_HOME
    fi
    log "Detected supported Java 8 runtime."
    return 0
  fi

  [[ "${AUTO_INSTALL_JAVA}" == "true" ]] \
    || die "Supported Java 8 runtime not found. Install JDK/JRE 8u281 or newer, or rerun without --skip-java-install."

  JAVA_INSTALL_MODE="$(printf '%s' "${JAVA_INSTALL_MODE}" | tr '[:upper:]' '[:lower:]')"
  case "${JAVA_INSTALL_MODE}" in
    standalone)
      install_standalone_java
      ;;
    package)
      warn "Package mode may register Java with the OS package manager. Use standalone mode to avoid touching customer Java alternatives."
      install_java_package
      ;;
    *)
      die "--java-install-mode must be standalone or package."
      ;;
  esac
}

prepare_download_dir() {
  [[ -z "${PACKAGE_URL}" && -z "${OBJECT_NAMESPACE}" && -z "${OBJECT_BUCKET}" && -z "${OBJECT_NAME}" ]] && return 0

  DOWNLOAD_DIR="$(prompt_text_with_default \
    "OCI_MGMT_AGENT_DOWNLOAD_DIR" \
    "folder where to download the Management Agent software" \
    "${DOWNLOAD_DIR}" \
    "${WORK_DIR}")"
  run mkdir -p "${DOWNLOAD_DIR}"
}

download_package() {
  if [[ -n "${PACKAGE_PATH}" ]]; then
    [[ "${DRY_RUN}" == "true" || -f "${PACKAGE_PATH}" ]] || die "Package not found: ${PACKAGE_PATH}"
    return 0
  fi

  prepare_download_dir

  local file_name
  if [[ -n "${PACKAGE_URL}" ]]; then
    have_command curl || die "curl is required for --package-url."
    file_name="${PACKAGE_URL%%\?*}"
    file_name="${file_name##*/}"
    [[ -n "${file_name}" ]] || file_name="oracle.mgmt_agent.package"
    PACKAGE_PATH="${DOWNLOAD_DIR}/${file_name}"
    log "Downloading Management Agent package from URL"
    run curl --fail --location --retry 3 --output "${PACKAGE_PATH}" "${PACKAGE_URL}"
    return 0
  fi

  have_command oci || die "OCI CLI is required for Object Storage package download."
  file_name="${OBJECT_NAME##*/}"
  [[ -n "${file_name}" ]] || file_name="oracle.mgmt_agent.package"
  PACKAGE_PATH="${DOWNLOAD_DIR}/${file_name}"
  log "Downloading Management Agent package from OCI Object Storage"
  run oci os object get \
    --namespace "${OBJECT_NAMESPACE}" \
    --bucket-name "${OBJECT_BUCKET}" \
    --name "${OBJECT_NAME}" \
    --file "${PACKAGE_PATH}"
}

validate_package_arch() {
  local arch
  local package_identity
  arch="$(uname -m)"
  package_identity="${PACKAGE_PATH} ${PACKAGE_URL} ${OBJECT_NAME}"

  if [[ "${package_identity}" == *Linux-x86_64* || "${package_identity}" == *x86_64* ]]; then
    [[ "${arch}" == "x86_64" ]] || die "Package name looks x86_64, but host architecture is ${arch}."
  fi

  if [[ "${package_identity}" == *Linux-Aarch64* || "${package_identity}" == *aarch64* || "${package_identity}" == *Aarch64* ]]; then
    [[ "${arch}" == "aarch64" ]] || die "Package name looks Aarch64, but host architecture is ${arch}."
  fi
}

write_response_file() {
  RESPONSE_FILE="${WORK_DIR}/input.rsp"
  local old_umask

  if [[ "${DRY_RUN}" == "true" ]]; then
    if [[ -n "${RESPONSE_FILE_SOURCE}" ]]; then
      log "Would copy response file ${RESPONSE_FILE_SOURCE} to ${RESPONSE_FILE}."
    else
      log "Would write ${RESPONSE_FILE} with redacted install key and wallet password."
    fi
    return 0
  fi

  old_umask="$(umask)"
  umask 077
  if [[ -n "${RESPONSE_FILE_SOURCE}" ]]; then
    cp "${RESPONSE_FILE_SOURCE}" "${RESPONSE_FILE}"
  else
    {
      printf 'managementAgentInstallKey = %s\n' "${INSTALL_KEY}"
      [[ -n "${WALLET_PASSWORD}" ]] && printf 'CredentialWalletPassword = %s\n' "${WALLET_PASSWORD}"
    } > "${RESPONSE_FILE}"
  fi

  {
    [[ -n "${AGENT_DISPLAY_NAME}" ]] && printf 'AgentDisplayName = %s\n' "${AGENT_DISPLAY_NAME}"
    [[ -n "${GATEWAY_HOST}" ]] && printf 'GatewayServerHost = %s\n' "${GATEWAY_HOST}"
    [[ -n "${GATEWAY_PORT}" ]] && printf 'GatewayServerPort = %s\n' "${GATEWAY_PORT}"
    [[ "${ENABLE_LOG_ANALYTICS_PLUGIN}" == "true" ]] && printf 'Service.plugin.logan.download=true\n'
  } >> "${RESPONSE_FILE}"

  chmod 600 "${RESPONSE_FILE}"
  umask "${old_umask}"
  log "Created response file at ${RESPONSE_FILE}"
}

cleanup_response_file() {
  if [[ "${KEEP_RESPONSE_FILE}" == "true" || "${DRY_RUN}" == "true" ]]; then
    return 0
  fi

  if [[ -n "${RESPONSE_FILE:-}" && -f "${RESPONSE_FILE}" ]]; then
    rm -f "${RESPONSE_FILE}"
    log "Removed response file containing install secrets."
  fi
}

configure_external_volume() {
  [[ -n "${EXTERNAL_VOLUME_TARGET}" ]] || return 0

  if [[ -e /opt/oracle/mgmt_agent && ! -L /opt/oracle/mgmt_agent ]]; then
    die "/opt/oracle/mgmt_agent already exists and is not a symlink."
  fi

  run mkdir -p "${EXTERNAL_VOLUME_TARGET}"
  run mkdir -p /opt/oracle
  run ln -sfn "${EXTERNAL_VOLUME_TARGET}" /opt/oracle/mgmt_agent
  export OPT_ORACLE_SYMLINK=true
  log "Using external volume target ${EXTERNAL_VOLUME_TARGET}"
}

install_rpm() {
  have_command rpm || die "rpm is required to install ${PACKAGE_PATH}."

  local setup_sh="/opt/oracle/mgmt_agent/agent_inst/bin/setup.sh"
  if [[ "${DRY_RUN}" != "true" && -x "${setup_sh}" ]]; then
    log "Management Agent software is already present; skipping RPM package install."
  else
    log "Installing Management Agent RPM"
    run rpm -ivh "${PACKAGE_PATH}"
  fi

  [[ "${DRY_RUN}" == "true" || -x "${setup_sh}" ]] || die "setup.sh not found after RPM install: ${setup_sh}"

  allow_agent_user_to_read_response_file
  log "Configuring Management Agent RPM install"
  run "${setup_sh}" "opts=${RESPONSE_FILE}"
}

allow_agent_user_to_read_response_file() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    log "Would grant mgmt_agent read access to ${RESPONSE_FILE}."
    return 0
  fi

  id mgmt_agent >/dev/null 2>&1 || {
    warn "mgmt_agent user does not exist yet; leaving response file owned by root."
    return 0
  }

  chgrp mgmt_agent "${WORK_DIR}" || true
  chmod 750 "${WORK_DIR}" || true
  chown mgmt_agent:mgmt_agent "${RESPONSE_FILE}"
  chmod 600 "${RESPONSE_FILE}"
}

install_zip() {
  have_command unzip || die "unzip is required to install ${PACKAGE_PATH}."

  local unzip_dir="${WORK_DIR}/unzipped"
  local installer=""
  run rm -rf "${unzip_dir}"
  run mkdir -p "${unzip_dir}"
  log "Extracting Management Agent ZIP"
  run unzip -q -o "${PACKAGE_PATH}" -d "${unzip_dir}"

  if [[ "${DRY_RUN}" != "true" ]]; then
    installer="$(find "${unzip_dir}" -maxdepth 3 -type f -name installer.sh -print -quit)"
    [[ -n "${installer}" ]] || die "installer.sh not found after extracting ${PACKAGE_PATH}."
    chmod +x "${installer}"
  else
    installer="${unzip_dir}/installer.sh"
  fi

  local installer_dir
  installer_dir="$(dirname "${installer}")"
  log "Running Management Agent ZIP installer"
  if [[ -n "${SERVICE_IDENTIFIER}" ]]; then
    run bash -c 'cd "$1" && ./installer.sh "$2" "$3"' bash "${installer_dir}" "${RESPONSE_FILE}" "${SERVICE_IDENTIFIER}"
  else
    run bash -c 'cd "$1" && ./installer.sh "$2"' bash "${installer_dir}" "${RESPONSE_FILE}"
  fi
}

install_package() {
  case "${PACKAGE_PATH}" in
    *.rpm)
      install_rpm
      ;;
    *.zip)
      configure_external_volume
      install_zip
      ;;
    *)
      die "Unsupported package type: ${PACKAGE_PATH}. Use an Oracle Management Agent .rpm or .zip file."
      ;;
  esac
}

add_agent_groups() {
  [[ -n "${ADDITIONAL_GROUPS}" ]] || return 0

  if [[ "${DRY_RUN}" != "true" ]]; then
    id mgmt_agent >/dev/null 2>&1 || die "mgmt_agent user does not exist after installation."
  fi

  log "Adding mgmt_agent to groups: ${ADDITIONAL_GROUPS}"
  run usermod -a -G "${ADDITIONAL_GROUPS}" mgmt_agent
}

restart_service() {
  [[ "${RESTART_SERVICE}" == "true" ]] || return 0
  have_command systemctl || {
    warn "systemctl not found; skipping service restart."
    return 0
  }

  log "Enabling and restarting mgmt_agent"
  run systemctl enable mgmt_agent
  run systemctl restart mgmt_agent
}

verify_agent() {
  if have_command systemctl; then
    if run systemctl --no-pager status mgmt_agent; then
      :
    else
      warn "systemctl status mgmt_agent reported a problem."
    fi
  fi

  local omcli="/opt/oracle/mgmt_agent/agent_inst/bin/omcli"
  if [[ "${DRY_RUN}" == "true" || -x "${omcli}" ]]; then
    if run "${omcli}" status agent; then
      :
    else
      warn "omcli status agent reported a problem."
    fi
  else
    warn "omcli not found at ${omcli}."
  fi
}

main() {
  parse_args "$@"
  validate_root
  validate_host
  load_secret_files
  validate_inputs
  check_existing_agent
  prepare_work_dir
  download_package
  validate_package_arch
  prepare_java_prerequisite
  write_response_file
  trap cleanup_response_file EXIT
  install_package
  add_agent_groups
  restart_service
  verify_agent
  log "Management Agent installation workflow complete."
}

main "$@"
