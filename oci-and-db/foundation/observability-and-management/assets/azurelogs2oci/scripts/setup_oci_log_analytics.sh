#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup_oci_log_analytics.sh – Provision OCI Streaming + Log
#   Analytics resources for the Azure → OCI log pipeline.
#
# Creates (or reuses existing):
#   1. Stream Pool + Stream (Kafka-compatible ingest)
#   2. Log Analytics Log Group (AzureLogs)
#   3. Log Analytics custom fields (38 fields)
#   4. Log Analytics JSON parsers (EntraID Audit + Diagnostic Log)
#   5. Log Analytics source (Azure Logs)
#   6. Service Connector Hub (Stream → Log Analytics)
#
# Prerequisites:
#   - oci CLI configured (oci setup config)
#   - .env.local populated with OCI variables (or prompted)
#   - Python 3 + oci-sdk (pip install oci)
#
# Usage:
#   ./scripts/setup_oci_log_analytics.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="$REPO_ROOT/.env.local"

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=discover_resources.sh
source "$SCRIPT_DIR/discover_resources.sh"

require_cmd oci
require_cmd python3

# Verify OCI Python SDK is installed (required for field/parser creation)
if ! python3 -c "import oci" 2>/dev/null; then
  err "OCI Python SDK not found. Install it with: pip install oci"
  exit 1
fi

# Load existing env
load_env "$ENV_PATH"

# ── Collect required OCI parameters ──────────────────────────
OCI_COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-${OCI_COMPARTMENT_OCID:-}}"
OCI_REGION="${region:-${OCI_REGION:-}}"
OCI_USER_OCID="${user:-${OCI_USER_OCID:-}}"
OCI_FINGERPRINT="${fingerprint:-${OCI_FINGERPRINT:-}}"
OCI_TENANCY_OCID="${tenancy:-${OCI_TENANCY_OCID:-}}"
OCI_KEY_FILE="${KEY_FILE:-${OCI_KEY_FILE:-}}"
OCI_KEY_CONTENT="${key_content:-${OCI_KEY_CONTENT:-}}"
OCI_KEY_PASSPHRASE="${pass_phrase:-${OCI_KEY_PASSPHRASE:-}}"

OCI_COMPARTMENT_ID="$(prompt_required "OCI compartment OCID" "$OCI_COMPARTMENT_ID")"
OCI_REGION="$(prompt_required "OCI region" "${OCI_REGION:-us-ashburn-1}")"

if [[ -z "$OCI_USER_OCID" ]]; then
  OCI_USER_OCID="$(prompt_required "OCI user OCID" "")"
fi
if [[ -z "$OCI_FINGERPRINT" ]]; then
  OCI_FINGERPRINT="$(prompt_required "OCI API key fingerprint" "")"
fi
if [[ -z "$OCI_TENANCY_OCID" ]]; then
  OCI_TENANCY_OCID="$(prompt_required "OCI tenancy OCID" "")"
fi
if [[ -z "$OCI_KEY_CONTENT" && -z "$OCI_KEY_FILE" ]]; then
  read -r -p "Path to OCI private key file (leave blank to paste): " key_path
  if [[ -n "$key_path" && -f "$key_path" ]]; then
    OCI_KEY_FILE="$key_path"
    OCI_KEY_CONTENT="$(cat "$key_path")"
  else
    read -r -s -p "Paste OCI private key content: " OCI_KEY_CONTENT
    echo
  fi
elif [[ -z "$OCI_KEY_CONTENT" && -n "$OCI_KEY_FILE" && -f "$OCI_KEY_FILE" ]]; then
  OCI_KEY_CONTENT="$(cat "$OCI_KEY_FILE")"
fi

# Defaults
STREAM_POOL_NAME="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
STREAM_NAME="${OCI_STREAM_NAME:-azure-inbound-stream}"
PARTITIONS="${OCI_STREAM_PARTITIONS:-1}"
LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-AzureLogs}"
NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"
SCH_NAME="${OCI_SCH_NAME:-Azure-Stream-to-LogAnalytics}"

# Parser / source names
PARSER_NAME="azureEntraIDAuditJsonParser"
SOURCE_NAME="Azure Logs"

echo ""
echo "============================================================"
echo "  OCI End-to-End Setup for azurelogs2oci"
echo "============================================================"
echo "  Compartment:  ${OCI_COMPARTMENT_ID:0:30}..."
echo "  Region:       $OCI_REGION"
echo "  Stream Pool:  $STREAM_POOL_NAME"
echo "  Stream:       $STREAM_NAME"
echo "  Log Group:    $LOG_GROUP_NAME"
echo "  SCH:          $SCH_NAME"
echo "  Parser:       $PARSER_NAME"
echo "  Source:       $SOURCE_NAME"
echo "============================================================"
echo ""

# ── Auto-detect Log Analytics namespace ──────────────────────
if [[ -z "$NAMESPACE" ]]; then
  if [[ -z "$OCI_TENANCY_OCID" ]]; then
    err "OCI tenancy OCID is required for namespace detection."
    err "Set 'tenancy' or 'OCI_TENANCY_OCID' in .env.local."
    exit 1
  fi
  info "Detecting Log Analytics namespace..."
  NAMESPACE=$(oci log-analytics namespace list \
      --compartment-id "$OCI_TENANCY_OCID" \
      --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
  if [[ -z "$NAMESPACE" || "$NAMESPACE" == "null" ]]; then
    err "Could not detect Log Analytics namespace."
    err "Ensure Log Analytics is onboarded in your tenancy:"
    err "  OCI Console > Observability & Management > Log Analytics > 'Start Using Log Analytics'"
    err "Or set OCI_LOG_ANALYTICS_NAMESPACE explicitly."
    exit 1
  fi
  ok "Namespace: $NAMESPACE"
fi

# ── Discover existing OCI resources ──────────────────────────
discover_oci_resources || true
show_discovery_summary "oci"

# Count how many resources were found
FOUND_COUNT=0
[[ -n "$DISC_OCI_STREAM_POOL_ID" ]] && ((FOUND_COUNT++)) || true
[[ -n "$DISC_OCI_STREAM_ID" ]] && ((FOUND_COUNT++)) || true
[[ -n "$DISC_OCI_LOG_GROUP_ID" ]] && ((FOUND_COUNT++)) || true
[[ -n "$DISC_OCI_SCH_ID" ]] && ((FOUND_COUNT++)) || true
[[ -n "$DISC_OCI_LA_SOURCE" ]] && ((FOUND_COUNT++)) || true

SETUP_MODE="create"  # create | reuse | destroy

if [[ $FOUND_COUNT -gt 0 ]]; then
  echo "Existing OCI resources found ($FOUND_COUNT/5)."
  echo ""
  echo "  [1] Use existing resources (skip creation for found resources)"
  echo "  [2] Create new alongside existing (prompted for new names)"
  echo "  [3] Destroy existing and recreate from scratch"
  echo ""
  read -r -p "Choose [1/2/3] (default: 1): " choice
  choice="${choice:-1}"

  case "$choice" in
    1) SETUP_MODE="reuse" ;;
    2) SETUP_MODE="create" ;;
    3) SETUP_MODE="destroy" ;;
    *) warn "Invalid choice; defaulting to [1] reuse."; SETUP_MODE="reuse" ;;
  esac
else
  info "No existing resources found. Creating all from scratch."
fi

# If destroy mode: tear down existing resources first
if [[ "$SETUP_MODE" == "destroy" ]]; then
  warn "Destroying existing OCI resources..."

  # SCH
  if [[ -n "$DISC_OCI_SCH_ID" ]]; then
    info "Deleting SCH..."
    local_sch_state=$(oci sch service-connector get \
        --service-connector-id "$DISC_OCI_SCH_ID" \
        --query 'data."lifecycle-state"' --raw-output 2>/dev/null || echo "UNKNOWN")
    if [[ "$local_sch_state" == "ACTIVE" ]]; then
      oci sch service-connector deactivate \
          --service-connector-id "$DISC_OCI_SCH_ID" \
          --wait-for-state SUCCEEDED \
          --max-wait-seconds 120 >/dev/null 2>&1 || true
    fi
    oci sch service-connector delete \
        --service-connector-id "$DISC_OCI_SCH_ID" \
        --force \
        --wait-for-state SUCCEEDED \
        --max-wait-seconds 300 2>/dev/null || true
    ok "SCH deleted"
  fi

  # LA content
  if [[ -n "$NAMESPACE" ]]; then
    export LA_NAMESPACE="$NAMESPACE"
    export OCI_COMPARTMENT_ID
    export OCI_USER_OCID OCI_FINGERPRINT OCI_TENANCY_OCID OCI_KEY_CONTENT OCI_KEY_FILE OCI_KEY_PASSPHRASE OCI_REGION
    python3 "$SCRIPT_DIR/teardown_oci_log_analytics.py" || true
  fi

  # Log Group
  if [[ -n "$DISC_OCI_LOG_GROUP_ID" ]]; then
    info "Deleting Log Group..."
    oci log-analytics log-group delete \
        --namespace-name "$NAMESPACE" \
        --log-group-id "$DISC_OCI_LOG_GROUP_ID" \
        --force 2>/dev/null || true
    ok "Log Group deleted"
  fi

  # Stream
  if [[ -n "$DISC_OCI_STREAM_ID" ]]; then
    info "Deleting Stream..."
    oci streaming admin stream delete \
        --stream-id "$DISC_OCI_STREAM_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 120 2>/dev/null || true
    ok "Stream deleted"
  fi

  # Stream Pool
  if [[ -n "$DISC_OCI_STREAM_POOL_ID" ]]; then
    info "Deleting Stream Pool..."
    oci streaming admin stream-pool delete \
        --stream-pool-id "$DISC_OCI_STREAM_POOL_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 120 2>/dev/null || true
    ok "Stream Pool deleted"
  fi

  ok "Existing resources destroyed. Proceeding to create..."
  # Reset discovery vars so creation logic runs
  DISC_OCI_STREAM_POOL_ID=""
  DISC_OCI_STREAM_ID=""
  DISC_OCI_LOG_GROUP_ID=""
  DISC_OCI_SCH_ID=""
  DISC_OCI_LA_SOURCE=""
  SETUP_MODE="create"
fi

# ── 1. Stream Pool ───────────────────────────────────────────
echo ""
echo "1/7  Stream Pool: $STREAM_POOL_NAME"

if [[ "$SETUP_MODE" == "reuse" && -n "$DISC_OCI_STREAM_POOL_ID" ]]; then
  POOL_ID="$DISC_OCI_STREAM_POOL_ID"
  ok "Reusing existing pool: ${POOL_ID:0:50}..."
else
  if [[ "$SETUP_MODE" == "create" && -n "$DISC_OCI_STREAM_POOL_ID" ]]; then
    # Creating new alongside existing
    STREAM_POOL_NAME="$(prompt_required "New stream pool name" "${STREAM_POOL_NAME}_2")"
  fi
  POOL_ID=$(oci streaming admin stream-pool create \
      --compartment-id "$OCI_COMPARTMENT_ID" \
      --name "$STREAM_POOL_NAME" \
      --query 'data.id' --raw-output \
      --wait-for-state ACTIVE \
      --max-wait-seconds 120)
  ok "Pool created: ${POOL_ID:0:50}..."
fi

# ── 2. Stream ────────────────────────────────────────────────
echo "2/7  Stream: $STREAM_NAME"

if [[ "$SETUP_MODE" == "reuse" && -n "$DISC_OCI_STREAM_ID" ]]; then
  STREAM_ID="$DISC_OCI_STREAM_ID"
  ok "Reusing existing stream: ${STREAM_ID:0:50}..."
else
  if [[ "$SETUP_MODE" == "create" && -n "$DISC_OCI_STREAM_ID" ]]; then
    STREAM_NAME="$(prompt_required "New stream name" "${STREAM_NAME}-2")"
  fi
  STREAM_ID=$(oci streaming admin stream create \
      --name "$STREAM_NAME" \
      --partitions "$PARTITIONS" \
      --stream-pool-id "$POOL_ID" \
      --query 'data.id' --raw-output \
      --wait-for-state ACTIVE \
      --max-wait-seconds 120)
  ok "Stream created: ${STREAM_ID:0:50}..."
fi

# ── 3. Kafka Connection Info ─────────────────────────────────
echo "3/7  Retrieving Kafka connection details..."
POOL_INFO=$(oci streaming admin stream-pool get --stream-pool-id "$POOL_ID")
KAFKA_ENDPOINT=$(echo "$POOL_INFO" | python3 -c "
import sys, json
d = json.load(sys.stdin)
settings = d.get('data', {}).get('kafka-settings', {})
print(settings.get('bootstrap-servers', 'N/A'))
" 2>/dev/null || echo "N/A")
ok "Bootstrap servers: $KAFKA_ENDPOINT"

# ── 4. Log Analytics Log Group ───────────────────────────────
echo "4/7  Log Analytics Log Group: $LOG_GROUP_NAME"

if [[ "$SETUP_MODE" == "reuse" && -n "$DISC_OCI_LOG_GROUP_ID" ]]; then
  LOG_GROUP_ID="$DISC_OCI_LOG_GROUP_ID"
  ok "Reusing existing log group: ${LOG_GROUP_ID:0:50}..."
else
  if [[ "$SETUP_MODE" == "create" && -n "$DISC_OCI_LOG_GROUP_ID" ]]; then
    LOG_GROUP_NAME="$(prompt_required "New log group name" "${LOG_GROUP_NAME}-2")"
  fi
  # Try to create; if it already exists (409), look it up and reuse
  LOG_GROUP_ID=$(oci log-analytics log-group create \
      --compartment-id "$OCI_COMPARTMENT_ID" \
      --namespace-name "$NAMESPACE" \
      --display-name "$LOG_GROUP_NAME" \
      --description "Azure log imports via azurelogs2oci pipeline" \
      --query 'data.id' --raw-output 2>/dev/null) || true
  if [[ -z "$LOG_GROUP_ID" || "$LOG_GROUP_ID" == "null" ]]; then
    info "Log group '$LOG_GROUP_NAME' already exists, looking it up..."
    LOG_GROUP_ID=$(oci log-analytics log-group list \
        --compartment-id "$OCI_COMPARTMENT_ID" \
        --namespace-name "$NAMESPACE" \
        --display-name "$LOG_GROUP_NAME" \
        --query 'data.items[0].id' --raw-output 2>/dev/null || true)
    if [[ -n "$LOG_GROUP_ID" && "$LOG_GROUP_ID" != "null" ]]; then
      ok "Reusing existing log group: ${LOG_GROUP_ID:0:50}..."
    else
      err "Could not create or find log group '$LOG_GROUP_NAME'"
      exit 1
    fi
  else
    ok "Log Group created: ${LOG_GROUP_ID:0:50}..."
  fi
fi

# ── 5. Create Log Analytics fields, parser, and source ────────
echo "5/7  Creating Azure log fields, parser, and source..."
export LA_NAMESPACE="$NAMESPACE"
export OCI_COMPARTMENT_ID
export OCI_USER_OCID OCI_FINGERPRINT OCI_TENANCY_OCID OCI_REGION
export OCI_KEY_CONTENT OCI_KEY_FILE OCI_KEY_PASSPHRASE

python3 "$REPO_ROOT/stack/scripts/setup_log_analytics.py"
ok "Log Analytics custom content created (38 fields, 2 parsers, source)"

# ── 6. Create Service Connector Hub ──────────────────────────
echo "6/7  Creating Service Connector Hub: $SCH_NAME"

SCH_ID=""
if [[ "$SETUP_MODE" == "reuse" && -n "$DISC_OCI_SCH_ID" ]]; then
  SCH_ID="$DISC_OCI_SCH_ID"
  ok "Reusing existing SCH: ${SCH_ID:0:50}..."
else
  if [[ "$SETUP_MODE" == "create" && -n "$DISC_OCI_SCH_ID" ]]; then
    SCH_NAME="$(prompt_required "New SCH name" "${SCH_NAME}-2")"
  fi

  # Source: OCI Streaming
  cat > /tmp/azure_sch_source.json << JSONEOF
{
  "kind": "streaming",
  "streamId": "$STREAM_ID",
  "cursor": {"kind": "TRIM_HORIZON"}
}
JSONEOF
  # Target: Log Analytics (logSourceIdentifier uses the source internal name)
  cat > /tmp/azure_sch_target.json << JSONEOF
{
  "kind": "loggingAnalytics",
  "logGroupId": "$LOG_GROUP_ID",
  "logSourceIdentifier": "azureLogsSource"
}
JSONEOF

  # SCH create is async (returns work request, not resource).
  # Fire the create, then look up the OCID by display name.
  oci sch service-connector create \
      --compartment-id "$OCI_COMPARTMENT_ID" \
      --display-name "$SCH_NAME" \
      --description "Forwards Azure logs from OCI Streaming to Log Analytics ($LOG_GROUP_NAME group)" \
      --source file:///tmp/azure_sch_source.json \
      --target file:///tmp/azure_sch_target.json \
      >/dev/null 2>&1 || true

  # Wait briefly, then resolve the OCID from the list API
  info "Waiting for SCH to appear..."
  attempts=0
  SCH_ID=""
  while [[ -z "$SCH_ID" || "$SCH_ID" == "null" ]] && [[ $attempts -lt 12 ]]; do
    sleep 5
    SCH_ID=$(oci sch service-connector list \
        --compartment-id "$OCI_COMPARTMENT_ID" \
        --display-name "$SCH_NAME" \
        --query 'data.items[0].id' --raw-output 2>/dev/null || true)
    ((attempts++))
  done

  if [[ -n "$SCH_ID" && "$SCH_ID" != "null" ]]; then
    ok "SCH created: ${SCH_ID:0:50}..."
  else
    warn "SCH creation may need manual setup (check IAM policies)"
    info "Required policy: Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment <name>"
    info "                 Allow any-user to use loganalytics-log-group in compartment <name>"
  fi
fi

# ── Cleanup temp files ────────────────────────────────────────
rm -f /tmp/azure_sch_source.json /tmp/azure_sch_target.json 2>/dev/null

# ── Derive message endpoint from Kafka bootstrap ─────────────
MSG_ENDPOINT=""
if [[ "$KAFKA_ENDPOINT" != "N/A" ]]; then
  MSG_ENDPOINT="https://$(echo "$KAFKA_ENDPOINT" | cut -d: -f1)"
fi

# ── Persist all OCIDs to .env.local ───────────────────────────
info "Persisting resource IDs to $ENV_PATH..."
update_env_var "OCI_STREAM_POOL_ID" "$POOL_ID" "$ENV_PATH"
update_env_var "OCI_STREAM_POOL_NAME" "$STREAM_POOL_NAME" "$ENV_PATH"
update_env_var "OCI_STREAM_OCID" "$STREAM_ID" "$ENV_PATH"
update_env_var "OCI_STREAM_NAME" "$STREAM_NAME" "$ENV_PATH"
update_env_var "OCI_LOG_GROUP_ID" "$LOG_GROUP_ID" "$ENV_PATH"
update_env_var "OCI_LOG_GROUP_NAME" "$LOG_GROUP_NAME" "$ENV_PATH"
update_env_var "OCI_LOG_ANALYTICS_NAMESPACE" "$NAMESPACE" "$ENV_PATH"
update_env_var "OCI_COMPARTMENT_ID" "$OCI_COMPARTMENT_ID" "$ENV_PATH"
if [[ -n "$SCH_ID" && "$SCH_ID" != "null" ]]; then
  update_env_var "OCI_SCH_ID" "$SCH_ID" "$ENV_PATH"
fi
update_env_var "OCI_SCH_NAME" "$SCH_NAME" "$ENV_PATH"
if [[ -n "$MSG_ENDPOINT" ]]; then
  update_env_var "OCI_MESSAGE_ENDPOINT" "$MSG_ENDPOINT" "$ENV_PATH"
fi
ok "Resource IDs saved to .env.local"

echo ""
echo "============================================================"
echo "  OCI Log Analytics Setup Complete"
echo "============================================================"
echo ""
echo "Persisted to .env.local:"
echo "  OCI_STREAM_OCID=$STREAM_ID"
echo "  OCI_STREAM_POOL_ID=$POOL_ID"
if [[ -n "$MSG_ENDPOINT" ]]; then
  echo "  OCI_MESSAGE_ENDPOINT=$MSG_ENDPOINT"
fi
echo "  OCI_LOG_ANALYTICS_NAMESPACE=$NAMESPACE"
echo "  OCI_COMPARTMENT_ID=$OCI_COMPARTMENT_ID"
echo "  OCI_LOG_GROUP_NAME=$LOG_GROUP_NAME"
echo "  OCI_LOG_GROUP_ID=$LOG_GROUP_ID"
echo "  OCI_SCH_NAME=$SCH_NAME"
if [[ -n "$SCH_ID" && "$SCH_ID" != "null" ]]; then
  echo "  OCI_SCH_ID=$SCH_ID"
fi
echo ""
echo "Pipeline:"
echo "  Azure Event Hub (EntraID Audit Logs)"
echo "    → Azure Function (Event Hub trigger + Cloud Provider enrichment)"
echo "    → OCI Stream: $STREAM_NAME"
echo "    → SCH: $SCH_NAME"
echo "    → Log Analytics: $LOG_GROUP_NAME (source: $SOURCE_NAME)"
echo ""
echo "Query example:"
echo "  'Cloud Provider' = 'Azure' | stats count by 'Azure Operation'"
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/drain_eventhub_to_oci.sh --from-beginning"
echo "  2. Verify in OCI Log Analytics Log Explorer"
echo ""
