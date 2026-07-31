#!/bin/bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

log_info() {
  echo "[INFO] $*"
}

CREATE_OCIR_PUBLIC_REGISTRY=false

unset -v COMPARTMENT_ID;
unset -v OCIR_REGION_KEY;
unset -v CHART_VERSION;
unset -v CHART_NAME;
unset -v HELM_REGISTRY;
unset -v IMAGE_PREFIX;
unset -v TENANCY_NAMESPACE;

while getopts c:k:v:n:r:p:t:a: flag
do
    case "${flag}" in
        c) COMPARTMENT_ID=${OPTARG};;
        k) OCIR_REGION_KEY=${OPTARG};;
        v) CHART_VERSION=${OPTARG};;
        n) CHART_NAME=${OPTARG};;
        r) HELM_REGISTRY=${OPTARG};;
        p) IMAGE_PREFIX=${OPTARG};;
        t) TENANCY_NAMESPACE=${OPTARG};;
        a) : ;; # kept for backward compatibility, ignored
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

if [ -z "$COMPARTMENT_ID" ] || [ -z "$OCIR_REGION_KEY" ] || [ -z "$CHART_VERSION" ] || [ -z "$CHART_NAME" ] || [ -z "$HELM_REGISTRY" ] || [ -z "$IMAGE_PREFIX" ]; then
        echo 'Missing some parameters' >&2
        exit 1
fi

require_cmd oci
require_cmd helm
require_cmd docker
require_cmd sed
require_cmd tr

SOURCE_REPO_NAME="mirror-source"

template_chart() {
  if [[ "$HELM_REGISTRY" == oci://* ]]; then
    helm template "$CHART_NAME" "${HELM_REGISTRY%/}/${CHART_NAME}" --version "$CHART_VERSION"
  else
    helm repo add "$SOURCE_REPO_NAME" "$HELM_REGISTRY" --force-update
    helm repo update "$SOURCE_REPO_NAME"
    helm template "$CHART_NAME" "${SOURCE_REPO_NAME}/${CHART_NAME}" --version "$CHART_VERSION"
  fi
}

REMOTE_REGISTRY="${OCIR_REGION_KEY}.ocir.io"
SKOPEO_IMAGE="quay.io/skopeo/stable:latest"

log_info "Starting Helm image mirroring workflow"
log_info "Chart: ${CHART_NAME}"
log_info "Chart version: ${CHART_VERSION}"
log_info "Source Helm registry: ${HELM_REGISTRY}"
log_info "Image destination prefix: ${IMAGE_PREFIX}"
log_info "Target OCIR registry: ${REMOTE_REGISTRY}"

REPO_NAMESPACE="${TENANCY_NAMESPACE:-}"
if [ -z "$REPO_NAMESPACE" ]; then
  log_info "TENANCY_NAMESPACE not provided. Resolving from OCI compartment"
  REPO_NAMESPACE=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output)
else
  log_info "Using TENANCY_NAMESPACE from input parameters"
fi
log_info "Resolved tenancy namespace: ${REPO_NAMESPACE}"

# Extract image names and tags
images=$(template_chart | grep -oE 'image:[[:space:]]*[^[:space:]]+' | sed 's/image:[[:space:]]*//')
# Remove duplicates
images=$(echo "$images" | tr ' ' '\n' | sort -u | tr '\n' ' ')
log_info "Resolved image list from chart template"

create_repo(){
  local repo_name="$1"
  local repo_id=""

  # Query can return non-zero when no items match; tolerate that and create.
  if ! repo_id=$(oci artifacts container repository list \
    --compartment-id "$COMPARTMENT_ID" \
    --display-name "$repo_name" \
    --limit 1 \
    --query data.items[0].id \
    --raw-output 2>/dev/null); then
    repo_id=""
  fi

  if [ "$repo_id" = "null" ]; then
    repo_id=""
  fi

  if [ -z "$repo_id" ]; then
    if ! repo_id=$(oci artifacts container repository create \
      --display-name "$repo_name" \
      --compartment-id "$COMPARTMENT_ID" \
      --is-public "$CREATE_OCIR_PUBLIC_REGISTRY" \
      --query data.id \
      --raw-output); then
      echo "Failed to create OCIR repository: $repo_name" >&2
      exit 1
    fi
  fi
}

run_skopeo_copy() {
  local src_image="$1"
  local dst_image="$2"
  local token="$3"

  docker run --rm "$SKOPEO_IMAGE" \
    copy --all \
    --dest-creds "BEARER_TOKEN:${token}" \
    "docker://${src_image}" \
    "docker://${dst_image}"
}

# Ensure the skopeo container image is available before starting the loop.
log_info "Ensuring skopeo helper image is available: ${SKOPEO_IMAGE}"
docker image inspect "$SKOPEO_IMAGE" >/dev/null 2>&1 || docker pull "$SKOPEO_IMAGE" >/dev/null

log_info "Requesting OCIR bearer token"
TOKEN="$(oci raw-request --http-method GET --target-uri "https://${REMOTE_REGISTRY}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi

for image in $images; do

  # Remove quotes and double quotes
  image=${image//[\"\']/}

  log_info "Processing source image: ${image}"
  image_ref="${image##*/}"
  image_name="${image_ref%%:*}"
  image_tag="${image_ref#*:}"

  image_name=$IMAGE_PREFIX/"$image_name"
  log_info "Ensuring destination repository exists: ${image_name}"

  create_repo "$image_name"

  # Copy all manifests/platforms to preserve digest references used by Flux.
  log_info "Mirroring image to OCIR: ${REMOTE_REGISTRY}/${REPO_NAMESPACE}/${image_name}:${image_tag}"
  run_skopeo_copy "$image" "$REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag" "$TOKEN"

  log_info "Mirrored $image to $REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag"

done

log_info "Helm image mirroring completed successfully"
