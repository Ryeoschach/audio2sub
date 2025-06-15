import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Default Vite port
    host: '0.0.0.0', // Allow access from network (Docker)
    proxy: {
      // Proxy API requests to the backend to avoid CORS issues during development
      '/api': {
        target: 'http://localhost:8000', // Your backend address
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
