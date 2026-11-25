"""Test perhitungan SAIDI, SAIFI, dan CAIDI dengan angka yang bisa dihitung manual."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete

from app.models import Feeder, Outage
from app.services.reliability import compute

START = datetime(2026, 11, 1)
END = datetime(2026, 12, 1)
NOW = END


@pytest.fixture
def two_feeders(session):
    """Ganti data contoh dengan 2 penyulang: 1.000 dan 3.000 pelanggan (total 4.000)."""
    session.execute(delete(Feeder))
    session.add_all(
        [
            Feeder(id="A", name="A", substation="GI X", area="X", capacity_a=400, customers=1000),
            Feeder(id="B", name="B", substation="GI X", area="X", capacity_a=400, customers=3000),
        ]
    )
    session.commit()
    return session


def outage(feeder, start, minutes, customers, cause="pohon"):
    end = start + timedelta(minutes=minutes) if minutes is not None else None
    return Outage(feeder_id=feeder, started_at=start, restored_at=end, customers_affected=customers, cause=cause, notes="")


def test_rumus_sesuai_hitungan_manual(two_feeders, settings):
    two_feeders.add_all(
        [
            outage("A", datetime(2026, 11, 5, 10), 60, 1000),  # 60.000 pelanggan-menit
            outage("B", datetime(2026, 11, 9, 14), 30, 500, cause="cuaca"),  # 15.000 pelanggan-menit
            outage("B", datetime(2026, 11, 10, 9), 3, 3000),  # 3 menit: gangguan sesaat, tidak dihitung
        ]
    )
    two_feeders.commit()
    r = compute(two_feeders, START, END, NOW, settings)
    # SAIFI = (1000 + 500) / 4000 = 0,375 kali
    # SAIDI = (60000 + 15000) / 4000 = 18,75 menit
    # CAIDI = 18,75 / 0,375 = 50 menit
    assert r.interruptions == 2
    assert r.saifi == 0.375
    assert r.saidi_minutes == 18.75
    assert r.caidi_minutes == 50.0
    assert [row.key for row in r.by_feeder] == ["A", "B"]  # diurutkan dari pelanggan-menit terbesar


def test_gangguan_melewati_batas_periode_dipotong(two_feeders, settings):
    # Mulai 30 menit sebelum periode, berlangsung 90 menit: hanya 60 menit di dalam periode.
    two_feeders.add(outage("A", START - timedelta(minutes=30), 90, 1000))
    two_feeders.commit()
    r = compute(two_feeders, START, END, NOW, settings)
    assert r.saidi_minutes == 60 * 1000 / 4000


def test_gangguan_belum_pulih_dihitung_sampai_sekarang(two_feeders, settings):
    now = datetime(2026, 11, 20, 12, 0)
    two_feeders.add(outage("B", now - timedelta(minutes=120), None, 3000))
    two_feeders.commit()
    r = compute(two_feeders, START, now, now, settings)
    assert r.saidi_minutes == 120 * 3000 / 4000


def test_tanpa_gangguan_semua_nol(two_feeders, settings):
    r = compute(two_feeders, START, END, NOW, settings)
    assert (r.interruptions, r.saidi_minutes, r.saifi, r.caidi_minutes) == (0, 0.0, 0.0, None)
