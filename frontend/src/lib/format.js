// Format angka dan waktu untuk tampilan.
// API mengirim waktu dalam UTC. Semua tampilan memakai WIB (Asia/Jakarta).

const TZ = "Asia/Jakarta";

/** "25 Nov 2026 14.05" dalam WIB. */
export function formatDateTime(iso) {
  if (!iso) return "-";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: TZ,
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

/** "14.05" dalam WIB, untuk sumbu grafik. */
export function formatTime(iso) {
  if (!iso) return "-";
  return new Intl.DateTimeFormat("id-ID", { timeZone: TZ, hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
}

/** Angka gaya Indonesia: 12.345,6 */
export function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("id-ID", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
}

/** Lama dalam menit menjadi "1 jam 25 menit" atau "40 menit". */
export function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return "-";
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h === 0) return `${m} menit`;
  return m === 0 ? `${h} jam` : `${h} jam ${m} menit`;
}

/** Selisih waktu yang mudah dibaca: "3 menit lalu". */
export function formatAgo(iso, now = new Date()) {
  if (!iso) return "-";
  const minutes = Math.round((now - new Date(iso)) / 60000);
  if (minutes < 1) return "baru saja";
  if (minutes < 60) return `${minutes} menit lalu`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} jam lalu`;
  return `${Math.floor(hours / 24)} hari lalu`;
}

/** Nilai untuk <input type="datetime-local"> dalam WIB, contoh "2026-11-25T14:05". */
export function toWibInputValue(date = new Date()) {
  const wib = new Date(date.getTime() + 7 * 3600 * 1000);
  return wib.toISOString().slice(0, 16);
}

/** Kebalikan toWibInputValue: isi input WIB menjadi ISO UTC untuk dikirim ke API. */
export function wibInputToIso(value) {
  if (!value) return null;
  return new Date(`${value}:00+07:00`).toISOString();
}
