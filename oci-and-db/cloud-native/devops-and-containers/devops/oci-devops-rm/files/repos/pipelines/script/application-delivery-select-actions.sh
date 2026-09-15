#!/bin/bash
set -euo pipefail

write_delivery_env() {
  {
    printf "BUILD_IMAGE=%s\n" "$BUILD_IMAGE"
    printf "PACKAGE_CHART=%s\n" "$PACKAGE_CHART"
    printf "CHECK_CHART=%s\n" "$CHECK_CHART"
    printf "source_dir=%q\n" "$SOURCE_DIR"
    printf "chart_source_dir=%q\n" "$CHART_SOURCE_DIR"
    printf "chart_path=%q\n" "$CHART_PATH"
    printf "chart_name=%q\n" "$CHART_NAME"
    printf "chart_repo_prefix=%q\n" "$CHART_REPO_PREFIX"
    printf "application_env_file=%q\n" "$APPLICATION_ENV_FILE"
    printf "application_validated_env_file=%q\n" "$APPLICATION_VALIDATED_ENV_FILE"
    printf "chart_values_file=%q\n" "$CHART_VALUES_FILE"
    printf "chart_version=%q\n" ""
  } > "$OUTPUT_ENV_FILE"
}

normalize_repo_url() {
  # OCI DevOps exposes a clean trigger URL, but Git remotes include SERVICE credentials.
  printf "%s" "$1" | sed -E 's#^(https://)[^/@]+(:[^/@]*)?@#\1#; s#\.git$##'
}

find_application_sources() {
  local candidate
  for candidate in "${OCI_WORKSPACE_DIR}"/*; do
    [ -d "$candidate" ] || continue
    [ -f "${candidate}/.oci-devops/application.env" ] || continue
    basename "$candidate"
  done
}

single_application_source() {
  local sources=("$@")
  if [ "${#sources[@]}" -ne 1 ]; then
    echo "Unable to select one application source. Found: ${sources[*]:-none}" >&2
    exit 1
  fi
  printf "%s\n" "${sources[0]}"
}

unset -v SOURCE_DIR
unset -v CHART_SOURCE_DIR
unset -v CHART_PATH
unset -v CHART_REPO_PREFIX
unset -v OUTPUT_ENV_FILE

while getopts s:a:p:r:o: flag; do
  case "${flag}" in
    s) SOURCE_DIR=${OPTARG} ;;
    a) CHART_SOURCE_DIR=${OPTARG} ;;
    p) CHART_PATH=${OPTARG} ;;
    r) CHART_REPO_PREFIX=${OPTARG} ;;
    o) OUTPUT_ENV_FILE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${CHART_SOURCE_DIR:-}" ] || [ -z "${CHART_PATH:-}" ] || [ -z "${CHART_REPO_PREFIX:-}" ] || [ -z "${OUTPUT_ENV_FILE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

: "${OCI_WORKSPACE_DIR:?OCI_WORKSPACE_DIR is required}"

application_sources=()
while IFS= read -r source_name; do
  application_sources+=("$source_name")
done < <(find_application_sources)
CHART_NAME="$(basename "$CHART_PATH")"
APPLICATION_ENV_FILE=".oci-devops/application.env"
APPLICATION_VALIDATED_ENV_FILE=".oci-devops/application.validated.env"
CHART_VALUES_FILE=""

trigger_source_url="$(normalize_repo_url "${OCI_TRIGGER_SOURCE_URL:-}")"
chart_remote_url="$(normalize_repo_url "$(git -C "${OCI_WORKSPACE_DIR}/${CHART_SOURCE_DIR}" config --get remote.origin.url || true)")"

BUILD_IMAGE=false
PACKAGE_CHART=false
CHECK_CHART=false

if [ -z "${OCI_TRIGGER_SOURCE_URL:-}" ]; then
  SOURCE_DIR="${SOURCE_DIR:-$(single_application_source "${application_sources[@]}")}"
  BUILD_IMAGE=true
  PACKAGE_CHART=true
elif [ "$trigger_source_url" = "$chart_remote_url" ]; then
  SOURCE_DIR="${SOURCE_DIR:-$(single_application_source "${application_sources[@]}")}"
  PACKAGE_CHART=true
else
  for source_candidate in "${application_sources[@]}"; do
    source_remote_url="$(normalize_repo_url "$(git -C "${OCI_WORKSPACE_DIR}/${source_candidate}" config --get remote.origin.url || true)")"
    if [ "$trigger_source_url" = "$source_remote_url" ]; then
      SOURCE_DIR="$source_candidate"
      BUILD_IMAGE=true
      CHECK_CHART=true
      break
    fi
  done

  if [ -z "${SOURCE_DIR:-}" ]; then
    echo "Unable to classify trigger source: ${OCI_TRIGGER_SOURCE_URL}" >&2
    echo "Application sources: ${application_sources[*]:-none}" >&2
    echo "Application chart URL: ${chart_remote_url}" >&2
    exit 1
  fi
fi

write_delivery_env

printf "Trigger source: %s\n" "${OCI_TRIGGER_SOURCE_URL:-manual}"
printf "Build image: %s\n" "$BUILD_IMAGE"
printf "Package chart: %s\n" "$PACKAGE_CHART"
printf "Check chart exists: %s\n" "$CHECK_CHART"
