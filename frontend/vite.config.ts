import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://0.0.0.0:8081', // FastAPI server
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/flask-api': {
        target: 'http://localhost:5000', // Flask server
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/flask-api/, ''),
      },
    },
  },
})
