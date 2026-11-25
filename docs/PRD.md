# Product Requirements Document (PRD): Pantau Distribusi

| | |
|---|---|
| Produk | Pantau Distribusi, dashboard pemantauan penyulang 20 kV |
| Versi dokumen | 1.0 |
| Pemilik produk | Muhamad Ivan Fadilah |
| Status | Rilis pertama (MVP) selesai |
| Sifat | Proyek portofolio dengan data fiktif |

## 1. Latar belakang

Jaringan distribusi 20 kV terdiri dari banyak penyulang yang keluar dari gardu induk. Pusat pengatur distribusi memantau beban dan kondisi penyulang lewat sistem SCADA, lalu mengoordinasikan pemulihan saat terjadi gangguan. Kinerjanya diukur antara lain dengan indeks keandalan SAIDI dan SAIFI per penyulang.

Ada empat masalah yang dijawab produk ini:

1. **Data heterogen.** RTU di gardu induk, relai atau meter digital di penyulang, dan sistem pembacaan meter mengirim data dengan struktur, satuan, dan format waktu berbeda. Integrasi titik ke titik membuat logika yang sama ditulis berulang.
2. **Beban lebih terlambat diketahui.** Operator butuh tanda yang jelas saat penyulang mendekati atau melewati batas kapasitas.
3. **Catatan gangguan tidak lengkap.** Waktu padam, waktu pulih, jumlah pelanggan terdampak, dan penyebab adalah bahan utama perhitungan keandalan. Jika dicatat manual dan terpisah, hasilnya rawan salah.
4. **Serah terima shift tidak terstruktur.** Gangguan yang masih terbuka atau alarm yang belum dikonfirmasi bisa terlewat saat pergantian shift.

## 2. Tujuan dan ukuran keberhasilan

| Tujuan | Ukuran keberhasilan |
|---|---|
| Satu pintu masuk untuk semua format | Tiga format diterima di satu endpoint tanpa kode khusus di luar adapter |
| Data yang tersimpan bisa dipercaya | Nilai di luar rentang, waktu masa depan, dan data ganda ditolak, dan semua penolakan dilaporkan beserta alasannya |
| Kondisi semua penyulang terlihat sekilas | Status setiap penyulang tampil di satu layar dan diperbarui setiap 5 detik |
| Gangguan tercatat tanpa ketik ulang | Gangguan terbuka dan tertutup otomatis dari telemetri |
| Indeks keandalan bisa ditelusuri | SAIDI, SAIFI, CAIDI dihitung sesuai definisi IEEE Std 1366 dan diuji dengan contoh hitungan manual |
| Mudah dijalankan dan dinilai | Bisa dijalankan dengan perintah di README, demo online bisa dibuka tanpa login |

**Di luar cakupan versi ini:** pembacaan protokol SCADA sungguhan, kendali jarak jauh (membuka atau menutup pemutus), login dan pembagian peran, peta jaringan geografis, pemisahan major event day, dan aplikasi mobile.

## 3. Pengguna sasaran

| Persona | Kebutuhan |
|---|---|
| **Operator ruang kendali** (dispatcher) | Melihat kondisi semua penyulang, tahu lebih awal saat beban mendekati batas, mencatat dan melengkapi gangguan, menyerahkan shift dengan rapi |
| **Analis keandalan** | Mendapat SAIDI, SAIFI, CAIDI per periode, mengetahui penyulang dan penyebab yang paling berpengaruh |
| **Gateway atau sistem lain** | Mengirim telemetri ke satu endpoint dan mendapat laporan hasil yang jelas |

## 4. User story

| ID | Sebagai | Saya ingin | Supaya |
|---|---|---|---|
| US-01 | gateway | mengirim telemetri dalam format asli saya | tidak perlu mengubah format di sisi perangkat |
| US-02 | gateway | menerima laporan rekaman yang ditolak beserta alasannya | masalah data bisa diperbaiki di sumbernya |
| US-03 | operator | melihat beban semua penyulang dikelompokkan per gardu induk | memahami kondisi jaringan sekilas |
| US-04 | operator | mendapat alarm saat beban melewati ambang atau penyulang padam | bisa bertindak sebelum gangguan meluas |
| US-05 | operator | mengonfirmasi alarm dengan nama saya | jelas siapa yang sudah menangani |
| US-06 | operator | gangguan tercatat otomatis saat tegangan hilang dan pulih | tidak perlu mengetik ulang waktu padam |
| US-07 | operator | melengkapi penyebab gangguan atau mencatat gangguan manual | data keandalan lengkap |
| US-08 | operator | melihat grafik arus 24 jam satu penyulang dengan garis ambang | mengenali pola beban puncak |
| US-09 | analis | melihat SAIDI, SAIFI, CAIDI untuk 7, 30, atau 90 hari | memantau tren keandalan |
| US-10 | analis | melihat rincian per penyulang dan per penyebab | menentukan prioritas perbaikan |
| US-11 | operator | mendapat ringkasan shift yang bisa disalin | serah terima tidak bergantung pada ingatan |
| US-12 | perekrut atau penguji | mencoba aplikasi tanpa memasang apa pun | menilai hasil kerja dengan cepat |

## 5. Kebutuhan fungsional

| ID | Kebutuhan | Prioritas | User story |
|---|---|---|---|
| FR-01 | `POST /api/v1/telemetry` menerima format `rtu-ioa`, `modbus`, dan `csv-meter`, dikenali dari isi payload | Wajib | US-01 |
| FR-02 | Endpoint telemetri menolak permintaan tanpa header `X-API-Key` yang benar (401) | Wajib | US-01 |
| FR-03 | Payload yang formatnya tidak dikenali ditolak (422) dengan daftar format yang didukung | Wajib | US-02 |
| FR-04 | Rekaman dengan penyulang tidak terdaftar, nilai di luar rentang, atau waktu masa depan ditolak per rekaman dengan alasan | Wajib | US-02 |
| FR-05 | Rekaman yang sama persis tidak disimpan dua kali | Wajib | US-01 |
| FR-06 | Status penyulang dihitung dari pengukuran terakhir: normal, waspada (≥80%), kritis (≥95%), padam (tegangan <2 kV), tanpa data | Wajib | US-03 |
| FR-07 | Perubahan status membuat atau menutup alarm, paling banyak satu alarm terbuka per penyulang | Wajib | US-04 |
| FR-08 | Alarm bisa dikonfirmasi satu kali dengan nama operator | Wajib | US-05 |
| FR-09 | Status padam membuka gangguan otomatis, status bukan padam menutupnya | Wajib | US-06 |
| FR-10 | Gangguan bisa dicatat manual, ditolak jika penyulang masih punya gangguan terbuka (409) atau waktu pulih sebelum waktu mulai (422) | Wajib | US-07 |
| FR-11 | Penyebab, jumlah pelanggan, catatan, dan waktu pulih gangguan bisa diperbarui | Wajib | US-07 |
| FR-12 | Riwayat pengukuran per penyulang tersedia untuk 1 sampai 168 jam | Wajib | US-08 |
| FR-13 | SAIDI, SAIFI, CAIDI dihitung untuk periode tertentu, hanya gangguan lebih dari 5 menit, dengan rincian per penyulang dan penyebab | Wajib | US-09, US-10 |
| FR-14 | Ringkasan shift 1 sampai 24 jam berisi kalimat dan hitungan | Wajib | US-11 |
| FR-15 | Frontend beralih ke mode demo jika backend tidak menjawab, dan kembali ke mode live saat backend siap | Wajib | US-12 |
| FR-16 | Mode demo menyediakan data contoh dan simulator agar demo selalu bergerak | Sebaiknya | US-12 |

## 6. Kebutuhan non-fungsional

| ID | Aspek | Kebutuhan |
|---|---|---|
| NFR-01 | Kinerja | Satu payload diproses di bawah 100 ms di laptop (dilaporkan di `processing_ms`) |
| NFR-02 | Keterbaruan | Dashboard memperbarui kondisi penyulang setiap 5 detik |
| NFR-03 | Keterluasan | Format baru cukup ditambah satu kelas adapter dan didaftarkan di registry |
| NFR-04 | Keamanan | API key untuk endpoint telemetri, CORS hanya untuk alamat frontend, teks ditampilkan lewat React (aman dari XSS) |
| NFR-05 | Ketertelusuran | Ringkasan shift dan indeks keandalan dihitung dengan aturan tetap yang bisa diperiksa, tanpa model AI |
| NFR-06 | Waktu | Database menyimpan UTC, API mengirim UTC berakhiran Z, tampilan memakai WIB |
| NFR-07 | Aksesibilitas | Status tidak hanya dibedakan dengan warna (selalu ada teks), bisa dipakai dengan keyboard |
| NFR-08 | Responsif | Tidak ada gulir mendatar di layar 390 px, kecuali tabel lebar yang bisa digeser |
| NFR-09 | Keterujian | Logika inti ditutup test otomatis dan dijalankan di CI setiap push |
| NFR-10 | Biaya | Bisa di-hosting gratis (Render free dan GitHub Pages) |

## 7. Risiko dan penanganan

| Risiko | Dampak | Penanganan |
|---|---|---|
| Server gratis tidur setelah 15 menit tanpa akses | Pengunjung pertama menunggu sekitar satu menit | Frontend langsung menampilkan mode demo dan beralih otomatis saat server siap |
| Disk server gratis tidak permanen | Data hilang saat server dinyalakan ulang | Mode demo mengisi ulang data contoh setiap start. Untuk data permanen, ganti `DATABASE_URL` ke PostgreSQL |
| Format perangkat berubah | Data ditolak | Penolakan dilaporkan per rekaman, adapter terisolasi sehingga perbaikan tidak menyentuh inti sistem |
| Jam perangkat tidak sinkron | Data dianggap dari masa depan | Toleransi 5 menit, sisanya ditolak dengan alasan jelas |
| Salah paham bahwa ini sistem resmi | Reputasi | Keterangan data fiktif dan tidak berafiliasi di README dan di aplikasi |

## 8. Rencana rilis

| Versi | Isi |
|---|---|
| 1.0 | Semua kebutuhan di dokumen ini |
| 1.1 | Login operator dan pencatatan siapa yang mengubah data gangguan |
| 1.2 | PostgreSQL di hosting, ekspor laporan keandalan ke Excel |
| 1.3 | Pemisahan major event day (TMED) sesuai IEEE Std 1366 |
