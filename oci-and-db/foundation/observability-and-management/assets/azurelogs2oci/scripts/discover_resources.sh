#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# discover_resources.sh – Scan Azure and OCI backends for
#   existing azurelogs2oci resources.
#
# Source this file from setup/teardown scripts:
#   source "$SCRIPT_DIR/discover_resources.sh"
#
# Requires:
#   - lib/common.sh already sourced (for info, ok, warn, err)
#   - OCI CLI + OCI_COMPARTMENT_ID for OCI discovery
#   - Azure CLI (logged in) for Azure discovery
#
# After calling discover_oci_resources / discover_azure_resources,
# results are available in DISC_* variables.
# ─────────────────────────────────────────────────────────────

# ── Shared helpers ───────────────────────────────────────────

parse_eventhub_namespace_from_connection_string() {
  local connection_string="${1:-${EventHubsConnectionString:-}}"
  if [[ "$connection_string" =~ Endpoint=sb://([^.]+)\.servicebus\.windows\.net/? ]]; then
    echo "${BASH_REMATCH[1]}"
  fi
}

is_oci_stream_pool_ocid() {
  local ocid="${1:-}"
  [[ "$ocid" == ocid1.streampool.* ]]
}

discover_azure_defaults() {
  local rg="${1:-${AZ_RG:-${EVENTHUB_RG:-}}}"

  DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-}"
  DISC_AZ_SUGGESTED_STORAGE_ACCOUNT="${AZ_STORAGE_ACCOUNT:-}"
  DISC_AZ_SUGGESTED_FUNCTION_APP="${AZ_FUNCTION_APP:-}"

  [[ -z "$rg" ]] && return 0
  command -v az >/dev/null 2>&1 || return 0
  az account show >/dev/null 2>&1 || return 0

  if [[ -z "$DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE" ]]; then
    DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE="$(parse_eventhub_namespace_from_connection_string)"
  fi

  if [[ -z "$DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE" ]]; then
    local namespaces=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && namespaces+=("$line")
    done < <(az eventhubs namespace list --resource-group "$rg" --query "[].name" -o tsv 2>/dev/null)
    if [[ ${#namespaces[@]} -eq 1 ]]; then
      DISC_AZ_SUGGESTED_EVENTHUB_NAMESPACE="${namespaces[0]}"
    fi
  fi

  if [[ -z "$DISC_AZ_SUGGESTED_STORAGE_ACCOUNT" ]]; then
    local storage_accounts=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && storage_accounts+=("$line")
    done < <(az storage account list --resource-group "$rg" --query "[].name" -o tsv 2>/dev/null)
    if [[ ${#storage_accounts[@]} -eq 1 ]]; then
      DISC_AZ_SUGGESTED_STORAGE_ACCOUNT="${storage_accounts[0]}"
    fi
  fi

  if [[ -z "$DISC_AZ_SUGGESTED_FUNCTION_APP" ]]; then
    local function_apps=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && function_apps+=("$line")
    done < <(az functionapp list --resource-group "$rg" --query "[].name" -o tsv 2>/dev/null)
    if [[ ${#function_apps[@]} -eq 1 ]]; then
      DISC_AZ_SUGGESTED_FUNCTION_APP="${function_apps[0]}"
    fi
  fi
}

discover_oci_stream_defaults() {
  local compartment="${1:-${OCI_COMPARTMENT_ID:-${OCI_COMPARTMENT_OCID:-}}}"
  local preferred_stream_id="${OCI_STREAM_OCID:-${StreamOcid:-}}"
  local preferred_stream_name="${OCI_STREAM_NAME:-}"

  DISC_OCI_SUGGESTED_STREAM_ID=""
  DISC_OCI_SUGGESTED_STREAM_NAME="$preferred_stream_name"
  DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT="${OCI_MESSAGE_ENDPOINT:-${MessageEndpoint:-}}"
  DISC_OCI_STREAM_OCID_IS_POOL="false"

  [[ -z "$compartment" ]] && return 0
  command -v oci >/dev/null 2>&1 || return 0

  if [[ -n "$preferred_stream_id" ]]; then
    if is_oci_stream_pool_ocid "$preferred_stream_id"; then
      DISC_OCI_STREAM_OCID_IS_POOL="true"
      return 0
    fi

    local stream_json=""
    stream_json="$(oci streaming admin stream get --stream-id "$preferred_stream_id" 2>/dev/null || true)"
    if [[ -n "$stream_json" ]]; then
      DISC_OCI_SUGGESTED_STREAM_ID="$preferred_stream_id"
      DISC_OCI_SUGGESTED_STREAM_NAME="$(printf '%s' "$stream_json" | python3 -c 'import json,sys; data=json.load(sys.stdin)["data"]; print(data.get("name",""))')"
      if [[ -z "$DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT" ]]; then
        DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT="$(printf '%s' "$stream_json" | python3 -c 'import json,sys; data=json.load(sys.stdin)["data"]; print(data.get("messages-endpoint",""))')"
      fi
      return 0
    fi
  fi

  local query='data[].{"id":id,"name":name,"endpoint":"messages-endpoint"}'
  if [[ -n "$preferred_stream_name" ]]; then
    query="data[?name=='$preferred_stream_name'].{\"id\":id,\"name\":name,\"endpoint\":\"messages-endpoint\"}"
  fi

  local streams_json=""
  streams_json="$(oci streaming admin stream list --compartment-id "$compartment" --query "$query" 2>/dev/null || true)"
  [[ -z "$streams_json" ]] && return 0

  local count=""
  count="$(printf '%s' "$streams_json" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("data", [])))' 2>/dev/null || true)"
  if [[ "$count" == "1" ]]; then
    DISC_OCI_SUGGESTED_STREAM_ID="$(printf '%s' "$streams_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"][0].get("id",""))')"
    DISC_OCI_SUGGESTED_STREAM_NAME="$(printf '%s' "$streams_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"][0].get("name",""))')"
    if [[ -z "$DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT" ]]; then
      DISC_OCI_SUGGESTED_MESSAGE_ENDPOINT="$(printf '%s' "$streams_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"][0].get("endpoint",""))')"
    fi
  fi
}

# ── OCI Discovery ────────────────────────────────────────────

# Populates:
#   DISC_OCI_STREAM_POOL_ID, DISC_OCI_STREAM_POOL_NAME
#   DISC_OCI_STREAM_ID, DISC_OCI_STREAM_NAME
#   DISC_OCI_LOG_GROUP_ID, DISC_OCI_LOG_GROUP_NAME
#   DISC_OCI_SCH_ID, DISC_OCI_SCH_NAME
#   DISC_OCI_LA_SOURCE
#   DISC_OCI_NAMESPACE
discover_oci_resources() {
  local compartment="${OCI_COMPARTMENT_ID:-${OCI_COMPARTMENT_OCID:-}}"
  local tenancy="${OCI_TENANCY_OCID:-${tenancy:-}}"
  local pool_name="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
  local stream_name="${OCI_STREAM_NAME:-azure-inbound-stream}"
  local log_group_name="${OCI_LOG_GROUP_NAME:-AzureLogs}"
  local sch_name="${OCI_SCH_NAME:-Azure-Stream-to-LogAnalytics}"
  local namespace="${OCI_LOG_ANALYTICS_NAMESPACE:-}"
  local source_name="Azure Logs"

  DISC_OCI_STREAM_POOL_ID=""
  DISC_OCI_STREAM_POOL_NAME="$pool_name"
  DISC_OCI_STREAM_ID=""
  DISC_OCI_STREAM_NAME="$stream_name"
  DISC_OCI_LOG_GROUP_ID=""
  DISC_OCI_LOG_GROUP_NAME="$log_group_name"
  DISC_OCI_SCH_ID=""
  DISC_OCI_SCH_NAME="$sch_name"
  DISC_OCI_LA_SOURCE=""
  DISC_OCI_NAMESPACE="$namespace"

  if [[ -z "$compartment" ]]; then
    warn "OCI_COMPARTMENT_ID not set; skipping OCI discovery."
    return 1
  fi

  if ! command -v oci >/dev/null 2>&1; then
    warn "oci CLI not found; skipping OCI discovery."
    return 1
  fi

  info "Discovering OCI resources..."

  # Namespace (requires tenancy OCID, not compartment)
  if [[ -z "$namespace" && -n "$tenancy" ]]; then
    namespace=$(oci log-analytics namespace list \
        --compartment-id "$tenancy" \
        --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
    [[ "$namespace" == "null" ]] && namespace=""
  fi
  DISC_OCI_NAMESPACE="$namespace"

  # Stream Pool
  local pool_result
  pool_result=$(oci streaming admin stream-pool list \
      --compartment-id "$compartment" \
      --name "$pool_name" \
      --lifecycle-state ACTIVE \
      --query 'data[0].id' --raw-output 2>/dev/null || true)
  if [[ -n "$pool_result" && "$pool_result" != "null" ]]; then
    DISC_OCI_STREAM_POOL_ID="$pool_result"
  fi

  # Stream
  local stream_result
  stream_result=$(oci streaming admin stream list \
      --compartment-id "$compartment" \
      --name "$stream_name" \
      --lifecycle-state ACTIVE \
      --query 'data[0].id' --raw-output 2>/dev/null || true)
  if [[ -n "$stream_result" && "$stream_result" != "null" ]]; then
    DISC_OCI_STREAM_ID="$stream_result"
  fi

  # Also check local env for stream OCID
  if [[ -z "$DISC_OCI_STREAM_ID" ]]; then
    local env_stream="${OCI_STREAM_OCID:-${StreamOcid:-}}"
    if [[ -n "$env_stream" && "$env_stream" != "null" && "$env_stream" != *"example"* ]]; then
      DISC_OCI_STREAM_ID="$env_stream"
    fi
  fi

  # Log Group
  if [[ -n "$namespace" ]]; then
    local lg_result
    lg_result=$(oci log-analytics log-group list \
        --compartment-id "$compartment" \
        --namespace-name "$namespace" \
        --query "data.items[?\"display-name\"=='$log_group_name'].id | [0]" \
        --raw-output 2>/dev/null || true)
    if [[ -n "$lg_result" && "$lg_result" != "null" && "$lg_result" != "None" ]]; then
      DISC_OCI_LOG_GROUP_ID="$lg_result"
    fi

    # LA Source
    local src_result
    src_result=$(oci log-analytics source list-sources \
        --namespace-name "$namespace" \
        --compartment-id "$compartment" \
        --name "$source_name" \
        --is-system ALL \
        --query 'data.items[0].name' --raw-output 2>/dev/null || true)
    if [[ -n "$src_result" && "$src_result" != "null" && "$src_result" != "None" ]]; then
      DISC_OCI_LA_SOURCE="$src_result"
    fi
  fi

  # Service Connector Hub
  local sch_result
  sch_result=$(oci sch service-connector list \
      --compartment-id "$compartment" \
      --display-name "$sch_name" \
      --lifecycle-state ACTIVE \
      --query 'data.items[0].id' --raw-output 2>/dev/null || true)
  if [[ -n "$sch_result" && "$sch_result" != "null" && "$sch_result" != "None" ]]; then
    DISC_OCI_SCH_ID="$sch_result"
  fi

  ok "OCI discovery complete."
}

# ── Azure Discovery ──────────────────────────────────────────

# Populates:
#   DISC_AZ_RG_EXISTS (true/false)
#   DISC_AZ_EVENTHUB_NS_EXISTS (true/false)
#   DISC_AZ_EVENTHUBS (comma-separated list)
#   DISC_AZ_STORAGE_ACCOUNT_EXISTS (true/false)
#   DISC_AZ_FUNCTION_APP_EXISTS (true/false)
#   DISC_AZ_FUNCTION_APP
discover_azure_resources() {
  local rg="${AZ_RG:-${EVENTHUB_RG:-azurelogs2oci-rg}}"
  local ns="${EVENTHUB_NAMESPACE:-}"
  local sa="${AZ_STORAGE_ACCOUNT:-}"
  local app="${AZ_FUNCTION_APP:-}"

  DISC_AZ_RG_EXISTS="false"
  DISC_AZ_EVENTHUB_NS_EXISTS="false"
  DISC_AZ_EVENTHUBS=""
  DISC_AZ_STORAGE_ACCOUNT_EXISTS="false"
  DISC_AZ_FUNCTION_APP_EXISTS="false"
  DISC_AZ_FUNCTION_APP="$app"

  if ! command -v az >/dev/null 2>&1; then
    warn "az CLI not found; skipping Azure discovery."
    return 1
  fi

  if ! az account show >/dev/null 2>&1; then
    warn "Azure CLI not logged in; skipping Azure discovery."
    return 1
  fi

  info "Discovering Azure resources..."

  # Resource Group
  local rg_exists
  rg_exists=$(az group exists -n "$rg" 2>/dev/null || echo "false")
  if [[ "$rg_exists" == "true" ]]; then
    DISC_AZ_RG_EXISTS="true"
  fi

  # Event Hubs Namespace
  if [[ -n "$ns" && "$DISC_AZ_RG_EXISTS" == "true" ]]; then
    if az eventhubs namespace show --resource-group "$rg" --name "$ns" >/dev/null 2>&1; then
      DISC_AZ_EVENTHUB_NS_EXISTS="true"

      # List Event Hubs
      local hubs_csv
      hubs_csv=$(az eventhubs eventhub list \
          --resource-group "$rg" \
          --namespace-name "$ns" \
          --query "[].name" -o tsv 2>/dev/null | tr '\n' ',' | sed 's/,$//')
      DISC_AZ_EVENTHUBS="$hubs_csv"
    fi
  fi

  # Storage Account
  if [[ -n "$sa" && "$DISC_AZ_RG_EXISTS" == "true" ]]; then
    if az storage account show -g "$rg" -n "$sa" >/dev/null 2>&1; then
      DISC_AZ_STORAGE_ACCOUNT_EXISTS="true"
    fi
  fi

  # Function App
  if [[ -n "$app" && "$DISC_AZ_RG_EXISTS" == "true" ]]; then
    if az functionapp show -g "$rg" -n "$app" >/dev/null 2>&1; then
      DISC_AZ_FUNCTION_APP_EXISTS="true"
    fi
  fi

  ok "Azure discovery complete."
}

# ── Discovery Summary ────────────────────────────────────────

show_discovery_summary() {
  local section="${1:-all}"  # "oci", "azure", or "all"

  echo ""
  echo "============================================================"
  echo "  Resource Discovery Summary"
  echo "============================================================"

  if [[ "$section" == "oci" || "$section" == "all" ]]; then
    echo ""
    echo "  OCI Resources:"
    printf "    %-25s %s\n" "Namespace:" "${DISC_OCI_NAMESPACE:-(not detected)}"
    printf "    %-25s %s\n" "Stream Pool:" \
      "$( [[ -n "$DISC_OCI_STREAM_POOL_ID" ]] && echo "FOUND (${DISC_OCI_STREAM_POOL_ID:0:40}...)" || echo "not found" )"
    printf "    %-25s %s\n" "Stream:" \
      "$( [[ -n "$DISC_OCI_STREAM_ID" ]] && echo "FOUND (${DISC_OCI_STREAM_ID:0:40}...)" || echo "not found" )"
    printf "    %-25s %s\n" "Log Group:" \
      "$( [[ -n "$DISC_OCI_LOG_GROUP_ID" ]] && echo "FOUND (${DISC_OCI_LOG_GROUP_ID:0:40}...)" || echo "not found" )"
    printf "    %-25s %s\n" "LA Source:" \
      "$( [[ -n "$DISC_OCI_LA_SOURCE" ]] && echo "FOUND ($DISC_OCI_LA_SOURCE)" || echo "not found" )"
    printf "    %-25s %s\n" "Service Connector Hub:" \
      "$( [[ -n "$DISC_OCI_SCH_ID" ]] && echo "FOUND (${DISC_OCI_SCH_ID:0:40}...)" || echo "not found" )"
  fi

  if [[ "$section" == "azure" || "$section" == "all" ]]; then
    echo ""
    echo "  Azure Resources:"
    printf "    %-25s %s\n" "Resource Group:" \
      "$( [[ "$DISC_AZ_RG_EXISTS" == "true" ]] && echo "EXISTS" || echo "not found" )"
    printf "    %-25s %s\n" "Event Hub Namespace:" \
      "$( [[ "$DISC_AZ_EVENTHUB_NS_EXISTS" == "true" ]] && echo "EXISTS" || echo "not found" )"
    printf "    %-25s %s\n" "Event Hubs:" \
      "${DISC_AZ_EVENTHUBS:-(none)}"
    printf "    %-25s %s\n" "Storage Account:" \
      "$( [[ "$DISC_AZ_STORAGE_ACCOUNT_EXISTS" == "true" ]] && echo "EXISTS" || echo "not found" )"
    printf "    %-25s %s\n" "Function App:" \
      "$( [[ "$DISC_AZ_FUNCTION_APP_EXISTS" == "true" ]] && echo "EXISTS ($DISC_AZ_FUNCTION_APP)" || echo "not found" )"
  fi

  echo ""
  echo "============================================================"
  echo ""
}
