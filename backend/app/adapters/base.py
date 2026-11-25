"""Kontrak bersama untuk semua adapter telemetri.

Ide utamanya sama dengan tesis Flowbeat: setiap sumber data punya format
sendiri, tetapi inti sistem hanya mengenal satu bentuk, yaitu
CanonicalMeasurement. Adapter-lah yang menerjemahkan.

Menambah sumber data baru = menambah satu kelas adapter + mendaftarkannya
di registry.py. Kode ingestion, alarm, dan laporan tidak perlu diubah.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..schemas import CanonicalMeasurement, RejectedRecord


class AdapterError(ValueError):
    """Payload dikenali formatnya tetapi isinya tidak bisa dibaca sama sekali."""


@dataclass
class ParseResult:
    measurements: list[CanonicalMeasurement] = field(default_factory=list)
    rejected: list[RejectedRecord] = field(default_factory=list)


class TelemetryAdapter(ABC):
    #: Nama format, disimpan di kolom source_format.
    name: str = "base"

    @abstractmethod
    def supports(self, payload: dict) -> bool:
        """True jika adapter ini mengenali bentuk payload (content-based routing)."""

    @abstractmethod
    def parse(self, payload: dict) -> ParseResult:
        """Ubah payload mentah menjadi daftar CanonicalMeasurement."""
