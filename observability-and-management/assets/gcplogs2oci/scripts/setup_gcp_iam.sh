#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup_gcp_iam.sh – Create recommended GCP IAM bindings for
#                    gcplogs2oci.
#
# Applies:
#   1) Bridge runtime SA (resource-scoped Pub/Sub least privilege)
#   2) Log Router sink writer (topic publish permission)
#   3) Optional setup principal roles (for automation/bootstrap)
#
# Optional environment variables:
#   GCP_BRIDGE_SA_EMAIL         Override runtime SA email
#   GCP_SETUP_PRINCIPAL         IAM member for setup automation roles
#   GCP_TEST_PUBLISHER_PRINCIPAL IAM member allowed to publish test data
#
# Usage:
#   ./scripts/setup_gcp_iam.sh
#   GCP_SETUP_PRINCIPAL="user:admin@example.com" ./scripts/setup_gcp_iam.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v gcloud >/dev/null 2>&1; then
    echo "ERROR: gcloud CLI is required."
    exit 1
fi

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

PROJECT="${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
TOPIC="${GCP_PUBSUB_TOPIC:-oci-log-export-topic}"
SUBSCRIPTION="${GCP_PUBSUB_SUBSCRIPTION:-fluentd-oci-bridge-sub}"
SINK_NAME="${GCP_LOG_SINK_NAME:-gcp-to-oci-sink}"
SA_NAME="${GCP_SA_NAME:-oci-log-shipper-sa}"
DEFAULT_SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
SA_EMAIL="${GCP_BRIDGE_SA_EMAIL:-$DEFAULT_SA_EMAIL}"
SETUP_PRINCIPAL="${GCP_SETUP_PRINCIPAL:-}"
TEST_PUBLISHER_PRINCIPAL="${GCP_TEST_PUBLISHER_PRINCIPAL:-}"

if [ -n "$SETUP_PRINCIPAL" ] && [[ "$SETUP_PRINCIPAL" != *:* ]]; then
    echo "ERROR: GCP_SETUP_PRINCIPAL must be in IAM member format (e.g. user:alice@example.com)."
    exit 1
fi

if [ -n "$TEST_PUBLISHER_PRINCIPAL" ] && [[ "$TEST_PUBLISHER_PRINCIPAL" != *:* ]]; then
    echo "ERROR: GCP_TEST_PUBLISHER_PRINCIPAL must be in IAM member format."
    exit 1
fi

gcloud config set project "$PROJECT" >/dev/null

UPDATED=0
SKIPPED=0
CREATED=0

add_project_binding() {
    local member="$1"
    local role="$2"
    gcloud projects add-iam-policy-binding "$PROJECT" \
        --member="$member" \
        --role="$role" \
        --condition=None \
        --quiet >/dev/null
    UPDATED=$((UPDATED + 1))
}

add_topic_binding() {
    local member="$1"
    local role="$2"
    gcloud pubsub topics add-iam-policy-binding "$TOPIC" \
        --project="$PROJECT" \
        --member="$member" \
        --role="$role" \
        --condition=None \
        --quiet >/dev/null
    UPDATED=$((UPDATED + 1))
}

add_subscription_binding() {
    local member="$1"
    local role="$2"
    gcloud pubsub subscriptions add-iam-policy-binding "$SUBSCRIPTION" \
        --project="$PROJECT" \
        --member="$member" \
        --role="$role" \
        --condition=None \
        --quiet >/dev/null
    UPDATED=$((UPDATED + 1))
}

echo "============================================================"
echo "  GCP IAM Setup for gcplogs2oci"
echo "============================================================"
echo "  Project:           $PROJECT"
echo "  Topic:             $TOPIC"
echo "  Subscription:      $SUBSCRIPTION"
echo "  Sink:              $SINK_NAME"
echo "  Bridge SA:         $SA_EMAIL"
[ -n "$SETUP_PRINCIPAL" ] && echo "  Setup principal:   $SETUP_PRINCIPAL"
echo "============================================================"
echo ""

# 1) Ensure bridge service account exists (default SA only)
if gcloud iam service-accounts describe "$SA_EMAIL" --project "$PROJECT" >/dev/null 2>&1; then
    echo "1/4  Bridge service account exists: $SA_EMAIL"
else
    if [ "$SA_EMAIL" != "$DEFAULT_SA_EMAIL" ]; then
        echo "1/4  WARNING: Custom bridge SA not found: $SA_EMAIL"
        echo "     Create it manually or unset GCP_BRIDGE_SA_EMAIL."
        SKIPPED=$((SKIPPED + 1))
    else
        echo "1/4  Creating bridge service account: $SA_NAME"
        gcloud iam service-accounts create "$SA_NAME" \
            --project "$PROJECT" \
            --display-name "OCI Log Shipper Service Account" >/dev/null
        CREATED=$((CREATED + 1))
    fi
fi

# 2) Runtime Pub/Sub least privilege bindings
echo "2/4  Applying bridge runtime Pub/Sub bindings..."
if ! gcloud pubsub subscriptions describe "$SUBSCRIPTION" --project "$PROJECT" >/dev/null 2>&1; then
    echo "     WARNING: Subscription not found ($SUBSCRIPTION). Skipping subscription IAM bindings."
    SKIPPED=$((SKIPPED + 1))
else
    add_subscription_binding "serviceAccount:$SA_EMAIL" "roles/pubsub.subscriber"
    add_subscription_binding "serviceAccount:$SA_EMAIL" "roles/pubsub.viewer"
    echo "     Added: roles/pubsub.subscriber + roles/pubsub.viewer on subscription"
fi

if ! gcloud pubsub topics describe "$TOPIC" --project "$PROJECT" >/dev/null 2>&1; then
    echo "     WARNING: Topic not found ($TOPIC). Skipping topic IAM bindings."
    SKIPPED=$((SKIPPED + 1))
else
    add_topic_binding "serviceAccount:$SA_EMAIL" "roles/pubsub.viewer"
    echo "     Added: roles/pubsub.viewer on topic"
fi

# 3) Sink writer publish permission on the topic
echo "3/4  Applying Log Router sink writer permissions..."
if ! gcloud logging sinks describe "$SINK_NAME" --project "$PROJECT" >/dev/null 2>&1; then
    echo "     WARNING: Sink not found ($SINK_NAME). Skipping sink-writer IAM binding."
    SKIPPED=$((SKIPPED + 1))
else
    if ! gcloud pubsub topics describe "$TOPIC" --project "$PROJECT" >/dev/null 2>&1; then
        echo "     WARNING: Topic not found ($TOPIC). Skipping sink-writer IAM binding."
        SKIPPED=$((SKIPPED + 1))
    else
        SINK_MEMBER="$(gcloud logging sinks describe "$SINK_NAME" --project "$PROJECT" --format='value(writerIdentity)')"
        if [ -z "$SINK_MEMBER" ] || [ "$SINK_MEMBER" = "None" ]; then
            echo "     WARNING: Could not resolve sink writerIdentity. Skipping."
            SKIPPED=$((SKIPPED + 1))
        else
            add_topic_binding "$SINK_MEMBER" "roles/pubsub.publisher"
            echo "     Added: roles/pubsub.publisher on topic for $SINK_MEMBER"
        fi
    fi
fi

# 4) Optional setup/test principals
echo "4/4  Applying optional setup/test principal bindings..."
if [ -n "$SETUP_PRINCIPAL" ]; then
    # Required by scripts/setup_gcp.sh operations.
    for role in \
        roles/serviceusage.serviceUsageAdmin \
        roles/pubsub.admin \
        roles/logging.configWriter \
        roles/iam.serviceAccountAdmin \
        roles/iam.serviceAccountKeyAdmin \
        roles/resourcemanager.projectIamAdmin; do
        add_project_binding "$SETUP_PRINCIPAL" "$role"
    done
    echo "     Added setup roles for $SETUP_PRINCIPAL"
else
    echo "     Skipped setup principal roles (GCP_SETUP_PRINCIPAL not set)."
    SKIPPED=$((SKIPPED + 1))
fi

if [ -n "$TEST_PUBLISHER_PRINCIPAL" ]; then
    if gcloud pubsub topics describe "$TOPIC" --project "$PROJECT" >/dev/null 2>&1; then
        add_topic_binding "$TEST_PUBLISHER_PRINCIPAL" "roles/pubsub.publisher"
        echo "     Added test publish role for $TEST_PUBLISHER_PRINCIPAL"
    else
        echo "     WARNING: Topic not found ($TOPIC). Skipping test publisher binding."
        SKIPPED=$((SKIPPED + 1))
    fi
else
    echo "     Skipped test publisher role (GCP_TEST_PUBLISHER_PRINCIPAL not set)."
    SKIPPED=$((SKIPPED + 1))
fi

echo ""
echo "============================================================"
echo "  GCP IAM Setup Complete"
echo "============================================================"
echo "  Created resources: $CREATED"
echo "  IAM bindings applied: $UPDATED"
echo "  Skipped items: $SKIPPED"
echo ""
echo "Recommended next steps:"
echo "  1. Run ./scripts/setup_gcp.sh to ensure topic/subscription/sink exist"
echo "  2. Validate with: python scripts/test_gcp_credentials.py"
echo ""
