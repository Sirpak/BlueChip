import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/games/upcoming': 'http://127.0.0.1:8000',
      '/teams': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/favicon.ico': 'http://127.0.0.1:8000',
      '/favicon.png': 'http://127.0.0.1:8000',
      '/apple-touch-icon.png': 'http://127.0.0.1:8000',
      '/site.webmanifest': 'http://127.0.0.1:8000',
    },
  },
})
