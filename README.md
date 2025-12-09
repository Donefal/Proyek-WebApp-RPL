# Proyek-WebApp-RPL
Tugas akhir Rekayasa Perangkat Lunak Semester 3

## Parkingly: Aplikasi booking parkir online dengan sistem self-service
Aplikasi yang akan dibuat bernama Parkingly yang memungkinkan pengguna untuk melakukan booking parkir secara online. Aplikasi ini memudahkan pengguna untuk melihat kesediaan lahan parkir, melakukan pemesanan lahan, dan melakukan pembayaran secara digital. Sistem ini didukung dengan perangkat keras berbasis IoT yang menggunakan sensor ultrasonic untuk memastikan kosongnya lahan parkir, sekaligus menghitung tarif parkir yang dibayarkan. Sehingga menghasillkan pengalaman self-service yang nyaman dilakukan

### Links
- 🔵 [Diagram Perancangan dkk](https://docs.google.com/document/d/1ssZJYY3XQVtuNRE1M58j9wiIHCUNradvOZLnqWeol6w/edit?usp=sharing)
- 🔵 [Drive dokumen](https://drive.google.com/drive/folders/1cyqF4U8dpLJOzde2isi9cRhaTVICb4Hb?usp=sharing )
- 🔵 [Link desain](https://www.figma.com/design/9frmEQL3vleBFF2hyxTNTm/Untitled?node-id=0-1&p=f&t=wYm7AqpiYEdpHEU2-0)
- 🔵 [Link pengumpulan monitoring RPL](https://forms.gle/kZs1g5QCwCTRw1pGA)
- 🔵 [Skematik WokWi](https://wokwi.com/projects/448224765608390657)

### Stack
- 🟢 HTML/CSS/JavaScript (Node Js)
- 🟡 Laragon + Python: MySQL + FastAPI
- 🔴 C++ 

## Running The WebApp (Dev Mode)
### 1. Nyalakan Laragon
- Buka laragon dan aktifkan `apache` server dan `mysql`. 
- Bila diminta login, gunakan ID: `root` dan masuk tanpa password
- Pastikan database dengan nama `fastapi_db` sudah dibuat (buka `phpmyadmin` via menu laragon)
### 2. Run Backend
Gunakan command berikut:
```powershell
backend/rundev.bat
```
### 3. Run Frontend
Gunakan command berikut:
```powershell
npm run dev
```
### 4. Buka webapp
- Frontend: `http://localhost:5001`
- Backend: `http://localhost:8000/docs`
- Database: Buka `phpmyadmin` via menu laragon (jika belum)