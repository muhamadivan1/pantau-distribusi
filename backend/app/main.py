"""Titik masuk aplikasi FastAPI.

Jalankan di laptop:
    uvicorn app.main:app --reload

Dokumentasi API interaktif tersedia di http://127.0.0.1:8000/docs
"""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, select

from . import db
from .config import Settings, get_settings
from .models import Feeder, Measurement
from .routers import alarms, feeders, outages, reports, telemetry
from .seed import seed_feeders, seed_history
from .services.ingestion import ingest
from .services.simulator import GridSimulator
from .timeutil import utcnow

VERSION = "1.1.0"
RETENTION_HOURS = 48  # mode demo: telemetri lebih lama dari ini dihapus agar database tidak membengkak
log = logging.getLogger("pantau")


def simulated_capacities(capacities: dict[str, float], settings: Settings) -> dict[str, float]:
    """Pilih penyulang yang disimulasikan. Daftar kosong berarti semua penyulang."""
    wanted = settings.simulated_feeder_list
    if not wanted:
        return capacities
    return {fid: cap for fid, cap in capacities.items() if fid in wanted}


async def run_simulator(settings: Settings) -> None:
    """Mode demo: kirim telemetri tiruan setiap demo_tick_seconds lewat jalur ingest."""
    with db.new_session() as session:
        capacities = {f.id: f.capacity_a for f in session.scalars(select(Feeder))}
    sim = GridSimulator(simulated_capacities(capacities, settings))
    tick = 0
    while True:
        await asyncio.sleep(settings.demo_tick_seconds)
        now = utcnow()
        try:
            with db.new_session() as session:
                for payload in sim.payloads_at(now):
                    ingest(session, payload, settings, now=now)
                tick += 1
                if tick % 720 == 0:  # kira-kira tiap jam pada tick 5 detik
                    session.execute(delete(Measurement).where(Measurement.measured_at < now - timedelta(hours=RETENTION_HOURS)))
                    session.commit()
        except Exception:  # simulator tidak boleh mematikan server
            log.exception("simulator gagal pada satu langkah")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.init_engine(settings.database_url)
        db.create_tables()
        task = None
        if settings.demo_mode:
            with db.new_session() as session:
                if seed_feeders(session):
                    seed_history(session, settings)
            if settings.demo_tick_seconds > 0:
                task = asyncio.create_task(run_simulator(settings))
        yield
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title=settings.app_name,
        version=VERSION,
        description=(
            "API pemantauan penyulang distribusi 20 kV: menerima telemetri dari berbagai format, "
            "membuat alarm dan catatan gangguan, serta menghitung SAIDI, SAIFI, dan CAIDI. "
            "Proyek portofolio dengan data fiktif."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.get("/api/v1/health", tags=["Sistem"], summary="Cek server hidup")
    def health():
        return {"status": "ok", "version": VERSION, "demo_mode": settings.demo_mode}

    for router in (feeders.router, telemetry.router, alarms.router, outages.router, reports.router):
        app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
