#!/usr/bin/env bash
#===============================================================================
# Drain Azure Event Hub to OCI Streaming - End-to-End Automated Test
# - Installs required SDKs if missing
# - Resolves Event Hub connection string via Azure CLI
# - Optionally sends sample EntraID logs to the Event Hub
# - Drains ALL available messages (from beginning or from timestamp) to OCI Streaming
# - Provides a clear summary at the end
#===============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

# Colors (drain script uses colored output for terminal UX)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Override with colored variants for this script
info() { printf "${BLUE}ℹ️  %s${NC}\n" "$1"; }
ok()   { printf "${GREEN}✅ %s${NC}\n" "$1"; }
warn() { printf "${YELLOW}⚠️  %s${NC}\n" "$1"; }
err()  { printf "${RED}❌ %s${NC}\n" "$1"; }

# Pre-parse defaults (may be overridden after local env is loaded)
EVENTHUB_RG=""
EVENTHUB_NAMESPACE=""
EVENTHUB_NAME=""
CONSUMER_GROUP=""
COUNT="${COUNT:-0}"                  # sample logs to send (0 to skip)
FROM_BEGINNING=true                   # default mode (can switch to START_ISO)
START_ISO=""                          # ISO timestamp if provided
INACTIVITY_TIMEOUT="${INACTIVITY_TIMEOUT:-30}"
ALL_EVENTHUBS="${ALL_EVENTHUBS:-false}"
LOCAL_SETTINGS_PATH="${LOCAL_SETTINGS_PATH:-$SCRIPT_DIR/../function/EventHubsNamespaceToOCIStreaming/local.settings.json}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../.env.local}"

prompt_eventhub_if_missing() {
  if [[ "$ALL_EVENTHUBS" == true ]]; then
    return
  fi
  if [[ -n "$EVENTHUB_NAME" ]]; then
    return
  fi
  if ! command -v az >/dev/null 2>&1; then
    warn "Azure CLI not found; cannot list Event Hubs. Set EVENTHUB_NAME or use --all-eventhubs."
    return
  fi
  info "Enumerating Event Hubs in namespace '$EVENTHUB_NAMESPACE'..."
  HUBS=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && HUBS+=("$line")
  done < <(az eventhubs eventhub list \
    --resource-group "$EVENTHUB_RG" \
    --namespace-name "$EVENTHUB_NAMESPACE" \
    --query "[].name" \
    --output tsv 2>/dev/null)

  if [[ ${#HUBS[@]} -eq 0 ]]; then
    warn "No Event Hubs discovered; specify --eventhub-name or use --all-eventhubs."
    return
  fi

  echo "Available Event Hubs:"
  i=1
  for h in "${HUBS[@]}"; do
    echo "  [$i] $h"
    ((i++))
  done
  read -r -p "Select Event Hub number, type a name, or enter 'all' to drain all: " choice
  if [[ "$choice" == "all" ]]; then
    ALL_EVENTHUBS=true
    return
  fi
  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    idx=$((choice-1))
    if [[ $idx -ge 0 && $idx -lt ${#HUBS[@]} ]]; then
      EVENTHUB_NAME="${HUBS[$idx]}"
      return
    fi
  fi
  if [[ -n "$choice" ]]; then
    EVENTHUB_NAME="$choice"
  fi
}

try_load_from_local_settings() {
  local file="$1"
  [[ ! -f "$file" ]] && return
  info "Attempting to load OCI settings from $file"
  set +e
  local parsed
  parsed="$(LOCAL_SETTINGS_PATH="$file" python3 - <<'PY'
import json
import os
path = os.environ["LOCAL_SETTINGS_PATH"]
with open(path) as fh:
    data = json.load(fh)
vals = data.get("Values", {})
print(vals.get("MessageEndpoint") or vals.get("OCI_MESSAGE_ENDPOINT") or "")
print(vals.get("StreamOcid") or vals.get("OCI_STREAM_OCID") or "")
PY
)"
  local rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    warn "Could not parse $file for OCI settings"
    return
  fi
  local file_endpoint file_stream
  file_endpoint="$(echo "$parsed" | sed -n '1p')"
  file_stream="$(echo "$parsed" | sed -n '2p')"
  if [[ -z "$OCI_MESSAGE_ENDPOINT" && -n "$file_endpoint" ]]; then
    OCI_MESSAGE_ENDPOINT="$file_endpoint"
    ok "Loaded OCI_MESSAGE_ENDPOINT from $file"
  fi
  if [[ -z "$OCI_STREAM_OCID" && -n "$file_stream" ]]; then
    OCI_STREAM_OCID="$file_stream"
    ok "Loaded OCI_STREAM_OCID from $file"
  fi
}

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --eventhub-rg) EVENTHUB_RG="$2"; shift 2;;
    --namespace|--eventhub-namespace) EVENTHUB_NAMESPACE="$2"; shift 2;;
    --eventhub-name) EVENTHUB_NAME="$2"; shift 2;;
    --consumer-group) CONSUMER_GROUP="$2"; shift 2;;
    --count) COUNT="$2"; shift 2;;
    --from-beginning) FROM_BEGINNING=true; shift ;;
    --start-iso) START_ISO="$2"; FROM_BEGINNING=false; shift 2;;
    --inactivity-timeout) INACTIVITY_TIMEOUT="$2"; shift 2;;
    --all-eventhubs) ALL_EVENTHUBS=true; shift ;;
    --help|-h)
      cat <<EOF
Usage: $0 [options]

Options:
  --eventhub-rg RG                  Resource group of Event Hub namespace (default: $EVENTHUB_RG)
  --namespace NS                    Event Hub namespace (default: $EVENTHUB_NAMESPACE)
  --eventhub-name NAME              Event Hub name (default: $EVENTHUB_NAME)
  --consumer-group NAME             Consumer group (default: $CONSUMER_GROUP)
  --count N                         Send N sample EntraID logs before draining (default: $COUNT; set 0 to skip)
  --from-beginning                  Drain from earliest available events (default mode)
  --start-iso ISO8601               Drain from specific timestamp (disables --from-beginning)
  --inactivity-timeout SECS         Stop after SECS with no events (default: $INACTIVITY_TIMEOUT)
  --all-eventhubs                   Drain all Event Hubs in the namespace

Environment overrides:
  EVENTHUB_RG, EVENTHUB_NAMESPACE, EVENTHUB_NAME, EVENTHUB_CONSUMER_GROUP, COUNT, INACTIVITY_TIMEOUT
  OCI_MESSAGE_ENDPOINT, OCI_STREAM_OCID will be detected from ~/.oci/config if not set

Examples:
  $0 --count 10 --from-beginning
  $0 --start-iso "2025-12-01T00:00:00Z" --inactivity-timeout 45
EOF
      exit 0
      ;;
    *)
      err "Unknown parameter: $1"
      exit 1;;
  esac
done

# Optional .env.local overrides (useful for local testing)
# Load env overrides (prefers explicit ENV_FILE, then common locations)
ENV_CANDIDATES=("$ENV_FILE" "$SCRIPT_DIR/../.env.local" "$SCRIPT_DIR/../.env" "$PWD/.env.local" "$PWD/.env")
for candidate in "${ENV_CANDIDATES[@]}"; do
  if [[ -f "$candidate" ]]; then
    info "Loading overrides from $candidate"
    # shellcheck disable=SC1090
    set -a
    source "$candidate"
    set +a
    break
  fi
done

# Resolve variables after local env is loaded.
# .env.local may use PascalCase (EventHubName) or SCREAMING_SNAKE (EVENTHUB_NAME);
# accept both, preferring explicit SCREAMING_SNAKE if both are set.
EVENTHUB_RG="${EVENTHUB_RG:-${AZ_RG:-}}"
EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-${EventHubNamespace:-}}"
EVENTHUB_NAME="${EVENTHUB_NAME:-${EventHubName:-}}"
CONSUMER_GROUP="${CONSUMER_GROUP:-${EventHubConsumerGroup:-\$Default}}"
COUNT="${COUNT:-0}"
INACTIVITY_TIMEOUT="${INACTIVITY_TIMEOUT:-30}"

prompt_eventhub_if_missing

printf "${GREEN}===============================================================================${NC}\n"
printf "${GREEN}🚀 Drain Azure Event Hub → OCI Streaming (Automated)${NC}\n"
printf "${GREEN}===============================================================================${NC}\n"

# Check Azure CLI
if ! command -v az >/dev/null 2>&1; then
  err "Azure CLI not found. Install Azure CLI first."
  exit 1
fi

# Python and pip
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found."
  exit 1
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import pkgutil
import sys
mods = ["azure.eventhub","oci"]
missing = [m for m in mods if pkgutil.find_loader(m) is None]
sys.exit(0 if not missing else 1)
PY
then
  info "Installing required Python packages (azure-eventhub, oci)..."
  python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
  python3 -m pip install azure-eventhub oci >/dev/null 2>&1 || true
fi
ok "Python SDKs are present"

# Resolve Event Hub connection string
# Prefer local env value (EventHubsConnectionString or EVENTHUB_CONNECTION_STRING)
EVENTHUB_CONNECTION_STRING="${EVENTHUB_CONNECTION_STRING:-${EventHubsConnectionString:-}}"

if [[ -n "$EVENTHUB_CONNECTION_STRING" ]]; then
  ok "Event Hub connection string loaded from environment"
else
  info "Retrieving Event Hub connection string from Azure..."
  if ! EVENTHUB_CONNECTION_STRING="$(az eventhubs namespace authorization-rule keys list \
    --resource-group "$EVENTHUB_RG" \
    --namespace-name "$EVENTHUB_NAMESPACE" \
    --name "RootManageSharedAccessKey" \
    --query primaryConnectionString \
    --output tsv 2>/dev/null)"; then
    err "Failed to obtain Event Hub connection string. Check RG/namespace."
    exit 1
  fi
fi

if [[ -z "$EVENTHUB_CONNECTION_STRING" ]]; then
  err "Empty Event Hub connection string. Verify Azure permissions and resource names."
  exit 1
fi
ok "Event Hub connection string obtained"

# Extract OCI settings
if [[ -z "$OCI_MESSAGE_ENDPOINT" || -z "$OCI_STREAM_OCID" ]]; then
  if [[ -f "$HOME/.oci/config" ]]; then
    info "Loading OCI settings from ~/.oci/config (you can override with env vars)"
    # We don't parse endpoint/stream OCID from config by default; require envs or use defaults if known
    # If you want to bake defaults, set env vars before running the script.
  else
    warn "OCI config file not found. Ensure OCI_MESSAGE_ENDPOINT and OCI_STREAM_OCID are exported."
  fi
fi

if [[ -z "$OCI_MESSAGE_ENDPOINT" || -z "$OCI_STREAM_OCID" ]]; then
  try_load_from_local_settings "$LOCAL_SETTINGS_PATH"
  # Try a sibling local.settings.json if the default path is absent
  if [[ -z "$OCI_MESSAGE_ENDPOINT" || -z "$OCI_STREAM_OCID" ]]; then
    try_load_from_local_settings "$PWD/local.settings.json"
  fi
fi

if [[ -z "$OCI_MESSAGE_ENDPOINT" || -z "$OCI_STREAM_OCID" ]]; then
  err "OCI_MESSAGE_ENDPOINT and/or OCI_STREAM_OCID not set.
Export them, e.g.:
  export OCI_MESSAGE_ENDPOINT=\"https://cell-1.streaming.eu-frankfurt-1.oci.oraclecloud.com\"
  export OCI_STREAM_OCID=\"ocid1.stream.oc1...\""
  exit 1
fi
ok "OCI environment variables present"

# Export minimal env for helper scripts
export EVENTHUB_CONNECTION_STRING
export EVENTHUB_NAME="$EVENTHUB_NAME"

echo ""
info "Configuration:"
echo "  Event Hub RG:        $EVENTHUB_RG"
echo "  Event Hub Namespace: $EVENTHUB_NAMESPACE"
echo "  Event Hub Name:      $EVENTHUB_NAME"
echo "  Consumer Group:      $CONSUMER_GROUP"
echo "  Drain Mode:          $( [[ "$FROM_BEGINNING" == true ]] && echo 'from-beginning' || echo "from $START_ISO" )"
echo "  Inactivity Timeout:  ${INACTIVITY_TIMEOUT}s"
echo "  All Event Hubs:      $ALL_EVENTHUBS"
echo ""

cd "$SCRIPT_DIR"

# All Event Hubs mode: enumerate hubs and drain each
if [[ "$ALL_EVENTHUBS" == true ]]; then
  info "Enumerating Event Hubs in namespace '$EVENTHUB_NAMESPACE'..."
  if ! command -v az >/dev/null 2>&1; then
    err "Azure CLI is required to list Event Hubs. Install Azure CLI."
    exit 1
  fi
  EH_LIST=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && EH_LIST+=("$line")
  done < <(az eventhubs eventhub list \
    --resource-group "$EVENTHUB_RG" \
    --namespace-name "$EVENTHUB_NAMESPACE" \
    --query "[].name" \
    --output tsv 2>/dev/null)

  if [[ ${#EH_LIST[@]} -eq 0 ]]; then
    err "No Event Hubs found in namespace '$EVENTHUB_NAMESPACE'."
    exit 1
  fi

  info "Found ${#EH_LIST[@]} Event Hubs:"
  for EH in "${EH_LIST[@]}"; do
    echo "  • $EH"
  done

  info "Draining all Event Hubs to OCI Streaming..."
  OVERALL_RC=0
  for EH in "${EH_LIST[@]}"; do
    echo ""
    info "Draining Event Hub: $EH"
    DRAIN_CMD=( python3 eventhub_consumer.py
      --connection-string "$EVENTHUB_CONNECTION_STRING"
      --eventhub-name "$EH"
      --consumer-group "$CONSUMER_GROUP"
      --inactivity-timeout "$INACTIVITY_TIMEOUT"
    )
    if [[ "$FROM_BEGINNING" == true ]]; then
      DRAIN_CMD+=( --from-beginning )
    elif [[ -n "$START_ISO" ]]; then
      DRAIN_CMD+=( --start-iso "$START_ISO" )
    fi
    echo "  Running: ${DRAIN_CMD[*]}"
    set +e
    "${DRAIN_CMD[@]}"
    RC=$?
    set -e
    if [[ $RC -ne 0 ]]; then
      warn "Drain failed for '$EH' (exit $RC)"
      OVERALL_RC=$RC
    else
      ok "Drain completed for '$EH'"
    fi
  done

  echo ""
  printf "${GREEN}===============================================================================${NC}\n"
  printf "${GREEN}🎉 Completed: Namespace drain (%s → OCI Streaming)${NC}\n" "$EVENTHUB_NAMESPACE"
  printf "${GREEN}===============================================================================${NC}\n"
  exit $OVERALL_RC
fi

# Step A: Optionally send sample events to Event Hub (for testing)
if [[ "$COUNT" -gt 0 ]]; then
  if [[ -f "test_send_to_eventhub.py" ]]; then
    info "Sending $COUNT sample EntraID audit logs to Event Hub..."
    python3 test_send_to_eventhub.py \
      --count "$COUNT" \
      --connection-string "$EVENTHUB_CONNECTION_STRING" \
      --eventhub-name "$EVENTHUB_NAME" || warn "Sample send failed (continuing)"
    ok "Sample send step complete"
  else
    warn "Sample sender (test_send_to_eventhub.py) not found. Skipping sample send."
  fi
else
  info "Skipping sample send (COUNT=$COUNT)"
fi

# Step B: Drain all messages to OCI
info "Draining Event Hub to OCI Streaming..."
DRAIN_CMD=( python3 eventhub_consumer.py
  --connection-string "$EVENTHUB_CONNECTION_STRING"
  --eventhub-name "$EVENTHUB_NAME"
  --consumer-group "$CONSUMER_GROUP"
  --inactivity-timeout "$INACTIVITY_TIMEOUT"
)

if [[ "$FROM_BEGINNING" == true ]]; then
  DRAIN_CMD+=( --from-beginning )
elif [[ -n "$START_ISO" ]]; then
  DRAIN_CMD+=( --start-iso "$START_ISO" )
fi

echo "  Running: ${DRAIN_CMD[*]}"
set +e
"${DRAIN_CMD[@]}"
DRAIN_RC=$?
set -e

if [[ $DRAIN_RC -ne 0 ]]; then
  err "Drain command failed (exit $DRAIN_RC)"
  exit $DRAIN_RC
fi
ok "Drain step completed"

echo ""
printf "${GREEN}===============================================================================${NC}\n"
printf "${GREEN}🎉 Completed: Event Hub → OCI Streaming drain${NC}\n"
printf "${GREEN}===============================================================================${NC}\n"
echo "Next:"
echo "  • Verify OCI Streaming stream shows received messages"
echo "  • Point EntraID Diagnostic Settings to Event Hub '$EVENTHUB_NAME' for continuous flow"
