import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PatientHome from './pages/PatientHome';
import Login from './pages/Login';
import DoctorDashboard from './pages/DoctorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';

/**
 * Componente Raíz de la Aplicación MediSinc-IA Frontend.
 * Configura las rutas públicas para pacientes (1), portal médico (2) y portal de administración (3).
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 1. Portal Público del Paciente: Pre-Triaje Clínico Inteligente */}
        <Route path="/" element={<PatientHome />} />

        {/* Ruta de Inicio de Sesión Institucional */}
        <Route path="/login" element={<Login />} />

        {/* 2. Portal Médico: Dashboard de Urgencias y Lista de Espera */}
        <Route
          path="/doctor/dashboard"
          element={
            <ProtectedRoute allowedRoles={['DOCTOR', 'ADMIN']}>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/doctor/patient/:id"
          element={
            <ProtectedRoute allowedRoles={['DOCTOR', 'ADMIN']}>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />

        {/* 3. Portal de Administración: CRUD Médicos, Historial Global y Bitácora AUDIT_LOG */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Redirección por defecto */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
