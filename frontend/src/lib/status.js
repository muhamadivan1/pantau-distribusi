// Arti setiap status dan penyebab gangguan untuk tampilan.
// Prinsip warna mengikuti gaya "high-performance HMI": kondisi normal
// ditampilkan abu-abu, warna hanya dipakai untuk kondisi yang butuh perhatian.

export const STATUS = {
  normal: { label: "Normal", tone: "normal", rank: 0 },
  waspada: { label: "Waspada", tone: "warn", rank: 1 },
  kritis: { label: "Kritis", tone: "crit", rank: 2 },
  padam: { label: "Padam", tone: "off", rank: 3 },
  tanpa_data: { label: "Tanpa data", tone: "stale", rank: -1 },
};

export const CAUSES = {
  belum_diketahui: "Belum diketahui",
  pohon: "Pohon atau ranting",
  hewan: "Hewan",
  peralatan: "Kerusakan peralatan",
  cuaca: "Cuaca",
  pihak_ketiga: "Pihak ketiga",
  pemeliharaan: "Pemeliharaan terencana",
};

// Ambang yang sama dengan backend (app/config.py). Dipakai untuk garis batas di grafik.
export const THRESHOLD = { waspada: 80, kritis: 95 };

export function statusMeta(status) {
  return STATUS[status] ?? STATUS.tanpa_data;
}

/** Hitung jumlah penyulang per status, untuk strip ringkasan. */
export function countByStatus(feeders) {
  const counts = { normal: 0, waspada: 0, kritis: 0, padam: 0, tanpa_data: 0 };
  for (const f of feeders) counts[f.status] = (counts[f.status] ?? 0) + 1;
  return counts;
}

/** Kelompokkan penyulang per gardu induk, urutan sesuai kemunculan. */
export function groupBySubstation(feeders) {
  const groups = new Map();
  for (const f of feeders) {
    if (!groups.has(f.substation)) groups.set(f.substation, []);
    groups.get(f.substation).push(f);
  }
  return [...groups.entries()].map(([substation, items]) => ({ substation, feeders: items }));
}

/** Lebar batang beban dalam persen, dibatasi 0 sampai 110 agar beban lebih tetap terlihat. */
export function barWidth(loadPct) {
  if (loadPct === null || loadPct === undefined) return 0;
  return (Math.max(0, Math.min(loadPct, 110)) * 100) / 110;
}
