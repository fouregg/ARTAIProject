import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// В деве фронт живёт на 5173 и проксирует API/WS на бэкенд,
// поэтому в коде везде используются относительные пути — как и в проде,
// где статику отдаёт сам FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
