#!/usr/bin/env bash
set -euo pipefail

curl -fsS -X POST http://localhost:5001/start
echo
curl -fsS -X POST http://localhost:5000/start
echo

echo "Pipeline started. Check progress with scripts/status_services.sh"