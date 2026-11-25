// Halaman detail penyulang: angka terkini, grafik arus 24 jam, dan riwayat gangguan.

import { Link, useParams } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { usePolling } from "../api/ApiContext.jsx";
import { ErrorNote, Loading, StatusLabel } from "../components/common.jsx";
import { formatDateTime, formatDuration, formatNumber, formatTime } from "../lib/format.js";
import { CAUSES, THRESHOLD } from "../lib/status.js";

const INK = "#22262a";
const WARN = "#b67b00";
const CRIT = "#b8321f";

function ChartTooltip({ active, payload, unit }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="chart-tip">
      <div>{formatDateTime(p.payload.measured_at)}</div>
      <strong>
        {formatNumber(p.value, 1)} {unit}
      </strong>
    </div>
  );
}

export default function FeederDetail() {
  const { id } = useParams();
  const feeder = usePolling((api) => api.feeder(id), [id], 5000);
  const series = usePolling((api) => api.measurements(id, 24), [id], 15000);
  const outages = usePolling((api) => api.outages("all", id), [id], 30000);

  if (feeder.error) return <ErrorNote message={feeder.error} />;
  if (feeder.loading) return <Loading />;
  const f = feeder.data;
  const m = f.latest;

  return (
    <>
      <Link to="/" className="text-link">
        Kembali ke kondisi jaringan
      </Link>
      <header className="page-head">
        <h1>
          {f.id} {f.name} <StatusLabel status={f.status} />
        </h1>
        <p className="muted">
          {f.substation}, {f.area}. Melayani {formatNumber(f.customers)} pelanggan.
        </p>
      </header>

      <dl className="stat-row">
        <div>
          <dt>Beban</dt>
          <dd>{m ? `${formatNumber(f.load_pct, 1)}%` : "-"}</dd>
        </div>
        <div>
          <dt>Arus</dt>
          <dd>{m ? `${formatNumber(m.current_a, 1)} A` : "-"}</dd>
        </div>
        <div>
          <dt>Kapasitas</dt>
          <dd>{formatNumber(f.capacity_a)} A</dd>
        </div>
        <div>
          <dt>Tegangan</dt>
          <dd>{m ? `${formatNumber(m.voltage_kv, 2)} kV` : "-"}</dd>
        </div>
        <div>
          <dt>Daya</dt>
          <dd>{m ? `${formatNumber(m.power_mw, 2)} MW` : "-"}</dd>
        </div>
      </dl>

      <section className="panel">
        <h2>Arus 24 jam terakhir</h2>
        <p className="muted small">Garis putus-putus menandai ambang waspada ({THRESHOLD.waspada}%) dan kritis ({THRESHOLD.kritis}%) dari kapasitas.</p>
        <div className="chart">
          {series.loading ? (
            <Loading />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={series.data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="#d3d5d0" vertical={false} />
                <XAxis dataKey="measured_at" tickFormatter={formatTime} minTickGap={40} stroke="#61676d" fontSize={12} />
                <YAxis domain={[0, f.capacity_a * 1.1]} tickCount={6} allowDecimals={false} stroke="#61676d" fontSize={12} unit=" A" width={64} />
                <Tooltip content={<ChartTooltip unit="A" />} />
                <ReferenceLine y={(f.capacity_a * THRESHOLD.waspada) / 100} stroke={WARN} strokeDasharray="5 4" />
                <ReferenceLine y={(f.capacity_a * THRESHOLD.kritis) / 100} stroke={CRIT} strokeDasharray="5 4" />
                <Line type="monotone" dataKey="current_a" stroke={INK} strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </section>

      <section className="panel">
        <h2>Riwayat gangguan</h2>
        {outages.data?.length === 0 && <p className="muted">Belum ada gangguan tercatat.</p>}
        {outages.data?.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Mulai</th>
                <th>Lama</th>
                <th>Penyebab</th>
                <th className="num">Pelanggan</th>
              </tr>
            </thead>
            <tbody>
              {outages.data.slice(0, 10).map((o) => (
                <tr key={o.id}>
                  <td>{formatDateTime(o.started_at)}</td>
                  <td>{o.restored_at ? formatDuration(o.duration_minutes) : <StatusLabel status="padam" />}</td>
                  <td>{CAUSES[o.cause] ?? o.cause}</td>
                  <td className="num">{formatNumber(o.customers_affected)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
