#!/bin/bash
# Script untuk menjalankan backend FastAPI

# Cek dan hentikan proses yang menggunakan port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Port 8000 sedang digunakan. Menghentikan proses..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Aktifkan virtual environment
source venv/bin/activate

# Pindah ke direktori parent untuk import backend module dengan benar
cd "$(dirname "$0")/.." || exit 1

# Jalankan uvicorn dari root directory
echo "Menjalankan backend FastAPI di http://localhost:8000"
cd backend
uvicorn main:app --reload --port 8000 --host 0.0.0.0

