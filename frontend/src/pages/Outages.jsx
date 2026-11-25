// Halaman Gangguan: daftar gangguan, catat gangguan manual, dan lengkapi
// penyebab atau waktu pulih untuk gangguan yang dibuka otomatis.

import { useState } from "react";

import { useApi, usePolling } from "../api/ApiContext.jsx";
import { ErrorNote, Loading, StatusLabel } from "../components/common.jsx";
import { formatDateTime, formatDuration, formatNumber, toWibInputValue, wibInputToIso } from "../lib/format.js";
import { CAUSES } from "../lib/status.js";

function CauseSelect({ value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {Object.entries(CAUSES).map(([key, label]) => (
        <option key={key} value={key}>
          {label}
        </option>
      ))}
    </select>
  );
}

/** Formulir catat gangguan baru. */
function NewOutageForm({ feeders, onSaved, onCancel }) {
  const { api } = useApi();
  const [form, setForm] = useState({ feeder_id: feeders[0]?.id ?? "", started_at: toWibInputValue(), restored_at: "", cause: "belum_diketahui", notes: "" });
  const [error, setError] = useState(null);
  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(event) {
    event.preventDefault();
    try {
      await api.createOutage({
        feeder_id: form.feeder_id,
        started_at: wibInputToIso(form.started_at),
        restored_at: wibInputToIso(form.restored_at),
        cause: form.cause,
        notes: form.notes,
      });
      onSaved();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="panel form-grid" onSubmit={submit}>
      <h2>Catat gangguan</h2>
      <label>
        Penyulang
        <select value={form.feeder_id} onChange={(e) => set("feeder_id")(e.target.value)}>
          {feeders.map((f) => (
            <option key={f.id} value={f.id}>
              {f.id} {f.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Mulai padam (WIB)
        <input type="datetime-local" required value={form.started_at} onChange={(e) => set("started_at")(e.target.value)} />
      </label>
      <label>
        Pulih (WIB, kosongkan jika belum)
        <input type="datetime-local" value={form.restored_at} onChange={(e) => set("restored_at")(e.target.value)} />
      </label>
      <label>
        Penyebab
        <CauseSelect value={form.cause} onChange={set("cause")} />
      </label>
      <label className="span-2">
        Catatan
        <input value={form.notes} onChange={(e) => set("notes")(e.target.value)} placeholder="Contoh: ranting menyentuh jaringan dekat tiang 12" />
      </label>
      <ErrorNote message={error} />
      <div className="actions span-2">
        <button type="submit" className="btn btn-primary">
          Simpan gangguan
        </button>
        <button type="button" className="btn" onClick={onCancel}>
          Batal
        </button>
      </div>
    </form>
  );
}

/** Baris edit: lengkapi penyebab dan waktu pulih. */
function EditRow({ outage, onSaved, onCancel }) {
  const { api } = useApi();
  const [cause, setCause] = useState(outage.cause);
  const [restored, setRestored] = useState(outage.restored_at ? toWibInputValue(new Date(outage.restored_at)) : "");
  const [error, setError] = useState(null);

  async function save() {
    try {
      const changes = { cause };
      if (restored) changes.restored_at = wibInputToIso(restored);
      await api.updateOutage(outage.id, changes);
      onSaved();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <tr className="edit-row">
      <td colSpan={6}>
        <div className="edit-inline">
          <label>
            Penyebab <CauseSelect value={cause} onChange={setCause} />
          </label>
          <label>
            Pulih (WIB) <input type="datetime-local" value={restored} onChange={(e) => setRestored(e.target.value)} />
          </label>
          <button type="button" className="btn btn-primary btn-small" onClick={save}>
            Simpan perubahan
          </button>
          <button type="button" className="btn btn-small" onClick={onCancel}>
            Batal
          </button>
          <ErrorNote message={error} />
        </div>
      </td>
    </tr>
  );
}

export default function Outages() {
  const [filter, setFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const outages = usePolling((api) => api.outages(filter), [filter], 10000);
  const feeders = usePolling((api) => api.feeders(), [], 0);
  const names = Object.fromEntries((feeders.data ?? []).map((f) => [f.id, f.name]));

  return (
    <>
      <header className="page-head">
        <h1>Gangguan</h1>
        <p className="muted">Gangguan dibuka otomatis saat tegangan penyulang hilang. Operator melengkapi penyebabnya untuk laporan keandalan.</p>
      </header>

      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Saring gangguan">
          {[
            ["all", "Semua"],
            ["open", "Belum pulih"],
            ["closed", "Sudah pulih"],
          ].map(([key, label]) => (
            <button key={key} type="button" aria-pressed={filter === key} onClick={() => setFilter(key)}>
              {label}
            </button>
          ))}
        </div>
        {!showForm && (
          <button type="button" className="btn btn-primary" onClick={() => setShowForm(true)}>
            Catat gangguan
          </button>
        )}
      </div>

      {showForm && feeders.data && (
        <NewOutageForm
          feeders={feeders.data}
          onCancel={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false);
            outages.reload();
          }}
        />
      )}

      <ErrorNote message={outages.error} />
      {outages.loading ? (
        <Loading />
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Penyulang</th>
              <th>Mulai</th>
              <th>Lama</th>
              <th>Penyebab</th>
              <th className="num">Pelanggan</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {outages.data.map((o) =>
              editing === o.id ? (
                <EditRow
                  key={o.id}
                  outage={o}
                  onCancel={() => setEditing(null)}
                  onSaved={() => {
                    setEditing(null);
                    outages.reload();
                  }}
                />
              ) : (
                <tr key={o.id} className={o.restored_at ? "" : "row-open"}>
                  <td>
                    {o.feeder_id} {names[o.feeder_id] ?? ""}
                    {o.auto_detected && <span className="muted small"> otomatis</span>}
                  </td>
                  <td>{formatDateTime(o.started_at)}</td>
                  <td>{o.restored_at ? formatDuration(o.duration_minutes) : <StatusLabel status="padam" />}</td>
                  <td className={o.cause === "belum_diketahui" ? "muted" : ""}>{CAUSES[o.cause] ?? o.cause}</td>
                  <td className="num">{formatNumber(o.customers_affected)}</td>
                  <td>
                    {(o.cause === "belum_diketahui" || !o.restored_at) && (
                      <button type="button" className="btn btn-small" onClick={() => setEditing(o.id)}>
                        Lengkapi
                      </button>
                    )}
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}
    </>
  );
}
