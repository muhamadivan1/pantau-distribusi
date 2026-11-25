// Halaman Alarm: daftar alarm dan konfirmasi oleh operator jaga.

import { useState } from "react";

import { useApi, usePolling } from "../api/ApiContext.jsx";
import { ErrorNote, Loading, StatusLabel } from "../components/common.jsx";
import { formatDateTime } from "../lib/format.js";

function savedOperator() {
  try {
    return localStorage.getItem("operatorName") ?? "";
  } catch {
    return "";
  }
}

export default function Alarms() {
  const { api } = useApi();
  const [filter, setFilter] = useState("open");
  const [operator, setOperator] = useState(savedOperator);
  const [actionError, setActionError] = useState(null);
  const alarms = usePolling((a) => a.alarms(filter), [filter], 5000);

  function changeOperator(value) {
    setOperator(value);
    try {
      localStorage.setItem("operatorName", value);
    } catch {
      /* nama tetap dipakai di sesi ini walau gagal disimpan */
    }
  }

  async function acknowledge(id) {
    if (operator.trim().length < 2) {
      setActionError("Isi nama operator dulu, minimal 2 huruf.");
      return;
    }
    try {
      setActionError(null);
      await api.acknowledge(id, operator.trim());
      alarms.reload();
    } catch (error) {
      setActionError(error.message);
    }
  }

  return (
    <>
      <header className="page-head">
        <h1>Alarm</h1>
      </header>

      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Saring alarm">
          <button type="button" aria-pressed={filter === "open"} onClick={() => setFilter("open")}>
            Aktif
          </button>
          <button type="button" aria-pressed={filter === "all"} onClick={() => setFilter("all")}>
            Semua
          </button>
        </div>
        <label className="field-inline">
          Operator jaga
          <input value={operator} onChange={(e) => changeOperator(e.target.value)} placeholder="Nama Anda" maxLength={80} />
        </label>
      </div>

      <ErrorNote message={actionError ?? alarms.error} />
      {alarms.loading ? (
        <Loading />
      ) : alarms.data.length === 0 ? (
        <p className="muted">{filter === "open" ? "Tidak ada alarm aktif. Semua penyulang dalam batas normal." : "Belum ada alarm."}</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Waktu</th>
              <th>Tingkat</th>
              <th>Pesan</th>
              <th>Konfirmasi</th>
              <th>Selesai</th>
            </tr>
          </thead>
          <tbody>
            {alarms.data.map((a) => (
              <tr key={a.id}>
                <td>{formatDateTime(a.raised_at)}</td>
                <td>
                  <StatusLabel status={a.level} />
                </td>
                <td>{a.message}</td>
                <td>
                  {a.acknowledged_at ? (
                    <span className="muted small">
                      {a.acknowledged_by}, {formatDateTime(a.acknowledged_at)}
                    </span>
                  ) : (
                    <button type="button" className="btn btn-small" onClick={() => acknowledge(a.id)}>
                      Konfirmasi
                    </button>
                  )}
                </td>
                <td>{a.cleared_at ? formatDateTime(a.cleared_at) : <span className="muted">Masih aktif</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
