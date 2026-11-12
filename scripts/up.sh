#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> [up] Subindo serviços Docker Compose (PostgreSQL 16 + MedVault API)..."
docker compose up -d --build

echo "==> [up] Aguardando API responder no healthcheck..."
for i in {1..30}; do
    if curl -fsS "http://localhost:${APP_PORT:-8000}/api/v1/health" >/dev/null 2>&1; then
        echo "==> [up] Serviços online! Swagger UI disponível em: http://localhost:${APP_PORT:-8000}/docs"
        exit 0
    fi
    sleep 1
done

echo "==> [up] Aviso: A API ainda está inicializando. Verifique com './scripts/logs.sh'."
