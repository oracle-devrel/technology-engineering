#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# teardown_azurelogs2oci.sh – Delete Azure + OCI resources
#   created by the azurelogs2oci pipeline.
#
# Usage:
#   ./scripts/teardown_azurelogs2oci.sh [flags]
#
# Flags:
#   --all              Both Azure + OCI (default)
#   --azure-only       Azure resources only
#   --oci-only         OCI resources only
#   --dry-run          Show what would be deleted
#   --force            Skip confirmation prompts
#   --purge-la         Delete Log Analytics content (source, parser, fields)
#                      By default, LA content is kept to preserve historical logs
#   --keep-rg          Delete Azure resources but keep the Resource Group
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="$REPO_ROOT/.env.local"

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=discover_resources.sh
source "$SCRIPT_DIR/discover_resources.sh"

# ── Parse flags ──────────────────────────────────────────────
SCOPE="all"        # all | azure | oci
DRY_RUN=false
FORCE=false
PURGE_LA=false     # By default, keep LA content (source, parser, fields)
KEEP_RG=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)          SCOPE="all"; shift ;;
    --azure-only)   SCOPE="azure"; shift ;;
    --oci-only)     SCOPE="oci"; shift ;;
    --dry-run)      DRY_RUN=true; shift ;;
    --force)        FORCE=true; shift ;;
    --purge-la)     PURGE_LA=true; shift ;;
    --keep-rg)      KEEP_RG=true; shift ;;
    --help|-h)
      cat <<EOF
Usage: $0 [flags]

Flags:
  --all              Both Azure + OCI (default)
  --azure-only       Azure resources only
  --oci-only         OCI resources only
  --dry-run          Show what would be deleted
  --force            Skip confirmation prompts
  --purge-la         Delete Log Analytics content (source, parser, fields)
                     By default, LA content is kept to preserve historical logs
  --keep-rg          Delete Azure resources but keep the Resource Group
EOF
      exit 0
      ;;
    *) err "Unknown flag: $1"; exit 1 ;;
  esac
done

# ── Load .env.local ──────────────────────────────────────────
load_env "$ENV_PATH"

# Resolve variables from .env.local
OCI_COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-${OCI_COMPARTMENT_OCID:-}}"
OCI_REGION="${region:-${OCI_REGION:-}}"
OCI_STREAM_POOL_NAME="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
OCI_STREAM_NAME="${OCI_STREAM_NAME:-azure-inbound-stream}"
OCI_LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-AzureLogs}"
OCI_SCH_NAME="${OCI_SCH_NAME:-Azure-Stream-to-LogAnalytics}"
OCI_LOG_ANALYTICS_NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"
AZ_RG="${AZ_RG:-${EVENTHUB_RG:-azurelogs2oci-rg}}"
AZ_STORAGE_ACCOUNT="${AZ_STORAGE_ACCOUNT:-}"
AZ_FUNCTION_APP="${AZ_FUNCTION_APP:-}"
EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-}"

# OCI auth env for teardown_oci_log_analytics.py
export OCI_USER_OCID="${user:-${OCI_USER_OCID:-}}"
export OCI_FINGERPRINT="${fingerprint:-${OCI_FINGERPRINT:-}}"
export OCI_TENANCY_OCID="${tenancy:-${OCI_TENANCY_OCID:-}}"
export OCI_KEY_CONTENT="${key_content:-${OCI_KEY_CONTENT:-}}"
export OCI_KEY_FILE="${KEY_FILE:-${OCI_KEY_FILE:-}}"
export OCI_KEY_PASSPHRASE="${pass_phrase:-${OCI_KEY_PASSPHRASE:-}}"
export OCI_REGION

MODE=""
[[ "$DRY_RUN" == true ]] && MODE="[DRY RUN] "

echo ""
echo "============================================================"
echo "  ${MODE}azurelogs2oci Teardown"
echo "============================================================"
echo "  Scope:       $SCOPE"
echo "  Dry run:     $DRY_RUN"
echo "  Purge LA:    $PURGE_LA"
echo "  Keep RG:     $KEEP_RG"
echo "============================================================"
echo ""

# ── Discover existing resources ──────────────────────────────
if [[ "$SCOPE" == "all" || "$SCOPE" == "oci" ]]; then
  discover_oci_resources || true
fi
if [[ "$SCOPE" == "all" || "$SCOPE" == "azure" ]]; then
  discover_azure_resources || true
fi

show_discovery_summary "$SCOPE"

# ── Confirmation ─────────────────────────────────────────────
if [[ "$FORCE" != true && "$DRY_RUN" != true ]]; then
  echo ""
  warn "This will PERMANENTLY DELETE the resources listed above."
  if ! prompt_yn "Continue with teardown?" "n"; then
    info "Aborted."
    exit 0
  fi
  echo ""
fi

# ── Helper: safe delete with 404 handling ────────────────────
# Usage: safe_delete "label" command args...
safe_delete() {
  local label="$1"; shift
  if [[ "$DRY_RUN" == true ]]; then
    info "${MODE}Would delete: $label"
    return 0
  fi
  info "Deleting: $label"
  set +e
  local output
  output=$("$@" 2>&1)
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    ok "Deleted: $label"
  elif echo "$output" | grep -qi "404\|NotFound\|not found\|does not exist\|NoSuchResource"; then
    ok "Already deleted: $label"
  else
    warn "Failed to delete $label (rc=$rc): $(echo "$output" | head -3)"
  fi
}

# ── OCI Teardown ─────────────────────────────────────────────
teardown_oci() {
  info "Starting OCI teardown..."
  echo ""

  local compartment="$OCI_COMPARTMENT_ID"
  if [[ -z "$compartment" ]]; then
    warn "OCI_COMPARTMENT_ID not set; cannot tear down OCI resources."
    return 1
  fi

  # 1. Service Connector Hub
  echo "  1/5  Service Connector Hub"
  if [[ -n "$DISC_OCI_SCH_ID" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      info "${MODE}Would delete SCH: ${DISC_OCI_SCH_ID:0:50}..."
    else
      # Deactivate first if needed (only ACTIVE or INACTIVE can be deleted)
      local sch_state
      sch_state=$(oci sch service-connector get \
          --service-connector-id "$DISC_OCI_SCH_ID" \
          --query 'data."lifecycle-state"' --raw-output 2>/dev/null || echo "UNKNOWN")

      if [[ "$sch_state" == "ACTIVE" ]]; then
        info "Deactivating SCH before deletion..."
        oci sch service-connector deactivate \
            --service-connector-id "$DISC_OCI_SCH_ID" \
            --wait-for-state SUCCEEDED \
            --max-wait-seconds 120 >/dev/null 2>&1 || true
      fi

      safe_delete "SCH: $DISC_OCI_SCH_NAME" \
        oci sch service-connector delete \
          --service-connector-id "$DISC_OCI_SCH_ID" \
          --force \
          --wait-for-state SUCCEEDED \
          --max-wait-seconds 300
    fi
    # Clear from .env.local
    [[ "$DRY_RUN" != true ]] && update_env_var "OCI_SCH_ID" "" "$ENV_PATH"
  else
    ok "SCH: not found (nothing to delete)"
  fi

  # 2. LA Source + Parser + Fields
  echo ""
  echo "  2/5  Log Analytics custom content (source, parser, fields)"
  local namespace="${DISC_OCI_NAMESPACE:-$OCI_LOG_ANALYTICS_NAMESPACE}"
  if [[ "$PURGE_LA" != true ]]; then
    info "Keeping LA content (source, parser, fields) for historical logs."
    info "Use --purge-la to delete LA content."
  elif [[ -n "$namespace" ]]; then
    export LA_NAMESPACE="$namespace"
    export OCI_COMPARTMENT_ID="$compartment"

    local py_args=()
    [[ "$DRY_RUN" == true ]] && py_args+=(--dry-run)

    python3 "$SCRIPT_DIR/teardown_oci_log_analytics.py" ${py_args[@]+"${py_args[@]}"}
  else
    warn "Log Analytics namespace unknown; skipping LA content teardown."
  fi

  # 3. Log Group
  echo ""
  echo "  3/5  Log Analytics Log Group"
  if [[ -n "$DISC_OCI_LOG_GROUP_ID" && -n "$namespace" ]]; then
    safe_delete "Log Group: $DISC_OCI_LOG_GROUP_NAME" \
      oci log-analytics log-group delete \
        --namespace-name "$namespace" \
        --log-group-id "$DISC_OCI_LOG_GROUP_ID" \
        --force
    [[ "$DRY_RUN" != true ]] && update_env_var "OCI_LOG_GROUP_ID" "" "$ENV_PATH"
  else
    ok "Log Group: not found (nothing to delete)"
  fi

  # 4. Stream
  echo ""
  echo "  4/5  Stream"
  if [[ -n "$DISC_OCI_STREAM_ID" ]]; then
    safe_delete "Stream: $DISC_OCI_STREAM_NAME" \
      oci streaming admin stream delete \
        --stream-id "$DISC_OCI_STREAM_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 120
    [[ "$DRY_RUN" != true ]] && update_env_var "OCI_STREAM_OCID" "" "$ENV_PATH"
  else
    ok "Stream: not found (nothing to delete)"
  fi

  # 5. Stream Pool
  echo ""
  echo "  5/5  Stream Pool"
  if [[ -n "$DISC_OCI_STREAM_POOL_ID" ]]; then
    safe_delete "Stream Pool: $DISC_OCI_STREAM_POOL_NAME" \
      oci streaming admin stream-pool delete \
        --stream-pool-id "$DISC_OCI_STREAM_POOL_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 120
    [[ "$DRY_RUN" != true ]] && update_env_var "OCI_STREAM_POOL_ID" "" "$ENV_PATH"
  else
    ok "Stream Pool: not found (nothing to delete)"
  fi

  echo ""
  ok "OCI teardown complete."
}

# ── Azure Teardown ───────────────────────────────────────────
teardown_azure() {
  info "Starting Azure teardown..."
  echo ""

  if ! command -v az >/dev/null 2>&1; then
    warn "az CLI not found; cannot tear down Azure resources."
    return 1
  fi

  if [[ "$DISC_AZ_RG_EXISTS" != "true" ]]; then
    ok "Resource group '$AZ_RG' does not exist (nothing to delete)."
    return 0
  fi

  if [[ "$KEEP_RG" == true ]]; then
    # Delete individual resources within the RG
    info "Deleting Azure resources individually (--keep-rg)..."

    # Function App
    if [[ "$DISC_AZ_FUNCTION_APP_EXISTS" == "true" && -n "$AZ_FUNCTION_APP" ]]; then
      safe_delete "Function App: $AZ_FUNCTION_APP" \
        az functionapp delete -g "$AZ_RG" -n "$AZ_FUNCTION_APP"
    fi

    # Storage Account
    if [[ "$DISC_AZ_STORAGE_ACCOUNT_EXISTS" == "true" && -n "$AZ_STORAGE_ACCOUNT" ]]; then
      safe_delete "Storage Account: $AZ_STORAGE_ACCOUNT" \
        az storage account delete -g "$AZ_RG" -n "$AZ_STORAGE_ACCOUNT" --yes
    fi

    # Event Hubs Namespace (cascades to all hubs)
    if [[ "$DISC_AZ_EVENTHUB_NS_EXISTS" == "true" && -n "$EVENTHUB_NAMESPACE" ]]; then
      safe_delete "Event Hubs Namespace: $EVENTHUB_NAMESPACE" \
        az eventhubs namespace delete --resource-group "$AZ_RG" --name "$EVENTHUB_NAMESPACE"
    fi

    ok "Azure resources deleted (resource group '$AZ_RG' kept)."
  else
    # Cascade delete entire resource group
    safe_delete "Resource Group: $AZ_RG (and all contained resources)" \
      az group delete -n "$AZ_RG" --yes --no-wait
    ok "Azure resource group deletion initiated (runs in background)."
  fi

  echo ""
  ok "Azure teardown complete."
}

# ── Execute teardown ─────────────────────────────────────────
if [[ "$SCOPE" == "all" || "$SCOPE" == "oci" ]]; then
  teardown_oci || true
fi

if [[ "$SCOPE" == "all" || "$SCOPE" == "azure" ]]; then
  teardown_azure || true
fi

echo ""
echo "============================================================"
echo "  ${MODE}Teardown Complete"
echo "============================================================"
if [[ "$DRY_RUN" == true ]]; then
  info "No resources were deleted (dry-run mode)."
  info "Remove --dry-run to perform actual deletion."
else
  info "All targeted resources have been deleted or deletion initiated."
  info "Run setup scripts to recreate: ./scripts/setup_oci_log_analytics.sh"
fi
echo ""
