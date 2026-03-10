import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
   const env = loadEnv(mode, process.cwd(), '');

   return {
      plugins: [react(), tailwindcss()],
      resolve: {
         alias: {
            '@': path.resolve(__dirname, './src'),
         },
      },
      server: {
         port: 3000,
         host: true,
         proxy: {
            '/api': {
               target: env.BACKEND_URL,
               changeOrigin: true,
            },
         },
      },
   };
});
