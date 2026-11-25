# Panduan Hosting: dari Repository sampai Tautan Bisa Dibagikan

Hasil akhir panduan ini:

| Bagian | Layanan | Alamat |
|---|---|---|
| Frontend | GitHub Pages (gratis) | `https://muhamadivan1.github.io/pantau-distribusi/` |
| Backend dan dokumentasi API | Render, paket Free | `https://pantau-distribusi-api.onrender.com/docs` |

Urutannya penting: **backend dulu**, karena alamat backend dibutuhkan saat membangun frontend.

Sebelum mulai, repository `pantau-distribusi` sudah harus ada di GitHub dan berstatus Public. Caranya ada di [PANDUAN_GITHUB.md](PANDUAN_GITHUB.md).

---

## A. Yang perlu diketahui tentang paket gratis Render

| Sifat | Akibat untuk proyek ini | Cara proyek ini menanganinya |
|---|---|---|
| Layanan tidur setelah 15 menit tanpa akses, dan butuh sekitar satu menit untuk bangun | Pengunjung pertama menunggu | Frontend langsung tampil dalam mode demo, lalu beralih otomatis ke server begitu server bangun |
| Sistem berkas tidak permanen: perubahan hilang setiap redeploy, restart, atau tidur | Database SQLite ikut terhapus | `DEMO_MODE=true` mengisi ulang data contoh setiap server start |
| 750 jam instans gratis per workspace per bulan | Cukup untuk satu layanan menyala terus | Cukup untuk satu backend |

Sumber: [Render Docs, Deploy for Free](https://render.com/docs/free). Render sendiri menyarankan paket gratis tidak dipakai untuk produksi. Untuk portofolio, paket ini cukup.

---

## B. Hosting backend di Render

### B1. Buat akun

1. Buka https://render.com, klik **Get Started**.
2. Pilih **GitHub** untuk mendaftar, supaya Render bisa membaca repository Anda.
3. Ikuti petunjuk pendaftaran sampai masuk ke Dashboard.

### B2. Buat layanan dari Blueprint

Repository ini sudah berisi `render.yaml`, jadi pengaturan terisi otomatis.

1. Di Dashboard, klik **New**, lalu **Blueprint**.
2. Pilih repository `muhamadivan1/pantau-distribusi`. Jika tidak muncul, klik **Configure account** dan beri Render akses ke repository itu.
3. Isi **Blueprint Name**, misalnya `pantau-distribusi`.
4. Render menampilkan satu layanan: `pantau-distribusi-api` (Web Service, Free). Klik **Deploy Blueprint** (atau **Apply**).
5. Tunggu proses build selesai, biasanya 2 sampai 5 menit. Log bisa dilihat di halaman layanan, tab **Logs**. Tanda berhasil: `Uvicorn running on http://0.0.0.0:...`.

### B3. Catat alamat dan kunci

1. Buka layanan `pantau-distribusi-api`. Alamatnya tertulis di bagian atas, misalnya `https://pantau-distribusi-api.onrender.com`. Jika nama itu sudah dipakai orang lain, Render menambahkan akhiran acak. **Pakai alamat yang tertulis di dashboard Anda.**
2. Buka tab **Environment**, cari `API_KEY`, klik ikon mata untuk melihat nilainya. Simpan baik-baik. Kunci ini dipakai jika ingin mengirim telemetri dari `tools/simulate.py` ke server online.

### B4. Periksa backend

Buka di browser:

| Alamat | Hasil yang benar |
|---|---|
| `https://<alamat-anda>/api/v1/health` | `{"status":"ok","version":"1.0.0","demo_mode":true}` |
| `https://<alamat-anda>/docs` | Halaman Swagger berisi semua endpoint |
| `https://<alamat-anda>/api/v1/feeders` | Enam penyulang dalam JSON |

Jika halaman memuat lama, itu wajar: server sedang bangun dari tidur.

### B5. Jika Blueprint gagal: buat manual

1. **New > Web Service**, pilih repository.
2. Isi:

    | Kolom | Nilai |
    |---|---|
    | Name | `pantau-distribusi-api` |
    | Language | Python 3 |
    | Branch | `main` |
    | Root Directory | `backend` |
    | Build Command | `pip install -r requirements.txt` |
    | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
    | Instance Type | Free |

3. Di **Environment Variables**, tambahkan:

    | Key | Value |
    |---|---|
    | `PYTHON_VERSION` | `3.12.8` |
    | `DEMO_MODE` | `true` |
    | `DEMO_TICK_SECONDS` | `5` |
    | `DATABASE_URL` | `sqlite:///./pantau.db` |
    | `CORS_ORIGINS` | `https://muhamadivan1.github.io,http://localhost:5173` |
    | `API_KEY` | kata acak panjang buatan Anda sendiri |

    Opsional: bila nanti memakai Gerbang Telemetri, tambahkan `DEMO_SIMULATED_FEEDERS` = `PYL-01,PYL-02,PYL-03,PYL-06`. Penjelasannya ada di `PANDUAN_HOSTING.md` repository `gerbang-telemetri`.

4. Di **Advanced**, isi **Health Check Path** dengan `/api/v1/health`.
5. Klik **Deploy Web Service**.

---

## C. Hosting frontend di GitHub Pages

Workflow `.github/workflows/deploy-frontend.yml` sudah disiapkan. Anda hanya perlu tiga pengaturan.

### C1. Aktifkan Pages lewat GitHub Actions

1. Buka repository di GitHub, klik **Settings**, lalu **Pages** di menu kiri.
2. Pada **Build and deployment > Source**, pilih **GitHub Actions**.

### C2. Simpan alamat backend sebagai variabel

1. Masih di **Settings**, buka **Secrets and variables > Actions**.
2. Pilih tab **Variables**, klik **New repository variable**.
3. Isi:

    | Kolom | Nilai |
    |---|---|
    | Name | `VITE_API_URL` |
    | Value | alamat backend dari langkah B3, **tanpa garis miring di akhir**, contoh `https://pantau-distribusi-api.onrender.com` |

4. Klik **Add variable**.

Ini bukan rahasia. Alamat backend memang akan terlihat oleh browser pengunjung. Jika variabel ini tidak diisi, website tetap jalan dalam mode demo.

### C3. Jalankan deploy

1. Klik tab **Actions**.
2. Pilih workflow **Deploy frontend** di kiri, klik **Run workflow**, lalu **Run workflow** lagi.
3. Tunggu dua job (`build` dan `deploy`) bertanda centang hijau, sekitar 1 sampai 2 menit.
4. Klik job `deploy`. Alamat website tertulis di sana: `https://muhamadivan1.github.io/pantau-distribusi/`.

Setelah ini, setiap push yang mengubah folder `frontend` akan men-deploy ulang secara otomatis.

### C4. Rapikan halaman repository

Di halaman utama repository, klik ikon roda gigi di samping **About**:

| Kolom | Isi |
|---|---|
| Description | `Dashboard pemantauan penyulang 20 kV: integrasi telemetri multi-format, alarm, gangguan, SAIDI/SAIFI. FastAPI + React.` |
| Website | centang **Use your GitHub Pages website** |
| Topics | `fastapi`, `react`, `python`, `rest-api`, `data-integration`, `scada`, `portfolio`, `category-backend` |

Topik `portfolio` dan `category-backend` dibaca oleh website portofolio Anda untuk menentukan urutan dan kategori.

---

## D. Periksa hasil online

- [ ] Buka `https://muhamadivan1.github.io/pantau-distribusi/`. Mula-mula tampil "Menghubungkan ke server" atau "Mode demo"
- [ ] Dalam sekitar satu menit, pojok kiri bawah berubah menjadi **Terhubung ke server**
- [ ] Angka beban berubah setiap beberapa detik (simulator berjalan di server)
- [ ] Konfirmasi satu alarm, lalu muat ulang halaman. Konfirmasi tetap tersimpan
- [ ] Buka halaman Keandalan dan Serah terima
- [ ] Buka dari HP, tampilan dua kolom tanpa gulir ke samping
- [ ] Buka `https://<alamat-backend>/docs` dan coba `GET /feeders` lewat tombol **Try it out**

---

## E. Mengirim telemetri ke server online (opsional)

Dari laptop, di folder `backend` dengan virtual environment aktif:

```bash
python tools/simulate.py --url https://<alamat-backend> --key <API_KEY dari langkah B3> --count 5 --trip PYL-02
```

Lihat dashboard online: PYL-02 akan padam lalu pulih.

---

## F. Masukkan ke website portofolio

Website portofolio `muhamadivan1.github.io` mengambil repository GitHub secara otomatis. Setelah topik di langkah C4 dipasang, proyek ini muncul sendiri.

Supaya tampil dengan cerita lengkap dan di urutan atas, tambahkan blok berikut di `assets/js/data.js` repository portofolio, di dalam `projects: [ ... ]`:

```js
{
  id: "pantau-distribusi",
  name: "Pantau Distribusi",
  repoName: "pantau-distribusi",
  boost: 35,
  category: "backend",
  status: "done",
  year: "2026",
  tagline: {
    id: "Dashboard pemantauan penyulang 20 kV dengan integrasi telemetri multi-format",
    en: "20 kV feeder monitoring dashboard with multi-format telemetry integration",
  },
  problem: {
    id: "Data beban penyulang datang dari RTU, IED, dan sistem meter dengan struktur, satuan, dan format waktu berbeda. Gangguan dan indeks keandalan sering dicatat terpisah.",
    en: "Feeder load data comes from RTUs, IEDs and metering systems with different structures, units and time formats. Outages and reliability indices are often recorded separately.",
  },
  solution: {
    id: "Backend FastAPI dengan pola Adapter dan Canonical Data Model untuk tiga format telemetri, alarm bertingkat, gangguan otomatis, serta SAIDI, SAIFI, CAIDI sesuai IEEE Std 1366. Frontend React menampilkan diagram busbar per gardu induk.",
    en: "A FastAPI backend using the Adapter and Canonical Data Model patterns for three telemetry formats, tiered alarms, automatic outage records, and SAIDI, SAIFI and CAIDI per IEEE Std 1366. A React frontend shows a busbar diagram per substation.",
  },
  role: {
    id: "Perancang dan pengembang tunggal, dari PRD, UML, BPMN, sampai deployment. Penulisan sebagian kode dibantu AI dan diverifikasi dengan test.",
    en: "Sole designer and developer, from PRD, UML and BPMN to deployment. Parts of the code were written with AI assistance and verified with tests.",
  },
  highlights: {
    id: [
      "Satu endpoint menerima tiga format telemetri yang dikenali dari isi payload",
      "Gangguan terbuka dan tertutup otomatis dari telemetri",
      "53 test otomatis (pytest dan Vitest) berjalan di GitHub Actions",
      "Mode demo tetap berfungsi saat server gratis sedang tidur",
    ],
    en: [
      "One endpoint accepts three telemetry formats detected from the payload",
      "Outages open and close automatically from telemetry",
      "53 automated tests (pytest and Vitest) run on GitHub Actions",
      "Demo mode keeps working while the free server is asleep",
    ],
  },
  stack: ["Python", "FastAPI", "SQLAlchemy", "React", "Vite", "Recharts", "pytest", "GitHub Actions"],
  repo: "",
  demo: "https://muhamadivan1.github.io/pantau-distribusi/",
},
```

Lalu di repository portofolio:

```bash
npm test
git add assets/js/data.js
git commit -m "feat: tambah proyek pantau distribusi ke daftar kurasi"
git push
```

---

## G. Masalah yang sering muncul

| Gejala | Penyebab | Solusi |
|---|---|---|
| Build Render gagal di `pip install` | Versi Python tidak cocok | Pastikan `PYTHON_VERSION` = `3.12.8` di tab Environment, lalu **Manual Deploy > Clear build cache & deploy** |
| Render menampilkan `Application exited early` | Start command salah atau Root Directory bukan `backend` | Cek kembali isian di B5 |
| Website selalu "Mode demo" | `VITE_API_URL` kosong atau salah | Cek variabel di C2, lalu jalankan ulang workflow Deploy frontend |
| Console browser menunjukkan galat CORS | Alamat website tidak ada di `CORS_ORIGINS` | Tambahkan alamat tanpa path (contoh `https://muhamadivan1.github.io`) di tab Environment Render, simpan, tunggu redeploy |
| Halaman Pages 404 | Source Pages belum diatur ke GitHub Actions, atau workflow belum jalan | Ulangi C1 dan C3 |
| Workflow gagal di langkah `deploy` dengan pesan izin | Source Pages masih "Deploy from a branch" | Ganti ke **GitHub Actions** di C1 |
| Data yang saya ubah hilang | Server tidur atau redeploy, disk gratis tidak permanen | Wajar di paket gratis. Untuk data permanen, pakai database PostgreSQL eksternal lewat `DATABASE_URL` |
| `401` saat simulate.py ke server online | Kunci salah | Salin ulang `API_KEY` dari tab Environment |
