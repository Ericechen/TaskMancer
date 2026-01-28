import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // Tauri 相容設定
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: true, // 允許外部連線
  },
  
  // 環境變數
  envPrefix: ['VITE_', 'TAURI_'],
})
