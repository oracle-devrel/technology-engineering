#!/bin/bash
# Manage the OCI Management Agent Prometheus data source(s) for the proxy.
#
# The Windows proxy has no OCI CLI, so the data source that feeds OCI Monitoring
# is managed from any host that has the OCI CLI configured (your workstation,
# a jump host, cloud shell, …).
#
# Subcommands:
#   list     — show existing data sources on the agent
#   create   — create the Prometheus (federate) data source — IDEMPOTENT:
#              it first checks the existing data sources and skips if one with
#              the same name already exists
#   destroy  — delete the data source(s) (all, or a single --name)
#
# Usage:
#   ./manage-oci-datasource.sh list    --agent-id <OCID> [--profile P]
#   ./manage-oci-datasource.sh create  --agent-id <OCID> --compartment-id <OCID> \
#                                       --name proxy_prometheus --namespace prometheus_proxy \
#                                       [--url <federate-url>] [--schedule-mins 1] [--profile P]
#   ./manage-oci-datasource.sh destroy --agent-id <OCID> [--name proxy_prometheus] [--profile P]

set -euo pipefail

ACTION="${1:-}"; shift || true

PROFILE="${OCI_CLI_PROFILE:-DEFAULT}"
AGENT_ID="" COMPARTMENT_ID="" NAME="" NAMESPACE="" URL="" SCHEDULE_MINS="1"
# Federate ALL jobs by default ({job=~".+"} percent-encoded). Forwards the
# aggregated exporter series — NOT Prometheus' own /metrics telemetry.
DEFAULT_URL='http://localhost:9090/federate?match%5B%5D=%7Bjob%3D~%22.%2B%22%7D'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent-id)        AGENT_ID="$2"; shift 2;;
    --compartment-id)  COMPARTMENT_ID="$2"; shift 2;;
    --name)            NAME="$2"; shift 2;;
    --namespace)       NAMESPACE="$2"; shift 2;;
    --url)             URL="$2"; shift 2;;
    --schedule-mins)   SCHEDULE_MINS="$2"; shift 2;;
    --profile)         PROFILE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

oci_() { oci --profile "$PROFILE" "$@"; }

usage() {
  echo "Usage: $0 {list|create|destroy} --agent-id <OCID> [options]" >&2
  echo "  create needs: --compartment-id --name --namespace [--url --schedule-mins]" >&2
  echo "  destroy accepts optional --name (default: delete all)" >&2
  exit 1
}

# Returns the data-sources JSON. When an agent has zero data sources the CLI
# prints nothing; emit '{}' so downstream JSON parsing doesn't choke (KB-25).
list_raw() { local out; out="$(oci_ management-agent agent list-data-sources --management-agent-id "$AGENT_ID" --all 2>/dev/null)"; echo "${out:-{}}"; }

case "$ACTION" in
  list)
    [[ -z "$AGENT_ID" ]] && usage
    list_raw | python3 -c "
import sys, json
items = (json.load(sys.stdin).get('data') or {}).get('items') or []
if not items:
    print('No data sources on this agent.')
else:
    print(f'{len(items)} data source(s):')
    for i in items:
        print(f\"  - {i.get('name')}  [{i.get('type')}]  key={i.get('key')}\")
        if i.get('url'): print(f\"      url: {i.get('url')}\")
"
    ;;

  create)
    [[ -z "$AGENT_ID" || -z "$COMPARTMENT_ID" || -z "$NAME" || -z "$NAMESPACE" ]] && usage
    URL="${URL:-$DEFAULT_URL}"
    # Idempotency: check existing data sources first.
    EXISTS=$(list_raw | python3 -c "
import sys, json
items = (json.load(sys.stdin).get('data') or {}).get('items') or []
print('yes' if any(i.get('name') == '$NAME' for i in items) else 'no')
")
    if [[ "$EXISTS" == "yes" ]]; then
      echo "Data source '$NAME' already exists — skipping create (idempotent)."
      echo "To recreate: $0 destroy --agent-id $AGENT_ID --name $NAME  then run create again."
      exit 0
    fi
    echo "Creating Prometheus data source '$NAME' (namespace '$NAMESPACE')..."
    oci_ management-agent agent create-prometheus-datasource \
      --management-agent-id "$AGENT_ID" --compartment-id "$COMPARTMENT_ID" \
      --name "$NAME" --namespace "$NAMESPACE" --url "$URL" --schedule-mins "$SCHEDULE_MINS" \
      --wait-for-state SUCCEEDED
    echo "Created."
    ;;

  destroy)
    [[ -z "$AGENT_ID" ]] && usage
    MATCHES=$(list_raw | python3 -c "
import sys, json
items = (json.load(sys.stdin).get('data') or {}).get('items') or []
flt = '$NAME'
for i in items:
    if not flt or i.get('name') == flt:
        print(i.get('key'), i.get('name'))
")
    if [[ -z "$MATCHES" ]]; then
      echo "No matching data sources to delete."
      exit 0
    fi
    echo "$MATCHES" | while read -r KEY DSNAME; do
      [[ -z "$KEY" ]] && continue
      echo "Deleting data source '$DSNAME' (key=$KEY)..."
      oci_ management-agent agent delete-data-source \
        --management-agent-id "$AGENT_ID" --data-source-key "$KEY" --force \
        --wait-for-state SUCCEEDED
    done
    echo "Done."
    ;;

  *) usage;;
esac
