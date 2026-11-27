#!/usr/bin/env bash
set -euo pipefail

echo "systemd:"
systemctl --no-pager status fraud-consumer fraud-producer || true

echo
echo "Application endpoints:"
curl -fsS http://localhost:5001/status || true
echo
curl -fsS http://localhost:5000/status || true
echo