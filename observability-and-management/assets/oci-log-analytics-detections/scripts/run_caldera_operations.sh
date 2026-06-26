#!/usr/bin/env bash
# Execute Caldera adversary operations for detection rule testing.
#
# Self-contained — no common.sh dependency.
# Runs 5 sequential operations with completion polling.
#
# Required env vars:
#   CALDERA_URL          — Caldera server URL (e.g., http://10.0.1.10:8888)
#   CALDERA_API_KEY_RED  — Red team API key
#
# Optional:
#   CALDERA_GROUP        — Agent group to target (default: red)
#   CALDERA_TIMEOUT      — Max seconds to wait per operation (default: 300)

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────
CALDERA_URL="${CALDERA_URL:-}"
CALDERA_API_KEY_RED="${CALDERA_API_KEY_RED:-}"
CALDERA_GROUP="${CALDERA_GROUP:-red}"
CALDERA_TIMEOUT="${CALDERA_TIMEOUT:-300}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ─── Helpers ──────────────────────────────────────────────────

banner() {
    echo ""
    echo "================================================================"
    echo "  $1"
    echo "================================================================"
}

info()  { echo "[caldera] $*"; }
warn()  { echo "[caldera] WARN: $*" >&2; }
error() { echo "[caldera] ERROR: $*" >&2; exit 1; }

api() {
    local method="$1" endpoint="$2"
    shift 2
    curl -sf --connect-timeout 5 --max-time 15 \
        -X "$method" \
        "${CALDERA_URL}${endpoint}" \
        -H "KEY:${CALDERA_API_KEY_RED}" \
        -H "Content-Type: application/json" \
        "$@" 2>/dev/null || echo ""
}

# ─── Pre-flight checks ───────────────────────────────────────

banner "Caldera Adversary Operations"

if [[ -z "$CALDERA_URL" || -z "$CALDERA_API_KEY_RED" ]]; then
    error "CALDERA_URL and CALDERA_API_KEY_RED must be set"
fi

info "Server:  $CALDERA_URL"
info "Group:   $CALDERA_GROUP"
info "Timeout: ${CALDERA_TIMEOUT}s per operation"

# Health check
health=$(api GET "/api/v2/health")
if ! echo "$health" | grep -qi "alive\|healthy\|ok"; then
    error "Caldera not responding at $CALDERA_URL"
fi
info "Health check: OK"

# Agent check
agents=$(api GET "/api/v2/agents")
agent_count=$(echo "$agents" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len([a for a in data if a.get('group','') == '${CALDERA_GROUP}' or '${CALDERA_GROUP}' == 'red']))
" 2>/dev/null || echo "0")

if [[ "$agent_count" -eq 0 ]]; then
    error "No agents available in group '$CALDERA_GROUP'"
fi
info "Agents available: $agent_count"

# Get default fact source
source_id=$(api GET "/api/v2/sources" | python3 -c "
import sys, json
sources = json.load(sys.stdin)
print(next((s['id'] for s in sources if s.get('name') == 'basic'), sources[0]['id'] if sources else ''))
" 2>/dev/null || echo "")

# ─── Resolve adversary profiles ──────────────────────────────

resolve_adversary() {
    local name_pattern="$1"
    api GET "/api/v2/adversaries" | python3 -c "
import sys, json
adversaries = json.load(sys.stdin)
for a in adversaries:
    if '${name_pattern}'.lower() in a.get('name','').lower():
        print(a['adversary_id'])
        break
" 2>/dev/null || echo ""
}

# ─── Wait for operation completion ────────────────────────────

wait_for_operation() {
    local op_id="$1"
    local op_name="$2"
    local timeout="$CALDERA_TIMEOUT"
    local elapsed=0
    local poll_interval=10

    info "Waiting for operation '$op_name' ($op_id) to complete..."

    while [[ $elapsed -lt $timeout ]]; do
        state=$(api GET "/api/v2/operations/$op_id" | python3 -c "
import sys, json
op = json.load(sys.stdin)
print(op.get('state', 'unknown'))
" 2>/dev/null || echo "unknown")

        if [[ "$state" == "finished" || "$state" == "cleanup" ]]; then
            info "Operation '$op_name' completed (state: $state) in ${elapsed}s"
            return 0
        fi

        sleep "$poll_interval"
        elapsed=$((elapsed + poll_interval))
        info "  ... $op_name: state=$state, elapsed=${elapsed}s"
    done

    warn "Operation '$op_name' timed out after ${timeout}s (state: $state)"
    return 1
}

# ─── Run operation with wait ─────────────────────────────────

run_operation() {
    local op_name="$1"
    local adversary_id="$2"
    local techniques="$3"

    if [[ -z "$adversary_id" ]]; then
        warn "No adversary profile found for $op_name. Skipping."
        return 1
    fi

    info "Creating operation: $op_name (adversary: $adversary_id)"
    info "  MITRE Techniques: $techniques"

    result=$(api POST "/api/v2/operations" -d "{
        \"name\": \"soc-detect-${op_name}\",
        \"adversary\": {\"adversary_id\": \"${adversary_id}\"},
        \"source\": {\"id\": \"${source_id}\"},
        \"auto_close\": true,
        \"jitter\": \"2/8\",
        \"group\": \"${CALDERA_GROUP}\"
    }")

    op_id=$(echo "$result" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('id', ''))
" 2>/dev/null || echo "")

    if [[ -z "$op_id" ]]; then
        warn "Failed to create operation $op_name"
        return 1
    fi

    info "Operation started: $op_name (id: $op_id)"
    wait_for_operation "$op_id" "$op_name"
}

# ─── Execute Operations ──────────────────────────────────────

# Operation 1: Discovery
banner "Operation 1: System & Network Discovery"
info "Techniques: T1082, T1016, T1049, T1033"
info "Expected detections: win_account_discovery, linux_system_owner_discovery"
discovery_id=$(resolve_adversary "discovery")
run_operation "discovery" "$discovery_id" "T1082,T1016,T1049,T1033" || true

# Operation 2: Credential Access
banner "Operation 2: Credential Access"
info "Techniques: T1003.001, T1558.003, T1552"
info "Expected detections: win_credential_dump_lsass, win_kerberoasting"
cred_id=$(resolve_adversary "credential")
run_operation "credential-access" "$cred_id" "T1003.001,T1558.003,T1552" || true

# Operation 3: Lateral Movement
banner "Operation 3: Lateral Movement"
info "Techniques: T1021.002, T1021.006, T1570"
info "Expected detections: win_psexec_lateral_movement, win_sysmon_lateral_movement_smb"
lateral_id=$(resolve_adversary "lateral")
run_operation "lateral-movement" "$lateral_id" "T1021.002,T1021.006,T1570" || true

# Operation 4: Collection
banner "Operation 4: File Collection"
info "Techniques: T1005, T1039, T1074"
info "Expected detections: linux_sensitive_data_access, win_data_staging"
collection_id=$(resolve_adversary "collection")
run_operation "collection" "$collection_id" "T1005,T1039,T1074" || true

# Operation 5: Exfiltration
banner "Operation 5: Data Exfiltration"
info "Techniques: T1041, T1048, T1567"
info "Expected detections: linux_exfiltration_over_alt_protocol, win_sysmon_dns_exfil"
exfil_id=$(resolve_adversary "exfiltration")
run_operation "exfiltration" "$exfil_id" "T1041,T1048,T1567" || true

# ─── Summary ─────────────────────────────────────────────────

banner "Operations Complete"
info "Monitor at: ${CALDERA_URL}/#/operations"
info ""
info "Next step: verify detections fired"
info "  python3 scripts/verify_caldera_detections.py"
