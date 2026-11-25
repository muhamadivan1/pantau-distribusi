"""Adapter format "rtu-ioa".

Meniru data dari RTU di gardu induk yang dikirim gateway dalam bentuk
daftar titik ukur. Setiap titik punya alamat (IOA, information object
address) dan nilai. Satu RTU bisa membawa data beberapa penyulang sekaligus.

Catatan jujur: ini representasi JSON yang disederhanakan untuk portofolio,
bukan pembacaan protokol SCADA yang sebenarnya. Di sistem nyata, gateway
protokol yang mengubah frame biner menjadi bentuk seperti ini.

Contoh payload:
{
  "rtu": "RTU-GI-DEMO-UTARA",
  "timestamp": "2026-11-25T08:00:00+07:00",
  "points": [
    {"ioa": 1001, "value": 245.3},   # arus PYL-01 (A)
    {"ioa": 1002, "value": 20.1},    # tegangan PYL-01 (kV)
    {"ioa": 1003, "value": 8.4}      # daya PYL-01 (MW)
  ]
}
"""

from collections import defaultdict
from datetime import datetime

from ..schemas import CanonicalMeasurement, RejectedRecord
from ..timeutil import to_db
from .base import AdapterError, ParseResult, TelemetryAdapter

# Peta alamat titik ukur ke (penyulang, besaran). Di dunia nyata peta ini
# berasal dari database konfigurasi SCADA.
IOA_MAP: dict[int, tuple[str, str]] = {
    1001: ("PYL-01", "current_a"),
    1002: ("PYL-01", "voltage_kv"),
    1003: ("PYL-01", "power_mw"),
    1011: ("PYL-02", "current_a"),
    1012: ("PYL-02", "voltage_kv"),
    1013: ("PYL-02", "power_mw"),
    1021: ("PYL-03", "current_a"),
    1022: ("PYL-03", "voltage_kv"),
    1023: ("PYL-03", "power_mw"),
}

QUANTITIES = ("current_a", "voltage_kv", "power_mw")


class RtuIoaAdapter(TelemetryAdapter):
    name = "rtu-ioa"

    def supports(self, payload: dict) -> bool:
        return isinstance(payload.get("points"), list) and "timestamp" in payload

    def parse(self, payload: dict) -> ParseResult:
        try:
            measured_at = to_db(datetime.fromisoformat(payload["timestamp"]))
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"timestamp tidak valid: {payload.get('timestamp')!r}") from exc

        # Kelompokkan titik ukur per penyulang: {"PYL-01": {"current_a": 245.3, ...}}
        grouped: dict[str, dict[str, float]] = defaultdict(dict)
        result = ParseResult()
        for point in payload["points"]:
            ioa = point.get("ioa")
            if ioa not in IOA_MAP:
                result.rejected.append(RejectedRecord(feeder_id=None, reasons=[f"IOA {ioa} tidak terdaftar"]))
                continue
            feeder_id, quantity = IOA_MAP[ioa]
            grouped[feeder_id][quantity] = float(point.get("value"))

        for feeder_id, values in grouped.items():
            missing = [q for q in QUANTITIES if q not in values]
            if missing:
                result.rejected.append(RejectedRecord(feeder_id=feeder_id, reasons=[f"titik ukur tidak lengkap: {', '.join(missing)}"]))
                continue
            result.measurements.append(
                CanonicalMeasurement(feeder_id=feeder_id, measured_at=measured_at, source_format=self.name, **values)
            )
        return result
