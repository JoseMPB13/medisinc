import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PatientHome from './pages/PatientHome';

/**
 * Componente Raíz de la Aplicación MediSinc-IA Frontend.
 * Configura el enrutador principal con react-router-dom.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta Pública Principal: Portal del Paciente */}
        <Route path="/" element={<PatientHome />} />

        {/* Redirección por defecto para rutas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
