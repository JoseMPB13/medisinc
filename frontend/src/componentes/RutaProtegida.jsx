/**
 * Componente Guardián de Rutas Protegidas en React.
 * Valida la existencia del token JWT y el rol requerido del usuario (MEDICO / ADMIN).
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';

export const RutaProtegida = ({ children, rolRequerido, requiredRole }) => {
  const ubicacion = useLocation();
  const usuario = servicioAutenticacion.obtenerUsuarioActual();
  const rolEsperado = rolRequerido || requiredRole;

  if (!usuario || !servicioAutenticacion.estaAutenticado()) {
    return <Navigate to="/iniciar-sesion" state={{ from: ubicacion }} replace />;
  }

  if (rolEsperado) {
    const rolesPermitidos = Array.isArray(rolEsperado) ? rolEsperado : [rolEsperado];
    // Soporte bilingüe para roles
    const rolUsuario = usuario.rol || usuario.role;
    const esValido = rolesPermitidos.some(
      (r) => r.toUpperCase() === rolUsuario?.toUpperCase() || (r === 'MEDICO' && rolUsuario === 'DOCTOR') || (r === 'DOCTOR' && rolUsuario === 'MEDICO')
    );

    if (!esValido) {
      return <Navigate to="/" replace />;
    }
  }

  return children;
};

export const ProtectedRoute = RutaProtegida;
export default RutaProtegida;
