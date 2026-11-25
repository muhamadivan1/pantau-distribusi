"""Pengaturan aplikasi.

Semua nilai bisa diganti lewat environment variable (atau berkas .env),
sehingga kode yang sama bisa jalan di laptop, di test, dan di server hosting
tanpa diubah.

Contoh:
    DATABASE_URL=sqlite:///./pantau.db
    API_KEY=rahasia-gateway
    DEMO_MODE=true
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Nama yang tampil di dokumentasi API (/docs).
    app_name: str = "Pantau Distribusi API"

    # SQLite cukup untuk demo. Ganti dengan PostgreSQL untuk produksi,
    # misalnya postgresql+psycopg://user:pass@host/db
    database_url: str = "sqlite:///./pantau.db"

    # Kunci yang wajib dikirim gateway saat mengirim telemetri (header X-API-Key).
    api_key: str = "dev-key-ganti-saya"

    # Mode demo: isi data contoh saat start dan jalankan simulator telemetri.
    demo_mode: bool = True
    demo_tick_seconds: float = 5.0

    # Penyulang yang datanya dibuat simulator internal (dipisah koma).
    # Kosong berarti semua penyulang. Isi misalnya "PYL-01,PYL-02,PYL-03,PYL-06"
    # bila PYL-04 dan PYL-05 sudah dikirim oleh Gerbang Telemetri (gateway Modbus),
    # supaya data kedua penyulang itu tidak dobel.
    demo_simulated_feeders: str = ""

    # Alamat frontend yang boleh memanggil API (dipisah koma).
    cors_origins: str = "http://localhost:5173,https://muhamadivan1.github.io"

    # Ambang status beban, dalam persen dari kapasitas arus penyulang.
    # Ini contoh ambang untuk portofolio, bukan angka resmi perusahaan mana pun.
    threshold_waspada_pct: float = 80.0
    threshold_kritis_pct: float = 95.0

    # Di bawah tegangan ini (kV) penyulang dianggap padam.
    padam_voltage_kv: float = 2.0

    # Gangguan yang lebih pendek dari ini tidak dihitung di SAIDI/SAIFI
    # (IEEE 1366 menghitung gangguan berkelanjutan, lebih dari 5 menit).
    sustained_minutes: float = 5.0

    @property
    def simulated_feeder_list(self) -> list[str]:
        return [f.strip().upper() for f in self.demo_simulated_feeders.split(",") if f.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Satu objek Settings untuk seluruh aplikasi (dibaca sekali)."""
    return Settings()
