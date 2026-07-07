#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$(mktemp -d)"
OUTPUT="$PROJECT_ROOT/soc-detection-stack.zip"

echo "Building ORM stack zip..."
echo "  Build dir: $BUILD_DIR"

# Copy Terraform files
cp "$SCRIPT_DIR"/*.tf "$BUILD_DIR/"
cp "$SCRIPT_DIR"/schema.yaml "$BUILD_DIR/"

# Copy project assets needed by provisioners
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/scripts"
cp -r "$PROJECT_ROOT/queries" "$BUILD_DIR/queries"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/config"
cp -r "$PROJECT_ROOT/test_data" "$BUILD_DIR/test_data"

# Create the zip
cd "$BUILD_DIR"
zip -r "$OUTPUT" . -x "*.pyc" "__pycache__/*" ".env*" "*.zip"

echo ""
echo "Stack zip created: $OUTPUT"
echo "Upload to OCI Resource Manager to deploy."

# Cleanup
rm -rf "$BUILD_DIR"
