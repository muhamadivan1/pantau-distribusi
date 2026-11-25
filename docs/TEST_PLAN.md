# Rencana dan Kasus Uji

Pengujian dilakukan di tiga lapis:

| Lapis | Alat | Jumlah | Cara menjalankan |
|---|---|---|---|
| Test backend | pytest | 39 | `cd backend && pytest` |
| Test frontend | Vitest | 14 | `cd frontend && npm test` |
| Uji manual | Browser di laptop dan HP | 16 | Tabel bagian 4 |

Test otomatis juga berjalan di GitHub Actions setiap push (`.github/workflows/ci.yml`). Setiap test backend memakai database SQLite baru di folder sementara, sehingga hasilnya tidak saling memengaruhi.

## 1. Kapan menguji

| Kejadian | Yang dijalankan |
|---|---|
| Sebelum setiap commit | `pytest` dan `npm test` |
| Mengubah tampilan | Tambah uji manual UM-01 sampai UM-16 |
| Setelah deploy | UM-01, UM-13, UM-14 di alamat online |

## 2. Test backend (38)

| ID | Berkas | Yang diuji |
|---|---|---|
| TB-01 | test_adapters | Registry memilih adapter dari isi payload, payload asing menghasilkan None |
| TB-02 | test_adapters | Tiga format dengan nilai yang sama menghasilkan rekaman kanonik yang identik, waktu WIB diubah ke UTC |
| TB-03 | test_adapters | RTU: titik ukur tidak lengkap dan IOA tidak terdaftar ditolak |
| TB-04 | test_adapters | RTU: timestamp rusak menimbulkan galat |
| TB-05 | test_adapters | Modbus: faktor skala diterapkan |
| TB-06 | test_adapters | Modbus: register kurang menimbulkan galat |
| TB-07 | test_adapters | CSV: angka ribuan dan desimal koma terbaca |
| TB-08 | test_adapters | CSV: baris rusak ditolak, baris lain tetap terbaca |
| TB-09 | test_adapters | CSV: header salah menimbulkan galat |
| TB-10 | test_ingestion | Data tersimpan, kiriman ulang dihitung duplikat |
| TB-11 | test_ingestion | Nilai di luar rentang ditolak dengan alasan |
| TB-12 | test_ingestion | Penyulang tidak terdaftar ditolak |
| TB-13 | test_ingestion | Waktu masa depan ditolak |
| TB-14 | test_ingestion | Beban 85% membuat alarm waspada, 97,5% menutupnya dan membuat alarm kritis, beban normal menutup semua |
| TB-15 | test_ingestion | Tegangan hilang membuka gangguan otomatis dengan jumlah pelanggan penyulang, tegangan kembali menutupnya |
| TB-16 | test_ingestion | Data susulan disimpan tetapi tidak membuat alarm |
| TB-17 | test_ingestion | Format tidak dikenal menimbulkan galat |
| TB-18 | test_reliability | SAIDI 18,75, SAIFI 0,375, CAIDI 50 sesuai hitungan manual, gangguan 3 menit tidak dihitung |
| TB-19 | test_reliability | Gangguan yang melewati awal periode dipotong |
| TB-20 | test_reliability | Gangguan belum pulih dihitung sampai sekarang |
| TB-21 | test_reliability | Tanpa gangguan, semua indeks nol dan CAIDI kosong |
| TB-22 | test_simulator | Simulator menghasilkan empat payload dalam tiga format |
| TB-23 | test_simulator | Payload simulator lolos ingest tanpa penolakan |
| TB-24 | test_simulator | Seed yang sama menghasilkan payload yang sama |
| TB-25 | test_simulator | Profil beban malam lebih tinggi dari dini hari |
| TB-26 | test_api | `/health` menjawab |
| TB-27 | test_api | Telemetri tanpa atau dengan API key salah ditolak 401 |
| TB-28 | test_api | Format asing ditolak 422 |
| TB-29 | test_api | Telemetri tersimpan, status penyulang menjadi kritis, waktu dikirim berakhiran Z |
| TB-30 | test_api | Penyulang tanpa data berstatus `tanpa_data`, penyulang asing 404 |
| TB-31 | test_api | Alarm hanya bisa dikonfirmasi sekali |
| TB-32 | test_api | Gangguan manual tercatat, gangguan ganda 409, penyebab dan waktu pulih bisa dilengkapi |
| TB-33 | test_api | Waktu pulih sebelum waktu mulai ditolak 422 |
| TB-34 | test_api | Penyebab tidak dikenal ditolak 422 |
| TB-35 | test_api | Laporan keandalan dan ringkasan shift memakai gangguan yang dicatat |
| TB-36 | test_api | Rentang keandalan terbalik ditolak 422 |
| TB-37 | test_simulator | `DEMO_SIMULATED_FEEDERS` membatasi penyulang simulator dan tidak lagi menghasilkan payload modbus (v1.1) |
| TB-37 | test_api | Dokumen OpenAPI memuat semua endpoint |
| TB-38 | test_api | Ringkasan shift tanpa kejadian berjudul "berjalan normal" |

## 3. Test frontend (14)

| ID | Berkas | Yang diuji |
|---|---|---|
| TF-01 | format.test | Waktu UTC ditampilkan dalam WIB |
| TF-02 | format.test | Angka memakai titik ribuan dan koma desimal |
| TF-03 | format.test | Lama gangguan ditulis dalam jam dan menit |
| TF-04 | format.test | Selisih waktu ditulis "3 menit lalu" |
| TF-05 | format.test | Isian waktu WIB bolak-balik ke ISO UTC tanpa bergeser |
| TF-06 | status.test | Status tidak dikenal dianggap tanpa data |
| TF-07 | status.test | Penyulang dihitung per status |
| TF-08 | status.test | Penyulang dikelompokkan per gardu induk |
| TF-09 | status.test | Batang beban dibatasi 0 sampai 110% |
| TF-10 | report.test | Teks serah terima berisi judul, ringkasan, dan butir catatan |
| TF-11 | demo.test | Kolom waktu digeser, kolom lain tetap |
| TF-12 | demo.test | Data demo tampil seolah baru diukur |
| TF-13 | demo.test | Konfirmasi alarm di mode demo tidak tertimpa |
| TF-14 | demo.test | Gangguan baru di mode demo memakai jumlah pelanggan penyulang |

Test frontend sudah dicoba di zona waktu UTC dan Asia/Jakarta dengan hasil yang sama.

## 4. Uji manual

Siapkan backend dan frontend seperti di [PANDUAN_MENJALANKAN.md](PANDUAN_MENJALANKAN.md). Untuk UM-02 sampai UM-04, kirim telemetri dengan `python tools/simulate.py --trip PYL-02`.

| ID | Skenario | Langkah | Hasil yang diharapkan |
|---|---|---|---|
| UM-01 | Halaman terbuka | Buka frontend | Dua gardu induk dengan tiga penyulang masing-masing, tanda "Terhubung ke server" |
| UM-02 | Penyulang padam | Jalankan simulator dengan `--trip PYL-02` | Kartu PYL-02 berwarna magenta, pemutus digambar kosong, garis putus-putus |
| UM-03 | Alarm padam | Buka Alarm | Alarm padam PYL-02 di urutan atas |
| UM-04 | Gangguan otomatis | Buka Gangguan | Gangguan PYL-02 bertanda "otomatis", lalu tertutup setelah enam langkah simulator |
| UM-05 | Konfirmasi tanpa nama | Kosongkan nama operator, klik Konfirmasi | Pesan "Isi nama operator dulu" |
| UM-06 | Konfirmasi alarm | Isi nama, klik Konfirmasi | Nama dan waktu konfirmasi tampil, tombol hilang |
| UM-07 | Lengkapi gangguan | Klik Lengkapi, pilih penyebab, simpan | Penyebab berubah |
| UM-08 | Catat gangguan manual | Klik Catat gangguan, simpan | Gangguan baru di atas daftar |
| UM-09 | Gangguan ganda | Catat lagi untuk penyulang yang sama | Pesan "masih punya gangguan yang belum pulih" |
| UM-10 | Detail penyulang | Klik satu kartu | Lima angka, grafik 24 jam dengan dua garis ambang, riwayat gangguan |
| UM-11 | Keandalan | Buka Keandalan, ganti 7, 30, 90 hari | Angka SAIDI, SAIFI, CAIDI dan dua grafik berubah |
| UM-12 | Serah terima | Buka Serah terima, klik Salin teks | Tombol berubah "Teks tersalin", teks bisa ditempel |
| UM-13 | Mode demo | Matikan backend, muat ulang frontend | Setelah sekitar 8 detik tampil "Mode demo" dan data contoh |
| UM-14 | Kembali live | Nyalakan backend lagi, tunggu | Dalam 20 detik berpindah ke "Terhubung ke server" |
| UM-15 | Tampilan HP | Lebar 390 px | Dua kartu per baris, tidak ada gulir ke samping |
| UM-16 | Dokumentasi API | Buka `/docs` di backend | Semua endpoint tampil dengan contoh payload tiga format |

## 5. Hasil pengujian rilis 1.1

Rilis 1.1 menambah satu test (TB-37): pytest 39 lulus, 0 gagal. Uji end-to-end bersama Gerbang Telemetri dicatat di `docs/TEST_PLAN.md` repository gateway.

## 6. Hasil pengujian rilis 1.0

| Lapis | Hasil |
|---|---|
| pytest | 38 lulus, 0 gagal |
| Vitest | 14 lulus, 0 gagal |
| Build frontend | Berhasil, halaman awal 363 kB (99 kB gzip) |
| Uji browser otomatis (Playwright) | UM-01, UM-05 sampai UM-13, UM-15 lulus pada lebar 1440 px dan 390 px |
| Simulator HTTP | `--trip` membuka gangguan otomatis, kunci salah berhenti dengan pesan jelas |

## 6. Kriteria lulus rilis

- [ ] `pytest` dan `npm test` 0 gagal
- [ ] Workflow CI di GitHub bertanda centang hijau
- [ ] UM-01 sampai UM-16 sesuai harapan
- [ ] Demo online terbuka dan beralih ke mode live setelah backend bangun
