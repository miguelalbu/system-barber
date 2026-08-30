import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Inside Docker the API is reachable by service name; outside, on localhost.
const API_TARGET = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000';

// Bind mounts on Windows and macOS do not forward inotify events into the
// container, so the file watcher never fires and HMR silently stops working.
// Polling is the fix, and it costs CPU — so it stays off unless asked for.
const USE_POLLING = process.env.VITE_USE_POLLING === 'true';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    strictPort: true,
    watch: USE_POLLING ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      // The API has no /api prefix of its own (routes are /auth/login, /team…),
      // so the prefix is stripped on the way through. Going through the proxy
      // instead of calling the backend directly keeps everything same-origin,
      // which means no CORS and no preflight in development.
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
});
