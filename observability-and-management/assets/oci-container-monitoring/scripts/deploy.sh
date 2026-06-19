#!/bin/bash
#######################################
# OCI Container Instance Monitoring
# Main Deployment Orchestration Script
#
# This script automates the complete deployment of:
# - OCI Container Instances
# - Logging infrastructure
# - Management Agent for Prometheus metrics
# - Monitoring dashboards and alarms
#
# Author: DevSecOps Team
# Version: 1.0.0
#######################################

set -euo pipefail

#######################################
# Script Configuration
#######################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${PROJECT_ROOT}/config/oci-monitoring.env"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
OUTPUT_DIR="${PROJECT_ROOT}/output"
LOGS_DIR="${PROJECT_ROOT}/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="${LOGS_DIR}/deployment-$(date +%Y%m%d-%H%M%S).log"

#######################################
# Logging Functions
#######################################
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $*" | tee -a "$LOG_FILE"
}

#######################################
# Banner
#######################################
print_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   OCI Container Instance Monitoring Automation                ║
║   Comprehensive deployment and monitoring solution            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

#######################################
# Prerequisite Checks
#######################################
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_tools=()

    # Check required commands
    command -v oci >/dev/null 2>&1 || missing_tools+=("oci-cli")
    command -v terraform >/dev/null 2>&1 || missing_tools+=("terraform")
    command -v jq >/dev/null 2>&1 || missing_tools+=("jq")
    command -v curl >/dev/null 2>&1 || missing_tools+=("curl")

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again"
        exit 1
    fi

    # Check OCI CLI configuration
    if ! oci iam region list --profile "${OCI_CLI_PROFILE:-DEFAULT}" >/dev/null 2>&1; then
        log_error "OCI CLI is not configured correctly"
        log_error "Run 'oci setup config' to configure OCI CLI"
        exit 1
    fi

    # Check Terraform version
    local tf_version
    tf_version=$(terraform version -json | jq -r '.terraform_version')
    log_info "Terraform version: $tf_version"

    # Verify minimum Terraform version (1.5.0)
    if ! printf '%s\n%s\n' "1.5.0" "$tf_version" | sort -V -C; then
        log_error "Terraform version must be 1.5.0 or higher"
        exit 1
    fi

    log_success "All prerequisites checked successfully"
}

#######################################
# Load Configuration
#######################################
load_config() {
    log_info "Loading configuration from ${CONFIG_FILE}..."

    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        log_error "Please create the configuration file from the template"
        exit 1
    fi

    # Source configuration file
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"

    # Validate required variables
    local required_vars=(
        "OCI_REGION"
        "OCI_TENANCY_OCID"
        "OCI_COMPARTMENT_OCID"
        "VCN_OCID"
        "SUBNET_OCID"
        "CONTAINER_INSTANCE_NAME"
        "CONTAINER_IMAGE"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required configuration variables: ${missing_vars[*]}"
        exit 1
    fi

    log_success "Configuration loaded successfully"
}

#######################################
# Create Output Directories
#######################################
create_directories() {
    log_info "Creating output directories..."

    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "${TERRAFORM_DIR}/output"

    log_success "Output directories created"
}

#######################################
# Generate Terraform Variables File
#######################################
generate_tfvars() {
    log_info "Generating Terraform variables file..."

    local tfvars_file="${TERRAFORM_DIR}/terraform.tfvars"

    # Pre-process container environment variables
    local container_env_map="{}"
    if [ -n "${CONTAINER_ENV_VARS}" ]; then
        # Parse KEY=VALUE,KEY2=VALUE2 into HCL map format
        container_env_map="{"
        IFS=',' read -ra PAIRS <<< "${CONTAINER_ENV_VARS}"
        for pair in "${PAIRS[@]}"; do
            if [[ $pair =~ ^([^=]+)=(.+)$ ]]; then
                key="${BASH_REMATCH[1]}"
                value="${BASH_REMATCH[2]}"
                container_env_map="${container_env_map}\"${key}\" = \"${value}\", "
            fi
        done
        container_env_map="${container_env_map%%, }}"  # Remove trailing comma and space
    fi

    # Pre-process NSG OCIDs
    local nsg_list="[]"
    if [ -n "${NSG_OCIDS}" ]; then
        # Parse comma-separated OCIDs into HCL list format
        nsg_list="["
        IFS=',' read -ra OCIDS <<< "${NSG_OCIDS}"
        for ocid in "${OCIDS[@]}"; do
            nsg_list="${nsg_list}\"${ocid}\", "
        done
        nsg_list="${nsg_list%%, }]"  # Remove trailing comma and space, add closing bracket
    fi

    cat > "$tfvars_file" << EOF
# Auto-generated Terraform variables
# Generated on: $(date)

# Provider Configuration
region           = "${OCI_REGION}"
tenancy_ocid     = "${OCI_TENANCY_OCID}"
compartment_ocid = "${OCI_COMPARTMENT_OCID}"

# Container Instance Configuration
container_instance_name = "${CONTAINER_INSTANCE_NAME}"
container_image        = "${CONTAINER_IMAGE}"
container_shape        = "${CONTAINER_SHAPE}"
container_ocpus        = ${CONTAINER_OCPUS}
container_memory_gb    = ${CONTAINER_MEMORY_GB}
container_count        = ${CONTAINER_COUNT}
container_port         = ${CONTAINER_PORT}
availability_domain    = ${AVAILABILITY_DOMAIN}

# Container Environment Variables (as map)
container_env_vars = ${container_env_map}

# Networking
vcn_ocid         = "${VCN_OCID}"
subnet_ocid      = "${SUBNET_OCID}"
assign_public_ip = ${ASSIGN_PUBLIC_IP}
nsg_ocids        = ${nsg_list}

# Logging Configuration
enable_logging     = ${ENABLE_LOGGING}
log_group_name     = "${LOG_GROUP_NAME}"
log_retention_days = ${LOG_RETENTION_DAYS}
enable_audit_logs  = ${ENABLE_AUDIT_LOGS}

# Management Agent Configuration (Legacy)
enable_management_agent     = ${ENABLE_MANAGEMENT_AGENT}
mgmt_agent_name            = "${MGMT_AGENT_NAME}"
mgmt_agent_install_key_name = "${MGMT_AGENT_INSTALL_KEY_NAME}"
prometheus_scrape_interval  = ${PROMETHEUS_SCRAPE_INTERVAL}
prometheus_metrics_port     = ${PROMETHEUS_METRICS_PORT}
prometheus_metrics_path     = "${PROMETHEUS_METRICS_PATH}"

# Sidecar Architecture Configuration
enable_shared_volumes             = ${ENABLE_SHARED_VOLUMES:-false}
enable_management_agent_sidecar   = ${ENABLE_MANAGEMENT_AGENT_SIDECAR:-false}
enable_prometheus_sidecar         = ${ENABLE_PROMETHEUS_SIDECAR:-false}
enable_log_forwarder_sidecar      = ${ENABLE_LOG_FORWARDER_SIDECAR:-false}

# Sidecar Container Images
mgmt_agent_sidecar_image       = "${MGMT_AGENT_SIDECAR_IMAGE:-}"
prometheus_sidecar_image       = "${PROMETHEUS_SIDECAR_IMAGE:-}"
log_forwarder_sidecar_image    = "${LOG_FORWARDER_SIDECAR_IMAGE:-}"

# Sidecar Resource Allocation
mgmt_agent_sidecar_memory_gb    = ${MGMT_AGENT_SIDECAR_MEMORY_GB:-1.0}
mgmt_agent_sidecar_ocpus        = ${MGMT_AGENT_SIDECAR_OCPUS:-0.25}
prometheus_sidecar_memory_gb    = ${PROMETHEUS_SIDECAR_MEMORY_GB:-1.0}
prometheus_sidecar_ocpus        = ${PROMETHEUS_SIDECAR_OCPUS:-0.25}
log_forwarder_sidecar_memory_gb = ${LOG_FORWARDER_SIDECAR_MEMORY_GB:-0.5}
log_forwarder_sidecar_ocpus     = ${LOG_FORWARDER_SIDECAR_OCPUS:-0.125}

# Prometheus Exporters Configuration
enable_prometheus_exporters  = ${ENABLE_PROMETHEUS_EXPORTERS:-true}
enable_nginx_exporter       = ${ENABLE_NGINX_EXPORTER:-false}
enable_redis_exporter       = ${ENABLE_REDIS_EXPORTER:-false}
enable_postgres_exporter    = ${ENABLE_POSTGRES_EXPORTER:-false}
enable_mysql_exporter       = ${ENABLE_MYSQL_EXPORTER:-false}
enable_blackbox_exporter    = ${ENABLE_BLACKBOX_EXPORTER:-false}

# Monitoring & Dashboards
create_dashboard       = ${CREATE_DASHBOARD}
dashboard_name        = "${DASHBOARD_NAME}"
metrics_namespace     = "${METRICS_NAMESPACE}"
enable_alarms         = ${ENABLE_ALARMS}
cpu_alarm_threshold   = ${CPU_ALARM_THRESHOLD}
memory_alarm_threshold = ${MEMORY_ALARM_THRESHOLD}

# Notification (if configured)
notification_topic_ocid = "${NOTIFICATION_TOPIC_OCID}"

# OCIR Authentication (if using private images)
ocir_username   = "${OCIR_USERNAME}"
ocir_auth_token = "${OCIR_AUTH_TOKEN}"

# Tags
freeform_tags = ${FREEFORM_TAGS}
defined_tags  = ${DEFINED_TAGS}
EOF

    log_success "Terraform variables file generated: $tfvars_file"
}

#######################################
# Initialize Terraform
#######################################
terraform_init() {
    log_info "Initializing Terraform..."

    cd "$TERRAFORM_DIR"

    if [ "$VERBOSE" = "true" ]; then
        terraform init
    else
        terraform init > /dev/null 2>&1
    fi

    log_success "Terraform initialized successfully"
}

#######################################
# Validate Terraform Configuration
#######################################
terraform_validate() {
    log_info "Validating Terraform configuration..."

    cd "$TERRAFORM_DIR"

    if terraform validate; then
        log_success "Terraform configuration is valid"
    else
        log_error "Terraform validation failed"
        exit 1
    fi
}

#######################################
# Plan Terraform Changes
#######################################
terraform_plan() {
    log_info "Planning Terraform changes..."

    cd "$TERRAFORM_DIR"

    local plan_file="${TF_PLAN_FILE:-tfplan}"

    if terraform plan -out="$plan_file"; then
        log_success "Terraform plan created: $plan_file"
    else
        log_error "Terraform planning failed"
        exit 1
    fi

    # Show plan summary
    log_info "Plan summary:"
    terraform show -no-color "$plan_file" | grep -E "Plan:|No changes" || true
}

#######################################
# Apply Terraform Changes
#######################################
terraform_apply() {
    log_info "Applying Terraform changes..."

    cd "$TERRAFORM_DIR"

    local plan_file="${TF_PLAN_FILE:-tfplan}"

    if [ "$DRY_RUN" = "true" ]; then
        log_warn "Dry run mode enabled - skipping apply"
        return 0
    fi

    if [ "$AUTO_APPROVE" = "true" ]; then
        terraform apply -auto-approve "$plan_file"
    else
        log_warn "Review the plan above. Do you want to apply these changes?"
        read -p "Enter 'yes' to continue: " -r
        if [[ $REPLY =~ ^[Yy]es$ ]]; then
            terraform apply "$plan_file"
        else
            log_error "Deployment cancelled by user"
            exit 1
        fi
    fi

    log_success "Terraform changes applied successfully"
}

#######################################
# Extract Terraform Outputs
#######################################
extract_outputs() {
    log_info "Extracting Terraform outputs..."

    cd "$TERRAFORM_DIR"

    # Save outputs to JSON file
    terraform output -json > "${OUTPUT_DIR}/terraform-outputs.json"

    # Extract key values
    CONTAINER_INSTANCE_ID=$(terraform output -raw container_instance_id 2>/dev/null || echo "")
    CONTAINER_PRIVATE_IP=$(terraform output -raw container_private_ip 2>/dev/null || echo "")
    CONTAINER_PUBLIC_IP=$(terraform output -raw container_public_ip 2>/dev/null || echo "")
    LOG_GROUP_ID=$(terraform output -raw log_group_id 2>/dev/null || echo "")

    # Display summary
    log_info "Deployment Summary:"
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║             Deployment Summary                        ║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} Container Instance ID: ${GREEN}${CONTAINER_INSTANCE_ID:0:40}...${NC}"
    echo -e "${CYAN}║${NC} Private IP: ${GREEN}${CONTAINER_PRIVATE_IP}${NC}"
    [ -n "$CONTAINER_PUBLIC_IP" ] && echo -e "${CYAN}║${NC} Public IP: ${GREEN}${CONTAINER_PUBLIC_IP}${NC}"
    [ -n "$LOG_GROUP_ID" ] && echo -e "${CYAN}║${NC} Log Group ID: ${GREEN}${LOG_GROUP_ID:0:40}...${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"

    log_success "Outputs extracted to: ${OUTPUT_DIR}/terraform-outputs.json"
}

#######################################
# Create Dashboard
#######################################
create_dashboard() {
    if [ "$CREATE_DASHBOARD" != "true" ]; then
        log_info "Dashboard creation disabled - skipping"
        return 0
    fi

    log_info "Creating monitoring dashboard..."

    # Substitute variables in dashboard template
    local dashboard_config="${OUTPUT_DIR}/dashboard-config.json"
    sed -e "s|\${COMPARTMENT_OCID}|${OCI_COMPARTMENT_OCID}|g" \
        -e "s|\${CONTAINER_INSTANCE_ID}|${CONTAINER_INSTANCE_ID}|g" \
        -e "s|\${METRICS_NAMESPACE}|${METRICS_NAMESPACE}|g" \
        "${PROJECT_ROOT}/templates/dashboard-config.json" > "$dashboard_config"

    # Create dashboard using OCI CLI
    if [ "$DRY_RUN" != "true" ]; then
        local dashboard_id
        dashboard_id=$(oci management-dashboard dashboard create \
            --from-json "file://${dashboard_config}" \
            --profile "${OCI_CLI_PROFILE:-DEFAULT}" \
            --query 'data.id' \
            --raw-output 2>/dev/null || echo "")

        if [ -n "$dashboard_id" ]; then
            log_success "Dashboard created: $dashboard_id"
            echo "$dashboard_id" > "${OUTPUT_DIR}/dashboard-id.txt"
        else
            log_warn "Dashboard creation failed or already exists"
        fi
    fi
}

#######################################
# Verify Deployment
#######################################
verify_deployment() {
    log_info "Verifying deployment..."

    local retry_count=0
    local max_retries=${RETRY_ATTEMPTS:-3}

    while [ $retry_count -lt $max_retries ]; do
        # Check container instance state
        local instance_state
        instance_state=$(oci container-instances container-instance get \
            --container-instance-id "$CONTAINER_INSTANCE_ID" \
            --profile "${OCI_CLI_PROFILE:-DEFAULT}" \
            --query 'data."lifecycle-state"' \
            --raw-output 2>/dev/null || echo "UNKNOWN")

        if [ "$instance_state" = "ACTIVE" ]; then
            log_success "Container instance is ACTIVE"
            break
        else
            log_warn "Container instance state: $instance_state (attempt $((retry_count + 1))/$max_retries)"
            sleep "${RETRY_DELAY:-10}"
            ((retry_count++))
        fi
    done

    if [ "$instance_state" != "ACTIVE" ]; then
        log_error "Container instance failed to reach ACTIVE state"
        if [ "$CLEANUP_ON_FAILURE" = "true" ]; then
            cleanup_on_failure
        fi
        exit 1
    fi

    # Test connectivity if public IP is assigned
    if [ -n "$CONTAINER_PUBLIC_IP" ] && [ "$ASSIGN_PUBLIC_IP" = "true" ]; then
        log_info "Testing connectivity to container..."
        if curl -s --connect-timeout 10 "http://${CONTAINER_PUBLIC_IP}:${CONTAINER_PORT}" >/dev/null 2>&1; then
            log_success "Container is accessible via public IP"
        else
            log_warn "Container may not be accessible yet - check security lists and NSGs"
        fi
    fi
}

#######################################
# Cleanup on Failure
#######################################
cleanup_on_failure() {
    log_warn "Cleaning up resources due to failure..."

    cd "$TERRAFORM_DIR"
    terraform destroy -auto-approve || log_error "Cleanup failed"

    log_info "Cleanup completed"
}

#######################################
# Generate Documentation
#######################################
generate_documentation() {
    log_info "Generating deployment documentation..."

    local doc_file="${OUTPUT_DIR}/DEPLOYMENT_INFO.md"

    cat > "$doc_file" << EOF
# OCI Container Instance Monitoring Deployment

**Deployment Date:** $(date)
**Deployment User:** $(whoami)

## Container Instance Details

- **Instance ID:** ${CONTAINER_INSTANCE_ID}
- **Instance Name:** ${CONTAINER_INSTANCE_NAME}
- **Container Image:** ${CONTAINER_IMAGE}
- **Private IP:** ${CONTAINER_PRIVATE_IP}
- **Public IP:** ${CONTAINER_PUBLIC_IP:-N/A}
- **Region:** ${OCI_REGION}

## Resource Configuration

- **Shape:** ${CONTAINER_SHAPE}
- **OCPUs:** ${CONTAINER_OCPUS}
- **Memory:** ${CONTAINER_MEMORY_GB} GB
- **Container Port:** ${CONTAINER_PORT}

## Logging

- **Log Group ID:** ${LOG_GROUP_ID:-N/A}
- **Retention:** ${LOG_RETENTION_DAYS} days

## Monitoring

- **Prometheus Metrics:** ${ENABLE_MANAGEMENT_AGENT}
- **Metrics Port:** ${PROMETHEUS_METRICS_PORT}
- **Scrape Interval:** ${PROMETHEUS_SCRAPE_INTERVAL}s
- **Dashboard Created:** ${CREATE_DASHBOARD}

## Access Information

### OCI Console URLs

- [Container Instance](https://cloud.oracle.com/compute/container-instances/${CONTAINER_INSTANCE_ID}?region=${OCI_REGION})
- [Logging](https://cloud.oracle.com/logging/log-groups/${LOG_GROUP_ID}?region=${OCI_REGION})
- [Monitoring](https://cloud.oracle.com/monitoring/alarms?region=${OCI_REGION}&compartmentId=${OCI_COMPARTMENT_OCID})

### Container Access

\`\`\`bash
# SSH to container (if configured)
# Connect via private IP if in same VCN
ssh user@${CONTAINER_PRIVATE_IP}

# Access via public IP (if enabled)
curl http://${CONTAINER_PUBLIC_IP:-N/A}:${CONTAINER_PORT}
\`\`\`

### View Logs

\`\`\`bash
# Using OCI CLI
oci logging-search search-logs \\
  --search-query "search \"${LOG_GROUP_ID}\" | sort by datetime desc" \\
  --time-start "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S.000Z)" \\
  --time-end "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
\`\`\`

## Management Agent

EOF

    if [ "$ENABLE_MANAGEMENT_AGENT" = "true" ]; then
        cat >> "$doc_file" << EOF
Management agent configuration files are available in:
- \`${OUTPUT_DIR}/install-agent.sh\`
- \`${OUTPUT_DIR}/prometheus-config.yml\`
- \`${OUTPUT_DIR}/service-discovery.json\`

To install the agent on a compute instance:
\`\`\`bash
chmod +x ${OUTPUT_DIR}/install-agent.sh
sudo ${OUTPUT_DIR}/install-agent.sh
\`\`\`
EOF
    fi

    cat >> "$doc_file" << EOF

## Next Steps

1. Verify container is running correctly
2. Check logs in OCI Console
3. Configure additional monitoring as needed
4. Set up alarms and notifications
5. Review dashboard widgets

## Terraform Outputs

See \`${OUTPUT_DIR}/terraform-outputs.json\` for complete output details.

## Cleanup

To destroy all resources:
\`\`\`bash
cd ${TERRAFORM_DIR}
terraform destroy
\`\`\`
EOF

    log_success "Documentation generated: $doc_file"
}

#######################################
# Main Deployment Function
#######################################
main() {
    print_banner

    # Create logs directory
    mkdir -p "$LOGS_DIR"

    log "Starting OCI Container Instance Monitoring deployment..."
    log "Log file: $LOG_FILE"

    # Execute deployment steps
    check_prerequisites
    load_config
    create_directories
    generate_tfvars
    terraform_init
    terraform_validate
    terraform_plan
    terraform_apply
    extract_outputs
    create_dashboard
    verify_deployment
    generate_documentation

    log_success "=================================="
    log_success "Deployment completed successfully!"
    log_success "=================================="
    log_info "Review deployment information in: ${OUTPUT_DIR}/DEPLOYMENT_INFO.md"
    log_info "Terraform outputs: ${OUTPUT_DIR}/terraform-outputs.json"
    log_info "Deployment log: $LOG_FILE"
}

#######################################
# Script Entry Point
#######################################
# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    plan)
        check_prerequisites
        load_config
        create_directories
        generate_tfvars
        terraform_init
        terraform_validate
        terraform_plan
        ;;
    destroy)
        log_warn "Destroying all resources..."
        cd "$TERRAFORM_DIR"
        terraform destroy
        ;;
    validate)
        check_prerequisites
        load_config
        terraform_init
        terraform_validate
        ;;
    *)
        echo "Usage: $0 {deploy|plan|destroy|validate}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  plan     - Generate Terraform plan only"
        echo "  destroy  - Destroy all resources"
        echo "  validate - Validate configuration only"
        exit 1
        ;;
esac
