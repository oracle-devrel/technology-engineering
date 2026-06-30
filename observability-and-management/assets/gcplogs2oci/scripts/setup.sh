#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup.sh – Unified end-to-end provisioning wizard
#
# Orchestrates the full GCP + OCI pipeline setup by checking
# prerequisites, probing existing resources, delegating to
# setup_gcp.sh / setup_oci.sh, validating credentials, and
# optionally running an end-to-end test.
#
# Usage:
#   ./scripts/setup.sh                        # interactive wizard
#   ./scripts/setup.sh --auto                 # non-interactive
#   ./scripts/setup.sh --auto --skip-tests    # non-interactive, no tests
#   ./scripts/setup.sh --dry-run              # show plan, change nothing
#   ./scripts/setup.sh --auto --e2e           # include end-to-end test
# ─────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Step 0: Parse flags ──────────────────────────────────────
AUTO=false
SKIP_TESTS=false
DRY_RUN=false
FORCE=false
E2E=false

while [ $# -gt 0 ]; do
    case "$1" in
        --auto)       AUTO=true ;;
        --skip-tests) SKIP_TESTS=true ;;
        --dry-run)    DRY_RUN=true ;;
        --force)      FORCE=true ;;
        --e2e)        E2E=true ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto         Non-interactive mode (skip confirmations, use defaults)"
            echo "  --skip-tests   Skip credential validation and e2e test"
            echo "  --dry-run      Show what would be done without executing"
            echo "  --force        Pass --force to child scripts"
            echo "  --e2e          Include end-to-end test (publish + drain)"
            echo "  -h, --help     Show this help"
            exit 0
            ;;
        *)
            echo "Unknown flag: $1 (use --help for usage)"
            exit 1
            ;;
    esac
    shift
done

# ── Color support ─────────────────────────────────────────────
if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    C_GREEN=$(tput setaf 2)
    C_RED=$(tput setaf 1)
    C_YELLOW=$(tput setaf 3)
    C_DIM=$(tput dim)
    C_BOLD=$(tput bold)
    C_RESET=$(tput sgr0)
else
    C_GREEN="" C_RED="" C_YELLOW="" C_DIM="" C_BOLD="" C_RESET=""
fi

# ── Helpers ───────────────────────────────────────────────────
TOTAL_STEPS=10
ERRORS=0

step_header() {
    local n="$1" title="$2"
    echo ""
    echo "${C_BOLD}  [$n/$TOTAL_STEPS] $title${C_RESET}"
    echo "  ────────────────────────────────────────────────────"
}

status_ok()   { echo "    ${C_GREEN}✓${C_RESET} $1"; }
status_fail() { echo "    ${C_RED}✗${C_RESET} $1"; }
status_skip() { echo "    ${C_DIM}–${C_RESET} $1"; }
status_warn() { echo "    ${C_YELLOW}!${C_RESET} $1"; }

ask_yn() {
    local prompt="$1" default="${2:-n}"
    if $AUTO; then
        [[ "$default" =~ ^[yY] ]] && return 0 || return 1
    fi
    local suffix
    if [[ "$default" =~ ^[yY] ]]; then suffix="[Y/n]"; else suffix="[y/N]"; fi
    read -rp "    $prompt $suffix: " answer
    answer="${answer:-$default}"
    [[ "$answer" =~ ^[yY] ]]
}

reload_env() {
    if [ -f "$PROJECT_DIR/.env.local" ]; then
        set -a; source "$PROJECT_DIR/.env.local"; set +a
    elif [ -f "$PROJECT_DIR/.env" ]; then
        set -a; source "$PROJECT_DIR/.env"; set +a
    fi
}

run_child() {
    local script="$1"
    shift
    local args=("$@")
    if $FORCE; then args+=(--force); fi

    if $DRY_RUN; then
        echo "    ${C_DIM}[dry-run] Would run: $script ${args[*]+"${args[*]}"}${C_RESET}"
        return 0
    fi

    echo ""
    if $AUTO; then
        "$script" ${args[@]+"${args[@]}"} < /dev/null
    else
        "$script" ${args[@]+"${args[@]}"}
    fi
}

# ── Banner ────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  gcplogs2oci – Unified Setup Wizard"
echo "============================================================"
flags=""
$AUTO       && flags+="auto "
$DRY_RUN    && flags+="dry-run "
$SKIP_TESTS && flags+="skip-tests "
$FORCE      && flags+="force "
$E2E        && flags+="e2e "
if [ -n "$flags" ]; then
    echo "  Flags: $flags"
fi
echo ""

# ══════════════════════════════════════════════════════════════
#  [1/10] Check prerequisites
# ══════════════════════════════════════════════════════════════
step_header 1 "Check prerequisites"

PREREQ_FAIL=0

for tool in gcloud oci python3 jq; do
    if command -v "$tool" &>/dev/null; then
        ver=""
        case "$tool" in
            python3) ver="$(python3 --version 2>&1 | awk '{print $2}')" ;;
            gcloud)  ver="$(gcloud version 2>/dev/null | head -1 | awk '{print $NF}')" ;;
            jq)      ver="$(jq --version 2>/dev/null)" ;;
        esac
        status_ok "$tool${ver:+ ($ver)}"
    else
        status_fail "$tool – not installed"
        ((PREREQ_FAIL++))
    fi
done

if python3 -c "import oci" 2>/dev/null; then
    status_ok "Python OCI SDK"
else
    status_fail "Python OCI SDK – pip install oci"
    ((PREREQ_FAIL++))
fi

if python3 -c "from google.cloud import pubsub_v1" 2>/dev/null; then
    status_ok "Python GCP Pub/Sub SDK"
else
    status_fail "Python GCP Pub/Sub SDK – pip install google-cloud-pubsub"
    ((PREREQ_FAIL++))
fi

if [ "$PREREQ_FAIL" -gt 0 ]; then
    echo ""
    echo "    ${C_RED}$PREREQ_FAIL prerequisite(s) missing. Install them and re-run.${C_RESET}"
    exit 1
fi

# ══════════════════════════════════════════════════════════════
#  [2/10] Check / configure .env.local
# ══════════════════════════════════════════════════════════════
step_header 2 "Check / configure .env.local"

if [ -f "$PROJECT_DIR/.env.local" ]; then
    status_ok ".env.local exists"
else
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        if $DRY_RUN; then
            echo "    ${C_DIM}[dry-run] Would copy .env.example → .env.local${C_RESET}"
        else
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env.local"
            status_ok "Copied .env.example → .env.local"
            if ! $AUTO; then
                echo ""
                echo "    ${C_YELLOW}Edit .env.local with your credentials, then re-run this script.${C_RESET}"
                exit 0
            fi
        fi
    else
        status_fail ".env.example not found – cannot bootstrap config"
        exit 1
    fi
fi

reload_env

echo ""
echo "    Key variables:"
for var in GCP_PROJECT_ID GCP_PUBSUB_TOPIC GCP_PUBSUB_SUBSCRIPTION \
           OCI_COMPARTMENT_OCID OCI_REGION OCI_STREAM_OCID; do
    val="${!var:-}"
    if [ -n "$val" ]; then
        status_ok "$var"
    else
        status_warn "$var – not set"
    fi
done

# ══════════════════════════════════════════════════════════════
#  [3/10] Check GCP authentication
# ══════════════════════════════════════════════════════════════
step_header 3 "Check GCP authentication"

GCP_ACCOUNT=""
if command -v gcloud &>/dev/null; then
    GCP_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)
fi

if [ -n "$GCP_ACCOUNT" ]; then
    status_ok "Authenticated as: $GCP_ACCOUNT"
else
    status_fail "No active gcloud account (run: gcloud auth login)"
    ((ERRORS++))
fi

# ══════════════════════════════════════════════════════════════
#  [4/10] Probe & provision GCP resources
# ══════════════════════════════════════════════════════════════
step_header 4 "Probe & provision GCP resources"

PROJECT="${GCP_PROJECT_ID:-}"
TOPIC="${GCP_PUBSUB_TOPIC:-oci-log-export-topic}"
SUBSCRIPTION="${GCP_PUBSUB_SUBSCRIPTION:-fluentd-oci-bridge-sub}"
SINK_NAME="${GCP_LOG_SINK_NAME:-gcp-to-oci-sink}"
SA_NAME="${GCP_SA_NAME:-oci-log-shipper-sa}"

GCP_MISSING=0

if [ -z "$PROJECT" ]; then
    status_fail "GCP_PROJECT_ID not set – cannot probe"
    ((ERRORS++))
    GCP_MISSING=99
else
    gcloud config set project "$PROJECT" &>/dev/null 2>&1 || true

    if gcloud pubsub topics describe "$TOPIC" &>/dev/null 2>&1; then
        status_ok "Pub/Sub Topic: $TOPIC"
    else
        status_fail "Pub/Sub Topic: $TOPIC"
        ((GCP_MISSING++))
    fi

    if gcloud pubsub subscriptions describe "$SUBSCRIPTION" &>/dev/null 2>&1; then
        status_ok "Pub/Sub Subscription: $SUBSCRIPTION"
    else
        status_fail "Pub/Sub Subscription: $SUBSCRIPTION"
        ((GCP_MISSING++))
    fi

    if gcloud logging sinks describe "$SINK_NAME" &>/dev/null 2>&1; then
        status_ok "Log Router Sink: $SINK_NAME"
    else
        status_fail "Log Router Sink: $SINK_NAME"
        ((GCP_MISSING++))
    fi

    SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
    if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null 2>&1; then
        status_ok "Service Account: $SA_EMAIL"
    else
        status_fail "Service Account: $SA_EMAIL"
        ((GCP_MISSING++))
    fi

    KEY_FILE="$PROJECT_DIR/gcp-sa-key.json"
    if [ -f "$KEY_FILE" ]; then
        status_ok "SA Key File: $KEY_FILE"
    else
        status_fail "SA Key File: $KEY_FILE"
        ((GCP_MISSING++))
    fi
fi

if [ "$GCP_MISSING" -gt 0 ] && [ "$GCP_MISSING" -ne 99 ]; then
    echo ""
    if ask_yn "Create missing GCP resources via setup_gcp.sh?" "y"; then
        if run_child "$SCRIPT_DIR/setup_gcp.sh"; then
            status_ok "setup_gcp.sh completed"
            reload_env
        else
            status_fail "setup_gcp.sh failed"
            ((ERRORS++))
            if ! $AUTO && ! ask_yn "Continue anyway?" "n"; then
                exit 1
            fi
        fi
    else
        status_skip "GCP provisioning skipped"
    fi
elif [ "$GCP_MISSING" -eq 0 ] && [ -n "$PROJECT" ]; then
    echo ""
    status_ok "All GCP resources exist – nothing to create"
fi

# ══════════════════════════════════════════════════════════════
#  [5/10] Validate GCP credentials
# ══════════════════════════════════════════════════════════════
step_header 5 "Validate GCP credentials"

if $SKIP_TESTS; then
    status_skip "Skipped (--skip-tests)"
elif $DRY_RUN; then
    echo "    ${C_DIM}[dry-run] Would run: python3 scripts/test_gcp_credentials.py${C_RESET}"
else
    if python3 "$SCRIPT_DIR/test_gcp_credentials.py"; then
        status_ok "GCP credentials valid"
    else
        status_fail "GCP credential validation failed"
        ((ERRORS++))
        if ! $AUTO && ! ask_yn "Continue anyway?" "n"; then
            exit 1
        fi
    fi
fi

# ══════════════════════════════════════════════════════════════
#  [6/10] Check OCI authentication
# ══════════════════════════════════════════════════════════════
step_header 6 "Check OCI authentication"

if command -v oci &>/dev/null; then
    if oci iam region list --output table &>/dev/null 2>&1; then
        status_ok "OCI CLI authenticated"
    else
        status_fail "OCI CLI auth check failed (run: oci setup config)"
        ((ERRORS++))
    fi
else
    status_fail "OCI CLI not installed"
    ((ERRORS++))
fi

# ══════════════════════════════════════════════════════════════
#  [7/10] Probe & provision OCI resources
# ══════════════════════════════════════════════════════════════
step_header 7 "Probe & provision OCI resources"

COMPARTMENT="${OCI_COMPARTMENT_OCID:-}"
REGION="${OCI_REGION:-}"
STREAM_POOL_NAME="${OCI_STREAM_POOL_NAME:-MultiCloud_Log_Pool}"
STREAM_NAME="${OCI_STREAM_NAME:-gcp-inbound-stream}"
LOG_GROUP_NAME="${OCI_LOG_GROUP_NAME:-GCPLogs}"
SCH_NAME="${OCI_SCH_NAME:-GCP-Stream-to-LogAnalytics}"
NAMESPACE="${OCI_LOG_ANALYTICS_NAMESPACE:-}"

OCI_MISSING=0

if [ -z "$COMPARTMENT" ] || [ -z "$REGION" ]; then
    status_fail "OCI_COMPARTMENT_OCID or OCI_REGION not set – cannot probe"
    ((ERRORS++))
    OCI_MISSING=99
else
    # Stream Pool
    POOL_ID=$(oci streaming admin stream-pool list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_POOL_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)
    if [ -n "$POOL_ID" ] && [ "$POOL_ID" != "null" ]; then
        status_ok "Stream Pool: $STREAM_POOL_NAME"
    else
        status_fail "Stream Pool: $STREAM_POOL_NAME"
        ((OCI_MISSING++))
    fi

    # Stream
    STREAM_ID=$(oci streaming admin stream list \
        --compartment-id "$COMPARTMENT" \
        --name "$STREAM_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data[0].id' --raw-output 2>/dev/null || true)
    if [ -n "$STREAM_ID" ] && [ "$STREAM_ID" != "null" ]; then
        status_ok "Stream: $STREAM_NAME"
    else
        status_fail "Stream: $STREAM_NAME"
        ((OCI_MISSING++))
    fi

    # Namespace auto-detect
    if [ -z "$NAMESPACE" ]; then
        NAMESPACE=$(oci log-analytics namespace list \
            --compartment-id "$COMPARTMENT" \
            --query 'data.items[0]."namespace-name"' --raw-output 2>/dev/null || true)
        [ "$NAMESPACE" = "null" ] && NAMESPACE=""
    fi

    if [ -n "$NAMESPACE" ]; then
        status_ok "Log Analytics Namespace: $NAMESPACE"

        # Log Group
        LG_ID=$(oci log-analytics log-group list \
            --compartment-id "$COMPARTMENT" \
            --namespace-name "$NAMESPACE" \
            --query "data.items[?\"display-name\"=='$LOG_GROUP_NAME'].id | [0]" \
            --raw-output 2>/dev/null || true)
        if [ -n "$LG_ID" ] && [ "$LG_ID" != "null" ] && [ "$LG_ID" != "None" ]; then
            status_ok "Log Group: $LOG_GROUP_NAME"
        else
            status_fail "Log Group: $LOG_GROUP_NAME"
            ((OCI_MISSING++))
        fi
    else
        status_fail "Log Analytics Namespace: not detected"
        ((OCI_MISSING++))
    fi

    # Connector Hub
    SCH_ID=$(oci sch service-connector list \
        --compartment-id "$COMPARTMENT" \
        --display-name "$SCH_NAME" \
        --lifecycle-state ACTIVE \
        --query 'data.items[0].id' --raw-output 2>/dev/null || true)
    if [ -n "$SCH_ID" ] && [ "$SCH_ID" != "null" ] && [ "$SCH_ID" != "None" ]; then
        status_ok "Connector Hub: $SCH_NAME"
    else
        status_fail "Connector Hub: $SCH_NAME"
        ((OCI_MISSING++))
    fi
fi

if [ "$OCI_MISSING" -gt 0 ] && [ "$OCI_MISSING" -ne 99 ]; then
    echo ""
    if ask_yn "Create missing OCI resources via setup_oci.sh?" "y"; then
        if run_child "$SCRIPT_DIR/setup_oci.sh"; then
            status_ok "setup_oci.sh completed"
            reload_env
        else
            status_fail "setup_oci.sh failed"
            ((ERRORS++))
            if ! $AUTO && ! ask_yn "Continue anyway?" "n"; then
                exit 1
            fi
        fi
    else
        status_skip "OCI provisioning skipped"
    fi
elif [ "$OCI_MISSING" -eq 0 ] && [ -n "$COMPARTMENT" ]; then
    echo ""
    status_ok "All OCI resources exist – nothing to create"
fi

# ══════════════════════════════════════════════════════════════
#  [8/10] Validate OCI credentials
# ══════════════════════════════════════════════════════════════
step_header 8 "Validate OCI credentials"

if $SKIP_TESTS; then
    status_skip "Skipped (--skip-tests)"
elif $DRY_RUN; then
    echo "    ${C_DIM}[dry-run] Would run: python3 scripts/test_oci_credentials.py${C_RESET}"
else
    if python3 "$SCRIPT_DIR/test_oci_credentials.py"; then
        status_ok "OCI credentials valid"
    else
        status_fail "OCI credential validation failed"
        ((ERRORS++))
        if ! $AUTO && ! ask_yn "Continue anyway?" "n"; then
            exit 1
        fi
    fi
fi

# ══════════════════════════════════════════════════════════════
#  [9/10] End-to-end test
# ══════════════════════════════════════════════════════════════
step_header 9 "End-to-end test"

RUN_E2E=false
if $SKIP_TESTS; then
    status_skip "Skipped (--skip-tests)"
elif $DRY_RUN; then
    echo "    ${C_DIM}[dry-run] Would publish test message and drain bridge${C_RESET}"
elif $E2E; then
    RUN_E2E=true
elif ! $AUTO; then
    if ask_yn "Run end-to-end test? (publish message + drain bridge)" "n"; then
        RUN_E2E=true
    else
        status_skip "End-to-end test skipped"
    fi
else
    status_skip "Skipped in --auto mode (use --e2e to include)"
fi

if $RUN_E2E; then
    echo "    Publishing test message..."
    if python3 "$SCRIPT_DIR/publish_test_message.py"; then
        status_ok "Test message published"
    else
        status_fail "Failed to publish test message"
        ((ERRORS++))
    fi

    echo "    Running bridge in drain mode..."
    if "$SCRIPT_DIR/drain_pubsub_to_oci.sh"; then
        status_ok "Bridge drain completed"
    else
        status_fail "Bridge drain failed"
        ((ERRORS++))
    fi
fi

# ══════════════════════════════════════════════════════════════
#  [10/10] Final summary
# ══════════════════════════════════════════════════════════════
step_header 10 "Final summary"

if $DRY_RUN; then
    echo "    ${C_DIM}[dry-run] Would run: ./scripts/status.sh${C_RESET}"
else
    echo ""
    "$SCRIPT_DIR/status.sh" || true
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "  ${C_GREEN}Setup complete!${C_RESET}"
    echo ""
    echo "  Next steps:"
    echo "    python -m bridge.main --drain    # test run (exits when queue empty)"
    echo "    python -m bridge.main            # continuous mode"
else
    echo "  ${C_YELLOW}Setup finished with $ERRORS error(s). Review the output above.${C_RESET}"
fi
echo ""

exit "$ERRORS"
