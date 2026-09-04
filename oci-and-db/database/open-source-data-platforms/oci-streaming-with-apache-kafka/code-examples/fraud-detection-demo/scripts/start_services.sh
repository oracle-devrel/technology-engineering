#!/usr/bin/env bash
set -euo pipefail

sudo systemctl start fraud-consumer
sudo systemctl start fraud-producer

echo "Services started."
echo "Consumer status: http://localhost:5001/status"
echo "Producer status: http://localhost:5000/status"