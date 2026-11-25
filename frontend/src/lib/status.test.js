// Test logika status untuk tampilan.
import { describe, expect, it } from "vitest";

import { barWidth, countByStatus, groupBySubstation, statusMeta } from "./status.js";

const FEEDERS = [
  { id: "A", substation: "GI 1", status: "normal" },
  { id: "B", substation: "GI 1", status: "padam" },
  { id: "C", substation: "GI 2", status: "kritis" },
];

describe("status", () => {
  it("status tidak dikenal dianggap tanpa data", () => {
    expect(statusMeta("aneh").label).toBe("Tanpa data");
  });

  it("menghitung penyulang per status", () => {
    expect(countByStatus(FEEDERS)).toMatchObject({ normal: 1, padam: 1, kritis: 1, waspada: 0 });
  });

  it("mengelompokkan penyulang per gardu induk sesuai urutan", () => {
    const groups = groupBySubstation(FEEDERS);
    expect(groups.map((g) => g.substation)).toEqual(["GI 1", "GI 2"]);
    expect(groups[0].feeders.map((f) => f.id)).toEqual(["A", "B"]);
  });

  it("batang beban dibatasi agar beban lebih tetap muat", () => {
    expect(barWidth(0)).toBe(0);
    expect(barWidth(110)).toBe(100);
    expect(barWidth(150)).toBe(100);
    expect(barWidth(null)).toBe(0);
  });
});
