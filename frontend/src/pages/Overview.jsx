// Halaman Ringkasan: kondisi semua penyulang, alarm aktif, dan ringkasan shift.

import { Link } from "react-router-dom";

import { usePolling } from "../api/ApiContext.jsx";
import Busbar from "../components/Busbar.jsx";
import { ErrorNote, Loading, StatusLabel } from "../components/common.jsx";
import { formatAgo } from "../lib/format.js";
import { countByStatus, groupBySubstation, STATUS } from "../lib/status.js";

function StatusStrip({ feeders }) {
  const counts = countByStatus(feeders);
  return (
    <dl className="status-strip">
      {["normal", "waspada", "kritis", "padam"].map((key) => (
        <div key={key} className={`strip-item ${counts[key] && key !== "normal" ? `tone-${STATUS[key].tone}` : ""}`}>
          <dt>{STATUS[key].label}</dt>
          <dd>{counts[key]}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function Overview() {
  const feeders = usePolling((api) => api.feeders(), [], 5000);
  const alarms = usePolling((api) => api.alarms("open"), [], 5000);
  const summary = usePolling((api) => api.shiftSummary(8), [], 30000);

  return (
    <>
      <header className="page-head">
        <h1>Kondisi jaringan</h1>
        {feeders.data && <StatusStrip feeders={feeders.data} />}
      </header>
      <ErrorNote message={feeders.error} />

      <div className="overview">
        <div className="overview-main">
          {feeders.loading ? <Loading /> : groupBySubstation(feeders.data ?? []).map((g) => <Busbar key={g.substation} {...g} />)}
        </div>

        <aside className="overview-side">
          <section className="panel">
            <h2>Alarm aktif</h2>
            {alarms.data?.length === 0 && <p className="muted">Tidak ada alarm aktif.</p>}
            <ul className="alarm-list">
              {(alarms.data ?? []).slice(0, 6).map((a) => (
                <li key={a.id} className={a.acknowledged_at ? "is-acked" : ""}>
                  <StatusLabel status={a.level} />
                  <span>{a.message}</span>
                  <span className="muted small">
                    {formatAgo(a.raised_at)}
                    {a.acknowledged_by ? `, dikonfirmasi ${a.acknowledged_by}` : ", belum dikonfirmasi"}
                  </span>
                </li>
              ))}
            </ul>
            <Link to="/alarm" className="text-link">
              Buka semua alarm
            </Link>
          </section>

          <section className="panel">
            <h2>Shift 8 jam terakhir</h2>
            {summary.data && <p className="lead">{summary.data.headline}</p>}
            <Link to="/serah-terima" className="text-link">
              Buka ringkasan serah terima
            </Link>
          </section>
        </aside>
      </div>
    </>
  );
}
