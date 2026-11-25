// Test klien demo: waktu digeser agar terkini, aksi operator tersimpan di memori.
import { describe, expect, it } from "vitest";

import { createDemoApi, shiftTimes } from "./demo.js";
import snapshot from "./demo-data.json";

const NOW = new Date("2027-01-01T00:00:00Z");

describe("mode demo", () => {
  it("menggeser kolom waktu dan membiarkan kolom lain", () => {
    const out = shiftTimes({ started_at: "2026-01-01T00:00:00Z", feeder_id: "PYL-01" }, 60_000);
    expect(out).toEqual({ started_at: "2026-01-01T00:01:00.000Z", feeder_id: "PYL-01" });
  });

  it("data terbaru tampil seolah baru diukur", async () => {
    const api = createDemoApi(snapshot, () => NOW);
    const feeders = await api.feeders();
    const latest = Math.max(...feeders.map((f) => new Date(f.latest.measured_at).getTime()));
    expect(NOW.getTime() - latest).toBeLessThan(30 * 60 * 1000);
  });

  it("konfirmasi alarm tersimpan dan tidak tertimpa", async () => {
    const api = createDemoApi(snapshot, () => NOW);
    const [alarm] = await api.alarms("all");
    await api.acknowledge(alarm.id, "Operator A");
    const again = await api.acknowledge(alarm.id, "Operator B");
    expect(again.acknowledged_by).toBe("Operator A");
  });

  it("gangguan baru memakai jumlah pelanggan penyulang", async () => {
    const api = createDemoApi(snapshot, () => NOW);
    const created = await api.createOutage({ feeder_id: "PYL-01", started_at: NOW.toISOString() });
    expect(created.customers_affected).toBe(8200);
    expect((await api.outages("open")).some((o) => o.id === created.id)).toBe(true);
  });
});
