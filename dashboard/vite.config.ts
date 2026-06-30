import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dashboard talks to the hypersignal FastAPI backend (which holds the
// GOLDRUSH_API_KEY server-side). In dev we proxy /api -> :8000 so the key
// never touches the browser.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
