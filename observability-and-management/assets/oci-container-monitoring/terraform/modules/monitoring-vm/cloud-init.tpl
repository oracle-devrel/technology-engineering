#!/bin/bash
#cloud-config

# OCI Monitoring VM Setup
# Installs: Management Agent, Prometheus, Grafana

set -e

#######################################
# Variables from Terraform
#######################################
MGMT_AGENT_KEY="${mgmt_agent_install_key}"
REGION="${region}"
COMPARTMENT_OCID="${compartment_ocid}"
GRAFANA_PASSWORD="${grafana_admin_password}"
PROMETHEUS_PORT="${prometheus_port}"
PROMETHEUS_TARGETS='${prometheus_targets}'

#######################################
# System Setup
#######################################
echo "===== Starting Monitoring VM Setup ====="
date

# Update system
yum update -y

# Install required packages
yum install -y wget curl unzip java-11-openjdk firewalld

# Enable and start firewalld
systemctl enable firewalld
systemctl start firewalld

#######################################
# Install Management Agent
#######################################
echo "===== Installing OCI Management Agent ====="

# Download Management Agent
cd /tmp
wget -q "https://objectstorage.$${REGION}.oraclecloud.com/n/idtskf8cjzhp/b/installer/o/Linux/latest/oracle.mgmt_agent.rpm"

# Install Management Agent
rpm -ivh oracle.mgmt_agent.rpm

# Create input response file
WALLET_PASSWORD=$(openssl rand -base64 32)
cat > /tmp/mgmt_agent_input.rsp <<EOF
ManagementAgentInstallKey=$${MGMT_AGENT_KEY}
AgentDisplayName=$(hostname)-mgmt-agent
CredentialWalletPassword=$${WALLET_PASSWORD}
Service.plugin.prometheus.download=true
PrometheusEmitterUrl=http://localhost:$${PROMETHEUS_PORT}
EOF

# Setup Management Agent
/opt/oracle/mgmt_agent/agent_inst/bin/setup.sh opts=/tmp/mgmt_agent_input.rsp

# Wait for agent to initialize
sleep 10

# Configure Prometheus plugin
echo "===== Configuring Management Agent Prometheus Plugin ====="

# Create Prometheus plugin configuration
mkdir -p /opt/oracle/mgmt_agent/agent_inst/config/prometheus
cat > /opt/oracle/mgmt_agent/agent_inst/config/prometheus/prometheusPluginConfig.json <<'PLUGEOF'
{
  "entities": [
    {
      "namespace": "oci_prometheus_metrics",
      "metricNamespace": "container_monitoring",
      "resourceGroup": "monitoring-demo",
      "prometheusConfig": {
        "sourceUrl": "http://localhost:${prometheus_port}",
        "scrapeInterval": "60s",
        "scrapeTimeout": "30s"
      }
    }
  ]
}
PLUGEOF

# Set correct ownership
chown oracle:oracle /opt/oracle/mgmt_agent/agent_inst/config/prometheus/prometheusPluginConfig.json

# Enable and start Management Agent
systemctl enable mgmt_agent
systemctl start mgmt_agent

# Wait for agent to fully start
sleep 20

# Cleanup
rm -f /tmp/mgmt_agent_input.rsp
rm -f /tmp/oracle.mgmt_agent.rpm

echo "Management Agent with Prometheus plugin installed successfully"

# Verify agent status
systemctl status mgmt_agent | head -20 || true
echo "Agent logs location: /opt/oracle/mgmt_agent/agent_inst/log/"

#######################################
# Install Prometheus
#######################################
echo "===== Installing Prometheus ====="

# Create prometheus user
useradd --no-create-home --shell /bin/false prometheus

# Download and install Prometheus
PROM_VERSION="2.47.0"
cd /tmp
wget "https://github.com/prometheus/prometheus/releases/download/v$${PROM_VERSION}/prometheus-$${PROM_VERSION}.linux-amd64.tar.gz"
tar xzf prometheus-$${PROM_VERSION}.linux-amd64.tar.gz

# Move binaries
cp prometheus-$${PROM_VERSION}.linux-amd64/prometheus /usr/local/bin/
cp prometheus-$${PROM_VERSION}.linux-amd64/promtool /usr/local/bin/
chown prometheus:prometheus /usr/local/bin/prometheus
chown prometheus:prometheus /usr/local/bin/promtool

# Create directories
mkdir -p /etc/prometheus
mkdir -p /var/lib/prometheus
chown prometheus:prometheus /etc/prometheus
chown prometheus:prometheus /var/lib/prometheus

# Copy console files
cp -r prometheus-$${PROM_VERSION}.linux-amd64/consoles /etc/prometheus
cp -r prometheus-$${PROM_VERSION}.linux-amd64/console_libraries /etc/prometheus
chown -R prometheus:prometheus /etc/prometheus/consoles
chown -R prometheus:prometheus /etc/prometheus/console_libraries

# Create Prometheus configuration with cAdvisor and Node Exporter scraping
cat > /etc/prometheus/prometheus.yml <<'PROMEOF'
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
  external_labels:
    monitor: 'oci-container-monitoring'
    region: '${region}'
    environment: 'production'

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'
          type: 'monitoring'

  # cAdvisor - Container metrics from all container instances
  # Collects: CPU, Memory, Network, Disk I/O metrics per container
  - job_name: 'cadvisor'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_cadvisor}
        labels:
          exporter: 'cadvisor'
          service: 'container-instances'
    metric_relabel_configs:
      # Keep only container metrics (not cgroup metrics)
      - source_labels: [container_label_com_docker_compose_service]
        regex: '.+'
        action: keep
      # Add helpful labels
      - source_labels: [name]
        target_label: container_name

  # Node Exporter - Host/Node metrics from all container instances
  # Collects: CPU, Memory, Disk, Filesystem, Network interface metrics
  - job_name: 'node-exporter'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_node_exporter}
        labels:
          exporter: 'node-exporter'
          service: 'container-instances'
    metric_relabel_configs:
      # Drop unnecessary filesystem metrics
      - source_labels: [__name__]
        regex: 'node_filesystem_(free|size|avail)_.*'
        action: keep

  # Nginx Exporter - Nginx web server metrics
  # Collects: Connections, requests, response codes
  - job_name: 'nginx-exporter'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_nginx_exporter}
        labels:
          exporter: 'nginx-exporter'
          service: 'container-instances'

  # Redis Exporter - Redis cache metrics
  # Collects: Memory usage, keyspace, clients, commands
  - job_name: 'redis-exporter'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_redis_exporter}
        labels:
          exporter: 'redis-exporter'
          service: 'container-instances'

  # PostgreSQL Exporter - PostgreSQL database metrics
  # Collects: Connections, transactions, locks, queries
  - job_name: 'postgres-exporter'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_postgres_exporter}
        labels:
          exporter: 'postgres-exporter'
          service: 'container-instances'

  # MySQL Exporter - MySQL database metrics
  # Collects: Connections, queries, InnoDB metrics
  - job_name: 'mysql-exporter'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_mysql_exporter}
        labels:
          exporter: 'mysql-exporter'
          service: 'container-instances'

  # Blackbox Exporter - Endpoint probing
  # Collects: HTTP/HTTPS availability, response time, SSL validity
  - job_name: 'blackbox-exporter'
    scrape_interval: 30s
    scrape_timeout: 10s
    static_configs:
      - targets: ${prometheus_targets_blackbox_exporter}
        labels:
          exporter: 'blackbox-exporter'
          service: 'container-instances'

  # Application-level Prometheus exporters (if any)
  # For applications that expose custom /metrics endpoints
  - job_name: 'application-metrics'
    scrape_interval: 30s
    static_configs:
      - targets: ${prometheus_targets_app}
        labels:
          exporter: 'application'
          service: 'custom-metrics'

# Alerting rules (optional - can be extended)
alerting:
  alertmanagers:
    - static_configs:
        - targets: []
          # Add Alertmanager targets here if needed
PROMEOF

chown prometheus:prometheus /etc/prometheus/prometheus.yml

# Create systemd service
cat > /etc/systemd/system/prometheus.service <<'SVCEOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
SVCEOF

# Enable and start Prometheus
systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus

# Allow Prometheus port in firewall
firewall-cmd --permanent --add-port=$${PROMETHEUS_PORT}/tcp
firewall-cmd --reload

echo "Prometheus installed successfully"

#######################################
# Install Grafana
#######################################
echo "===== Installing Grafana ====="

# Add Grafana repository
cat > /etc/yum.repos.d/grafana.repo <<'GRAFEOF'
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
GRAFEOF

# Install Grafana
yum install -y grafana

# Configure Grafana
cat > /etc/grafana/grafana.ini <<'GINIEOF'
[server]
protocol = http
http_port = 3000
domain = localhost

[security]
admin_user = admin
admin_password = ${grafana_admin_password}

[auth.anonymous]
enabled = false
GINIEOF

# Enable and start Grafana
systemctl enable grafana-server
systemctl start grafana-server

# Allow Grafana port in firewall
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --reload

echo "Grafana installed successfully"

#######################################
# Configure Grafana Data Source (Prometheus)
#######################################
echo "===== Configuring Grafana ====="

# Wait for Grafana to start
sleep 30

# Add Prometheus as data source
curl -X POST http://admin:$${GRAFANA_PASSWORD}@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }'

echo "Grafana data source configured"

#######################################
# Create Monitoring Dashboard
#######################################
echo "===== Creating Docker Monitoring Dashboard ====="

# Import comprehensive Docker/Container Monitoring dashboard
# Includes: cAdvisor metrics (container-level) and Node Exporter metrics (host-level)
curl -X POST http://admin:$${GRAFANA_PASSWORD}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Docker Container Monitoring (cAdvisor + Node Exporter)",
      "tags": ["docker", "cadvisor", "node-exporter", "containers", "oci"],
      "timezone": "browser",
      "schemaVersion": 27,
      "version": 1,
      "refresh": "30s",
      "panels": [
        {
          "id": 1,
          "title": "Container CPU Usage (%)",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
          "targets": [{"expr": "rate(container_cpu_usage_seconds_total{image!=\"\"}[5m]) * 100", "legendFormat": "{{name}}"}],
          "fieldConfig": {"defaults": {"unit": "percent"}}
        },
        {
          "id": 2,
          "title": "Container Memory Usage (MB)",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
          "targets": [{"expr": "container_memory_usage_bytes{image!=\"\"} / 1024 / 1024", "legendFormat": "{{name}}"}],
          "fieldConfig": {"defaults": {"unit": "decmbytes"}}
        },
        {
          "id": 3,
          "title": "Container Network I/O (MB/s)",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
          "targets": [
            {"expr": "rate(container_network_receive_bytes_total{image!=\"\"}[5m]) / 1024 / 1024", "legendFormat": "RX: {{name}}"},
            {"expr": "rate(container_network_transmit_bytes_total{image!=\"\"}[5m]) / 1024 / 1024", "legendFormat": "TX: {{name}}"}
          ],
          "fieldConfig": {"defaults": {"unit": "MBs"}}
        },
        {
          "id": 4,
          "title": "Node CPU Usage (%)",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
          "targets": [{"expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)", "legendFormat": "{{instance}}"}],
          "fieldConfig": {"defaults": {"unit": "percent", "max": 100, "min": 0}}
        },
        {
          "id": 5,
          "title": "Node Memory Usage (%)",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
          "targets": [{"expr": "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))", "legendFormat": "{{instance}}"}],
          "fieldConfig": {"defaults": {"unit": "percent", "max": 100, "min": 0}}
        },
        {
          "id": 6,
          "title": "Running Containers",
          "type": "stat",
          "gridPos": {"h": 4, "w": 6, "x": 12, "y": 16},
          "targets": [{"expr": "count(container_last_seen{image!=\"\"})", "legendFormat": "Containers"}],
          "options": {"textMode": "value_and_name", "colorMode": "background"}
        },
        {
          "id": 7,
          "title": "Node Uptime (Days)",
          "type": "stat",
          "gridPos": {"h": 4, "w": 6, "x": 18, "y": 16},
          "targets": [{"expr": "avg(node_time_seconds - node_boot_time_seconds) / 86400", "legendFormat": "Uptime"}],
          "fieldConfig": {"defaults": {"unit": "d", "decimals": 1}}
        }
      ]
    },
    "overwrite": true
  }'

echo "Docker monitoring dashboard created successfully"

# Import additional dashboard for Prometheus metrics
curl -X POST http://admin:$${GRAFANA_PASSWORD}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Prometheus Stats",
      "tags": ["prometheus", "monitoring"],
      "timezone": "browser",
      "schemaVersion": 27,
      "version": 1,
      "refresh": "30s",
      "panels": [
        {
          "id": 1,
          "title": "Prometheus Targets",
          "type": "stat",
          "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
          "targets": [{"expr": "count(up)", "legendFormat": "Total Targets"}]
        },
        {
          "id": 2,
          "title": "Targets Up/Down",
          "type": "stat",
          "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
          "targets": [
            {"expr": "count(up == 1)", "legendFormat": "Up"},
            {"expr": "count(up == 0)", "legendFormat": "Down"}
          ]
        },
        {
          "id": 3,
          "title": "Scrape Duration",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 24, "x": 0, "y": 6},
          "targets": [{"expr": "scrape_duration_seconds", "legendFormat": "{{job}} - {{instance}}"}]
        }
      ]
    },
    "overwrite": true
  }'

echo "Prometheus stats dashboard created successfully"

#######################################
# Final Setup
#######################################
echo "===== Finalizing Setup ====="

# Create info file
cat > /root/monitoring-vm-info.txt <<INFO
OCI Monitoring VM Setup Complete
=================================

Installed Services:
- OCI Management Agent: Running on port (internal)
- Prometheus: Running on port $${PROMETHEUS_PORT}
- Grafana: Running on port 3000

Access Information:
- Grafana URL: http://$(hostname -I | awk '{print $1}'):3000
- Grafana Username: admin
- Grafana Password: $${GRAFANA_PASSWORD}
- Prometheus URL: http://$(hostname -I | awk '{print $1}'):$${PROMETHEUS_PORT}

To check service status:
  sudo systemctl status mgmt_agent
  sudo systemctl status prometheus
  sudo systemctl status grafana-server

To view logs:
  sudo journalctl -u mgmt_agent -f
  sudo journalctl -u prometheus -f
  sudo journalctl -u grafana-server -f
INFO

cat /root/monitoring-vm-info.txt

echo "===== Monitoring VM Setup Complete ====="
date
