# Quick Start Guide

Get up and running with OCI Container Instance Monitoring in 10 minutes.

## Prerequisites

Before you begin, ensure you have:
- ✅ Active OCI account with administrator access
- ✅ VCN and subnet already created
- ✅ Terminal/command line access
- ✅ Internet connectivity

## Step-by-Step Setup

### Step 1: Clone or Download (1 minute)

If you haven't already, navigate to the project directory:
```bash
cd /Users/abirzu/dev/oci-monitoring
```

### Step 2: Install Prerequisites (3-5 minutes)

Run the automated installer:
```bash
./scripts/install-prerequisites.sh
```

This installs:
- OCI CLI
- Terraform
- jq (JSON processor)
- curl

**Or install manually:**

**macOS:**
```bash
brew install oci-cli terraform jq
```

**Linux:**
```bash
# OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Terraform (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform jq
```

### Step 3: Configure OCI CLI (2 minutes)

```bash
oci setup config
```

When prompted, provide:
1. **Config location**: Press Enter for default (`~/.oci/config`)
2. **User OCID**: Found in OCI Console → Profile → User Settings
3. **Tenancy OCID**: Found in OCI Console → Profile → Tenancy
4. **Region**: Your home region (e.g., `us-ashburn-1`)
5. **Generate RSA key pair**: `Y` (if you don't have one)
6. **Key location**: Press Enter for default

**Verify configuration:**
```bash
oci iam region list
```

### Step 4: Interactive Environment Setup (2 minutes)

Run the setup wizard:
```bash
./scripts/setup-environment.sh
```

The wizard will guide you through:
1. **Compartment selection** - Choose where to deploy resources
2. **Region selection** - Confirm or change region
3. **VCN and Subnet** - Select existing networking
4. **Container settings** - Image, resources, name
5. **Logging options** - Enable logs and retention
6. **Monitoring options** - Management Agent and dashboards

**Example responses:**
```
Enter Compartment OCID: ocid1.compartment.oc1..aaaaaaa...
Enter Region [us-ashburn-1]: <press enter>
Enter VCN OCID: ocid1.vcn.oc1.iad.aaaaaaa...
Enter Subnet OCID: ocid1.subnet.oc1.iad.aaaaaaa...
Container Instance Name [monitoring-demo]: nginx-demo
Container Image [nginx:latest]: <press enter>
OCPUs [1]: <press enter>
Memory GB [4]: <press enter>
Container Port [80]: <press enter>
Assign Public IP? (true/false) [true]: <press enter>
Enable Logging? (true/false) [true]: <press enter>
Log Retention Days [30]: <press enter>
Enable Management Agent? (true/false) [true]: <press enter>
Prometheus Metrics Port [9090]: <press enter>
Create Monitoring Dashboard? (true/false) [true]: <press enter>
```

### Step 5: Deploy! (3-5 minutes)

```bash
./scripts/deploy.sh
```

This will:
1. ✅ Validate prerequisites
2. ✅ Initialize Terraform
3. ✅ Create IAM policies
4. ✅ Deploy container instance
5. ✅ Configure logging
6. ✅ Set up Management Agent
7. ✅ Create monitoring dashboard
8. ✅ Verify deployment

**Expected output:**
```
╔═══════════════════════════════════════════════════════════════╗
║   OCI Container Instance Monitoring Automation                ║
║   Comprehensive deployment and monitoring solution            ║
╚═══════════════════════════════════════════════════════════════╝

[2024-01-15 10:30:00] INFO: Checking prerequisites...
[2024-01-15 10:30:01] SUCCESS: All prerequisites checked successfully
[2024-01-15 10:30:01] INFO: Loading configuration...
[2024-01-15 10:30:01] SUCCESS: Configuration loaded successfully
...
[2024-01-15 10:35:00] SUCCESS: Deployment completed successfully!
```

### Step 6: Verify Deployment (1 minute)

**Check deployment information:**
```bash
cat output/DEPLOYMENT_INFO.md
```

**Get container IP addresses:**
```bash
cd terraform
terraform output container_public_ip
terraform output container_private_ip
```

**Test container access:**
```bash
PUBLIC_IP=$(cd terraform && terraform output -raw container_public_ip)
curl http://$PUBLIC_IP
```

Expected: HTML response from nginx

**View logs:**
```bash
./scripts/view-logs.sh
```

## What's Next?

### Access OCI Console

The deployment provides direct links to resources:

1. **Container Instance:**
   ```
   https://cloud.oracle.com/compute/container-instances/<instance-id>?region=<region>
   ```

2. **Logs:**
   ```
   https://cloud.oracle.com/logging/log-groups/<log-group-id>?region=<region>
   ```

3. **Monitoring:**
   ```
   https://cloud.oracle.com/monitoring/alarms?region=<region>
   ```

### View Monitoring Dashboard

1. Go to OCI Console → Observability & Management → Dashboards
2. Find "Container Instance Monitoring Dashboard"
3. View real-time metrics:
   - CPU Utilization
   - Memory Usage
   - Network Traffic
   - Disk I/O

### Customize Your Deployment

Edit the configuration:
```bash
vim config/oci-monitoring.env
```

Common customizations:
```bash
# Use different container
export CONTAINER_IMAGE="httpd:latest"

# Increase resources
export CONTAINER_OCPUS="2"
export CONTAINER_MEMORY_GB="8"

# Change port
export CONTAINER_PORT="8080"

# Add environment variables
export CONTAINER_ENV_VARS="ENV=production,DEBUG=false"
```

Apply changes:
```bash
./scripts/deploy.sh
```

## Common Use Cases

### Deploy a Web Application

```bash
# Edit config
vim config/oci-monitoring.env

# Set your application image
export CONTAINER_IMAGE="myapp:latest"
export CONTAINER_PORT="3000"
export CONTAINER_ENV_VARS="NODE_ENV=production,PORT=3000"

# Deploy
./scripts/deploy.sh
```

### Deploy Multiple Containers

```bash
# First container
export CONTAINER_INSTANCE_NAME="web-app-1"
./scripts/deploy.sh

# Second container (new workspace)
export CONTAINER_INSTANCE_NAME="web-app-2"
export TF_WORKSPACE="app2"
./scripts/deploy.sh
```

### Use Private Container Registry (OCIR)

```bash
# Configure OCIR
export OCIR_USERNAME="<namespace>/oracleidentitycloudservice/user@example.com"
export OCIR_AUTH_TOKEN="<auth-token>"
export CONTAINER_IMAGE="<region>.ocir.io/<namespace>/myapp:v1.0"

# Deploy
./scripts/deploy.sh
```

## Cleanup

### Destroy All Resources

```bash
./scripts/deploy.sh destroy
```

Or:
```bash
cd terraform
terraform destroy
```

**Warning:** This will permanently delete:
- Container instances
- Log groups and logs
- IAM policies and dynamic groups
- Dashboards

## Troubleshooting

### Container Not Starting

**Check logs:**
```bash
./scripts/view-logs.sh
# Select "System Logs"
```

**Common issues:**
1. **Invalid image** - Verify image exists: `docker pull <image>`
2. **Insufficient resources** - Try smaller shape or different AD
3. **Network issues** - Check VCN/subnet configuration

### Cannot Access Container

**Verify public IP:**
```bash
terraform output container_public_ip
```

**Check security list:**
```bash
# Get subnet
SUBNET_ID=$(cd terraform && terraform output -raw subnet_ocid)

# View security lists
oci network subnet get --subnet-id "$SUBNET_ID"
```

**Add ingress rule:**
```bash
# Allow HTTP traffic (port 80)
oci network security-list update \
  --security-list-id <sec-list-id> \
  --ingress-security-rules '[{"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":80,"max":80}}}]'
```

### No Logs Appearing

**Wait 2-3 minutes** for logs to propagate

**Check log configuration:**
```bash
LOG_GROUP_ID=$(cd terraform && terraform output -raw log_group_id)
oci logging log-group get --log-group-id "$LOG_GROUP_ID"
```

**Recreate logs:**
```bash
cd terraform
terraform destroy -target=module.logging
terraform apply
```

## Getting Help

### Documentation
- **Main README**: `README.md`
- **Troubleshooting Guide**: `docs/TROUBLESHOOTING.md`
- **Configuration Reference**: `config/oci-monitoring.env`

### Debug Mode
```bash
export VERBOSE="true"
./scripts/deploy.sh
```

### View Logs
```bash
tail -f logs/deployment-*.log
```

### Common Commands

**View all resources:**
```bash
cd terraform
terraform show
```

**Get specific output:**
```bash
terraform output <output-name>
```

**Refresh state:**
```bash
terraform refresh
```

**Plan changes:**
```bash
./scripts/deploy.sh plan
```

## Next Steps

Once your basic deployment is working:

1. **Add Alarms** - Get notified of issues
2. **Custom Dashboards** - Create widgets for your metrics
3. **Multiple Environments** - Deploy dev/staging/prod
4. **CI/CD Integration** - Automate deployments
5. **Custom Containers** - Deploy your applications
6. **Advanced Networking** - Service mesh, load balancing
7. **Backup & Recovery** - Plan for disaster scenarios

## Summary

You've successfully:
- ✅ Installed prerequisites
- ✅ Configured OCI CLI
- ✅ Set up environment
- ✅ Deployed container instance
- ✅ Enabled logging and monitoring
- ✅ Created dashboards
- ✅ Verified deployment

**Total time:** ~10-15 minutes

**You now have:**
- Running container instance
- Comprehensive logging
- Real-time monitoring
- Custom dashboards
- Automated infrastructure

Enjoy your fully monitored OCI Container Instance! 🚀
