#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> [setup] Configurando ambiente virtual Python em .venv..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> [setup] Atualizando pip e instalando dependências do pyproject.toml (.[dev])..."
pip install --upgrade pip
pip install -e ".[dev]"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "==> [setup] Criando arquivo .env a partir de .env.example..."
    cp .env.example .env
fi

echo "==> [setup] Ambiente pronto! Use './scripts/test.sh' ou './scripts/dev.sh'."
