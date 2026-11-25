# Diagram UML Pantau Distribusi

Semua diagram ditulis dengan [Mermaid](https://mermaid.js.org) sehingga langsung tampil di GitHub dan mudah diubah.

## 1. Use Case Diagram

```mermaid
flowchart LR
    OP(["Operator ruang kendali"])
    AN(["Analis keandalan"])
    GW(["Gateway perangkat"])

    subgraph Sistem["Pantau Distribusi"]
        direction TB
        UC1(["Kirim telemetri"])
        UC2(["Validasi dan simpan pengukuran"])
        UC3(["Pantau kondisi penyulang"])
        UC4(["Lihat grafik beban penyulang"])
        UC5(["Konfirmasi alarm"])
        UC6(["Kelola gangguan"])
        UC7(["Lihat indeks keandalan"])
        UC8(["Susun ringkasan serah terima"])
        UC9(["Perbarui alarm dan gangguan otomatis"])
    end

    GW --- UC1
    OP --- UC3
    OP --- UC4
    OP --- UC5
    OP --- UC6
    OP --- UC8
    AN --- UC7

    UC1 -. include .-> UC2
    UC2 -. include .-> UC9
    UC3 -. extend .-> UC4
```

## 2. Class Diagram

Kelas utama di lapisan adapter, service, dan data.

```mermaid
classDiagram
    class TelemetryAdapter {
        <<abstract>>
        +name: str
        +supports(payload) bool
        +parse(payload) ParseResult
    }
    class RtuIoaAdapter {
        +IOA_MAP
    }
    class ModbusAdapter {
        +REGISTER_MAP
    }
    class CsvMeterAdapter {
        +HEADER
    }
    class AdapterRegistry {
        -adapters: list
        +resolve(payload) TelemetryAdapter
        +names: list
    }
    class ParseResult {
        +measurements: list
        +rejected: list
    }
    class CanonicalMeasurement {
        +feeder_id: str
        +measured_at: datetime
        +current_a: float
        +voltage_kv: float
        +power_mw: float
        +source_format: str
    }
    class IngestionService {
        +ingest(session, payload, settings) IngestResult
        +validate(m, feeder, now) list
        +record_hash(m) str
    }
    class StatusService {
        +classify(current, voltage, capacity, settings) tuple
        +load_percent(current, capacity) float
    }
    class EventService {
        +apply_status(session, feeder, status, pct, at) EventCounts
    }
    class ReliabilityService {
        +compute(session, start, end, now, settings) ReliabilityOut
    }
    class Feeder {
        +id: str
        +name: str
        +substation: str
        +capacity_a: float
        +customers: int
    }
    class Measurement {
        +feeder_id: str
        +measured_at: datetime
        +current_a: float
        +voltage_kv: float
        +power_mw: float
        +record_hash: str
    }
    class Alarm {
        +level: str
        +raised_at: datetime
        +acknowledged_by: str
        +cleared_at: datetime
    }
    class Outage {
        +started_at: datetime
        +restored_at: datetime
        +cause: str
        +customers_affected: int
        +auto_detected: bool
    }

    TelemetryAdapter <|-- RtuIoaAdapter
    TelemetryAdapter <|-- ModbusAdapter
    TelemetryAdapter <|-- CsvMeterAdapter
    AdapterRegistry o-- TelemetryAdapter
    TelemetryAdapter ..> ParseResult : menghasilkan
    ParseResult o-- CanonicalMeasurement
    IngestionService ..> AdapterRegistry : memakai
    IngestionService ..> StatusService : memakai
    IngestionService ..> EventService : memakai
    IngestionService ..> Measurement : menyimpan
    EventService ..> Alarm : membuka dan menutup
    EventService ..> Outage : membuka dan menutup
    ReliabilityService ..> Outage : membaca
    Feeder "1" -- "*" Measurement
    Feeder "1" -- "*" Alarm
    Feeder "1" -- "*" Outage
```

## 3. Sequence Diagram: ingest telemetri

```mermaid
sequenceDiagram
    participant G as Gateway
    participant R as Router /telemetry
    participant I as ingest()
    participant AR as AdapterRegistry
    participant AD as Adapter
    participant ST as classify()
    participant EV as apply_status()
    participant DB as Database

    G->>R: POST /api/v1/telemetry + X-API-Key
    alt API key salah
        R-->>G: 401
    end
    R->>I: ingest(payload)
    I->>AR: resolve(payload)
    alt tidak ada adapter yang cocok
        AR-->>I: None
        I-->>R: UnknownFormatError
        R-->>G: 422 format tidak dikenali
    end
    AR-->>I: adapter
    I->>AD: parse(payload)
    AD-->>I: measurements + rejected
    loop setiap rekaman, urut waktu
        I->>DB: cek penyulang, validasi, cek hash
        alt ditolak atau duplikat
            I->>I: catat di rejected atau duplicates
        else lolos
            I->>DB: simpan Measurement
            opt rekaman paling baru untuk penyulang ini
                I->>ST: classify(arus, tegangan, kapasitas)
                ST-->>I: status, persen beban
                I->>EV: apply_status(...)
                EV->>DB: buka atau tutup Alarm dan Outage
            end
        end
    end
    I->>DB: commit
    I-->>R: IngestResult
    R-->>G: 201 + ringkasan hasil
```

## 4. Sequence Diagram: operator menangani gangguan

```mermaid
sequenceDiagram
    actor O as Operator
    participant FE as Frontend
    participant API as Backend
    participant DB as Database

    Note over API,DB: Telemetri dengan tegangan 0 kV sudah membuka alarm padam dan gangguan otomatis
    FE->>API: GET /feeders, GET /alarms (setiap 5 detik)
    API-->>FE: PYL-02 padam, alarm padam aktif
    O->>FE: isi nama, klik Konfirmasi
    FE->>API: POST /alarms/{id}/acknowledge
    API->>DB: simpan acknowledged_at dan acknowledged_by
    API-->>FE: alarm terkonfirmasi
    Note over API,DB: Tegangan kembali, gangguan ditutup otomatis
    O->>FE: buka Gangguan, klik Lengkapi, pilih penyebab
    FE->>API: PATCH /outages/{id} cause=pohon
    API->>DB: perbarui gangguan
    API-->>FE: gangguan lengkap
    O->>FE: buka Keandalan
    FE->>API: GET /reliability?days=30
    API-->>FE: SAIDI, SAIFI, CAIDI terbaru
```

## 5. Activity Diagram: menentukan status penyulang

```mermaid
flowchart TD
    S([Pengukuran baru tersimpan]) --> N{Paling baru untuk penyulang ini?}
    N -- Tidak --> X([Selesai, status tidak berubah])
    N -- Ya --> V{Tegangan < 2 kV?}
    V -- Ya --> P[Status padam]
    V -- Tidak --> L[Hitung beban = arus / kapasitas x 100]
    L --> K{Beban >= 95%?}
    K -- Ya --> KR[Status kritis]
    K -- Tidak --> W{Beban >= 80%?}
    W -- Ya --> WA[Status waspada]
    W -- Tidak --> NO[Status normal]
    P --> E[apply_status]
    KR --> E
    WA --> E
    NO --> E
    E --> Z([Selesai])
```

## 6. State Diagram: alarm

```mermaid
stateDiagram-v2
    [*] --> AktifBelumDikonfirmasi : status penyulang bukan normal
    AktifBelumDikonfirmasi --> AktifDikonfirmasi : operator konfirmasi
    AktifBelumDikonfirmasi --> Selesai : status kembali normal
    AktifDikonfirmasi --> Selesai : status kembali normal
    AktifBelumDikonfirmasi --> Selesai : level berubah, alarm baru dibuat
    AktifDikonfirmasi --> Selesai : level berubah, alarm baru dibuat
    Selesai --> [*]
```

## 7. State Diagram: gangguan

```mermaid
stateDiagram-v2
    [*] --> Terbuka : tegangan hilang (otomatis) atau dicatat operator
    Terbuka --> Pulih : tegangan kembali atau waktu pulih diisi
    Pulih --> Lengkap : penyebab diisi
    Terbuka --> Terbuka : penyebab diisi lebih dulu
    Lengkap --> [*]
    Pulih --> [*] : tetap dihitung, penyebab "belum diketahui"
```

## 8. Deployment Diagram

```mermaid
flowchart LR
    subgraph Browser["Perangkat operator"]
        UI["Frontend React<br/>(HTML, CSS, JS statis)"]
    end
    subgraph GitHub
        REPO["Repository"]
        ACT["GitHub Actions<br/>test + build"]
        PAGES["GitHub Pages"]
    end
    subgraph Render["Render free web service"]
        UV["Uvicorn + FastAPI"]
        SQL[("SQLite<br/>disk sementara")]
    end
    REPO --> ACT --> PAGES
    REPO -- autoDeploy --> UV
    PAGES -- "unduh aset" --> UI
    UI -- "REST JSON (HTTPS)" --> UV
    UV --> SQL
```
