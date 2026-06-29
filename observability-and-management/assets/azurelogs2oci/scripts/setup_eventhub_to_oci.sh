#!/usr/bin/env bash
# Interactive helper to collect Azure Event Hub + OCI Streaming settings and write a local .env.local
# - Discovers Event Hubs via Azure CLI (allows multi-select)
# - Resolves the Event Hubs connection string via Azure CLI (RootManageSharedAccessKey)
# - Prompts for OCI stream endpoint/OCID and credentials
# - Writes .env.local (git-ignored) for use by drain_eventhub_to_oci.sh and local.settings.json generation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="$REPO_ROOT/.env.local"

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=discover_resources.sh
source "$SCRIPT_DIR/discover_resources.sh"

require_cmd az
require_cmd python3

# Preload existing local env to reuse values if present
load_env "$ENV_PATH"

RG_DEFAULT="${EVENTHUB_RG:-}"
NS_DEFAULT="${EVENTHUB_NAMESPACE:-}"
EH_DEFAULT="${EVENTHUB_NAME:-}"
CG_DEFAULT="${EventHubConsumerGroup:-${EVENTHUB_CONSUMER_GROUP:-\$Default}}"
REGION_DEFAULT="${region:-us-ashburn-1}"
OCI_ENDPOINT_DEFAULT="${OCI_MESSAGE_ENDPOINT:-${MessageEndpoint:-}}"
OCI_STREAM_DEFAULT="${OCI_STREAM_OCID:-${StreamOcid:-}}"

EVENTHUB_RG="$(prompt_default "Resource group for Event Hubs namespace" "${RG_DEFAULT:-<rg-name>}")"
discover_azure_defaults "$EVENTHUB_RG"
NS_DEFAULT="${NS_DEFAULT:-${DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE:-}}"
EVENTHUB_NAMESPACE="$(prompt_default "Event Hubs namespace" "${NS_DEFAULT:-<namespace>}")"

# Discover event hubs and allow multi-select
info "Fetching Event Hubs in namespace '$EVENTHUB_NAMESPACE'..."
set +e
HUBS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && HUBS+=("$line")
done < <(az eventhubs eventhub list --resource-group "$EVENTHUB_RG" --namespace-name "$EVENTHUB_NAMESPACE" --query "[].name" -o tsv 2>/dev/null)
set -e

EVENTHUB_NAMES_CSV=""
if [[ ${#HUBS[@]} -gt 0 ]]; then
  info "Available Event Hubs:"
  i=1
  for h in "${HUBS[@]}"; do
    echo "  [$i] $h"
    ((i++))
  done
read -r -p "Enter comma-separated numbers (or names) to include (leave blank to keep previous value): " selection
if [[ -n "$selection" ]]; then
  # Accept numbers or names
  IFS=',' read -r -a choices <<<"$selection"
  SELECTED=()
    for c in "${choices[@]}"; do
      c_trim="${c//[[:space:]]/}"
      if [[ "$c_trim" =~ ^[0-9]+$ ]]; then
        idx=$((c_trim-1))
        [[ $idx -ge 0 && $idx -lt ${#HUBS[@]} ]] && SELECTED+=("${HUBS[$idx]}")
      elif [[ -n "$c_trim" ]]; then
        SELECTED+=("$c_trim")
      fi
    done
    if [[ ${#SELECTED[@]} -gt 0 ]]; then
      EVENTHUB_NAMES_CSV="$(IFS=','; echo "${SELECTED[*]}")"
    fi
  fi
fi

if [[ -z "$EVENTHUB_NAMES_CSV" ]]; then
  EVENTHUB_NAMES_CSV="$(prompt_default "Comma-separated Event Hub names" "${EventHubNamesCsv:-${EH_DEFAULT:-insights-activity-logs}}")"
fi

EVENTHUB_CONSUMER_GROUP="$(prompt_default "Consumer group" "$CG_DEFAULT")"
PRIMARY_EVENTHUB="$(echo "$EVENTHUB_NAMES_CSV" | cut -d',' -f1 | tr -d '[:space:]')"

# Connection string via Azure CLI
info "Resolving Event Hubs connection string from Azure..."
set +e
EVENTHUB_CONNECTION_STRING="$(az eventhubs namespace authorization-rule keys list \
  --resource-group "$EVENTHUB_RG" \
  --namespace-name "$EVENTHUB_NAMESPACE" \
  --name "RootManageSharedAccessKey" \
  --query primaryConnectionString -o tsv 2>/dev/null)"
set -e
if [[ -z "$EVENTHUB_CONNECTION_STRING" ]]; then
  warn "Could not resolve connection string automatically. Please paste it."
  EVENTHUB_CONNECTION_STRING="$(prompt_default "EventHubsConnectionString" "${EventHubsConnectionString:-Endpoint=sb://...}")"
else
  ok "Resolved connection string from Azure CLI"
fi

discover_oci_stream_defaults
if [[ "$DISC_OCI_STREAM_OCID_IS_POOL" == "true" ]]; then
  warn "Configured OCI stream value points to a Stream Pool. Select the Stream OCID instead."
  OCI_STREAM_DEFAULT=""
fi
OCI_STREAM_DEFAULT="${OCI_STREAM_DEFAULT:-${DISC_OCI_SUGGESTED_STREAM_ID:-}}"
OCI_ENDPOINT_DEFAULT="${OCI_ENDPOINT_DEFAULT:-${DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT:-}}"

OCI_STREAM_OCID="$(prompt_default "OCI stream OCID (not stream pool)" "${OCI_STREAM_DEFAULT:-ocid1.stream.oc1..xxxx}")"
if is_oci_stream_pool_ocid "$OCI_STREAM_OCID"; then
  err "OCI stream value points to a Stream Pool. Use the Stream OCID (ocid1.stream...)."
  exit 1
fi
OCI_MESSAGE_ENDPOINT="$(prompt_default "OCI message endpoint" "${OCI_ENDPOINT_DEFAULT:-https://cell-1.streaming.<region>.oci.oraclecloud.com}")"

user="$(prompt_default "OCI user OCID" "${user:-ocid1.user.oc1..example}")"
fingerprint="$(prompt_default "OCI API key fingerprint" "${fingerprint:-<fingerprint>}")"
tenancy="$(prompt_default "OCI tenancy OCID" "${tenancy:-ocid1.tenancy.oc1..example}")"
region="$(prompt_default "OCI region" "$REGION_DEFAULT")"

key_content="${key_content:-}"
if [[ -z "$key_content" || "$key_content" == "-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----" ]]; then
  read -r -p "Path to OCI private key file (leave blank to paste manually): " key_path
  if [[ -n "$key_path" && -f "$key_path" ]]; then
    key_content="$(cat "$key_path")"
  else
    key_content="$(prompt_secret "Paste OCI private key content (will be written to .env.local)")"
  fi
fi
pass_phrase="$(prompt_default "OCI key pass phrase (blank if none)" "${pass_phrase:-}")"

# Confirm write
if [[ -f "$ENV_PATH" ]]; then
  warn "$ENV_PATH exists and will be overwritten."
fi
cat > "$ENV_PATH" <<EOF
# Generated by scripts/setup_eventhub_to_oci.sh
EventHubsConnectionString='$EVENTHUB_CONNECTION_STRING'
EventHubConsumerGroup='$EVENTHUB_CONSUMER_GROUP'
EventHubNamesCsv='$EVENTHUB_NAMES_CSV'
EventHubName='$PRIMARY_EVENTHUB'
EVENTHUB_RG='$EVENTHUB_RG'
EVENTHUB_NAMESPACE='$EVENTHUB_NAMESPACE'
EVENTHUB_NAME='$PRIMARY_EVENTHUB'

OCI_MESSAGE_ENDPOINT='$OCI_MESSAGE_ENDPOINT'
OCI_STREAM_OCID='$OCI_STREAM_OCID'

user='$user'
key_content='$key_content'
pass_phrase='$pass_phrase'
fingerprint='$fingerprint'
tenancy='$tenancy'
region='$region'

# Optional script tuning
COUNT='${COUNT:-0}'
INACTIVITY_TIMEOUT='${INACTIVITY_TIMEOUT:-30}'
EOF

ok "Wrote $ENV_PATH (git-ignored). Use it with drain_eventhub_to_oci.sh or to build local.settings.json."
info "Next: run ./scripts/drain_eventhub_to_oci.sh --from-beginning to validate connectivity."
