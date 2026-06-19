#!/bin/bash
#######################################
# OCI Container Monitoring - Environment Setup
# Interactive script to configure environment
#######################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${PROJECT_ROOT}/config/oci-monitoring.env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  OCI Container Monitoring - Environment Setup    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Check if OCI CLI is configured
if ! oci iam region list >/dev/null 2>&1; then
    echo -e "${YELLOW}OCI CLI is not configured. Please run 'oci setup config' first.${NC}"
    exit 1
fi

# Get OCI tenancy information
echo -e "${GREEN}Retrieving OCI tenancy information...${NC}"
TENANCY_OCID=$(oci iam compartment list --compartment-id-in-subtree true --all --query 'data[?name==`root`].id | [0]' --raw-output 2>/dev/null || echo "")

if [ -z "$TENANCY_OCID" ]; then
    echo -e "${YELLOW}Could not retrieve tenancy OCID automatically.${NC}"
    read -p "Enter your Tenancy OCID: " TENANCY_OCID
fi

echo -e "${BLUE}Tenancy OCID: ${TENANCY_OCID}${NC}"

# Get compartment OCID
echo ""
echo -e "${GREEN}Available Compartments:${NC}"
oci iam compartment list --compartment-id-in-subtree true --all \
    --query 'data[*].[name,"id"]' --output table 2>/dev/null || true

echo ""
read -p "Enter Compartment OCID: " COMPARTMENT_OCID

# Get region
CURRENT_REGION=$(oci iam region-subscription list --query 'data[?"is-home-region"==`true`]."region-name" | [0]' --raw-output 2>/dev/null || echo "us-ashburn-1")
echo ""
echo -e "${GREEN}Available Regions:${NC}"
oci iam region list --query 'data[*].name' --output table 2>/dev/null || true
echo ""
read -p "Enter Region [${CURRENT_REGION}]: " REGION
REGION=${REGION:-$CURRENT_REGION}

# Get VCN and Subnet
echo ""
echo -e "${GREEN}Retrieving VCNs in compartment...${NC}"
oci network vcn list --compartment-id "$COMPARTMENT_OCID" \
    --query 'data[*].["display-name","id"]' --output table 2>/dev/null || true

echo ""
read -p "Enter VCN OCID: " VCN_OCID

echo ""
echo -e "${GREEN}Retrieving Subnets in VCN...${NC}"
oci network subnet list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$VCN_OCID" \
    --query 'data[*].["display-name","id"]' --output table 2>/dev/null || true

echo ""
read -p "Enter Subnet OCID: " SUBNET_OCID

# Container configuration
echo ""
echo -e "${CYAN}Container Configuration${NC}"
read -p "Container Instance Name [monitoring-demo]: " CONTAINER_NAME
CONTAINER_NAME=${CONTAINER_NAME:-monitoring-demo}

read -p "Container Image [nginx:latest]: " CONTAINER_IMAGE
CONTAINER_IMAGE=${CONTAINER_IMAGE:-nginx:latest}

read -p "OCPUs [1]: " OCPUS
OCPUS=${OCPUS:-1}

read -p "Memory GB [4]: " MEMORY
MEMORY=${MEMORY:-4}

read -p "Container Port [80]: " PORT
PORT=${PORT:-80}

read -p "Assign Public IP? (true/false) [true]: " PUBLIC_IP
PUBLIC_IP=${PUBLIC_IP:-true}

# Logging configuration
echo ""
echo -e "${CYAN}Logging Configuration${NC}"
read -p "Enable Logging? (true/false) [true]: " ENABLE_LOGGING
ENABLE_LOGGING=${ENABLE_LOGGING:-true}

read -p "Log Retention Days (30/60/90/120/180/365) [30]: " LOG_RETENTION
LOG_RETENTION=${LOG_RETENTION:-30}

# Management Agent
echo ""
echo -e "${CYAN}Management Agent Configuration${NC}"
read -p "Enable Management Agent for Prometheus? (true/false) [true]: " ENABLE_AGENT
ENABLE_AGENT=${ENABLE_AGENT:-true}

read -p "Prometheus Metrics Port [9090]: " METRICS_PORT
METRICS_PORT=${METRICS_PORT:-9090}

# Dashboard
echo ""
echo -e "${CYAN}Monitoring Dashboard${NC}"
read -p "Create Monitoring Dashboard? (true/false) [true]: " CREATE_DASH
CREATE_DASH=${CREATE_DASH:-true}

# Generate configuration file
echo ""
echo -e "${GREEN}Generating configuration file...${NC}"

cat > "$CONFIG_FILE" << EOF
#!/bin/bash
# OCI Container Instance Monitoring Configuration
# Generated on: $(date)

# OCI Authentication & Region
export OCI_CLI_PROFILE="DEFAULT"
export OCI_REGION="${REGION}"
export OCI_TENANCY_OCID="${TENANCY_OCID}"
export OCI_COMPARTMENT_OCID="${COMPARTMENT_OCID}"

# Container Instance Configuration
export CONTAINER_INSTANCE_NAME="${CONTAINER_NAME}"
export CONTAINER_IMAGE="${CONTAINER_IMAGE}"
export CONTAINER_SHAPE="CI.Standard.E4.Flex"
export CONTAINER_OCPUS="${OCPUS}"
export CONTAINER_MEMORY_GB="${MEMORY}"
export CONTAINER_COUNT="1"
export CONTAINER_PORT="${PORT}"
export CONTAINER_ENV_VARS=""
export AVAILABILITY_DOMAIN="1"

# Networking Configuration
export VCN_OCID="${VCN_OCID}"
export SUBNET_OCID="${SUBNET_OCID}"
export ASSIGN_PUBLIC_IP="${PUBLIC_IP}"
export NSG_OCIDS=""

# Logging Configuration
export ENABLE_LOGGING="${ENABLE_LOGGING}"
export LOG_GROUP_NAME="container-instance-logs"
export LOG_RETENTION_DAYS="${LOG_RETENTION}"
export ENABLE_AUDIT_LOGS="true"
export LOG_LEVEL="INFO"

# Management Agent Configuration
export ENABLE_MANAGEMENT_AGENT="${ENABLE_AGENT}"
export MGMT_AGENT_NAME="container-prometheus-agent"
export MGMT_AGENT_INSTALL_KEY_NAME="container-agent-key"
export PROMETHEUS_SCRAPE_INTERVAL="60"
export PROMETHEUS_SCRAPE_TIMEOUT="10"
export PROMETHEUS_METRICS_PORT="${METRICS_PORT}"
export PROMETHEUS_METRICS_PATH="/metrics"
export MGMT_AGENT_VERSION=""

# Monitoring & Dashboards
export CREATE_DASHBOARD="${CREATE_DASH}"
export DASHBOARD_NAME="Container Instance Monitoring Dashboard"
export METRICS_NAMESPACE="container_monitoring"
export NOTIFICATION_TOPIC_OCID=""
export ENABLE_ALARMS="false"
export CPU_ALARM_THRESHOLD="80"
export MEMORY_ALARM_THRESHOLD="80"

# Terraform Configuration
export TF_BACKEND="local"
export TF_STATE_BUCKET=""
export TF_WORKSPACE="dev"

# OCIR Authentication
export OCIR_USERNAME=""
export OCIR_AUTH_TOKEN=""

# Tags
export FREEFORM_TAGS='{"Environment":"Development","ManagedBy":"Terraform"}'
export DEFINED_TAGS='{}'

# Script Behavior
export VERBOSE="false"
export DRY_RUN="false"
export AUTO_APPROVE="false"
export CLEANUP_ON_FAILURE="false"

# Advanced Settings
export TF_PLAN_FILE="tfplan"
export MAX_WAIT_TIME="600"
export RETRY_ATTEMPTS="3"
export RETRY_DELAY="10"
EOF

chmod 600 "$CONFIG_FILE"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Configuration Complete!                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration file created: ${CONFIG_FILE}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Review and customize: ${CONFIG_FILE}"
echo -e "2. Run deployment: ${SCRIPT_DIR}/deploy.sh"
echo ""
