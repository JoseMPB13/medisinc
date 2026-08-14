import React from 'react';
import { Navigate } from 'react-router-dom';
import { getCurrentUser } from '../services/authService';

/**
 * Componente Wrapper de Rutas Protegidas para el Portal Médico.
 * Verifica si existe una sesión médica activa. Si no, redirige a /login.
 */
function ProtectedRoute({ children }) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
