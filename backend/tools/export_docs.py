"""Ekspor berkas pendukung dari kode:

1. docs/openapi.json
   Spesifikasi OpenAPI lengkap, bisa diimpor ke Postman atau dibuka di
   https://editor.swagger.io

2. frontend/src/api/demo-data.json
   Cuplikan respons API dengan data contoh. Dipakai frontend saat server
   backend tidak bisa dihubungi (mode demo di GitHub Pages), sehingga isi
   demo berasal dari logika backend yang sama, bukan angka karangan.

Cara pakai (dari folder backend):
    python tools/export_docs.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(database_url=f"sqlite:///{tmp}/export.db", demo_mode=True, demo_tick_seconds=0)
        with TestClient(create_app(settings)) as client:
            spec = client.get("/openapi.json").json()
            (ROOT / "docs" / "openapi.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            feeders = client.get("/api/v1/feeders").json()
            demo = {
                "generated_note": "Cuplikan dari backend dengan data contoh fiktif. Dibuat oleh backend/tools/export_docs.py",
                # Frontend menggeser semua waktu sebesar (sekarang - exported_at) agar demo terasa terkini.
                "exported_at": client.get("/api/v1/reports/shift-summary?hours=1").json()["end"],
                "feeders": feeders,
                "measurements": {f["id"]: client.get(f"/api/v1/feeders/{f['id']}/measurements?hours=24").json() for f in feeders},
                "alarms": client.get("/api/v1/alarms?status=all&limit=50").json(),
                "outages": client.get("/api/v1/outages?limit=100").json(),
                "reliability": {d: client.get(f"/api/v1/reliability?days={d}").json() for d in (7, 30, 90)},
                "shift_summary": client.get("/api/v1/reports/shift-summary?hours=8").json(),
            }
            target = ROOT / "frontend" / "src" / "api" / "demo-data.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(demo, ensure_ascii=False) + "\n", encoding="utf-8")

    print("dibuat: docs/openapi.json")
    print("dibuat: frontend/src/api/demo-data.json")


if __name__ == "__main__":
    main()
