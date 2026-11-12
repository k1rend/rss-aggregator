import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

// The Express server in ../src does not enable CORS, so in development we proxy
// API calls through the Vite dev/preview server instead of calling it cross-origin.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = env.VITE_PROXY_TARGET || 'http://localhost:3000';
  const proxy = {
    '/api': { target: apiTarget, changeOrigin: true },
    '/health': { target: apiTarget, changeOrigin: true },
  };

  return {
    plugins: [vue()],
    server: { port: 5173, proxy },
    preview: { port: 4173, proxy },
  };
});
