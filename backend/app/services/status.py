"""Menentukan status penyulang dari satu pengukuran.

Urutan pemeriksaan:
1. Tegangan di bawah padam_voltage_kv        -> padam
2. Beban >= threshold_kritis_pct dari kapasitas -> kritis
3. Beban >= threshold_waspada_pct              -> waspada
4. Selain itu                                  -> normal
"""

from ..config import Settings

LEVEL_ORDER = {"normal": 0, "waspada": 1, "kritis": 2, "padam": 3}


def load_percent(current_a: float, capacity_a: float) -> float:
    """Persentase beban terhadap kapasitas, dibulatkan satu angka di belakang koma."""
    if capacity_a <= 0:
        return 0.0
    return round(current_a / capacity_a * 100, 1)


def classify(current_a: float, voltage_kv: float, capacity_a: float, settings: Settings) -> tuple[str, float]:
    """Kembalikan (status, persen_beban)."""
    pct = load_percent(current_a, capacity_a)
    if voltage_kv < settings.padam_voltage_kv:
        return "padam", pct
    if pct >= settings.threshold_kritis_pct:
        return "kritis", pct
    if pct >= settings.threshold_waspada_pct:
        return "waspada", pct
    return "normal", pct
