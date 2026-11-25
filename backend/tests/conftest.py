"""Perlengkapan bersama untuk test.

Setiap test mendapat database SQLite baru di folder sementara, sehingga
hasil test tidak saling memengaruhi dan tidak menyentuh database asli.
"""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.config import Settings
from app.main import create_app
from app.seed import seed_feeders

API_KEY = "test-key"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", api_key=API_KEY, demo_mode=False)


@pytest.fixture
def session(settings):
    """Session database dengan 6 penyulang contoh, tanpa telemetri."""
    db.init_engine(settings.database_url)
    db.create_tables()
    with db.new_session() as s:
        seed_feeders(s)
        yield s


@pytest.fixture
def client(settings):
    """Klien HTTP untuk menguji endpoint lewat aplikasi lengkap."""
    app = create_app(settings)
    with TestClient(app) as c:
        with db.new_session() as s:
            seed_feeders(s)
        yield c
