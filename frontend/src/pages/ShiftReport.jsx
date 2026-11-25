// Halaman Serah terima: ringkasan kejadian selama shift untuk operator berikutnya.

import { useState } from "react";

import { usePolling } from "../api/ApiContext.jsx";
import { ErrorNote, Loading } from "../components/common.jsx";
import { formatDateTime } from "../lib/format.js";
import { toPlainText } from "../lib/report.js";

const COUNT_LABELS = {
  alarm_waspada: "Alarm waspada",
  alarm_kritis: "Alarm kritis",
  alarm_padam: "Alarm padam",
  alarm_belum_dikonfirmasi: "Alarm aktif belum dikonfirmasi",
  gangguan_baru: "Gangguan baru",
  gangguan_pulih: "Gangguan pulih",
  gangguan_masih_terbuka: "Gangguan masih terbuka",
};

export default function ShiftReport() {
  const [hours, setHours] = useState(8);
  const [copied, setCopied] = useState(false);
  const report = usePolling((api) => api.shiftSummary(hours), [hours], 30000);
  const s = report.data;

  async function copy() {
    try {
      await navigator.clipboard.writeText(toPlainText(s));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <>
      <header className="page-head">
        <h1>Serah terima shift</h1>
        <p className="muted">Disusun dari data alarm, gangguan, dan beban terakhir dengan aturan tetap, sehingga setiap kalimat bisa ditelusuri ke datanya.</p>
      </header>

      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Lama shift">
          {[8, 12, 24].map((h) => (
            <button key={h} type="button" aria-pressed={hours === h} onClick={() => setHours(h)}>
              {h} jam
            </button>
          ))}
        </div>
        {s && (
          <button type="button" className="btn" onClick={copy}>
            {copied ? "Teks tersalin" : "Salin teks"}
          </button>
        )}
      </div>

      <ErrorNote message={report.error} />
      {report.loading || !s ? (
        <Loading />
      ) : (
        <div className="two-col">
          <section className="panel">
            <h2>{s.headline}</h2>
            <p className="muted small">
              {formatDateTime(s.start)} sampai {formatDateTime(s.end)}
            </p>
            {s.lines.length === 0 ? <p>Tidak ada catatan khusus.</p> : <ul className="report-lines">{s.lines.map((l) => <li key={l}>{l}</li>)}</ul>}
          </section>
          <section className="panel">
            <h2>Hitungan</h2>
            <dl className="count-list">
              {Object.entries(COUNT_LABELS).map(([key, label]) => (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd>{s.counts[key] ?? 0}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>
      )}
    </>
  );
}
