import React from 'react';

/**
 * Componente principal de la aplicación MediSinc-IA.
 * Sirve como contenedor inicial para el enrutamiento y la maquetación base.
 */
function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-center p-4">
      <header className="text-center max-w-2xl">
        <h1 className="text-4xl font-bold text-sky-400 mb-2">
          MediSinc-IA
        </h1>
        <p className="text-slate-400 text-lg mb-6">
          Sistema Inteligente de Pre-Triaje Clínico y Resumen Asistido por IA
        </p>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
          <p className="text-emerald-400 font-semibold mb-2">
            ✓ Estado de Inicialización: Listo
          </p>
          <p className="text-sm text-slate-300">
            Estructura base de Frontend (React + Vite) y Backend (FastAPI) configurada.
          </p>
        </div>
      </header>
    </div>
  );
}

export default App;
