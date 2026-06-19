# Prometheus-Based Docker Container Monitoring Guide

## Overview

This guide explains the comprehensive Prometheus-based monitoring solution for OCI Container Instances, featuring:

- **cAdvisor**: Container-level metrics (CPU, memory, network, disk per container)
- **Node Exporter**: Host-level metrics (system resources, filesystem, network interfaces)
- **Prometheus**: Time-series metrics collection and storage
- **Grafana**: Rich visualization dashboards
- **OCI Management Agent**: Integration with OCI Monitoring service

---

## Architecture

### Enhanced Monitoring Stack

```
┌──────────────────────────────────────────────────────────┐
│                    Monitoring VM                          │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────────┐ │
│  │ OCI Mgmt     │  │ Prometheus │  │ Grafana         │ │
│  │ Agent        │◄─┤ Server     │◄─┤ Dashboards      │ │
│  │              │  │            │  │                 │ │
│  │ ├─Prometheus │  │ Port 9090  │  │ Port 3000       │ │
│  │ │ Plugin     │  └────────────┘  └─────────────────┘ │
│  │ └─Scrapes ───┼───────┘                              │
│  └──────────────┘         ↓                             │
└──────────────────────────│──────────────────────────────┘
                            │ Scrapes metrics from containers
                            ↓
    ┌───────────────────────┬───────────────────────┐
    │                       │                       │
┌───▼────────────┐  ┌──────▼────────┐  ┌──────────▼───┐
│ Container 1    │  │ Container 2   │  │ Container N  │
│ ┌────────────┐ │  │ ┌───────────┐ │  │ ┌──────────┐ │
│ │ App        │ │  │ │ App       │ │  │ │ App      │ │
│ │ (nginx)    │ │  │ │ (service) │ │  │ │ (app)    │ │
│ └────────────┘ │  │ └───────────┘ │  │ └──────────┘ │
│ ┌────────────┐ │  │ ┌───────────┐ │  │ ┌──────────┐ │
│ │ cAdvisor   │ │  │ │ cAdvisor  │ │  │ │ cAdvisor │ │
│ │ :8080      │ │  │ │ :8080     │ │  │ │ :8080    │ │
│ └────────────┘ │  │ └───────────┘ │  │ └──────────┘ │
│ ┌────────────┐ │  │ ┌───────────┐ │  │ ┌──────────┐ │
│ │ Node       │ │  │ │ Node      │ │  │ │ Node     │ │
│ │ Exporter   │ │  │ │ Exporter  │ │  │ │ Exporter │ │
│ │ :9100      │ │  │ │ :9100     │ │  │ │ :9100    │ │
│ └────────────┘ │  │ └───────────┘ │  │ └──────────┘ │
└────────────────┘  └───────────────┘  └──────────────┘
```

---

## Components

### 1. cAdvisor (Container Advisor)

**Purpose**: Collects container-specific metrics

**Port**: 8080

**Metrics Collected**:
- Container CPU usage (per container)
- Container memory usage (RSS, cache, swap)
- Container network I/O (bytes in/out, packets)
- Container disk I/O (read/write bytes and operations)
- Container filesystem usage
- Container process count
- Container restart count

**Sample Metrics**:
```promql
# CPU usage per container
container_cpu_usage_seconds_total{name="nginx"}

# Memory usage per container
container_memory_usage_bytes{name="nginx"}

# Network traffic per container
container_network_receive_bytes_total{name="nginx"}
container_network_transmit_bytes_total{name="nginx"}
```

**Image**: `gcr.io/cadvisor/cadvisor:latest`

**Resource Requirements**:
- Memory: 500MB
- CPU: 0.1 OCPU

---

### 2. Node Exporter

**Purpose**: Collects host/node-level system metrics

**Port**: 9100

**Metrics Collected**:
- Host CPU usage (per core, per mode)
- Host memory usage (total, available, buffers, cache)
- Host disk I/O statistics
- Host filesystem usage and inodes
- Host network interface statistics
- Host load average
- Host uptime
- Host temperature (if available)

**Sample Metrics**:
```promql
# CPU usage by mode
node_cpu_seconds_total{mode="idle"}
node_cpu_seconds_total{mode="system"}
node_cpu_seconds_total{mode="user"}

# Memory metrics
node_memory_MemTotal_bytes
node_memory_MemAvailable_bytes
node_memory_Buffers_bytes
node_memory_Cached_bytes

# Disk I/O
node_disk_read_bytes_total
node_disk_written_bytes_total

# Network interfaces
node_network_receive_bytes_total{device="eth0"}
node_network_transmit_bytes_total{device="eth0"}

# System uptime
node_boot_time_seconds
node_time_seconds
```

**Image**: `prom/node-exporter:latest`

**Resource Requirements**:
- Memory: 300MB
- CPU: 0.1 OCPU

---

### 3. Prometheus Server

**Purpose**: Scrapes, stores, and queries metrics from all exporters

**Port**: 9090

**Configuration**:
- Scrape interval: 15 seconds
- Scrape timeout: 10 seconds
- Retention: 15 days (default)

**Scrape Jobs**:

1. **prometheus** - Self-monitoring
   ```yaml
   - job_name: 'prometheus'
     static_configs:
       - targets: ['localhost:9090']
   ```

2. **cadvisor** - Container metrics from all container instances
   ```yaml
   - job_name: 'cadvisor'
     scrape_interval: 15s
     static_configs:
       - targets: ['10.0.0.100:8080', '10.0.0.47:8080', ...]
   ```

3. **node-exporter** - Host metrics from all container instances
   ```yaml
   - job_name: 'node-exporter'
     scrape_interval: 15s
     static_configs:
       - targets: ['10.0.0.100:9100', '10.0.0.47:9100', ...]
   ```

**Storage Location**: `/var/lib/prometheus`

**Configuration File**: `/etc/prometheus/prometheus.yml`

**Systemd Service**: `prometheus.service`

---

### 4. Grafana

**Purpose**: Visualize metrics with rich dashboards

**Port**: 3000

**Default Credentials**:
- Username: `admin`
- Password: (set in deployment config)

**Pre-configured Dashboards**:

1. **Docker Container Monitoring (cAdvisor + Node Exporter)**
   - Container CPU Usage (%)
   - Container Memory Usage (MB)
   - Container Network I/O (MB/s)
   - Node CPU Usage (%)
   - Node Memory Usage (%)
   - Running Containers Count
   - Node Uptime

2. **Prometheus Stats**
   - Total Targets
   - Targets Up/Down Status
   - Scrape Duration
   - Scrape Errors

**Data Source**: Prometheus (http://localhost:9090)

**Access URL**: `http://<monitoring-vm-ip>:3000`

---

### 5. OCI Management Agent

**Purpose**: Send Prometheus metrics to OCI Monitoring service

**Key Features**:
- Reads metrics from local Prometheus server
- Sends to OCI Monitoring namespace: `oci_prometheus_metrics`
- Metric namespace: `container_monitoring`
- Scrape interval: 60 seconds

**Configuration**:
- Install location: `/opt/oracle/mgmt_agent`
- Config file: `/opt/oracle/mgmt_agent/agent_inst/config/prometheus/prometheusPluginConfig.json`
- Log location: `/opt/oracle/mgmt_agent/agent_inst/log/`

**Systemd Service**: `mgmt_agent.service`

**Status Check**:
```bash
sudo systemctl status mgmt_agent
```

---

## Deployment

### Prerequisites

1. OCI tenancy configured
2. VCN and subnet created
3. Management Agent Install Key generated from OCI Console

### Configuration

Edit `config/oci-monitoring.env`:

```bash
# Enable Prometheus exporters (cAdvisor + Node Exporter)
export ENABLE_PROMETHEUS_EXPORTERS="true"

# Disable legacy agent sidecar (doesn't work in containers)
export ENABLE_MANAGEMENT_AGENT="false"

# Deploy Monitoring VM with Prometheus + Grafana
export DEPLOY_MONITORING_VM="true"
export ENABLE_GRAFANA="true"

# Network Security (NSG)
export CREATE_NSG="true"
export ALLOWED_CIDR="<your-ip>/32"

# SSH Access
export SSH_PUBLIC_KEY="$(cat ~/.ssh/id_rsa.pub)"

# Grafana Password
export GRAFANA_ADMIN_PASSWORD="YourSecurePassword123"
```

### Deploy

```bash
cd /Users/abirzu/dev/oci-monitoring

# Deploy infrastructure
./scripts/deploy.sh deploy

# Wait for deployment (5-10 minutes)
# The monitoring VM will auto-install:
# - OCI Management Agent
# - Prometheus
# - Grafana
# - Pre-configured dashboards
```

### Access Monitoring

After deployment, you'll receive:

```
Monitoring VM Public IP: 203.0.113.10
Grafana URL: http://203.0.113.10:3000
Prometheus URL: http://203.0.113.10:9090

Grafana Credentials:
  Username: admin
  Password: YourSecurePassword123
```

---

## Usage

### Accessing Grafana

1. Open browser: `http://<monitoring-vm-ip>:3000`
2. Login with admin credentials
3. Navigate to Dashboards → Browse
4. Select "Docker Container Monitoring"

### Accessing Prometheus

1. Open browser: `http://<monitoring-vm-ip>:9090`
2. Go to "Status" → "Targets" to see all scraped endpoints
3. Go to "Graph" to run PromQL queries

### Example PromQL Queries

**Container CPU Usage (%)**:
```promql
rate(container_cpu_usage_seconds_total{image!=""}[5m]) * 100
```

**Container Memory Usage (GB)**:
```promql
container_memory_usage_bytes{image!=""} / 1024 / 1024 / 1024
```

**Node CPU Usage (%)**:
```promql
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**Node Memory Usage (%)**:
```promql
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
```

**Container Network Traffic (MB/s)**:
```promql
rate(container_network_receive_bytes_total{image!=""}[5m]) / 1024 / 1024
rate(container_network_transmit_bytes_total{image!=""}[5m]) / 1024 / 1024
```

---

## Network Security

All ports are restricted by Network Security Groups (NSG):

### Container Instance NSG

**Ingress (from your IP only)**:
- Port 80 (HTTP)
- Port 443 (HTTPS)
- Port 8080 (cAdvisor)
- Port 9100 (Node Exporter)

**Ingress (from Monitoring VM only)**:
- Port 8080 (Prometheus scraping cAdvisor)
- Port 9100 (Prometheus scraping Node Exporter)

### Monitoring VM NSG

**Ingress (from your IP only)**:
- Port 22 (SSH)
- Port 3000 (Grafana)
- Port 9090 (Prometheus)

---

## Metrics Flow

```
Container Instances
   ├─ cAdvisor (:8080) ──┐
   └─ Node Exporter (:9100) ──┐
                              │
                              ↓ (scrapes every 15s)
                       Prometheus (:9090)
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ↓                   ↓
           Grafana (:3000)    OCI Management Agent
           (Visualization)    (Sends to OCI Monitoring)
                                      │
                                      ↓
                              OCI Monitoring Service
                              (oci_prometheus_metrics namespace)
```

---

## Resource Allocation

### Per Container Instance

With Prometheus exporters enabled:

| Component | Memory | CPU | Percentage |
|-----------|--------|-----|------------|
| Application | Dynamic | Dynamic | ~80% |
| cAdvisor | 500MB | 0.1 OCPU | ~8% |
| Node Exporter | 300MB | 0.1 OCPU | ~7% |
| **Total Overhead** | **800MB** | **0.2 OCPU** | **15%** |

**Example** (1 OCPU, 4GB RAM):
- Application gets: 0.8 OCPU, 3.2GB RAM
- Exporters use: 0.2 OCPU, 0.8GB RAM

### Monitoring VM

| Component | Memory | CPU |
|-----------|--------|-----|
| Management Agent | 1GB | 0.2 OCPU |
| Prometheus | 2GB | 0.3 OCPU |
| Grafana | 1GB | 0.2 OCPU |
| **Total** | **4GB** | **0.7 OCPU** |

**Recommended VM Shape**: 1 OCPU, 8GB RAM (leaves 4GB free)

---

## Cost Analysis

### With Prometheus Exporters (Enhanced Monitoring)

| Component | Monthly Cost (approx) |
|-----------|------------------------|
| 1 Container Instance (1 OCPU, 4GB) | $10 |
| Monitoring VM (1 OCPU, 8GB) | $15 |
| **Total for 1 container** | **$25** |
| **Total for 10 containers** | **$115** (10×$10 + $15) |
| **Total for 50 containers** | **$515** (50×$10 + $15) |

### Without Exporters (Native Metrics Only)

| Component | Monthly Cost (approx) |
|-----------|------------------------|
| 1 Container Instance (1 OCPU, 4GB) | $10 |
| **Total for 1 container** | **$10** |
| **Total for 10 containers** | **$100** |

**Additional Cost for Enhanced Monitoring**: $15/month (fixed, regardless of container count)

---

## Monitoring Best Practices

### 1. Scrape Interval Tuning

**Default**: 15 seconds

**Adjust based on needs**:
- High-precision monitoring: 10s (more storage, more CPU)
- Normal monitoring: 15s (recommended)
- Low-frequency monitoring: 30s or 60s (less storage)

### 2. Retention Policy

**Default**: 15 days

**Adjust in Prometheus config**:
```bash
# Edit systemd service
sudo vi /etc/systemd/system/prometheus.service

# Add retention flags:
ExecStart=/usr/local/bin/prometheus \
    --storage.tsdb.retention.time=30d \
    --storage.tsdb.retention.size=50GB
```

### 3. Alert Configuration

Create alert rules in Prometheus:

```yaml
# /etc/prometheus/alert.rules.yml
groups:
  - name: container_alerts
    rules:
      - alert: HighContainerCPU
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 5m
        annotations:
          summary: "Container {{ $labels.name }} high CPU"

      - alert: HighContainerMemory
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        annotations:
          summary: "Container {{ $labels.name }} high memory"
```

### 4. Dashboard Customization

**Add custom panels in Grafana**:
1. Click "Add Panel"
2. Select data source: Prometheus
3. Enter PromQL query
4. Configure visualization (Graph, Stat, Gauge, etc.)
5. Save dashboard

---

## Troubleshooting

### cAdvisor Not Scraping

```bash
# Check if cAdvisor is running
oci container-instances container list --container-instance-id <instance-id>

# Check cAdvisor metrics endpoint
curl http://<container-ip>:8080/metrics

# Check Prometheus targets
curl http://<monitoring-vm-ip>:9090/api/v1/targets
```

### Node Exporter Not Scraping

```bash
# Check Node Exporter metrics
curl http://<container-ip>:9100/metrics

# Verify NSG rules allow port 9100
```

### Prometheus Not Scraping

```bash
# SSH to Monitoring VM
ssh opc@<monitoring-vm-ip>

# Check Prometheus status
sudo systemctl status prometheus

# Check Prometheus logs
sudo journalctl -u prometheus -f

# Verify Prometheus config
cat /etc/prometheus/prometheus.yml
```

### Grafana Dashboard Not Showing Data

```bash
# Check Grafana data source
curl http://admin:<password>@localhost:3000/api/datasources

# Check if Prometheus is reachable from Grafana
curl http://localhost:9090/api/v1/query?query=up

# Restart Grafana
sudo systemctl restart grafana-server
```

### Management Agent Not Sending to OCI

```bash
# Check agent status
sudo systemctl status mgmt_agent

# Check agent logs
tail -f /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log

# Verify Prometheus plugin config
cat /opt/oracle/mgmt_agent/agent_inst/config/prometheus/prometheusPluginConfig.json

# Restart agent
sudo systemctl restart mgmt_agent
```

---

## Maintenance

### Update Prometheus

```bash
# SSH to Monitoring VM
ssh opc@<monitoring-vm-ip>

# Download new version
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.50.0/prometheus-2.50.0.linux-amd64.tar.gz
tar xzf prometheus-2.50.0.linux-amd64.tar.gz

# Stop Prometheus
sudo systemctl stop prometheus

# Replace binary
sudo cp prometheus-2.50.0.linux-amd64/prometheus /usr/local/bin/
sudo chown prometheus:prometheus /usr/local/bin/prometheus

# Start Prometheus
sudo systemctl start prometheus
```

### Update Grafana

```bash
# Update Grafana
sudo yum update grafana -y

# Restart Grafana
sudo systemctl restart grafana-server
```

### Backup Prometheus Data

```bash
# Create snapshot
sudo tar czf /tmp/prometheus-backup-$(date +%Y%m%d).tar.gz /var/lib/prometheus

# Download to local machine
scp opc@<monitoring-vm-ip>:/tmp/prometheus-backup-*.tar.gz .
```

---

## Summary

This Prometheus-based monitoring solution provides:

✅ **Comprehensive Metrics**: Container + Host level metrics
✅ **Industry Standard**: Prometheus + Grafana stack
✅ **OCI Integration**: Management Agent sends to OCI Monitoring
✅ **Scalable**: Monitors 1 to 100+ containers from single VM
✅ **Cost Effective**: Fixed $15/month overhead regardless of scale
✅ **Secure**: NSG-restricted access, no public exposure
✅ **Production Ready**: Auto-configured, tested, documented

For questions or issues, refer to the main documentation or check the troubleshooting section above.
