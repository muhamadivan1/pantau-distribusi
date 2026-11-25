// Halaman Keandalan: SAIDI, SAIFI, CAIDI dan rinciannya per penyulang dan penyebab.

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { usePolling } from "../api/ApiContext.jsx";
import { ErrorNote, Loading } from "../components/common.jsx";
import { formatDateTime, formatNumber } from "../lib/format.js";

const PERIODS = [7, 30, 90];

function Breakdown({ title, rows }) {
  const data = rows.map((r) => ({ ...r, hours: r.customer_minutes / 60 }));
  return (
    <section className="panel">
      <h2>{title}</h2>
      <p className="muted small">Pelanggan-jam padam: lama padam dikali jumlah pelanggan yang terdampak.</p>
      {rows.length === 0 ? (
        <p className="muted">Tidak ada gangguan berkelanjutan di periode ini.</p>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(160, rows.length * 36)}>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
            <CartesianGrid stroke="#d3d5d0" horizontal={false} />
            <XAxis type="number" stroke="#61676d" fontSize={12} tickFormatter={(v) => formatNumber(v)} />
            <YAxis type="category" dataKey="label" width={170} stroke="#61676d" fontSize={12} />
            <Tooltip formatter={(v) => [`${formatNumber(v)} pelanggan-jam`, ""]} separator="" />
            <Bar dataKey="hours" fill="#3a3f44" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}

export default function Reliability() {
  const [days, setDays] = useState(30);
  const rel = usePolling((api) => api.reliability(days), [days], 60000);
  const r = rel.data;

  return (
    <>
      <header className="page-head">
        <h1>Keandalan</h1>
        <p className="muted">Indeks keandalan distribusi menurut definisi IEEE Std 1366, dihitung dari catatan gangguan.</p>
      </header>

      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Periode">
          {PERIODS.map((d) => (
            <button key={d} type="button" aria-pressed={days === d} onClick={() => setDays(d)}>
              {d} hari
            </button>
          ))}
        </div>
      </div>

      <ErrorNote message={rel.error} />
      {rel.loading || !r ? (
        <Loading />
      ) : (
        <>
          <p className="muted small">
            {formatDateTime(r.start)} sampai {formatDateTime(r.end)}. {formatNumber(r.customers_served)} pelanggan dilayani, {r.interruptions} gangguan berkelanjutan (lebih
            dari {r.sustained_threshold_minutes} menit).
          </p>
          <dl className="kpi-row">
            <div>
              <dt>SAIDI</dt>
              <dd>
                {formatNumber(r.saidi_minutes, 1)} <span className="unit">menit per pelanggan</span>
              </dd>
              <p className="formula">Jumlah (lama padam x pelanggan padam) dibagi jumlah pelanggan dilayani</p>
            </div>
            <div>
              <dt>SAIFI</dt>
              <dd>
                {formatNumber(r.saifi, 3)} <span className="unit">kali per pelanggan</span>
              </dd>
              <p className="formula">Jumlah pelanggan padam dibagi jumlah pelanggan dilayani</p>
            </div>
            <div>
              <dt>CAIDI</dt>
              <dd>
                {r.caidi_minutes === null ? "-" : formatNumber(r.caidi_minutes, 1)} <span className="unit">menit per gangguan</span>
              </dd>
              <p className="formula">SAIDI dibagi SAIFI, rata-rata lama pemulihan</p>
            </div>
          </dl>
          <div className="two-col">
            <Breakdown title="Per penyulang" rows={r.by_feeder} />
            <Breakdown title="Per penyebab" rows={r.by_cause} />
          </div>
        </>
      )}
    </>
  );
}
