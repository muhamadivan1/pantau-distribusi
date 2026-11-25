# Panduan Menjalankan Pantau Distribusi

## 1. Yang perlu dipasang

| Alat | Versi | Cek dengan | Unduh |
|---|---|---|---|
| Python | 3.12 atau lebih baru | `python --version` | https://www.python.org/downloads (centang **Add python.exe to PATH**) |
| Node.js | 22 LTS | `node --version` | https://nodejs.org |
| Git | terbaru | `git --version` | https://git-scm.com/downloads |
| VS Code | terbaru | | https://code.visualstudio.com |

Perintah di bawah ditulis untuk **Git Bash** atau terminal VS Code di Windows. Di sebagian komputer, `python` bernama `py`.

## 2. Menjalankan backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Git Bash di Windows
# .venv\Scripts\activate           # Command Prompt atau PowerShell
# source .venv/bin/activate        # macOS atau Linux
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Tanda berhasil: muncul `Uvicorn running on http://127.0.0.1:8000`.

| Alamat | Isi |
|---|---|
| http://127.0.0.1:8000/docs | Dokumentasi API interaktif, bisa mencoba setiap endpoint |
| http://127.0.0.1:8000/api/v1/feeders | Status semua penyulang dalam JSON |

Saat pertama start, mode demo mengisi data contoh (6 penyulang, telemetri 24 jam, 28 gangguan) ke berkas `pantau.db`, lalu simulator mengirim telemetri setiap 5 detik.

### Pengaturan

Salin `.env.example` menjadi `.env` di folder `backend`, lalu ubah sesuai kebutuhan:

| Variabel | Bawaan | Fungsi |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./pantau.db` | Lokasi database |
| `API_KEY` | `dev-key-ganti-saya` | Kunci untuk `POST /telemetry` |
| `DEMO_MODE` | `true` | Isi data contoh dan jalankan simulator |
| `DEMO_TICK_SECONDS` | `5` | Jeda simulator. `0` mematikan simulator tetapi tetap mengisi data contoh |
| `DEMO_SIMULATED_FEEDERS` | kosong (semua) | Penyulang yang dibuat simulator, dipisah koma. Isi `PYL-01,PYL-02,PYL-03,PYL-06` bila PYL-04 dan PYL-05 dipasok Gerbang Telemetri |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Alamat frontend yang boleh memanggil API |
| `THRESHOLD_WASPADA_PCT` | `80` | Ambang status waspada |
| `THRESHOLD_KRITIS_PCT` | `95` | Ambang status kritis |
| `PADAM_VOLTAGE_KV` | `2` | Di bawah tegangan ini penyulang dianggap padam |

Untuk mengulang data dari awal, hentikan server, hapus `pantau.db`, lalu jalankan lagi.

## 3. Menjalankan frontend

Buka terminal kedua (backend tetap berjalan):

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Buka http://localhost:5173. Pojok kiri bawah harus menunjukkan **Terhubung ke server**.

Isi `frontend/.env`:

| Variabel | Fungsi |
|---|---|
| `VITE_API_URL=http://127.0.0.1:8000` | Alamat backend |
| `VITE_API_URL=` (kosong) | Mode demo tanpa backend |

Setiap mengubah `.env`, hentikan `npm run dev` dengan `Ctrl + C` lalu jalankan lagi.

## 4. Mengirim telemetri seperti gateway

Untuk menunjukkan endpoint telemetri bekerja tanpa simulator internal, jalankan backend dengan simulator mati:

```bash
# terminal 1, di folder backend
DEMO_TICK_SECONDS=0 uvicorn app.main:app --reload

# terminal 2, di folder backend
python tools/simulate.py --url http://127.0.0.1:8000 --key dev-key-ganti-saya
```

Pilihan lain:

| Perintah | Fungsi |
|---|---|
| `python tools/simulate.py --trip PYL-02` | Paksa PYL-02 padam enam langkah lalu pulih |
| `python tools/simulate.py --count 3` | Kirim tiga langkah saja |
| `python tools/simulate.py --interval 1` | Kirim setiap detik |

Setiap baris keluaran menunjukkan adapter yang dipakai dan berapa rekaman tersimpan, ditolak, serta alarm dan gangguan yang terbentuk.

Di PowerShell, ganti `DEMO_TICK_SECONDS=0 uvicorn ...` dengan `$env:DEMO_TICK_SECONDS=0; uvicorn app.main:app --reload`.

## 5. Menjalankan test

```bash
cd backend && pytest          # 39 test
cd frontend && npm test       # 14 test
```

## 6. Membuat ulang berkas turunan

Beberapa berkas dihasilkan dari kode. Jalankan ulang setelah mengubah endpoint, data contoh, atau proses bisnis:

| Berkas | Perintah (dari folder utama) |
|---|---|
| `docs/openapi.json` dan `frontend/src/api/demo-data.json` | `python backend/tools/export_docs.py` |
| `docs/bpmn/*.bpmn` | `python tools/build_bpmn.py` |

## 7. Menambah format telemetri baru

1. Buat berkas di `backend/app/adapters/`, misalnya `scada_json.py`, berisi kelas turunan `TelemetryAdapter` dengan metode `supports()` dan `parse()`.
2. Daftarkan di `default_registry` dalam `backend/app/adapters/registry.py`.
3. Tambah test di `backend/tests/test_adapters.py`, termasuk test bahwa hasilnya sama dengan format lain untuk nilai yang sama.

Tidak ada perubahan di service, router, maupun frontend.

## 8. Masalah yang sering muncul

| Gejala | Penyebab | Solusi |
|---|---|---|
| `python` tidak dikenali | Python belum di PATH | Pasang ulang dan centang Add to PATH, atau pakai `py` |
| `uvicorn` tidak dikenali | Virtual environment belum aktif | Jalankan perintah aktivasi di bagian 2 |
| Frontend tetap "Mode demo" | Backend mati, atau `.env` frontend belum dibuat | Cek http://127.0.0.1:8000/api/v1/health, lalu jalankan ulang `npm run dev` |
| Galat CORS di Console browser | Alamat frontend tidak ada di `CORS_ORIGINS` | Tambahkan alamatnya di `backend/.env` |
| `401` saat menjalankan simulate.py | Kunci berbeda dengan `API_KEY` server | Samakan `--key` dengan `API_KEY` |
| Port 8000 sudah dipakai | Server lain masih berjalan | `uvicorn app.main:app --port 8001` dan sesuaikan `VITE_API_URL` |
