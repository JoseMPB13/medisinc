/**
 * Enrutador Principal de la Aplicación Frontend MediSinc-IA.
 * Configura las rutas públicas del paciente, inicio de sesión y rutas protegidas médicas y administrativas.
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import InicioPaciente from './paginas/InicioPaciente';
import IniciarSesion from './paginas/IniciarSesion';
import PanelMedico from './paginas/PanelMedico';
import PanelAdministrador from './paginas/PanelAdministrador';
import PantallaSeguimientoPaciente from './paginas/PantallaSeguimientoPaciente';
import RutaProtegida from './componentes/RutaProtegida';

function App() {
  return (
    <Routes>
      {/* 1. Portal Público de Paciente (Pre-Triaje y Comprobante QR) */}
      <Route path="/" element={<InicioPaciente />} />
      <Route path="/paciente" element={<InicioPaciente />} />
      <Route path="/seguimiento/:codigo" element={<PantallaSeguimientoPaciente />} />

      {/* 2. Portal de Autenticación */}
      <Route path="/iniciar-sesion" element={<IniciarSesion />} />
      <Route path="/login" element={<IniciarSesion />} />

      {/* 3. Portal Médico de Guardia (Protegido por Rol MEDICO / DOCTOR) */}
      <Route
        path="/medico"
        element={
          <RutaProtegida rolRequerido={['MEDICO', 'ADMIN']}>
            <PanelMedico />
          </RutaProtegida>
        }
      />
      <Route
        path="/doctor"
        element={
          <RutaProtegida rolRequerido={['MEDICO', 'ADMIN']}>
            <PanelMedico />
          </RutaProtegida>
        }
      />

      {/* 4. Portal de Administración y Auditoría (Protegido por Rol ADMIN) */}
      <Route
        path="/admin"
        element={
          <RutaProtegida rolRequerido="ADMIN">
            <PanelAdministrador />
          </RutaProtegida>
        }
      />

      {/* 5. Ruta por Defecto / Redirección */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
