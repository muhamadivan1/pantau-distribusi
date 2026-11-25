"""Adapter format "modbus".

Meniru data dari relai proteksi atau meter digital (IED) di satu penyulang
yang dibaca lewat register. Nilai register berupa bilangan bulat yang harus
dikali faktor skala, dan waktunya berupa epoch (detik sejak 1970, UTC).

Catatan jujur: API ini tidak berbicara protokol Modbus secara langsung.
Pembacaan register Modbus TCP dilakukan oleh gateway (lihat proyek
Gerbang Telemetri), lalu gateway mengirim hasilnya dalam bentuk JSON ini.
Nilai register dikirim apa adanya, dan faktor skala diterapkan di sini.

Contoh payload:
{
  "device": "IED-PYL-04",
  "feeder": "PYL-04",
  "ts_epoch": 1795568400,
  "registers": {"40001": 2453, "40002": 2010, "40003": 845}
}
"""

from datetime import UTC, datetime

from ..schemas import CanonicalMeasurement
from .base import AdapterError, ParseResult, TelemetryAdapter

# register -> (besaran, faktor pengali)
REGISTER_MAP: dict[str, tuple[str, float]] = {
    "40001": ("current_a", 0.1),  # 2453 -> 245.3 A
    "40002": ("voltage_kv", 0.01),  # 2010 -> 20.10 kV
    "40003": ("power_mw", 0.01),  # 845  -> 8.45 MW
}


class ModbusAdapter(TelemetryAdapter):
    name = "modbus"

    def supports(self, payload: dict) -> bool:
        return isinstance(payload.get("registers"), dict) and "feeder" in payload

    def parse(self, payload: dict) -> ParseResult:
        try:
            measured_at = datetime.fromtimestamp(int(payload["ts_epoch"]), UTC).replace(tzinfo=None)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise AdapterError(f"ts_epoch tidak valid: {payload.get('ts_epoch')!r}") from exc

        registers = payload["registers"]
        missing = [reg for reg in REGISTER_MAP if reg not in registers]
        if missing:
            raise AdapterError(f"register tidak lengkap: {', '.join(missing)}")

        values = {quantity: round(int(registers[reg]) * scale, 3) for reg, (quantity, scale) in REGISTER_MAP.items()}
        measurement = CanonicalMeasurement(
            feeder_id=str(payload["feeder"]), measured_at=measured_at, source_format=self.name, **values
        )
        return ParseResult(measurements=[measurement])
