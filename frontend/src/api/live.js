// Klien API sungguhan: memanggil backend FastAPI lewat fetch.
// Semua fungsi mengembalikan Promise berisi JSON dari server.

export function createLiveApi(baseUrl) {
  const root = baseUrl.replace(/\/$/, "") + "/api/v1";

  async function request(path, options = {}) {
    const response = await fetch(root + path, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      // FastAPI mengirim pesan galat di "detail" (teks atau daftar galat validasi).
      const detail = typeof body.detail === "string" ? body.detail : "Data yang dikirim tidak valid.";
      throw new Error(detail);
    }
    return body;
  }

  return {
    health: (signal) => request("/health", { signal }),
    feeders: () => request("/feeders"),
    feeder: (id) => request(`/feeders/${encodeURIComponent(id)}`),
    measurements: (id, hours = 24) => request(`/feeders/${encodeURIComponent(id)}/measurements?hours=${hours}`),
    alarms: (status = "open") => request(`/alarms?status=${status}`),
    acknowledge: (id, by) => request(`/alarms/${id}/acknowledge`, { method: "POST", body: JSON.stringify({ by }) }),
    outages: (status = "all", feederId) => request(`/outages?status=${status}${feederId ? `&feeder_id=${encodeURIComponent(feederId)}` : ""}`),
    createOutage: (data) => request("/outages", { method: "POST", body: JSON.stringify(data) }),
    updateOutage: (id, data) => request(`/outages/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    reliability: (days = 30) => request(`/reliability?days=${days}`),
    shiftSummary: (hours = 8) => request(`/reports/shift-summary?hours=${hours}`),
  };
}
