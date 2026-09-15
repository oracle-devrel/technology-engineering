#!/bin/bash
set -euo pipefail

validate_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
}

unset -v application_env_file
unset -v output_env_file

while getopts f:o: flag; do
  case "${flag}" in
    f) application_env_file=${OPTARG} ;;
    o) output_env_file=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${application_env_file:-}" ]; then
  echo "Missing application metadata file parameter" >&2
  exit 1
fi

if [ ! -f "$application_env_file" ]; then
  echo "Application metadata file not found at ${application_env_file}" >&2
  exit 1
fi

component_name=""

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in
    ""|\#*) continue ;;
  esac

  if [[ ! "$line" =~ ^[a-z_]+=[A-Za-z0-9._:/+-]+$ ]]; then
    echo "Invalid line in ${application_env_file}: ${line}" >&2
    exit 1
  fi

  key="${line%%=*}"
  value="${line#*=}"

  case "$key" in
    component_name) component_name="$value" ;;
    *)
      echo "Unsupported key in ${application_env_file}: ${key}" >&2
      exit 1
      ;;
  esac
done < "$application_env_file"

if ! validate_name "$component_name"; then
  echo "Invalid component_name: ${component_name}" >&2
  exit 1
fi

if [ -n "${output_env_file:-}" ]; then
  {
    printf "component_name=%s\n" "$component_name"
  } > "$output_env_file"
fi

printf "Loaded component metadata for %s\n" "$component_name"
