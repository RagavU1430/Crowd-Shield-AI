import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
        timeout: 0,
        proxyTimeout: 0,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
      '/processed': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
})
