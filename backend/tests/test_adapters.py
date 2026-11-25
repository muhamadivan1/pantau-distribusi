"""Test adapter: tiga format berbeda harus menghasilkan bentuk kanonik yang sama."""

from datetime import UTC, datetime

import pytest

from app.adapters.base import AdapterError
from app.adapters.csv_meter import CsvMeterAdapter
from app.adapters.modbus import ModbusAdapter
from app.adapters.registry import default_registry
from app.adapters.rtu_ioa import RtuIoaAdapter

# 25 Nov 2026 08:00 WIB = 01:00 UTC
UTC_TIME = datetime(2026, 11, 25, 1, 0, 0)

RTU = {
    "rtu": "RTU-GI-DEMO-UTARA",
    "timestamp": "2026-11-25T08:00:00+07:00",
    "points": [{"ioa": 1001, "value": 245.3}, {"ioa": 1002, "value": 20.1}, {"ioa": 1003, "value": 7.69}],
}
MODBUS = {
    "device": "IED-PYL-01",
    "feeder": "PYL-01",
    "ts_epoch": int(UTC_TIME.replace(tzinfo=UTC).timestamp()),  # epoch selalu UTC
    "registers": {"40001": 2453, "40002": 2010, "40003": 769},
}
CSV = {"content": "penyulang;waktu;arus_a;tegangan_kv;daya_mw\nPYL-01;25/11/2026 08:00:00;245,30;20,10;7,69"}


def test_registry_memilih_adapter_dari_isi_payload():
    assert default_registry.resolve(RTU).name == "rtu-ioa"
    assert default_registry.resolve(MODBUS).name == "modbus"
    assert default_registry.resolve(CSV).name == "csv-meter"
    assert default_registry.resolve({"foo": "bar"}) is None
    assert default_registry.resolve(["bukan", "objek"]) is None


def test_tiga_format_menghasilkan_rekaman_kanonik_yang_sama():
    hasil = [adapter.parse(p).measurements[0] for adapter, p in ((RtuIoaAdapter(), RTU), (ModbusAdapter(), MODBUS), (CsvMeterAdapter(), CSV))]
    pembanding = [m.model_dump(exclude={"source_format"}) for m in hasil]
    assert pembanding[0] == pembanding[1] == pembanding[2]
    assert hasil[0].measured_at == UTC_TIME  # WIB sudah diubah ke UTC
    assert {m.source_format for m in hasil} == {"rtu-ioa", "modbus", "csv-meter"}


def test_rtu_titik_tidak_lengkap_dan_ioa_asing_ditolak():
    payload = {**RTU, "points": [{"ioa": 1001, "value": 200}, {"ioa": 9999, "value": 1}]}
    result = RtuIoaAdapter().parse(payload)
    assert result.measurements == []
    alasan = " ".join(r for rej in result.rejected for r in rej.reasons)
    assert "IOA 9999 tidak terdaftar" in alasan
    assert "tidak lengkap" in alasan


def test_rtu_timestamp_rusak_menimbulkan_error():
    with pytest.raises(AdapterError):
        RtuIoaAdapter().parse({**RTU, "timestamp": "kemarin sore"})


def test_modbus_menerapkan_faktor_skala():
    m = ModbusAdapter().parse(MODBUS).measurements[0]
    assert (m.current_a, m.voltage_kv, m.power_mw) == (245.3, 20.1, 7.69)


def test_modbus_register_kurang_menimbulkan_error():
    with pytest.raises(AdapterError):
        ModbusAdapter().parse({**MODBUS, "registers": {"40001": 100}})


def test_csv_angka_ribuan_dan_desimal_koma():
    payload = {"content": "penyulang;waktu;arus_a;tegangan_kv;daya_mw\nPYL-03;25/11/2026 08:00:00;1.010,5;20,1;29,0"}
    m = CsvMeterAdapter().parse(payload).measurements[0]
    assert m.current_a == 1010.5


def test_csv_baris_rusak_ditolak_baris_lain_tetap_terbaca():
    payload = {"content": CSV["content"] + "\nPYL-02;tanggal salah;1;2;3"}
    result = CsvMeterAdapter().parse(payload)
    assert len(result.measurements) == 1
    assert result.rejected[0].reasons == ["baris 3 tidak bisa dibaca"]


def test_csv_header_salah_menimbulkan_error():
    with pytest.raises(AdapterError):
        CsvMeterAdapter().parse({"content": "penyulang;jam;arus\nPYL-01;08:00;10"})
