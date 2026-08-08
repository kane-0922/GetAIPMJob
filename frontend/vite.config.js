import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    proxy: {
      '/stream_run': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/run': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
    },
  },
})
