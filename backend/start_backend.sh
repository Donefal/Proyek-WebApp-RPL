#!/bin/bash
# Script untuk menjalankan backend FastAPI dengan benar

# Pindah ke root directory project
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Aktifkan virtual environment
source backend/venv/bin/activate

# Cek dan hentikan proses yang menggunakan port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Port 8000 sedang digunakan. Menghentikan proses..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Set PYTHONPATH dan jalankan uvicorn dari root directory
export PYTHONPATH="$SCRIPT_DIR"

echo "=========================================="
echo "Menjalankan backend FastAPI..."
echo "URL: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "=========================================="
python -m uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0

