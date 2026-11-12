#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
    bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> [lint] Verificando qualidade e estilo do código com Ruff..."
ruff check src tests scripts
ruff format --check src tests scripts
echo "==> [lint] Tudo limpo!"
