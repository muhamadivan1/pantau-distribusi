# Panduan GitHub: Commit dan Push Pantau Distribusi

Panduan ini membawa folder proyek dari laptop ke repository GitHub `muhamadivan1/pantau-distribusi` dengan **18 commit bertahap**. Setelah itu, lanjut ke [PANDUAN_HOSTING.md](PANDUAN_HOSTING.md) untuk membuatnya online.

| Bagian | Isi |
|---|---|
| A | Persiapan (sekali per laptop) |
| B | Buat repository di GitHub |
| C | Siapkan folder |
| D | 18 commit bertahap |
| E | Push |
| F | Memperbarui proyek setelah ini |
| G | Masalah yang sering muncul |
| H | Pembaruan ke versi 1.1.0 (integrasi Gerbang Telemetri) |

Semua perintah ditulis untuk **Git Bash** di Windows. Cara membukanya: buka folder proyek di File Explorer, klik kanan di area kosong, pilih **Open Git Bash here** (di Windows 11 ada di **Show more options**).

Pesan commit mengikuti [Conventional Commits](https://www.conventionalcommits.org): `jenis(bagian): ringkasan`.

| Jenis | Dipakai untuk |
|---|---|
| `feat` | Fitur baru |
| `fix` | Perbaikan kesalahan |
| `test` | Menambah atau mengubah test |
| `docs` | Dokumentasi |
| `ci` | Workflow GitHub Actions dan konfigurasi deploy |
| `chore` | Persiapan dan pengaturan proyek |

---

## A. Persiapan

1. Pasang Git dari https://git-scm.com/downloads (biarkan pilihan bawaan).
2. Atur identitas. Email **harus sama** dengan email terverifikasi di https://github.com/settings/emails, atau commit tidak dihitung di grafik kontribusi.

    ```bash
    git config --global user.name "Muhamad Ivan Fadilah"
    git config --global user.email "email-terdaftar-di-github@contoh.com"
    git config --global init.defaultBranch main
    ```

3. Pastikan test lulus sebelum commit (lihat [docs/PANDUAN_MENJALANKAN.md](docs/PANDUAN_MENJALANKAN.md)):

    ```bash
    cd backend && pytest && cd ..
    cd frontend && npm ci && npm test && cd ..
    ```

## B. Buat repository di GitHub

1. Buka https://github.com/new.
2. **Repository name**: `pantau-distribusi`.
3. **Description**: `Dashboard pemantauan penyulang 20 kV: integrasi telemetri multi-format, alarm, gangguan, SAIDI/SAIFI. FastAPI + React.`
4. Pilih **Public**.
5. Jangan centang README, jangan pilih .gitignore, jangan pilih license. Ketiganya sudah ada.
6. Klik **Create repository**.

## C. Siapkan folder

1. Ekstrak `pantau-distribusi.zip`, lalu pindahkan folder `pantau-distribusi` ke tempat kerja tetap, misalnya `D:\Projects\pantau-distribusi`.
2. Buka Git Bash di folder itu. Pastikan `README.md`, `backend`, dan `frontend` langsung terlihat:

    ```bash
    ls
    ```

3. Pastikan belum ada riwayat Git (hasil yang benar: `fatal: not a git repository`):

    ```bash
    git status
    ```

    Jika malah menampilkan daftar berkas, hapus riwayat lama dengan `rm -rf .git`.

4. Pastikan berkas yang tidak boleh ikut (folder `node_modules`, `.venv`, `pantau.db`, `.env`) tidak ada, atau sudah tercantum di `.gitignore`. Berkas `.gitignore` sudah disiapkan, jadi folder itu otomatis diabaikan.

5. Mulai repository:

    ```bash
    git init
    ```

## D. 18 commit bertahap

Jalankan satu blok, tunggu selesai, lalu lanjut ke blok berikutnya. Cara menempel di Git Bash: klik kanan lalu **Paste**, atau `Shift + Insert`.

### Backend

**Commit 1. Inisialisasi**

```bash
git add .gitignore LICENSE
git commit -m "chore: inisialisasi proyek pantau distribusi"
```

**Commit 2. Pengaturan, database, dan model**

```bash
git add backend/app/__init__.py backend/app/config.py backend/app/db.py backend/app/models.py backend/app/timeutil.py backend/requirements.txt backend/.env.example backend/.python-version backend/pytest.ini
git commit -m "feat(backend): tambah pengaturan, koneksi database, dan model tabel"
```

**Commit 3. Skema API**

```bash
git add backend/app/schemas.py
git commit -m "feat(backend): tambah skema data masuk dan keluar API"
```

**Commit 4. Adapter tiga format**

```bash
git add backend/app/adapters/
git commit -m "feat(backend): tambah adapter rtu-ioa, modbus, dan csv-meter dengan registry"
```

**Commit 5. Ingest, status, alarm, dan gangguan**

```bash
git add backend/app/services/__init__.py backend/app/services/status.py backend/app/services/events.py backend/app/services/ingestion.py
git commit -m "feat(backend): tambah alur ingest, status penyulang, alarm, dan gangguan otomatis"
```

**Commit 6. Keandalan dan serah terima**

```bash
git add backend/app/services/reliability.py backend/app/services/shift_report.py
git commit -m "feat(backend): hitung SAIDI SAIFI CAIDI dan ringkasan serah terima shift"
```

**Commit 7. Simulator dan data contoh**

```bash
git add backend/app/services/simulator.py backend/app/seed.py
git commit -m "feat(backend): tambah simulator telemetri dan data contoh fiktif"
```

**Commit 8. Endpoint dan titik masuk**

```bash
git add backend/app/deps.py backend/app/routers/ backend/app/main.py
git commit -m "feat(backend): tambah endpoint REST dan titik masuk aplikasi"
```

**Commit 9. Test backend**

```bash
git add backend/tests/ backend/requirements-dev.txt
git commit -m "test(backend): tambah test adapter, ingest, keandalan, simulator, dan API"
```

**Commit 10. Skrip pendukung**

```bash
git add backend/tools/
git commit -m "feat(backend): tambah gateway tiruan dan skrip ekspor dokumen"
```

### Frontend

**Commit 11. Kerangka React**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html frontend/.env.example frontend/public/ frontend/src/main.jsx
git commit -m "feat(frontend): tambah kerangka proyek React dan Vite"
```

**Commit 12. Lapisan data**

```bash
git add frontend/src/api/ApiContext.jsx frontend/src/api/live.js frontend/src/api/demo.js frontend/src/api/demo-data.json frontend/src/lib/format.js frontend/src/lib/status.js frontend/src/lib/report.js
git commit -m "feat(frontend): tambah klien API live, mode demo, dan alat format"
```

**Commit 13. Halaman dan tampilan**

```bash
git add frontend/src/App.jsx frontend/src/components/ frontend/src/pages/ frontend/src/styles.css
git commit -m "feat(frontend): tambah diagram busbar, enam halaman, dan gaya tampilan"
```

**Commit 14. Test frontend**

```bash
git add frontend/src/api/demo.test.js frontend/src/lib/format.test.js frontend/src/lib/status.test.js frontend/src/lib/report.test.js
git commit -m "test(frontend): tambah test format, status, laporan, dan mode demo"
```

### Deploy dan dokumentasi

**Commit 15. CI dan konfigurasi hosting**

```bash
git add .github/ render.yaml
git commit -m "ci: tambah workflow test, deploy GitHub Pages, dan blueprint Render"
```

**Commit 16. Dokumen rancangan**

```bash
git add docs/PRD.md docs/ARCHITECTURE.md docs/UML.md docs/DATA_MODEL.md docs/API.md docs/openapi.json docs/TEST_PLAN.md docs/PANDUAN_MENJALANKAN.md
git commit -m "docs: tambah PRD, arsitektur, UML, model data, API, dan rencana uji"
```

**Commit 17. BPMN**

```bash
git add docs/BPMN.md docs/bpmn/ tools/
git commit -m "docs: tambah diagram BPMN dan skrip pembuatnya"
```

**Commit 18. README dan panduan**

```bash
git add README.md PANDUAN_GITHUB.md PANDUAN_HOSTING.md CHANGELOG.md docs/screenshots/
git commit -m "docs: tambah README, panduan GitHub dan hosting, changelog, dan tangkapan layar"
```

### Periksa sebelum push

```bash
git status
git log --oneline
```

`git status` harus menampilkan `nothing to commit, working tree clean`, dan `git log --oneline` harus menampilkan 18 baris.

Jika `git status` masih menunjukkan berkas tersisa, lihat namanya. Berkas seperti `pantau.db`, `node_modules`, atau `.env` seharusnya tidak muncul (sudah diabaikan). Berkas lain yang memang bagian proyek bisa di-commit dengan pesan yang sesuai.

## E. Push

```bash
git branch -M main
git remote add origin https://github.com/muhamadivan1/pantau-distribusi.git
git push -u origin main
```

Saat pertama push, pilih **Sign in with your browser**. Push berhasil jika muncul `main -> main`.

Setelah push:

1. Buka tab **Actions**. Workflow **CI** harus bertanda centang hijau (sekitar 1 sampai 2 menit). Ini bukti di depan perekrut bahwa semua test lulus.
2. Workflow **Deploy frontend** mungkin gagal di langkah `deploy` karena Pages belum diaktifkan. Itu normal. Lanjutkan ke [PANDUAN_HOSTING.md](PANDUAN_HOSTING.md) bagian C, lalu jalankan ulang.

## F. Memperbarui proyek setelah ini

```bash
git pull
cd backend && pytest && cd ..
cd frontend && npm test && cd ..
git add <berkas yang diubah>
git commit -m "jenis(bagian): ringkasan perubahan"
git push
```

Setiap push ke `main`: CI menjalankan test, Render men-deploy ulang backend, dan perubahan di folder `frontend` men-deploy ulang GitHub Pages.

Contoh pesan commit berikutnya:

| Perubahan | Pesan commit |
|---|---|
| Menambah format telemetri | `feat(backend): tambah adapter format scada-json` |
| Mengubah ambang status | `fix(backend): sesuaikan ambang beban kritis` |
| Mengubah tampilan | `feat(frontend): tambah filter gardu induk di halaman utama` |
| Memperbarui data demo setelah mengubah endpoint | `chore: perbarui openapi.json dan data demo` |
| Rilis versi baru | `docs: catat perubahan versi 1.1.0` |

Setelah mengubah endpoint atau data contoh, jalankan `python backend/tools/export_docs.py` supaya `docs/openapi.json` dan data demo frontend ikut terbarui.

## G. Masalah yang sering muncul

| Pesan | Penyebab | Solusi |
|---|---|---|
| `pathspec '...' did not match any files` | Nama berkas salah ketik atau folder belum diekstrak lengkap | Cek dengan `ls`, salin ulang perintah |
| `nothing to commit` di salah satu blok | Berkas sudah masuk commit sebelumnya | Lanjut ke blok berikutnya |
| `Author identity unknown` | Identitas Git belum diatur | Ulangi A nomor 2 |
| `remote origin already exists` | Remote pernah ditambahkan | `git remote set-url origin https://github.com/muhamadivan1/pantau-distribusi.git` |
| `failed to push some refs` | Repository GitHub terlanjur dibuat dengan README | Karena isinya hanya berkas bawaan GitHub, timpa: `git push -u origin main --force`. Pakai `--force` hanya untuk kasus ini |
| `node_modules` ikut terdaftar di `git status` | `.gitignore` tidak ikut tersalin | Pastikan berkas `.gitignore` ada di folder utama |
| Workflow CI gagal | Ada test yang gagal | Klik workflow yang merah, baca langkah yang gagal, perbaiki, commit, dan push lagi |

## H. Pembaruan ke versi 1.1.0 (integrasi Gerbang Telemetri)

Versi 1.1.0 menambah pengaturan `DEMO_SIMULATED_FEEDERS`, supaya PYL-04 dan PYL-05 bisa dipasok oleh [Gerbang Telemetri](https://github.com/muhamadivan1/gerbang-telemetri) tanpa data dobel.

**Bila belum pernah push sama sekali**, abaikan bagian ini. Berkas di zip sudah versi 1.1.0, jadi 18 commit di bagian D sudah memuat perubahannya.

**Bila versi 1.0.0 sudah ada di GitHub**, lakukan langkah berikut.

1. Ekstrak zip versi baru ke folder sementara, lalu salin berkas berikut ke folder proyek Anda dan timpa yang lama. Jangan menyalin folder `.git`.

    | Berkas | Perubahan |
    |---|---|
    | `backend/app/config.py` | pengaturan baru `demo_simulated_feeders` |
    | `backend/app/main.py` | simulator hanya membuat penyulang yang dipilih, versi 1.1.0 |
    | `backend/app/adapters/modbus.py` | keterangan hubungan dengan gateway |
    | `backend/.env.example` | contoh `DEMO_SIMULATED_FEEDERS` |
    | `backend/tests/test_simulator.py` | test baru |
    | `docs/openapi.json`, `frontend/src/api/demo-data.json` | dibuat ulang dengan `export_docs.py` |
    | `README.md`, `CHANGELOG.md`, `PANDUAN_HOSTING.md`, `PANDUAN_GITHUB.md`, `docs/PANDUAN_MENJALANKAN.md`, `docs/TEST_PLAN.md` | dokumentasi |

2. Pastikan test lulus:

    ```bash
    cd backend && pytest && cd ..
    cd frontend && npm test && cd ..
    ```

3. Tiga commit:

    ```bash
    git add backend/app/config.py backend/app/main.py backend/app/adapters/modbus.py backend/.env.example backend/tests/test_simulator.py
    git commit -m "feat(backend): DEMO_SIMULATED_FEEDERS untuk berbagi data dengan gateway"
    ```

    ```bash
    git add docs/openapi.json frontend/src/api/demo-data.json
    git commit -m "chore: perbarui openapi.json dan data demo ke versi 1.1.0"
    ```

    ```bash
    git add README.md CHANGELOG.md PANDUAN_HOSTING.md PANDUAN_GITHUB.md docs/PANDUAN_MENJALANKAN.md docs/TEST_PLAN.md
    git commit -m "docs: catat integrasi Gerbang Telemetri dan rilis 1.1.0"
    ```

4. Periksa, push, dan tandai versi:

    ```bash
    git status
    git push
    git tag -a v1.1.0 -m "Pantau Distribusi v1.1.0"
    git push origin v1.1.0
    ```

    `git status` harus `nothing to commit, working tree clean` sebelum push.

5. Render men-deploy ulang backend otomatis. Tambahkan `DEMO_SIMULATED_FEEDERS` di tab Environment Render hanya bila Gerbang Telemetri sudah dihosting. Tanpa variabel itu, perilaku Pantau sama persis dengan versi 1.0.0.

