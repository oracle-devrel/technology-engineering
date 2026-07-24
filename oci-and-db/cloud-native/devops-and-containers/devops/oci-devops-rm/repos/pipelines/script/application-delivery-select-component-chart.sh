#!/bin/bash
set -euo pipefail

write_component_env() {
  {
    printf "BUILD_IMAGE=%s\n" "$BUILD_IMAGE"
    printf "PACKAGE_CHART=%s\n" "$PACKAGE_CHART"
    printf "CHECK_CHART=%s\n" "$CHECK_CHART"
    printf "source_dir=%q\n" "$source_dir"
    printf "chart_source_dir=%q\n" "$chart_source_dir"
    printf "chart_path=%q\n" "$COMPONENT_CHART_PATH"
    printf "chart_name=%q\n" "$COMPONENT_NAME"
    printf "chart_repo_prefix=%q\n" "$chart_repo_prefix"
    printf "application_env_file=%q\n" "$application_env_file"
    printf "application_validated_env_file=%q\n" "$application_validated_env_file"
    printf "chart_values_file=%q\n" ""
    printf "chart_version=%q\n" ""
  } > "$OUTPUT_ENV_FILE"
}

unset -v DELIVERY_ENV_FILE
unset -v COMPONENT_NAME
unset -v COMPONENT_CHART_PATH
unset -v OUTPUT_ENV_FILE

while getopts e:n:p:o: flag; do
  case "${flag}" in
    e) DELIVERY_ENV_FILE=${OPTARG} ;;
    n) COMPONENT_NAME=${OPTARG} ;;
    p) COMPONENT_CHART_PATH=${OPTARG} ;;
    o) OUTPUT_ENV_FILE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${DELIVERY_ENV_FILE:-}" ] || [ -z "${COMPONENT_NAME:-}" ] || [ -z "${COMPONENT_CHART_PATH:-}" ] || [ -z "${OUTPUT_ENV_FILE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

source "$DELIVERY_ENV_FILE"

write_component_env

printf "Selected component chart: %s\n" "$COMPONENT_NAME"
printf "Component chart path: %s\n" "$COMPONENT_CHART_PATH"
