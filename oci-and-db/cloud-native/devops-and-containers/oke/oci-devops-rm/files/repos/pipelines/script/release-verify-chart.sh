#!/bin/bash
set -euo pipefail

unset -v RELEASE_ENV_FILE
unset -v OCIR_REGION_KEY
unset -v TENANCY_NAMESPACE

while getopts e:k:t: flag; do
  case "${flag}" in
    e) RELEASE_ENV_FILE=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${RELEASE_ENV_FILE:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${TENANCY_NAMESPACE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

: "${OCI_WORKSPACE_DIR:?OCI_WORKSPACE_DIR is required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$RELEASE_ENV_FILE"

cd "${OCI_WORKSPACE_DIR}/${chart_source_dir}"
chart_version="$(bash "${SCRIPT_DIR}/read-chart-version.sh" -p "$chart_path")"

remote_registry="${OCIR_REGION_KEY}.ocir.io"
chart_url="oci://${remote_registry}/${TENANCY_NAMESPACE}/${chart_repo_prefix%/}/${chart_name}"

# Helm uses an OCIR bearer token here because release validation is registry-only.
token="$(oci raw-request --http-method GET --target-uri "https://${remote_registry}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$token" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

echo "$token" | helm registry login "$remote_registry" -u BEARER_TOKEN --password-stdin
if ! helm show chart "$chart_url" --version "$chart_version" >/dev/null 2>&1; then
  echo "Application chart is missing: ${chart_url}:${chart_version}" >&2
  exit 1
fi

{
  grep -v '^chart_version=' "$RELEASE_ENV_FILE" || true
  printf "chart_version=%q\n" "$chart_version"
} > "${RELEASE_ENV_FILE}.tmp"
mv "${RELEASE_ENV_FILE}.tmp" "$RELEASE_ENV_FILE"

printf "Verified application chart: %s:%s\n" "$chart_url" "$chart_version"
