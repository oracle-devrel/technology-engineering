#!/bin/bash
set -euo pipefail

DEFAULT_STACK_ID="ocid1.ormstack.oc1.eu-frankfurt-1.amaaaaaauevftmqahquri6ywkezcpdskdb5vcxskx52k4443h65awnsjwuva"
STACK_ID="${ORM_STACK_ID:-$DEFAULT_STACK_ID}"
IFS="." read -r _ _ _ INFERRED_STACK_REGION _ <<< "$STACK_ID"
STACK_REGION="${ORM_STACK_REGION:-$INFERRED_STACK_REGION}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP_PATH="$ROOT_DIR/stack.zip"

cd "$ROOT_DIR"
STACK_DEVELOPMENT_MODE="${STACK_DEVELOPMENT_MODE:-true}" ./update.sh

oci resource-manager stack update \
  --region "$STACK_REGION" \
  --stack-id "$STACK_ID" \
  --config-source "$ZIP_PATH" \
  --force \
  --wait-for-state ACTIVE \
  --query 'data."lifecycle-state"' \
  --raw-output

printf "Uploaded %s to Resource Manager stack %s in %s\n" "$ZIP_PATH" "$STACK_ID" "$STACK_REGION"
