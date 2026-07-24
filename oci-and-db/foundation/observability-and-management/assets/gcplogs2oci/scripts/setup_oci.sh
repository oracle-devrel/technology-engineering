#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup_oci.sh – Provision OCI Streaming, Log Analytics, and
#                Connector Hub resources for the
#                GCP → OCI log pipeline.
#
# Creates:
#   1. Stream Pool + Stream (Kafka-compatible ingest)
#   2. Log Analytics Log Group (GCPLogs)
#   3. Log Analytics custom fields (GCP Cloud Logging schema)
#   4. Log Analytics JSON parser (GCP Cloud Logging JSON Parser)
#   5. Log Analytics source (GCP Cloud Logging Logs)
#   6. Connector Hub (Stream → Log Analytics)
#
# Prerequisites:
#   - oci CLI configured (oci setup config)
#   - .env.local populated with OCI variables
#   - Python 3 + oci-sdk (pip install oci)
#
# Usage:
#   ./scripts/setup_oci.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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
PARTITIONS="${OCI_STREAM_PARTITIONS:-1}"
LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-GCPLogs}"
NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"
SCH_NAME="${OCI_SCH_NAME:-GCP-Stream-to-LogAnalytics}"

# Source / parser names
PARSER_NAME="gcpCloudLoggingJsonParser"
SOURCE_NAME="GCP Cloud Logging Logs"

echo "============================================================"
echo "  OCI End-to-End Setup for gcplogs2oci"
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

# ── Auto-detect Log Analytics namespace ──────────────────────
if [ -z "$NAMESPACE" ]; then
    echo "Detecting Log Analytics namespace..."
    NAMESPACE=$(oci log-analytics namespace list \
        --compartment-id "$COMPARTMENT" \
        --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
    if [ -z "$NAMESPACE" ] || [ "$NAMESPACE" = "null" ]; then
        echo "ERROR: Could not detect Log Analytics namespace. Set OCI_LOG_ANALYTICS_NAMESPACE."
        exit 1
    fi
    echo "  Namespace: $NAMESPACE"
fi

# ── Interactive stream selection ───────────────────────────
SKIP_STREAM_CREATION=false

if [ -n "${OCI_STREAM_OCID:-}" ]; then
    # Stream OCID provided via env — verify it exists and get pool ID
    echo ""
    echo "OCI_STREAM_OCID is set. Verifying stream..."
    STREAM_INFO=$(oci streaming admin stream get --stream-id "$OCI_STREAM_OCID" 2>/dev/null || true)
    if [ -z "$STREAM_INFO" ]; then
        echo "ERROR: Stream $OCI_STREAM_OCID not found or not accessible."
        exit 1
    fi
    STREAM_ID="$OCI_STREAM_OCID"
    POOL_ID=$(echo "$STREAM_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['stream-pool-id'])")
    STREAM_NAME=$(echo "$STREAM_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['name'])")
    echo "  Using stream: $STREAM_NAME (${STREAM_ID:0:50}...)"
    echo "  Stream pool:  ${POOL_ID:0:50}..."
    SKIP_STREAM_CREATION=true
elif [ -t 0 ]; then
    # Interactive mode — list existing streams and let user choose
    echo ""
    echo "Checking for existing streams in compartment..."
    STREAM_JSON=$(oci streaming admin stream list \
        --compartment-id "$COMPARTMENT" \
        --lifecycle-state ACTIVE \
        --all \
        --query 'data[].{name:name, id:id}' 2>/dev/null || echo "[]")

    mapfile -t STREAM_NAMES < <(echo "$STREAM_JSON" | python3 -c "
import sys, json
streams = json.load(sys.stdin)
for s in streams:
    print(s['name'])
" 2>/dev/null || true)

    mapfile -t STREAM_IDS < <(echo "$STREAM_JSON" | python3 -c "
import sys, json
streams = json.load(sys.stdin)
for s in streams:
    print(s['id'])
" 2>/dev/null || true)

    if [ ${#STREAM_NAMES[@]} -gt 0 ]; then
        echo ""
        echo "  Existing streams in compartment:"
        for i in "${!STREAM_NAMES[@]}"; do
            printf "    %d) %s  (%s...)\n" "$((i+1))" "${STREAM_NAMES[$i]}" "${STREAM_IDS[$i]:0:50}"
        done
        CREATE_IDX=$(( ${#STREAM_NAMES[@]} + 1 ))
        printf "    %d) [Create a new stream]\n" "$CREATE_IDX"
        echo ""
        while true; do
            read -rp "  Select a stream [1-$CREATE_IDX]: " choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$CREATE_IDX" ]; then
                break
            else
                echo "  Invalid selection. Enter a number between 1 and $CREATE_IDX."
            fi
        done

        if [ "$choice" -lt "$CREATE_IDX" ]; then
            # User selected an existing stream
            STREAM_ID="${STREAM_IDS[$((choice-1))]}"
            STREAM_NAME="${STREAM_NAMES[$((choice-1))]}"
            echo "  Selected: $STREAM_NAME"
            echo ""
            # Look up the stream pool ID from the selected stream
            STREAM_DETAIL=$(oci streaming admin stream get --stream-id "$STREAM_ID")
            POOL_ID=$(echo "$STREAM_DETAIL" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['stream-pool-id'])")
            echo "  Stream pool: ${POOL_ID:0:50}..."
            SKIP_STREAM_CREATION=true

            # Offer to save to .env.local
            if [ -f "$PROJECT_DIR/.env.local" ]; then
                read -rp "  Save OCI_STREAM_OCID to .env.local? [Y/n]: " save_choice
                if [[ ! "$save_choice" =~ ^[nN] ]]; then
                    if grep -q '^OCI_STREAM_OCID=' "$PROJECT_DIR/.env.local"; then
                        sed -i.bak "s|^OCI_STREAM_OCID=.*|OCI_STREAM_OCID=\"$STREAM_ID\"|" "$PROJECT_DIR/.env.local"
                        rm -f "$PROJECT_DIR/.env.local.bak"
                    else
                        echo "OCI_STREAM_OCID=\"$STREAM_ID\"" >> "$PROJECT_DIR/.env.local"
                    fi
                    echo "  Saved to .env.local"
                fi
            fi
        else
            echo "  Creating a new stream..."
        fi
    else
        echo "  No existing streams found. Creating a new one..."
    fi
fi

# ── 1. Create Stream Pool ───────────────────────────────────
if [ "$SKIP_STREAM_CREATION" = true ]; then
    echo ""
    echo "1/7  Stream Pool: using existing (from selected stream)"
else
    echo ""
    echo "1/7  Creating Stream Pool: $STREAM_POOL_NAME"
    EXISTING_POOL=$(oci streaming admin stream-pool list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_POOL_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)

    if [ -n "$EXISTING_POOL" ] && [ "$EXISTING_POOL" != "null" ]; then
        POOL_ID="$EXISTING_POOL"
        echo "     Pool already exists: ${POOL_ID:0:50}..."
    else
        POOL_ID=$(oci streaming admin stream-pool create \
            --compartment-id "$COMPARTMENT" \
            --name "$STREAM_POOL_NAME" \
            --query 'data.id' --raw-output \
            --wait-for-state ACTIVE \
            --max-wait-seconds 120)
        echo "     Pool created: ${POOL_ID:0:50}..."
    fi
fi

# ── 2. Create Stream ────────────────────────────────────────
if [ "$SKIP_STREAM_CREATION" = true ]; then
    echo "2/7  Stream: using existing ($STREAM_NAME)"
else
    echo "2/7  Creating Stream: $STREAM_NAME"
    EXISTING_STREAM=$(oci streaming admin stream list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)

    if [ -n "$EXISTING_STREAM" ] && [ "$EXISTING_STREAM" != "null" ]; then
        STREAM_ID="$EXISTING_STREAM"
        echo "     Stream already exists: ${STREAM_ID:0:50}..."
    else
        STREAM_ID=$(oci streaming admin stream create \
            --name "$STREAM_NAME" \
            --partitions "$PARTITIONS" \
            --stream-pool-id "$POOL_ID" \
            --query 'data.id' --raw-output \
            --wait-for-state ACTIVE \
            --max-wait-seconds 120)
        echo "     Stream created: ${STREAM_ID:0:50}..."
    fi
fi

# ── 3. Kafka Connection Info ───────────────────────────────
echo "3/7  Retrieving Kafka connection details..."
POOL_INFO=$(oci streaming admin stream-pool get --stream-pool-id "$POOL_ID")
KAFKA_ENDPOINT=$(echo "$POOL_INFO" | python3 -c "
import sys, json
d = json.load(sys.stdin)
settings = d.get('data', {}).get('kafka-settings', {})
print(settings.get('bootstrap-servers', 'N/A'))
" 2>/dev/null || echo "N/A")
echo "     Bootstrap servers: $KAFKA_ENDPOINT"

# ── 4. Create Log Analytics Log Group ────────────────────────
echo "4/7  Creating Log Analytics Log Group: $LOG_GROUP_NAME"
EXISTING_LG=$(oci log-analytics log-group list \
    --compartment-id "$COMPARTMENT" \
    --namespace-name "$NAMESPACE" \
    --query "data.items[?\"display-name\"=='$LOG_GROUP_NAME'].id | [0]" \
    --raw-output 2>/dev/null || true)

if [ -n "$EXISTING_LG" ] && [ "$EXISTING_LG" != "null" ] && [ "$EXISTING_LG" != "None" ]; then
    LOG_GROUP_ID="$EXISTING_LG"
    echo "     Log Group already exists: ${LOG_GROUP_ID:0:50}..."
else
    LOG_GROUP_ID=$(oci log-analytics log-group create \
        --compartment-id "$COMPARTMENT" \
        --namespace-name "$NAMESPACE" \
        --display-name "$LOG_GROUP_NAME" \
        --description "GCP Cloud Logging imports via gcplogs2oci bridge" \
        --query 'data.id' --raw-output)
    echo "     Log Group created: ${LOG_GROUP_ID:0:50}..."
fi

# ── 5. Create custom Log Analytics fields + parser ──────────
echo "5/7  Creating GCP Cloud Logging parser and fields..."
export LA_NAMESPACE="$NAMESPACE"

python3 << 'PYEOF'
import oci, os, sys, json

sys.path.insert(0, os.environ.get("PROJECT_DIR", "."))

# Build OCI config from environment
key_file = os.environ.get("OCI_KEY_FILE")
key_content = os.environ.get("OCI_KEY_CONTENT")
if key_file:
    import re, textwrap
    with open(os.path.expanduser(key_file)) as f:
        raw = f.read()
    # parse_key inline (minimal)
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

# ── Create custom fields (auto-generated internal names) ────
from oci.log_analytics.models import UpsertLogAnalyticsFieldDetails

field_display_names = [
    # Multicloud
    "Cloud Provider",
    # Core GCP LogEntry fields
    "GCP Insert ID",
    "GCP Log Name",
    "GCP Resource Type",
    "GCP Project ID",
    "GCP Service Name",
    "GCP Method Name",
    "GCP Principal Email",
    "GCP Zone",
    "GCP Instance ID",
    "GCP Trace ID",
    "GCP Span ID",
    "GCP Text Payload",
    # HTTP request (Cloud Run, Load Balancer, etc.)
    "GCP HTTP Method",
    "GCP HTTP URL",
    "GCP HTTP Status",
    "GCP HTTP Latency",
    "GCP HTTP Protocol",
    "GCP HTTP Remote IP",
    "GCP HTTP Request Size",
    "GCP HTTP Response Size",
    "GCP HTTP Server IP",
    "GCP HTTP User Agent",
    # Source location & operation
    "GCP Operation ID",
    "GCP Source File",
    "GCP Source Line",
    "GCP Source Function",
    # Cloud Run resource labels
    "GCP Configuration Name",
    "GCP Location",
    "GCP Cloud Run Service",
    "GCP Revision Name",
    # Audit log extended fields
    "GCP Resource Name",
    "GCP Caller IP",
    "GCP Caller User Agent",
    # Metadata
    "GCP Receive Timestamp",
    # Resource labels (multi-type)
    "GCP Subscription ID",
    "GCP Topic ID",
    "GCP Sink Name",
    "GCP Sink Destination",
    # Labels
    "GCP Label Instance ID",
]

field_name_map = {}
for display_name in field_display_names:
    details = UpsertLogAnalyticsFieldDetails()
    details.display_name = display_name
    details.data_type = "String"
    details.is_multi_valued = False
    try:
        resp = client.upsert_field(namespace, details)
        field_name_map[display_name] = resp.data.name
        print(f"     Field OK  {resp.data.name:12s} -> {display_name}")
    except oci.exceptions.ServiceError as e:
        # Field may already exist; try to find it
        try:
            fields = client.list_fields(namespace, display_name_contains=display_name).data.items
            for f in fields:
                if f.display_name == display_name:
                    field_name_map[display_name] = f.name
                    print(f"     Field EXISTS {f.name:12s} -> {display_name}")
                    break
        except Exception:
            print(f"     Field ERR: {display_name}: {e.message}")

# ── Create JSON parser ──────────────────────────────────────
# Map: (field_display_name or built-in name, json_path, seq)
# 44 field mappings covering all GCP LogEntry types:
#   - Audit logs (gce_instance, pubsub_topic/subscription, logging_sink, project)
#   - Cloud Run logs (stdout, requests with httpRequest)
#   - Generic metadata (trace, span, receiveTimestamp, etc.)
field_mappings = [
    # Built-in LA fields
    ("msg",                      "$.jsonPayload.message",                                1),
    ("sevlvl",                   "$.severity",                                           2),
    ("time",                     "$.timestamp",                                          3),
    ("method",                   "$.protoPayload.methodName",                            4),
    # Multicloud
    ("Cloud Provider",           "$.cloudProvider",                                      5),
    # Core GCP LogEntry
    ("GCP Insert ID",            "$.insertId",                                           6),
    ("GCP Log Name",             "$.logName",                                            7),
    ("GCP Resource Type",        "$.resource.type",                                      8),
    ("GCP Project ID",           "$.resource.labels.project_id",                         9),
    ("GCP Service Name",         "$.protoPayload.serviceName",                          10),
    ("GCP Method Name",          "$.protoPayload.methodName",                           11),
    ("GCP Principal Email",      "$.protoPayload.authenticationInfo.principalEmail",    12),
    ("GCP Zone",                 "$.resource.labels.zone",                              13),
    ("GCP Instance ID",          "$.resource.labels.instance_id",                       14),
    ("GCP Trace ID",             "$.trace",                                             15),
    ("GCP Span ID",              "$.spanId",                                            16),
    ("GCP Text Payload",         "$.textPayload",                                       17),
    # HTTP request (full)
    ("GCP HTTP Method",          "$.httpRequest.requestMethod",                          18),
    ("GCP HTTP URL",             "$.httpRequest.requestUrl",                             19),
    ("GCP HTTP Status",          "$.httpRequest.status",                                20),
    ("GCP HTTP Latency",         "$.httpRequest.latency",                               21),
    ("GCP HTTP Protocol",        "$.httpRequest.protocol",                              22),
    ("GCP HTTP Remote IP",       "$.httpRequest.remoteIp",                              23),
    ("GCP HTTP Request Size",    "$.httpRequest.requestSize",                           24),
    ("GCP HTTP Response Size",   "$.httpRequest.responseSize",                          25),
    ("GCP HTTP Server IP",       "$.httpRequest.serverIp",                              26),
    ("GCP HTTP User Agent",      "$.httpRequest.userAgent",                             27),
    # Source location & operation
    ("GCP Operation ID",         "$.operation.id",                                      28),
    ("GCP Source File",          "$.sourceLocation.file",                               29),
    ("GCP Source Line",          "$.sourceLocation.line",                               30),
    ("GCP Source Function",      "$.sourceLocation.function",                           31),
    # Cloud Run resource labels
    ("GCP Configuration Name",   "$.resource.labels.configuration_name",                32),
    ("GCP Location",             "$.resource.labels.location",                          33),
    ("GCP Cloud Run Service",    "$.resource.labels.service_name",                      34),
    ("GCP Revision Name",        "$.resource.labels.revision_name",                     35),
    # Audit log extended
    ("GCP Resource Name",        "$.protoPayload.resourceName",                         36),
    ("GCP Caller IP",            "$.protoPayload.requestMetadata.callerIp",             37),
    ("GCP Caller User Agent",    "$.protoPayload.requestMetadata.callerSuppliedUserAgent", 38),
    # Metadata
    ("GCP Receive Timestamp",    "$.receiveTimestamp",                                  39),
    # Resource labels (multi-type)
    ("GCP Subscription ID",      "$.resource.labels.subscription_id",                   40),
    ("GCP Topic ID",             "$.resource.labels.topic_id",                          41),
    ("GCP Sink Name",            "$.resource.labels.name",                              42),
    ("GCP Sink Destination",     "$.resource.labels.destination",                       43),
    # Labels
    ("GCP Label Instance ID",    "$.labels.instanceId",                                 44),
]

from oci.log_analytics.models import (
    UpsertLogAnalyticsParserDetails,
    LogAnalyticsParserField,
    LogAnalyticsField,
)

parser_field_maps = []
for name_or_display, json_path, seq in field_mappings:
    internal = field_name_map.get(name_or_display, name_or_display)
    parser_field_maps.append(
        LogAnalyticsParserField(
            field=LogAnalyticsField(name=internal),
            parser_field_name=internal,
            parser_field_sequence=seq,
            storage_field_name=internal,
            structured_column_info=json_path,
        )
    )

# Example log content for UI validation (synthetic — exercises all 44 field mappings)
example_log = {
    "cloudProvider": "GCP",
    "insertId": "abc123def456-0",
    "timestamp": "2026-01-15T10:30:00.000Z",
    "receiveTimestamp": "2026-01-15T10:30:00.500Z",
    "severity": "INFO",
    "logName": "projects/my-project/logs/cloudaudit.googleapis.com%2Factivity",
    "resource": {
        "type": "cloud_run_revision",
        "labels": {
            "project_id": "my-project",
            "zone": "us-central1-a",
            "instance_id": "1234567890",
            "configuration_name": "my-service",
            "location": "europe-west1",
            "service_name": "my-service",
            "revision_name": "my-service-00001-abc",
            "subscription_id": "my-subscription",
            "topic_id": "my-topic",
            "name": "my-log-sink",
            "destination": "pubsub.googleapis.com/projects/my-project/topics/export",
        },
    },
    "protoPayload": {
        "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
        "methodName": "v1.compute.instances.start",
        "serviceName": "compute.googleapis.com",
        "authenticationInfo": {"principalEmail": "user@example.com"},
        "resourceName": "projects/my-project/zones/us-central1-a/instances/my-instance",
        "requestMetadata": {
            "callerIp": "203.0.113.50",
            "callerSuppliedUserAgent": "google-cloud-sdk gcloud/450.0.0",
        },
        "status": {},
    },
    "jsonPayload": {"message": "Instance started successfully"},
    "textPayload": "Container started on port 8080",
    "httpRequest": {
        "requestMethod": "GET",
        "requestUrl": "https://my-service.europe-west1.run.app/api/health",
        "status": 200,
        "latency": "0.025s",
        "protocol": "HTTP/1.1",
        "remoteIp": "203.0.113.50",
        "requestSize": "256",
        "responseSize": "1024",
        "serverIp": "10.0.0.1",
        "userAgent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
    },
    "trace": "projects/my-project/traces/abc123def456789",
    "spanId": "000000000000004a",
    "operation": {"id": "operation-12345"},
    "sourceLocation": {"file": "handler.py", "line": "42", "function": "handleRequest"},
    "labels": {"instanceId": "00a1b2c3d4e5f6"},
}
example_content = json.dumps(example_log, indent=2)

# Upsert parser via SDK (handles etag for updates)
parser_details = UpsertLogAnalyticsParserDetails(
    name="gcpCloudLoggingJsonParser",
    display_name="GCP Cloud Logging JSON Parser",
    description="Parses all GCP Cloud Logging LogEntry JSON types with 44 field mappings covering audit, Cloud Run, HTTP request, and metadata fields",
    type="JSON",
    language="en_US",
    encoding="UTF-8",
    is_default=True,
    is_single_line_content=False,
    is_system=False,
    header_content="$:0",
    content=example_content,
    example_content=example_content,
    field_maps=parser_field_maps,
)

# Get existing etag if parser already exists
etag = None
try:
    existing = client.get_parser(namespace, "gcpCloudLoggingJsonParser")
    etag = existing.headers.get("etag")
except oci.exceptions.ServiceError:
    pass

kwargs = {"if_match": etag} if etag else {}
result = client.upsert_parser(namespace, parser_details, **kwargs)
print(f"     Parser OK: {result.data.name} ({len(result.data.field_maps)} field maps)")

# Save field name map for source creation
with open('/tmp/gcp_field_name_map.json', 'w') as f:
    json.dump(field_name_map, f, indent=2)

PYEOF

# ── 6. Create Log Analytics source ──────────────────────────
echo "6/7  Creating Log Analytics source: $SOURCE_NAME"

# Check if source already exists
EXISTING_SOURCE=$(oci log-analytics source list-sources \
    --namespace-name "$NAMESPACE" \
    --compartment-id "$COMPARTMENT" \
    --name "$SOURCE_NAME" \
    --is-system ALL \
    --query 'data.items[0].name' --raw-output 2>/dev/null || true)

if [ -n "$EXISTING_SOURCE" ] && [ "$EXISTING_SOURCE" != "null" ] && [ "$EXISTING_SOURCE" != "None" ]; then
    echo "     Source already exists: $EXISTING_SOURCE"
else
    # Prepare parsers and entity-types JSON
    cat > /tmp/gcp_source_parsers.json << 'JSONEOF'
[{"name": "gcpCloudLoggingJsonParser", "isDefault": true}]
JSONEOF

    cat > /tmp/gcp_source_entity_types.json << 'JSONEOF'
[{"entityType": "oci_generic_resource", "entityTypeCategory": "Undefined", "entityTypeDisplayName": "OCI Generic Resource"}]
JSONEOF

    SOURCE_RESULT=$(oci log-analytics source upsert-source \
        --namespace-name "$NAMESPACE" \
        --name gcpCloudLoggingSource \
        --display-name "$SOURCE_NAME" \
        --description "GCP Cloud Logging structured logs from Pub/Sub via OCI Streaming. Supports multicloud monitoring with Cloud Provider = GCP." \
        --type-name "os_file" \
        --is-system false \
        --is-for-cloud false \
        --parsers file:///tmp/gcp_source_parsers.json \
        --entity-types file:///tmp/gcp_source_entity_types.json \
        2>&1 || true)

    if echo "$SOURCE_RESULT" | grep -q '"name"'; then
        echo "     Source created"
    else
        echo "     Source creation result: $(echo "$SOURCE_RESULT" | head -3)"
    fi
fi

# ── 7. Create Connector Hub ─────────────────────────────────
echo "7/7  Creating Connector Hub: $SCH_NAME"

EXISTING_SCH=$(oci sch service-connector list \
    --compartment-id "$COMPARTMENT" \
    --display-name "$SCH_NAME" \
    --lifecycle-state ACTIVE \
    --query 'data.items[0].id' --raw-output 2>/dev/null || true)

if [ -n "$EXISTING_SCH" ] && [ "$EXISTING_SCH" != "null" ] && [ "$EXISTING_SCH" != "None" ]; then
    SCH_ID="$EXISTING_SCH"
    echo "     SCH already exists: ${SCH_ID:0:50}..."
else
    # Source: OCI Streaming
    cat > /tmp/sch_source.json << JSONEOF
{
  "kind": "streaming",
  "streamId": "$STREAM_ID",
  "cursor": {"kind": "TRIM_HORIZON"}
}
JSONEOF

    # Target: Log Analytics with the GCP source
    cat > /tmp/sch_target.json << JSONEOF
{
  "kind": "loggingAnalytics",
  "logGroupId": "$LOG_GROUP_ID",
  "logSourceIdentifier": "$SOURCE_NAME"
}
JSONEOF

    SCH_ID=$(oci sch service-connector create \
        --compartment-id "$COMPARTMENT" \
        --display-name "$SCH_NAME" \
        --description "Forwards GCP Pub/Sub logs from OCI Streaming to Log Analytics ($LOG_GROUP_NAME group) using GCP Cloud Logging parser" \
        --source file:///tmp/sch_source.json \
        --target file:///tmp/sch_target.json \
        --query 'data.id' --raw-output \
        --wait-for-state ACTIVE \
        --max-wait-seconds 300 2>&1 || true)

    if [ -n "$SCH_ID" ] && [ "$SCH_ID" != "null" ]; then
        echo "     SCH created: ${SCH_ID:0:50}..."
    else
        echo "     SCH creation may need manual setup (check IAM policies)"
        echo "     Run: ./scripts/setup_oci_iam.sh --sch-only"
        echo "     Required policy: Allow any-user to use stream-pull + stream-consume"
        echo "                      Allow any-user to use log-analytics-log-group"
    fi
fi

# ── Cleanup temp files ──────────────────────────────────────
rm -f /tmp/gcp_field_name_map.json \
      /tmp/gcp_source_parsers.json /tmp/gcp_source_entity_types.json \
      /tmp/sch_source.json /tmp/sch_target.json 2>/dev/null

# Derive message endpoint
MSG_ENDPOINT=""
if [ "$KAFKA_ENDPOINT" != "N/A" ]; then
    MSG_ENDPOINT="https://$(echo "$KAFKA_ENDPOINT" | cut -d: -f1 | sed 's/^cell-1.streaming./cell-1.streaming./')"
fi

echo ""
echo "============================================================"
echo "  OCI Setup Complete"
echo "============================================================"
echo ""
echo "  Resources created in OCI ($REGION):"
echo "  ┌──────────────────────────┬────────────────────────────────────┐"
echo "  │ Resource                 │ Name / Value                       │"
echo "  ├──────────────────────────┼────────────────────────────────────┤"
echo "  │ Stream Pool              │ $STREAM_POOL_NAME                  │"
echo "  │ Stream                   │ $STREAM_NAME                       │"
echo "  │ Kafka Bootstrap          │ $KAFKA_ENDPOINT                    │"
echo "  │ Log Analytics Namespace  │ $NAMESPACE                         │"
echo "  │ Log Analytics Log Group  │ $LOG_GROUP_NAME                    │"
echo "  │ Custom Fields            │ 40 GCP-specific fields             │"
echo "  │ JSON Parser              │ $PARSER_NAME (44 mappings)         │"
echo "  │ Log Analytics Source     │ $SOURCE_NAME                       │"
echo "  │ Connector Hub            │ $SCH_NAME                          │"
echo "  └──────────────────────────┴────────────────────────────────────┘"
echo ""
echo "  Pipeline:"
echo "    GCP Cloud Logging → Pub/Sub → Bridge → OCI Stream → SCH → Log Analytics"
echo ""
echo "  Update .env.local with:"
echo "    OCI_STREAM_OCID=$STREAM_ID"
echo "    OCI_STREAM_POOL_ID=$POOL_ID"
[ -n "$MSG_ENDPOINT" ] && echo "    OCI_MESSAGE_ENDPOINT=$MSG_ENDPOINT"
echo "    OCI_LOG_ANALYTICS_NAMESPACE=$NAMESPACE"
echo ""
echo "Next steps:"
echo "  1. Update .env.local with the values above"
echo "  2. Run: python scripts/test_oci_credentials.py"
echo "  3. Run: python -m bridge.main --drain"
echo ""
