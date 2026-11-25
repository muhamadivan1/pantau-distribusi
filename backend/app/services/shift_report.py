"""Ringkasan serah terima shift.

Operator yang bergantian jaga perlu tahu apa yang terjadi selama shift
sebelumnya. Fungsi ini menyusun ringkasan dalam kalimat dari data alarm,
gangguan, dan beban terakhir.

Ringkasan dibuat dengan aturan (rule-based), bukan model AI, supaya isinya
selalu bisa ditelusuri ke data dan tidak mengarang.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Alarm, Feeder, Measurement, Outage
from ..schemas import ShiftSummaryOut
from ..timeutil import WIB, as_utc
from .reliability import CAUSE_LABELS
from .status import load_percent


def _jam(dt: datetime) -> str:
    return as_utc(dt).astimezone(WIB).strftime("%H:%M WIB")


def build(session: Session, hours: int, now: datetime, settings: Settings) -> ShiftSummaryOut:
    start = now - timedelta(hours=hours)
    feeders = {f.id: f for f in session.scalars(select(Feeder))}

    alarms = list(session.scalars(select(Alarm).where(Alarm.raised_at >= start, Alarm.raised_at <= now)))
    unacked_open = list(session.scalars(select(Alarm).where(Alarm.cleared_at.is_(None), Alarm.acknowledged_at.is_(None))))
    started = list(session.scalars(select(Outage).where(Outage.started_at >= start, Outage.started_at <= now)))
    restored = list(session.scalars(select(Outage).where(Outage.restored_at >= start, Outage.restored_at <= now)))
    still_open = list(session.scalars(select(Outage).where(Outage.restored_at.is_(None))))

    counts = {
        "alarm_waspada": sum(a.level == "waspada" for a in alarms),
        "alarm_kritis": sum(a.level == "kritis" for a in alarms),
        "alarm_padam": sum(a.level == "padam" for a in alarms),
        "alarm_belum_dikonfirmasi": len(unacked_open),
        "gangguan_baru": len(started),
        "gangguan_pulih": len(restored),
        "gangguan_masih_terbuka": len(still_open),
    }

    lines: list[str] = []
    if still_open:
        for o in still_open:
            name = feeders[o.feeder_id].name if o.feeder_id in feeders else o.feeder_id
            lines.append(f"Gangguan masih terbuka di {o.feeder_id} {name} sejak {_jam(o.started_at)}, penyebab: {CAUSE_LABELS.get(o.cause, o.cause).lower()}.")
    for o in restored:
        minutes = (o.restored_at - o.started_at).total_seconds() / 60
        lines.append(f"{o.feeder_id} padam {minutes:.0f} menit dan pulih pukul {_jam(o.restored_at)}.")
    if unacked_open:
        ids = ", ".join(sorted({a.feeder_id for a in unacked_open}))
        lines.append(f"{len(unacked_open)} alarm aktif belum dikonfirmasi operator: {ids}.")

    # Penyulang dengan beban tertinggi berdasarkan pengukuran terakhir.
    latest_time = select(Measurement.feeder_id, func.max(Measurement.measured_at).label("t")).group_by(Measurement.feeder_id).subquery()
    latest = session.execute(
        select(Measurement).join(latest_time, (Measurement.feeder_id == latest_time.c.feeder_id) & (Measurement.measured_at == latest_time.c.t))
    ).scalars()
    loads = sorted(
        ((load_percent(m.current_a, feeders[m.feeder_id].capacity_a), m.feeder_id) for m in latest if m.feeder_id in feeders),
        reverse=True,
    )
    if loads:
        pct, fid = loads[0]
        lines.append(f"Beban tertinggi saat ini di {fid} {feeders[fid].name}: {pct:.0f}% dari kapasitas.")

    # Judul dipilih dari kondisi paling penting lebih dulu.
    if counts["gangguan_masih_terbuka"]:
        headline = f"Perlu tindak lanjut: {counts['gangguan_masih_terbuka']} gangguan masih terbuka."
    elif counts["gangguan_baru"] or counts["gangguan_pulih"] or counts["alarm_padam"]:
        headline = "Ada gangguan selama shift, semuanya sudah pulih."
    elif counts["alarm_kritis"] or counts["alarm_waspada"]:
        headline = "Tanpa gangguan, tetapi ada penyulang yang sempat mendekati atau melewati batas beban."
    else:
        headline = "Shift berjalan normal tanpa gangguan."

    return ShiftSummaryOut(start=as_utc(start), end=as_utc(now), headline=headline, lines=lines, counts=counts)
