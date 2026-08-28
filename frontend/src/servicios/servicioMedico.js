/**
 * Servicio de Comunicación con la API Médica y Flujo Hospitalario de MediSinc-IA.
 * Conexión a endpoints en español con autenticación Bearer JWT y control de concurrencia.
 */

import axios from 'axios';
import { servicioAutenticacion } from './servicioAutenticacion';

const URL_BASE_API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const obtenerCabeceras = () => {
  const token = servicioAutenticacion.obtenerToken();
  return {
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  };
};

export const servicioMedico = {
  /**
   * Obtiene la lista de guardia y métricas cuantitativas en tiempo real.
   * @param {boolean} soloDisponibles - Filtrar únicamente pacientes sin médico asignado
   */
  async obtenerPanelGuardia(soloDisponibles = false) {
    const res = await axios.get(
      `${URL_BASE_API}/api/v1/medico/panel?solo_disponibles=${soloDisponibles}`,
      obtenerCabeceras()
    );
    return res.data;
  },

  /**
   * Obtiene la lista de pacientes bajo atención directa del médico autenticado.
   * @param {boolean} incluirRevisados - Incluir consultas cerradas en el histórico
   */
  async obtenerMisPacientes(incluirRevisados = false) {
    const res = await axios.get(
      `${URL_BASE_API}/api/v1/medico/mis-pacientes?incluir_revisados=${incluirRevisados}`,
      obtenerCabeceras()
    );
    return res.data;
  },

  /**
   * Reclama un paciente de la cola general y lo asigna al médico actual (Estado -> EN_CONSULTA).
   * Control de concurrencia: Retorna HTTP 409 si el paciente ya fue tomado por otro colega.
   * @param {string} triajeId - ID o código del registro de triaje
   */
  async asignarPaciente(triajeId) {
    const res = await axios.post(
      `${URL_BASE_API}/api/v1/medico/asignar/${triajeId}`,
      {},
      obtenerCabeceras()
    );
    return res.data;
  },

  /**
   * Libera un paciente en consulta devolviéndolo a la cola general en estado 'LISTO'.
   * @param {string} triajeId - ID o código del registro de triaje
   */
  async liberarPaciente(triajeId) {
    const res = await axios.post(
      `${URL_BASE_API}/api/v1/medico/liberar/${triajeId}`,
      {},
      obtenerCabeceras()
    );
    return res.data;
  },

  /**
   * Obtiene el expediente clínico completo con CI descifrado en memoria y datos sanitizados.
   * @param {string} triajeId - ID o código de acceso del paciente
   */
  async obtenerExpedientePaciente(triajeId) {
    const res = await axios.get(
      `${URL_BASE_API}/api/v1/medico/paciente/${triajeId}`,
      obtenerCabeceras()
    );
    return res.data;
  },

  /**
   * Registra el diagnóstico presuntivo, conducta y cierre de consulta (Estado -> REVISADO).
   * @param {object} datosRevision - { triaje_id, medico_id, notas_medico, prioridad_ajustada }
   */
  async guardarRevisionMedica(datosRevision) {
    const res = await axios.post(
      `${URL_BASE_API}/api/v1/medico/revisar`,
      datosRevision,
      obtenerCabeceras()
    );
    return res.data;
  },
};

// Aliases para retrocompatibilidad
export const doctorService = {
  getGuardDashboard: (onlyAvailable) => servicioMedico.obtenerPanelGuardia(onlyAvailable),
  getMyPatients: (includeReviewed) => servicioMedico.obtenerMisPacientes(includeReviewed),
  assignPatient: (triageId) => servicioMedico.asignarPaciente(triageId),
  releasePatient: (triageId) => servicioMedico.liberarPaciente(triageId),
  getPatientRecord: (triageId) => servicioMedico.obtenerExpedientePaciente(triageId),
  saveMedicalReview: (reviewData) => servicioMedico.guardarRevisionMedica(reviewData),
};
