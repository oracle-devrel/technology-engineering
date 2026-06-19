# Container Instance Monitoring Guide

## Monitoring Options for OCI Container Instances

OCI Container Instances support multiple monitoring approaches:

1. **Native Metrics** (Automatic) - Basic CPU, Memory, Network metrics
2. **Prometheus + Exporters** (Enhanced) - Comprehensive Docker monitoring with cAdvisor + Node Exporter
3. ~~Management Agent Sidecar~~ (Deprecated) - Does NOT work in containers

**Recommended**: Use Native Metrics for simple deployments, or Prometheus + Exporters for production monitoring.

---

## Option 1: Native Metrics (Automatic, No Configuration)

Container Instances in OCI **automatically send metrics to OCI Monitoring**. You do NOT need to install Management Agent inside containers.

## Why Agent Sidecar Doesn't Work

Management Agent cannot run in Container Instance containers because:

1. ❌ Containers don't have systemd (agent requires it)
2. ❌ Container Instances are not full VMs
3. ❌ Agent needs host-level access
4. ❌ RPM installation fails in containers

## What Works: Native Container Instance Metrics

### Automatically Available Metrics

OCI Container Instances send these metrics to OCI Monitoring **automatically**:

| Metric Name | Description | Unit |
|-------------|-------------|------|
| `CpuUtilization` | CPU usage percentage | Percent |
| `MemoryUtilization` | Memory usage percentage | Percent |
| `NetworkBytesIn` | Network ingress | Bytes |
| `NetworkBytesOut` | Network egress | Bytes |

### Accessing Metrics

**OCI Console:**
1. Navigate to: **Observability & Management** → **Monitoring** → **Metrics Explorer**
2. Compartment: Select your compartment
3. Metric Namespace: `oci_computecontainerinstance`
4. Select metrics to view

**OCI CLI:**
```bash
# List available metrics
oci monitoring metric list \
  --compartment-id <compartment-ocid> \
  --namespace oci_computecontainerinstance

# Query specific metric
oci monitoring metric-data summarize-metrics-data \
  --namespace oci_computecontainerinstance \
  --query-text "CpuUtilization[1m].mean()" \
  --compartment-id <compartment-ocid>
```

---

## Architecture Options

### Single Container Instance (Your Current Case)

```
Container Instance
├── Application Container
│   └── Your app (nginx, etc.)
└── Native Metrics
    └── Auto-sent to OCI Monitoring
```

**Cost:** ~$10-13/month (1 OCPU)
**Metrics:** OCI Monitoring Console
**No agent needed!** ✅

---

### Multiple Container Instances (10+)

```
Monitoring VM
├── Management Agent
├── Prometheus
└── Grafana
    ↓ Scrapes from ↓
Container 1, Container 2, ... Container N
(Each exposes Prometheus metrics on :9090)
```

**Cost:** $15 VM + $10/container
**Metrics:** Grafana + OCI Monitoring
**Agent on VM, not containers** ✅

---

## Recommended Configuration

### For Single/Few Containers (< 10)

**Edit:** `config/oci-monitoring.env`

```bash
# Disable agent sidecar (not needed!)
export ENABLE_MANAGEMENT_AGENT="false"

# No monitoring VM needed
export DEPLOY_MONITORING_VM="false"

# Enable NSG security
export CREATE_NSG="true"
export ALLOWED_CIDR="<your-ip>/32"
```

### For Multiple Containers (10+) with Grafana

**Use the interactive setup:**

```bash
./scripts/interactive-setup.sh
# Choose: "Yes" for multiple instances
# This deploys Monitoring VM with Grafana
```

---

## Custom Application Metrics (Optional)

If your application exposes Prometheus metrics, you can still collect them:

### Without Agent (Simple HTTP endpoint)

```bash
# Your app exposes metrics at :9090/metrics
curl http://<container-ip>:9090/metrics
```

### With Monitoring VM (Grafana visualization)

The Monitoring VM's Prometheus can scrape your container metrics:

```yaml
# /etc/prometheus/prometheus.yml (on Monitoring VM)
scrape_configs:
  - job_name: 'my-containers'
    static_configs:
      - targets:
        - '10.0.0.100:9090'  # Container IP
        - '10.0.0.47:9090'
        - '10.0.0.48:9090'
```

---

## Monitoring Best Practices

### 1. Use Native Metrics (Always)
- Free, automatic, no configuration
- View in OCI Console
- Set up OCI Alarms for thresholds

### 2. Add Prometheus Metrics (Optional)
- Only if your app exports them
- Use Monitoring VM to collect (don't use sidecar)
- Visualize in Grafana

### 3. Never Use Agent Sidecar
- ❌ Doesn't work in containers
- ❌ Wastes 30% resources
- ❌ Won't register with OCI
- ✅ Use VM instead if you need Management Agent

---

## Viewing Your Current Metrics

### OCI Console

1. Navigate to: https://cloud.oracle.com/monitoring/metrics
2. Select:
   - **Compartment**: Your compartment
   - **Namespace**: `oci_computecontainerinstance`
   - **Resource**: `monitoring-demo`
3. Click **Update Chart**

### Create Alarms

```bash
# Example: CPU alarm
oci monitoring alarm create \
  --compartment-id <compartment-ocid> \
  --display-name "Container High CPU" \
  --metric-compartment-id <compartment-ocid> \
  --namespace oci_computecontainerinstance \
  --query "CpuUtilization[1m].mean() > 80" \
  --severity "CRITICAL" \
  --destinations '["<topic-ocid>"]'
```

---

## Migration Guide

### Current State
- ✅ Container Instance: ACTIVE
- ❌ Agent Sidecar: Not working (expected)
- ✅ Native Metrics: Working

### Recommended Actions

#### Option A: Keep It Simple (Recommended for 1 container)

```bash
# 1. Update config to remove agent
vi config/oci-monitoring.env

# Set:
export ENABLE_MANAGEMENT_AGENT="false"

# 2. Redeploy (removes non-functional sidecar)
./scripts/deploy.sh deploy

# 3. View metrics in OCI Console
# Navigate to Monitoring → Metrics Explorer
```

#### Option B: Add Grafana (If you want dashboards)

```bash
# 1. Run interactive setup
./scripts/interactive-setup.sh

# 2. Choose:
# - "No" for multiple instances
# - "Yes" for Grafana

# 3. Deploy
./scripts/deploy.sh deploy

# 4. Access Grafana
# http://<vm-ip>:3000
```

---

## FAQ

**Q: Why can't I see the agent in my tenancy?**
A: Because Container Instances don't support Management Agent. This is expected and correct.

**Q: How do I monitor my containers then?**
A: Use native Container Instance metrics in OCI Monitoring (automatic, free).

**Q: Do I need Prometheus/Grafana?**
A: Only if you want:
- Custom dashboards
- Historical data beyond 90 days
- Multiple containers (10+)
- Custom application metrics

**Q: Where should Management Agent run?**
A: On a Compute Instance (VM), never in a Container Instance container.

**Q: Is the sidecar approach wrong?**
A: Yes, for Management Agent. Use a Monitoring VM instead.

---

## Summary

| What | Where It Runs | Purpose |
|------|---------------|---------|
| **Native Metrics** | Container Instance | Auto-collected, always available |
| **Management Agent** | Monitoring VM | Collects from multiple sources |
| **Prometheus** | Monitoring VM | Scrapes metrics, stores history |
| **Grafana** | Monitoring VM | Dashboards and visualization |

**For your single container:** Just use native metrics. No agent needed!

---

## Option 2: Prometheus-Based Monitoring (Enhanced)

For production deployments requiring comprehensive monitoring, we provide a **Prometheus-based monitoring stack** with:

### Components

1. **cAdvisor** (Container Metrics Exporter)
   - Runs as sidecar in each container instance
   - Collects container-level metrics (CPU, memory, network, disk per container)
   - Exposes metrics on port 8080

2. **Node Exporter** (Host Metrics Exporter)
   - Runs as sidecar in each container instance
   - Collects host-level metrics (system resources, filesystem, network)
   - Exposes metrics on port 9100

3. **Prometheus Server** (Metrics Collection & Storage)
   - Runs on centralized Monitoring VM
   - Scrapes metrics from all container instances (every 15 seconds)
   - Stores time-series data (15 days retention)

4. **Grafana** (Visualization & Dashboards)
   - Runs on centralized Monitoring VM
   - Pre-configured dashboards for Docker/container monitoring
   - Rich visualizations and alerting

5. **OCI Management Agent** (OCI Integration)
   - Runs on centralized Monitoring VM
   - Reads metrics from Prometheus
   - Sends to OCI Monitoring service

### Architecture

```
Monitoring VM (1 OCPU, 8GB)
├── Management Agent ────────► OCI Monitoring
├── Prometheus (scrapes)
└── Grafana (visualizes)
    ↓ Scrapes metrics from ↓
┌────────────────┬────────────────┬──────────┐
│ Container 1    │ Container 2    │  ...     │
│ ├─ App         │ ├─ App         │          │
│ ├─ cAdvisor    │ ├─ cAdvisor    │          │
│ └─ Node Exp.   │ └─ Node Exp.   │          │
└────────────────┴────────────────┴──────────┘
```

### Benefits

✅ **Comprehensive Metrics**: Container + Host level metrics
✅ **Industry Standard**: Prometheus + Grafana stack
✅ **Production Ready**: Pre-configured dashboards and alerts
✅ **Scalable**: Single VM monitors unlimited containers
✅ **Cost Effective**: $15/month fixed overhead (VM cost)
✅ **OCI Integration**: Metrics sent to OCI Monitoring

### When to Use

Use Prometheus-based monitoring if you need:
- **Production monitoring** with comprehensive metrics
- **Custom dashboards** and visualizations
- **Historical data** beyond 90 days
- **Monitoring multiple containers** (10+ containers)
- **Per-container metrics** (not just instance-level)
- **Advanced alerting** and notification

### Cost

| Component | Cost |
|-----------|------|
| Container Instance (1 OCPU, 4GB) | $10/month |
| Monitoring VM (1 OCPU, 8GB) | $15/month |
| **Total for 1 container** | **$25/month** |
| **Total for 10 containers** | **$115/month** ($10×10 + $15) |

**Break-even**: More cost-effective than native-only approach when monitoring 10+ containers with Grafana needs.

### Getting Started

See the comprehensive guide: **[Prometheus Monitoring Guide](./PROMETHEUS_MONITORING_GUIDE.md)**

### Quick Deployment

```bash
cd /Users/abirzu/dev/oci-monitoring

# Enable Prometheus exporters
export ENABLE_PROMETHEUS_EXPORTERS="true"
export DEPLOY_MONITORING_VM="true"
export ENABLE_GRAFANA="true"

# Deploy
./scripts/deploy.sh deploy

# Access Grafana
# http://<monitoring-vm-ip>:3000
# Username: admin
# Password: (set in config)
```

### Dashboard Examples

**Pre-configured Dashboards**:
1. **Docker Container Monitoring**
   - Container CPU Usage (%)
   - Container Memory Usage (MB)
   - Container Network I/O (MB/s)
   - Node CPU/Memory Usage (%)
   - Running Containers Count

2. **Prometheus Stats**
   - Target Status (Up/Down)
   - Scrape Duration
   - Metrics Ingestion Rate

---

## Comparison: Native vs Prometheus

| Feature | Native Metrics | Prometheus + Exporters |
|---------|----------------|------------------------|
| **Setup** | Automatic | 10-minute deployment |
| **Container Metrics** | Basic (instance-level) | Comprehensive (per-container) |
| **Host Metrics** | No | Yes (CPU, disk, network) |
| **Visualization** | OCI Console | Grafana + OCI Console |
| **Historical Data** | 90 days | Unlimited (configurable) |
| **Custom Dashboards** | No | Yes |
| **Alerting** | OCI Alarms | Grafana + OCI Alarms |
| **Cost (1 container)** | $10/month | $25/month |
| **Cost (10 containers)** | $100/month | $115/month |
| **Best For** | Simple deployments | Production monitoring |

---

## Recommendation by Use Case

| Use Case | Recommended Solution |
|----------|---------------------|
| **Single container, basic monitoring** | Native Metrics |
| **1-5 containers, basic monitoring** | Native Metrics |
| **Production workload, single container** | Prometheus + Exporters |
| **10+ containers** | Prometheus + Exporters |
| **Need custom dashboards** | Prometheus + Exporters |
| **Need per-container metrics** | Prometheus + Exporters |
| **Need historical data > 90 days** | Prometheus + Exporters |

---

## Additional Resources

- **[Prometheus Monitoring Guide](./PROMETHEUS_MONITORING_GUIDE.md)** - Complete setup and usage guide
- **[Architecture Guide](./ARCHITECTURE_GUIDE.md)** - Architecture patterns comparison
- **[Enhancements Summary](../ENHANCEMENTS_SUMMARY.md)** - Recent enhancements and features
