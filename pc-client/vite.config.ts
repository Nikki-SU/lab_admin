import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const isElectron = process.env.ELECTRON === 'true'
  
  return {
    plugins: [react()],
    base: isElectron ? './' : '/',
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
        mode === 'production' 
          ? (isElectron ? 'http://localhost:8000/api' : '/api')
          : '/api'
      )
    }
  }
})
