"""Tabel database (ORM).

Empat tabel utama:
    feeders       data induk penyulang 20 kV
    measurements  hasil pengukuran yang sudah dalam bentuk kanonik
    alarms        peringatan beban atau padam untuk operator
    outages       catatan gangguan (padam) untuk menghitung keandalan

Semua waktu disimpan dalam UTC. Konversi ke WIB dilakukan di frontend.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Feeder(Base):
    __tablename__ = "feeders"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # contoh: PYL-01
    name: Mapped[str] = mapped_column(String(80))
    substation: Mapped[str] = mapped_column(String(80))  # gardu induk asal penyulang
    area: Mapped[str] = mapped_column(String(80))
    capacity_a: Mapped[float] = mapped_column(Float)  # batas arus yang dijadikan 100%
    customers: Mapped[int] = mapped_column(Integer)  # jumlah pelanggan yang dilayani

    measurements: Mapped[list["Measurement"]] = relationship(back_populates="feeder")


class Measurement(Base):
    __tablename__ = "measurements"
    # record_hash unik: data yang dikirim ulang tidak tersimpan dua kali.
    __table_args__ = (UniqueConstraint("record_hash", name="uq_measurement_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feeder_id: Mapped[str] = mapped_column(ForeignKey("feeders.id"), index=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    current_a: Mapped[float] = mapped_column(Float)
    voltage_kv: Mapped[float] = mapped_column(Float)
    power_mw: Mapped[float] = mapped_column(Float)
    source_format: Mapped[str] = mapped_column(String(20))  # adapter yang membacanya
    record_hash: Mapped[str] = mapped_column(String(64))

    feeder: Mapped[Feeder] = relationship(back_populates="measurements")


class Alarm(Base):
    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feeder_id: Mapped[str] = mapped_column(ForeignKey("feeders.id"), index=True)
    level: Mapped[str] = mapped_column(String(10))  # waspada | kritis | padam
    message: Mapped[str] = mapped_column(String(200))
    load_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    raised_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Outage(Base):
    __tablename__ = "outages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feeder_id: Mapped[str] = mapped_column(ForeignKey("feeders.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    restored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cause: Mapped[str] = mapped_column(String(30), default="belum_diketahui")
    customers_affected: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    # True jika dibuka otomatis dari telemetri (tegangan hilang), False jika dicatat manual.
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False)
