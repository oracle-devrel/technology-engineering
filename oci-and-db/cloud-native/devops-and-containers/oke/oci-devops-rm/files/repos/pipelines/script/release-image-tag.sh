#!/bin/bash
set -euo pipefail

SKOPEO_IMAGE="${SKOPEO_IMAGE:-quay.io/skopeo/stable:v1.15.2}"

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

validate_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
}

validate_release_tag() {
  local value="$1"
  [[ "$value" =~ ^[0-9]+[.][0-9]+[.][0-9]+-rc[.][0-9]+$ ]]
}

validate_commit_id() {
  local value="$1"
  [[ "$value" =~ ^[a-f0-9]{40}$ ]]
}

validate_region_key() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9]+$ ]]
}

validate_namespace() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
}

run_skopeo() {
  # The build image has Docker; skopeo runs as a pinned container to avoid local installs.
  docker run --rm "$SKOPEO_IMAGE" "$@"
}

image_exists() {
  local image_ref="$1"
  run_skopeo inspect --creds "BEARER_TOKEN:${TOKEN}" "docker://${image_ref}" >/dev/null 2>&1
}

release_tag_exists() {
  local object_id
  object_id="$(oci devops repository list-refs \
    --repository-id "$SOURCE_REPOSITORY_ID" \
    --ref-type TAG \
    --ref-name "$RELEASE_TAG" \
    --query 'data.items[0]."object-id"' \
    --raw-output)"
  [ -n "$object_id" ] && [ "$object_id" != "null" ]
}

inspect_digest() {
  local image_ref="$1"
  local inspect_file="$2"
  run_skopeo inspect --creds "BEARER_TOKEN:${TOKEN}" "docker://${image_ref}" > "$inspect_file"
  python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("Digest", ""))' "$inspect_file"
}

unset -v COMPARTMENT_ID
unset -v OCIR_REGION_KEY
unset -v COMPONENT_NAME
unset -v OCIR_REPOSITORY_PATH
unset -v TENANCY_NAMESPACE
unset -v RELEASE_TAG
unset -v COMMIT_ID
unset -v SOURCE_REPOSITORY_ID
unset -v OUTPUT_ENV_FILE

while getopts c:k:n:p:t:g:i:r:o: flag; do
  case "${flag}" in
    c) COMPARTMENT_ID=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    n) COMPONENT_NAME=${OPTARG} ;;
    p) OCIR_REPOSITORY_PATH=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    g) RELEASE_TAG=${OPTARG} ;;
    i) COMMIT_ID=${OPTARG} ;;
    r) SOURCE_REPOSITORY_ID=${OPTARG} ;;
    o) OUTPUT_ENV_FILE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${COMPARTMENT_ID:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${COMPONENT_NAME:-}" ] || [ -z "${OCIR_REPOSITORY_PATH:-}" ] || [ -z "${RELEASE_TAG:-}" ] || [ -z "${COMMIT_ID:-}" ] || [ -z "${SOURCE_REPOSITORY_ID:-}" ]; then
  echo "Missing required parameters" >&2
  exit 1
fi

require_cmd docker
require_cmd oci
require_cmd python3

COMMIT_ID="$(printf "%s" "$COMMIT_ID" | tr '[:upper:]' '[:lower:]')"

if ! validate_ocid "$COMPARTMENT_ID"; then
  echo "Invalid compartment OCID" >&2
  exit 1
fi

if ! validate_ocid "$SOURCE_REPOSITORY_ID"; then
  echo "Invalid source repository OCID" >&2
  exit 1
fi

if ! validate_region_key "$OCIR_REGION_KEY"; then
  echo "Invalid OCIR region key: ${OCIR_REGION_KEY}" >&2
  exit 1
fi

if ! validate_name "$COMPONENT_NAME"; then
  echo "Invalid component name: ${COMPONENT_NAME}" >&2
  exit 1
fi

if ! validate_repo_path "$OCIR_REPOSITORY_PATH"; then
  echo "Invalid OCIR repository path: ${OCIR_REPOSITORY_PATH}" >&2
  exit 1
fi

if ! validate_release_tag "$RELEASE_TAG"; then
  echo "Invalid release tag: ${RELEASE_TAG}" >&2
  exit 1
fi

if ! validate_commit_id "$COMMIT_ID"; then
  echo "Invalid commit id: ${COMMIT_ID}" >&2
  exit 1
fi

if [ -n "${TENANCY_NAMESPACE:-}" ] && ! validate_namespace "$TENANCY_NAMESPACE"; then
  echo "Invalid tenancy namespace: ${TENANCY_NAMESPACE}" >&2
  exit 1
fi

repo_namespace="${TENANCY_NAMESPACE:-}"
if [ -z "$repo_namespace" ]; then
  repo_namespace=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query "data.namespace" --raw-output)
fi

REMOTE_REGISTRY="${OCIR_REGION_KEY}.ocir.io"
IMAGE_REPOSITORY="${OCIR_REPOSITORY_PATH%/}"
IMAGE_REPOSITORY_REF="${REMOTE_REGISTRY}/${repo_namespace}/${IMAGE_REPOSITORY}"
SOURCE_SHA_TAG="${COMMIT_ID:0:7}"
SOURCE_IMAGE="${IMAGE_REPOSITORY_REF}:${SOURCE_SHA_TAG}"
TARGET_IMAGE="${IMAGE_REPOSITORY_REF}:${RELEASE_TAG}"

TOKEN="$(oci raw-request --http-method GET --target-uri "https://${REMOTE_REGISTRY}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

if ! image_exists "$SOURCE_IMAGE"; then
  echo "Source image does not exist: ${SOURCE_IMAGE}" >&2
  exit 1
fi

if image_exists "$TARGET_IMAGE"; then
  echo "Target image already exists: ${TARGET_IMAGE}" >&2
  exit 1
fi

if release_tag_exists; then
  echo "Release Git tag already exists: ${RELEASE_TAG}" >&2
  exit 1
fi

source_inspect="$(mktemp)"
target_inspect="$(mktemp)"
source_digest="$(inspect_digest "$SOURCE_IMAGE" "$source_inspect")"

run_skopeo copy \
  --all \
  --src-creds "BEARER_TOKEN:${TOKEN}" \
  --dest-creds "BEARER_TOKEN:${TOKEN}" \
  "docker://${SOURCE_IMAGE}" \
  "docker://${TARGET_IMAGE}"

# Digest equality proves the release tag points at the exact image built from the commit SHA.
target_digest="$(inspect_digest "$TARGET_IMAGE" "$target_inspect")"
if [ "$source_digest" != "$target_digest" ]; then
  echo "Released image digest mismatch: ${source_digest} != ${target_digest}" >&2
  exit 1
fi

if release_tag_exists; then
  echo "Release Git tag already exists: ${RELEASE_TAG}" >&2
  exit 1
fi

oci devops repository create-or-update-git-tag-details \
  --repository-id "$SOURCE_REPOSITORY_ID" \
  --ref-name "$RELEASE_TAG" \
  --object-id "$COMMIT_ID" >/dev/null

if [ -n "${OUTPUT_ENV_FILE:-}" ]; then
  {
    printf "source_sha_tag=%s\n" "$SOURCE_SHA_TAG"
    printf "promoted_image_tag=%s\n" "$RELEASE_TAG"
    printf "promoted_image_uri=%s\n" "$TARGET_IMAGE"
  } > "$OUTPUT_ENV_FILE"
fi

printf "Tagged repository commit %s as %s\n" "$COMMIT_ID" "$RELEASE_TAG"
printf "Released %s to %s\n" "$SOURCE_IMAGE" "$TARGET_IMAGE"
printf "Digest: %s\n" "$target_digest"
