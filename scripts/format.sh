#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
    bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> [format] Corrigindo imports e formatando código com Ruff..."
ruff format src tests scripts
ruff check --fix src tests scripts
echo "==> [format] Formatação concluída!"
