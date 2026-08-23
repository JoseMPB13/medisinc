import axios from 'axios';
import { getCurrentUser } from './authService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Helper para inyectar headers de autenticación institucional en las llamadas de administración.
 */
const getAuthHeaders = () => {
  const user = getCurrentUser();
  return {
    headers: {
      'Content-Type': 'application/json',
      'X-User-Role': user?.role || 'ADMIN',
      'Authorization': `Bearer ${user?.role === 'ADMIN' ? 'admin-jwt-token' : 'doctor-jwt-token'}`
    }
  };
};

/**
 * Servicio API para el Portal de Administración (Rol ADMIN).
 */
export const adminService = {
  // 1. Obtener métricas estadísticas globales
  getStats: async () => {
    const resp = await axios.get(`${API_BASE_URL}/admin/stats`, getAuthHeaders());
    return resp.data;
  },

  // 2. Listar personal médico
  getDoctors: async (params = {}) => {
    const resp = await axios.get(`${API_BASE_URL}/admin/doctors`, {
      ...getAuthHeaders(),
      params
    });
    return resp.data;
  },

  // 3. Crear nuevo médico o administrador
  createDoctor: async (doctorPayload) => {
    const resp = await axios.post(`${API_BASE_URL}/admin/doctors`, doctorPayload, getAuthHeaders());
    return resp.data;
  },

  // 4. Actualizar médico existente
  updateDoctor: async (doctorId, updatePayload) => {
    const resp = await axios.put(`${API_BASE_URL}/admin/doctors/${doctorId}`, updatePayload, getAuthHeaders());
    return resp.data;
  },

  // 5. Historial global de pacientes
  getPatientHistory: async (params = {}) => {
    const resp = await axios.get(`${API_BASE_URL}/admin/patients/history`, {
      ...getAuthHeaders(),
      params
    });
    return resp.data;
  },

  // 6. Consultar bitácora inalterable de auditoría
  getAuditLogs: async (params = {}) => {
    const resp = await axios.get(`${API_BASE_URL}/admin/audit-logs`, {
      ...getAuthHeaders(),
      params
    });
    return resp.data;
  }
};

export default adminService;
