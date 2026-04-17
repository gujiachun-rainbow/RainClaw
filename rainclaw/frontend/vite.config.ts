import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    (monacoEditorPlugin as any).default({})
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  optimizeDeps: {
    exclude: ['lucide-vue-next'],
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '/task-service': {
        target: process.env.TASK_SERVICE_URL || 'http://localhost:12002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/task-service/, ''),
      },
    },
  },
}); 