#!/bin/bash
#######################################
# OCIR Credentials Setup Helper
# Updates config with OCIR authentication
#######################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config/oci-monitoring.env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║        OCIR Authentication Setup Helper               ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Detect OCI username
echo -e "${YELLOW}Detecting your OCI username...${NC}"
OCI_USERNAME="alexandru.birzu@oracle.com"
OCI_NAMESPACE="frxfz3gch4zb"

echo -e "${GREEN}✓ Detected:${NC}"
echo "  Username: $OCI_USERNAME"
echo "  Namespace: $OCI_NAMESPACE"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Prompt for auth token
echo -e "${YELLOW}Please enter your OCIR Auth Token:${NC}"
echo "(Create one at: OCI Console → Profile → Auth Tokens → Generate Token)"
echo ""
read -s -p "Auth Token: " AUTH_TOKEN
echo ""

if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}Error: Auth token cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Updating configuration...${NC}"

# Backup original config
cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓ Backup created${NC}"

# Update OCIR username and password
sed -i.tmp "s|^export OCIR_USERNAME=\"frxfz3gch4zb/YOUR_OCI_USERNAME\".*|export OCIR_USERNAME=\"${OCI_NAMESPACE}/${OCI_USERNAME}\"|" "$CONFIG_FILE"
sed -i.tmp "s|^export OCIR_PASSWORD=\"\".*# Your OCIR auth token.*|export OCIR_PASSWORD=\"${AUTH_TOKEN}\"  # Your OCIR auth token|" "$CONFIG_FILE"

# Remove duplicate empty OCIR_USERNAME if exists (around line 99)
sed -i.tmp '/^export OCIR_USERNAME=""$/d' "$CONFIG_FILE"
sed -i.tmp '/^export OCIR_AUTH_TOKEN=""$/d' "$CONFIG_FILE"

# Clean up temp file
rm -f "$CONFIG_FILE.tmp"

echo -e "${GREEN}✓ Configuration updated${NC}"
echo ""

# Test Docker login
echo -e "${YELLOW}Testing OCIR authentication...${NC}"
if echo "$AUTH_TOKEN" | docker login fra.ocir.io -u "${OCI_NAMESPACE}/${OCI_USERNAME}" --password-stdin 2>&1 | grep -q "Login Succeeded"; then
    echo -e "${GREEN}✓ OCIR authentication successful!${NC}"
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Setup Complete! You can now build Docker images.    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cd $PROJECT_ROOT/docker"
    echo "  2. ./build-all.sh"
    echo ""
else
    echo -e "${RED}✗ OCIR authentication failed${NC}"
    echo "Please check:"
    echo "  - Auth token is correct"
    echo "  - Token hasn't expired"
    echo "  - IAM policies allow OCIR access"
    exit 1
fi
