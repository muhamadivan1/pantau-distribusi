"""Membuat alarm dan membuka atau menutup gangguan dari perubahan status.

Aturan alarm (paling banyak satu alarm terbuka per penyulang):
- Status normal        -> alarm terbuka ditutup (cleared_at diisi).
- Status bukan normal  -> jika belum ada alarm terbuka, atau levelnya berbeda,
                          alarm lama ditutup dan alarm baru dibuat.

Aturan gangguan otomatis:
- Status padam dan belum ada gangguan terbuka -> buka gangguan baru.
- Status bukan padam dan ada gangguan terbuka  -> tutup (restored_at diisi).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Alarm, Feeder, Outage

MESSAGES = {
    "waspada": "Beban {name} {pct:.0f}% dari kapasitas, mendekati batas",
    "kritis": "Beban {name} {pct:.0f}% dari kapasitas, melewati batas kritis",
    "padam": "Tegangan {name} hilang, penyulang padam",
}


@dataclass
class EventCounts:
    alarms_raised: int = 0
    outages_opened: int = 0
    outages_closed: int = 0


def open_alarm(session: Session, feeder_id: str) -> Alarm | None:
    stmt = select(Alarm).where(Alarm.feeder_id == feeder_id, Alarm.cleared_at.is_(None)).order_by(Alarm.raised_at.desc())
    return session.scalars(stmt).first()


def open_outage(session: Session, feeder_id: str) -> Outage | None:
    stmt = select(Outage).where(Outage.feeder_id == feeder_id, Outage.restored_at.is_(None)).order_by(Outage.started_at.desc())
    return session.scalars(stmt).first()


def apply_status(session: Session, feeder: Feeder, status: str, load_pct: float, at: datetime) -> EventCounts:
    """Terapkan aturan alarm dan gangguan untuk satu status baru."""
    counts = EventCounts()

    # ---- Alarm ----
    current = open_alarm(session, feeder.id)
    if status == "normal":
        if current:
            current.cleared_at = at
    elif current is None or current.level != status:
        if current:
            current.cleared_at = at
        session.add(
            Alarm(
                feeder_id=feeder.id,
                level=status,
                message=MESSAGES[status].format(name=feeder.name, pct=load_pct),
                load_pct=None if status == "padam" else load_pct,
                raised_at=at,
            )
        )
        counts.alarms_raised += 1

    # ---- Gangguan ----
    outage = open_outage(session, feeder.id)
    if status == "padam" and outage is None:
        session.add(
            Outage(
                feeder_id=feeder.id,
                started_at=at,
                customers_affected=feeder.customers,
                cause="belum_diketahui",
                notes="Dibuka otomatis dari telemetri: tegangan hilang.",
                auto_detected=True,
            )
        )
        counts.outages_opened += 1
    elif status != "padam" and outage is not None:
        outage.restored_at = at
        counts.outages_closed += 1

    session.flush()  # supaya pemeriksaan berikutnya di request yang sama melihat perubahan ini
    return counts
