"""Simulator gateway: kirim telemetri tiruan ke API lewat HTTP.

Berguna untuk mencoba API yang berjalan dengan DEMO_MODE=false, atau untuk
menunjukkan bahwa endpoint /telemetry bekerja seperti dipanggil gateway sungguhan.

Cara pakai (dari folder backend):
    python tools/simulate.py --url http://127.0.0.1:8000 --key dev-key-ganti-saya
    python tools/simulate.py --trip PYL-02          # paksa PYL-02 padam beberapa langkah
"""

import argparse
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agar "app" bisa diimpor

from app.seed import FEEDERS  # noqa: E402
from app.services.simulator import GridSimulator  # noqa: E402
from app.timeutil import utcnow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Kirim telemetri tiruan ke Pantau Distribusi API")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--key", default="dev-key-ganti-saya", help="nilai header X-API-Key")
    parser.add_argument("--interval", type=float, default=5, help="jeda antar kiriman, detik")
    parser.add_argument("--count", type=int, default=0, help="jumlah langkah, 0 = terus berjalan")
    parser.add_argument("--trip", default="", help="paksa satu penyulang padam, contoh PYL-02")
    args = parser.parse_args()

    sim = GridSimulator({fid: cap for fid, _n, _g, _a, cap, _c in FEEDERS})
    if args.trip:
        sim._trip_left[args.trip] = 6  # padam 6 langkah lalu pulih sendiri

    step = 0
    with httpx.Client(base_url=args.url, headers={"X-API-Key": args.key}, timeout=10) as client:
        while args.count == 0 or step < args.count:
            for payload in sim.payloads_at(utcnow()):
                r = client.post("/api/v1/telemetry", json=payload)
                body = r.json()
                if r.status_code == 401:
                    sys.exit("Ditolak: periksa nilai --key (harus sama dengan API_KEY di server).")
                if r.status_code == 201:
                    print(f"{body['adapter']:<10} tersimpan={body['stored']} ditolak={len(body['rejected'])} alarm={body['alarms_raised']} gangguan_baru={body['outages_opened']}")
                else:
                    print(f"GAGAL {r.status_code}: {body}")
            step += 1
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
