// Kerangka aplikasi: navigasi samping dan daftar halaman.
// HashRouter dipakai agar alamat seperti /#/alarm tetap jalan di GitHub Pages
// (GitHub Pages tidak bisa mengarahkan semua alamat ke index.html).

import { lazy, Suspense } from "react";
import { HashRouter, NavLink, Route, Routes } from "react-router-dom";

import { ApiProvider, useApi } from "./api/ApiContext.jsx";
import { ConnectionBanner, Loading } from "./components/common.jsx";
import Alarms from "./pages/Alarms.jsx";
import Outages from "./pages/Outages.jsx";
import Overview from "./pages/Overview.jsx";
import ShiftReport from "./pages/ShiftReport.jsx";

// Halaman bergrafik dimuat saat dibuka saja, supaya halaman awal lebih ringan.
const FeederDetail = lazy(() => import("./pages/FeederDetail.jsx"));
const Reliability = lazy(() => import("./pages/Reliability.jsx"));

const NAV = [
  ["/", "Kondisi jaringan"],
  ["/alarm", "Alarm"],
  ["/gangguan", "Gangguan"],
  ["/keandalan", "Keandalan"],
  ["/serah-terima", "Serah terima"],
];

function ModeBadge() {
  const { mode } = useApi();
  const label = { live: "Terhubung ke server", demo: "Mode demo", connecting: "Menghubungkan" }[mode];
  return <span className={`mode mode-${mode}`}>{label}</span>;
}

export default function App() {
  return (
    <ApiProvider>
      <HashRouter>
        <div className="shell">
          <nav className="sidebar" aria-label="Navigasi utama">
            <div className="brand">
              <span className="brand-name">Pantau Distribusi</span>
              <span className="brand-sub">Penyulang 20 kV</span>
            </div>
            <ul>
              {NAV.map(([to, label]) => (
                <li key={to}>
                  <NavLink to={to} end={to === "/"}>
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
            <div className="sidebar-foot">
              <ModeBadge />
              <p>Proyek portofolio dengan data fiktif. Tidak berafiliasi dengan perusahaan listrik mana pun.</p>
            </div>
          </nav>

          <main className="main">
            <ConnectionBanner />
            <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/penyulang/:id" element={<FeederDetail />} />
              <Route path="/alarm" element={<Alarms />} />
              <Route path="/gangguan" element={<Outages />} />
              <Route path="/keandalan" element={<Reliability />} />
              <Route path="/serah-terima" element={<ShiftReport />} />
              <Route path="*" element={<p>Halaman tidak ditemukan.</p>} />
            </Routes>
            </Suspense>
          </main>
        </div>
      </HashRouter>
    </ApiProvider>
  );
}
