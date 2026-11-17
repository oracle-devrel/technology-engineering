#!/usr/bin/env bash
set -euo pipefail

curl -fsS -X POST http://localhost:5000/stop || true
curl -fsS -X POST http://localhost:5001/stop || true

sudo systemctl stop fraud-producer
sudo systemctl stop fraud-consumer

echo "Services stopped."