"""Data contoh untuk demo.

Isi:
- 6 penyulang fiktif di 2 gardu induk fiktif.
- Telemetri 24 jam terakhir setiap 15 menit, dimasukkan lewat jalur ingest
  (sehingga alarm dan gangguan otomatis ikut terbentuk).
- Riwayat gangguan 90 hari ke belakang untuk halaman keandalan.

Semua nama, angka, dan kejadian adalah fiktif.
"""

import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .models import Feeder, Outage
from .services.ingestion import ingest
from .services.simulator import GridSimulator
from .timeutil import utcnow

FEEDERS = [
    # id, nama, gardu induk, area, kapasitas (A), jumlah pelanggan
    ("PYL-01", "Cempaka", "GI Demo Utara", "Kota Utara", 400, 8200),
    ("PYL-02", "Dahlia", "GI Demo Utara", "Kota Utara", 400, 9100),
    ("PYL-03", "Kenanga", "GI Demo Utara", "Kawasan Industri", 630, 1450),
    ("PYL-04", "Melati", "GI Demo Selatan", "Kota Selatan", 400, 7600),
    ("PYL-05", "Anggrek", "GI Demo Selatan", "Kota Selatan", 400, 10350),
    ("PYL-06", "Teratai", "GI Demo Selatan", "Pinggiran Kota", 300, 5300),
]

CAUSE_WEIGHTS = {"pohon": 30, "hewan": 12, "peralatan": 22, "cuaca": 18, "pihak_ketiga": 8, "pemeliharaan": 10}


def seed_feeders(session: Session) -> bool:
    """Isi tabel penyulang jika masih kosong. True jika baru diisi."""
    if session.scalar(select(Feeder.id).limit(1)):
        return False
    for fid, name, gi, area, cap, cust in FEEDERS:
        session.add(Feeder(id=fid, name=name, substation=gi, area=area, capacity_a=cap, customers=cust))
    session.commit()
    return True


def seed_history(session: Session, settings: Settings, now: datetime | None = None, seed: int = 7) -> None:
    """Riwayat telemetri 24 jam dan gangguan 90 hari."""
    now = now or utcnow()
    capacities = {f.id: f.capacity_a for f in session.scalars(select(Feeder))}

    # Telemetri 24 jam, setiap 15 menit, lewat jalur ingest yang sebenarnya.
    sim = GridSimulator(capacities, seed=seed, trip_probability=0.006, trip_ticks=(1, 3))
    t = (now - timedelta(hours=24)).replace(second=0)
    t = t - timedelta(minutes=t.minute % 15)
    while t <= now:
        for payload in sim.payloads_at(t):
            ingest(session, payload, settings, now=now)
        t += timedelta(minutes=15)

    # Riwayat gangguan 90 hari (sebelum 24 jam terakhir supaya tidak tumpang tindih).
    rng = random.Random(seed)
    feeders = list(session.scalars(select(Feeder)))
    causes, weights = zip(*CAUSE_WEIGHTS.items(), strict=True)
    for _ in range(28):
        feeder = rng.choice(feeders)
        started = now - timedelta(days=rng.uniform(1.2, 90), minutes=rng.randint(0, 59))
        duration = rng.choice([rng.randint(8, 45), rng.randint(30, 120), rng.randint(90, 300)])
        # Sebagian gangguan hanya mengenai sebagian pelanggan (setelah manuver jaringan).
        share = rng.choice([1.0, 1.0, 0.6, 0.35])
        session.add(
            Outage(
                feeder_id=feeder.id,
                started_at=started.replace(microsecond=0),
                restored_at=(started + timedelta(minutes=duration)).replace(microsecond=0),
                cause=rng.choices(causes, weights)[0],
                customers_affected=int(feeder.customers * share),
                notes="Data contoh",
                auto_detected=rng.random() < 0.6,
            )
        )
    session.commit()
