import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Configuración principal de Vite para el proyecto MediSinc-IA
export default defineConfig({
  plugins: [react()],
  envDir: '../', // Carga el archivo .env desde la raíz del proyecto
  server: {
    port: 5173,
    host: true
  }
});
