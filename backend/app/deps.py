"""Dependency FastAPI yang dipakai bersama oleh semua router."""

from fastapi import Header, HTTPException, Request, status

from .config import Settings


def get_app_settings(request: Request) -> Settings:
    """Pengaturan milik aplikasi yang sedang berjalan (bisa diganti saat test)."""
    return request.app.state.settings


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    """Tolak permintaan tanpa header X-API-Key yang benar."""
    settings: Settings = request.app.state.settings
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key tidak ada atau salah")
