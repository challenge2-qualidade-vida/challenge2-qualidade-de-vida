import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// A API do grupo fica sob /api/v1. Em desenvolvimento, o Vite repassa as chamadas ao backend local.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api/v1": "http://localhost:8001" },
  },
  build: { outDir: "dist", sourcemap: true },
});
