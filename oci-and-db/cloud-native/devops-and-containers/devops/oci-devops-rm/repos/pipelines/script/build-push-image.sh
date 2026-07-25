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

validate_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._-]+$ ]]
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
unset -v IMAGE_NAME
unset -v OCIR_REPOSITORY_PATH
unset -v TENANCY_NAMESPACE

while getopts c:k:n:p:t: flag; do
  case "${flag}" in
    c) COMPARTMENT_ID=${OPTARG} ;;
    k) OCIR_REGION_KEY=${OPTARG} ;;
    n) IMAGE_NAME=${OPTARG} ;;
    p) OCIR_REPOSITORY_PATH=${OPTARG} ;;
    t) TENANCY_NAMESPACE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${COMPARTMENT_ID:-}" ] || [ -z "${OCIR_REGION_KEY:-}" ] || [ -z "${IMAGE_NAME:-}" ] || [ -z "${OCIR_REPOSITORY_PATH:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

require_cmd docker
require_cmd git
require_cmd oci

if ! validate_ocid "$COMPARTMENT_ID"; then
  echo "Invalid compartment OCID" >&2
  exit 1
fi

if ! validate_region_key "$OCIR_REGION_KEY"; then
  echo "Invalid OCIR region key: ${OCIR_REGION_KEY}" >&2
  exit 1
fi

if ! validate_name "$IMAGE_NAME"; then
  echo "Invalid image name: ${IMAGE_NAME}" >&2
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

if [ ! -f Dockerfile ]; then
  echo "Dockerfile not found in $(pwd)" >&2
  exit 1
fi

IMAGE_TAG="$(git rev-parse --short=7 HEAD)"
IMAGE_REPOSITORY="${OCIR_REPOSITORY_PATH%/}"

repo_namespace="${TENANCY_NAMESPACE:-}"
if [ -z "$repo_namespace" ]; then
  repo_namespace=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query "data.namespace" --raw-output)
fi

if ! repo_id=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_ID" --display-name "$IMAGE_REPOSITORY" --limit 1 --query "data.items[0].id" --raw-output 2>/dev/null); then
  repo_id=""
fi

if [ "$repo_id" = "null" ]; then
  repo_id=""
fi

if [ -z "$repo_id" ]; then
  oci artifacts container repository create --display-name "$IMAGE_REPOSITORY" --compartment-id "$COMPARTMENT_ID" >/dev/null
fi

REMOTE_REGISTRY="${OCIR_REGION_KEY}.ocir.io"
IMAGE_URI="${REMOTE_REGISTRY}/${repo_namespace}/${IMAGE_REPOSITORY}:${IMAGE_TAG}"

TOKEN="$(oci raw-request --http-method GET --target-uri "https://${REMOTE_REGISTRY}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

echo "$TOKEN" | docker login "$REMOTE_REGISTRY" -u BEARER_TOKEN --password-stdin
# Publish a multi-architecture manifest without relying on Buildx. OCI DevOps
# currently ships an older Buildx plugin, while Docker's manifest command is
# enough for this starter image lifecycle.
AMD64_IMAGE_URI="${REMOTE_REGISTRY}/${repo_namespace}/${IMAGE_REPOSITORY}:${IMAGE_TAG}-amd64"
ARM64_IMAGE_URI="${REMOTE_REGISTRY}/${repo_namespace}/${IMAGE_REPOSITORY}:${IMAGE_TAG}-arm64"

docker build --pull --platform linux/amd64 --tag "$AMD64_IMAGE_URI" .
docker push "$AMD64_IMAGE_URI"

docker build --pull --platform linux/arm64 --tag "$ARM64_IMAGE_URI" .
docker push "$ARM64_IMAGE_URI"

docker manifest rm "$IMAGE_URI" >/dev/null 2>&1 || true
if docker manifest add --help >/dev/null 2>&1; then
  docker manifest create "$IMAGE_URI"
  docker manifest add "$IMAGE_URI" "$AMD64_IMAGE_URI"
  docker manifest add "$IMAGE_URI" "$ARM64_IMAGE_URI"
  docker manifest push --all "$IMAGE_URI" "docker://${IMAGE_URI}"
else
  docker manifest create "$IMAGE_URI" "$AMD64_IMAGE_URI" "$ARM64_IMAGE_URI"
  docker manifest annotate "$IMAGE_URI" "$AMD64_IMAGE_URI" --os linux --arch amd64
  docker manifest annotate "$IMAGE_URI" "$ARM64_IMAGE_URI" --os linux --arch arm64
  docker manifest push "$IMAGE_URI"
fi

printf "%s\n" "$IMAGE_TAG" > image-version.txt
printf "Built and pushed %s\n" "$IMAGE_URI"
