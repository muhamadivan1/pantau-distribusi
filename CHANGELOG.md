# Catatan Perubahan

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/). Versi terbaru di paling atas.

## [1.1.0] - 2026-11-25

### Ditambahkan
- Pengaturan `DEMO_SIMULATED_FEEDERS` untuk memilih penyulang yang dibuat simulator internal. Dipakai saat PYL-04 dan PYL-05 dipasok Gerbang Telemetri, supaya datanya tidak datang dari dua sumber
- Test `test_simulated_feeders_bisa_dibatasi` (39 test pytest)

### Diubah
- Versi API menjadi 1.1.0
- Keterangan adapter `modbus` menjelaskan bahwa pembacaan protokol Modbus dilakukan gateway, sedangkan API menerima hasilnya dalam JSON

## [1.0.0] - 2026-11-25

### Ditambahkan

**Backend**
- Endpoint `POST /api/v1/telemetry` dengan API key, menerima format `rtu-ioa`, `modbus`, dan `csv-meter` yang dikenali dari isi payload
- Adapter dan Canonical Data Model, registry adapter
- Validasi rentang nilai, penolakan waktu masa depan, deduplikasi SHA-256, penanganan data susulan
- Status penyulang (normal, waspada, kritis, padam, tanpa data) dengan ambang yang bisa diatur
- Alarm bertingkat dengan konfirmasi operator
- Gangguan otomatis dari telemetri, pencatatan dan pembaruan gangguan manual
- SAIDI, SAIFI, CAIDI sesuai definisi IEEE Std 1366, rincian per penyulang dan penyebab
- Ringkasan serah terima shift berbasis aturan
- Simulator telemetri tiga format, data contoh fiktif, skrip gateway tiruan
- 38 test pytest

**Frontend**
- Halaman kondisi jaringan dengan diagram busbar per gardu induk
- Detail penyulang dengan grafik arus 24 jam dan garis ambang
- Halaman alarm, gangguan, keandalan, dan serah terima shift
- Mode demo otomatis saat backend tidak menjawab, beralih ke live saat backend siap
- Tampilan responsif sampai lebar 390 px
- 14 test Vitest

**Deploy dan dokumentasi**
- GitHub Actions untuk test dan deploy GitHub Pages, blueprint Render
- README, PRD, arsitektur, UML, BPMN (3 proses), dokumentasi API dan OpenAPI, model data, rencana uji
- Panduan menjalankan, panduan GitHub, dan panduan hosting
