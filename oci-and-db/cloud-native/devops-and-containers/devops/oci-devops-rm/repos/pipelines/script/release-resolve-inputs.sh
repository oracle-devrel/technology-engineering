#!/bin/bash
set -euo pipefail

unset -v RELEASE_TAG
unset -v COMMIT_ID
unset -v SOURCE_DIR
unset -v CHART_SOURCE_DIR
unset -v CHART_PATH
unset -v CHART_REPO_PREFIX
unset -v OUTPUT_ENV_FILE

while getopts g:i:s:a:p:r:o: flag; do
  case "${flag}" in
    g) RELEASE_TAG=${OPTARG} ;;
    i) COMMIT_ID=${OPTARG} ;;
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

if [ -z "${RELEASE_TAG:-}" ] || [ -z "${CHART_SOURCE_DIR:-}" ] || [ -z "${CHART_PATH:-}" ] || [ -z "${CHART_REPO_PREFIX:-}" ] || [ -z "${OUTPUT_ENV_FILE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

: "${OCI_WORKSPACE_DIR:?OCI_WORKSPACE_DIR is required}"
: "${OCI_STAGE_ID:?OCI_STAGE_ID is required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLICATION_ENV_FILE=".oci-devops/application.env"
APPLICATION_VALIDATED_ENV_FILE=".oci-devops/application.validated.env"

find_application_sources() {
  local candidate
  for candidate in "${OCI_WORKSPACE_DIR}"/*; do
    [ -d "$candidate" ] || continue
    [ -f "${candidate}/.oci-devops/application.env" ] || continue
    basename "$candidate"
  done
}

application_sources=()
while IFS= read -r source_name; do
  application_sources+=("$source_name")
done < <(find_application_sources)

if [ -z "${SOURCE_DIR:-}" ]; then
  if [ -z "${COMMIT_ID:-}" ] || [ "$COMMIT_ID" = "CHANGE_ME" ]; then
    if [ "${#application_sources[@]}" -ne 1 ]; then
      echo "Unable to select one application source for release. Found: ${application_sources[*]:-none}" >&2
      exit 1
    fi
    SOURCE_DIR="${application_sources[0]}"
  else
    normalized_commit_id="$(printf "%s" "$COMMIT_ID" | tr '[:upper:]' '[:lower:]')"
    for source_candidate in "${application_sources[@]}"; do
      if git -C "${OCI_WORKSPACE_DIR}/${source_candidate}" cat-file -e "${normalized_commit_id}^{commit}" 2>/dev/null; then
        SOURCE_DIR="$source_candidate"
        break
      fi
    done
    if [ -z "${SOURCE_DIR:-}" ]; then
      echo "Unable to find application source containing commit: ${normalized_commit_id}" >&2
      exit 1
    fi
  fi
fi

cd "${OCI_WORKSPACE_DIR}/${SOURCE_DIR}"
bash "${SCRIPT_DIR}/read-application-metadata.sh" \
  -f "$APPLICATION_ENV_FILE" \
  -o "$APPLICATION_VALIDATED_ENV_FILE"
source "$APPLICATION_VALIDATED_ENV_FILE"

source_repository_id="$(oci devops build-pipeline-stage get --stage-id "$OCI_STAGE_ID" --query 'data."build-source-collection".items[?name==`'"$SOURCE_DIR"'`]."repository-id" | [0]' --raw-output)"
if [ -z "$source_repository_id" ] || [ "$source_repository_id" = "null" ]; then
  echo "Unable to derive source repository id for build source: ${SOURCE_DIR}" >&2
  exit 1
fi

if [ -z "${COMMIT_ID:-}" ] || [ "$COMMIT_ID" = "CHANGE_ME" ]; then
  resolved_commit_id="$(git rev-parse origin/main)"
else
  resolved_commit_id="$COMMIT_ID"
fi
resolved_commit_id="$(printf "%s" "$resolved_commit_id" | tr '[:upper:]' '[:lower:]')"

git merge-base --is-ancestor "$resolved_commit_id" origin/main

{
  printf "release_tag=%q\n" "$RELEASE_TAG"
  printf "resolved_commit_id=%q\n" "$resolved_commit_id"
  printf "source_repository_id=%q\n" "$source_repository_id"
  printf "source_dir=%q\n" "$SOURCE_DIR"
  printf "chart_source_dir=%q\n" "$CHART_SOURCE_DIR"
  printf "chart_path=%q\n" "$CHART_PATH"
  printf "chart_name=%q\n" "$(basename "$CHART_PATH")"
  printf "chart_repo_prefix=%q\n" "$CHART_REPO_PREFIX"
  printf "component_name=%q\n" "$component_name"
  printf "release_env_file=%q\n" "application-release.env"
  printf "chart_version=%q\n" ""
} > "$OUTPUT_ENV_FILE"

printf "Release tag: %s\n" "$RELEASE_TAG"
printf "Source commit: %s\n" "$resolved_commit_id"
printf "Component: %s\n" "$component_name"
