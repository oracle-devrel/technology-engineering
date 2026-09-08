#!/usr/bin/env bash
# =============================================================================
# Build the OCI Resource Manager stack package.
#
# Produces ../sentiment-intelligence.zip containing every artifact Resource
# Manager needs to create the stack: the Terraform root (*.tf), the child
# modules, and schema.yaml — all at the ROOT of the zip (RMS requires the
# configuration at the archive root, not nested in a folder).
#
# Deployment-time and local-only files are excluded (state, plans, the
# provider cache, tfvars with secrets, editor/OS cruft).
#
# Run manually or via the git pre-commit hook, which regenerates the zip
# whenever files under deployment/ are staged.
# =============================================================================
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEPLOY_DIR")"
ZIP_PATH="$PROJECT_ROOT/sentiment-intelligence.zip"

# Delete the previous package so the zip is a fresh, exact snapshot.
rm -f "$ZIP_PATH"

# Package the deployment sources with the config at the archive root.
( cd "$DEPLOY_DIR" && zip -r -q "$ZIP_PATH" . \
    -x '*.terraform*' \
       '*.tfstate*' \
       'tfplan' '*.tfplan' \
       'terraform.tfvars' \
       'build-stack-zip.sh' \
       '*.DS_Store' \
       '*/.DS_Store' )

echo "Built $ZIP_PATH"
