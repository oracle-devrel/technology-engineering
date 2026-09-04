#!/usr/bin/env bash

set -euo pipefail

# -------- CONFIG (platform sets these) --------
VAULT_ID=""
COMPARTMENT_ID=""
KEY_ID=""
OCI_PROFILE="${OCI_PROFILE:-DEFAULT}"

SCRIPT_NAME="./$(basename "$0")"

SECRET_NAME=""
INPUT_FILE=""
TEMPLATE_OUTPUT=""
NAMESPACE="<namespace>"
STORE_NAME="<secret-store-name>"
STORE_KIND="<ClusterSecretStore|SecretStore>"
TARGET_SECRET_NAME="<kubernetes-secret-name>"
TEMPLATE_ONLY=false
DRY_RUN=false
INPUT=""
JSON=""

usage() {
  cat <<EOF_USAGE
Usage:
  $SCRIPT_NAME <secret-name> [file] [options]

Examples:
  $SCRIPT_NAME app-dev secrets.env
  $SCRIPT_NAME app-prod secrets.env -o app-prod-externalsecret-template.yml
  cat secrets.env | $SCRIPT_NAME app-dev -o app-dev-externalsecret-template.yml
  printf 'DB_PASSWORD=secret\nAPI_KEY=abc123\n' | $SCRIPT_NAME app-dev -o app-dev-externalsecret-template.yml
  $SCRIPT_NAME app-dev --template-only -o app-dev-externalsecret-template.yml

Input:
  Either:
    - pass a file (KEY=value per line)
    - or pipe via stdin

Options:
  -o, --template-output <file>
      Write the generated ExternalSecret template to a YAML file.

  --namespace <namespace>
      Set metadata.namespace in the generated template.
      Default: <namespace>

  --store <name>
      Set spec.secretStoreRef.name in the generated template.
      Default: <secret-store-name>

  --store-kind <ClusterSecretStore|SecretStore>
      Set spec.secretStoreRef.kind in the generated template.
      Default: <ClusterSecretStore|SecretStore>

  --target <secret-name>
      Set spec.target.name in the generated template.
      Default: <kubernetes-secret-name>

  --template-only
      Generate the ExternalSecret template without creating or updating
      the OCI Vault secret. Input is optional in this mode.

  --dry-run
      Parse and validate input, print the generated JSON, and generate
      the ExternalSecret template without creating or updating the OCI
      Vault secret. Input is required unless --template-only is also used.

  -h, --help
      Show this help.

Notes:
  Script logs are written to stdout. Use -o/--template-output when you
  want a clean YAML file without log lines mixed into it.

  The generated template includes dataFrom.extract by default and a
  commented data section that can be used to manually select or rename keys.
EOF_USAGE
}

log() {
  echo "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

require_value() {
  local option="$1"
  local value="${2:-}"

  if [[ -z "$value" || "$value" == --* ]]; then
    fail "$option requires a value"
  fi
}

parse_args() {
  if [[ $# -eq 0 ]]; then
    usage
    exit 0
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      -o|--template-output)
        require_value "$1" "${2:-}"
        TEMPLATE_OUTPUT="$2"
        shift 2
        ;;
      --namespace)
        require_value "$1" "${2:-}"
        NAMESPACE="$2"
        shift 2
        ;;
      --store)
        require_value "$1" "${2:-}"
        STORE_NAME="$2"
        shift 2
        ;;
      --store-kind)
        require_value "$1" "${2:-}"
        STORE_KIND="$2"
        shift 2
        ;;
      --target)
        require_value "$1" "${2:-}"
        TARGET_SECRET_NAME="$2"
        shift 2
        ;;
      --template-only)
        TEMPLATE_ONLY=true
        shift
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --*)
        fail "Unknown option: $1"
        ;;
      *)
        if [[ -z "$SECRET_NAME" ]]; then
          SECRET_NAME="$1"
        elif [[ -z "$INPUT_FILE" ]]; then
          INPUT_FILE="$1"
        else
          fail "Unexpected argument: $1"
        fi
        shift
        ;;
    esac
  done

  if [[ -z "$SECRET_NAME" ]]; then
    usage
    exit 0
  fi
}

derive_region() {
  export OCI_CLI_REGION
  OCI_CLI_REGION="$(echo "$VAULT_ID" | cut -d'.' -f4)"

  if [[ -z "$OCI_CLI_REGION" ]]; then
    fail "Failed to extract region from VAULT_ID"
  fi

  log "Using region: $OCI_CLI_REGION"
}

ensure_dependencies() {
  command -v jq >/dev/null 2>&1 || fail "Missing dependency: jq"
}

read_input() {
  if [[ -n "$INPUT_FILE" ]]; then
    [[ -f "$INPUT_FILE" ]] || fail "Input file not found: $INPUT_FILE"
    INPUT="$(cat "$INPUT_FILE")"
    return
  fi

  if [[ "$TEMPLATE_ONLY" == true && -t 0 ]]; then
    INPUT=""
    return
  fi

  if [[ -t 0 ]]; then
    fail "No input provided. Pass a file or pipe KEY=value lines via stdin."
  fi

  INPUT="$(cat)"
}

parse_env_to_json() {
  if [[ -z "$INPUT" ]]; then
    if [[ "$TEMPLATE_ONLY" == true ]]; then
      JSON="{}"
      return
    fi

    fail "No input provided"
  fi

  JSON="{}"

  local line_number=0
  local raw_line
  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    line_number=$((line_number + 1))

    local line trimmed entry key value
    line="${raw_line%$'\r'}"
    trimmed="$(printf '%s' "$line" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"

    if [[ -z "$trimmed" || "$trimmed" == \#* ]]; then
      continue
    fi

    entry="$(printf '%s' "$trimmed" | sed -E 's/^export[[:space:]]+//')"

    if [[ "$entry" =~ ^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"

      if [[ ${#value} -ge 2 ]]; then
        if [[ "${value:0:1}" == '"' && "${value: -1}" == '"' ]]; then
          value="${value:1:${#value}-2}"
        elif [[ "${value:0:1}" == "'" && "${value: -1}" == "'" ]]; then
          value="${value:1:${#value}-2}"
        fi
      fi

      JSON="$(jq --arg key "$key" --arg value "$value" '. + {($key): $value}' <<< "$JSON")"
    else
      fail "Malformed env input on line $line_number: $line"
    fi
  done <<< "$INPUT"
}

print_generated_json() {
  log "Generated JSON:"
  echo "$JSON" | jq .
}

render_external_secret_template() {
  cat <<EOF_TEMPLATE
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: ${SECRET_NAME}
  namespace: ${NAMESPACE}
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: ${STORE_NAME}
    kind: ${STORE_KIND}
  target:
    name: ${TARGET_SECRET_NAME}
    creationPolicy: Owner

  # Option A: import all keys from the OCI Vault secret JSON.
  dataFrom:
    - extract:
        key: ${SECRET_NAME}

  # Option B: manually map selected keys or rename them.
  # Remove dataFrom above if using this section.
  # data:
EOF_TEMPLATE

  local keys
  keys="$(echo "$JSON" | jq -r 'keys[]?' 2>/dev/null || true)"

  if [[ -n "$keys" ]]; then
    while IFS= read -r key; do
      cat <<EOF_KEY
  #   - secretKey: ${key}
  #     remoteRef:
  #       key: ${SECRET_NAME}
  #       property: ${key}
EOF_KEY
    done <<< "$keys"
  else
    cat <<EOF_PLACEHOLDER
  #   - secretKey: <kubernetes-secret-key>
  #     remoteRef:
  #       key: ${SECRET_NAME}
  #       property: <json-property-in-oci-vault-secret>
EOF_PLACEHOLDER
  fi
}

write_or_print_template() {
  if [[ -n "$TEMPLATE_OUTPUT" ]]; then
    render_external_secret_template > "$TEMPLATE_OUTPUT"
    log "ExternalSecret template written to: $TEMPLATE_OUTPUT"
  else
    log ""
    log "ExternalSecret template:"
    log ""
    render_external_secret_template
  fi
}

create_or_update_secret() {
  if [[ "$TEMPLATE_ONLY" == true ]]; then
    log "Template-only mode: skipping OCI Vault secret create/update"
    return
  fi

  if [[ "$DRY_RUN" == true ]]; then
    log "Dry-run mode: skipping OCI Vault secret create/update"
    return
  fi

  local base64_content
  base64_content="$(echo -n "$JSON" | base64 | tr -d '\n')"

  log "Checking if secret exists: $SECRET_NAME"

  local existing_secret_id
  existing_secret_id="$(oci vault secret list \
    --compartment-id "$COMPARTMENT_ID" \
    --name "$SECRET_NAME" \
    --profile "$OCI_PROFILE" \
    --query "data[0].id" \
    --raw-output 2>/dev/null || echo "")"

  if [[ -z "$existing_secret_id" || "$existing_secret_id" == "null" ]]; then
    log "Creating secret: $SECRET_NAME"

    oci vault secret create-base64 \
      --compartment-id "$COMPARTMENT_ID" \
      --vault-id "$VAULT_ID" \
      --key-id "$KEY_ID" \
      --secret-name "$SECRET_NAME" \
      --secret-content-content "$base64_content" \
      --profile "$OCI_PROFILE" >/dev/null

    log "Secret created"
  else
    log "Updating existing secret"

    oci vault secret update-base64 \
      --secret-id "$existing_secret_id" \
      --secret-content-content "$base64_content" \
      --profile "$OCI_PROFILE" >/dev/null

    log "Secret updated"
  fi
}

main() {
  parse_args "$@"
  derive_region
  ensure_dependencies
  read_input
  parse_env_to_json
  print_generated_json
  create_or_update_secret
  write_or_print_template
  log "Done: $SECRET_NAME"
}

main "$@"
