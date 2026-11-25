// Diagram satu garis yang disederhanakan: busbar 20 kV satu gardu induk,
// dengan penyulang yang tersambung lewat pemutus (breaker).
//
//   GI Demo Utara  ══════════════════════════════   <- busbar
//                     │            │           ┆
//                     ■            ■           □     <- pemutus (□ = terbuka/padam)
//                  [Cempaka]   [Dahlia]   [Kenanga]  <- kartu penyulang

import { Link } from "react-router-dom";

import { formatAgo, formatNumber } from "../lib/format.js";
import { statusMeta } from "../lib/status.js";
import { LoadBar, StatusLabel } from "./common.jsx";

function FeederTile({ feeder }) {
  const tone = statusMeta(feeder.status).tone;
  const m = feeder.latest;
  const off = feeder.status === "padam";
  return (
    <li className={`feeder tone-${tone}`}>
      <span className={`feeder-drop ${off ? "is-open" : ""}`} aria-hidden="true" />
      <span className={`breaker ${off ? "is-open" : ""}`} title={off ? "Pemutus terbuka" : "Pemutus tertutup"} aria-hidden="true" />
      <Link className="feeder-card" to={`/penyulang/${feeder.id}`}>
        <span className="feeder-head">
          <span className="feeder-id">{feeder.id}</span>
          <span className="feeder-name">{feeder.name}</span>
          {feeder.status !== "normal" && <StatusLabel status={feeder.status} />}
        </span>
        <span className="feeder-load">
          <span className="big-number">{m ? formatNumber(feeder.load_pct, 0) : "-"}</span>
          <span className="unit">% beban</span>
        </span>
        <LoadBar loadPct={feeder.load_pct} status={feeder.status} />
        <span className="feeder-readings">
          <span>{m ? formatNumber(m.current_a, 0) : "-"} / {formatNumber(feeder.capacity_a)} A</span>
          <span>{m ? formatNumber(m.voltage_kv, 1) : "-"} kV</span>
          <span>{m ? formatNumber(m.power_mw, 1) : "-"} MW</span>
        </span>
        <span className="feeder-meta">{m ? `Data ${formatAgo(m.measured_at)} lewat ${m.source_format}` : "Belum ada data"}</span>
      </Link>
    </li>
  );
}

export default function Busbar({ substation, feeders }) {
  return (
    <section className="busbar-group" aria-label={substation}>
      <h2 className="busbar-title">
        {substation} <span className="muted">busbar 20 kV</span>
      </h2>
      <div className="busbar" aria-hidden="true" />
      <ul className="feeder-row">
        {feeders.map((f) => (
          <FeederTile key={f.id} feeder={f} />
        ))}
      </ul>
    </section>
  );
}
