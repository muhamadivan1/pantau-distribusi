"""Endpoint alarm: daftar dan konfirmasi (acknowledge) oleh operator."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Alarm
from ..schemas import AcknowledgeIn, AlarmOut
from ..timeutil import as_utc, utcnow

router = APIRouter(prefix="/alarms", tags=["Alarm"])


def _out(alarm: Alarm) -> AlarmOut:
    out = AlarmOut.model_validate(alarm)
    for field in ("raised_at", "acknowledged_at", "cleared_at"):
        setattr(out, field, as_utc(getattr(out, field)))
    return out


@router.get("", response_model=list[AlarmOut], summary="Daftar alarm, terbaru di atas")
def list_alarms(
    status: Literal["open", "all"] = Query("open", description="open = belum selesai, all = termasuk yang sudah normal"),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    stmt = select(Alarm).order_by(Alarm.raised_at.desc()).limit(limit)
    if status == "open":
        stmt = stmt.where(Alarm.cleared_at.is_(None))
    return [_out(a) for a in session.scalars(stmt)]


@router.post("/{alarm_id}/acknowledge", response_model=AlarmOut, summary="Konfirmasi alarm sudah dilihat operator")
def acknowledge(alarm_id: int, body: AcknowledgeIn, session: Session = Depends(get_session)):
    alarm = session.get(Alarm, alarm_id)
    if alarm is None:
        raise HTTPException(404, f"alarm {alarm_id} tidak ditemukan")
    if alarm.acknowledged_at is None:  # konfirmasi kedua tidak menimpa yang pertama
        alarm.acknowledged_at = utcnow()
        alarm.acknowledged_by = body.by
        session.commit()
    return _out(alarm)
