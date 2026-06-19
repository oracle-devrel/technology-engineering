#!/bin/bash
#######################################
# OCI Container Instance - Log Viewer
# View container logs in real-time
#######################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_ROOT}/output"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get container instance ID and log group ID from Terraform outputs
if [ -f "${OUTPUT_DIR}/terraform-outputs.json" ]; then
    CONTAINER_INSTANCE_ID=$(jq -r '.container_instance_id.value' "${OUTPUT_DIR}/terraform-outputs.json" 2>/dev/null || echo "")
    LOG_GROUP_ID=$(jq -r '.log_group_id.value' "${OUTPUT_DIR}/terraform-outputs.json" 2>/dev/null || echo "")
else
    echo -e "${YELLOW}Terraform outputs not found. Please run deployment first.${NC}"
    exit 1
fi

if [ -z "$CONTAINER_INSTANCE_ID" ] || [ "$CONTAINER_INSTANCE_ID" = "null" ]; then
    echo -e "${YELLOW}Container Instance ID not found in outputs${NC}"
    exit 1
fi

echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      OCI Container Instance - Log Viewer         ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Container Instance ID: ${BLUE}${CONTAINER_INSTANCE_ID}${NC}"
echo -e "${GREEN}Log Group ID: ${BLUE}${LOG_GROUP_ID}${NC}"
echo ""

# Function to display logs
view_logs() {
    local log_type=$1

    # Platform-independent date calculation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS (BSD date)
        local time_start=$(date -u -v-1H +%Y-%m-%dT%H:%M:%S.000Z)
    else
        # Linux (GNU date)
        local time_start=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S.000Z)
    fi
    local time_end=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    echo -e "${GREEN}Fetching ${log_type} logs from last hour...${NC}"
    echo ""

    oci logging-search search-logs \
        --search-query "search \"${LOG_GROUP_ID}\" | source='${log_type}' | sort by datetime desc" \
        --time-start "$time_start" \
        --time-end "$time_end" \
        --query 'data.results[*].data.message' \
        --output table 2>/dev/null || echo "No logs found"
}

# Menu
PS3="Select log type to view: "
options=("Application Logs" "System Logs" "All Logs (Live Tail)" "Container Instance Details" "Quit")

select opt in "${options[@]}"
do
    case $opt in
        "Application Logs")
            view_logs "application"
            ;;
        "System Logs")
            view_logs "system"
            ;;
        "All Logs (Live Tail)")
            echo -e "${GREEN}Tailing logs (Ctrl+C to stop)...${NC}"
            echo ""
            while true; do
                view_logs "application"
                sleep 5
            done
            ;;
        "Container Instance Details")
            echo -e "${GREEN}Container Instance Details:${NC}"
            oci container-instances container-instance get \
                --container-instance-id "$CONTAINER_INSTANCE_ID" \
                --query 'data' \
                --output table 2>/dev/null || echo "Failed to retrieve details"
            ;;
        "Quit")
            echo -e "${GREEN}Goodbye!${NC}"
            break
            ;;
        *)
            echo -e "${YELLOW}Invalid option $REPLY${NC}"
            ;;
    esac
    echo ""
done
