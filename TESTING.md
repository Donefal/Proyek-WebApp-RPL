# Panduan Testing Register & Login

## Yang Sudah Diperbaiki

1. **Schema untuk Register & Login**: Ditambahkan `RegisterRequest` dan `LoginRequest` di `schemas.py`
2. **Router Auth**: Diperbaiki untuk menggunakan Pydantic schema dan error handling yang lebih baik
3. **Error Handling Frontend**: Diperbaiki untuk membaca error message dari FastAPI (format `{"detail": "message"}`)

## Cara Testing

### 1. Pastikan Backend Berjalan
```bash
cd Proyek-WebApp-RPL/backend
./run.sh
```

Backend harus berjalan di `http://localhost:8000`

### 2. Pastikan Database Siap
- Pastikan MySQL berjalan
- Pastikan database `fastapi_db` sudah dibuat
- Tabel akan dibuat otomatis saat pertama kali backend dijalankan

### 3. Test Register
1. Buka `http://localhost:5001/register.html`
2. Isi form:
   - Nama Lengkap: (contoh: "Budi Santoso")
   - Email: (contoh: "budi@example.com")
   - Password: (contoh: "123456")
3. Klik "Daftar"
4. Jika berhasil, akan muncul alert "Registrasi berhasil. Silakan login."
5. Cek di phpMyAdmin, data harus muncul di tabel `customer`

### 4. Test Login
1. Buka `http://localhost:5001/login.html`
2. Isi form dengan email dan password yang sudah didaftarkan
3. Klik "Submit"
4. Jika berhasil, akan redirect ke `index.html`
5. Cek di browser console (F12), harus ada session di localStorage

## Troubleshooting

### Error: "Email sudah terdaftar"
- Email tersebut sudah ada di database
- Gunakan email lain atau hapus data di database

### Error: "Email atau password salah"
- Email tidak ditemukan di database
- Pastikan sudah register terlebih dahulu

### Error: "Data tidak lengkap"
- Pastikan semua field diisi
- Cek format email harus valid

### Error: Connection refused / Network error
- Pastikan backend FastAPI berjalan di port 8000
- Cek di browser: `http://localhost:8000` harus menampilkan `{"message": "FastAPI is running!"}`
- Cek CORS sudah dikonfigurasi dengan benar

### Data tidak muncul di database
- Pastikan database connection di `database.py` benar
- Cek MySQL berjalan
- Cek database `fastapi_db` sudah dibuat
- Restart backend setelah mengubah database config

## Cek Database

Untuk melihat data yang sudah terdaftar:
```sql
SELECT * FROM customer;
```

atau melalui phpMyAdmin:
- Buka `http://localhost/phpmyadmin`
- Pilih database `fastapi_db`
- Buka tabel `customer`

