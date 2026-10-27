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

# Package only reviewed inputs, even when the working directory contains local
# credentials, generated repositories, or one-off maintenance scripts.
MANIFEST="$ROOT_DIR/release-files.txt"
while IFS= read -r entry; do
  case "$entry" in
    ""|/*|../*|*/../*|*/..|./*|*/./*) echo "Unsafe release path: $entry" >&2; exit 1 ;;
  esac
  if [ ! -f "$ROOT_DIR/$entry" ]; then
    echo "Missing release file: $entry" >&2
    exit 1
  fi
  parent="$entry"
  while [ "$parent" != "." ]; do
    if [ -L "$ROOT_DIR/$parent" ]; then
      echo "Release paths must not contain symlinks: $entry" >&2
      exit 1
    fi
    parent="$(dirname "$parent")"
  done
done < "$MANIFEST"

OUTPUT_ZIP="$(cd "$(dirname "$OUTPUT_ZIP")" && pwd)/$(basename "$OUTPUT_ZIP")"

rsync -a \
  --files-from="$MANIFEST" \
  --exclude ".git" \
  --exclude ".agents" \
  --exclude ".agents.zip" \
  --exclude "downloads" \
  --exclude ".terraform" \
  --exclude ".idea" \
  --exclude ".oca" \
  --exclude ".tmp-*" \
  --exclude "Projects" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude "AGENT.md" \
  --exclude "script/update_orm_stack.sh" \
  --exclude "script/package_user_skill.sh" \
  --exclude "terraform.tfstate*" \
  --exclude "*.tfvars" \
  --exclude "*.tfvars.json" \
  --exclude ".env" \
  --exclude ".env.*" \
  --exclude ".DS_Store" \
  --exclude "*.zip" \
  --exclude "stack.zip.sha256" \
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

(
  cd "$(dirname "$OUTPUT_ZIP")"
  shasum -a 256 "$(basename "$OUTPUT_ZIP")" > "$(basename "$OUTPUT_ZIP").sha256"
)

printf "Built %s in %s mode\n" "$OUTPUT_ZIP" "$([ "$DEVELOPMENT_MODE" = "true" ] && echo development || echo release)"
