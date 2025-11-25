# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# Readme Irdhan
 Parkingly - Frontend
Irdhan: Frontend (HTML/CSS/JS)
- Cara setup frontend dari desain yg udh dibuat
- Connect backend (via fetch() dari js)
- Cara nampilin live data kesediaan parkir via map buatan
- QR Scan & generation dan gimana caranya agar disimpan (misal ke backend dulu apa gmn)
- Cara wesbitenya agar adaptif ke ukuran layar (mobile & pc)
- Setup batasan yang perlu, level frontend (input gk bisa kosong, gk boleh spasi, dkk) -> termasuk perubahan UI misal gk bisa dipencet dulu
- yg lainnya menyesuaikan

ref gpt https://chatgpt.com/s/t_691fbbdbbe4c8191943c4325af96020b 

UI figma https://www.figma.com/design/9frmEQL3vleBFF2hyxTNTm/Untitled?m=dev&t=7jvFiXfBvYlcRK0V-1

# ~~Paket 1 – Core Setup (paling penting dulu)~~
Berisi file dasar agar project langsung jalan:
- main.jsx
- App.jsx
- routes/AppRoutes.jsx
- services/api.js
- Struktur folder minimal versi hidup

# Paket 2 – Auth (Login + Register)
Berisi:
- pages/Login.jsx
- pages/Register.jsx
- services/auth.js
- components/Input.jsx
- components/Button.jsx
- hooks/useAuth.js

# Paket 3 – Map Parkir (live availability)
- pages/Map.jsx
- components/MapSlot.jsx
- services/slots.js

# Paket 4 – Karcis (QR, timer, harga)
- pages/Karcis.jsx
- components/QRViewer.jsx
- services/ticket.js

# Paket 5 – E-Wallet
- pages/Ewallet.jsx
- services/wallet.js

# Paket 6 – Admin
- pages/admin/AdminDashboard.jsx
- pages/admin/AdminScan.jsx
- components/QRScanner.jsx
- services/admin.js

# Paket 7 – Utils / Helpers
- utils/formatCurrency.js
- utils/formatTime.js
- utils/constants.js

# Paket 8 – Layouts
- layouts/UserLayout.jsx
- layouts/AdminLayout.jsx
- components/Navbar.jsx


---
---

# fungsi setiap pages

# Paket 1 – Struktur Halaman & Fungsinya

Berikut daftar lengkap halaman beserta fungsi utamanya berdasarkan diagram aktivitas dan diagram sekuens.

---

## 1. Login Page
**Fungsi:**
- Form input email/username & password.
- Mengirim request verifikasi akun ke backend.
- Menampilkan status verifikasi (berhasil/gagal).
- Redirect ke halaman “Map Kesediaan” jika sukses.

---

## 2. Register Page
**Fungsi:**
- Form registrasi: nama, email/no-telp, password.
- Request pembuatan akun ke backend.
- Menampilkan status registrasi.
- Redirect ke Login jika sukses.

---

## 3. Map Kesediaan (Halaman Utama Pemesan)
**Fungsi:**
- Menampilkan status seluruh slot parkir (kosong / dibooking / terisi).
- Memilih slot → request booking.
- Menampilkan hasil booking + QR ticket.
- Menyediakan tombol:
  - Scan QR Masuk
  - Scan QR Keluar
- Menampilkan countdown masa booking.

---

## 4. Ticket / QR Page (Scan QR Masuk)
**Fungsi:**
- Mengakses kamera untuk scan QR.
- Mengirim data QR ke backend untuk validasi.
- Menampilkan hasil validasi (valid/tidak valid).
- Indikator bahwa gerbang terbuka (jika valid).

---

## 5. Wallet Page (E-Wallet)
**Fungsi:**
- Menampilkan saldo pengguna.
- Form input dan tombol top-up saldo.
- Menampilkan notifikasi top-up berhasil.
- (Opsional) Riwayat transaksi.

---

## 6. Admin Dashboard
**Fungsi:**
- Menampilkan status seluruh slot parkir secara real-time.
- Ringkasan penggunaan harian (jumlah mobil masuk/keluar).
- Tombol navigasi:
  - Scan QR Admin
  - Laporan Keuangan.

---

## 7. Admin Scan Page
**Fungsi:**
- Scan QR seperti user, tetapi dengan kemampuan override.
- Menampilkan detail transaksi/booking berdasarkan QR.
- Tombol manual membuka gerbang (untuk kondisi khusus).
- Menampilkan status slot terkait.

---

## 8. Laporan Keuangan (Admin)
**Fungsi:**
- Menampilkan seluruh transaksi (parkir, denda, top-up, dsb).
- Filter berdasarkan tanggal.
- Perhitungan total pendapatan.
- (Opsional) Export CSV/PDF.

---

# Ringkasan
| Page | Fungsi Utama |
|------|--------------|
| Login | Verifikasi akun & masuk ke sistem |
| Register | Membuat akun baru |
| Map Kesediaan | Cek slot, booking, QR ticket |
| Scan Ticket | Validasi QR untuk masuk |
| Wallet | Saldo & top-up |
| Admin Dashboard | Monitoring lahan & navigasi admin |
| Admin Scan | Scan & override admin |
| Laporan Keuangan | Rekap & total transaksi |

---

# Catatan
- Paket 1: fokus UI lengkap + integrasi dasar.
- Paket 2: auth system, logic integrasi penuh, pembayaran, laporan, override admin.
