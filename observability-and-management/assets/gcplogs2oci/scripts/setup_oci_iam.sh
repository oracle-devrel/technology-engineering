#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup_oci_iam.sh – Create recommended OCI IAM policies for
#                    gcplogs2oci.
#
# Policies:
#   1) Connector Hub runtime policy (always applied)
#   2) Optional setup/operator group policy
#   3) Optional bridge sender group policy
#
# Optional environment variables:
#   OCI_IAM_POLICY_PREFIX   Policy name prefix (default: gcplogs2oci)
#   OCI_IAM_OPERATOR_GROUP  Group that runs setup_oci.sh / destroy_oci.sh
#   OCI_IAM_BRIDGE_GROUP    Group used by bridge OCI API key principal
#
# Usage:
#   ./scripts/setup_oci_iam.sh
#   ./scripts/setup_oci_iam.sh --sch-only
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SCH_ONLY=false
while [ $# -gt 0 ]; do
    case "$1" in
        --sch-only) SCH_ONLY=true ;;
        *)
            echo "ERROR: Unknown argument: $1"
            echo "Usage: ./scripts/setup_oci_iam.sh [--sch-only]"
            exit 1
            ;;
    esac
    shift
done

if ! command -v oci >/dev/null 2>&1; then
    echo "ERROR: oci CLI is required."
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

TENANCY_OCID="${OCI_TENANCY_OCID:?OCI_TENANCY_OCID is required}"
COMPARTMENT_OCID="${OCI_COMPARTMENT_OCID:?OCI_COMPARTMENT_OCID is required}"
POLICY_PREFIX="${OCI_IAM_POLICY_PREFIX:-gcplogs2oci}"
OPERATOR_GROUP="${OCI_IAM_OPERATOR_GROUP:-}"
BRIDGE_GROUP="${OCI_IAM_BRIDGE_GROUP:-}"

UPDATED=0
CREATED=0
SKIPPED=0

to_json_array() {
    python3 - "$@" <<'PYEOF'
import json
import sys

print(json.dumps(sys.argv[1:]))
PYEOF
}

upsert_policy() {
    local policy_name="$1"
    local description="$2"
    shift 2
    local statements=("$@")

    local statements_json
    statements_json="$(to_json_array "${statements[@]}")"

    local policy_id
    policy_id="$(oci iam policy list \
        --compartment-id "$TENANCY_OCID" \
        --name "$policy_name" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || true)"

    if [ -n "$policy_id" ] && [ "$policy_id" != "null" ] && [ "$policy_id" != "None" ]; then
        oci iam policy update \
            --policy-id "$policy_id" \
            --description "$description" \
            --statements "$statements_json" \
            --force >/dev/null
        echo "  Updated policy: $policy_name"
        UPDATED=$((UPDATED + 1))
    else
        oci iam policy create \
            --compartment-id "$TENANCY_OCID" \
            --name "$policy_name" \
            --description "$description" \
            --statements "$statements_json" >/dev/null
        echo "  Created policy: $policy_name"
        CREATED=$((CREATED + 1))
    fi
}

echo "============================================================"
echo "  OCI IAM Setup for gcplogs2oci"
echo "============================================================"
echo "  Tenancy:       ${TENANCY_OCID:0:30}..."
echo "  Compartment:   ${COMPARTMENT_OCID:0:30}..."
echo "  Policy prefix: $POLICY_PREFIX"
if [ -n "$OPERATOR_GROUP" ]; then
    echo "  Operator group: $OPERATOR_GROUP"
fi
if [ -n "$BRIDGE_GROUP" ]; then
    echo "  Bridge group:   $BRIDGE_GROUP"
fi
[ "$SCH_ONLY" = true ] && echo "  Mode: SCH policy only"
echo "============================================================"
echo ""

# 1) Connector Hub runtime policy (required by pipeline)
SCH_POLICY_NAME="${POLICY_PREFIX}-sch-pipeline"
SCH_POLICY_DESC="Allow Connector Hub to consume OCI Streaming and write to Log Analytics for gcplogs2oci"
SCH_STATEMENTS=(
    "Allow any-user to use stream-pull in compartment id '${COMPARTMENT_OCID}' where all {request.principal.type='serviceconnector'}"
    "Allow any-user to use stream-consume in compartment id '${COMPARTMENT_OCID}' where all {request.principal.type='serviceconnector'}"
    "Allow any-user to use log-analytics-log-group in compartment id '${COMPARTMENT_OCID}' where all {request.principal.type='serviceconnector'}"
)
upsert_policy "$SCH_POLICY_NAME" "$SCH_POLICY_DESC" "${SCH_STATEMENTS[@]}"

if [ "$SCH_ONLY" = false ]; then
    # 2) Setup operator policy (optional but recommended)
    if [ -n "$OPERATOR_GROUP" ]; then
        OPERATOR_POLICY_NAME="${POLICY_PREFIX}-setup-operator"
        OPERATOR_POLICY_DESC="Allow setup operators to provision gcplogs2oci OCI resources"
        OPERATOR_STATEMENTS=(
            "Allow group ${OPERATOR_GROUP} to manage stream-pools in compartment id '${COMPARTMENT_OCID}'"
            "Allow group ${OPERATOR_GROUP} to manage streams in compartment id '${COMPARTMENT_OCID}'"
            "Allow group ${OPERATOR_GROUP} to manage serviceconnectors in compartment id '${COMPARTMENT_OCID}'"
            "Allow group ${OPERATOR_GROUP} to manage log-analytics-log-group in compartment id '${COMPARTMENT_OCID}'"
            "Allow group ${OPERATOR_GROUP} to manage loganalytics-features-family in compartment id '${COMPARTMENT_OCID}'"
        )
        upsert_policy "$OPERATOR_POLICY_NAME" "$OPERATOR_POLICY_DESC" "${OPERATOR_STATEMENTS[@]}"
    else
        echo "  Skipped operator policy (OCI_IAM_OPERATOR_GROUP not set)."
        SKIPPED=$((SKIPPED + 1))
    fi

    # 3) Bridge sender policy (optional; required when bridge uses OCI API key)
    if [ -n "$BRIDGE_GROUP" ]; then
        BRIDGE_POLICY_NAME="${POLICY_PREFIX}-bridge-stream-push"
        BRIDGE_POLICY_DESC="Allow bridge runtime principal to push messages to OCI Streaming"
        BRIDGE_STATEMENTS=(
            "Allow group ${BRIDGE_GROUP} to use stream-push in compartment id '${COMPARTMENT_OCID}'"
            "Allow group ${BRIDGE_GROUP} to inspect streams in compartment id '${COMPARTMENT_OCID}'"
        )
        upsert_policy "$BRIDGE_POLICY_NAME" "$BRIDGE_POLICY_DESC" "${BRIDGE_STATEMENTS[@]}"
    else
        echo "  Skipped bridge policy (OCI_IAM_BRIDGE_GROUP not set)."
        SKIPPED=$((SKIPPED + 1))
    fi
fi

echo ""
echo "============================================================"
echo "  OCI IAM Setup Complete"
echo "============================================================"
echo "  Policies created: $CREATED"
echo "  Policies updated: $UPDATED"
echo "  Skipped: $SKIPPED"
echo ""
echo "Recommended next steps:"
echo "  1. Run ./scripts/setup_oci.sh"
echo "  2. Validate with: python scripts/test_oci_credentials.py"
echo ""
