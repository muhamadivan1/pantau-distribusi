"""
tools/build_bpmn.py
---------------------------------------------------------------------------
Membuat berkas BPMN 2.0 (.bpmn) untuk dokumentasi proses bisnis sistem
Pantau Distribusi. Berkas hasilnya bisa dibuka dan diedit di https://demo.bpmn.io
atau Camunda Modeler.

Kenapa lewat skrip, bukan digambar manual?
  - Proses ditulis sebagai data (lane, elemen, alur) yang mudah dibaca dan diubah.
  - Tata letak (koordinat) dihitung otomatis, jadi diagram selalu rapi.
  - Tidak butuh pustaka tambahan, cukup Python 3.

Cara menjalankan (dari folder utama proyek):
    python tools/build_bpmn.py

Hasil: docs/bpmn/*.bpmn
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "bpmn"

# Ukuran dan jarak (piksel) untuk tata letak otomatis.
LANE_H = 220  # tinggi satu lane
COL_W = 185  # jarak antar kolom
X0 = 130  # posisi kolom pertama dari tepi kiri pool
POOL_X, POOL_Y = 40, 40
LANE_LABEL_W = 30  # lebar label lane di sisi kiri

SIZE = {
    "startEvent": (36, 36),
    "endEvent": (36, 36),
    "task": (140, 90),
    "userTask": (140, 90),
    "serviceTask": (140, 90),
    "exclusiveGateway": (50, 50),
}

# ===========================================================================
# DEFINISI PROSES
# Setiap elemen: (id, jenis, label, lane, kolom, geser_vertikal)
# Setiap alur:   (dari, ke, label, cara_belok)
#   cara_belok "h" = mendatar dulu lalu tegak (bawaan)
#   cara_belok "v" = tegak dulu lalu mendatar
# ===========================================================================

PROCESSES = [
    {
        "file": "01-penanganan-gangguan.bpmn",
        "id": "Proses_Gangguan",
        "name": "Penanganan gangguan penyulang",
        "lanes": ["Operator ruang kendali", "Sistem Pantau Distribusi", "Regu lapangan"],
        "elements": [
            ("s1", "startEvent", "Tegangan penyulang hilang", 1, 0, 0),
            ("t1", "serviceTask", "Buka gangguan dan alarm padam otomatis", 1, 1, 0),
            ("t2", "userTask", "Konfirmasi alarm", 0, 2, 0),
            ("t3", "userTask", "Perintahkan regu memeriksa jaringan", 0, 3, 0),
            ("t4", "userTask", "Telusuri jaringan dan temukan penyebab", 2, 4, 0),
            ("g1", "exclusiveGateway", "Bisa dipulihkan cepat?", 2, 5, 0),
            ("t6", "userTask", "Manuver jaringan ke penyulang lain", 0, 6, 0),
            ("t5", "userTask", "Perbaiki penyebab gangguan", 2, 7, 0),
            ("t7", "serviceTask", "Tegangan kembali, gangguan ditutup otomatis", 1, 8, 0),
            ("t8", "userTask", "Lengkapi penyebab gangguan", 0, 9, 0),
            ("e1", "endEvent", "Data siap dihitung ke SAIDI dan SAIFI", 0, 10, 0),
        ],
        "flows": [
            ("s1", "t1", "", "h"),
            ("t1", "t2", "", "h"),
            ("t2", "t3", "", "h"),
            ("t3", "t4", "", "h"),
            ("t4", "g1", "", "h"),
            ("g1", "t5", "Ya", "h"),
            ("g1", "t6", "Tidak", "v"),
            ("t6", "t5", "", "h"),
            ("t5", "t7", "", "h"),
            ("t7", "t8", "", "h"),
            ("t8", "e1", "", "h"),
        ],
    },
    {
        "file": "02-penerimaan-telemetri.bpmn",
        "id": "Proses_Telemetri",
        "name": "Penerimaan telemetri dari berbagai format",
        "lanes": ["Gateway perangkat", "API Pantau Distribusi"],
        "elements": [
            ("s1", "startEvent", "Data ukur terkumpul", 0, 0, 0),
            ("t1", "serviceTask", "Kirim POST /telemetry dengan X-API-Key", 0, 1, 0),
            ("g1", "exclusiveGateway", "API key benar?", 1, 2, 0),
            ("e401", "endEvent", "Ditolak 401", 1, 2, 60),
            ("g2", "exclusiveGateway", "Format dikenali adapter?", 1, 3, 0),
            ("e422", "endEvent", "Ditolak 422", 1, 3, 60),
            ("t2", "serviceTask", "Ubah ke bentuk kanonik lewat adapter", 1, 5, 0),
            ("t3", "serviceTask", "Validasi rentang dan cek duplikat", 1, 6, 0),
            ("g3", "exclusiveGateway", "Rekaman lolos?", 1, 7, 0),
            ("erej", "endEvent", "Dilaporkan sebagai ditolak", 1, 7, 60),
            ("t4", "serviceTask", "Simpan pengukuran", 1, 9, 0),
            ("t5", "serviceTask", "Perbarui status, alarm, dan gangguan", 1, 10, 0),
            ("t6", "serviceTask", "Terima ringkasan hasil", 0, 11, 0),
            ("e1", "endEvent", "Telemetri diproses", 0, 12, 0),
        ],
        "flows": [
            ("s1", "t1", "", "h"),
            ("t1", "g1", "", "h"),
            ("g1", "g2", "Ya", "h"),
            ("g1", "e401", "Tidak", "v"),
            ("g2", "t2", "Ya", "h"),
            ("g2", "e422", "Tidak", "v"),
            ("t2", "t3", "", "h"),
            ("t3", "g3", "", "h"),
            ("g3", "t4", "Ya", "h"),
            ("g3", "erej", "Tidak", "v"),
            ("t4", "t5", "", "h"),
            ("t5", "t6", "", "h"),
            ("t6", "e1", "", "h"),
        ],
    },
    {
        "file": "03-serah-terima-shift.bpmn",
        "id": "Proses_SerahTerima",
        "name": "Serah terima shift operator",
        "lanes": ["Operator shift lama", "Sistem Pantau Distribusi", "Operator shift baru"],
        "elements": [
            ("s1", "startEvent", "Shift akan berakhir", 0, 0, 0),
            ("t1", "userTask", "Buka halaman Serah terima", 0, 1, 0),
            ("t2", "serviceTask", "Susun ringkasan dari alarm, gangguan, dan beban", 1, 2, 0),
            ("t3", "userTask", "Lengkapi penyebab gangguan yang belum diisi", 0, 3, 0),
            ("t4", "userTask", "Salin teks ringkasan ke grup operator", 0, 4, 0),
            ("t5", "userTask", "Baca ringkasan dan alarm yang belum dikonfirmasi", 2, 5, 0),
            ("g1", "exclusiveGateway", "Ada gangguan masih terbuka?", 2, 6, 0),
            ("t6", "userTask", "Lanjutkan penanganan gangguan", 2, 7, -55),
            ("e1", "endEvent", "Shift baru berjalan", 2, 8, 0),
        ],
        "flows": [
            ("s1", "t1", "", "h"),
            ("t1", "t2", "", "h"),
            ("t2", "t3", "", "h"),
            ("t3", "t4", "", "h"),
            ("t4", "t5", "", "h"),
            ("t5", "g1", "", "h"),
            ("g1", "t6", "Ya", "h"),
            ("g1", "e1", "Tidak", "h"),
            ("t6", "e1", "", "h"),
        ],
    },
]


# ===========================================================================
# PEMBUAT XML
# ===========================================================================


def layout(proc):
    """Hitung kotak (x, y, lebar, tinggi) setiap elemen dari lane dan kolomnya."""
    boxes = {}
    for el_id, kind, _label, lane, col, dy in proc["elements"]:
        w, h = SIZE[kind]
        cx = POOL_X + LANE_LABEL_W + X0 + col * COL_W
        cy = POOL_Y + lane * LANE_H + LANE_H // 2 + dy
        boxes[el_id] = (cx - w // 2, cy - h // 2, w, h)
    return boxes


def waypoints(src, dst, mode):
    """Titik belok garis alur antara dua kotak."""
    sx, sy, sw, sh = src
    tx, ty, tw, th = dst
    s_cx, s_cy = sx + sw // 2, sy + sh // 2
    t_cx, t_cy = tx + tw // 2, ty + th // 2

    if mode == "v":
        start_y = sy + sh if t_cy > s_cy else sy
        if abs(t_cx - s_cx) < 5:
            # Tujuan tepat di atas atau di bawah sumber: cukup satu garis lurus.
            end_y = ty if t_cy > s_cy else ty + th
            return [(s_cx, start_y), (t_cx, end_y)]
        # Tegak dari atas atau bawah sumber, lalu mendatar ke sisi kiri tujuan.
        return [(s_cx, start_y), (s_cx, t_cy), (tx, t_cy)]

    start = (sx + sw, s_cy)
    end = (tx, t_cy)
    if s_cy == t_cy:
        return [start, end]
    mid_x = (start[0] + end[0]) // 2
    return [start, (mid_x, s_cy), (mid_x, t_cy), end]


def label_position(pts, mode):
    """Letak label Ya atau Tidak supaya tidak bertumpuk dengan label lain.

    - Garis lurus: sedikit di kanan atas titik awal.
    - Garis mendatar lalu tegak: di samping ruas tegak, dekat tujuan.
    - Garis tegak dulu: di atas ruas mendatar, tepat setelah belokan.
    """
    if len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        if x1 == x2:  # garis lurus tegak
            return x1 + 8, (y1 + y2) // 2 - 7
        return x1 + 10, y1 - 20
    if mode == "v":
        (x1, _y1), (_x2, y2) = pts[0], pts[1]
        return x1 + 12, y2 - 18
    (mx, _y1), (_mx, y2) = pts[1], pts[2]
    return mx + 8, y2 - 20


def build_xml(proc):
    boxes = layout(proc)
    lanes = proc["lanes"]
    max_col = max(e[4] for e in proc["elements"])
    pool_w = LANE_LABEL_W + X0 + max_col * COL_W + 140
    pool_h = LANE_H * len(lanes)
    pid = proc["id"]

    incoming = {e[0]: [] for e in proc["elements"]}
    outgoing = {e[0]: [] for e in proc["elements"]}
    for i, (a, b, _l, _m) in enumerate(proc["flows"]):
        fid = f"Flow_{i + 1}"
        outgoing[a].append(fid)
        incoming[b].append(fid)

    sem = []  # bagian semantik (isi proses)
    sem.append(f'  <bpmn:collaboration id="Collab_{pid}">')
    sem.append(f'    <bpmn:participant id="Pool_{pid}" name="{escape(proc["name"])}" processRef="{pid}" />')
    sem.append("  </bpmn:collaboration>")
    sem.append(f'  <bpmn:process id="{pid}" isExecutable="false">')
    sem.append(f'    <bpmn:laneSet id="LaneSet_{pid}">')
    for li, lane in enumerate(lanes):
        sem.append(f'      <bpmn:lane id="Lane_{pid}_{li}" name="{escape(lane)}">')
        for el_id, *_rest in [e for e in proc["elements"] if e[3] == li]:
            sem.append(f"        <bpmn:flowNodeRef>{pid}_{el_id}</bpmn:flowNodeRef>")
        sem.append("      </bpmn:lane>")
    sem.append("    </bpmn:laneSet>")
    for el_id, kind, label, *_rest in proc["elements"]:
        sem.append(f'    <bpmn:{kind} id="{pid}_{el_id}" name="{escape(label)}">')
        for f in incoming[el_id]:
            sem.append(f"      <bpmn:incoming>{pid}_{f}</bpmn:incoming>")
        for f in outgoing[el_id]:
            sem.append(f"      <bpmn:outgoing>{pid}_{f}</bpmn:outgoing>")
        sem.append(f"    </bpmn:{kind}>")
    for i, (a, b, label, _m) in enumerate(proc["flows"]):
        name = f' name="{escape(label)}"' if label else ""
        sem.append(f'    <bpmn:sequenceFlow id="{pid}_Flow_{i + 1}"{name} sourceRef="{pid}_{a}" targetRef="{pid}_{b}" />')
    sem.append("  </bpmn:process>")

    di = []  # bagian gambar (koordinat)
    di.append(f'  <bpmndi:BPMNDiagram id="Diagram_{pid}">')
    di.append(f'    <bpmndi:BPMNPlane id="Plane_{pid}" bpmnElement="Collab_{pid}">')
    di.append(f'      <bpmndi:BPMNShape id="Pool_{pid}_di" bpmnElement="Pool_{pid}" isHorizontal="true">')
    di.append(f'        <dc:Bounds x="{POOL_X}" y="{POOL_Y}" width="{pool_w}" height="{pool_h}" />')
    di.append("      </bpmndi:BPMNShape>")
    for li in range(len(lanes)):
        di.append(f'      <bpmndi:BPMNShape id="Lane_{pid}_{li}_di" bpmnElement="Lane_{pid}_{li}" isHorizontal="true">')
        di.append(f'        <dc:Bounds x="{POOL_X + LANE_LABEL_W}" y="{POOL_Y + li * LANE_H}" width="{pool_w - LANE_LABEL_W}" height="{LANE_H}" />')
        di.append("      </bpmndi:BPMNShape>")
    # Gerbang yang punya cabang naik: namanya ditaruh di bawah agar tidak tertabrak garis.
    label_below = {a for a, b, _l, m in proc["flows"] if m == "v" and boxes[b][1] < boxes[a][1]}

    for el_id, kind, *_rest in proc["elements"]:
        x, y, w, h = boxes[el_id]
        marker = ' isMarkerVisible="true"' if kind == "exclusiveGateway" else ""
        di.append(f'      <bpmndi:BPMNShape id="{pid}_{el_id}_di" bpmnElement="{pid}_{el_id}"{marker}>')
        di.append(f'        <dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />')
        if kind in ("startEvent", "endEvent", "exclusiveGateway"):
            # Label peristiwa di bawah simbol. Label gerbang di atas simbol,
            # karena cabang "Tidak" sering keluar lewat bawah gerbang.
            above = kind == "exclusiveGateway" and el_id not in label_below
            label_y = y - 46 if above else y + h + 6
            di.append("        <bpmndi:BPMNLabel>")
            di.append(f'          <dc:Bounds x="{x + w // 2 - 50}" y="{label_y}" width="100" height="40" />')
            di.append("        </bpmndi:BPMNLabel>")
        di.append("      </bpmndi:BPMNShape>")
    for i, (a, b, label, mode) in enumerate(proc["flows"]):
        pts = waypoints(boxes[a], boxes[b], mode)
        di.append(f'      <bpmndi:BPMNEdge id="{pid}_Flow_{i + 1}_di" bpmnElement="{pid}_Flow_{i + 1}">')
        for px, py in pts:
            di.append(f'        <di:waypoint x="{px}" y="{py}" />')
        if label:
            lx, ly = label_position(pts, mode)
            di.append("        <bpmndi:BPMNLabel>")
            di.append(f'          <dc:Bounds x="{lx}" y="{ly}" width="40" height="14" />')
            di.append("        </bpmndi:BPMNLabel>")
        di.append("      </bpmndi:BPMNEdge>")
    di.append("    </bpmndi:BPMNPlane>")
    di.append("  </bpmndi:BPMNDiagram>")

    head = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'
        ' xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"'
        ' xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"'
        ' xmlns:di="http://www.omg.org/spec/DD/20100524/DI"'
        f' id="Definitions_{pid}" targetNamespace="https://github.com/muhamadivan1/pantau-distribusi/bpmn">\n'
    )
    return head + "\n".join(sem + di) + "\n</bpmn:definitions>\n"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for proc in PROCESSES:
        path = OUT_DIR / proc["file"]
        path.write_text(build_xml(proc), encoding="utf-8")
        print(f"dibuat: {path.relative_to(OUT_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
