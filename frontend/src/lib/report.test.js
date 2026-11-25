import { describe, expect, it } from "vitest";

import { toPlainText } from "./report.js";

describe("teks serah terima", () => {
  it("berisi judul, ringkasan, dan setiap catatan sebagai butir", () => {
    const text = toPlainText({ start: "2026-11-25T00:00:00Z", end: "2026-11-25T08:00:00Z", headline: "Shift normal.", lines: ["Catatan satu."] });
    expect(text.split("\n")).toEqual([expect.stringContaining("Serah terima shift"), "Shift normal.", "- Catatan satu."]);
  });
});
