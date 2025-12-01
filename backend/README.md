# Parkingly - Backend

## Content:
1. Instalasi
2. Testing

## Instalasi
Untuk menginstall dependencies yang dibutuhkan ketik command berikut pada direktori `backend/`

### 1. Buat Virtual Environment 
```powershell
python3 -m venv .venv
```

### 2. Run Virtual Environment
```powershell
.venv/Scripts/activate
```

### 3. (Troubleshoot) Jika ErrorId : UnauthorizedAccess
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass
```
Command diatas akan mengizinkan user saat ini untuk menjalankan script pada powershell. Lalu ketik command pada `step 2` kembali

### 4. Pengecekan
Apabila Virtual Environment sudah berjalan akan ada `(.venv)` sebelum direktori pada terminal. Akan muncul file `.venv` juga pada folder backend

### 5. Instalasi dependencies
```powershell
pip install -r requirements.txt
```

### 6. Keluar dari Virtual Environment
Gunakan ini apabila ingin mengerjakan bagian lain selain Backend. Cukup dengan command:
```powershell
deactivate
```

### 7. Menyalakan ulang venv
Seperti pada step 2:
```powershell
.venv/Scripts/activate
```

## Running Backend
Gunakan command berikut ketika **setelah melakukan instalasi dan venv dalam keadaan aktif**. Command berikut akan mengatifkan fastAPI di dengan ip host 0.0.0.0 (listening semua device termasuk esp32) dan pada port 8000
```powershell
fastapi dev fastAPI_esp32:app --host 0.0.0.0 --port 8000
```

### Testing
Untuk melakukan testing dapat membuka http://127.0.0.1:8000/docs yang juga tercantum pada respon dari command diatas