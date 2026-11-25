"""Alat bantu waktu.

Aturan proyek ini:
- Database menyimpan waktu UTC tanpa zona (naive), karena SQLite tidak
  menyimpan zona waktu.
- API selalu mengirim waktu dengan zona UTC (akhiran Z atau +00:00).
- Frontend mengubahnya ke WIB saat ditampilkan.
"""

from datetime import UTC, datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7), name="WIB")


def utcnow() -> datetime:
    """Waktu sekarang dalam UTC tanpa zona, siap disimpan ke database."""
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)


def to_db(dt: datetime) -> datetime:
    """Ubah waktu apa pun ke UTC tanpa zona. Waktu tanpa zona dianggap sudah UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt.replace(microsecond=0)


def as_utc(dt: datetime | None) -> datetime | None:
    """Tempelkan zona UTC ke waktu dari database sebelum dikirim lewat API."""
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
