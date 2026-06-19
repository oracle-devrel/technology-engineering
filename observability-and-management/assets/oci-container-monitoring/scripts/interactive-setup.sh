#!/bin/bash
#######################################
# Interactive OCI Monitoring Setup
# Helps users choose the best monitoring architecture
#######################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${PROJECT_ROOT}/config/oci-monitoring.env"

#######################################
# Banner
#######################################
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   OCI Container Instance Monitoring - Interactive Setup   ║
║   Smart monitoring architecture selection                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

#######################################
# Detect User's Public IP
#######################################
echo -e "${BLUE}[INFO]${NC} Detecting your public IP address..."
USER_PUBLIC_IP=$(curl -s https://api.ipify.org || curl -s https://ifconfig.me || echo "")

if [ -z "$USER_PUBLIC_IP" ]; then
    echo -e "${YELLOW}[WARNING]${NC} Could not automatically detect your IP"
    read -p "Please enter your public IP address: " USER_PUBLIC_IP
fi

echo -e "${GREEN}[SUCCESS]${NC} Your IP: ${CYAN}$USER_PUBLIC_IP${NC}"
ALLOWED_CIDR="${USER_PUBLIC_IP}/32"

#######################################
# Architecture Selection
#######################################
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  MONITORING ARCHITECTURE SELECTION${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Please answer a few questions to determine the best monitoring architecture:"
echo ""

# Question 1: Multiple instances
echo -e "${YELLOW}Question 1:${NC} Do you plan to deploy multiple container instances?"
echo "   This helps us recommend the optimal monitoring setup."
echo ""
echo "   [1] No, just a single container instance (or a few)"
echo "   [2] Yes, I plan to deploy many container instances"
echo ""
read -p "Your choice [1-2]: " MULTIPLE_INSTANCES

# Question 2: Grafana preference
echo ""
echo -e "${YELLOW}Question 2:${NC} Do you want Grafana for visualization?"
echo "   Grafana provides rich dashboards and alerting."
echo ""
echo "   [1] No, I'll use OCI Console for monitoring"
echo "   [2] Yes, I want Grafana dashboards"
echo ""
read -p "Your choice [1-2]: " WANT_GRAFANA

# Question 3: SSH Key
echo ""
if [ "$MULTIPLE_INSTANCES" = "2" ] || [ "$WANT_GRAFANA" = "2" ]; then
    echo -e "${YELLOW}Question 3:${NC} Do you have an SSH public key?"
    echo "   Required for VM access if deploying monitoring VM."
    echo ""
    read -p "Path to SSH public key [~/.ssh/id_rsa.pub]: " SSH_KEY_PATH
    SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/id_rsa.pub}"
    SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"

    if [ ! -f "$SSH_KEY_PATH" ]; then
        echo -e "${YELLOW}[WARNING]${NC} SSH key not found. Generating new key..."
        mkdir -p ~/.ssh
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "oci-monitoring-$(date +%Y%m%d)"
        SSH_KEY_PATH="~/.ssh/id_rsa.pub"
    fi
    SSH_PUBLIC_KEY=$(cat "$SSH_KEY_PATH")
fi

#######################################
# Recommendation
#######################################
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  RECOMMENDATION${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$MULTIPLE_INSTANCES" = "2" ]; then
    DEPLOYMENT_MODE="vm"
    echo -e "${GREEN}✓ Recommended Architecture:${NC} ${YELLOW}Centralized Monitoring VM${NC}"
    echo ""
    echo "  ${CYAN}Why this approach?${NC}"
    echo "  • More cost-effective for multiple container instances"
    echo "  • Centralized metrics collection and storage"
    echo "  • Single management point for all monitoring"
    echo "  • Better scalability (can monitor 100+ containers)"
    echo "  • Includes Grafana for rich visualizations"
    echo "  • Lower per-container overhead"
    echo ""
    echo "  ${CYAN}What will be deployed:${NC}"
    echo "  • Monitoring VM (1 OCPU, 8GB RAM) with:"
    echo "    - OCI Management Agent"
    echo "    - Prometheus"
    echo "    - Grafana (optional)"
    echo "  • Network Security Group (restricted to your IP)"
    echo "  • Container instances WITHOUT agent sidecars"
    echo ""
elif [ "$WANT_GRAFANA" = "2" ]; then
    DEPLOYMENT_MODE="vm"
    echo -e "${GREEN}✓ Recommended Architecture:${NC} ${YELLOW}Monitoring VM with Grafana${NC}"
    echo ""
    echo "  ${CYAN}Why this approach?${NC}"
    echo "  • Grafana provides superior visualization"
    echo "  • Centralized dashboard management"
    echo "  • Historical metrics storage in Prometheus"
    echo "  • Custom alerting capabilities"
    echo ""
    echo "  ${CYAN}What will be deployed:${NC}"
    echo "  • Monitoring VM with Grafana + Prometheus"
    echo "  • Network Security Group (restricted to your IP)"
    echo "  • Container instances with metrics exporters"
    echo ""
else
    DEPLOYMENT_MODE="sidecar"
    echo -e "${GREEN}✓ Recommended Architecture:${NC} ${YELLOW}Sidecar Pattern${NC}"
    echo ""
    echo "  ${CYAN}Why this approach?${NC}"
    echo "  • Simplest setup for few containers"
    echo "  • No additional infrastructure needed"
    echo "  • Agent runs alongside your container"
    echo "  • Direct metrics to OCI Monitoring"
    echo "  • Good for 1-10 container instances"
    echo ""
    echo "  ${CYAN}What will be deployed:${NC}"
    echo "  • Container instance with 2 containers:"
    echo "    - Your application container"
    echo "    - Management Agent sidecar"
    echo "  • Network Security Group (restricted to your IP)"
    echo "  • Metrics sent directly to OCI Monitoring"
    echo ""
fi

echo ""
read -p "Proceed with this architecture? [Y/n]: " PROCEED
PROCEED="${PROCEED:-Y}"

if [[ ! "$PROCEED" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[INFO]${NC} Setup cancelled by user"
    exit 0
fi

#######################################
# Update Configuration
#######################################
echo ""
echo -e "${BLUE}[INFO]${NC} Updating configuration..."

# Load existing config or create new
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Update deployment mode
if [ "$DEPLOYMENT_MODE" = "vm" ]; then
    sed -i.bak "s/^export ENABLE_MANAGEMENT_AGENT=.*/export ENABLE_MANAGEMENT_AGENT=\"false\"  # Using VM instead/" "$CONFIG_FILE" || \
        echo 'export ENABLE_MANAGEMENT_AGENT="false"' >> "$CONFIG_FILE"

    echo 'export DEPLOY_MONITORING_VM="true"' >> "$CONFIG_FILE"
    echo 'export ENABLE_GRAFANA="true"' >> "$CONFIG_FILE"
    echo "export SSH_PUBLIC_KEY=\"$SSH_PUBLIC_KEY\"" >> "$CONFIG_FILE"
    echo 'export GRAFANA_ADMIN_PASSWORD="'$(openssl rand -base64 16)'"' >> "$CONFIG_FILE"
else
    sed -i.bak "s/^export ENABLE_MANAGEMENT_AGENT=.*/export ENABLE_MANAGEMENT_AGENT=\"true\"  # Sidecar pattern/" "$CONFIG_FILE" || \
        echo 'export ENABLE_MANAGEMENT_AGENT="true"' >> "$CONFIG_FILE"

    echo 'export DEPLOY_MONITORING_VM="false"' >> "$CONFIG_FILE"
fi

# Update NSG configuration
echo "export CREATE_NSG=\"true\"" >> "$CONFIG_FILE"
echo "export ALLOWED_CIDR=\"$ALLOWED_CIDR\"" >> "$CONFIG_FILE"

# Clean up backup
rm -f "${CONFIG_FILE}.bak"

echo -e "${GREEN}[SUCCESS]${NC} Configuration updated"

#######################################
# Security Information
#######################################
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SECURITY CONFIGURATION${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✓ Network Security Group will be created${NC}"
echo -e "  Allowed IP: ${CYAN}$ALLOWED_CIDR${NC}"
echo ""
echo "  Allowed ports from your IP:"
if [ "$DEPLOYMENT_MODE" = "vm" ]; then
    echo "  • SSH (22)      - VM management"
    echo "  • HTTP (80)     - Container access"
    echo "  • Grafana (3000) - Dashboard access"
    echo "  • Prometheus (9090) - Metrics API"
else
    echo "  • HTTP (80)     - Container access"
    echo "  • Prometheus (9090) - Metrics endpoint"
fi
echo ""
echo -e "${YELLOW}[INFO]${NC} All other IPs will be blocked"
echo ""

#######################################
# Next Steps
#######################################
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  NEXT STEPS${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Review configuration: ${CYAN}$CONFIG_FILE${NC}"
echo "2. Deploy the infrastructure:"
echo "   ${YELLOW}cd $PROJECT_ROOT${NC}"
echo "   ${YELLOW}./scripts/deploy.sh deploy${NC}"
echo ""

if [ "$DEPLOYMENT_MODE" = "vm" ]; then
    echo "3. After deployment, access Grafana:"
    echo "   URL will be displayed after deployment"
    echo "   Username: ${CYAN}admin${NC}"
    echo "   Password: ${CYAN}(generated, check output)${NC}"
    echo ""
    echo "4. Add container instance targets to Prometheus"
    echo "   (automatically configured during deployment)"
    echo ""
fi

echo -e "${GREEN}[INFO]${NC} Setup complete! Ready to deploy."
echo ""
