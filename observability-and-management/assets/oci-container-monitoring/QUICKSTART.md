# Quick Start Guide - Sidecar Architecture

## 🎯 Overview

This guide will help you quickly deploy the OCI Container Instance monitoring solution with Management Agent and Prometheus sidecars.

## 📋 Prerequisites

Before you begin, ensure you have:

1. **OCI CLI** configured with appropriate credentials
2. **Docker** installed and running
3. **Terraform** 1.5.0 or higher
4. **OCI Compartment** with VCN and subnet already created
5. **Management Agent Install Key** from OCI Console

## 🚀 Quick Deploy (5 Steps)

### Step 1: Get Your OCI Tenancy Namespace

```bash
oci os ns get
# Note the output - you'll need this for OCIR
```

### Step 2: Configure the Environment

Edit `config/oci-monitoring.env` and update:

```bash
# Required - Your OCI Configuration
export OCI_REGION="eu-frankfurt-1"  # Your region
export OCI_TENANCY_OCID="ocid1.tenancy..."
export OCI_COMPARTMENT_OCID="ocid1.compartment..."
export VCN_OCID="ocid1.vcn..."
export SUBNET_OCID="ocid1.subnet..."

# Required - OCIR Configuration
export OCIR_REGION="fra"  # Your region key
export OCIR_NAMESPACE="your-tenancy-namespace"  # From step 1
export OCIR_USERNAME="your-namespace/your-username"
export OCIR_PASSWORD="your-auth-token"  # Create in OCI Console

# Required - Management Agent
export MGMT_AGENT_INSTALL_KEY_NAME="your-install-key-name"

# Sidecar Configuration (already enabled by default)
export ENABLE_SHARED_VOLUMES="true"
export ENABLE_MANAGEMENT_AGENT_SIDECAR="true"
export ENABLE_PROMETHEUS_SIDECAR="true"
```

### Step 3: Build and Push Docker Images

```bash
# Navigate to docker directory
cd docker

# Build and push all images to OCIR
./build-all.sh

# This will:
# 1. Build Management Agent sidecar
# 2. Build Prometheus sidecar
# 3. Build sample application with metrics
# 4. Push all images to OCIR
```

**Expected Output:**
```
Building Management Agent Sidecar...
✓ Management Agent Sidecar pushed successfully

Building Prometheus Sidecar...
✓ Prometheus Sidecar pushed successfully

Building Application with Metrics...
✓ Application with Metrics pushed successfully
```

### Step 4: Update Configuration with Image URLs

After building, update `config/oci-monitoring.env` with the actual image URLs:

```bash
export MGMT_AGENT_SIDECAR_IMAGE="fra.ocir.io/YOUR-NAMESPACE/oci-monitoring/mgmt-agent-sidecar:1.0.0"
export PROMETHEUS_SIDECAR_IMAGE="fra.ocir.io/YOUR-NAMESPACE/oci-monitoring/prometheus-sidecar:1.0.0"
export APP_WITH_METRICS_IMAGE="fra.ocir.io/YOUR-NAMESPACE/oci-monitoring/app-with-metrics:1.0.0"

# Use the app-with-metrics image as your container
export CONTAINER_IMAGE="${APP_WITH_METRICS_IMAGE}"
```

### Step 5: Deploy to OCI

```bash
# Navigate back to project root
cd ..

# Run the deployment
./scripts/deploy.sh deploy

# For auto-approval (no prompts):
export AUTO_APPROVE=true
./scripts/deploy.sh deploy
```

## ✅ Verify Deployment

### Check Container Instance Status

```bash
# Get the container instance OCID from terraform output
cd terraform
terraform output container_instance_id

# Check status
oci container-instances container-instance get \
  --container-instance-id <your-instance-ocid>
```

### Check All Containers are Running

```bash
# List all containers in the instance
oci container-instances container list \
  --container-instance-id <your-instance-ocid> \
  --compartment-id <your-compartment-ocid>
```

You should see:
- ✅ `monitoring-demo-app` - Your application
- ✅ `monitoring-demo-mgmt-agent-sidecar` - Management Agent
- ✅ `monitoring-demo-prometheus-sidecar` - Prometheus
- ✅ `monitoring-demo-cadvisor` - Container metrics (if enabled)
- ✅ `monitoring-demo-node-exporter` - Host metrics (if enabled)

### Access the Application

```bash
# Get the public IP
cd terraform
terraform output container_public_ip

# Access the application
curl http://<public-ip>

# Check metrics endpoint
curl http://<public-ip>/metrics
```

### Verify Metrics in OCI Monitoring

1. Go to **OCI Console** → **Observability & Management** → **Monitoring**
2. Navigate to **Metrics Explorer**
3. Select namespace: `container_monitoring`
4. You should see metrics flowing from your container instance

### Check Management Agent Registration

1. Go to **OCI Console** → **Observability & Management** → **Management Agents**
2. Look for an agent with your container instance name
3. Status should show **Active**

## 🔧 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           OCI Container Instance                        │
│                                                           │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │ Application  │  │ Prometheus  │  │ Management     │ │
│  │ (Port 80)    │  │ Sidecar     │  │ Agent Sidecar  │ │
│  │              │  │ (Port 9090) │  │                │ │
│  └──────┬───────┘  └──────┬──────┘  └────────┬───────┘ │
│         │                  │                   │         │
│         └──────────────────┼───────────────────┘         │
│                  Shared Volumes                          │
│              /metrics   &   /logs                        │
└─────────────────────────────────────────────────────────┘
                              │
                              ↓
                    OCI Monitoring Service
```

## 📊 Resource Allocation

Default resource allocation for 4GB, 1 OCPU instance:

| Container | Memory | CPU | Purpose |
|-----------|--------|-----|---------|
| Application | 1.5 GB | 0.5 OCPU | Your workload |
| Management Agent | 1.0 GB | 0.25 OCPU | OCI integration |
| Prometheus | 1.0 GB | 0.25 OCPU | Metrics aggregation |
| cAdvisor | 0.5 GB | 0.1 OCPU | Container metrics |

**Total**: ~4 GB, ~1.0 OCPU

## 🎛️ Configuration Options

### Enable/Disable Components

In `config/oci-monitoring.env`:

```bash
# Sidecar architecture (recommended)
export ENABLE_SHARED_VOLUMES="true"
export ENABLE_MANAGEMENT_AGENT_SIDECAR="true"
export ENABLE_PROMETHEUS_SIDECAR="true"

# Exporters (optional)
export ENABLE_PROMETHEUS_EXPORTERS="true"  # cAdvisor + Node Exporter
export ENABLE_NGINX_EXPORTER="false"
export ENABLE_REDIS_EXPORTER="false"
export ENABLE_POSTGRES_EXPORTER="false"
export ENABLE_MYSQL_EXPORTER="false"
export ENABLE_BLACKBOX_EXPORTER="false"
```

### Adjust Resource Allocation

```bash
# Total instance resources
export CONTAINER_OCPUS="2"      # Scale up for more containers
export CONTAINER_MEMORY_GB="8"  # Scale up for larger workloads

# Sidecar resources (adjust if needed)
export MGMT_AGENT_SIDECAR_MEMORY_GB="1.0"
export MGMT_AGENT_SIDECAR_OCPUS="0.25"
export PROMETHEUS_SIDECAR_MEMORY_GB="1.0"
export PROMETHEUS_SIDECAR_OCPUS="0.25"
```

### Change Scrape Interval

```bash
export PROMETHEUS_SCRAPE_INTERVAL="60"  # seconds
export PROMETHEUS_SCRAPE_TIMEOUT="10"   # seconds
```

## 🧪 Testing

### Run Local Docker Build Test

```bash
cd docker

# Test build without pushing
./build-all.sh --skip-push

# Test individual images
docker run -it --rm \
  -p 80:80 \
  -v /tmp/metrics:/metrics \
  -v /tmp/logs:/logs \
  app-with-metrics:1.0.0
```

### Validate Terraform Configuration

```bash
cd terraform

# Initialize
terraform init

# Validate syntax
terraform validate

# Preview changes
terraform plan
```

## 🐛 Troubleshooting

### Images Not Pulling from OCIR

**Problem**: Container instance fails to pull images

**Solution**:
1. Verify OCIR credentials in config file
2. Check image URLs are correct
3. Ensure images were pushed successfully:
   ```bash
   oci artifacts container image list \
     --compartment-id <compartment-ocid> \
     --repository-name oci-monitoring/mgmt-agent-sidecar
   ```

### Management Agent Not Registering

**Problem**: Agent sidecar runs but not visible in OCI Console

**Solution**:
1. Check agent logs:
   ```bash
   oci container-instances container retrieve-logs \
     --container-id <mgmt-agent-container-id>
   ```
2. Verify install key is valid in OCI Console
3. Check IAM policies allow agent registration
4. Ensure `MGMT_AGENT_INSTALL_KEY_NAME` is correct

### Containers Keep Restarting

**Problem**: Containers show RESTARTING status

**Solution**:
1. Check if resource limits are too low
2. Increase total instance resources
3. Check container logs for errors:
   ```bash
   oci container-instances container retrieve-logs \
     --container-id <container-id>
   ```

### Metrics Not Showing in OCI Monitoring

**Problem**: No metrics visible in OCI Console

**Solution**:
1. Verify Prometheus sidecar is running
2. Check Management Agent sidecar status
3. Test Prometheus endpoint:
   ```bash
   # From within container instance
   curl http://localhost:9090/metrics
   ```
4. Verify metrics namespace is correct: `container_monitoring`

## 📚 Additional Resources

- **Architecture Details**: See `ARCHITECTURE.md`
- **Build Instructions**: See `BUILD.md`
- **Implementation Status**: See `IMPLEMENTATION_STATUS.md`
- **Full Documentation**: See `README.md`

## 🎯 What's Next?

After successful deployment:

1. **Set up Grafana** (optional): Connect to Prometheus for visualization
2. **Configure Alarms**: Set up OCI Monitoring alarms for critical metrics
3. **Add Custom Metrics**: Modify your application to expose business metrics
4. **Scale Resources**: Adjust instance size based on workload requirements

## 💰 Cost Optimization

Typical monthly costs for 4GB/1 OCPU instance in Frankfurt region:

- **Container Instance**: ~$30/month
- **Management Agent**: Free (included with OCI)
- **OCI Monitoring**: Free tier (first 500M data points)
- **Data Transfer**: Minimal (mostly internal)

**Total**: ~$30-40/month

## 📞 Support

For issues or questions:
1. Check `IMPLEMENTATION_STATUS.md` for known issues
2. Review `ARCHITECTURE.md` for design decisions
3. Examine logs in `logs/` directory
4. Consult OCI documentation for service-specific issues

---

**Version**: 1.0.0 (Sidecar Architecture)
**Last Updated**: 2025-10-28
**Status**: Production Ready 🚀
