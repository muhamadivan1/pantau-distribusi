"""Test simulator: payload tiruan harus lolos jalur ingest yang sebenarnya."""

from datetime import datetime

from app.seed import FEEDERS
from app.services.ingestion import ingest
from app.services.simulator import GridSimulator, daily_profile

CAPACITIES = {fid: cap for fid, _n, _g, _a, cap, _c in FEEDERS}
AT = datetime(2026, 11, 25, 12, 0)  # 19:00 WIB, beban puncak


def test_simulator_menghasilkan_tiga_format():
    payloads = GridSimulator(CAPACITIES, seed=1, trip_probability=0).payloads_at(AT)
    # 1 RTU (3 penyulang) + 2 Modbus + 1 CSV
    assert len(payloads) == 4


def test_payload_simulator_lolos_ingest_tanpa_penolakan(session, settings):
    sim = GridSimulator(CAPACITIES, seed=1, trip_probability=0)
    results = [ingest(session, p, settings, now=AT) for p in sim.payloads_at(AT)]
    assert sum(r.stored for r in results) == 6
    assert all(not r.rejected for r in results)
    assert {r.adapter for r in results} == {"rtu-ioa", "modbus", "csv-meter"}


def test_simulator_dengan_seed_sama_hasilnya_sama():
    a = GridSimulator(CAPACITIES, seed=42).payloads_at(AT)
    b = GridSimulator(CAPACITIES, seed=42).payloads_at(AT)
    assert a == b


def test_beban_puncak_malam_lebih_tinggi_dari_dini_hari():
    assert daily_profile(19) > daily_profile(3)


def test_simulated_feeders_bisa_dibatasi():
    """DEMO_SIMULATED_FEEDERS dipakai saat PYL-04 dan PYL-05 dipasok gateway Modbus."""
    from app.config import Settings
    from app.main import simulated_capacities

    caps = {"PYL-01": 400, "PYL-04": 400, "PYL-05": 400, "PYL-06": 300}
    semua = simulated_capacities(caps, Settings(demo_simulated_feeders=""))
    assert semua == caps

    sebagian = simulated_capacities(caps, Settings(demo_simulated_feeders=" pyl-01, PYL-06 "))
    assert sebagian == {"PYL-01": 400, "PYL-06": 300}
    # payload yang dihasilkan tidak lagi berisi format modbus
    sim = GridSimulator(sebagian, seed=1, trip_probability=0)
    payloads = sim.payloads_at(datetime(2026, 11, 25, 1, 0))
    assert not any("registers" in p for p in payloads)
