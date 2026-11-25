"""Bentuk data yang masuk dan keluar dari API (Pydantic).

Skema di sini juga menjadi dasar dokumentasi otomatis di /docs dan
berkas docs/openapi.json.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["normal", "waspada", "kritis", "padam", "tanpa_data"]
Cause = Literal["pohon", "hewan", "peralatan", "cuaca", "pihak_ketiga", "pemeliharaan", "belum_diketahui"]


class CanonicalMeasurement(BaseModel):
    """Bentuk kanonik: semua format telemetri diubah ke bentuk ini oleh adapter."""

    feeder_id: str
    measured_at: datetime  # selalu UTC
    current_a: float
    voltage_kv: float
    power_mw: float
    source_format: str


# ---------- Penyulang ----------


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measured_at: datetime
    current_a: float
    voltage_kv: float
    power_mw: float
    source_format: str


class FeederOut(BaseModel):
    id: str
    name: str
    substation: str
    area: str
    capacity_a: float
    customers: int
    status: Status
    load_pct: float | None = Field(None, description="Arus terakhir dibagi kapasitas, dalam persen")
    latest: MeasurementOut | None = None


# ---------- Telemetri ----------


class RejectedRecord(BaseModel):
    feeder_id: str | None
    reasons: list[str]


class IngestResult(BaseModel):
    adapter: str
    received: int
    stored: int
    duplicates: int
    rejected: list[RejectedRecord]
    alarms_raised: int
    outages_opened: int
    outages_closed: int
    processing_ms: float


# ---------- Alarm ----------


class AlarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feeder_id: str
    level: str
    message: str
    load_pct: float | None
    raised_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    cleared_at: datetime | None


class AcknowledgeIn(BaseModel):
    by: str = Field(..., min_length=2, max_length=80, examples=["Operator Shift Pagi"])


# ---------- Gangguan ----------


class OutageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feeder_id: str
    started_at: datetime
    restored_at: datetime | None
    cause: str
    customers_affected: int
    notes: str
    auto_detected: bool
    duration_minutes: float | None = None


class OutageCreate(BaseModel):
    feeder_id: str
    started_at: datetime
    restored_at: datetime | None = None
    cause: Cause = "belum_diketahui"
    customers_affected: int | None = Field(None, ge=0, description="Kosongkan untuk memakai jumlah pelanggan penyulang")
    notes: str = ""


class OutageUpdate(BaseModel):
    restored_at: datetime | None = None
    cause: Cause | None = None
    customers_affected: int | None = Field(None, ge=0)
    notes: str | None = None


# ---------- Keandalan ----------


class ReliabilityRow(BaseModel):
    key: str
    label: str
    interruptions: int
    customers_interrupted: int
    customer_minutes: float


class ReliabilityOut(BaseModel):
    start: datetime
    end: datetime
    customers_served: int
    sustained_threshold_minutes: float
    interruptions: int
    saidi_minutes: float
    saifi: float
    caidi_minutes: float | None
    by_feeder: list[ReliabilityRow]
    by_cause: list[ReliabilityRow]


# ---------- Ringkasan shift ----------


class ShiftSummaryOut(BaseModel):
    start: datetime
    end: datetime
    headline: str
    lines: list[str]
    counts: dict[str, int]
