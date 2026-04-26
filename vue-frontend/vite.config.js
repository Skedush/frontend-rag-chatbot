import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        // Docker 环境用 backend，服务名在 docker network 中解析
        // 本地开发用 localhost:8000
        target: process.env.VITE_API_TARGET || 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
})
