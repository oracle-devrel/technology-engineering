#!/bin/bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

validate_ocid() {
  local value="$1"
  [[ "$value" =~ ^ocid1\.[a-z0-9_-]+\.[a-z0-9_-]*\.[a-z0-9-]*\.[a-z0-9]+$ ]]
}

validate_repo_path() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$ ]]
}

validate_chart_path() {
  local value="$1"
  [[ "$value" = "." || "$value" =~ ^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$ ]]
}

validate_values_path() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9]+([._-][A-Za-z0-9]+)*(/[A-Za-z0-9]+([._-][A-Za-z0-9]+)*)*\.ya?ml$ ]]
}

validate_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
}

validate_version() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._:+-]+$ ]]
}

validate_region_key() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9]+$ ]]
}

validate_namespace() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
}

unset -v COMPARTMENT_ID
unset -v OCIR_REGION_KEY
unset -v CHART_NAME
unset -v CHART_VERSION
unset -v CHART_PATH
unset -v OCIR_REPOSITORY_PATH
unset -v TENANCY_NAMESPACE
unset -v VALUES_FILE

while getopts c:k:n:v:d:p:t:f: flag; do
  case "${flag}" in
    c) COMPARTMENT_ID=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    n) CHART_NAME=${OPTARG} ;;
    v) CHART_VERSION=${OPTARG} ;;
    d) CHART_PATH=${OPTARG} ;;
    p) OCIR_REPOSITORY_PATH=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    f) VALUES_FILE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${COMPARTMENT_ID:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${CHART_NAME:-}" ] || [ -z "${CHART_VERSION:-}" ] || [ -z "${CHART_PATH:-}" ] || [ -z "${OCIR_REPOSITORY_PATH:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

require_cmd oci
require_cmd helm
require_cmd python3

if ! validate_ocid "$COMPARTMENT_ID"; then
  echo "Invalid compartment OCID" >&2
  exit 1
fi

if ! validate_region_key "$OCIR_REGION_KEY"; then
  echo "Invalid OCIR region key: ${OCIR_REGION_KEY}" >&2
  exit 1
fi

if ! validate_name "$CHART_NAME"; then
  echo "Invalid chart name: ${CHART_NAME}" >&2
  exit 1
fi

if ! validate_version "$CHART_VERSION"; then
  echo "Invalid chart version: ${CHART_VERSION}" >&2
  exit 1
fi

if ! validate_chart_path "$CHART_PATH"; then
  echo "Invalid chart path: ${CHART_PATH}. Use a safe relative chart path." >&2
  exit 1
fi

if ! validate_repo_path "$OCIR_REPOSITORY_PATH"; then
  echo "Invalid OCIR repository path: ${OCIR_REPOSITORY_PATH}" >&2
  exit 1
fi

if [ -n "${TENANCY_NAMESPACE:-}" ] && ! validate_namespace "$TENANCY_NAMESPACE"; then
  echo "Invalid tenancy namespace: ${TENANCY_NAMESPACE}" >&2
  exit 1
fi

if [ ! -f "${CHART_PATH}/Chart.yaml" ]; then
  echo "Chart.yaml not found at ${CHART_PATH}" >&2
  exit 1
fi

if [ -n "${VALUES_FILE:-}" ]; then
  if ! validate_values_path "$VALUES_FILE"; then
    echo "Invalid values file path: ${VALUES_FILE}. Use a safe relative YAML path." >&2
    exit 1
  fi

  if [ ! -f "$VALUES_FILE" ]; then
    echo "Values file not found at ${VALUES_FILE}" >&2
    exit 1
  fi

  cp "$VALUES_FILE" "${CHART_PATH}/values.yaml"
fi

CHART_ARCHIVE="${CHART_NAME}-${CHART_VERSION}.tgz"
cleanup() {
  rm -f "$CHART_ARCHIVE"
}
trap cleanup EXIT

repo_namespace="${TENANCY_NAMESPACE:-}"
if [ -z "$repo_namespace" ]; then
  repo_namespace=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query "data.namespace" --raw-output)
fi

if ! repo_id=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_ID" --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --limit 1 --query "data.items[0].id" --raw-output 2>/dev/null); then
  repo_id=""
fi

if [ "$repo_id" = "null" ]; then
  repo_id=""
fi

if [ -z "$repo_id" ]; then
  oci artifacts container repository create --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --compartment-id "$COMPARTMENT_ID" >/dev/null
fi

repo_path="${OCIR_REGION_KEY}.ocir.io/${repo_namespace}/${OCIR_REPOSITORY_PATH}"

CHART_PATH="$CHART_PATH" CHART_VERSION="$CHART_VERSION" python3 - <<'PY'
import os
from pathlib import Path

p = Path(os.environ["CHART_PATH"]) / "Chart.yaml"
text = p.read_text()
lines = []
seen = False
for line in text.splitlines():
    if line.startswith("version:"):
        lines.append(f"version: {os.environ['CHART_VERSION']}")
        seen = True
    else:
        lines.append(line)
if not seen:
    lines.append(f"version: {os.environ['CHART_VERSION']}")
p.write_text("\n".join(lines) + "\n")
PY

helm lint "${CHART_PATH}"
helm package "${CHART_PATH}"

TOKEN="$(oci raw-request --http-method GET --target-uri "https://${OCIR_REGION_KEY}.ocir.io/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

echo "$TOKEN" | helm registry login "${OCIR_REGION_KEY}.ocir.io" -u BEARER_TOKEN --password-stdin
helm push "$CHART_ARCHIVE" "oci://${repo_path}"
