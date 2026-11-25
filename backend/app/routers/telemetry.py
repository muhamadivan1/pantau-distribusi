"""Endpoint penerimaan telemetri dari gateway (dilindungi X-API-Key)."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..adapters.base import AdapterError
from ..config import Settings
from ..db import get_session
from ..deps import get_app_settings, require_api_key
from ..schemas import IngestResult
from ..services.ingestion import UnknownFormatError, ingest

router = APIRouter(prefix="/telemetry", tags=["Telemetri"])

EXAMPLES = {
    "rtu-ioa": {
        "summary": "RTU gardu induk (titik ukur IOA)",
        "value": {
            "rtu": "RTU-GI-DEMO-UTARA",
            "timestamp": "2026-11-25T08:00:00+07:00",
            "points": [{"ioa": 1001, "value": 245.3}, {"ioa": 1002, "value": 20.1}, {"ioa": 1003, "value": 7.69}],
        },
    },
    "modbus": {
        "summary": "IED penyulang (register Modbus)",
        "value": {"device": "IED-PYL-04", "feeder": "PYL-04", "ts_epoch": 1795568400, "registers": {"40001": 2453, "40002": 2010, "40003": 769}},
    },
    "csv-meter": {
        "summary": "Ekspor CSV sistem meter",
        "value": {"content": "penyulang;waktu;arus_a;tegangan_kv;daya_mw\nPYL-06;25/11/2026 08:00:00;210,50;20,10;6,59"},
    },
}


@router.post(
    "",
    response_model=IngestResult,
    status_code=201,
    dependencies=[Depends(require_api_key)],
    summary="Kirim telemetri dalam format apa pun yang didukung",
    description="Format dikenali otomatis dari isi payload. Rekaman yang ditolak tetap dilaporkan beserta alasannya.",
)
def post_telemetry(
    payload: dict[str, Any] = Body(..., openapi_examples=EXAMPLES),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
):
    try:
        return ingest(session, payload, settings)
    except (UnknownFormatError, AdapterError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
