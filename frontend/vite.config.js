import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** FastAPI default port (8000 is often blocked on Windows — see README). */
const API_PROXY_TARGET = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8787";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: API_PROXY_TARGET,
        changeOrigin: true,
      },
    },
  },
});
