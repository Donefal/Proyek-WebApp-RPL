# Dokumentasi Integrasi Frontend dan Backend

## Ringkasan
Frontend dan Backend FastAPI telah terintegrasi. Frontend sekarang memanggil API FastAPI langsung tanpa melalui Express.js mock server.

## Perubahan yang Dilakukan

### Backend (FastAPI)
1. **CORS Middleware**: Ditambahkan untuk mengizinkan request dari frontend
2. **Router Baru**:
   - `routers/auth.py`: Authentication (login, register)
   - `routers/parking.py`: Parking operations (spots, book, active, cancel, history)
   - `routers/wallet.py`: Wallet operations (balance, topup)
   - `routers/admin.py`: Admin operations (spots, scan, reports)

3. **Main.py**: Diupdate untuk include semua router baru

### Frontend
1. **API_BASE_URL**: Diubah dari `http://localhost:5001/api` menjadi `http://localhost:8000`
   - File yang diupdate: `app.js`, `booking.js`, `auth.js`

## Cara Menjalankan

### 1. Setup Database
Pastikan MySQL sudah berjalan dan database `fastapi_db` sudah dibuat.

### 2. Setup Virtual Environment (Hanya pertama kali)
```bash
cd Proyek-WebApp-RPL/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Jalankan Backend FastAPI
**Cara 1: Menggunakan script (Paling Mudah - RECOMMENDED)**
```bash
cd Proyek-WebApp-RPL
./backend/start_backend.sh
```

**Cara 2: Manual dari root directory**
```bash
cd Proyek-WebApp-RPL
source backend/venv/bin/activate
export PYTHONPATH=$(pwd)
python -m uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0
```

**Cara 3: Manual dari backend directory (tidak disarankan)**
```bash
cd Proyek-WebApp-RPL/backend
source venv/bin/activate
cd ..
export PYTHONPATH=$(pwd)
python -m uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0
```

Backend akan berjalan di `http://localhost:8000`

### 4. Jalankan Frontend
Buka file HTML langsung di browser atau gunakan web server sederhana:

```bash
cd Proyek-WebApp-RPL/frontend
# Menggunakan Python
python -m http.server 5001

# Atau menggunakan Node.js (jika masih ada server.js)
# node server.js
```

Frontend akan berjalan di `http://localhost:5001`

## Endpoint API

### Authentication
- `POST /auth/register` - Registrasi user baru
- `POST /auth/login` - Login user

### Parking
- `GET /parking/spots` - Dapatkan semua slot parkir
- `POST /parking/book` - Buat booking baru
- `GET /parking/active` - Dapatkan booking aktif
- `POST /parking/cancel` - Batalkan booking
- `GET /parking/history` - Dapatkan riwayat parkir

### Wallet
- `GET /wallet` - Dapatkan saldo wallet
- `POST /wallet/topup` - Top up saldo

### Admin
- `GET /admin/spots` - Dapatkan semua slot (admin view)
- `POST /admin/scan` - Scan QR code untuk validasi
- `GET /admin/reports` - Dapatkan laporan admin

## Catatan Penting

1. **Authentication**: Saat ini menggunakan token sederhana (`token-{user_id}`). Untuk production, disarankan menggunakan JWT yang proper.

2. **Database**: Pastikan semua tabel sudah dibuat. FastAPI akan membuat tabel otomatis saat pertama kali dijalankan jika menggunakan `models.Base.metadata.create_all()`.

3. **CORS**: CORS sudah dikonfigurasi untuk mengizinkan request dari `localhost:5001` dan `localhost:8000`.

4. **QR Token**: QR token untuk booking disimpan di response, bukan di database. Untuk production, disarankan menyimpan QR token di database.

## Troubleshooting

1. **Error CORS**: Pastikan backend FastAPI sudah berjalan dan CORS sudah dikonfigurasi dengan benar.

2. **Error 401 Unauthorized**: Pastikan user sudah login dan token sudah disimpan di localStorage.

3. **Error Database**: Pastikan MySQL sudah berjalan dan kredensial di `database.py` sudah benar.

4. **Endpoint tidak ditemukan**: Pastikan semua router sudah di-include di `main.py`.

