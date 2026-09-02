#!/usr/bin/env bash
# =============================================================================
# Sentiment Intelligence — Build & Deploy Script
#
# This script:
#   1. Builds Docker images for the backend and frontend
#   2. Pushes them to OCI Container Registry (OCIR)
#   3. Applies Terraform to create/update infrastructure
#   4. Creates the OCIR pull secret in Kubernetes
#
# Prerequisites:
#   - OCI CLI configured (oci session authenticate or ~/.oci/config)
#   - Docker installed and running
#   - Terraform >= 1.5
#   - kubectl installed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---- Configuration (override via environment) ----
REGION="${OCI_REGION:-eu-frankfurt-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REPO_NAME="${OCIR_REPO_NAME:-sentiment-intel}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [COMMAND]

Commands:
  build       Build Docker images locally
  push        Push Docker images to OCIR
  infra       Apply Terraform infrastructure
  deploy      Full deployment (build + push + infra)
  destroy     Tear down all infrastructure
  kubeconfig  Set up kubectl for the OKE cluster
  help        Show this help message

Environment variables:
  OCI_REGION      OCI region (default: eu-frankfurt-1)
  IMAGE_TAG       Docker image tag (default: latest)
  OCIR_REPO_NAME  OCIR repository name (default: sentiment-intel)
EOF
}

get_ocir_info() {
  NAMESPACE=$(oci os ns get --query 'data' --raw-output 2>/dev/null)
  REGION_KEY=$(oci iam region list --query "data[?name=='${REGION}'].key | [0]" --raw-output 2>/dev/null | tr '[:upper:]' '[:lower:]')
  OCIR_URL="${REGION_KEY}.ocir.io/${NAMESPACE}/${REPO_NAME}"
  log "OCIR URL: ${OCIR_URL}"
}

cmd_build() {
  log "Building Docker images..."
  get_ocir_info

  log "Building backend image..."
  docker build -t "${OCIR_URL}/backend:${IMAGE_TAG}" "${PROJECT_ROOT}/backend/"

  log "Building frontend image..."
  docker build -t "${OCIR_URL}/frontend:${IMAGE_TAG}" \
    --build-arg VITE_API_BASE_URL="/api" \
    "${PROJECT_ROOT}/frontend/"

  log "Docker images built successfully."
}

cmd_push() {
  get_ocir_info

  log "Logging into OCIR..."
  docker login "${REGION_KEY}.ocir.io"

  log "Pushing backend image..."
  docker push "${OCIR_URL}/backend:${IMAGE_TAG}"

  log "Pushing frontend image..."
  docker push "${OCIR_URL}/frontend:${IMAGE_TAG}"

  log "Images pushed successfully."
}

cmd_infra() {
  log "Applying Terraform infrastructure..."
  cd "$SCRIPT_DIR"

  if [ ! -f terraform.tfvars ]; then
    err "terraform.tfvars not found. Copy terraform.tfvars.example and fill in your values."
    exit 1
  fi

  terraform init -upgrade
  terraform plan -out=tfplan
  terraform apply tfplan
  rm -f tfplan

  log "Infrastructure deployed successfully."
}

cmd_kubeconfig() {
  log "Setting up kubectl..."
  cd "$SCRIPT_DIR"

  CLUSTER_ID=$(terraform output -raw oke_cluster_id)
  oci ce cluster create-kubeconfig \
    --cluster-id "$CLUSTER_ID" \
    --region "$REGION" \
    --token-version 2.0.0 \
    --kube-endpoint PUBLIC_ENDPOINT

  log "kubectl configured. Testing connection..."
  kubectl get nodes
}

cmd_deploy() {
  cmd_build
  cmd_push
  cmd_infra

  log "Setting up kubeconfig..."
  cmd_kubeconfig

  log "Creating OCIR pull secret..."
  get_ocir_info
  NAMESPACE_K8S=$(terraform -chdir="$SCRIPT_DIR" output -raw app_namespace)

  kubectl create secret docker-registry ocir-secret \
    --namespace "$NAMESPACE_K8S" \
    --docker-server="${REGION_KEY}.ocir.io" \
    --docker-username="${NAMESPACE}/oracleidentitycloudservice/<your-email>" \
    --docker-password='<your-auth-token>' \
    --docker-email='<your-email>' \
    --dry-run=client -o yaml | kubectl apply -f -

  warn "Update the OCIR secret with your actual credentials:"
  warn "  kubectl edit secret ocir-secret -n ${NAMESPACE_K8S}"

  log "Restarting deployments to pick up images..."
  kubectl rollout restart deployment/backend -n "$NAMESPACE_K8S"
  kubectl rollout restart deployment/frontend -n "$NAMESPACE_K8S"

  log "Deployment complete!"
  log "Frontend URL will be available at the LoadBalancer external IP:"
  kubectl get svc frontend-service -n "$NAMESPACE_K8S"
}

cmd_destroy() {
  warn "This will DESTROY all infrastructure!"
  read -rp "Are you sure? (yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    log "Cancelled."
    exit 0
  fi

  cd "$SCRIPT_DIR"
  terraform destroy
  log "Infrastructure destroyed."
}

# ---- Main ----
case "${1:-help}" in
  build)      cmd_build ;;
  push)       cmd_push ;;
  infra)      cmd_infra ;;
  deploy)     cmd_deploy ;;
  destroy)    cmd_destroy ;;
  kubeconfig) cmd_kubeconfig ;;
  help|*)     usage ;;
esac
