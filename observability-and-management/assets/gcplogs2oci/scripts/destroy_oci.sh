#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# destroy_oci.sh – Remove all OCI resources created by setup_oci.sh
#
# Deletes (in dependency-safe order):
#   1. Connector Hub
#   2. Log Analytics Source
#   3. Log Analytics Parser + 40 custom fields (via Python SDK)
#   4. Log Analytics Log Group
#   5. Stream
#   6. Stream Pool
#
# Prerequisites:
#   - oci CLI configured (oci setup config)
#   - .env.local populated with OCI variables
#   - Python 3 + oci-sdk (pip install oci)
#
# Usage:
#   ./scripts/destroy_oci.sh           # interactive (with confirmation)
#   ./scripts/destroy_oci.sh --force   # skip confirmation prompt
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

# Load environment
if [ -f "$PROJECT_DIR/.env.local" ]; then
    set -a; source "$PROJECT_DIR/.env.local"; set +a
    echo "Loaded .env.local"
elif [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
    echo "Loaded .env"
else
    echo "ERROR: No .env.local or .env found."
    exit 1
fi

COMPARTMENT="${OCI_COMPARTMENT_OCID:?OCI_COMPARTMENT_OCID is required}"
REGION="${OCI_REGION:?OCI_REGION is required}"

STREAM_POOL_NAME="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
STREAM_NAME="${OCI_STREAM_NAME:-gcp-inbound-stream}"
LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-GCPLogs}"
NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"
SCH_NAME="${OCI_SCH_NAME:-GCP-Stream-to-LogAnalytics}"

PARSER_NAME="gcpCloudLoggingJsonParser"
SOURCE_NAME="GCP Cloud Logging Logs"

# ── Auto-detect Log Analytics namespace ──────────────────────
if [ -z "$NAMESPACE" ]; then
    echo "Detecting Log Analytics namespace..."
    NAMESPACE=$(oci log-analytics namespace list \
        --compartment-id "$COMPARTMENT" \
        --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
    if [ -z "$NAMESPACE" ] || [ "$NAMESPACE" = "null" ]; then
        echo "WARNING: Could not detect Log Analytics namespace. Parser/field/source cleanup will be skipped."
        NAMESPACE=""
    else
        echo "  Namespace: $NAMESPACE"
    fi
fi

echo ""
echo "============================================================"
echo "  OCI Destroy for gcplogs2oci"
echo "============================================================"
echo "  Compartment:  ${COMPARTMENT:0:30}..."
echo "  Region:       $REGION"
echo "  Stream Pool:  $STREAM_POOL_NAME"
echo "  Stream:       $STREAM_NAME"
echo "  Log Group:    $LOG_GROUP_NAME"
echo "  SCH:          $SCH_NAME"
echo "  Parser:       $PARSER_NAME"
echo "  Source:       $SOURCE_NAME"
echo "============================================================"
echo ""

# ── Confirmation ──────────────────────────────────────────────
if [ "$FORCE" = false ]; then
    echo "WARNING: This will permanently delete the above OCI resources."
    read -rp "Continue? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[yY] ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

DELETED=0
SKIPPED=0

# ── 1. Delete Connector Hub ──────────────────────────────────
echo "1/7  Deleting Connector Hub: $SCH_NAME"
SCH_ID=$(oci sch service-connector list \
    --compartment-id "$COMPARTMENT" \
    --display-name "$SCH_NAME" \
    --lifecycle-state ACTIVE \
    --query 'data.items[0].id' --raw-output 2>/dev/null || true)

if [ -n "$SCH_ID" ] && [ "$SCH_ID" != "null" ] && [ "$SCH_ID" != "None" ]; then
    oci sch service-connector delete \
        --service-connector-id "$SCH_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 300 2>/dev/null || true
    echo "     Deleted: ${SCH_ID:0:50}..."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 2. Delete Log Analytics Source ───────────────────────────
echo "2/7  Deleting Log Analytics source: $SOURCE_NAME"
if [ -n "$NAMESPACE" ]; then
    EXISTING_SOURCE=$(oci log-analytics source list-sources \
        --namespace-name "$NAMESPACE" \
        --compartment-id "$COMPARTMENT" \
        --name "$SOURCE_NAME" \
        --is-system ALL \
        --query 'data.items[0].name' --raw-output 2>/dev/null || true)

    if [ -n "$EXISTING_SOURCE" ] && [ "$EXISTING_SOURCE" != "null" ] && [ "$EXISTING_SOURCE" != "None" ]; then
        oci log-analytics source delete-source \
            --namespace-name "$NAMESPACE" \
            --source-name "$EXISTING_SOURCE" \
            --force 2>/dev/null || true
        echo "     Deleted: $EXISTING_SOURCE"
        ((DELETED++))
    else
        echo "     Not found, skipping."
        ((SKIPPED++))
    fi
else
    echo "     Skipped (no namespace)."
    ((SKIPPED++))
fi

# ── 3. Delete Log Analytics Parser + 4. Custom Fields ────────
echo "3/7  Deleting Log Analytics parser: $PARSER_NAME"
echo "4/7  Deleting 40 custom Log Analytics fields..."
if [ -n "$NAMESPACE" ]; then
    export LA_NAMESPACE="$NAMESPACE"

    python3 << 'PYEOF'
import oci, os, sys, json

# Build OCI config from environment
key_file = os.environ.get("OCI_KEY_FILE")
key_content = os.environ.get("OCI_KEY_CONTENT")
if key_file:
    import re
    with open(os.path.expanduser(key_file)) as f:
        raw = f.read()
    begin = re.search(r"-----BEGIN [A-Z ]+-----", raw)
    end = re.search(r"-----END [A-Z ]+-----", raw)
    key_pem = raw[begin.start():end.end()]
elif key_content:
    key_pem = key_content
else:
    print("ERROR: Set OCI_KEY_FILE or OCI_KEY_CONTENT")
    sys.exit(1)

cfg = {
    "user": os.environ["OCI_USER_OCID"],
    "key_content": key_pem,
    "pass_phrase": os.environ.get("OCI_KEY_PASSPHRASE", ""),
    "fingerprint": os.environ["OCI_FINGERPRINT"],
    "tenancy": os.environ["OCI_TENANCY_OCID"],
    "region": os.environ["OCI_REGION"],
}

namespace = os.environ["LA_NAMESPACE"]
client = oci.log_analytics.LogAnalyticsClient(cfg)

# ── Delete parser ──
parser_deleted = False
try:
    existing = client.get_parser(namespace, "gcpCloudLoggingJsonParser")
    etag = existing.headers.get("etag")
    client.delete_parser(namespace, "gcpCloudLoggingJsonParser", if_match=etag)
    print("     Parser deleted: gcpCloudLoggingJsonParser")
    parser_deleted = True
except oci.exceptions.ServiceError as e:
    if e.status == 404:
        print("     Parser not found, skipping.")
    else:
        print(f"     Parser delete error: {e.message}")

# ── Delete custom fields ──
field_display_names = [
    "Cloud Provider",
    "GCP Insert ID", "GCP Log Name", "GCP Resource Type", "GCP Project ID",
    "GCP Service Name", "GCP Method Name", "GCP Principal Email", "GCP Zone", "GCP Instance ID",
    "GCP Trace ID", "GCP Span ID", "GCP Text Payload",
    "GCP HTTP Method", "GCP HTTP URL", "GCP HTTP Status", "GCP HTTP Latency", "GCP HTTP Protocol",
    "GCP HTTP Remote IP", "GCP HTTP Request Size", "GCP HTTP Response Size", "GCP HTTP Server IP", "GCP HTTP User Agent",
    "GCP Operation ID", "GCP Source File", "GCP Source Line", "GCP Source Function",
    "GCP Configuration Name", "GCP Location", "GCP Cloud Run Service", "GCP Revision Name",
    "GCP Resource Name", "GCP Caller IP", "GCP Caller User Agent",
    "GCP Receive Timestamp",
    "GCP Subscription ID", "GCP Topic ID", "GCP Sink Name", "GCP Sink Destination",
    "GCP Label Instance ID",
]

deleted_fields = 0
skipped_fields = 0
for display_name in field_display_names:
    try:
        fields = client.list_fields(namespace, display_name_contains=display_name).data.items
        found = False
        for f in fields:
            if f.display_name == display_name:
                client.delete_field(namespace, f.name)
                deleted_fields += 1
                found = True
                break
        if not found:
            skipped_fields += 1
    except oci.exceptions.ServiceError as e:
        if e.status == 409:
            print(f"     Field in use (cannot delete): {display_name}")
        else:
            skipped_fields += 1
    except Exception:
        skipped_fields += 1

print(f"     Fields deleted: {deleted_fields}  skipped: {skipped_fields}")

# Write counts for the outer shell
with open('/tmp/gcplogs2oci_destroy_counts.json', 'w') as f:
    json.dump({"parser": 1 if parser_deleted else 0, "fields_deleted": deleted_fields, "fields_skipped": skipped_fields}, f)

PYEOF

    # Read counts from Python
    if [ -f /tmp/gcplogs2oci_destroy_counts.json ]; then
        PARSER_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/gcplogs2oci_destroy_counts.json')); print(d['parser'])")
        FIELDS_DEL=$(python3 -c "import json; d=json.load(open('/tmp/gcplogs2oci_destroy_counts.json')); print(d['fields_deleted'])")
        DELETED=$((DELETED + PARSER_COUNT + FIELDS_DEL))
        FIELDS_SKIP=$(python3 -c "import json; d=json.load(open('/tmp/gcplogs2oci_destroy_counts.json')); print(d['fields_skipped'])")
        SKIPPED=$((SKIPPED + (1 - PARSER_COUNT) + FIELDS_SKIP))
        rm -f /tmp/gcplogs2oci_destroy_counts.json
    fi
else
    echo "     Skipped (no namespace)."
    SKIPPED=$((SKIPPED + 2))
fi

# ── 5. Delete Log Analytics Log Group ────────────────────────
echo "5/7  Deleting Log Analytics Log Group: $LOG_GROUP_NAME"
if [ -n "$NAMESPACE" ]; then
    LOG_GROUP_ID=$(oci log-analytics log-group list \
        --compartment-id "$COMPARTMENT" \
        --namespace-name "$NAMESPACE" \
        --query "data.items[?\"display-name\"=='$LOG_GROUP_NAME'].id | [0]" \
        --raw-output 2>/dev/null || true)

    if [ -n "$LOG_GROUP_ID" ] && [ "$LOG_GROUP_ID" != "null" ] && [ "$LOG_GROUP_ID" != "None" ]; then
        oci log-analytics log-group delete \
            --namespace-name "$NAMESPACE" \
            --log-group-id "$LOG_GROUP_ID" \
            --force 2>/dev/null || true
        echo "     Deleted: ${LOG_GROUP_ID:0:50}..."
        ((DELETED++))
    else
        echo "     Not found, skipping."
        ((SKIPPED++))
    fi
else
    echo "     Skipped (no namespace)."
    ((SKIPPED++))
fi

# ── 6. Delete Stream ─────────────────────────────────────────
echo "6/7  Deleting Stream: $STREAM_NAME"

# Use OCI_STREAM_OCID if set, otherwise search by name
if [ -n "${OCI_STREAM_OCID:-}" ]; then
    STREAM_ID="$OCI_STREAM_OCID"
else
    STREAM_ID=$(oci streaming admin stream list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)
fi

if [ -n "$STREAM_ID" ] && [ "$STREAM_ID" != "null" ] && [ "$STREAM_ID" != "None" ]; then
    oci streaming admin stream delete \
        --stream-id "$STREAM_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 300 2>/dev/null || true
    echo "     Deleted: ${STREAM_ID:0:50}..."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 7. Delete Stream Pool ───────────────────────────────────
echo "7/7  Deleting Stream Pool: $STREAM_POOL_NAME"
POOL_ID=$(oci streaming admin stream-pool list \
    --compartment-id "$COMPARTMENT" \
    --name "$STREAM_POOL_NAME" \
    --lifecycle-state ACTIVE \
    --query 'data[0].id' --raw-output 2>/dev/null || true)

if [ -n "$POOL_ID" ] && [ "$POOL_ID" != "null" ] && [ "$POOL_ID" != "None" ]; then
    oci streaming admin stream-pool delete \
        --stream-pool-id "$POOL_ID" \
        --force \
        --wait-for-state DELETED \
        --max-wait-seconds 300 2>/dev/null || true
    echo "     Deleted: ${POOL_ID:0:50}..."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── Cleanup ──────────────────────────────────────────────────
rm -f /tmp/gcplogs2oci_destroy_counts.json 2>/dev/null

echo ""
echo "============================================================"
echo "  OCI Destroy Complete"
echo "============================================================"
echo "  Deleted: $DELETED   Skipped (not found): $SKIPPED"
echo ""
echo "To re-create resources, run: ./scripts/setup_oci.sh"
echo ""
