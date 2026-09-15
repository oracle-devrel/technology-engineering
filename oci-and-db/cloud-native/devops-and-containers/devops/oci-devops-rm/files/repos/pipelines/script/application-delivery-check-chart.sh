#!/bin/bash
set -euo pipefail

write_delivery_env() {
  {
    printf "BUILD_IMAGE=%s\n" "$BUILD_IMAGE"
    printf "PACKAGE_CHART=%s\n" "$PACKAGE_CHART"
    printf "CHECK_CHART=%s\n" "$CHECK_CHART"
    printf "source_dir=%q\n" "$source_dir"
    printf "chart_source_dir=%q\n" "$chart_source_dir"
    printf "chart_path=%q\n" "$chart_path"
    printf "chart_name=%q\n" "$chart_name"
    printf "chart_repo_prefix=%q\n" "$chart_repo_prefix"
    printf "application_env_file=%q\n" "$application_env_file"
    printf "application_validated_env_file=%q\n" "$application_validated_env_file"
    printf "chart_values_file=%q\n" "$chart_values_file"
    printf "chart_version=%q\n" "$chart_version"
  } > "$DELIVERY_ENV_FILE"
}

unset -v DELIVERY_ENV_FILE
unset -v OCIR_REGION_KEY
unset -v TENANCY_NAMESPACE

while getopts e:k:t: flag; do
  case "${flag}" in
    e) DELIVERY_ENV_FILE=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${DELIVERY_ENV_FILE:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${TENANCY_NAMESPACE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

source "$DELIVERY_ENV_FILE"

if [ "$CHECK_CHART" != "true" ]; then
  echo "Skipping chart existence check."
  exit 0
fi

: "${OCI_WORKSPACE_DIR:?OCI_WORKSPACE_DIR is required}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${chart_version:-}" ]; then
  chart_version="$(bash "${SCRIPT_DIR}/read-chart-version.sh" -p "${OCI_WORKSPACE_DIR}/${chart_source_dir}/${chart_path}")"
  write_delivery_env
fi

remote_registry="${OCIR_REGION_KEY}.ocir.io"
chart_url="oci://${remote_registry}/${TENANCY_NAMESPACE}/${chart_repo_prefix%/}/${chart_name}"

# Helm authenticates to OCIR with the same bearer-token pattern used by Docker.
token="$(oci raw-request --http-method GET --target-uri "https://${remote_registry}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$token" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

echo "$token" | helm registry login "$remote_registry" -u BEARER_TOKEN --password-stdin
if helm show chart "$chart_url" --version "$chart_version" >/dev/null 2>&1; then
  echo "Chart already exists: ${chart_url}:${chart_version}"
else
  # First source builds need to publish the matching chart before releases can refer to it.
  echo "Chart is missing; this run will package and upload it: ${chart_url}:${chart_version}"
  PACKAGE_CHART=true
  write_delivery_env
fi
