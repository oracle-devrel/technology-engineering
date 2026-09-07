#!/bin/bash

# RUN IN CLOUD SHELL!!!!

REMOTE_REGISTRY="lhr.ocir.io" # Replace it with your own regional registry
CREATE_OCIR_PUBLIC_REGISTRY=true
COMPARTMENT_ID="ocid1.compartment.oc1..."   # Compartment where images will be created

unset -v HELM_CHART;

while getopts c: flag
do
    case "${flag}" in
        c) HELM_CHART=${OPTARG};;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

if [ -z "$HELM_CHART" ]; then
        echo 'Missing -c (helm chart)' >&2
        exit 1
fi

# Extract image names and tags
images=$(helm template $HELM_CHART | grep -oE 'image:[[:space:]]*[^[:space:]]+' | sed 's/image:[[:space:]]*//')
# Remove duplicates
images=$(echo "$images" | tr ' ' '\n' | sort -u | tr '\n' ' ')

create_repo(){
  #Checking if registry creation necessary
  repo_id=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_ID" --display-name "$1" --limit 1 --query data.items[0].id --raw-output);
  # Create repo if it does not exist!
  [ -z "$repo_id" ] && repo_id=$(oci artifacts container repository create --display-name "$1" --compartment-id "$COMPARTMENT_ID" --is-public $CREATE_OCIR_PUBLIC_REGISTRY --query data.id --raw-output);
  # If repo_id is still empty, an error has occurred
  [ -z "$repo_id" ] && exit 1
}

for image in $images; do

  # Remove quotes and double quotes
  image=${image//[\"\']/}

  echo "Processing image: $image"
  base_image="${image#*/}"
  image_name="${base_image%%:*}"
  image_tag="${base_image#*:}"

  REPO_NAMESPACE=$(oci artifacts container configuration get --compartment-id "$COMPARTMENT_ID" --query data.namespace --raw-output);

  create_repo "$image_name"

  TOKEN=$(oci raw-request --http-method GET --target-uri "https://${REMOTE_REGISTRY}/20180419/docker/token" | jq -r .data.token);

  skopeo copy "docker://$image" "docker://$REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag" --multi-arch system --override-os "linux" --dest-creds BEARER_TOKEN:$TOKEN

  echo "Mirrored $image to $REMOTE_REGISTRY/$REPO_NAMESPACE/$image_name:$image_tag"

done