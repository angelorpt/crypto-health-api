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

echo "==> [demo-scenario] Executando cenário de demonstração (2 pacientes com 80.0 kg + Tamper Check)..."
python3 scripts/inspect_db.py
