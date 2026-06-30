#!/usr/bin/env bash
# Provision Azure resources (RG, storage, Function App) and deploy azurelogs2oci for continuous delivery to OCI Streaming.
# - Loads .env.local if present and prompts for any missing values.
# - Discovers Event Hubs and connection string via Azure CLI when possible.
# - Prefers Azure Functions Core Tools remote build for Linux-safe deployment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="$REPO_ROOT/.env.local"
FUNCTION_PATH="$REPO_ROOT/function/EventHubsNamespaceToOCIStreaming"

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=discover_resources.sh
source "$SCRIPT_DIR/discover_resources.sh"

require_cmd az
require_cmd python3
if ! command -v func >/dev/null 2>&1; then
  require_cmd zip
fi

# Verify Azure CLI is logged in
if ! az account show >/dev/null 2>&1; then
  err "Azure CLI is not logged in. Run 'az login' first."
  exit 1
fi

# Load existing env without failing on unset
load_env "$ENV_PATH"

# ── Collect basic Azure parameters ────────────────────────────
echo ""
echo "============================================================"
echo "  Azure → OCI Streaming Provisioning"
echo "============================================================"
echo ""

# Inputs with defaults
RG_DEFAULT="${AZ_RG:-${RESOURCE_GROUP:-azurelogs2oci-rg}}"
LOC_DEFAULT="${AZ_LOCATION:-${LOCATION:-westeurope}}"
SA_DEFAULT="${AZ_STORAGE_ACCOUNT:-}"
APP_DEFAULT="${AZ_FUNCTION_APP:-}"
PLAN_TYPE_DEFAULT="${PLAN_TYPE:-consumption}" # consumption | premium

EVENTHUB_RG="${EVENTHUB_RG:-$RG_DEFAULT}"
EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-}"
EVENTHUB_CONSUMER_GROUP="${EventHubConsumerGroup:-${EVENTHUB_CONSUMER_GROUP:-\$Default}}"
EVENTHUB_NAMES_CSV="${EventHubNamesCsv:-${EVENTHUB_NAME:-}}"

OCI_MESSAGE_ENDPOINT="${OCI_MESSAGE_ENDPOINT:-${MessageEndpoint:-}}"
OCI_STREAM_OCID="${OCI_STREAM_OCID:-${StreamOcid:-}}"
user="${user:-}"
key_content="${key_content:-}"
pass_phrase="${pass_phrase:-}"
fingerprint="${fingerprint:-}"
tenancy="${tenancy:-}"
region="${region:-us-ashburn-1}"

AZ_RG="$(prompt_required "Azure resource group" "${EVENTHUB_RG:-$RG_DEFAULT}")"
AZ_LOCATION="$(prompt_required "Azure location" "$LOC_DEFAULT")"
discover_azure_defaults "$AZ_RG"
EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-${DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE:-}}"
SA_DEFAULT="${SA_DEFAULT:-${DISC_AZ_SUGGESTED_STORAGE_ACCOUNT:-}}"
APP_DEFAULT="${APP_DEFAULT:-${DISC_AZ_SUGGESTED_FUNCTION_APP:-}}"
EVENTHUB_NAMESPACE="$(prompt_required "Event Hubs namespace" "${EVENTHUB_NAMESPACE:-<namespace>}")"
PLAN_TYPE="$(prompt_required "Function plan type (consumption/premium)" "$PLAN_TYPE_DEFAULT")"

# ── Discover existing Azure resources ─────────────────────────
discover_azure_resources || true

AZURE_MODE="create"  # create | reuse | destroy

AZURE_FOUND=0
[[ "$DISC_AZ_RG_EXISTS" == "true" ]] && ((AZURE_FOUND++)) || true
[[ "$DISC_AZ_EVENTHUB_NS_EXISTS" == "true" ]] && ((AZURE_FOUND++)) || true
[[ "$DISC_AZ_FUNCTION_APP_EXISTS" == "true" ]] && ((AZURE_FOUND++)) || true

if [[ $AZURE_FOUND -gt 0 ]]; then
  show_discovery_summary "azure"

  echo "Existing Azure resources found ($AZURE_FOUND)."
  echo ""
  echo "  [1] Use existing resources (reuse what's found)"
  echo "  [2] Create new resources (prompted for new names)"
  echo "  [3] Destroy existing and recreate"
  echo ""
  read -r -p "Choose [1/2/3] (default: 1): " az_choice
  az_choice="${az_choice:-1}"

  case "$az_choice" in
    1) AZURE_MODE="reuse" ;;
    2) AZURE_MODE="create" ;;
    3) AZURE_MODE="destroy" ;;
    *) warn "Invalid choice; defaulting to [1] reuse."; AZURE_MODE="reuse" ;;
  esac
fi

# Handle destroy mode
if [[ "$AZURE_MODE" == "destroy" ]]; then
  warn "Destroying existing Azure resources..."
  if [[ "$DISC_AZ_RG_EXISTS" == "true" ]]; then
    info "Deleting resource group $AZ_RG (cascades to all resources)..."
    az group delete -n "$AZ_RG" --yes 2>/dev/null || true
    ok "Resource group deleted"
  fi
  AZURE_MODE="create"
fi

# Ensure resource group exists before any downstream Azure operations
info "Ensuring resource group exists..."
az group create -n "$AZ_RG" -l "$AZ_LOCATION" >/dev/null

if [[ "$AZURE_MODE" == "reuse" ]]; then
  info "Reusing existing Azure Event Hub resources."
fi

info "Fetching Event Hubs in namespace '$EVENTHUB_NAMESPACE'..."
HUBS=()
set +e
while IFS= read -r line; do
  [[ -n "$line" ]] && HUBS+=("$line")
done < <(az eventhubs eventhub list --resource-group "$AZ_RG" --namespace-name "$EVENTHUB_NAMESPACE" --query "[].name" -o tsv 2>/dev/null)
set -e

if [[ ${#HUBS[@]} -gt 0 ]]; then
  info "Available Event Hubs:"
  i=1
  for h in "${HUBS[@]}"; do
    echo "  [$i] $h"
    ((i++))
  done
  read -r -p "Enter comma-separated numbers or names to include (leave blank to keep current '${EVENTHUB_NAMES_CSV:-<none>}'): " selection
  if [[ -n "$selection" ]]; then
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

EVENTHUB_NAMES_CSV="$(prompt_required "Comma-separated Event Hub names" "${EVENTHUB_NAMES_CSV:-insights-activity-logs}")"
EVENTHUB_CONSUMER_GROUP="$(prompt_required "Consumer group for function (leave \$Default if unsure)" "$EVENTHUB_CONSUMER_GROUP")"
PRIMARY_EVENTHUB="$(echo "$EVENTHUB_NAMES_CSV" | cut -d',' -f1 | tr -d '[:space:]')"

# Ensure Event Hub namespace and hubs exist (creates if missing, skips if reusing)
if [[ "$AZURE_MODE" != "reuse" ]]; then
  info "Ensuring Event Hubs namespace exists..."
  if ! az eventhubs namespace show --resource-group "$AZ_RG" --name "$EVENTHUB_NAMESPACE" >/dev/null 2>&1; then
    az eventhubs namespace create --resource-group "$AZ_RG" --name "$EVENTHUB_NAMESPACE" --location "$AZ_LOCATION" >/dev/null
    ok "Created Event Hubs namespace $EVENTHUB_NAMESPACE"
  else
    ok "Namespace $EVENTHUB_NAMESPACE exists"
  fi

  IFS=',' read -r -a HUB_LIST <<<"$EVENTHUB_NAMES_CSV"
  for hub in "${HUB_LIST[@]}"; do
    hub_trim="${hub//[[:space:]]/}"
    [[ -z "$hub_trim" ]] && continue
    if ! az eventhubs eventhub show --resource-group "$AZ_RG" --namespace-name "$EVENTHUB_NAMESPACE" --name "$hub_trim" >/dev/null 2>&1; then
      az eventhubs eventhub create --resource-group "$AZ_RG" --namespace-name "$EVENTHUB_NAMESPACE" --name "$hub_trim" >/dev/null
      ok "Created Event Hub $hub_trim"
    else
      ok "Event Hub $hub_trim exists"
    fi
    if [[ "$EVENTHUB_CONSUMER_GROUP" != "\$Default" ]]; then
      if ! az eventhubs eventhub consumer-group show --resource-group "$AZ_RG" --namespace-name "$EVENTHUB_NAMESPACE" --eventhub-name "$hub_trim" --name "$EVENTHUB_CONSUMER_GROUP" >/dev/null 2>&1; then
        az eventhubs eventhub consumer-group create --resource-group "$AZ_RG" --namespace-name "$EVENTHUB_NAMESPACE" --eventhub-name "$hub_trim" --name "$EVENTHUB_CONSUMER_GROUP" >/dev/null
        ok "Created consumer group $EVENTHUB_CONSUMER_GROUP on $hub_trim"
      fi
    fi
  done
else
  ok "Using existing Event Hub resources (namespace: $EVENTHUB_NAMESPACE)"
fi

# Resolve connection string with retries
info "Resolving Event Hubs connection string from Azure..."
EventHubsConnectionString=""
for attempt in 1 2 3; do
  set +e
  EventHubsConnectionString="$(az eventhubs namespace authorization-rule keys list \
    --resource-group "$AZ_RG" \
    --namespace-name "$EVENTHUB_NAMESPACE" \
    --name "RootManageSharedAccessKey" \
    --query primaryConnectionString -o tsv 2>/dev/null)"
  rc=$?
  set -e
  [[ $rc -eq 0 && -n "$EventHubsConnectionString" ]] && break
  warn "Attempt $attempt to resolve connection string failed. Retrying in 5s..."
  sleep 5
done

if [[ -z "$EventHubsConnectionString" ]]; then
  warn "Could not auto-resolve connection string."
  EventHubsConnectionString="$(prompt_required "EventHubsConnectionString" "${EventHubsConnectionString:-Endpoint=sb://...}")"
else
  ok "Resolved connection string"
fi

# OCI inputs
discover_oci_stream_defaults
if [[ "$DISC_OCI_STREAM_OCID_IS_POOL" == "true" ]]; then
  warn "Configured OCI_STREAM_OCID points to a Stream Pool. The Function requires a Stream OCID."
  OCI_STREAM_OCID=""
fi
OCI_STREAM_OCID="${OCI_STREAM_OCID:-${DISC_OCI_SUGGESTED_STREAM_ID:-}}"
OCI_MESSAGE_ENDPOINT="${OCI_MESSAGE_ENDPOINT:-${DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT:-}}"

OCI_STREAM_OCID="$(prompt_required "OCI stream OCID (not stream pool)" "${OCI_STREAM_OCID:-ocid1.stream.oc1..xxxx}")"
if is_oci_stream_pool_ocid "$OCI_STREAM_OCID"; then
  err "OCI_STREAM_OCID points to a Stream Pool. Use the Stream OCID (ocid1.stream...)."
  exit 1
fi
OCI_MESSAGE_ENDPOINT="$(prompt_required "OCI message endpoint" "${OCI_MESSAGE_ENDPOINT:-https://cell-1.streaming.<region>.oci.oraclecloud.com}")"
user="$(prompt_required "OCI user OCID" "${user:-ocid1.user.oc1..example}")"
fingerprint="$(prompt_required "OCI API key fingerprint" "${fingerprint:-<fingerprint>}")"
tenancy="$(prompt_required "OCI tenancy OCID" "${tenancy:-ocid1.tenancy.oc1..example}")"
region="$(prompt_required "OCI region" "$region")"

if [[ -z "$key_content" || "$key_content" == "-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----" ]]; then
  read -r -p "Path to OCI private key file (leave blank to paste): " key_path
  if [[ -z "$key_path" && -n "${KEY_FILE:-}" && -f "${KEY_FILE:-}" ]]; then
    key_path="$KEY_FILE"
  fi
  if [[ -n "$key_path" && -f "$key_path" ]]; then
    KEY_FILE="$key_path"
    key_content="$(cat "$key_path")"
  else
    key_content="$(prompt_secret "Paste OCI private key content (will be stored in Function App settings)")"
  fi
fi
# Normalize key_content (strip CR and trailing spaces)
key_content="$(printf '%s' "$key_content" | tr -d '\r')"
pass_phrase="$(prompt_default "OCI key pass phrase (blank if none)" "${pass_phrase:-}")"

# Azure names
if [[ -z "${SA_DEFAULT}" ]]; then
  RAND=$(python3 - <<'PY'
import random,string
print('logs' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)))
PY
)
  AZ_STORAGE_ACCOUNT="$RAND"
else
  AZ_STORAGE_ACCOUNT="$SA_DEFAULT"
fi
if [[ -z "${APP_DEFAULT}" ]]; then
  RAND_APP=$(python3 - <<'PY'
import random,string
print('azurelogs2oci-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
PY
)
  AZ_FUNCTION_APP="$RAND_APP"
else
  AZ_FUNCTION_APP="$APP_DEFAULT"
fi
AZ_PLAN="${AZ_FUNCTION_APP}-plan"

AZ_STORAGE_ACCOUNT="$(prompt_default "Azure storage account name (must be globally unique)" "$AZ_STORAGE_ACCOUNT")"
AZ_FUNCTION_APP="$(prompt_default "Azure Function App name" "$AZ_FUNCTION_APP")"
AZ_PLAN="$(prompt_default "Azure App Service plan name (used for premium)" "$AZ_PLAN")"

info "Creating resource group (if needed)..."
az group create -n "$AZ_RG" -l "$AZ_LOCATION" >/dev/null

info "Creating storage account (if needed)..."
az storage account create -g "$AZ_RG" -n "$AZ_STORAGE_ACCOUNT" -l "$AZ_LOCATION" --sku Standard_LRS >/dev/null

info "Creating Function App (if needed)..."
if ! az functionapp show -g "$AZ_RG" -n "$AZ_FUNCTION_APP" >/dev/null 2>&1; then
  if [[ "$PLAN_TYPE" == "premium" ]]; then
    info "Creating premium plan $AZ_PLAN (EP1)..."
    az functionapp plan create \
      -g "$AZ_RG" \
      -n "$AZ_PLAN" \
      --location "$AZ_LOCATION" \
      --number-of-workers 1 \
      --sku EP1 \
      --is-linux >/dev/null
    az functionapp create \
      -g "$AZ_RG" \
      -n "$AZ_FUNCTION_APP" \
      --plan "$AZ_PLAN" \
      --runtime python \
      --runtime-version 3.11 \
      --functions-version 4 \
      --os-type linux \
      --storage-account "$AZ_STORAGE_ACCOUNT" >/dev/null
  else
    az functionapp create \
      -g "$AZ_RG" \
      -n "$AZ_FUNCTION_APP" \
      --consumption-plan-location "$AZ_LOCATION" \
      --runtime python \
      --runtime-version 3.11 \
      --functions-version 4 \
      --os-type linux \
      --storage-account "$AZ_STORAGE_ACCOUNT" >/dev/null
  fi
else
  warn "Function App $AZ_FUNCTION_APP already exists; will reuse."
fi

# Flatten key_content to single line for app settings
KEY_ONELINE="$(printf '%s' "$key_content" | tr -d '\r' | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g')"

info "Configuring app settings..."
az functionapp config appsettings set -g "$AZ_RG" -n "$AZ_FUNCTION_APP" --settings \
  EventHubsConnectionString="$EventHubsConnectionString" \
  EventHubConsumerGroup="$EVENTHUB_CONSUMER_GROUP" \
  EventHubName="$PRIMARY_EVENTHUB" \
  EventHubNamesCsv="$EVENTHUB_NAMES_CSV" \
  MessageEndpoint="$OCI_MESSAGE_ENDPOINT" \
  StreamOcid="$OCI_STREAM_OCID" \
  user="$user" \
  key_content="$KEY_ONELINE" \
  pass_phrase="$pass_phrase" \
  fingerprint="$fingerprint" \
  tenancy="$tenancy" \
  region="$region" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  ENABLE_ORYX_BUILD="true" >/dev/null

pushd "$FUNCTION_PATH" >/dev/null
# Remove any local .python_packages to avoid bundling platform-specific wheels
rm -rf .python_packages
if command -v func >/dev/null 2>&1; then
  info "Deploying with Azure Functions Core Tools remote build..."
  func azure functionapp publish "$AZ_FUNCTION_APP" --python --build remote --force
else
  warn "Functions Core Tools (func) not found; falling back to Azure CLI zip deploy with remote build."
  warn "If deployment indexing fails on Azure Linux, install Functions Core Tools and rerun."
  TMP_DIR="$(mktemp -d)"
  TMP_ZIP="$TMP_DIR/azurelogs2oci.zip"
  zip -qry "$TMP_ZIP" . -x ".venv/*" "__pycache__/*" "*/__pycache__/*" "*.pyc" ".python_packages/*" ".funcignore" "local.settings.json"
  info "Deploying zip to Function App with remote build (Oryx)..."
  az functionapp deployment source config-zip -g "$AZ_RG" -n "$AZ_FUNCTION_APP" --src "$TMP_ZIP" --build-remote true >/dev/null
fi
popd >/dev/null

info "Verifying deployed functions are indexed..."
DEPLOYED_FUNCTIONS=""
for attempt in 1 2 3 4 5 6; do
  set +e
  DEPLOYED_FUNCTIONS="$(az functionapp function list -g "$AZ_RG" -n "$AZ_FUNCTION_APP" --query "[].name" -o tsv 2>/dev/null)"
  rc=$?
  set -e
  if [[ $rc -eq 0 && -n "$DEPLOYED_FUNCTIONS" ]]; then
    break
  fi
  sleep 10
done
if [[ -n "$DEPLOYED_FUNCTIONS" ]]; then
  ok "Function indexing complete: $(printf '%s' "$DEPLOYED_FUNCTIONS" | paste -sd, -)"
else
  warn "Function indexing could not be confirmed yet. Check 'az functionapp function list -g $AZ_RG -n $AZ_FUNCTION_APP'."
fi

# Persist latest values to .env.local for reuse
info "Updating $ENV_PATH with latest values..."
cat > "$ENV_PATH" <<EOF
# Generated by provision_azure_to_oci.sh
EventHubsConnectionString='$EventHubsConnectionString'
EventHubConsumerGroup='$EVENTHUB_CONSUMER_GROUP'
EventHubName='$PRIMARY_EVENTHUB'
EventHubNamesCsv='$EVENTHUB_NAMES_CSV'
EVENTHUB_RG='$AZ_RG'
EVENTHUB_NAMESPACE='$EVENTHUB_NAMESPACE'

OCI_MESSAGE_ENDPOINT='$OCI_MESSAGE_ENDPOINT'
OCI_STREAM_OCID='$OCI_STREAM_OCID'

user='$user'
key_content='$key_content'
KEY_FILE='${KEY_FILE:-}'
pass_phrase='$pass_phrase'
fingerprint='$fingerprint'
tenancy='$tenancy'
region='$region'

# OCI identifiers (used by setup_oci_log_analytics.sh)
OCI_USER_OCID='$user'
OCI_FINGERPRINT='$fingerprint'
OCI_TENANCY_OCID='$tenancy'
OCI_REGION='$region'
OCI_KEY_CONTENT='$key_content'
OCI_COMPARTMENT_ID='${OCI_COMPARTMENT_ID:-${OCI_COMPARTMENT_OCID:-}}'
OCI_LOG_ANALYTICS_NAMESPACE='${OCI_LOG_ANALYTICS_NAMESPACE:-}'
OCI_LOG_GROUP_NAME='${OCI_LOG_GROUP_NAME:-AzureLogs}'
OCI_SCH_NAME='${OCI_SCH_NAME:-Azure-Stream-to-LogAnalytics}'
OCI_STREAM_POOL_ID='${OCI_STREAM_POOL_ID:-}'
OCI_STREAM_POOL_NAME='${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}'
OCI_LOG_GROUP_ID='${OCI_LOG_GROUP_ID:-}'
OCI_SCH_ID='${OCI_SCH_ID:-}'

# Azure app + storage
AZ_RG='$AZ_RG'
AZ_LOCATION='$AZ_LOCATION'
AZ_STORAGE_ACCOUNT='$AZ_STORAGE_ACCOUNT'
AZ_FUNCTION_APP='$AZ_FUNCTION_APP'
AZ_PLAN='$AZ_PLAN'

# Optional script tuning
COUNT='${COUNT:-0}'
INACTIVITY_TIMEOUT='${INACTIVITY_TIMEOUT:-30}'
EOF

ok "Deployment complete."
info "Function App: $AZ_FUNCTION_APP (RG: $AZ_RG, Location: $AZ_LOCATION)"
info "Event Hubs namespace: $EVENTHUB_NAMESPACE | Hubs: $EVENTHUB_NAMES_CSV | Consumer group: $EVENTHUB_CONSUMER_GROUP"
info "OCI stream: $OCI_STREAM_OCID @ $OCI_MESSAGE_ENDPOINT"

# ── Optional: OCI Log Analytics end-to-end setup ─────────────
echo ""
echo "============================================================"
echo "  OCI Log Analytics End-to-End Setup"
echo "============================================================"
echo ""
info "The Azure Function is now deployed and forwarding events to OCI Streaming."
info "To complete the pipeline to OCI Log Analytics, run setup_oci_log_analytics.sh."
echo ""

if prompt_yn "Set up OCI Log Analytics now? (creates Log Group, parser, source, SCH)" "y"; then
  if [[ -z "${OCI_COMPARTMENT_ID:-}" ]]; then
    OCI_COMPARTMENT_ID="$(prompt_required "OCI compartment OCID (required for Log Analytics)" "")"
    export OCI_COMPARTMENT_ID
    # Update .env.local with compartment
    update_env_var "OCI_COMPARTMENT_ID" "$OCI_COMPARTMENT_ID" "$ENV_PATH"
  fi
  export OCI_REGION="$region"
  export OCI_USER_OCID="$user"
  export OCI_FINGERPRINT="$fingerprint"
  export OCI_TENANCY_OCID="$tenancy"
  export OCI_KEY_CONTENT="$key_content"
  export OCI_KEY_PASSPHRASE="${pass_phrase:-}"

  info "Launching OCI Log Analytics setup..."
  bash "$SCRIPT_DIR/setup_oci_log_analytics.sh"
else
  info "Skipping Log Analytics setup. You can run it later:"
  info "  ./scripts/setup_oci_log_analytics.sh"
fi

echo ""
info "Next: tail logs with 'az webapp log tail -g $AZ_RG -n $AZ_FUNCTION_APP'"
info "       or with Functions Core Tools: 'func azure functionapp logstream $AZ_FUNCTION_APP --resource-group $AZ_RG' (not supported on Linux Consumption; use premium plan or Application Insights Live Metrics)"
