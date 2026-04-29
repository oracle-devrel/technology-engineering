#!/bin/bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

log_info() {
  echo "[INFO] $*" >&2
}

require_cmd oci
require_cmd docker

unset -v COMPARTMENT_ID;
unset -v REGION_KEY;
unset -v OCI_REGION;
unset -v FLUX_OPERATOR_VERSION;
unset -v OCIR_REPOSITORY_PATH;
unset -v TENANCY_NAMESPACE;
unset -v DOCKER_AUTH_DIR;

GITOPS_AGENT_NAME="flux-operator"
COMPONENTS="source-controller,kustomize-controller,helm-controller"

while getopts c:k:v:p:t: flag
do
    case "${flag}" in
        c) COMPARTMENT_ID=${OPTARG};;
        k) REGION_KEY=${OPTARG};;
        v) FLUX_OPERATOR_VERSION=${OPTARG};;
        p) OCIR_REPOSITORY_PATH=${OPTARG};;
        t) TENANCY_NAMESPACE=${OPTARG};;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

if [ -z "$COMPARTMENT_ID" ] || [ -z "$OCIR_REPOSITORY_PATH" ]; then
        echo 'Missing some parameters' >&2
        exit 1
fi

OCI_REGION="${OCI_CLI_REGION:-}"
if [ -z "$OCI_REGION" ]; then
  log_info "OCI_CLI_REGION not set. Falling back to OCI CLI config"
  OCI_REGION="$(oci configure get region 2>/dev/null || true)"
else
  log_info "Using OCI region from OCI_CLI_REGION"
fi

if [ -z "$OCI_REGION" ]; then
  echo "Unable to resolve OCI region. Set OCI_CLI_REGION or configure OCI CLI region." >&2
  exit 1
fi

log_info "Resolving OCIR region key for OCI region: ${OCI_REGION}"
if [ -z "${REGION_KEY:-}" ]; then
  REGION_KEY="$(oci iam region list --query "data[?name == '$OCI_REGION'].key | [0]" --raw-output | tr '[:upper:]' '[:lower:]')"
  if [ -z "$REGION_KEY" ] || [ "$REGION_KEY" = "null" ]; then
    echo "Unable to resolve OCIR region key for region: $OCI_REGION" >&2
    exit 1
  fi
else
  REGION_KEY="$(echo "$REGION_KEY" | tr '[:upper:]' '[:lower:]')"
  log_info "Using REGION_KEY from input parameters"
fi

log_info "Starting Flux mirror workflow"
log_info "OCI region: ${OCI_REGION}"
log_info "Target registry: ${REGION_KEY}.ocir.io"
log_info "Target repository path prefix: ${OCIR_REPOSITORY_PATH}"

DOCKER_AUTH_DIR="${DOCKER_CONFIG:-${HOME:-/root}/.docker}"
mkdir -p "${DOCKER_AUTH_DIR}"
log_info "Using Docker auth directory on host: ${DOCKER_AUTH_DIR}"

create_repo() {
  local CREATE_OCIR_PUBLIC_REGISTRY=false
  local repo_name="$1"
  local repo_id=""

  log_info "Ensuring OCIR repository exists: ${repo_name}"

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
    log_info "Repository not found. Creating: ${repo_name}"
    if ! repo_id=$(oci artifacts container repository create \
      --display-name "$repo_name" \
      --compartment-id "$COMPARTMENT_ID" \
      --is-public "$CREATE_OCIR_PUBLIC_REGISTRY" \
      --query data.id \
      --raw-output); then
      echo "Failed to create OCIR repository: $repo_name" >&2
      exit 1
    fi
    log_info "Repository created: ${repo_name}"
  else
    log_info "Repository already exists: ${repo_name}"
  fi
}


#Checking if registry creation necessary
log_info "Preparing chart and component repositories in OCIR"
create_repo "$OCIR_REPOSITORY_PATH/charts/$GITOPS_AGENT_NAME"

# Create repositories for Flux components.
IFS=',' read -r -a components <<< "$COMPONENTS"
for component in "${components[@]}"; do
  create_repo "$OCIR_REPOSITORY_PATH/$component"
done

# Create also a repository for flux-operator image
create_repo "$OCIR_REPOSITORY_PATH/$GITOPS_AGENT_NAME"

# Login to the registry
log_info "Authenticating to OCIR"
log_info "Requesting OCIR bearer token"
TOKEN="$(oci raw-request --http-method GET --target-uri "https://${REGION_KEY}.ocir.io/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi
log_info "Writing docker login credentials into: ${DOCKER_AUTH_DIR}"
echo "$TOKEN" | DOCKER_CONFIG="${DOCKER_AUTH_DIR}" docker login ${REGION_KEY}.ocir.io -u BEARER_TOKEN --password-stdin;
log_info "OCIR login completed"

# Find the latest flux operator version through skopeo
SKOPEO_IMAGE="quay.io/skopeo/stable:latest"
FLUX_OPERATOR_CLI_IMAGE="ghcr.io/controlplaneio-fluxcd/flux-operator-cli"

get_latest_flux_operator_version() {
  local tags_json
  local latest_version

  log_info "Ensuring skopeo helper image is available: ${SKOPEO_IMAGE}"
  docker image inspect "$SKOPEO_IMAGE" >/dev/null 2>&1 || docker pull "$SKOPEO_IMAGE" >/dev/null

  log_info "Listing available tags for ${FLUX_OPERATOR_CLI_IMAGE}"
  if ! tags_json=$(docker run --rm "$SKOPEO_IMAGE" list-tags "docker://${FLUX_OPERATOR_CLI_IMAGE}"); then
    echo "Failed to list tags for ${FLUX_OPERATOR_CLI_IMAGE}" >&2
    exit 1
  fi

  latest_version=$(
    echo "$tags_json" \
      | tr -d '[:space:]' \
      | sed 's/.*"Tags":\[//; s/\].*//' \
      | tr ',' '\n' \
      | tr -d '"' \
      | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' \
      | sed 's/^v//' \
      | sort -t. -k1,1n -k2,2n -k3,3n \
      | tail -1
  )

  if [ -z "$latest_version" ]; then
    echo "No semver tag found for ${FLUX_OPERATOR_CLI_IMAGE}" >&2
    exit 1
  fi

  echo "v${latest_version}"
}

if [ -z "${FLUX_OPERATOR_VERSION:-}" ]; then
  log_info "No Flux Operator version provided. Resolving latest version from ${FLUX_OPERATOR_CLI_IMAGE}"
  FLUX_OPERATOR_VERSION="$(get_latest_flux_operator_version)"
fi
log_info "Using Flux Operator version: ${FLUX_OPERATOR_VERSION}"

if [ -z "${TENANCY_NAMESPACE:-}" ]; then
  log_info "Resolving OCIR tenancy namespace from compartment"
  TENANCY_NAMESPACE=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output)
else
  log_info "Using TENANCY_NAMESPACE from input parameters"
fi
log_info "Resolved OCIR namespace: ${TENANCY_NAMESPACE}"

FLUX_OPERATOR_CLI_VERSION_IMAGE="${FLUX_OPERATOR_CLI_IMAGE}:${FLUX_OPERATOR_VERSION}"
log_info "Ensuring CLI image is available locally: ${FLUX_OPERATOR_CLI_VERSION_IMAGE}"
docker image inspect "$FLUX_OPERATOR_CLI_VERSION_IMAGE" >/dev/null 2>&1 || docker pull "$FLUX_OPERATOR_CLI_VERSION_IMAGE" >/dev/null

log_info "Running flux-operator distro mirror for components: ${COMPONENTS}"
log_info "Mounting Docker auth directory into container: ${DOCKER_AUTH_DIR} -> /tmp/docker-config"
docker run --rm \
  --user 0:0 \
  -e DOCKER_CONFIG=/tmp/docker-config \
  -v "${DOCKER_AUTH_DIR}:/tmp/docker-config:ro" \
  --entrypoint=flux-operator \
  "$FLUX_OPERATOR_CLI_VERSION_IMAGE" \
  distro mirror "${REGION_KEY}.ocir.io/${TENANCY_NAMESPACE}/${OCIR_REPOSITORY_PATH}" --components "$COMPONENTS"

log_info "Flux component mirroring completed successfully"
log_info "Mirror target: ${REGION_KEY}.ocir.io/${TENANCY_NAMESPACE}/${OCIR_REPOSITORY_PATH}"
