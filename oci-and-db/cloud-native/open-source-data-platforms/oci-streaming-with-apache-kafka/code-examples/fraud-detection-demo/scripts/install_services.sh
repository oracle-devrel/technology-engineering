#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_DIR/venv"

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/install_services.sh"
  exit 1
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/producer/requirements.txt"
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/consumer/requirements.txt"

chown -R opc:opc "$REPO_DIR"

cat > /etc/systemd/system/fraud-consumer.service <<SERVICE
[Unit]
Description=Fraud Scoring Consumer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=$REPO_DIR/consumer
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/fraud-producer.service <<SERVICE
[Unit]
Description=Fraud Simulator Producer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=$REPO_DIR/producer
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable fraud-consumer fraud-producer

echo "Installed services from $REPO_DIR."
echo "Edit these configs before starting the pipeline:"
echo "  $REPO_DIR/consumer/app_config.yaml"
echo "  $REPO_DIR/consumer/kafka_client.properties"
echo "  $REPO_DIR/producer/app_config.yaml"
echo "  $REPO_DIR/producer/kafka_client.properties"
