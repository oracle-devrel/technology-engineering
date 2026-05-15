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

unset -v COMPARTMENT_ID;
unset -v OCIR_REGION_KEY;
unset -v CHART_VERSION;
unset -v CHART_NAME;
unset -v OCIR_REPOSITORY_PATH;
unset -v HELM_REGISTRY;
unset -v TENANCY_NAMESPACE;

while getopts c:k:n:v:p:r:t: flag
do
    case "${flag}" in
        c) COMPARTMENT_ID=${OPTARG};;
        k) OCIR_REGION_KEY=${OPTARG};;
        v) CHART_VERSION=${OPTARG};;
        n) CHART_NAME=${OPTARG};;
        p) OCIR_REPOSITORY_PATH=${OPTARG};;
        r) HELM_REGISTRY=${OPTARG};;
        t) TENANCY_NAMESPACE=${OPTARG};;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

if [ -z "$COMPARTMENT_ID" ] ||  [ -z "$OCIR_REGION_KEY" ] || [ -z "$CHART_VERSION" ] || [ -z "$CHART_NAME" ] || [ -z "$OCIR_REPOSITORY_PATH" ] || [ -z "$HELM_REGISTRY" ]; then
        echo 'Missing some parameters' >&2
        exit 1
fi

require_cmd oci
require_cmd helm

SOURCE_REPO_NAME="mirror-source"

pull_chart() {
  if [[ "$HELM_REGISTRY" == oci://* ]]; then
    helm pull "${HELM_REGISTRY%/}/${CHART_NAME}" --version "$CHART_VERSION"
  else
    helm repo add "$SOURCE_REPO_NAME" "$HELM_REGISTRY" --force-update
    helm repo update "$SOURCE_REPO_NAME"
    helm pull "${SOURCE_REPO_NAME}/${CHART_NAME}" --version "$CHART_VERSION"
  fi
}

log_info "Starting Helm chart mirror workflow"
log_info "Chart: ${CHART_NAME}"
log_info "Requested chart version: ${CHART_VERSION}"
log_info "Source Helm registry: ${HELM_REGISTRY}"
log_info "Target OCIR registry: ${OCIR_REGION_KEY}.ocir.io"

# Ensure helm repository path ends with /charts
if [[ "$OCIR_REPOSITORY_PATH" != */charts ]]; then
  log_info "Appending /charts to repository path: ${OCIR_REPOSITORY_PATH}"
  OCIR_REPOSITORY_PATH="${OCIR_REPOSITORY_PATH%/}/charts"
fi
log_info "Normalized OCIR repository path: ${OCIR_REPOSITORY_PATH}"

#Checking if registry creation necessary
log_info "Ensuring OCIR repository exists: ${OCIR_REPOSITORY_PATH}/${CHART_NAME}"
if ! repo_id=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_ID" --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --limit 1 --query data.items[0].id --raw-output 2>/dev/null); then
  repo_id=""
fi
if [ "$repo_id" = "null" ]; then
  repo_id=""
fi
# Create repo if it does not exist!
if [ -z "$repo_id" ]; then
  log_info "Repository not found. Creating it now"
  repo_id=$(oci artifacts container repository create --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --compartment-id "$COMPARTMENT_ID" --query data.id --raw-output)
else
  log_info "Repository already exists"
fi
# If repo_id is still empty, an error has occurred
[ -z "$repo_id" ] && exit 1

repo_namespace="${TENANCY_NAMESPACE:-}"
if [ -z "$repo_namespace" ]; then
  log_info "TENANCY_NAMESPACE not provided. Resolving from OCI compartment"
  repo_namespace=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output)
else
  log_info "Using TENANCY_NAMESPACE from input parameters"
fi
log_info "Resolved tenancy namespace: ${repo_namespace}"
repo_path=${OCIR_REGION_KEY}.ocir.io/${repo_namespace}/${OCIR_REPOSITORY_PATH}
log_info "Computed destination chart path: oci://${repo_path}"

log_info "Pulling chart from source registry"
pull_chart

log_info "Requesting OCIR bearer token"
TOKEN="$(oci raw-request --http-method GET --target-uri "https://${OCIR_REGION_KEY}.ocir.io/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')";
if [ -z "$TOKEN" ]; then
  echo "Failed to fetch OCIR bearer token" >&2
  exit 1
fi
log_info "Authenticating Helm client to OCIR"
echo $TOKEN | helm registry login ${OCIR_REGION_KEY}.ocir.io -u BEARER_TOKEN --password-stdin;

log_info "Pushing chart to OCIR"
helm push ${CHART_NAME}-${CHART_VERSION}.tgz oci://${repo_path};
log_info "Removing local chart archive"
rm -f ${CHART_NAME}-${CHART_VERSION}.tgz

log_info "Helm chart mirroring completed successfully"
echo "Mirrored ${CHART_NAME} to oci://${repo_path}"
