#!/bin/bash
set -e

echo "=========================================="
echo "CLAUDE MYTHOS STARTUP SCRIPT"
echo "=========================================="

echo "[1/4] Checking Python..."
python --version

echo "[2/4] Checking working directory..."
pwd
ls -la

echo "[3/4] Testing app import..."
python -c "from app.main import app; print('✅ App imported OK')" || {
    echo "❌ FAILED to import app"
    python -c "import sys; print(sys.path)"
    exit 1
}

echo "[4/4] Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
