// Konfigurasi Vite (server pengembangan dan build) serta Vitest (test).
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // base "./" membuat hasil build bisa dibuka dari subfolder mana pun,
  // termasuk GitHub Pages (https://user.github.io/nama-repo/).
  base: "./",
  test: {
    environment: "node",
  },
});
