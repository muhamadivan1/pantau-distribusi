"""Endpoint gangguan: daftar, catat manual, dan lengkapi penyebab atau waktu pulih."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Feeder, Outage
from ..schemas import OutageCreate, OutageOut, OutageUpdate
from ..services.events import open_outage
from ..timeutil import as_utc, to_db

router = APIRouter(prefix="/outages", tags=["Gangguan"])


def _out(o: Outage) -> OutageOut:
    out = OutageOut.model_validate(o)
    out.started_at = as_utc(o.started_at)
    out.restored_at = as_utc(o.restored_at)
    if o.restored_at:
        out.duration_minutes = round((o.restored_at - o.started_at).total_seconds() / 60, 1)
    return out


@router.get("", response_model=list[OutageOut], summary="Daftar gangguan, terbaru di atas")
def list_outages(
    status: Literal["open", "closed", "all"] = Query("all"),
    feeder_id: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    stmt = select(Outage).order_by(Outage.started_at.desc()).limit(limit)
    if status == "open":
        stmt = stmt.where(Outage.restored_at.is_(None))
    elif status == "closed":
        stmt = stmt.where(Outage.restored_at.is_not(None))
    if feeder_id:
        stmt = stmt.where(Outage.feeder_id == feeder_id)
    return [_out(o) for o in session.scalars(stmt)]


@router.post("", response_model=OutageOut, status_code=201, summary="Catat gangguan secara manual")
def create_outage(body: OutageCreate, session: Session = Depends(get_session)):
    feeder = session.get(Feeder, body.feeder_id)
    if feeder is None:
        raise HTTPException(404, f"penyulang {body.feeder_id} tidak ditemukan")
    started = to_db(body.started_at)
    restored = to_db(body.restored_at) if body.restored_at else None
    if restored and restored <= started:
        raise HTTPException(422, "waktu pulih harus setelah waktu mulai")
    if restored is None and open_outage(session, feeder.id):
        raise HTTPException(409, f"{feeder.id} masih punya gangguan yang belum pulih")

    outage = Outage(
        feeder_id=feeder.id,
        started_at=started,
        restored_at=restored,
        cause=body.cause,
        customers_affected=feeder.customers if body.customers_affected is None else body.customers_affected,
        notes=body.notes,
        auto_detected=False,
    )
    session.add(outage)
    session.commit()
    return _out(outage)


@router.patch("/{outage_id}", response_model=OutageOut, summary="Perbarui penyebab, jumlah pelanggan, catatan, atau waktu pulih")
def update_outage(outage_id: int, body: OutageUpdate, session: Session = Depends(get_session)):
    outage = session.get(Outage, outage_id)
    if outage is None:
        raise HTTPException(404, f"gangguan {outage_id} tidak ditemukan")
    changes = body.model_dump(exclude_unset=True)
    if "restored_at" in changes and changes["restored_at"] is not None:
        changes["restored_at"] = to_db(changes["restored_at"])
        if changes["restored_at"] <= outage.started_at:
            raise HTTPException(422, "waktu pulih harus setelah waktu mulai")
    for key, value in changes.items():
        setattr(outage, key, value)
    session.commit()
    return _out(outage)
