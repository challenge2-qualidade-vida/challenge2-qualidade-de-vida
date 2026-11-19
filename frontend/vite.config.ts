import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// A API roda em http://127.0.0.1:8000 (uvicorn). O proxy evita CORS no desenvolvimento.
const API = process.env.ECONOMIA_API ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": API,
      "/saude": API,
    },
  },
});
