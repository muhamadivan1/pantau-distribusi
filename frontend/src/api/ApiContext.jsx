// Menentukan apakah aplikasi memakai server sungguhan atau mode demo,
// lalu membagikan klien API yang sesuai ke seluruh halaman.
//
// Alur:
//   1. Jika VITE_API_URL kosong, langsung mode demo.
//   2. Jika ada, coba /health. Server hosting gratis bisa butuh sekitar satu
//      menit untuk bangun, jadi selama menunggu tampil status "menghubungkan".
//   3. Gagal dalam batas waktu -> mode demo, sambil terus mencoba di belakang.
//      Begitu server hidup, aplikasi pindah ke mode live dengan sendirinya.

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { createDemoApi } from "./demo.js";
import { createLiveApi } from "./live.js";

const API_URL = (import.meta.env.VITE_API_URL ?? "").trim();
const FIRST_TRY_MS = 8000; // tunggu awal sebelum beralih ke demo
const RETRY_MS = 20000; // jeda mencoba ulang di belakang layar
const RETRY_LIMIT = 9; // sekitar 3 menit

const ApiContext = createContext(null);

async function ping(api, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    await api.health(controller.signal);
    return true;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export function ApiProvider({ children }) {
  const live = useMemo(() => (API_URL ? createLiveApi(API_URL) : null), []);
  const demo = useMemo(() => createDemoApi(), []);
  const [mode, setMode] = useState(API_URL ? "connecting" : "demo");

  useEffect(() => {
    if (!live) return undefined;
    let stopped = false;
    let attempts = 0;
    let timer;

    async function attempt(timeout) {
      const ok = await ping(live, timeout);
      if (stopped) return;
      if (ok) return setMode("live");
      setMode("demo");
      if (++attempts < RETRY_LIMIT) timer = setTimeout(() => attempt(RETRY_MS), RETRY_MS);
    }
    attempt(FIRST_TRY_MS);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [live]);

  const value = useMemo(() => ({ api: mode === "live" ? live : demo, mode, apiUrl: API_URL }), [mode, live, demo]);
  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApi() {
  return useContext(ApiContext);
}

/**
 * Ambil data dan perbarui berkala.
 * fetcher menerima klien api, contoh: (api) => api.feeders()
 * Mengembalikan { data, error, loading, reload }.
 */
export function usePolling(fetcher, deps = [], intervalMs = 5000) {
  const { api, mode } = useApi();
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const reload = useCallback(async () => {
    try {
      const data = await fetcherRef.current(api);
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState((s) => ({ ...s, error: error.message, loading: false }));
    }
  }, [api]);

  useEffect(() => {
    if (mode === "connecting") return undefined;
    reload();
    if (!intervalMs) return undefined;
    const id = setInterval(reload, intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, mode, intervalMs, ...deps]);

  return { ...state, reload };
}
