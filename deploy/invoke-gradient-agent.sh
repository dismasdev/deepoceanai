#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
AGENT_URL="https://agents.do-ai.run/v1/b69807eb-816f-453a-883a-f8ecb234afb6/production/run"
PROMPT="${1:-Hello from Brainstorm AI}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE"
  exit 1
fi

TOK="$(python - <<'PY'
from pathlib import Path
for line in Path('.env').read_text(encoding='utf-8', errors='replace').splitlines():
    if line.startswith('DIGITALOCEAN_API_TOKEN='):
        print(line.split('=',1)[1].strip())
        break
PY
)"

if [[ -z "$TOK" ]]; then
  echo "ERROR: DIGITALOCEAN_API_TOKEN is empty in .env"
  exit 1
fi

curl -sS -X POST "$AGENT_URL" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"$PROMPT\"}"

echo
