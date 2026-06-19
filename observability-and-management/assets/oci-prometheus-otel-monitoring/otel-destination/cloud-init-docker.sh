#!/bin/bash
# Cloud-init for the OTEL destination VM (Ubuntu): install Docker + compose plugin.
# The otel-destination/ files are copied to the VM afterward, then:
#   cd /opt/otel-destination && docker compose up -d
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
usermod -aG docker ubuntu || true
mkdir -p /opt/otel-destination
echo "Docker installed. Copy otel-destination/* to /opt/otel-destination and run: docker compose up -d"
