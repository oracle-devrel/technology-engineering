#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# drain_pubsub_to_oci.sh – Run the bridge in drain mode
#
# Pulls all pending messages from GCP Pub/Sub, forwards them to
# OCI Streaming, and exits after INACTIVITY_TIMEOUT seconds of
# silence. Useful for ad-hoc backfills and smoke tests.
#
# Usage:
#   ./scripts/drain_pubsub_to_oci.sh
#   ./scripts/drain_pubsub_to_oci.sh --log-level DEBUG
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Activate venv if present
if [ -d ".venv/bin" ]; then
    source .venv/bin/activate
fi

echo "Starting bridge in drain mode..."
python -m bridge.main --drain "$@"
