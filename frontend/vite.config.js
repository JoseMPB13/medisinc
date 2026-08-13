import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Configuración principal de Vite para el proyecto MediSinc-IA
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
});
