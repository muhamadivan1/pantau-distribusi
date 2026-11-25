"""Alur utama penerimaan telemetri.

    payload mentah
      -> registry.resolve()      pilih adapter dari isi payload
      -> adapter.parse()         ubah ke CanonicalMeasurement
      -> validate()              periksa penyulang, rentang nilai, waktu
      -> record_hash()           lewati data yang sudah pernah tersimpan
      -> simpan Measurement
      -> classify() + apply_status()  alarm dan gangguan (hanya untuk data terbaru)
"""

import hashlib
import time
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..adapters.base import AdapterError
from ..adapters.registry import AdapterRegistry, default_registry
from ..config import Settings
from ..models import Feeder, Measurement
from ..schemas import CanonicalMeasurement, IngestResult, RejectedRecord
from ..timeutil import utcnow
from .events import EventCounts, apply_status
from .status import classify

# Rentang nilai yang masuk akal untuk penyulang 20 kV. Di luar ini dianggap
# data rusak (sensor error, salah skala), bukan kondisi jaringan.
RANGES = {
    "current_a": (0.0, 1000.0),
    "voltage_kv": (0.0, 24.0),
    "power_mw": (0.0, 30.0),
}
CLOCK_SKEW = timedelta(minutes=5)  # toleransi jam perangkat yang sedikit maju


class UnknownFormatError(ValueError):
    """Tidak ada adapter yang mengenali payload."""


def record_hash(m: CanonicalMeasurement) -> str:
    """Sidik jari rekaman. Rekaman yang sama persis selalu menghasilkan hash yang sama."""
    raw = f"{m.feeder_id}|{m.measured_at.isoformat()}|{m.current_a:.3f}|{m.voltage_kv:.3f}|{m.power_mw:.3f}"
    return hashlib.sha256(raw.encode()).hexdigest()


def validate(m: CanonicalMeasurement, feeder: Feeder | None, now: datetime) -> list[str]:
    """Kembalikan daftar alasan penolakan. Kosong berarti lolos."""
    reasons = []
    if feeder is None:
        reasons.append(f"penyulang {m.feeder_id} tidak terdaftar")
    for field, (low, high) in RANGES.items():
        value = getattr(m, field)
        if not low <= value <= high:
            reasons.append(f"{field}={value} di luar rentang {low}-{high}")
    if m.measured_at > now + CLOCK_SKEW:
        reasons.append("waktu pengukuran berada di masa depan")
    return reasons


def ingest(
    session: Session,
    payload: dict,
    settings: Settings,
    now: datetime | None = None,
    registry: AdapterRegistry = default_registry,
) -> IngestResult:
    started = time.perf_counter()
    now = now or utcnow()

    adapter = registry.resolve(payload)
    if adapter is None:
        raise UnknownFormatError(f"format tidak dikenali. Format yang didukung: {', '.join(registry.names)}")
    try:
        parsed = adapter.parse(payload)
    except AdapterError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise AdapterError(f"payload {adapter.name} tidak bisa dibaca: {exc}") from exc

    rejected: list[RejectedRecord] = list(parsed.rejected)
    stored = duplicates = 0
    totals = EventCounts()

    # Urutkan berdasarkan waktu supaya status diterapkan sesuai urutan kejadian.
    for m in sorted(parsed.measurements, key=lambda x: x.measured_at):
        feeder = session.get(Feeder, m.feeder_id)
        reasons = validate(m, feeder, now)
        if reasons:
            rejected.append(RejectedRecord(feeder_id=m.feeder_id, reasons=reasons))
            continue

        digest = record_hash(m)
        if session.scalar(select(Measurement.id).where(Measurement.record_hash == digest)):
            duplicates += 1
            continue

        # Data susulan (lebih lama dari data terakhir) tetap disimpan untuk grafik,
        # tetapi tidak mengubah alarm atau gangguan yang sedang berjalan.
        latest_at = session.scalar(select(func.max(Measurement.measured_at)).where(Measurement.feeder_id == m.feeder_id))
        is_newest = latest_at is None or m.measured_at > latest_at

        session.add(Measurement(record_hash=digest, **m.model_dump()))
        session.flush()
        stored += 1

        if is_newest:
            status, pct = classify(m.current_a, m.voltage_kv, feeder.capacity_a, settings)
            counts = apply_status(session, feeder, status, pct, m.measured_at)
            totals.alarms_raised += counts.alarms_raised
            totals.outages_opened += counts.outages_opened
            totals.outages_closed += counts.outages_closed

    session.commit()
    return IngestResult(
        adapter=adapter.name,
        received=len(parsed.measurements) + len(parsed.rejected),
        stored=stored,
        duplicates=duplicates,
        rejected=rejected,
        alarms_raised=totals.alarms_raised,
        outages_opened=totals.outages_opened,
        outages_closed=totals.outages_closed,
        processing_ms=round((time.perf_counter() - started) * 1000, 2),
    )
