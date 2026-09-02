#!/bin/sh
# ============================================================================
# CuOPT Frontend - Docker Entrypoint Script
# Starts both Nginx (frontend) and Node.js (API server)
# ============================================================================

set -e

echo "============================================"
echo "  CuOPT Frontend Container Starting..."
echo "============================================"

# Print environment info (without sensitive data)
echo "Environment:"
echo "  - CUOPT_ENDPOINT: ${CUOPT_ENDPOINT:-not set}"
echo "  - OCI_GENAI_ENDPOINT: ${OCI_GENAI_ENDPOINT:-not set}"
echo "  - NODE_ENV: ${NODE_ENV:-production}"

# Create log directories
mkdir -p /var/log/nginx

# Start the Express API server in background
echo "Starting Express API server on port 3001..."
cd /app
node server/index.js &
NODE_PID=$!

# Wait for Express server to be ready
echo "Waiting for API server to be ready..."
sleep 3

# Check if Node process is running
if ! kill -0 $NODE_PID 2>/dev/null; then
    echo "ERROR: Express server failed to start"
    exit 1
fi

echo "API server started successfully (PID: $NODE_PID)"

# Start Nginx in foreground
echo "Starting Nginx on port 80..."
echo "============================================"
echo "  CuOPT Frontend Ready!"
echo "  - Frontend: http://localhost:80"
echo "  - API: http://localhost:3001"
echo "============================================"

# Run nginx in foreground
exec nginx -g "daemon off;"
