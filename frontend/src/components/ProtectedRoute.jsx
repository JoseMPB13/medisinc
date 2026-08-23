import React from 'react';
import { Navigate } from 'react-router-dom';
import { getCurrentUser } from '../services/authService';

/**
 * Componente Wrapper de Rutas Protegidas para el Portal Médico y de Administración.
 * Valida sesión activa y controla acceso granular por rol (DOCTOR, ADMIN).
 */
function ProtectedRoute({ children, allowedRoles }) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = currentUser.role || 'DOCTOR';
    if (!allowedRoles.includes(userRole)) {
      // Redirigir al dashboard correspondiente a su rol si intenta acceder a una ruta no permitida
      return userRole === 'ADMIN' ? (
        <Navigate to="/admin/dashboard" replace />
      ) : (
        <Navigate to="/doctor/dashboard" replace />
      );
    }
  }

  return children;
}

export default ProtectedRoute;
