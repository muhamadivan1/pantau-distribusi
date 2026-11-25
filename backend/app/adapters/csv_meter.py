"""Adapter format "csv-meter".

Meniru ekspor berkas dari sistem pembacaan meter: teks CSV dengan pemisah
titik koma, angka desimal memakai koma (gaya Indonesia), dan waktu
"hari/bulan/tahun jam:menit:detik" dalam WIB.

Contoh payload:
{
  "content": "penyulang;waktu;arus_a;tegangan_kv;daya_mw\\nPYL-06;25/11/2026 08:00:00;210,5;20,1;6,9"
}
"""

import csv
import io
from datetime import datetime

from ..schemas import CanonicalMeasurement, RejectedRecord
from ..timeutil import WIB, to_db
from .base import AdapterError, ParseResult, TelemetryAdapter

HEADER = ["penyulang", "waktu", "arus_a", "tegangan_kv", "daya_mw"]


def _angka(teks: str) -> float:
    """'1.210,5' -> 1210.5 (format angka Indonesia)."""
    return float(teks.strip().replace(".", "").replace(",", "."))


class CsvMeterAdapter(TelemetryAdapter):
    name = "csv-meter"

    def supports(self, payload: dict) -> bool:
        content = payload.get("content")
        return isinstance(content, str) and content.lower().startswith("penyulang;")

    def parse(self, payload: dict) -> ParseResult:
        rows = list(csv.reader(io.StringIO(payload["content"].strip()), delimiter=";"))
        if [h.strip().lower() for h in rows[0]] != HEADER:
            raise AdapterError(f"header CSV harus: {';'.join(HEADER)}")

        result = ParseResult()
        for line_no, row in enumerate(rows[1:], start=2):
            if not any(cell.strip() for cell in row):
                continue  # lewati baris kosong
            feeder_id = row[0].strip() if row else None
            try:
                waktu = datetime.strptime(row[1].strip(), "%d/%m/%Y %H:%M:%S").replace(tzinfo=WIB)
                result.measurements.append(
                    CanonicalMeasurement(
                        feeder_id=feeder_id,
                        measured_at=to_db(waktu),
                        current_a=_angka(row[2]),
                        voltage_kv=_angka(row[3]),
                        power_mw=_angka(row[4]),
                        source_format=self.name,
                    )
                )
            except (IndexError, ValueError):
                result.rejected.append(RejectedRecord(feeder_id=feeder_id, reasons=[f"baris {line_no} tidak bisa dibaca"]))
        return result
