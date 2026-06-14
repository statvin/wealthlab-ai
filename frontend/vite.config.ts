import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// O dev server expõe a API sob /api e repassa para o FastAPI em :8000
// (assim não há dor de CORS no desenvolvimento).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
