"""Endpoint laporan: indeks keandalan dan ringkasan serah terima shift."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import get_session
from ..deps import get_app_settings
from ..schemas import ReliabilityOut, ShiftSummaryOut
from ..services import reliability, shift_report
from ..timeutil import to_db, utcnow

router = APIRouter(tags=["Laporan"])


@router.get("/reliability", response_model=ReliabilityOut, summary="SAIDI, SAIFI, dan CAIDI untuk satu periode")
def get_reliability(
    days: int = Query(30, ge=1, le=366, description="Dipakai jika start dan end kosong"),
    start: datetime | None = Query(None, description="Awal periode (ISO 8601)"),
    end: datetime | None = Query(None, description="Akhir periode (ISO 8601)"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
):
    now = utcnow()
    end_db = to_db(end) if end else now
    start_db = to_db(start) if start else end_db - timedelta(days=days)
    if start_db >= end_db:
        raise HTTPException(422, "start harus sebelum end")
    return reliability.compute(session, start_db, end_db, now, settings)


@router.get("/reports/shift-summary", response_model=ShiftSummaryOut, summary="Ringkasan untuk serah terima shift operator")
def get_shift_summary(
    hours: int = Query(8, ge=1, le=24),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
):
    return shift_report.build(session, hours, utcnow(), settings)
