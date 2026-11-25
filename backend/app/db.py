"""Koneksi database dengan SQLAlchemy 2.

Setiap request API mendapat satu Session lewat dependency get_session(),
lalu Session ditutup otomatis setelah request selesai.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Kelas induk semua tabel (lihat models.py)."""


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_engine(database_url: str) -> Engine:
    """Buat engine dan pabrik Session. Dipanggil sekali saat aplikasi start."""
    global _engine, _SessionLocal
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_engine(database_url, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def create_tables() -> None:
    """Buat semua tabel jika belum ada."""
    from . import models  # noqa: F401  (impor agar tabel terdaftar di Base)

    assert _engine is not None, "init_engine() belum dipanggil"
    Base.metadata.create_all(_engine)


def new_session() -> Session:
    """Session baru untuk dipakai di luar request (seed, simulator)."""
    assert _SessionLocal is not None, "init_engine() belum dipanggil"
    return _SessionLocal()


def get_session() -> Iterator[Session]:
    """Dependency FastAPI: satu Session per request."""
    session = new_session()
    try:
        yield session
    finally:
        session.close()
