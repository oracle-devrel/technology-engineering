#!/usr/bin/env bash
# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  uv venv .venv
fi

echo "Installing Python dependencies..."
uv pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "Creating local .env from .env.example..."
  cp .env.example .env
fi

if [ "${1:-}" != "--skip-node-install" ]; then
  if [ ! -d "node_modules" ]; then
    echo
    echo "Node dependencies are not installed."
    if ! command -v npm >/dev/null 2>&1; then
      echo "npm was not found. Install Node.js 20 or newer, then rerun ./setup.sh."
      exit 1
    fi
    echo "If your network requires VPN or proxy access for npm, enable it before continuing."
    echo "Otherwise npm package downloads can time out or fail."
    printf "Run npm install now? [y/N] "
    read -r answer
    case "$answer" in
      y|Y|yes|YES)
        npm install
        ;;
      *)
        echo "Skipped npm install. Run it later after enabling network access if needed."
        ;;
    esac
  else
    echo "Node dependencies already installed."
  fi
fi

echo
echo "Setup complete."
echo "Run the app with: ./start.sh"
