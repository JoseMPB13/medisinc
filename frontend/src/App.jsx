import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PatientHome from './pages/PatientHome';
import Login from './pages/Login';
import DoctorDashboard from './pages/DoctorDashboard';
import ProtectedRoute from './components/ProtectedRoute';

/**
 * Componente Raíz de la Aplicación MediSinc-IA Frontend.
 * Configura las rutas públicas para pacientes y las rutas protegidas para profesionales médicos.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta Pública Principal: Portal de Pre-Triaje del Paciente */}
        <Route path="/" element={<PatientHome />} />

        {/* Ruta Pública de Autenticación Institucional Médica */}
        <Route path="/login" element={<Login />} />

        {/* Rutas Protegidas del Portal Médico */}
        <Route
          path="/doctor/dashboard"
          element={
            <ProtectedRoute>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/doctor/patient/:id"
          element={
            <ProtectedRoute>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />

        {/* Redirección por defecto para rutas no existentes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
