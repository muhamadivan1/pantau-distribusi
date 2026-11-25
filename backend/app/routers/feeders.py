"""Endpoint penyulang: daftar dengan status terkini, detail, dan riwayat ukur."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import get_session
from ..deps import get_app_settings
from ..models import Feeder, Measurement
from ..schemas import FeederOut, MeasurementOut
from ..services.status import classify
from ..timeutil import as_utc, utcnow

router = APIRouter(prefix="/feeders", tags=["Penyulang"])


def _latest_by_feeder(session: Session) -> dict[str, Measurement]:
    """Pengukuran terakhir setiap penyulang dalam satu query."""
    last = select(Measurement.feeder_id, func.max(Measurement.measured_at).label("t")).group_by(Measurement.feeder_id).subquery()
    rows = session.scalars(
        select(Measurement).join(last, (Measurement.feeder_id == last.c.feeder_id) & (Measurement.measured_at == last.c.t))
    )
    return {m.feeder_id: m for m in rows}


def _to_out(feeder: Feeder, latest: Measurement | None, settings: Settings) -> FeederOut:
    if latest is None:
        return FeederOut(**_feeder_fields(feeder), status="tanpa_data")
    status, pct = classify(latest.current_a, latest.voltage_kv, feeder.capacity_a, settings)
    measurement = MeasurementOut.model_validate(latest)
    measurement.measured_at = as_utc(measurement.measured_at)
    return FeederOut(**_feeder_fields(feeder), status=status, load_pct=pct, latest=measurement)


def _feeder_fields(f: Feeder) -> dict:
    return {"id": f.id, "name": f.name, "substation": f.substation, "area": f.area, "capacity_a": f.capacity_a, "customers": f.customers}


@router.get("", response_model=list[FeederOut], summary="Daftar penyulang beserta status terkini")
def list_feeders(session: Session = Depends(get_session), settings: Settings = Depends(get_app_settings)):
    latest = _latest_by_feeder(session)
    return [_to_out(f, latest.get(f.id), settings) for f in session.scalars(select(Feeder).order_by(Feeder.id))]


@router.get("/{feeder_id}", response_model=FeederOut, summary="Detail satu penyulang")
def get_feeder(feeder_id: str, session: Session = Depends(get_session), settings: Settings = Depends(get_app_settings)):
    feeder = session.get(Feeder, feeder_id)
    if feeder is None:
        raise HTTPException(404, f"penyulang {feeder_id} tidak ditemukan")
    latest = session.scalars(select(Measurement).where(Measurement.feeder_id == feeder_id).order_by(Measurement.measured_at.desc()).limit(1)).first()
    return _to_out(feeder, latest, settings)


@router.get("/{feeder_id}/measurements", response_model=list[MeasurementOut], summary="Riwayat pengukuran (untuk grafik)")
def list_measurements(
    feeder_id: str,
    hours: int = Query(24, ge=1, le=168, description="Rentang ke belakang, dalam jam"),
    session: Session = Depends(get_session),
):
    if session.get(Feeder, feeder_id) is None:
        raise HTTPException(404, f"penyulang {feeder_id} tidak ditemukan")
    since = utcnow() - timedelta(hours=hours)
    rows = session.scalars(
        select(Measurement).where(Measurement.feeder_id == feeder_id, Measurement.measured_at >= since).order_by(Measurement.measured_at)
    )
    out = []
    for m in rows:
        item = MeasurementOut.model_validate(m)
        item.measured_at = as_utc(item.measured_at)
        out.append(item)
    return out
