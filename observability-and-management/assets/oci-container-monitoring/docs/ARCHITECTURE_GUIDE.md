# OCI Container Monitoring - Architecture Guide

## Overview

This guide helps you choose the best monitoring architecture for your OCI Container Instances deployment.

## Architecture Options

### Option 1: Sidecar Pattern (Single/Few Containers)

**Best for:**
- 1-10 container instances
- Simple deployments
- Quick start
- No additional infrastructure needed

**Architecture:**
```
┌─────────────────────────────────────────┐
│ Container Instance                       │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ App Container│  │ Agent Sidecar   │ │
│  │              │◄─┤ (Mgmt Agent)    │ │
│  │ Port: 80     │  │ Scrapes :9090   │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
         ↓
    OCI Monitoring
```

**Pros:**
- ✅ Simple setup
- ✅ No additional VMs
- ✅ Agent runs with container
- ✅ Auto-scales with container
- ✅ Direct OCI Monitoring integration

**Cons:**
- ❌ Agent overhead per container (30% resources)
- ❌ Not cost-effective for many instances
- ❌ Limited visualization (OCI Console only)
- ❌ No historical data beyond OCI retention

---

### Option 2: Centralized Monitoring VM (Multiple Containers)

**Best for:**
- 10+ container instances
- Production deployments
- Need for Grafana dashboards
- Custom alerting requirements
- Historical metrics storage

**Architecture:**
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Container 1  │  │ Container 2  │  │ Container N  │
│ (nginx)      │  │ (app)        │  │ (service)    │
│ :9090/metrics│  │ :9090/metrics│  │ :9090/metrics│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         ↓
       ┌─────────────────────────────────────┐
       │ Monitoring VM                        │
       │  ┌────────────────┐  ┌────────────┐│
       │  │ Prometheus     │  │ Grafana    ││
       │  │ (Scrapes all)  │◄─┤ (Visualize)││
       │  └───────┬────────┘  └────────────┘│
       │          │ Management Agent         │
       │          ↓                          │
       └──────────┼───────────────────────────┘
                  ↓
            OCI Monitoring
```

**Pros:**
- ✅ Cost-effective for scale (single VM monitors all)
- ✅ Includes Grafana for rich dashboards
- ✅ Prometheus for historical data
- ✅ Custom alerting with Grafana
- ✅ No per-container agent overhead
- ✅ Centralized management
- ✅ Can monitor 100+ containers

**Cons:**
- ❌ Additional VM cost (1 OCPU, 8GB)
- ❌ Slightly more complex setup
- ❌ Single point of failure (mitigated by OCI Monitoring backup)

---

## Cost Comparison

### Sidecar Pattern (5 containers)

| Resource | Quantity | Cost/Month* |
|----------|----------|-------------|
| Container Instance (with agent) | 5 × 1.3 OCPU | $65 |
| OCI Monitoring | Included | $0 |
| **Total** | | **$65** |

### Centralized VM (5 containers)

| Resource | Quantity | Cost/Month* |
|----------|----------|-------------|
| Container Instance (no agent) | 5 × 1 OCPU | $50 |
| Monitoring VM | 1 × 1 OCPU, 8GB | $15 |
| OCI Monitoring | Included | $0 |
| **Total** | | **$65** |

**Break-even point: 10+ containers** - VM approach becomes cheaper

\* Approximate costs in USD, actual costs vary by region

---

## Feature Comparison

| Feature | Sidecar | Centralized VM |
|---------|---------|----------------|
| **Setup Time** | 5 min | 10 min |
| **Grafana Dashboards** | ❌ | ✅ |
| **Prometheus Storage** | ❌ | ✅ |
| **Historical Data** | 90 days (OCI) | Unlimited (Prometheus) |
| **Custom Alerts** | OCI Alarms | Grafana + OCI |
| **Per-Container Overhead** | 30% | 0% |
| **Scalability** | 1-10 instances | 1-100+ instances |
| **Visualization** | OCI Console | Grafana + OCI Console |
| **Query Language** | MQL | PromQL + MQL |
| **Cost Efficiency** | Good < 10 | Good > 10 |

---

## Decision Tree

```
Do you need Grafana?
  ├─ YES → Use Centralized VM
  └─ NO  → How many containers?
           ├─ 1-10   → Use Sidecar Pattern
           └─ 10+    → Use Centralized VM
```

---

## Security

Both architectures include:
- ✅ Network Security Groups (NSG)
- ✅ Access restricted to your IP only
- ✅ Resource Principal authentication (no hardcoded credentials)
- ✅ Encrypted metric transmission
- ✅ IAM policies with least privilege

### Allowed Ports

**Sidecar Pattern:**
- Port 80/443 (HTTP/HTTPS) - Your IP only
- Port 9090 (Prometheus metrics) - Your IP only

**Centralized VM:**
- Port 22 (SSH) - Your IP only
- Port 80/443 (HTTP/HTTPS) - Your IP only
- Port 3000 (Grafana) - Your IP only
- Port 9090 (Prometheus) - Your IP only

---

## Deployment Steps

### Interactive Setup (Recommended)

```bash
cd /path/to/oci-monitoring
./scripts/interactive-setup.sh
```

This script will:
1. Detect your public IP
2. Ask about your deployment needs
3. Recommend the best architecture
4. Configure security (NSG with your IP)
5. Generate deployment configuration

### Manual Setup

#### Sidecar Pattern

```bash
# 1. Configure
cp config/oci-monitoring.conf config/oci-monitoring.env
vi config/oci-monitoring.env  # Edit settings

# Set these values:
export ENABLE_MANAGEMENT_AGENT="true"
export DEPLOY_MONITORING_VM="false"
export CREATE_NSG="true"
export ALLOWED_CIDR="<your-ip>/32"

# 2. Deploy
./scripts/deploy.sh deploy
```

#### Centralized VM

```bash
# 1. Configure
cp config/oci-monitoring.conf config/oci-monitoring.env
vi config/oci-monitoring.env

# Set these values:
export ENABLE_MANAGEMENT_AGENT="false"
export DEPLOY_MONITORING_VM="true"
export CREATE_NSG="true"
export ALLOWED_CIDR="<your-ip>/32"
export SSH_PUBLIC_KEY="$(cat ~/.ssh/id_rsa.pub)"
export ENABLE_GRAFANA="true"

# 2. Deploy
./scripts/deploy.sh deploy
```

---

## Monitoring Capabilities

### Metrics Collected

Both architectures collect:
- Container CPU usage
- Container memory usage
- Network I/O
- Disk I/O
- Container restart count
- Custom application metrics (if exposed)

### OCI Native Metrics

Available in OCI Monitoring Console:
- `CpuUtilization`
- `MemoryUtilization`
- `NetworkBytesIn`
- `NetworkBytesOut`

### Prometheus Metrics (VM architecture)

Additional metrics in Grafana:
- `container_cpu_usage_seconds_total`
- `container_memory_usage_bytes`
- `container_network_receive_bytes_total`
- `container_network_transmit_bytes_total`
- Plus any custom metrics your app exposes

---

## Grafana Dashboards (VM Architecture Only)

Pre-configured dashboards include:
1. **Container Overview** - All containers at a glance
2. **Resource Usage** - CPU, memory, network trends
3. **Application Metrics** - Custom metrics from your apps
4. **Alerts Dashboard** - Active alerts and history

---

## Troubleshooting

### Sidecar Pattern

```bash
# Check agent container logs
oci container-instances container retrieve-logs \
  --container-id <agent-container-ocid>

# Check if metrics are being collected
# OCI Console → Monitoring → Metrics Explorer
```

### Centralized VM

```bash
# SSH to monitoring VM
ssh opc@<vm-public-ip>

# Check services
sudo systemctl status mgmt_agent
sudo systemctl status prometheus
sudo systemctl status grafana-server

# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana
# Browser: http://<vm-public-ip>:3000
```

---

## Migration Between Architectures

### From Sidecar to Centralized VM

1. Deploy monitoring VM:
```bash
export DEPLOY_MONITORING_VM="true"
./scripts/deploy.sh deploy
```

2. Update container instances (remove agents):
```bash
export ENABLE_MANAGEMENT_AGENT="false"
./scripts/deploy.sh deploy
```

3. Verify metrics in Grafana

### From Centralized VM to Sidecar

1. Add agents to containers:
```bash
export ENABLE_MANAGEMENT_AGENT="true"
./scripts/deploy.sh deploy
```

2. Optionally remove VM:
```bash
export DEPLOY_MONITORING_VM="false"
terraform destroy -target=module.monitoring_vm
```

---

## Best Practices

1. **Start Simple** - Use sidecar for POC/development
2. **Scale Smart** - Switch to VM when scaling beyond 10 instances
3. **Secure Access** - Always use NSG with specific IP restrictions
4. **Monitor the Monitor** - Set up alerts for monitoring VM health
5. **Backup Configs** - Keep Grafana dashboard configs in git
6. **Regular Updates** - Update Prometheus and Grafana monthly
7. **Resource Tagging** - Tag all resources for cost tracking

---

## Support

- **Documentation**: `/docs` directory
- **Issues**: Check logs in `/logs` directory
- **OCI Support**: https://support.oracle.com

---

## Quick Reference

| Action | Sidecar | VM |
|--------|---------|-----|
| **View Metrics** | OCI Console | Grafana (port 3000) |
| **View Logs** | OCI CLI | SSH + journalctl |
| **Add Alert** | OCI Alarms | Grafana Alerts |
| **Scale** | Add container instances | Update Prometheus config |
| **Cost** | $13/OCPU/month | $15 VM + $10/OCPU container |
