#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_SPEC="$ROOT_DIR/deploy/do-backend-app.yaml"
FRONTEND_SPEC="$ROOT_DIR/deploy/do-frontend-app.yaml"

if [[ -z "${DIGITALOCEAN_API_TOKEN:-}" ]]; then
  echo "ERROR: DIGITALOCEAN_API_TOKEN is not set."
  echo "Run: export DIGITALOCEAN_API_TOKEN=\"<your-token>\""
  exit 1
fi

if ! command -v doctl >/dev/null 2>&1; then
  if [[ -x "$HOME/.local/bin/doctl" ]]; then
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "ERROR: doctl is not installed."
    exit 1
  fi
fi

echo "Authenticating doctl with DIGITALOCEAN_API_TOKEN..."
doctl auth init -t "$DIGITALOCEAN_API_TOKEN" >/dev/null

echo "Creating backend app from spec: $BACKEND_SPEC"
doctl apps create --spec "$BACKEND_SPEC"

echo "Creating frontend app from spec: $FRONTEND_SPEC"
doctl apps create --spec "$FRONTEND_SPEC"

echo "Done. List apps with: doctl apps list"
