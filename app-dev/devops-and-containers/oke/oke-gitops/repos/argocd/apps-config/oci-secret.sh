#!/usr/bin/env bash

set -euo pipefail

# -------- CONFIG (platform sets these) --------
VAULT_ID="${VAULT_ID:-<vault-ocid>}"
COMPARTMENT_ID="${COMPARTMENT_ID:-<compartment-ocid>}"
KEY_ID="${KEY_ID:-<key-ocid>}"
OCI_PROFILE="${OCI_PROFILE:-DEFAULT}"

# -------- DERIVE REGION FROM VAULT OCID --------

export OCI_CLI_REGION=$(echo "$VAULT_ID" | cut -d'.' -f4)

if [[ -z "$OCI_CLI_REGION" ]]; then
  echo "❌  Failed to extract region from VAULT_ID"
  exit 1
fi

echo "🌍  Using region: $OCI_CLI_REGION"

# -------- USAGE --------
usage() {
  cat <<EOF
Usage:
  $0 <app> <env> [file]

Examples:
  $0 kontract dev
  $0 kontract prod secrets.env

Input:
  Either:
    - pass a file (KEY=value per line)
    - or pipe via stdin

Example:
  cat <<EOF | $0 kontract dev
  DB_PASSWORD=secret
  API_KEY=abc123
  EOF
EOF
  exit 1
}

[[ $# -lt 2 ]] && usage

APP="$1"
ENV="$2"
INPUT_FILE="${3:-}"

SECRET_NAME="${APP}-${ENV}"

# -------- READ INPUT --------
if [[ -n "${INPUT_FILE}" ]]; then
  INPUT="$(cat "$INPUT_FILE")"
else
  INPUT="$(cat)"
fi

if [[ -z "$INPUT" ]]; then
  echo "❌  No input provided"
  exit 1
fi

# -------- CONVERT TO JSON --------
JSON=$(echo "$INPUT" | awk -F= '
  NF==2 {
    gsub(/"/, "\\\"", $2);
    printf "\"%s\":\"%s\",\n", $1, $2
  }
' | sed '$ s/,$//' | awk 'BEGIN { print "{" } { print } END { print "}" }')

echo "🔧  Generated JSON:"
echo "$JSON" | jq .

# -------- BASE64 ENCODE --------
BASE64_CONTENT=$(echo -n "$JSON" | base64 | tr -d '\n')

# -------- CHECK IF SECRET EXISTS --------
echo "🔍  Checking if secret exists: $SECRET_NAME"

EXISTING_SECRET_ID=$(oci vault secret list \
  --compartment-id "$COMPARTMENT_ID" \
  --name "$SECRET_NAME" \
  --profile "$OCI_PROFILE" \
  --query "data[0].id" \
  --raw-output 2>/dev/null || echo "")

# -------- CREATE OR UPDATE --------
if [[ -z "$EXISTING_SECRET_ID" || "$EXISTING_SECRET_ID" == "null" ]]; then
  echo "🆕  Creating secret: $SECRET_NAME"

  oci vault secret create-base64 \
    --compartment-id "$COMPARTMENT_ID" \
    --vault-id "$VAULT_ID" \
    --key-id "$KEY_ID" \
    --secret-name "$SECRET_NAME" \
    --secret-content-content "$BASE64_CONTENT" \
    --profile "$OCI_PROFILE" >/dev/null

  echo "✅  Secret created"

else
  echo "♻️  Updating existing secret"

  oci vault secret update-base64 \
    --secret-id "$EXISTING_SECRET_ID" \
    --secret-content-content "$BASE64_CONTENT" \
    --profile "$OCI_PROFILE" >/dev/null

  echo "✅  Secret updated"
fi

echo "🚀  Done: $SECRET_NAME"