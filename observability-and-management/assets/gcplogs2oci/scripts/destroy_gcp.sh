#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# destroy_gcp.sh – Remove all GCP resources created by setup_gcp.sh
#
# Deletes (in reverse creation order):
#   1. Log Router Sink
#   2. Pub/Sub Subscription
#   3. Pub/Sub Topic
#   4. Service Account (and IAM bindings)
#   5. Local SA key file
#
# Usage:
#   ./scripts/destroy_gcp.sh           # interactive (with confirmation)
#   ./scripts/destroy_gcp.sh --force   # skip confirmation prompt
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
    echo "ERROR: No .env.local or .env found. Copy .env.example to .env.local and fill in values."
    exit 1
fi

# ── Interactive GCP project selection (same as setup_gcp.sh) ──
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    if [ -t 0 ]; then
        echo "GCP_PROJECT_ID is not set. Detecting available projects..."
        echo ""
        mapfile -t PROJECTS < <(gcloud projects list --format='value(projectId)' --sort-by=projectId 2>/dev/null)
        if [ ${#PROJECTS[@]} -eq 0 ]; then
            echo "ERROR: No GCP projects found. Ensure gcloud is authenticated (gcloud auth login)."
            exit 1
        fi
        echo "  Available GCP Projects:"
        for i in "${!PROJECTS[@]}"; do
            printf "    %d) %s\n" "$((i+1))" "${PROJECTS[$i]}"
        done
        echo ""
        while true; do
            read -rp "  Select a project [1-${#PROJECTS[@]}]: " choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#PROJECTS[@]}" ]; then
                GCP_PROJECT_ID="${PROJECTS[$((choice-1))]}"
                echo "  Selected: $GCP_PROJECT_ID"
                break
            else
                echo "  Invalid selection. Enter a number between 1 and ${#PROJECTS[@]}."
            fi
        done
    else
        echo "ERROR: GCP_PROJECT_ID is required (set in .env.local or export it)."
        exit 1
    fi
fi

PROJECT="$GCP_PROJECT_ID"
TOPIC="${GCP_PUBSUB_TOPIC:-oci-log-export-topic}"
SUBSCRIPTION="${GCP_PUBSUB_SUBSCRIPTION:-fluentd-oci-bridge-sub}"
SINK_NAME="${GCP_LOG_SINK_NAME:-gcp-to-oci-sink}"
SA_NAME="${GCP_SA_NAME:-oci-log-shipper-sa}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
KEY_FILE="$PROJECT_DIR/gcp-sa-key.json"

echo ""
echo "============================================================"
echo "  GCP Destroy for gcplogs2oci"
echo "============================================================"
echo "  Project:      $PROJECT"
echo "  Topic:        $TOPIC"
echo "  Subscription: $SUBSCRIPTION"
echo "  Sink:         $SINK_NAME"
echo "  SA:           $SA_EMAIL"
echo "============================================================"
echo ""

# ── Confirmation ──────────────────────────────────────────────
if [ "$FORCE" = false ]; then
    echo "WARNING: This will permanently delete the above GCP resources."
    read -rp "Continue? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[yY] ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

gcloud config set project "$PROJECT"

DELETED=0
SKIPPED=0

# ── 1. Delete Log Router Sink ─────────────────────────────────
echo "1/5  Deleting Log Router sink: $SINK_NAME"
if gcloud logging sinks describe "$SINK_NAME" &>/dev/null; then
    gcloud logging sinks delete "$SINK_NAME" --quiet
    echo "     Deleted."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 2. Delete Pub/Sub Subscription ────────────────────────────
echo "2/5  Deleting Pub/Sub subscription: $SUBSCRIPTION"
if gcloud pubsub subscriptions describe "$SUBSCRIPTION" &>/dev/null; then
    gcloud pubsub subscriptions delete "$SUBSCRIPTION" --quiet
    echo "     Deleted."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 3. Delete Pub/Sub Topic ──────────────────────────────────
echo "3/5  Deleting Pub/Sub topic: $TOPIC"
if gcloud pubsub topics describe "$TOPIC" &>/dev/null; then
    gcloud pubsub topics delete "$TOPIC" --quiet
    echo "     Deleted."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 4. Delete Service Account ────────────────────────────────
echo "4/5  Deleting service account: $SA_EMAIL"
if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    gcloud iam service-accounts delete "$SA_EMAIL" --quiet
    echo "     Deleted (IAM bindings removed automatically)."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

# ── 5. Delete local key file ─────────────────────────────────
echo "5/5  Removing local SA key file: $KEY_FILE"
if [ -f "$KEY_FILE" ]; then
    rm -f "$KEY_FILE"
    echo "     Removed."
    ((DELETED++))
else
    echo "     Not found, skipping."
    ((SKIPPED++))
fi

echo ""
echo "============================================================"
echo "  GCP Destroy Complete"
echo "============================================================"
echo "  Deleted: $DELETED   Skipped (not found): $SKIPPED"
echo ""
echo "To re-create resources, run: ./scripts/setup_gcp.sh"
echo ""
