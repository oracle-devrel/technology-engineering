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
unset -v COMPARTMENT_ID
unset -v OCIR_REGION_KEY
unset -v IMAGE_REPOSITORY_PATH
unset -v TENANCY_NAMESPACE

while getopts e:c:k:p:t: flag; do
  case "${flag}" in
    e) DELIVERY_ENV_FILE=${OPTARG} ;;
    c) COMPARTMENT_ID=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    p) IMAGE_REPOSITORY_PATH=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${DELIVERY_ENV_FILE:-}" ] || [ -z "${COMPARTMENT_ID:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${IMAGE_REPOSITORY_PATH:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

: "${OCI_WORKSPACE_DIR:?OCI_WORKSPACE_DIR is required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DELIVERY_ENV_FILE"

if [ "$BUILD_IMAGE" != "true" ]; then
  echo "Skipping image build."
  exit 0
fi

cd "${OCI_WORKSPACE_DIR}/${source_dir}"
bash "${SCRIPT_DIR}/read-application-metadata.sh" \
  -f "$application_env_file" \
  -o "$application_validated_env_file"
source "$application_validated_env_file"

bash "${SCRIPT_DIR}/build-push-image.sh" \
  -c "$COMPARTMENT_ID" \
  -k "$OCIR_REGION_KEY" \
  -n "$component_name" \
  -p "$IMAGE_REPOSITORY_PATH" \
  -t "${TENANCY_NAMESPACE:-}"

write_delivery_env
