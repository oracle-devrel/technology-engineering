#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# status.sh – Audit the current state of all gcplogs2oci resources
#
# Checks the existence and health of every resource created by
# setup_gcp.sh and setup_oci.sh, plus credentials and bridge config.
#
# Usage:
#   ./scripts/status.sh
# ─────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment
ENV_FILE=""
if [ -f "$PROJECT_DIR/.env.local" ]; then
    set -a; source "$PROJECT_DIR/.env.local"; set +a
    ENV_FILE="$PROJECT_DIR/.env.local"
elif [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
    ENV_FILE="$PROJECT_DIR/.env"
fi

# Counters
PASS=0
FAIL=0
WARN=0

# ── Helpers ──────────────────────────────────────────────────
mask() {
    local val="$1" keep="${2:-6}"
    if [ -z "$val" ]; then echo ""; return; fi
    if [ ${#val} -le "$keep" ]; then echo "***"; return; fi
    echo "${val:0:$keep}...***"
}

check_pass() { echo "    [OK]   $1"; ((PASS++)); }
check_fail() { echo "    [FAIL] $1"; ((FAIL++)); }
check_warn() { echo "    [WARN] $1"; ((WARN++)); }
check_skip() { echo "    [SKIP] $1"; }

separator() {
    echo ""
    echo "  ── $1 ──"
}

echo ""
echo "============================================================"
echo "  gcplogs2oci – Infrastructure Status Report"
echo "============================================================"
echo ""

# ── 0. Local Environment ─────────────────────────────────────
separator "Local Environment"

if [ -n "$ENV_FILE" ]; then
    check_pass "Environment file: $ENV_FILE"
else
    check_fail "No .env.local or .env found"
fi

if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    if python3 -c "import oci" 2>/dev/null; then
        check_pass "Python OCI SDK installed"
    else
        check_warn "Python OCI SDK not installed (pip install oci)"
    fi
    if python3 -c "from google.cloud import pubsub_v1" 2>/dev/null; then
        check_pass "Python GCP Pub/Sub SDK installed"
    else
        check_warn "Python GCP Pub/Sub SDK not installed (pip install google-cloud-pubsub)"
    fi
fi

if command -v gcloud &>/dev/null; then
    GCLOUD_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)
    if [ -n "$GCLOUD_ACCOUNT" ]; then
        check_pass "gcloud CLI authenticated: $(mask "$GCLOUD_ACCOUNT" 10)"
    else
        check_warn "gcloud CLI installed but not authenticated"
    fi
else
    check_fail "gcloud CLI not installed"
fi

if command -v oci &>/dev/null; then
    check_pass "OCI CLI installed"
else
    check_fail "OCI CLI not installed"
fi

# ── 1. GCP Resources ─────────────────────────────────────────
separator "GCP Resources"

PROJECT="${GCP_PROJECT_ID:-}"
TOPIC="${GCP_PUBSUB_TOPIC:-oci-log-export-topic}"
SUBSCRIPTION="${GCP_PUBSUB_SUBSCRIPTION:-fluentd-oci-bridge-sub}"
SINK_NAME="${GCP_LOG_SINK_NAME:-gcp-to-oci-sink}"
SA_NAME="${GCP_SA_NAME:-oci-log-shipper-sa}"

if [ -z "$PROJECT" ]; then
    check_fail "GCP_PROJECT_ID not set"
    echo "         Skipping GCP resource checks."
else
    check_pass "GCP Project: $PROJECT"
    gcloud config set project "$PROJECT" &>/dev/null

    # Topic
    if gcloud pubsub topics describe "$TOPIC" &>/dev/null; then
        check_pass "Pub/Sub Topic: $TOPIC"
    else
        check_fail "Pub/Sub Topic: $TOPIC (not found)"
    fi

    # Subscription
    if gcloud pubsub subscriptions describe "$SUBSCRIPTION" &>/dev/null; then
        SUB_INFO=$(gcloud pubsub subscriptions describe "$SUBSCRIPTION" --format='value(ackDeadlineSeconds,messageRetentionDuration)' 2>/dev/null || true)
        check_pass "Pub/Sub Subscription: $SUBSCRIPTION"
    else
        check_fail "Pub/Sub Subscription: $SUBSCRIPTION (not found)"
    fi

    # Sink
    if gcloud logging sinks describe "$SINK_NAME" &>/dev/null; then
        SINK_FILTER=$(gcloud logging sinks describe "$SINK_NAME" --format='value(filter)' 2>/dev/null || true)
        check_pass "Log Router Sink: $SINK_NAME (filter: $SINK_FILTER)"
    else
        check_fail "Log Router Sink: $SINK_NAME (not found)"
    fi

    # Service Account
    SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
    if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
        check_pass "Service Account: $SA_EMAIL"
    else
        check_fail "Service Account: $SA_EMAIL (not found)"
    fi

    # Local key file
    KEY_FILE="$PROJECT_DIR/gcp-sa-key.json"
    if [ -f "$KEY_FILE" ]; then
        check_pass "SA Key File: $KEY_FILE"
    else
        check_warn "SA Key File: $KEY_FILE (not found — using ADC?)"
    fi
fi

# ── 2. OCI Credentials ──────────────────────────────────────
separator "OCI Credentials"

OCI_VARS=("OCI_USER_OCID" "OCI_FINGERPRINT" "OCI_TENANCY_OCID" "OCI_REGION" "OCI_COMPARTMENT_OCID")
for var in "${OCI_VARS[@]}"; do
    val="${!var:-}"
    if [ -n "$val" ]; then
        check_pass "$var: $(mask "$val")"
    else
        check_fail "$var: not set"
    fi
done

# Key file or content
if [ -n "${OCI_KEY_FILE:-}" ]; then
    EXPANDED_KEY="${OCI_KEY_FILE/#\~/$HOME}"
    if [ -f "$EXPANDED_KEY" ]; then
        check_pass "OCI_KEY_FILE: $OCI_KEY_FILE (exists)"
    else
        check_fail "OCI_KEY_FILE: $OCI_KEY_FILE (file not found)"
    fi
elif [ -n "${OCI_KEY_CONTENT:-}" ]; then
    check_pass "OCI_KEY_CONTENT: set (inline PEM)"
else
    check_fail "OCI_KEY_FILE / OCI_KEY_CONTENT: neither set"
fi

# ── 3. OCI Resources ─────────────────────────────────────────
separator "OCI Resources"

COMPARTMENT="${OCI_COMPARTMENT_OCID:-}"
REGION="${OCI_REGION:-}"
STREAM_POOL_NAME="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
STREAM_NAME="${OCI_STREAM_NAME:-gcp-inbound-stream}"
LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-GCPLogs}"
SCH_NAME="${OCI_SCH_NAME:-GCP-Stream-to-LogAnalytics}"
NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"

if [ -z "$COMPARTMENT" ] || [ -z "$REGION" ]; then
    check_fail "OCI_COMPARTMENT_OCID or OCI_REGION not set"
    echo "         Skipping OCI resource checks."
else
    # Auto-detect namespace
    if [ -z "$NAMESPACE" ]; then
        NAMESPACE=$(oci log-analytics namespace list \
            --compartment-id "$COMPARTMENT" \
            --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
        if [ -z "$NAMESPACE" ] || [ "$NAMESPACE" = "null" ]; then
            check_fail "Log Analytics namespace: not detected (is Log Analytics onboarded?)"
            NAMESPACE=""
        else
            check_pass "Log Analytics namespace: $NAMESPACE (auto-detected)"
        fi
    else
        check_pass "Log Analytics namespace: $NAMESPACE"
    fi

    # Stream Pool
    POOL_ID=$(oci streaming admin stream-pool list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_POOL_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)
    if [ -n "$POOL_ID" ] && [ "$POOL_ID" != "null" ]; then
        check_pass "Stream Pool: $STREAM_POOL_NAME (ACTIVE)"
    else
        check_fail "Stream Pool: $STREAM_POOL_NAME (not found)"
    fi

    # Stream
    if [ -n "${OCI_STREAM_OCID:-}" ]; then
        STREAM_STATE=$(oci streaming admin stream get \
            --stream-id "$OCI_STREAM_OCID" \
            --query 'data."lifecycle-state"' --raw-output 2>/dev/null || true)
        if [ -n "$STREAM_STATE" ] && [ "$STREAM_STATE" != "null" ]; then
            if [ "$STREAM_STATE" = "ACTIVE" ]; then
                check_pass "Stream: $(mask "$OCI_STREAM_OCID" 20) ($STREAM_STATE)"
            else
                check_warn "Stream: $(mask "$OCI_STREAM_OCID" 20) ($STREAM_STATE)"
            fi
        else
            check_fail "Stream: OCI_STREAM_OCID set but stream not found"
        fi
    else
        STREAM_ID=$(oci streaming admin stream list \
            --compartment-id "$COMPARTMENT" \
            --name "$STREAM_NAME" \
            --lifecycle-state ACTIVE \
            --query 'data[0].id' --raw-output 2>/dev/null || true)
        if [ -n "$STREAM_ID" ] && [ "$STREAM_ID" != "null" ]; then
            check_pass "Stream: $STREAM_NAME (ACTIVE)"
        else
            check_fail "Stream: $STREAM_NAME (not found)"
        fi
    fi

    # Log Analytics Log Group
    if [ -n "$NAMESPACE" ]; then
        LG_ID=$(oci log-analytics log-group list \
            --compartment-id "$COMPARTMENT" \
            --namespace-name "$NAMESPACE" \
            --query "data.items[?\"display-name\"=='$LOG_GROUP_NAME'].id | [0]" \
            --raw-output 2>/dev/null || true)
        if [ -n "$LG_ID" ] && [ "$LG_ID" != "null" ] && [ "$LG_ID" != "None" ]; then
            check_pass "Log Analytics Log Group: $LOG_GROUP_NAME"
        else
            check_fail "Log Analytics Log Group: $LOG_GROUP_NAME (not found)"
        fi

        # Parser
        PARSER_EXISTS=$(oci log-analytics parser get-parser \
            --namespace-name "$NAMESPACE" \
            --parser-name "gcpCloudLoggingJsonParser" \
            --query 'data.name' --raw-output 2>/dev/null || true)
        if [ -n "$PARSER_EXISTS" ] && [ "$PARSER_EXISTS" != "null" ] && [ "$PARSER_EXISTS" != "None" ]; then
            FIELD_COUNT=$(oci log-analytics parser get-parser \
                --namespace-name "$NAMESPACE" \
                --parser-name "gcpCloudLoggingJsonParser" \
                --query 'length(data."field-maps")' --raw-output 2>/dev/null || echo "?")
            check_pass "Log Analytics Parser: gcpCloudLoggingJsonParser ($FIELD_COUNT field mappings)"
        else
            check_fail "Log Analytics Parser: gcpCloudLoggingJsonParser (not found)"
        fi

        # Source
        SOURCE_EXISTS=$(oci log-analytics source list-sources \
            --namespace-name "$NAMESPACE" \
            --compartment-id "$COMPARTMENT" \
            --name "GCP Cloud Logging Logs" \
            --is-system ALL \
            --query 'data.items[0].name' --raw-output 2>/dev/null || true)
        if [ -n "$SOURCE_EXISTS" ] && [ "$SOURCE_EXISTS" != "null" ] && [ "$SOURCE_EXISTS" != "None" ]; then
            check_pass "Log Analytics Source: GCP Cloud Logging Logs"
        else
            check_fail "Log Analytics Source: GCP Cloud Logging Logs (not found)"
        fi
    else
        check_skip "Log Analytics resources (no namespace)"
    fi

    # Connector Hub
    SCH_ID=$(oci sch service-connector list \
        --compartment-id "$COMPARTMENT" \
        --display-name "$SCH_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data.items[0].id' --raw-output 2>/dev/null || true)
    if [ -n "$SCH_ID" ] && [ "$SCH_ID" != "null" ] && [ "$SCH_ID" != "None" ]; then
        check_pass "Connector Hub: $SCH_NAME (ACTIVE)"
    else
        # Check if it exists but in non-ACTIVE state
        SCH_ANY=$(oci sch service-connector list \
            --compartment-id "$COMPARTMENT" \
            --display-name "$SCH_NAME" \
            --query 'data.items[0]."lifecycle-state"' --raw-output 2>/dev/null || true)
        if [ -n "$SCH_ANY" ] && [ "$SCH_ANY" != "null" ] && [ "$SCH_ANY" != "None" ]; then
            check_warn "Connector Hub: $SCH_NAME ($SCH_ANY)"
        else
            check_fail "Connector Hub: $SCH_NAME (not found)"
        fi
    fi
fi

# ── 4. Bridge Configuration ─────────────────────────────────
separator "Bridge Configuration"

BRIDGE_VARS=("OCI_MESSAGE_ENDPOINT" "OCI_STREAM_OCID")
for var in "${BRIDGE_VARS[@]}"; do
    val="${!var:-}"
    if [ -n "$val" ]; then
        check_pass "$var: $(mask "$val" 15)"
    else
        check_fail "$var: not set (needed for bridge runtime)"
    fi
done

for var in MAX_BATCH_SIZE MAX_BATCH_BYTES INACTIVITY_TIMEOUT; do
    val="${!var:-}"
    if [ -n "$val" ]; then
        check_pass "$var: $val"
    else
        check_skip "$var: using default"
    fi
done

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  Status Summary"
echo "============================================================"
echo "    Passed:   $PASS"
echo "    Warnings: $WARN"
echo "    Failed:   $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  All checks passed. Pipeline is ready."
    echo ""
    echo "  Run the bridge:"
    echo "    python -m bridge.main --drain    # test mode"
    echo "    python -m bridge.main            # continuous"
elif [ "$FAIL" -le 3 ]; then
    echo "  Some checks failed. Review the items above."
    echo ""
    echo "  Setup commands:"
    echo "    ./scripts/setup_gcp.sh           # provision GCP resources"
    echo "    ./scripts/setup_oci.sh           # provision OCI resources"
else
    echo "  Multiple checks failed. Run the setup scripts first."
    echo ""
    echo "  Quick start:"
    echo "    cp .env.example .env.local       # configure credentials"
    echo "    ./scripts/setup_gcp.sh           # provision GCP"
    echo "    ./scripts/setup_oci.sh           # provision OCI"
fi

echo ""
exit "$FAIL"
