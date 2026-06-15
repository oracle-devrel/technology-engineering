import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Dev: browser calls same-origin /api/... so you always hit the local FastAPI app (avoids
      // wrong VITE_API_BASE_URL or a stale process on another port).
      '/api': {
        // Dedicated port — 8001 often has multiple stale uvicorn/python listeners on Windows.
        target: 'http://127.0.0.1:8055',
        changeOrigin: true,
      },
    },
  },
})
