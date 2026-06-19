#!/bin/bash
# Application Container Entrypoint
# Starts nginx and metrics generation

echo "Starting application with metrics..."

# Start metrics generator in background
/usr/local/bin/generate-metrics.sh &

# Start nginx
exec "$@"
