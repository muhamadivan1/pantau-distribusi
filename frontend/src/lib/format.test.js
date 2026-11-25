// Test fungsi format: tampilan harus memakai WIB dan gaya angka Indonesia.
import { describe, expect, it } from "vitest";

import { formatAgo, formatDateTime, formatDuration, formatNumber, toWibInputValue, wibInputToIso } from "./format.js";

describe("format", () => {
  it("menampilkan waktu UTC dalam WIB", () => {
    // 01.00 UTC = 08.00 WIB
    expect(formatDateTime("2026-11-25T01:00:00Z")).toContain("08.00");
  });

  it("memakai titik ribuan dan koma desimal", () => {
    expect(formatNumber(10350)).toBe("10.350");
    expect(formatNumber(19.854, 2)).toBe("19,85");
    expect(formatNumber(null)).toBe("-");
  });

  it("menulis lama gangguan dalam jam dan menit", () => {
    expect(formatDuration(40)).toBe("40 menit");
    expect(formatDuration(60)).toBe("1 jam");
    expect(formatDuration(85)).toBe("1 jam 25 menit");
  });

  it("menulis selisih waktu yang mudah dibaca", () => {
    const now = new Date("2026-11-25T10:00:00Z");
    expect(formatAgo("2026-11-25T09:57:00Z", now)).toBe("3 menit lalu");
    expect(formatAgo("2026-11-25T07:00:00Z", now)).toBe("3 jam lalu");
  });

  it("input WIB bolak-balik ke ISO UTC tanpa bergeser", () => {
    const date = new Date("2026-11-25T01:30:00Z");
    expect(toWibInputValue(date)).toBe("2026-11-25T08:30");
    expect(wibInputToIso("2026-11-25T08:30")).toBe("2026-11-25T01:30:00.000Z");
    expect(wibInputToIso("")).toBeNull();
  });
});
