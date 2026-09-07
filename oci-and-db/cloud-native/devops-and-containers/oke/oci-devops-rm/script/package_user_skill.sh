#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="use-oke-devops-starter"
SKILL_PARENT="${ROOT_DIR}/.agents/skills"
OUTPUT_DIR="${ROOT_DIR}/downloads"
OUTPUT_ZIP="${OUTPUT_DIR}/${SKILL_NAME}.zip"

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_ZIP"

(
  cd "$SKILL_PARENT"
  zip -qr "$OUTPUT_ZIP" "$SKILL_NAME"
)

printf 'Built %s\n' "$OUTPUT_ZIP"
