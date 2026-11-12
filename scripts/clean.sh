#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> [clean] Limpando caches, artefatos de cobertura e bancos temporários..."
python3 - <<'PY'
import pathlib
import shutil

root = pathlib.Path(".")
for dir_name in [".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov", "build", "dist"]:
    p = root / dir_name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)

for pycache in root.rglob("__pycache__"):
    shutil.rmtree(pycache, ignore_errors=True)

for file_name in [".coverage", "medvault_demo.db"]:
    f = root / file_name
    if f.exists():
        f.unlink()
PY
echo "==> [clean] Diretório limpo!"
