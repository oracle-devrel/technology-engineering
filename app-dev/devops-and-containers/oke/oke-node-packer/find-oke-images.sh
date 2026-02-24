#!/bin/bash

REGION=""
CLUSTER_OCID="" #The OCID of your OKE cluster.
OKE_VERSION="1.34" # match minor (e.g., 1.31, 1.32,1.33 ...), needed for OKEImage
OS_MAJOR="8" # optional, The major version of the Oracle Linux.
#EXCLUDE_PATTERN="aarch64|GPU" # optional,A pattern to exclude certain images (e.g.,aarch64|GPU to exclude ARM or GPU images)

oci ce node-pool-options get --region "${REGION}" --node-pool-option-id "${CLUSTER_OCID}" --output json | jq -r --arg ver "${OKE_VERSION:-}" --arg os "${OS_MAJOR:-}" --arg ex "${EXCLUDE_PATTERN:-}" '.data.sources[] | . as $src | ($src["source-name"] // "") as $name | select( ($ver == "" or ($name | test($ver))) and ($os == "" or ($name | test($os; "i"))) and ($ex == "" or ($name | test($ex; "i") | not)) ) | {id: $src["image-id"], source_name: $name}'