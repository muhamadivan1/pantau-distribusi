// Komponen kecil yang dipakai di banyak halaman.

import { useApi } from "../api/ApiContext.jsx";
import { statusMeta, THRESHOLD, barWidth } from "../lib/status.js";

/** Label status dengan titik warna. Status normal sengaja tidak berwarna. */
export function StatusLabel({ status }) {
  const meta = statusMeta(status);
  return <span className={`status status-${meta.tone}`}>{meta.label}</span>;
}

/** Batang beban dengan penanda ambang waspada dan kritis. */
export function LoadBar({ loadPct, status }) {
  const tone = statusMeta(status).tone;
  return (
    <div className="loadbar" role="img" aria-label={`Beban ${loadPct ?? 0} persen`}>
      <div className={`loadbar-fill tone-${tone}`} style={{ width: `${barWidth(loadPct)}%` }} />
      <span className="loadbar-tick" style={{ left: `${barWidth(THRESHOLD.waspada)}%` }} title="Ambang waspada 80%" />
      <span className="loadbar-tick tick-crit" style={{ left: `${barWidth(THRESHOLD.kritis)}%` }} title="Ambang kritis 95%" />
    </div>
  );
}

/** Pemberitahuan sumber data: server sungguhan atau data contoh. */
export function ConnectionBanner() {
  const { mode, apiUrl } = useApi();
  if (mode === "live") return null;
  if (mode === "connecting") {
    return (
      <div className="banner banner-wait" role="status">
        Menghubungkan ke server. Server hosting gratis butuh sekitar satu menit untuk bangun setelah lama tidak dipakai.
      </div>
    );
  }
  return (
    <div className="banner" role="status">
      Mode demo: menampilkan data contoh fiktif di browser.
      {apiUrl ? " Server belum menjawab, aplikasi akan beralih otomatis saat server siap." : " Isi VITE_API_URL untuk terhubung ke backend."}
    </div>
  );
}

export function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <p className="error-note" role="alert">
      {message}
    </p>
  );
}

export function Loading() {
  return <p className="muted">Memuat data.</p>;
}
