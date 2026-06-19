#!/bin/bash
#######################################
# Build and Push All Custom Container Images to OCIR
#
# This script builds:
# 1. Management Agent Sidecar
# 2. Prometheus Sidecar
# 3. Application with Metrics
# 4. Log Forwarder Sidecar
#
# After successful build and push, it automatically updates
# config/oci-monitoring.env with the new image URLs.
#
# Usage: ./build-all.sh [--skip-push] [--version VERSION]
#######################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
VERSION="${VERSION:-1.0.0}"
SKIP_PUSH=false
BUILD_PLATFORM="linux/amd64"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-push)
      SKIP_PUSH=true
      shift
      ;;
    --version)
      VERSION="$2"
      shift 2
      ;;
    --platform)
      BUILD_PLATFORM="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --skip-push         Build images but don't push to OCIR"
      echo "  --version VERSION   Set image version (default: 1.0.0)"
      echo "  --platform PLATFORM Set build platform (default: linux/amd64)"
      echo "  -h, --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Load configuration
CONFIG_FILE="${PROJECT_ROOT}/config/oci-monitoring.env"
if [ -f "$CONFIG_FILE" ]; then
  echo -e "${BLUE}Loading configuration from $CONFIG_FILE${NC}"
  source "$CONFIG_FILE"
else
  echo -e "${YELLOW}Warning: Configuration file not found at $CONFIG_FILE${NC}"
  echo -e "${YELLOW}Using default values${NC}"
fi

# Get OCI namespace if not set
if [ -z "$OCIR_NAMESPACE" ]; then
  echo -e "${BLUE}Getting OCI namespace...${NC}"
  OCIR_NAMESPACE=$(oci os ns get --query 'data' --raw-output 2>/dev/null || echo "")
  if [ -z "$OCIR_NAMESPACE" ]; then
    echo -e "${RED}Error: Could not determine OCIR namespace${NC}"
    echo -e "${YELLOW}Please set OCIR_NAMESPACE in config/oci-monitoring.env${NC}"
    exit 1
  fi
fi

# Set defaults if not configured
OCIR_REGION="${OCIR_REGION:-fra}"
OCIR_ENDPOINT="${OCIR_ENDPOINT:-${OCIR_REGION}.ocir.io}"
OCIR_REPO_BASE="${OCIR_ENDPOINT}/${OCIR_NAMESPACE}/oci-monitoring"

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Building OCI Monitoring Container Images             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  OCIR Region:    ${OCIR_REGION}"
echo -e "  OCIR Namespace: ${OCIR_NAMESPACE}"
echo -e "  OCIR Endpoint:  ${OCIR_ENDPOINT}"
echo -e "  Version:        ${VERSION}"
echo -e "  Platform:       ${BUILD_PLATFORM}"
echo -e "  Skip Push:      ${SKIP_PUSH}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo -e "${RED}Error: Docker is not installed${NC}"
  exit 1
fi

# Check if logged into OCIR (only if not skipping push)
if [ "$SKIP_PUSH" = false ]; then
  echo -e "${BLUE}Checking OCIR authentication...${NC}"
  if [ -z "$OCIR_USERNAME" ] || [ -z "$OCIR_PASSWORD" ]; then
    echo -e "${YELLOW}Warning: OCIR credentials not set${NC}"
    echo -e "${YELLOW}Please login to OCIR manually:${NC}"
    echo -e "  docker login ${OCIR_ENDPOINT}"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
  else
    echo -e "${BLUE}Logging into OCIR...${NC}"
    echo "$OCIR_PASSWORD" | docker login -u "$OCIR_USERNAME" --password-stdin "$OCIR_ENDPOINT" || {
      echo -e "${RED}Error: Failed to login to OCIR${NC}"
      exit 1
    }
  fi
fi

#######################################
# Build Management Agent Sidecar
#######################################
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Management Agent Sidecar${NC}"
echo -e "${GREEN}========================================${NC}"

IMAGE_NAME="mgmt-agent-sidecar"
LOCAL_TAG="${IMAGE_NAME}:${VERSION}"
OCIR_TAG="${OCIR_REPO_BASE}/${IMAGE_NAME}:${VERSION}"
OCIR_TAG_LATEST="${OCIR_REPO_BASE}/${IMAGE_NAME}:latest"

cd "${SCRIPT_DIR}/management-agent"
echo -e "${BLUE}Building ${LOCAL_TAG}...${NC}"
docker build --platform "${BUILD_PLATFORM}" -t "${LOCAL_TAG}" .

echo -e "${BLUE}Tagging for OCIR: ${OCIR_TAG}${NC}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG_LATEST}"

if [ "$SKIP_PUSH" = false ]; then
  echo -e "${BLUE}Pushing to OCIR...${NC}"
  docker push "${OCIR_TAG}"
  docker push "${OCIR_TAG_LATEST}"
  echo -e "${GREEN}✓ Management Agent Sidecar pushed successfully${NC}"
else
  echo -e "${YELLOW}Skipping push (--skip-push enabled)${NC}"
fi

#######################################
# Build Prometheus Sidecar
#######################################
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Prometheus Sidecar${NC}"
echo -e "${GREEN}========================================${NC}"

IMAGE_NAME="prometheus-sidecar"
LOCAL_TAG="${IMAGE_NAME}:${VERSION}"
OCIR_TAG="${OCIR_REPO_BASE}/${IMAGE_NAME}:${VERSION}"
OCIR_TAG_LATEST="${OCIR_REPO_BASE}/${IMAGE_NAME}:latest"

cd "${SCRIPT_DIR}/prometheus"
echo -e "${BLUE}Building ${LOCAL_TAG}...${NC}"
docker build --platform "${BUILD_PLATFORM}" -t "${LOCAL_TAG}" .

echo -e "${BLUE}Tagging for OCIR: ${OCIR_TAG}${NC}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG_LATEST}"

if [ "$SKIP_PUSH" = false ]; then
  echo -e "${BLUE}Pushing to OCIR...${NC}"
  docker push "${OCIR_TAG}"
  docker push "${OCIR_TAG_LATEST}"
  echo -e "${GREEN}✓ Prometheus Sidecar pushed successfully${NC}"
else
  echo -e "${YELLOW}Skipping push (--skip-push enabled)${NC}"
fi

#######################################
# Build Application with Metrics
#######################################
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Application with Metrics${NC}"
echo -e "${GREEN}========================================${NC}"

IMAGE_NAME="app-with-metrics"
LOCAL_TAG="${IMAGE_NAME}:${VERSION}"
OCIR_TAG="${OCIR_REPO_BASE}/${IMAGE_NAME}:${VERSION}"
OCIR_TAG_LATEST="${OCIR_REPO_BASE}/${IMAGE_NAME}:latest"

cd "${SCRIPT_DIR}/app-with-metrics"
echo -e "${BLUE}Building ${LOCAL_TAG}...${NC}"
docker build --platform "${BUILD_PLATFORM}" -t "${LOCAL_TAG}" .

echo -e "${BLUE}Tagging for OCIR: ${OCIR_TAG}${NC}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG_LATEST}"

if [ "$SKIP_PUSH" = false ]; then
  echo -e "${BLUE}Pushing to OCIR...${NC}"
  docker push "${OCIR_TAG}"
  docker push "${OCIR_TAG_LATEST}"
  echo -e "${GREEN}✓ Application with Metrics pushed successfully${NC}"
else
  echo -e "${YELLOW}Skipping push (--skip-push enabled)${NC}"
fi

#######################################
# Build Log Forwarder Sidecar
#######################################
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Log Forwarder Sidecar${NC}"
echo -e "${GREEN}========================================${NC}"

IMAGE_NAME="log-forwarder-sidecar"
LOCAL_TAG="${IMAGE_NAME}:${VERSION}"
OCIR_TAG="${OCIR_REPO_BASE}/${IMAGE_NAME}:${VERSION}"
OCIR_TAG_LATEST="${OCIR_REPO_BASE}/${IMAGE_NAME}:latest"

cd "${SCRIPT_DIR}/log-forwarder"
echo -e "${BLUE}Building ${LOCAL_TAG}...${NC}"
docker build --platform "${BUILD_PLATFORM}" -t "${LOCAL_TAG}" .

echo -e "${BLUE}Tagging for OCIR: ${OCIR_TAG}${NC}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG}"
docker tag "${LOCAL_TAG}" "${OCIR_TAG_LATEST}"

if [ "$SKIP_PUSH" = false ]; then
  echo -e "${BLUE}Pushing to OCIR...${NC}"
  docker push "${OCIR_TAG}"
  docker push "${OCIR_TAG_LATEST}"
  echo -e "${GREEN}✓ Log Forwarder Sidecar pushed successfully${NC}"
else
  echo -e "${YELLOW}Skipping push (--skip-push enabled)${NC}"
fi

#######################################
# Summary
#######################################
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Build Complete!                                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Built images:${NC}"
echo -e "  1. ${OCIR_REPO_BASE}/mgmt-agent-sidecar:${VERSION}"
echo -e "  2. ${OCIR_REPO_BASE}/prometheus-sidecar:${VERSION}"
echo -e "  3. ${OCIR_REPO_BASE}/app-with-metrics:${VERSION}"
echo -e "  4. ${OCIR_REPO_BASE}/log-forwarder-sidecar:${VERSION}"
echo ""

if [ "$SKIP_PUSH" = false ]; then
  echo -e "${GREEN}All images have been pushed to OCIR successfully!${NC}"
  echo ""

  # Update config/oci-monitoring.env file automatically
  echo -e "${BLUE}Updating config/oci-monitoring.env with new image URLs...${NC}"

  # Define new image URLs
  MGMT_AGENT_IMAGE="${OCIR_REPO_BASE}/mgmt-agent-sidecar:${VERSION}"
  PROMETHEUS_IMAGE="${OCIR_REPO_BASE}/prometheus-sidecar:${VERSION}"
  APP_IMAGE="${OCIR_REPO_BASE}/app-with-metrics:${VERSION}"
  LOG_FORWARDER_IMAGE="${OCIR_REPO_BASE}/log-forwarder-sidecar:${VERSION}"

  # Update or add image URLs in config file
  if [ -f "$CONFIG_FILE" ]; then
    # Update MGMT_AGENT_SIDECAR_IMAGE
    if grep -q "^export MGMT_AGENT_SIDECAR_IMAGE=" "$CONFIG_FILE"; then
      sed -i.bak "s|^export MGMT_AGENT_SIDECAR_IMAGE=.*|export MGMT_AGENT_SIDECAR_IMAGE=\"${MGMT_AGENT_IMAGE}\"|" "$CONFIG_FILE"
    else
      echo "export MGMT_AGENT_SIDECAR_IMAGE=\"${MGMT_AGENT_IMAGE}\"" >> "$CONFIG_FILE"
    fi

    # Update PROMETHEUS_SIDECAR_IMAGE
    if grep -q "^export PROMETHEUS_SIDECAR_IMAGE=" "$CONFIG_FILE"; then
      sed -i.bak "s|^export PROMETHEUS_SIDECAR_IMAGE=.*|export PROMETHEUS_SIDECAR_IMAGE=\"${PROMETHEUS_IMAGE}\"|" "$CONFIG_FILE"
    else
      echo "export PROMETHEUS_SIDECAR_IMAGE=\"${PROMETHEUS_IMAGE}\"" >> "$CONFIG_FILE"
    fi

    # Update APP_WITH_METRICS_IMAGE
    if grep -q "^export APP_WITH_METRICS_IMAGE=" "$CONFIG_FILE"; then
      sed -i.bak "s|^export APP_WITH_METRICS_IMAGE=.*|export APP_WITH_METRICS_IMAGE=\"${APP_IMAGE}\"|" "$CONFIG_FILE"
    else
      echo "export APP_WITH_METRICS_IMAGE=\"${APP_IMAGE}\"" >> "$CONFIG_FILE"
    fi

    # Update LOG_FORWARDER_SIDECAR_IMAGE
    if grep -q "^export LOG_FORWARDER_SIDECAR_IMAGE=" "$CONFIG_FILE"; then
      sed -i.bak "s|^export LOG_FORWARDER_SIDECAR_IMAGE=.*|export LOG_FORWARDER_SIDECAR_IMAGE=\"${LOG_FORWARDER_IMAGE}\"|" "$CONFIG_FILE"
    else
      echo "export LOG_FORWARDER_SIDECAR_IMAGE=\"${LOG_FORWARDER_IMAGE}\"" >> "$CONFIG_FILE"
    fi

    # Also update CONTAINER_IMAGE to use the app-with-metrics image
    if grep -q "^export CONTAINER_IMAGE=" "$CONFIG_FILE"; then
      sed -i.bak "s|^export CONTAINER_IMAGE=.*|export CONTAINER_IMAGE=\"${APP_IMAGE}\"|" "$CONFIG_FILE"
    fi

    # Clean up backup file
    rm -f "${CONFIG_FILE}.bak"

    echo -e "${GREEN}✓ Configuration file updated successfully!${NC}"
    echo ""
    echo -e "${BLUE}Updated image URLs:${NC}"
    echo -e "  MGMT_AGENT_SIDECAR_IMAGE=\"${MGMT_AGENT_IMAGE}\""
    echo -e "  PROMETHEUS_SIDECAR_IMAGE=\"${PROMETHEUS_IMAGE}\""
    echo -e "  APP_WITH_METRICS_IMAGE=\"${APP_IMAGE}\""
    echo -e "  LOG_FORWARDER_SIDECAR_IMAGE=\"${LOG_FORWARDER_IMAGE}\""
    echo -e "  CONTAINER_IMAGE=\"${APP_IMAGE}\""
  else
    echo -e "${YELLOW}Warning: Config file not found at $CONFIG_FILE${NC}"
    echo -e "${BLUE}Please create it with the following content:${NC}"
    echo -e "  export MGMT_AGENT_SIDECAR_IMAGE=\"${MGMT_AGENT_IMAGE}\""
    echo -e "  export PROMETHEUS_SIDECAR_IMAGE=\"${PROMETHEUS_IMAGE}\""
    echo -e "  export APP_WITH_METRICS_IMAGE=\"${APP_IMAGE}\""
    echo -e "  export LOG_FORWARDER_SIDECAR_IMAGE=\"${LOG_FORWARDER_IMAGE}\""
  fi

  echo ""
  echo -e "${BLUE}Next steps:${NC}"
  echo -e "  1. Review updated config/oci-monitoring.env"
  echo -e "  2. Run: ./scripts/deploy.sh deploy"
else
  echo -e "${YELLOW}Images built locally but not pushed to OCIR${NC}"
  echo -e "${BLUE}To push images, run without --skip-push flag${NC}"
fi

echo ""
