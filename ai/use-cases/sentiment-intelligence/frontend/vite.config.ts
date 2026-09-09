import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // Relative assets keep the SPA working behind the AICoE /d/<session>/ prefix.
  base: './',
  plugins: [react()],
  server: {
    port: 3060,
    proxy: {
      '/api': {
        target: 'http://localhost:4060',
        changeOrigin: true,
      },
    },
  },
})
