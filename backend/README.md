# Parkingly - Backend

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
`pip install -r requirements.txt`