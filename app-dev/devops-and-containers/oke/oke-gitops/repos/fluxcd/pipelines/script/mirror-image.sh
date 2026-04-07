#!/bin/bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

CREATE_OCIR_PUBLIC_REGISTRY=false
unset -v COMPARTMENT_ID;
unset -v OCIR_REGION_KEY;
unset -v IMAGE_PREFIX;
unset -v IMAGES;

while getopts c:k:p:a:i: flag
do
    case "${flag}" in
        c) COMPARTMENT_ID=${OPTARG};;
        k) OCIR_REGION_KEY=${OPTARG};;
        p) IMAGE_PREFIX=${OPTARG};;
        a) : ;; # kept for backward compatibility, ignored
        i) IMAGES=${OPTARG};;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

if [ -z "$COMPARTMENT_ID" ] || [ -z "$OCIR_REGION_KEY" ] || [ -z "$IMAGE_PREFIX" ] || [ -z "$IMAGES" ]; then
        echo 'Missing some parameters' >&2
        exit 1
fi

REMOTE_REGISTRY="${OCIR_REGION_KEY}.ocir.io"

require_cmd oci
require_cmd docker
require_cmd sed
require_cmd tr

SKOPEO_IMAGE="quay.io/skopeo/stable:latest"

# Extract image names and tags
IMAGES=(${IMAGES//,/ })
# Remove duplicates
IMAGES=$(echo "$IMAGES" | tr ' ' '\n' | sort -u | tr '\n' ' ')

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
docker image inspect "$SKOPEO_IMAGE" >/dev/null 2>&1 || docker pull "$SKOPEO_IMAGE" >/dev/null

for image in $IMAGES; do

  # Remove quotes and double quotes
  image=${image//[\"\']/}

  echo "Processing image: $image"
  base_image="${image#*/}"
  image_name="${base_image%%:*}"
  image_tag="${base_image#*:}"

  image_name=$IMAGE_PREFIX/"$image_name"

  REPO_NAMESPACE=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output);

  create_repo "$image_name"

  TOKEN="$(oci raw-request --http-method GET --target-uri "https://${REMOTE_REGISTRY}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
  if [ -z "$TOKEN" ]; then
    echo "Failed to fetch OCIR bearer token" >&2
    exit 1
  fi

  # Copy all manifests/platforms to preserve digest references used by Flux.
  run_skopeo_copy "$image" "$REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag" "$TOKEN"

  echo "Mirrored $image to $REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag"

done
