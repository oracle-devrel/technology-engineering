# Troubleshooting Guide

## Table of Contents
- [Prerequisites Issues](#prerequisites-issues)
- [Configuration Issues](#configuration-issues)
- [Terraform Issues](#terraform-issues)
- [Container Instance Issues](#container-instance-issues)
- [Logging Issues](#logging-issues)
- [Management Agent Issues](#management-agent-issues)
- [Networking Issues](#networking-issues)
- [Performance Issues](#performance-issues)

## Prerequisites Issues

### OCI CLI Authentication Errors

**Problem:** `ServiceError: The user does not have permission to perform this operation`

**Causes:**
- Incorrect OCI CLI configuration
- Missing or incorrect API key
- Insufficient IAM permissions

**Solutions:**

1. Verify OCI CLI configuration:
```bash
cat ~/.oci/config
oci iam region list
```

2. Reconfigure OCI CLI:
```bash
oci setup config
```

3. Test authentication:
```bash
oci iam availability-domain list --compartment-id <tenancy-ocid>
```

4. Verify API key fingerprint matches:
```bash
openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | openssl md5 -c
```

### Terraform Version Issues

**Problem:** `Error: Unsupported Terraform Core version`

**Solution:**
```bash
# Check version
terraform version

# Upgrade Terraform (macOS)
brew upgrade terraform

# Upgrade Terraform (Linux)
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

## Configuration Issues

### Missing Required Variables

**Problem:** `Error: Missing required configuration variables`

**Solution:**

1. Check configuration file exists:
```bash
ls -la config/oci-monitoring.env
```

2. Verify all required variables are set:
```bash
source config/oci-monitoring.env
echo $OCI_COMPARTMENT_OCID
echo $VCN_OCID
echo $SUBNET_OCID
```

3. Run interactive setup if missing:
```bash
./scripts/setup-environment.sh
```

### Invalid OCID Format

**Problem:** `Error: Invalid OCID format`

**Symptoms:**
- OCIDs don't start with `ocid1.`
- OCIDs contain spaces or special characters

**Solution:**

Verify OCID format:
```bash
# Valid OCID format
ocid1.compartment.oc1..aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Get OCIDs from OCI CLI
oci iam compartment list --all --query 'data[*].[name,id]' --output table
oci network vcn list --compartment-id <compartment-ocid> --query 'data[*].[\"display-name\",id]' --output table
```

## Terraform Issues

### State Lock Errors

**Problem:** `Error: Error acquiring the state lock`

**Cause:** Previous Terraform run was interrupted

**Solution:**

1. Check lock info:
```bash
cd terraform
terraform force-unlock <LOCK_ID>
```

2. If lock ID unknown, find in error message or:
```bash
# Delete state lock manually (last resort)
rm -f terraform.tfstate.lock.info
```

### Resource Already Exists

**Problem:** `Error: Resource already exists`

**Solutions:**

1. Import existing resource:
```bash
cd terraform
terraform import module.container_instance.oci_container_instances_container_instance.main <instance-ocid>
```

2. Or remove from Terraform state:
```bash
terraform state rm module.container_instance.oci_container_instances_container_instance.main
```

3. Or destroy and recreate:
```bash
terraform destroy -target=module.container_instance
terraform apply
```

### Provider Authentication Issues

**Problem:** `Error: 401-NotAuthenticated`

**Solutions:**

1. Verify provider configuration in `terraform/provider.tf`

2. Use environment variables:
```bash
export TF_VAR_region="us-ashburn-1"
export TF_VAR_tenancy_ocid="ocid1.tenancy..."
```

3. Or use OCI CLI config:
```bash
# Terraform will use ~/.oci/config by default
terraform init
```

## Container Instance Issues

### Instance Fails to Start

**Problem:** Container instance stuck in `CREATING` or fails to `ACTIVE` state

**Debug Steps:**

1. Check instance status:
```bash
INSTANCE_ID=$(cd terraform && terraform output -raw container_instance_id)
oci container-instances container-instance get \
  --container-instance-id "$INSTANCE_ID" \
  --query 'data.["lifecycle-state","lifecycle-details"]'
```

2. View container logs:
```bash
./scripts/view-logs.sh
# Select "System Logs"
```

3. Check for common issues:
   - Invalid container image
   - Insufficient resources in AD
   - Subnet/VCN misconfiguration
   - Image pull authentication failure

**Solutions:**

**Invalid Image:**
```bash
# Test image locally
docker pull nginx:latest

# Or use known-good image
export CONTAINER_IMAGE="nginx:latest"
```

**Resource Constraints:**
```bash
# Try different availability domain
export AVAILABILITY_DOMAIN="2"

# Or reduce resources
export CONTAINER_OCPUS="1"
export CONTAINER_MEMORY_GB="2"
```

**Image Pull Errors (Private Registry):**
```bash
# Verify OCIR credentials
export OCIR_USERNAME="<namespace>/oracleidentitycloudservice/user@example.com"
export OCIR_AUTH_TOKEN="<valid-token>"

# Test authentication
docker login <region>.ocir.io
```

### Container Instance Crashes

**Problem:** Container starts but crashes immediately

**Debug:**

1. Check application logs:
```bash
./scripts/view-logs.sh
# Select "Application Logs"
```

2. Common causes:
   - Application error
   - Missing environment variables
   - Port conflicts
   - Resource limits

**Solutions:**

1. Add debug environment variables:
```bash
export CONTAINER_ENV_VARS="DEBUG=true,LOG_LEVEL=debug"
```

2. Increase resources:
```bash
export CONTAINER_MEMORY_GB="8"
export CONTAINER_OCPUS="2"
```

3. Test container locally first:
```bash
docker run -p 80:80 -e DEBUG=true nginx:latest
```

### Cannot Access Container

**Problem:** Container is running but not accessible

**Check:**

1. Verify container has IP:
```bash
cd terraform
terraform output container_private_ip
terraform output container_public_ip
```

2. Test connectivity:
```bash
PUBLIC_IP=$(cd terraform && terraform output -raw container_public_ip)
curl -v http://$PUBLIC_IP:80
```

3. Check security lists:
```bash
SUBNET_ID=$(cd terraform && terraform output -raw subnet_ocid)

# Get security list
oci network subnet get --subnet-id "$SUBNET_ID" \
  --query 'data."security-list-ids"'

# View ingress rules
oci network security-list get --security-list-id <sec-list-ocid> \
  --query 'data."ingress-security-rules"'
```

**Solutions:**

Add ingress rule for container port:
```bash
# Get security list ID
SEC_LIST_ID="<your-security-list-ocid>"

# Add rule allowing port 80
oci network security-list update \
  --security-list-id "$SEC_LIST_ID" \
  --ingress-security-rules '[{
    "source": "0.0.0.0/0",
    "protocol": "6",
    "isStateless": false,
    "tcpOptions": {
      "destinationPortRange": {
        "min": 80,
        "max": 80
      }
    }
  }]'
```

## Logging Issues

### No Logs Appearing

**Problem:** Logs not showing in OCI Console or CLI

**Debug:**

1. Verify log group exists:
```bash
LOG_GROUP_ID=$(cd terraform && terraform output -raw log_group_id)
oci logging log-group get --log-group-id "$LOG_GROUP_ID"
```

2. Check log configuration:
```bash
oci logging log list --log-group-id "$LOG_GROUP_ID"
```

3. Verify IAM policies:
```bash
# Check dynamic group exists
oci iam dynamic-group list --compartment-id <tenancy-ocid> --all \
  | jq '.data[] | select(.name | contains("container"))'

# Check policies
oci iam policy list --compartment-id <compartment-ocid> --all \
  | jq '.data[] | select(.name | contains("logging"))'
```

**Solutions:**

1. Recreate log resources:
```bash
cd terraform
terraform destroy -target=module.logging
terraform apply
```

2. Manually create IAM policy:
```bash
cat > logging-policy.json << EOF
{
  "statements": [
    "Allow dynamic-group <dynamic-group-name> to use log-content in compartment id <compartment-ocid>",
    "Allow dynamic-group <dynamic-group-name> to use log-groups in compartment id <compartment-ocid>"
  ]
}
EOF

oci iam policy create \
  --compartment-id <compartment-ocid> \
  --name container-logging-policy \
  --description "Container Instance Logging Policy" \
  --statements file://logging-policy.json
```

### Log Retention Not Working

**Problem:** Logs deleted before retention period

**Solution:**

Update log retention:
```bash
LOG_ID="<log-ocid>"

oci logging log update \
  --log-group-id "$LOG_GROUP_ID" \
  --log-id "$LOG_ID" \
  --retention-duration 60
```

## Management Agent Issues

### Agent Installation Fails

**Problem:** Management agent won't install

**Debug:**

1. Check OS compatibility:
```bash
cat /etc/os-release
# Supported: Oracle Linux 7/8, RHEL 7/8, Ubuntu 18.04/20.04, Debian 10/11
```

2. Verify install key:
```bash
cd output
cat agent-config.json | jq '.install_key'
```

3. Check agent logs:
```bash
sudo tail -f /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log
```

**Solutions:**

1. Manual installation:
```bash
# Download installer
wget https://objectstorage.us-ashburn-1.oraclecloud.com/n/idtskf8cjzhp/b/installer/o/Linux/latest/oracle.mgmt_agent.rpm

# Install
sudo rpm -ivh oracle.mgmt_agent.rpm

# Configure
cat > /tmp/input.rsp << EOF
ManagementAgentInstallKey=<install-key>
AgentDisplayName=$(hostname)-agent
Service.plugin.prometheus.download=true
EOF

sudo /opt/oracle/mgmt_agent/agent_inst/bin/setup.sh opts=/tmp/input.rsp
```

2. Check firewall:
```bash
# Agent needs outbound HTTPS (443)
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Agent Not Collecting Metrics

**Problem:** Agent installed but no metrics in OCI

**Debug:**

1. Check agent status:
```bash
sudo systemctl status mgmt_agent
sudo journalctl -u mgmt_agent -n 100
```

2. Verify Prometheus plugin:
```bash
sudo /opt/oracle/mgmt_agent/agent_inst/bin/agentcore status
# Should show prometheus_emitter plugin as RUNNING
```

3. Test metrics endpoint:
```bash
curl http://localhost:9090/metrics
```

**Solutions:**

1. Restart agent:
```bash
sudo systemctl restart mgmt_agent
```

2. Enable Prometheus plugin:
```bash
sudo /opt/oracle/mgmt_agent/agent_inst/bin/agentcore enable-plugin prometheus_emitter
```

3. Check configuration:
```bash
sudo cat /opt/oracle/mgmt_agent/agent_inst/config/prometheus.yml
```

4. Verify network connectivity to OCI:
```bash
ping ingestion.telemetry.us-ashburn-1.oraclecloud.com
```

## Networking Issues

### Subnet Full

**Problem:** `Error: No available IP addresses in subnet`

**Solution:**

1. Use different subnet or create new subnet:
```bash
oci network subnet create \
  --compartment-id <compartment-ocid> \
  --vcn-id <vcn-ocid> \
  --cidr-block "10.0.2.0/24" \
  --display-name "container-subnet"
```

2. Or expand existing subnet (if possible)

### VCN DNS Issues

**Problem:** Container can't resolve DNS

**Solutions:**

1. Verify VCN DNS settings:
```bash
oci network vcn get --vcn-id <vcn-ocid> | jq '.data."dns-label"'
```

2. Add custom DNS to container:
```bash
export CONTAINER_ENV_VARS="DNS_SERVERS=8.8.8.8,8.8.4.4"
```

## Performance Issues

### High CPU Usage

**Solutions:**

1. Increase OCPUs:
```bash
# Stop current instance
terraform destroy -target=module.container_instance

# Update configuration
export CONTAINER_OCPUS="2"

# Redeploy
terraform apply
```

2. Check for runaway processes in container:
```bash
# Access container logs
./scripts/view-logs.sh

# Or use container exec (if enabled)
oci container-instances container exec \
  --container-id <container-ocid> \
  --command "top"
```

### High Memory Usage

**Solutions:**

1. Increase memory:
```bash
export CONTAINER_MEMORY_GB="8"
terraform apply
```

2. Add memory limits to application:
```bash
export CONTAINER_ENV_VARS="JAVA_OPTS=-Xmx2g"
```

### Slow Container Startup

**Causes:**
- Large container image
- Slow image registry
- Insufficient resources

**Solutions:**

1. Use lighter base image:
```bash
# Instead of full OS image
FROM nginx:alpine
```

2. Increase resources temporarily:
```bash
export CONTAINER_OCPUS="2"
export CONTAINER_MEMORY_GB="8"
```

3. Pre-pull image to OCIR (closer to OCI region)

## Getting Additional Help

### Enable Debug Logging

```bash
# In config/oci-monitoring.env
export VERBOSE="true"
export TF_LOG="DEBUG"

# Run deployment
./scripts/deploy.sh 2>&1 | tee debug.log
```

### Collect Diagnostic Information

```bash
# System info
uname -a
cat /etc/os-release

# Tool versions
oci --version
terraform version
jq --version

# OCI resources
cd terraform
terraform show
terraform output -json > outputs.json

# Logs
./scripts/view-logs.sh

# Container details
CONTAINER_ID=$(terraform output -raw container_instance_id)
oci container-instances container-instance get --container-instance-id "$CONTAINER_ID" > container-details.json
```

### Contact Support

When contacting support, provide:
1. Error messages and stack traces
2. Deployment logs from `logs/` directory
3. Terraform outputs
4. OCI resource OCIDs
5. Steps to reproduce the issue
6. Diagnostic information collected above
