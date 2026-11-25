"""Test endpoint HTTP dari request sampai database."""

from datetime import UTC, datetime, timedelta

from app.timeutil import utcnow
from tests.conftest import API_KEY

HEADERS = {"X-API-Key": API_KEY}


def now_csv_payload(feeder="PYL-06", current="150,00", voltage="20,10"):
    """Payload CSV dengan waktu sekarang dalam WIB."""
    wib = (datetime.now(UTC) + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
    return {"content": f"penyulang;waktu;arus_a;tegangan_kv;daya_mw\n{feeder};{wib};{current};{voltage};4,50"}


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok"


def test_telemetri_wajib_api_key(client):
    assert client.post("/api/v1/telemetry", json=now_csv_payload()).status_code == 401
    assert client.post("/api/v1/telemetry", json=now_csv_payload(), headers={"X-API-Key": "salah"}).status_code == 401


def test_telemetri_format_asing_422(client):
    r = client.post("/api/v1/telemetry", json={"apa": "ini"}, headers=HEADERS)
    assert r.status_code == 422
    assert "format tidak dikenali" in r.json()["detail"]


def test_telemetri_tersimpan_dan_status_penyulang_berubah(client):
    r = client.post("/api/v1/telemetry", json=now_csv_payload(current="290,00"), headers=HEADERS)
    assert r.status_code == 201
    assert r.json()["adapter"] == "csv-meter"
    assert r.json()["stored"] == 1

    feeder = client.get("/api/v1/feeders/PYL-06").json()  # kapasitas 300 A, 290 A = 96,7%
    assert feeder["status"] == "kritis"
    assert feeder["load_pct"] == 96.7
    assert feeder["latest"]["measured_at"].endswith("Z")  # waktu dikirim dalam UTC


def test_penyulang_tanpa_data_dan_404(client):
    feeders = client.get("/api/v1/feeders").json()
    assert len(feeders) == 6
    assert {f["status"] for f in feeders} == {"tanpa_data"}
    assert client.get("/api/v1/feeders/PYL-99").status_code == 404


def test_alarm_bisa_dikonfirmasi_sekali(client):
    client.post("/api/v1/telemetry", json=now_csv_payload(current="290,00"), headers=HEADERS)
    alarm = client.get("/api/v1/alarms").json()[0]
    first = client.post(f"/api/v1/alarms/{alarm['id']}/acknowledge", json={"by": "Operator A"}).json()
    second = client.post(f"/api/v1/alarms/{alarm['id']}/acknowledge", json={"by": "Operator B"}).json()
    assert first["acknowledged_by"] == second["acknowledged_by"] == "Operator A"


def test_catat_gangguan_manual_dan_lengkapi_penyebab(client):
    start = (datetime.now(UTC) - timedelta(minutes=50)).isoformat()
    r = client.post("/api/v1/outages", json={"feeder_id": "PYL-01", "started_at": start})
    assert r.status_code == 201
    outage = r.json()
    assert outage["customers_affected"] == 8200 and outage["cause"] == "belum_diketahui"

    # Gangguan kedua di penyulang yang sama ditolak selama yang pertama belum pulih.
    assert client.post("/api/v1/outages", json={"feeder_id": "PYL-01", "started_at": start}).status_code == 409

    restored = datetime.now(UTC).isoformat()
    r = client.patch(f"/api/v1/outages/{outage['id']}", json={"cause": "pohon", "restored_at": restored})
    assert r.status_code == 200
    assert r.json()["cause"] == "pohon"
    assert 49 <= r.json()["duration_minutes"] <= 51


def test_waktu_pulih_sebelum_mulai_ditolak(client):
    start = datetime.now(UTC) - timedelta(hours=1)
    body = {"feeder_id": "PYL-02", "started_at": start.isoformat(), "restored_at": (start - timedelta(minutes=5)).isoformat()}
    assert client.post("/api/v1/outages", json=body).status_code == 422


def test_penyebab_tidak_dikenal_ditolak(client):
    body = {"feeder_id": "PYL-02", "started_at": utcnow().isoformat(), "cause": "alien"}
    assert client.post("/api/v1/outages", json=body).status_code == 422


def test_laporan_keandalan_dan_ringkasan_shift(client):
    start = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    restored = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    client.post("/api/v1/outages", json={"feeder_id": "PYL-03", "started_at": start, "restored_at": restored, "cause": "hewan"})

    rel = client.get("/api/v1/reliability?days=7").json()
    assert rel["interruptions"] == 1
    assert rel["saifi"] == round(1450 / 42000, 4)

    summary = client.get("/api/v1/reports/shift-summary?hours=8").json()
    assert summary["counts"]["gangguan_pulih"] == 1
    assert summary["headline"] == "Ada gangguan selama shift, semuanya sudah pulih."
    assert any("PYL-03 padam 60 menit" in line for line in summary["lines"])


def test_rentang_keandalan_terbalik_ditolak(client):
    r = client.get("/api/v1/reliability", params={"start": "2026-11-10T00:00:00Z", "end": "2026-11-01T00:00:00Z"})
    assert r.status_code == 422


def test_dokumentasi_openapi_lengkap(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ["/api/v1/telemetry", "/api/v1/feeders", "/api/v1/alarms", "/api/v1/outages", "/api/v1/reliability", "/api/v1/reports/shift-summary"]:
        assert path in paths


def test_ringkasan_shift_tanpa_kejadian(client):
    summary = client.get("/api/v1/reports/shift-summary?hours=8").json()
    assert summary["headline"] == "Shift berjalan normal tanpa gangguan."
    assert summary["counts"]["gangguan_baru"] == 0
