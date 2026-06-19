#!/bin/bash

# SYNOPSIS: Installs Prometheus node_exporter on Linux and sets it up as a systemd service.
# USAGE: sudo ./install-node-exporter.sh

set -e

VERSION="1.11.1"
PORT="9100"
USER="node_exporter"

# Check for root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit
fi

echo "Installing Prometheus node_exporter v$VERSION..."

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

URL="https://github.com/prometheus/node_exporter/releases/download/v$VERSION/node_exporter-$VERSION.linux-$BIN_ARCH.tar.gz"
echo "Downloading $URL..."
curl -L "$URL" -o node_exporter.tar.gz

# Extract
tar xvf node_exporter.tar.gz
cp "node_exporter-$VERSION.linux-$BIN_ARCH/node_exporter" /usr/local/bin/
chown "$USER":"$USER" /usr/local/bin/node_exporter

# Cleanup
rm -rf node_exporter.tar.gz "node_exporter-$VERSION.linux-$BIN_ARCH"

# Create Systemd Service
echo "Creating systemd service..."
cat <<EOF > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=$USER
Group=$USER
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:$PORT

[Install]
WantedBy=multi-user.target
EOF

# Reload and Start
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Open the host firewall for the exporter port. OCI Linux images ship with a
# host firewall enabled (firewalld on Oracle Linux/RHEL, default iptables REJECT
# rules on Ubuntu), so without this the exporter is unreachable from Prometheus
# even when the OCI security list allows the port.
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

echo "node_exporter installed and started on port $PORT."
echo "Verify at: http://$(hostname -I | awk '{print $1}'):$PORT/metrics"
