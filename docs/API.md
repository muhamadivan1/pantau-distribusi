# Dokumentasi API Pantau Distribusi

Base URL:

| Lingkungan | Alamat |
|---|---|
| Laptop | `http://127.0.0.1:8000/api/v1` |
| Hosting | `https://<nama-layanan>.onrender.com/api/v1` |

Dokumentasi interaktif (Swagger UI) tersedia di `/docs` dan ReDoc di `/redoc`. Spesifikasi lengkapnya ada di [openapi.json](openapi.json), yang bisa diimpor ke Postman (**Import > File**) atau dibuka di https://editor.swagger.io.

## Aturan umum

| Hal | Aturan |
|---|---|
| Format | JSON, `Content-Type: application/json` |
| Waktu | Dikirim dalam UTC berakhiran `Z`. Waktu tanpa zona dianggap UTC |
| Autentikasi | Hanya `POST /telemetry` yang wajib header `X-API-Key` |
| Galat | `{"detail": "pesan"}`. Galat validasi skema berbentuk daftar dari FastAPI |
| Angka | Titik sebagai pemisah desimal (standar JSON). Format CSV meter memakai koma |

## Daftar endpoint

| Metode | Path | Fungsi | Kode sukses |
|---|---|---|---|
| GET | `/health` | Cek server hidup | 200 |
| POST | `/telemetry` | Kirim telemetri (wajib `X-API-Key`) | 201 |
| GET | `/feeders` | Semua penyulang dengan status terkini | 200 |
| GET | `/feeders/{id}` | Detail satu penyulang | 200 |
| GET | `/feeders/{id}/measurements?hours=24` | Riwayat pengukuran, 1 sampai 168 jam | 200 |
| GET | `/alarms?status=open` | Alarm, `open` atau `all` | 200 |
| POST | `/alarms/{id}/acknowledge` | Konfirmasi alarm | 200 |
| GET | `/outages?status=all&feeder_id=` | Gangguan, `open`, `closed`, atau `all` | 200 |
| POST | `/outages` | Catat gangguan manual | 201 |
| PATCH | `/outages/{id}` | Perbarui penyebab, pelanggan, catatan, waktu pulih | 200 |
| GET | `/reliability?days=30` | SAIDI, SAIFI, CAIDI | 200 |
| GET | `/reports/shift-summary?hours=8` | Ringkasan serah terima shift | 200 |

---

## POST /telemetry

Menerima telemetri dalam salah satu dari tiga format. Format dikenali dari isi payload, jadi tidak ada parameter format.

**Header:** `X-API-Key: <kunci>`

### Format 1: rtu-ioa

Titik ukur dari RTU gardu induk. Satu payload bisa berisi beberapa penyulang. Penyulang ditentukan dari peta alamat IOA di `app/adapters/rtu_ioa.py`.

```json
{
  "rtu": "RTU-GI-DEMO-UTARA",
  "timestamp": "2026-11-25T08:00:00+07:00",
  "points": [
    {"ioa": 1001, "value": 245.3},
    {"ioa": 1002, "value": 20.1},
    {"ioa": 1003, "value": 7.69}
  ]
}
```

| IOA | Penyulang | Besaran |
|---|---|---|
| 1001, 1002, 1003 | PYL-01 | arus (A), tegangan (kV), daya (MW) |
| 1011, 1012, 1013 | PYL-02 | arus, tegangan, daya |
| 1021, 1022, 1023 | PYL-03 | arus, tegangan, daya |

### Format 2: modbus

Register dari IED satu penyulang. Nilai berupa bilangan bulat berskala, waktu berupa epoch detik (UTC).

```json
{
  "device": "IED-PYL-04",
  "feeder": "PYL-04",
  "ts_epoch": 1795568400,
  "registers": {"40001": 2453, "40002": 2010, "40003": 769}
}
```

| Register | Besaran | Faktor | Contoh |
|---|---|---|---|
| 40001 | Arus (A) | x 0,1 | 2453 menjadi 245,3 A |
| 40002 | Tegangan (kV) | x 0,01 | 2010 menjadi 20,10 kV |
| 40003 | Daya (MW) | x 0,01 | 769 menjadi 7,69 MW |

### Format 3: csv-meter

Teks CSV dengan pemisah titik koma, desimal koma, dan waktu WIB.

```json
{
  "content": "penyulang;waktu;arus_a;tegangan_kv;daya_mw\nPYL-06;25/11/2026 08:00:00;210,50;20,10;6,59"
}
```

### Respons 201

```json
{
  "adapter": "modbus",
  "received": 1,
  "stored": 1,
  "duplicates": 0,
  "rejected": [],
  "alarms_raised": 1,
  "outages_opened": 0,
  "outages_closed": 0,
  "processing_ms": 5.47
}
```

Rekaman yang ditolak tidak menggagalkan rekaman lain. Contoh payload CSV dengan dua baris bermasalah:

```json
{
  "adapter": "csv-meter",
  "received": 2,
  "stored": 0,
  "duplicates": 0,
  "rejected": [
    {"feeder_id": "PYL-06", "reasons": ["current_a=1250.0 di luar rentang 0.0-1000.0"]},
    {"feeder_id": "PYL-09", "reasons": ["penyulang PYL-09 tidak terdaftar"]}
  ],
  "alarms_raised": 0,
  "outages_opened": 0,
  "outages_closed": 0,
  "processing_ms": 1.01
}
```

### Aturan validasi

| Isian | Rentang diterima |
|---|---|
| `current_a` | 0 sampai 1.000 A |
| `voltage_kv` | 0 sampai 24 kV |
| `power_mw` | 0 sampai 30 MW |
| `measured_at` | Paling lambat 5 menit setelah waktu server |
| Penyulang | Harus terdaftar di tabel `feeders` |
| Duplikat | Penyulang, waktu, dan ketiga nilai sama persis dengan rekaman yang sudah ada |

### Galat

| Kode | Kapan | Contoh `detail` |
|---|---|---|
| 401 | `X-API-Key` tidak ada atau salah | `X-API-Key tidak ada atau salah` |
| 422 | Format tidak dikenali | `format tidak dikenali. Format yang didukung: rtu-ioa, modbus, csv-meter` |
| 422 | Format dikenali tapi tidak bisa dibaca | `ts_epoch tidak valid: 'kemarin'` |

---

## GET /feeders dan GET /feeders/{id}

```json
{
  "id": "PYL-04",
  "name": "Melati",
  "substation": "GI Demo Selatan",
  "area": "Kota Selatan",
  "capacity_a": 400.0,
  "customers": 7600,
  "status": "waspada",
  "load_pct": 86.2,
  "latest": {
    "measured_at": "2026-11-25T07:03:00Z",
    "current_a": 345.0,
    "voltage_kv": 20.04,
    "power_mw": 10.77,
    "source_format": "modbus"
  }
}
```

`status` bernilai `normal`, `waspada`, `kritis`, `padam`, atau `tanpa_data`. Penyulang tanpa pengukuran punya `latest: null` dan `load_pct: null`. Penyulang yang tidak ada menghasilkan 404.

## GET /feeders/{id}/measurements

Parameter `hours` (1 sampai 168, bawaan 24). Hasil diurutkan dari yang terlama.

```json
[
  {"measured_at": "2026-11-25T06:15:00Z", "current_a": 220.2, "voltage_kv": 20.12, "power_mw": 6.91, "source_format": "modbus"},
  {"measured_at": "2026-11-25T06:30:00Z", "current_a": 213.4, "voltage_kv": 20.18, "power_mw": 6.71, "source_format": "modbus"}
]
```

---

## GET /alarms

Parameter `status` (`open` atau `all`, bawaan `open`) dan `limit` (1 sampai 500). Terbaru di atas.

```json
{
  "id": 10,
  "feeder_id": "PYL-04",
  "level": "waspada",
  "message": "Beban Melati 86% dari kapasitas, mendekati batas",
  "load_pct": 86.2,
  "raised_at": "2026-11-25T07:03:00Z",
  "acknowledged_at": null,
  "acknowledged_by": null,
  "cleared_at": null
}
```

## POST /alarms/{id}/acknowledge

```json
{"by": "Operator Pagi"}
```

Respons berisi alarm dengan `acknowledged_at` dan `acknowledged_by` terisi. Konfirmasi kedua tidak menimpa yang pertama. Nama harus 2 sampai 80 karakter (422 jika tidak).

---

## GET /outages

Parameter `status` (`open`, `closed`, `all`), `feeder_id`, dan `limit` (1 sampai 1.000).

## POST /outages

```json
{
  "feeder_id": "PYL-03",
  "started_at": "2026-11-25T01:15:00Z",
  "cause": "pohon",
  "notes": "Ranting menyentuh jaringan"
}
```

| Isian | Wajib | Keterangan |
|---|---|---|
| `feeder_id` | Ya | |
| `started_at` | Ya | |
| `restored_at` | Tidak | Kosong berarti belum pulih |
| `cause` | Tidak | `pohon`, `hewan`, `peralatan`, `cuaca`, `pihak_ketiga`, `pemeliharaan`, `belum_diketahui` (bawaan) |
| `customers_affected` | Tidak | Kosong berarti seluruh pelanggan penyulang |
| `notes` | Tidak | |

Respons 201:

```json
{
  "id": 31,
  "feeder_id": "PYL-03",
  "started_at": "2026-11-25T01:15:00Z",
  "restored_at": null,
  "cause": "pohon",
  "customers_affected": 1450,
  "notes": "Ranting menyentuh jaringan",
  "auto_detected": false,
  "duration_minutes": null
}
```

| Kode | Kapan |
|---|---|
| 404 | Penyulang tidak ada |
| 409 | Penyulang masih punya gangguan yang belum pulih |
| 422 | `restored_at` tidak setelah `started_at`, atau penyebab tidak dikenal |

## PATCH /outages/{id}

Kirim hanya isian yang ingin diubah.

```json
{"restored_at": "2026-11-25T02:05:00Z"}
```

Respons berisi gangguan lengkap dengan `duration_minutes` terhitung (contoh: `50.0`).

---

## GET /reliability

Parameter `days` (1 sampai 366, bawaan 30), atau `start` dan `end` dalam ISO 8601.

```json
{
  "start": "2026-10-26T07:03:33Z",
  "end": "2026-11-25T07:03:33Z",
  "customers_served": 42000,
  "sustained_threshold_minutes": 5.0,
  "interruptions": 12,
  "saidi_minutes": 123.28,
  "saifi": 1.7008,
  "caidi_minutes": 72.48,
  "by_feeder": [
    {"key": "PYL-01", "label": "PYL-01 Cempaka", "interruptions": 3, "customers_interrupted": 19270, "customer_minutes": 1956110.0}
  ],
  "by_cause": [
    {"key": "pohon", "label": "Pohon atau ranting", "interruptions": 5, "customers_interrupted": 23742, "customer_minutes": 3454224.0}
  ]
}
```

Rumus dan penyederhanaannya dijelaskan di [ARCHITECTURE.md](ARCHITECTURE.md) bagian 6. `caidi_minutes` bernilai `null` jika tidak ada gangguan. `start` setelah `end` menghasilkan 422.

## GET /reports/shift-summary

Parameter `hours` (1 sampai 24, bawaan 8).

```json
{
  "start": "2026-11-24T23:03:33Z",
  "end": "2026-11-25T07:03:33Z",
  "headline": "Ada gangguan selama shift, semuanya sudah pulih.",
  "lines": [
    "PYL-03 padam 50 menit dan pulih pukul 09:05 WIB.",
    "Beban tertinggi saat ini di PYL-04 Melati: 86% dari kapasitas."
  ],
  "counts": {
    "alarm_waspada": 1,
    "alarm_kritis": 0,
    "alarm_padam": 0,
    "alarm_belum_dikonfirmasi": 0,
    "gangguan_baru": 1,
    "gangguan_pulih": 1,
    "gangguan_masih_terbuka": 0
  }
}
```

## Contoh memanggil dengan curl

```bash
# Kirim telemetri Modbus
curl -X POST http://127.0.0.1:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-ganti-saya" \
  -d '{"device":"IED-PYL-04","feeder":"PYL-04","ts_epoch":1795568400,"registers":{"40001":3450,"40002":2004,"40003":1077}}'

# Lihat status semua penyulang
curl http://127.0.0.1:8000/api/v1/feeders

# Indeks keandalan 90 hari
curl "http://127.0.0.1:8000/api/v1/reliability?days=90"
```

Contoh `ts_epoch` di atas adalah 25 November 2026 pukul 08.00 WIB. Untuk waktu sekarang, jalankan `python -c "import time; print(int(time.time()))"`.
