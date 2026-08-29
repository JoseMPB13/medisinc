/**
 * Servicio de Comunicación para el Portal de Administración y Auditoría de MediSinc-IA.
 * Conecta con los endpoints /api/v1/admin/*.
 */

import axios from 'axios';
import { servicioAutenticacion } from './servicioAutenticacion';

const URL_BASE_API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const clienteApiAdmin = axios.create({
  baseURL: URL_BASE_API,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Interceptor para inyectar token de autenticación
clienteApiAdmin.interceptors.request.use((config) => {
  const token = servicioAutenticacion.obtenerToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const servicioAdmin = {
  /**
   * Obtiene las métricas cuantitativas consolidadas del centro de salud.
   * @returns {Promise<Object>} Estadísticas globales en tiempo real.
   */
  async obtenerEstadisticasAdmin() {
    try {
      const respuesta = await clienteApiAdmin.get('/api/v1/admin/estadisticas');
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al obtener estadísticas:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Obtiene la lista de profesionales médicos registrados.
   * @param {Object} filtros - { rol, esta_activo, busqueda }
   * @returns {Promise<Array>} Lista de perfiles.
   */
  async listarMedicos(filtros = {}) {
    try {
      const respuesta = await clienteApiAdmin.get('/api/v1/admin/medicos', { params: filtros });
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al listar médicos:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Registra una nueva cuenta de médico o administrador en la plataforma.
   * @param {Object} datosMedico - { nombre_completo, correo, password, especialidad, rol }
   * @returns {Promise<Object>} Registro creado.
   */
  async crearMedico(datosMedico) {
    try {
      const payload = {
        nombre_completo: datosMedico.nombre_completo || datosMedico.full_name,
        full_name: datosMedico.nombre_completo || datosMedico.full_name,
        correo: datosMedico.correo || datosMedico.email,
        email: datosMedico.correo || datosMedico.email,
        password: datosMedico.password,
        especialidad: datosMedico.especialidad || datosMedico.specialty || 'Medicina General',
        specialty: datosMedico.especialidad || datosMedico.specialty || 'Medicina General',
        rol: datosMedico.rol || datosMedico.role || 'MEDICO',
        role: datosMedico.rol || datosMedico.role || 'MEDICO',
      };
      const respuesta = await clienteApiAdmin.post('/api/v1/admin/medicos', payload);
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al crear médico:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Actualiza el perfil, especialidad, turno de guardia y estado de un médico.
   * @param {string} medicoId - ID del facultativo.
   * @param {Object} datosMedico - { nombre_completo, especialidad, rol, turno_asignado, dias_guardia, esta_activo }
   * @returns {Promise<Object>} Registro actualizado.
   */
  async actualizarMedico(medicoId, datosMedico) {
    try {
      const payload = {
        nombre_completo: datosMedico.nombre_completo || datosMedico.full_name,
        especialidad: datosMedico.especialidad || datosMedico.specialty,
        rol: datosMedico.rol || datosMedico.role,
        turno_asignado: datosMedico.turno_asignado || datosMedico.assigned_shift,
        dias_guardia: datosMedico.dias_guardia || datosMedico.duty_days,
        esta_activo: datosMedico.esta_activo !== undefined ? datosMedico.esta_activo : datosMedico.is_active,
      };
      const respuesta = await clienteApiAdmin.put(`/api/v1/admin/medicos/${medicoId}`, payload);
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al actualizar médico:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Consulta la bitácora inalterable de auditoría.
   * @param {number} limite - Cantidad de registros (por defecto 50).
   * @param {string} accion - Filtro opcional por tipo de acción.
   * @returns {Promise<Array>} Lista de eventos de auditoría.
   */
  async listarRegistrosAuditoria(limite = 50, accion = null) {
    try {
      const params = { limit: limite };
      if (accion) params.action = accion;
      const respuesta = await clienteApiAdmin.get('/api/v1/admin/registros-auditoria', { params });
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al obtener auditoría:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Obtiene el historial consolidado de pacientes recibidos.
   * @returns {Promise<Array>} Lista histórica de triajes.
   */
  async listarPacientesHistorico() {
    try {
      const respuesta = await clienteApiAdmin.get('/api/v1/admin/pacientes');
      return respuesta.data;
    } catch (error) {
      console.error('[servicioAdmin] Error al listar pacientes:', error);
      throw error.response?.data || error;
    }
  },
};

// Aliases de retrocompatibilidad
export const adminService = {
  getAdminStats: servicioAdmin.obtenerEstadisticasAdmin,
  listDoctors: servicioAdmin.listarMedicos,
  createDoctor: servicioAdmin.crearMedico,
  getAuditLogs: servicioAdmin.listarRegistrosAuditoria,
  listHistoricalPatients: servicioAdmin.listarPacientesHistorico,
};

export default servicioAdmin;
