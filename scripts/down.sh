#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "${1:-}" == "--volumes" || "${1:-}" == "-v" ]]; then
    echo "==> [down] Derrubando containers e removendo volumes de dados..."
    docker compose down -v --remove-orphans
else
    echo "==> [down] Derrubando containers Docker Compose (mantendo volumes)..."
    docker compose down --remove-orphans
fi
