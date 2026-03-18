#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${DIGITALOCEAN_API_TOKEN:-}" ]]; then
  echo "ERROR: DIGITALOCEAN_API_TOKEN is not set."
  echo "Run: export DIGITALOCEAN_API_TOKEN=\"<your-token>\""
  exit 1
fi

echo "Checking gradient CLI..."
if ! command -v gradient >/dev/null 2>&1; then
  if [[ -x "$ROOT_DIR/.venv/bin/gradient" ]]; then
    export PATH="$ROOT_DIR/.venv/bin:$PATH"
  else
    echo "ERROR: gradient CLI not found."
    exit 1
  fi
fi

echo "Gradient version:"
gradient --version

echo "If not configured yet, run this manually once:"
echo "  uv run gradient agent configure"
echo "Use entrypoint file: backend/adk_entrypoint.py"

echo "Deploying ADK agent..."
uv run gradient agent deploy

echo "Done. Check deployment output above for run URL."
