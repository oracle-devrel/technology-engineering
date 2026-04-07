#!/bin/bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

unset -v COMPARTMENT_ID;
unset -v OCIR_REGION_KEY;
unset -v CHART_VERSION;
unset -v CHART_NAME;
unset -v OCIR_REPOSITORY_PATH;
unset -v HELM_REGISTRY;

while getopts c:k:n:v:p:r: flag
do
    case "${flag}" in
        c) COMPARTMENT_ID=${OPTARG};;
        k) OCIR_REGION_KEY=${OPTARG};;
        v) CHART_VERSION=${OPTARG};;
        n) CHART_NAME=${OPTARG};;
        p) OCIR_REPOSITORY_PATH=${OPTARG};;
        r) HELM_REGISTRY=${OPTARG};;
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

#Checking if registry creation necessary
repo_id=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_ID" --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --limit 1 --query data.items[0].id --raw-output);
# Create repo if it does not exist!
[ -z "$repo_id" ] && repo_id=$(oci artifacts container repository create --display-name "$OCIR_REPOSITORY_PATH/$CHART_NAME" --compartment-id "$COMPARTMENT_ID" --query data.id --raw-output);
# If repo_id is still empty, an error has occurred
[ -z "$repo_id" ] && exit 1

repo_namespace=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output);
repo_path=${OCIR_REGION_KEY}.ocir.io/${repo_namespace}/${OCIR_REPOSITORY_PATH}

helm pull ${HELM_REGISTRY}/${CHART_NAME} --version $CHART_VERSION
TOKEN="$(oci raw-request --http-method GET --target-uri "https://${OCIR_REGION_KEY}.ocir.io/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')";
echo $TOKEN | helm registry login ${OCIR_REGION_KEY}.ocir.io -u BEARER_TOKEN --password-stdin;
helm push ${CHART_NAME}-${CHART_VERSION}.tgz oci://${repo_path};
rm -f ${CHART_NAME}-${CHART_VERSION}.tgz

echo "Mirrored ${CHART_NAME} to oci://${repo_path}"
