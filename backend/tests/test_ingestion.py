"""Test alur ingest: validasi, deduplikasi, alarm, dan gangguan otomatis."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import Alarm, Measurement, Outage
from app.services.ingestion import UnknownFormatError, ingest

NOW = datetime(2026, 11, 25, 12, 0, 0)  # UTC


def modbus(feeder: str, at: datetime, current: float, voltage: float = 20.0, power: float = 6.0) -> dict:
    """Bangun payload Modbus singkat untuk satu penyulang."""
    return {
        "device": f"IED-{feeder}",
        "feeder": feeder,
        "ts_epoch": int(at.replace(tzinfo=UTC).timestamp()),
        "registers": {"40001": round(current * 10), "40002": round(voltage * 100), "40003": round(power * 100)},
    }


def count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_data_tersimpan_dan_kiriman_ulang_tidak_ganda(session, settings):
    payload = modbus("PYL-04", NOW, 200)
    first = ingest(session, payload, settings, now=NOW)
    second = ingest(session, payload, settings, now=NOW)
    assert (first.stored, first.duplicates) == (1, 0)
    assert (second.stored, second.duplicates) == (0, 1)
    assert count(session, Measurement) == 1


def test_nilai_di_luar_rentang_ditolak(session, settings):
    result = ingest(session, modbus("PYL-04", NOW, 1500), settings, now=NOW)
    assert result.stored == 0
    assert "current_a=1500.0 di luar rentang" in result.rejected[0].reasons[0]


def test_penyulang_tidak_terdaftar_ditolak(session, settings):
    result = ingest(session, modbus("PYL-99", NOW, 100), settings, now=NOW)
    assert result.rejected[0].reasons == ["penyulang PYL-99 tidak terdaftar"]


def test_waktu_masa_depan_ditolak(session, settings):
    result = ingest(session, modbus("PYL-04", NOW + timedelta(hours=1), 100), settings, now=NOW)
    assert result.rejected[0].reasons == ["waktu pengukuran berada di masa depan"]


def test_beban_tinggi_membuat_alarm_lalu_tertutup_saat_normal(session, settings):
    # PYL-04 berkapasitas 400 A: 340 A = 85% (waspada), 390 A = 97,5% (kritis)
    ingest(session, modbus("PYL-04", NOW, 340), settings, now=NOW + timedelta(hours=1))
    ingest(session, modbus("PYL-04", NOW + timedelta(minutes=5), 390), settings, now=NOW + timedelta(hours=1))
    alarms = list(session.scalars(select(Alarm).order_by(Alarm.raised_at)))
    assert [a.level for a in alarms] == ["waspada", "kritis"]
    assert alarms[0].cleared_at is not None  # alarm waspada ditutup saat naik ke kritis
    assert alarms[1].cleared_at is None

    ingest(session, modbus("PYL-04", NOW + timedelta(minutes=10), 200), settings, now=NOW + timedelta(hours=1))
    assert session.scalar(select(func.count()).select_from(Alarm).where(Alarm.cleared_at.is_(None))) == 0


def test_tegangan_hilang_membuka_gangguan_dan_pulih_menutupnya(session, settings):
    later = NOW + timedelta(hours=1)
    result = ingest(session, modbus("PYL-05", NOW, 0, voltage=0, power=0), settings, now=later)
    assert result.outages_opened == 1
    outage = session.scalars(select(Outage)).one()
    assert outage.auto_detected and outage.restored_at is None
    assert outage.customers_affected == 10350  # jumlah pelanggan PYL-05

    result = ingest(session, modbus("PYL-05", NOW + timedelta(minutes=40), 250), settings, now=later)
    assert result.outages_closed == 1
    assert outage.restored_at == NOW + timedelta(minutes=40)


def test_data_susulan_tidak_mengubah_alarm(session, settings):
    later = NOW + timedelta(hours=1)
    ingest(session, modbus("PYL-04", NOW, 200), settings, now=later)  # data terbaru: normal
    result = ingest(session, modbus("PYL-04", NOW - timedelta(minutes=30), 395), settings, now=later)  # data lama: kritis
    assert result.stored == 1
    assert result.alarms_raised == 0


def test_format_tidak_dikenal_menimbulkan_error(session, settings):
    with pytest.raises(UnknownFormatError):
        ingest(session, {"halo": "dunia"}, settings, now=NOW)
