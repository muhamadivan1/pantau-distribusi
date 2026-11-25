// Klien API tiruan untuk mode demo (tanpa server).
//
// Datanya berasal dari demo-data.json, yaitu cuplikan respons backend asli
// yang dibuat oleh backend/tools/export_docs.py. Supaya demo terasa terkini,
// semua waktu digeser sejauh (sekarang - waktu ekspor).
//
// Aksi operator (konfirmasi alarm, catat gangguan) disimpan di memori saja
// dan hilang saat halaman dimuat ulang.

import snapshot from "./demo-data.json";

const TIME_KEYS = new Set(["measured_at", "raised_at", "acknowledged_at", "cleared_at", "started_at", "restored_at", "start", "end"]);

/** Salin data sambil menggeser semua kolom waktu sejauh offsetMs. */
export function shiftTimes(value, offsetMs) {
  if (Array.isArray(value)) return value.map((v) => shiftTimes(v, offsetMs));
  if (value && typeof value === "object") {
    const out = {};
    for (const [key, v] of Object.entries(value)) {
      out[key] = TIME_KEYS.has(key) && typeof v === "string" ? new Date(new Date(v).getTime() + offsetMs).toISOString() : shiftTimes(v, offsetMs);
    }
    return out;
  }
  return value;
}

const delay = (ms = 150) => new Promise((resolve) => setTimeout(resolve, ms));

export function createDemoApi(source = snapshot, now = () => new Date()) {
  const offset = now().getTime() - new Date(source.exported_at).getTime();
  const data = shiftTimes(source, offset);
  let nextOutageId = Math.max(0, ...data.outages.map((o) => o.id)) + 1;

  const find = (list, id) => {
    const item = list.find((x) => x.id === Number(id));
    if (!item) throw new Error(`data ${id} tidak ditemukan`);
    return item;
  };

  return {
    health: async () => ({ status: "ok", demo_mode: true }),
    feeders: async () => (await delay(), structuredClone(data.feeders)),
    feeder: async (id) => {
      await delay();
      const f = data.feeders.find((x) => x.id === id);
      if (!f) throw new Error(`penyulang ${id} tidak ditemukan`);
      return structuredClone(f);
    },
    measurements: async (id) => (await delay(), structuredClone(data.measurements[id] ?? [])),
    alarms: async (status = "open") => {
      await delay();
      const list = status === "open" ? data.alarms.filter((a) => !a.cleared_at) : data.alarms;
      return structuredClone(list);
    },
    acknowledge: async (id, by) => {
      const alarm = find(data.alarms, id);
      if (!alarm.acknowledged_at) Object.assign(alarm, { acknowledged_at: now().toISOString(), acknowledged_by: by });
      return structuredClone(alarm);
    },
    outages: async (status = "all", feederId) => {
      await delay();
      let list = data.outages;
      if (status === "open") list = list.filter((o) => !o.restored_at);
      if (status === "closed") list = list.filter((o) => o.restored_at);
      if (feederId) list = list.filter((o) => o.feeder_id === feederId);
      return structuredClone(list);
    },
    createOutage: async (body) => {
      const feeder = data.feeders.find((f) => f.id === body.feeder_id);
      const outage = {
        id: nextOutageId++,
        feeder_id: body.feeder_id,
        started_at: body.started_at,
        restored_at: body.restored_at ?? null,
        cause: body.cause ?? "belum_diketahui",
        customers_affected: body.customers_affected ?? feeder?.customers ?? 0,
        notes: body.notes ?? "",
        auto_detected: false,
        duration_minutes: body.restored_at ? (new Date(body.restored_at) - new Date(body.started_at)) / 60000 : null,
      };
      data.outages.unshift(outage);
      return structuredClone(outage);
    },
    updateOutage: async (id, changes) => {
      const outage = find(data.outages, id);
      Object.assign(outage, changes);
      if (outage.restored_at) outage.duration_minutes = (new Date(outage.restored_at) - new Date(outage.started_at)) / 60000;
      return structuredClone(outage);
    },
    // Keandalan dan ringkasan shift memakai hasil hitungan backend saat ekspor.
    reliability: async (days = 30) => (await delay(), structuredClone(data.reliability[days] ?? data.reliability[30])),
    shiftSummary: async () => (await delay(), structuredClone(data.shift_summary)),
  };
}
