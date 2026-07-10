#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_ZIP="${STACK_ZIP_PATH:-${ROOT_DIR}/stack.zip}"
DEVELOPMENT_MODE="${STACK_DEVELOPMENT_MODE:-false}"

if [ "$DEVELOPMENT_MODE" != "true" ] && [ "$DEVELOPMENT_MODE" != "false" ]; then
  echo "STACK_DEVELOPMENT_MODE must be true or false." >&2
  exit 1
fi

STAGING_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

rsync -a \
  --exclude ".git" \
  --exclude ".agents" \
  --exclude ".terraform" \
  --exclude ".idea" \
  --exclude ".oca" \
  --exclude ".tmp-*" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude "AGENT.md" \
  --exclude "script/update_orm_stack.sh" \
  --exclude "terraform.tfstate*" \
  --exclude "*.tfvars" \
  --exclude ".DS_Store" \
  --exclude "stack.zip" \
  "$ROOT_DIR/" "$STAGING_DIR/"

if [ "$DEVELOPMENT_MODE" = "true" ]; then
  find "$STAGING_DIR" -name '*.tf' -type f -exec perl -0pi -e \
    's/\n[ \t]*lifecycle \{\n[ \t]*ignore_changes = all\n[ \t]*\}\n/\n/g' {} +
  printf 'development_mode = true\n' >"$STAGING_DIR/development.auto.tfvars"
fi

rm -f "$OUTPUT_ZIP"
(
  cd "$STAGING_DIR"
  zip -qr "$OUTPUT_ZIP" .
)

printf "Built %s in %s mode\n" "$OUTPUT_ZIP" "$([ "$DEVELOPMENT_MODE" = "true" ] && echo development || echo release)"
