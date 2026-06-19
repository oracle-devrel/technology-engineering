#!/bin/bash

# SYNOPSIS: Installs Prometheus stackdriver_exporter on Linux for GCP monitoring.
# USAGE: sudo ./install-gcp-exporter.sh <project-id> <path-to-json-key> [metric-prefixes]

set -e

VERSION="0.19.0"
PORT="9255"
USER="gcp_exporter"

PROJECT_ID=$1
KEY_PATH=$2
PREFIXES=$3

if [ -z "$PROJECT_ID" ] || [ -z "$KEY_PATH" ]; then
    echo "Usage: sudo $0 <project-id> <path-to-json-key> [metric-prefixes]"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo "Error: Key file not found at $KEY_PATH"
    exit 1
fi

# Check for root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit
fi

echo "Installing Prometheus stackdriver_exporter v$VERSION..."

# Create user
if ! id "$USER" &>/dev/null; then
    useradd --no-create-home --shell /bin/false "$USER"
fi

# Download
ARCH=$(uname -m)
case $ARCH in
    x86_64) BIN_ARCH="amd64" ;;
    aarch64) BIN_ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

URL="https://github.com/prometheus-community/stackdriver_exporter/releases/download/v$VERSION/stackdriver_exporter-$VERSION.linux-$BIN_ARCH.tar.gz"
echo "Downloading $URL..."
curl -L "$URL" -o gcp_exporter.tar.gz

# Extract
tar xvf gcp_exporter.tar.gz
cp "stackdriver_exporter-$VERSION.linux-$BIN_ARCH/stackdriver_exporter" /usr/local/bin/
chown "$USER":"$USER" /usr/local/bin/stackdriver_exporter

# Cleanup
rm -rf gcp_exporter.tar.gz "stackdriver_exporter-$VERSION.linux-$BIN_ARCH"

# Create Systemd Service
echo "Creating systemd service..."

ARGS="--google.project-id=$PROJECT_ID"
if [ -n "$PREFIXES" ]; then
    ARGS="$ARGS --monitoring.metrics-type-prefixes=$PREFIXES"
fi

cat <<EOF > /etc/systemd/system/gcp_exporter.service
[Unit]
Description=GCP Stackdriver Exporter
After=network.target

[Service]
User=$USER
Group=$USER
Type=simple
Environment="GOOGLE_APPLICATION_CREDENTIALS=$KEY_PATH"
ExecStart=/usr/local/bin/stackdriver_exporter $ARGS --web.listen-address=:$PORT

[Install]
WantedBy=multi-user.target
EOF

# Reload and Start
systemctl daemon-reload
systemctl enable gcp_exporter
systemctl start gcp_exporter

# Open the host firewall for the exporter port (OCI Linux images enable a host
# firewall by default, which otherwise blocks Prometheus from scraping).
open_firewall_port() {
    local port="$1"
    if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld; then
        firewall-cmd --add-port="${port}/tcp" --permanent && firewall-cmd --reload
        echo "Opened ${port}/tcp in firewalld."
    elif command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
        ufw allow "${port}/tcp" && echo "Opened ${port}/tcp in ufw."
    elif command -v iptables >/dev/null 2>&1; then
        if ! iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
            iptables -I INPUT -p tcp --dport "$port" -j ACCEPT
            command -v netfilter-persistent >/dev/null 2>&1 && netfilter-persistent save 2>/dev/null || true
            echo "Opened ${port}/tcp in iptables."
        fi
    fi
}
open_firewall_port "$PORT"

echo "stackdriver_exporter installed and started on port $PORT."
echo "Verify at: http://$(hostname -I | awk '{print $1}'):$PORT/metrics"
