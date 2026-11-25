"""Simulator telemetri untuk demo.

Menghasilkan pembacaan beban penyulang yang mirip pola harian (rendah dini
hari, puncak sore sampai malam), lalu mengemasnya dalam TIGA format berbeda
sesuai sumber datanya. Payload hasil simulator masuk lewat jalur ingest yang
sama dengan data dari gateway, jadi demo menguji alur yang sebenarnya.

Semua angka adalah data fiktif.
"""

import math
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..adapters.rtu_ioa import IOA_MAP
from ..timeutil import WIB

# Sumber data tiap penyulang menentukan format payload-nya.
FEEDER_FORMAT = {
    "PYL-01": "rtu-ioa",
    "PYL-02": "rtu-ioa",
    "PYL-03": "rtu-ioa",
    "PYL-04": "modbus",
    "PYL-05": "modbus",
    "PYL-06": "csv-meter",
}

# Pengali beban per penyulang: >1 berarti penyulang lebih padat.
LOAD_FACTOR = {"PYL-01": 0.95, "PYL-02": 1.05, "PYL-03": 0.8, "PYL-04": 0.9, "PYL-05": 1.16, "PYL-06": 0.75}


@dataclass
class Reading:
    feeder_id: str
    at: datetime  # UTC tanpa zona
    current_a: float
    voltage_kv: float
    power_mw: float


def daily_profile(hour_wib: float) -> float:
    """Bentuk beban harian (0 sampai 1): dasar malam, naik siang, puncak sekitar pukul 19."""
    night_base = 0.5
    midday = 0.15 * math.exp(-((hour_wib - 11) ** 2) / 10)
    evening_peak = 0.32 * math.exp(-((hour_wib - 19) ** 2) / 6)
    return night_base + midday + evening_peak


@dataclass
class GridSimulator:
    capacities: dict[str, float]  # {feeder_id: kapasitas arus}
    seed: int | None = None
    trip_probability: float = 0.003  # peluang padam per penyulang per langkah
    trip_ticks: tuple[int, int] = (4, 14)  # lama padam dalam jumlah langkah
    rng: random.Random = field(init=False)
    _trip_left: dict[str, int] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.rng = random.Random(self.seed)

    def read(self, feeder_id: str, at: datetime) -> Reading:
        """Satu pembacaan untuk satu penyulang pada waktu tertentu."""
        # Status padam yang sedang berjalan.
        left = self._trip_left.get(feeder_id, 0)
        if left == 0 and self.rng.random() < self.trip_probability:
            left = self.rng.randint(*self.trip_ticks)
        if left > 0:
            self._trip_left[feeder_id] = left - 1
            return Reading(feeder_id, at, 0.0, 0.0, 0.0)

        hour = at.replace(tzinfo=UTC).astimezone(WIB)
        hour_wib = hour.hour + hour.minute / 60
        fraction = daily_profile(hour_wib) * LOAD_FACTOR.get(feeder_id, 1.0) * self.rng.uniform(0.96, 1.04)
        current = round(self.capacities[feeder_id] * fraction, 1)
        voltage = round(20.4 - 0.6 * fraction + self.rng.uniform(-0.1, 0.1), 2)  # makin berat, tegangan sedikit turun
        power = round(math.sqrt(3) * voltage * current * 0.9 / 1000, 2)  # P = akar3 x V x I x cos phi (0,9)
        return Reading(feeder_id, at, current, voltage, power)

    def payloads_at(self, at: datetime) -> list[dict]:
        """Semua payload pada satu waktu, dalam format masing-masing sumber."""
        readings = [self.read(fid, at) for fid in self.capacities]
        return build_payloads(readings, at)


def build_payloads(readings: list[Reading], at: datetime) -> list[dict]:
    payloads: list[dict] = []
    at_wib = at.replace(tzinfo=UTC).astimezone(WIB)

    # 1) Satu payload RTU untuk semua penyulang yang lewat RTU gardu induk.
    reverse_ioa = {(fid, q): ioa for ioa, (fid, q) in IOA_MAP.items()}
    points = []
    for r in readings:
        if FEEDER_FORMAT.get(r.feeder_id) == "rtu-ioa":
            for q in ("current_a", "voltage_kv", "power_mw"):
                points.append({"ioa": reverse_ioa[(r.feeder_id, q)], "value": getattr(r, q)})
    if points:
        payloads.append({"rtu": "RTU-GI-DEMO-UTARA", "timestamp": at_wib.isoformat(), "points": points})

    # 2) Satu payload Modbus per penyulang.
    for r in readings:
        if FEEDER_FORMAT.get(r.feeder_id) == "modbus":
            payloads.append(
                {
                    "device": f"IED-{r.feeder_id}",
                    "feeder": r.feeder_id,
                    "ts_epoch": int(at.replace(tzinfo=UTC).timestamp()),
                    "registers": {
                        "40001": round(r.current_a * 10),
                        "40002": round(r.voltage_kv * 100),
                        "40003": round(r.power_mw * 100),
                    },
                }
            )

    # 3) Satu berkas CSV untuk penyulang yang dibaca lewat sistem meter.
    rows = ["penyulang;waktu;arus_a;tegangan_kv;daya_mw"]
    for r in readings:
        if FEEDER_FORMAT.get(r.feeder_id) == "csv-meter":
            angka = lambda v: f"{v:.2f}".replace(".", ",")  # noqa: E731  (desimal koma)
            rows.append(f"{r.feeder_id};{at_wib.strftime('%d/%m/%Y %H:%M:%S')};{angka(r.current_a)};{angka(r.voltage_kv)};{angka(r.power_mw)}")
    if len(rows) > 1:
        payloads.append({"content": "\n".join(rows)})

    return payloads
