#!/usr/bin/env bash

set -euo pipefail

SNAPSHOT_TAG=${1:-$(date +%Y%m%d)}

echo "Creating snapshots with tag: $SNAPSHOT_TAG"

terraform output -json custom_software_source_ids | jq -r '
to_entries[] | "\(.value.id)|\(.value.display_name)"
' | while IFS="|" read -r ID NAME; do

  SNAP_NAME="${NAME/custom/snap}-${SNAPSHOT_TAG}"

  echo "→ Creating snapshot: $SNAP_NAME"

  oci os-management-hub software-source create-snapshot \
    --software-source-id "$ID" \
    --display-name "$SNAP_NAME" \
    --wait-for-state SUCCEEDED

done
