#!/bin/bash
#
# OCI Metrics Report Generator - CloudShell Wrapper
#
# This script simplifies running the report generator in OCI CloudShell
# by automatically detecting authentication and providing helpful defaults.
#
# Usage:
#   ./cloudshell_report.sh <compartment_ocid> <namespace> <metric1> [metric2] ...
#
# Examples:
#   # Generate compute metrics report
#   ./cloudshell_report.sh ocid1.compartment.oc1..xxx oci_computeagent CpuUtilization MemoryUtilization
#
#   # Generate block volume report for 7 days
#   ./cloudshell_report.sh ocid1.compartment.oc1..xxx oci_blockvolume VolumeReadOps VolumeWriteOps --hours 168
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       OCI Metrics Report Generator - CloudShell Mode         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in CloudShell
if [ -n "$OCI_CLI_CLOUD_SHELL" ]; then
    echo -e "${GREEN}✓ Running in OCI CloudShell${NC}"
    AUTH_METHOD="security_token"
elif [ "$OCI_CLI_AUTH" = "instance_principal" ]; then
    echo -e "${GREEN}✓ Using Instance Principal authentication${NC}"
    AUTH_METHOD="instance_principal"
else
    echo -e "${YELLOW}! Running outside CloudShell, using config file authentication${NC}"
    AUTH_METHOD="config_file"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import oci" 2>/dev/null; then
    echo -e "${YELLOW}Installing OCI SDK...${NC}"
    pip3 install --user oci flask flask-cors python-dateutil
fi

# Parse arguments
show_help() {
    echo ""
    echo "Usage: $0 <compartment_ocid> <namespace> <metric1> [metric2] ... [options]"
    echo ""
    echo "Arguments:"
    echo "  compartment_ocid    OCID of the compartment to query"
    echo "  namespace           Metric namespace (e.g., oci_computeagent)"
    echo "  metric1, metric2    Metric name(s) to include"
    echo ""
    echo "Options:"
    echo "  --hours <n>         Hours of data to fetch (default: 24)"
    echo "  --interval <i>      Aggregation interval: 1m, 5m, 15m, 1h, 6h, 1d (default: 1h)"
    echo "  --statistic <s>     Statistic: mean, max, min, sum, count (default: mean)"
    echo "  --group-by <dim>    Group by dimension (e.g., resourceId)"
    echo "  --output <file>     Output file name (default: metrics_report.html)"
    echo "  --json              Output JSON instead of HTML"
    echo "  --list-namespaces   List available namespaces and exit"
    echo "  --list-metrics      List available metrics in namespace and exit"
    echo ""
    echo "Examples:"
    echo "  # Compute metrics for 24 hours"
    echo "  $0 ocid1.compartment.oc1..xxx oci_computeagent CpuUtilization MemoryUtilization"
    echo ""
    echo "  # Block volume metrics for 7 days, grouped by resource"
    echo "  $0 ocid1.compartment.oc1..xxx oci_blockvolume VolumeReadOps --hours 168 --group-by resourceId"
    echo ""
    echo "  # List all namespaces in compartment"
    echo "  $0 ocid1.compartment.oc1..xxx --list-namespaces"
    echo ""
    echo "Common Namespaces:"
    echo "  oci_computeagent         - Compute instance metrics"
    echo "  oci_blockvolume          - Block volume metrics"
    echo "  oci_vcn                  - Network metrics"
    echo "  oci_lbaas                - Load balancer metrics"
    echo "  oci_autonomous_database  - Autonomous DB metrics"
    echo "  oci_objectstorage        - Object storage metrics"
    echo ""
}

if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Extract compartment (first argument)
COMPARTMENT="$1"
shift

# Check for discovery commands first
if [ "$1" = "--list-namespaces" ] || [ "$1" = "--list-compartments" ]; then
    echo ""
    python3 "$SCRIPT_DIR/generate_report.py" \
        --auth "$AUTH_METHOD" \
        -c "$COMPARTMENT" \
        "$1"
    exit 0
fi

# Extract namespace (second argument)
NAMESPACE="$1"
shift

# Check for --list-metrics
if [ "$1" = "--list-metrics" ]; then
    echo ""
    python3 "$SCRIPT_DIR/generate_report.py" \
        --auth "$AUTH_METHOD" \
        -c "$COMPARTMENT" \
        -n "$NAMESPACE" \
        --list-metrics
    exit 0
fi

# Collect metrics and options
METRICS=()
EXTRA_ARGS=()
OUTPUT="metrics_report_$(date +%Y%m%d_%H%M%S).html"

while [ $# -gt 0 ]; do
    case "$1" in
        --hours|--interval|--statistic|--group-by|--output|--resource-group|--title)
            if [ "$1" = "--output" ]; then
                OUTPUT="$2"
            fi
            EXTRA_ARGS+=("$1" "$2")
            shift 2
            ;;
        --json)
            EXTRA_ARGS+=("$1")
            OUTPUT="${OUTPUT%.html}.json"
            shift
            ;;
        --*)
            EXTRA_ARGS+=("$1")
            shift
            ;;
        *)
            METRICS+=("-m" "$1")
            shift
            ;;
    esac
done

# Validate we have at least one metric
if [ ${#METRICS[@]} -eq 0 ]; then
    echo -e "${RED}Error: At least one metric name is required${NC}"
    echo "Run '$0 --help' for usage information"
    exit 1
fi

# Build and run command
echo ""
echo -e "${BLUE}Generating report...${NC}"
echo "  Compartment: ${COMPARTMENT:0:40}..."
echo "  Namespace: $NAMESPACE"
echo "  Metrics: ${METRICS[*]}"
echo ""

python3 "$SCRIPT_DIR/generate_report.py" \
    --auth "$AUTH_METHOD" \
    -c "$COMPARTMENT" \
    -n "$NAMESPACE" \
    "${METRICS[@]}" \
    -o "$OUTPUT" \
    "${EXTRA_ARGS[@]}"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Report Generated!                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Output file: ${BLUE}$OUTPUT${NC}"
    echo ""

    # In CloudShell, suggest how to download
    if [ -n "$OCI_CLI_CLOUD_SHELL" ]; then
        echo -e "${YELLOW}To download the report from CloudShell:${NC}"
        echo "  1. Click the gear icon (⚙️) in the top right"
        echo "  2. Select 'Download'"
        echo "  3. Enter the filename: $OUTPUT"
        echo ""
        echo "Or use: cloudshell download $OUTPUT"
    fi
else
    echo -e "${RED}Report generation failed${NC}"
    exit 1
fi
