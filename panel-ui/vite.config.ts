import { defineConfig } from "vite";

// Development: /api (and the session tab's WebSocket) go to the panel (127.0.0.1:8765). The build lands in dist/,
// which the panel serves from a checkout; the wheel carries it as mekanik/panel/static (pyproject force-include).
export default defineConfig({
  server: { host: "127.0.0.1", proxy: { "/api": { target: "http://127.0.0.1:8765", ws: true }, "/login": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", chunkSizeWarningLimit: 4000 },
});
