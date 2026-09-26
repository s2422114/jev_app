import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 開発中、/api/* を backend（uvicorn）へ転送する。
    // 本番では Render の静的サイト側の書き換えルールが同じ役目をするので、
    // フロントのコードは開発でも本番でも "/api/judge" と書けばよい。
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
