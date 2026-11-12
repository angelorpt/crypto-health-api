#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
    bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR/src"

HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-8000}"

echo "==> [dev] Iniciando MedVault Crypto API em http://${HOST}:${PORT} (Docs: /docs)..."
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
