#!/bin/sh
set -e

PLACEHOLDER="/__BASE_PATH_PLACEHOLDER__"
PREFIX="${BASE_PATH:-}"
PREFIX="${PREFIX%/}"
ESCAPED=$(printf '%s' "$PREFIX" | sed 's/[\/&|]/\\&/g')

# OCI Hosted Deployments mounts the container filesystem as read-only
# except /tmp. Copy the app to /tmp so we can sed the placeholder.
echo "[entrypoint] Staging app in /tmp/app (OCI fs is read-only outside /tmp)..."
mkdir -p /tmp/app
cp -r /app/. /tmp/app/
cd /tmp/app

echo "[entrypoint] Replacing ${PLACEHOLDER} with '${PREFIX}' in built assets..."
find ./server.js ./.next ./public -type f \
  \( -name "*.js" -o -name "*.html" -o -name "*.json" -o -name "*.rsc" -o -name "*.css" \) \
  -exec sed -i "s|${PLACEHOLDER}|${ESCAPED}|g" {} +

echo "[entrypoint] Done. Starting Next.js server from /tmp/app..."
exec node server.js
