# Model Data Pantau Distribusi

Database menyimpan empat tabel. Semua waktu disimpan dalam UTC tanpa zona, lalu API menempelkan zona UTC saat mengirim. Definisinya ada di `backend/app/models.py`.

## 1. Entity Relationship Diagram

```mermaid
erDiagram
    FEEDERS ||--o{ MEASUREMENTS : "diukur"
    FEEDERS ||--o{ ALARMS : "memicu"
    FEEDERS ||--o{ OUTAGES : "mengalami"

    FEEDERS {
        string id PK "contoh PYL-01"
        string name
        string substation "gardu induk"
        string area
        float capacity_a "arus yang dianggap 100 persen"
        int customers "jumlah pelanggan dilayani"
    }
    MEASUREMENTS {
        int id PK
        string feeder_id FK
        datetime measured_at "UTC"
        float current_a
        float voltage_kv
        float power_mw
        string source_format "rtu-ioa, modbus, csv-meter"
        string record_hash UK "SHA-256"
    }
    ALARMS {
        int id PK
        string feeder_id FK
        string level "waspada, kritis, padam"
        string message
        float load_pct "kosong untuk padam"
        datetime raised_at
        datetime acknowledged_at "kosong jika belum"
        string acknowledged_by
        datetime cleared_at "kosong jika masih aktif"
    }
    OUTAGES {
        int id PK
        string feeder_id FK
        datetime started_at
        datetime restored_at "kosong jika belum pulih"
        string cause
        int customers_affected
        text notes
        bool auto_detected
    }
```

## 2. Kamus data

### feeders

| Kolom | Tipe | Wajib | Keterangan | Contoh |
|---|---|---|---|---|
| `id` | teks (20) | Ya | Kode penyulang, kunci utama | `PYL-05` |
| `name` | teks (80) | Ya | Nama penyulang | `Anggrek` |
| `substation` | teks (80) | Ya | Gardu induk asal | `GI Demo Selatan` |
| `area` | teks (80) | Ya | Wilayah layanan | `Kota Selatan` |
| `capacity_a` | desimal | Ya | Batas arus untuk menghitung persen beban | `400` |
| `customers` | bilangan bulat | Ya | Jumlah pelanggan, dipakai sebagai N di SAIDI dan SAIFI | `10350` |

### measurements

| Kolom | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `id` | bilangan bulat | Ya | Kunci utama, otomatis |
| `feeder_id` | teks | Ya | Kunci asing ke `feeders.id`, berindeks |
| `measured_at` | waktu | Ya | Waktu pengukuran (UTC), berindeks |
| `current_a` | desimal | Ya | Arus, 0 sampai 1.000 A |
| `voltage_kv` | desimal | Ya | Tegangan, 0 sampai 24 kV |
| `power_mw` | desimal | Ya | Daya aktif, 0 sampai 30 MW |
| `source_format` | teks (20) | Ya | Adapter yang membaca rekaman ini |
| `record_hash` | teks (64) | Ya | SHA-256 dari penyulang, waktu, dan nilai. Unik, mencegah duplikat |

### alarms

| Kolom | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `id` | bilangan bulat | Ya | Kunci utama |
| `feeder_id` | teks | Ya | Kunci asing |
| `level` | teks | Ya | `waspada`, `kritis`, atau `padam` |
| `message` | teks (200) | Ya | Kalimat untuk operator |
| `load_pct` | desimal | Tidak | Persen beban saat alarm dibuat |
| `raised_at` | waktu | Ya | Waktu alarm dibuat (sama dengan waktu pengukuran pemicunya) |
| `acknowledged_at` | waktu | Tidak | Waktu dikonfirmasi |
| `acknowledged_by` | teks (80) | Tidak | Nama operator |
| `cleared_at` | waktu | Tidak | Waktu alarm selesai. Kosong berarti masih aktif |

### outages

| Kolom | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `id` | bilangan bulat | Ya | Kunci utama |
| `feeder_id` | teks | Ya | Kunci asing |
| `started_at` | waktu | Ya | Mulai padam |
| `restored_at` | waktu | Tidak | Pulih. Kosong berarti masih padam |
| `cause` | teks (30) | Ya | Salah satu kode penyebab di bawah |
| `customers_affected` | bilangan bulat | Ya | Pelanggan terdampak, bisa lebih kecil dari pelanggan penyulang setelah manuver |
| `notes` | teks | Ya | Catatan bebas, boleh kosong |
| `auto_detected` | boolean | Ya | `true` jika dibuka dari telemetri |

### Kode penyebab gangguan

| Kode | Label |
|---|---|
| `pohon` | Pohon atau ranting |
| `hewan` | Hewan |
| `peralatan` | Kerusakan peralatan |
| `cuaca` | Cuaca |
| `pihak_ketiga` | Pihak ketiga |
| `pemeliharaan` | Pemeliharaan terencana |
| `belum_diketahui` | Belum diketahui |

## 3. Bentuk kanonik

Bukan tabel, tetapi kontrak antara adapter dan inti sistem (`CanonicalMeasurement` di `app/schemas.py`):

| Isian | Tipe | Aturan |
|---|---|---|
| `feeder_id` | teks | Kode penyulang |
| `measured_at` | waktu | Selalu UTC |
| `current_a` | desimal | Ampere |
| `voltage_kv` | desimal | Kilovolt |
| `power_mw` | desimal | Megawatt |
| `source_format` | teks | Nama adapter |

## 4. Data contoh

Mode demo mengisi data fiktif berikut (`app/seed.py`):

| Penyulang | Nama | Gardu induk | Kapasitas | Pelanggan | Sumber data |
|---|---|---|---|---|---|
| PYL-01 | Cempaka | GI Demo Utara | 400 A | 8.200 | rtu-ioa |
| PYL-02 | Dahlia | GI Demo Utara | 400 A | 9.100 | rtu-ioa |
| PYL-03 | Kenanga | GI Demo Utara | 630 A | 1.450 | rtu-ioa |
| PYL-04 | Melati | GI Demo Selatan | 400 A | 7.600 | modbus |
| PYL-05 | Anggrek | GI Demo Selatan | 400 A | 10.350 | modbus |
| PYL-06 | Teratai | GI Demo Selatan | 300 A | 5.300 | csv-meter |

Ditambah telemetri 24 jam terakhir setiap 15 menit dan 28 gangguan acak dalam 90 hari terakhir.

## 5. Pindah ke PostgreSQL

Kode tidak perlu diubah. Pasang driver lalu ganti `DATABASE_URL`:

```bash
pip install "psycopg[binary]"
DATABASE_URL=postgresql+psycopg://user:password@host:5432/pantau
```

Tabel dibuat otomatis saat aplikasi start. Untuk perubahan skema di masa depan, sebaiknya tambahkan Alembic untuk migrasi.
