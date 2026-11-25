"""Registry adapter: memilih adapter berdasarkan ISI payload.

Gateway tidak perlu menyebutkan formatnya. Registry mencoba setiap adapter
secara berurutan dan memakai yang pertama mengenali payload.
"""

from .base import TelemetryAdapter
from .csv_meter import CsvMeterAdapter
from .modbus import ModbusAdapter
from .rtu_ioa import RtuIoaAdapter


class AdapterRegistry:
    def __init__(self, adapters: list[TelemetryAdapter]):
        self.adapters = adapters

    def resolve(self, payload: dict) -> TelemetryAdapter | None:
        if not isinstance(payload, dict):
            return None
        return next((a for a in self.adapters if a.supports(payload)), None)

    @property
    def names(self) -> list[str]:
        return [a.name for a in self.adapters]


# Daftar adapter yang aktif. Tambahkan adapter baru di sini.
default_registry = AdapterRegistry([RtuIoaAdapter(), ModbusAdapter(), CsvMeterAdapter()])
