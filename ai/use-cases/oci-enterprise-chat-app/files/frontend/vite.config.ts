import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

const DEFAULT_ENTERPRISE_AI_URL = 'https://aiq-rb.163-192-63-55.nip.io';

/**
 * Keep the browser on the local origin while forwarding API calls to the
 * deployed EnterpriseAI service. This avoids CORS configuration and keeps
 * the service credentials out of the client bundle.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const enterpriseAiUrl = (
    env.ENTERPRISE_AI_API_URL || DEFAULT_ENTERPRISE_AI_URL
  ).replace(/\/$/, '');

  const localBackend = env.LOCAL_BACKEND_URL || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    server: {
      port: 3000,
      open: true,
      proxy: {
        // Authentication remains local. The local backend holds the admin
        // secret; the browser never receives it in a Vite environment file.
        '/api/auth': {
          target: localBackend,
          changeOrigin: true,
        },
        '/api/workflows': { target: localBackend, changeOrigin: true },
        '/api/batch': { target: localBackend, changeOrigin: true },
        '/api': {
          target: enterpriseAiUrl,
          changeOrigin: true,
          secure: true,
        },
      },
    },
    build: {
      outDir: 'build',
    },
  };
});
