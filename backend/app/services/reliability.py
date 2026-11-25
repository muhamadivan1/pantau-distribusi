"""Indeks keandalan distribusi: SAIDI, SAIFI, CAIDI.

Definisi mengikuti IEEE Std 1366 (Guide for Electric Power Distribution
Reliability Indices):

    SAIFI = jumlah pelanggan padam / jumlah pelanggan dilayani
            (berapa kali rata-rata satu pelanggan mengalami padam)

    SAIDI = jumlah (lama padam x pelanggan padam) / jumlah pelanggan dilayani
            (berapa menit rata-rata satu pelanggan mengalami padam)

    CAIDI = SAIDI / SAIFI
            (rata-rata lama pemulihan per kejadian padam yang dialami pelanggan)

Penyederhanaan di proyek ini (ditulis juga di docs/ARCHITECTURE.md):
- Hanya gangguan berkelanjutan (lebih dari sustained_minutes) yang dihitung.
- Gangguan yang melewati batas periode hanya dihitung bagian di dalam periode.
- Gangguan yang belum pulih dihitung sampai waktu sekarang.
- Belum ada pemisahan major event day (TMED).
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Feeder, Outage
from ..schemas import ReliabilityOut, ReliabilityRow
from ..timeutil import as_utc

CAUSE_LABELS = {
    "pohon": "Pohon atau ranting",
    "hewan": "Hewan",
    "peralatan": "Kerusakan peralatan",
    "cuaca": "Cuaca",
    "pihak_ketiga": "Pihak ketiga",
    "pemeliharaan": "Pemeliharaan terencana",
    "belum_diketahui": "Belum diketahui",
}


def minutes_between(a: datetime, b: datetime) -> float:
    return max((b - a).total_seconds() / 60, 0.0)


def compute(session: Session, start: datetime, end: datetime, now: datetime, settings: Settings) -> ReliabilityOut:
    feeders = {f.id: f for f in session.scalars(select(Feeder))}
    customers_served = sum(f.customers for f in feeders.values())

    # Gangguan yang beririsan dengan periode [start, end].
    stmt = select(Outage).where(
        Outage.started_at < end,
        or_(Outage.restored_at.is_(None), Outage.restored_at > start),
    )

    by_feeder: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0])  # [kejadian, pelanggan, pelanggan-menit]
    by_cause: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0])
    total_events = total_customers = 0
    total_customer_minutes = 0.0

    for outage in session.scalars(stmt):
        actual_end = outage.restored_at or now
        if minutes_between(outage.started_at, actual_end) <= settings.sustained_minutes:
            continue  # gangguan sesaat, tidak dihitung
        minutes = minutes_between(max(outage.started_at, start), min(actual_end, end))
        n = outage.customers_affected

        total_events += 1
        total_customers += n
        total_customer_minutes += minutes * n
        for bucket, key in ((by_feeder, outage.feeder_id), (by_cause, outage.cause)):
            bucket[key][0] += 1
            bucket[key][1] += n
            bucket[key][2] += minutes * n

    saifi = total_customers / customers_served if customers_served else 0.0
    saidi = total_customer_minutes / customers_served if customers_served else 0.0

    def rows(data: dict, label_of) -> list[ReliabilityRow]:
        out = [
            ReliabilityRow(key=k, label=label_of(k), interruptions=int(v[0]), customers_interrupted=int(v[1]), customer_minutes=round(v[2], 1))
            for k, v in data.items()
        ]
        return sorted(out, key=lambda r: r.customer_minutes, reverse=True)

    return ReliabilityOut(
        start=as_utc(start),
        end=as_utc(end),
        customers_served=customers_served,
        sustained_threshold_minutes=settings.sustained_minutes,
        interruptions=total_events,
        saidi_minutes=round(saidi, 2),
        saifi=round(saifi, 4),
        caidi_minutes=round(saidi / saifi, 2) if saifi else None,
        by_feeder=rows(by_feeder, lambda k: f"{k} {feeders[k].name}" if k in feeders else k),
        by_cause=rows(by_cause, lambda k: CAUSE_LABELS.get(k, k)),
    )
