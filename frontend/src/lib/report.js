// Ubah ringkasan shift menjadi teks polos untuk ditempel ke grup WhatsApp atau buku laporan.
import { formatDateTime } from "./format.js";

export function toPlainText(summary) {
  const lines = [
    `Serah terima shift ${formatDateTime(summary.start)} sampai ${formatDateTime(summary.end)}`,
    summary.headline,
    ...summary.lines.map((l) => `- ${l}`),
  ];
  return lines.join("\n");
}
