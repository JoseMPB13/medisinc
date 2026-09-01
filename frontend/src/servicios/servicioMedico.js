/**
 * Servicio de Comunicación con la API Médica y Flujo Hospitalario de MediSinc-IA.
 * Conexión a endpoints en español con autenticación Bearer JWT y control de concurrencia.
 */

import axios from 'axios';
import { servicioAutenticacion } from './servicioAutenticacion';

// URL Base configurable mediante variables de entorno (Vite) con soporte para red local
const URL_BASE_API = (
  import.meta.env.VITE_API_BASE_URL
  || import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' && window.location.hostname ? `http://${window.location.hostname}:8000` : 'http://localhost:8000')
).replace(/\/api\/v1\/?$/, '');

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
   * @param {string} [especialidad=null] - Filtrar por especialidad médica solicitada
   */
  async obtenerPanelGuardia(soloDisponibles = false, especialidad = null) {
    let url = `${URL_BASE_API}/api/v1/medico/panel?solo_disponibles=${soloDisponibles}`;
    if (especialidad && especialidad !== 'Todas') {
      url += `&especialidad=${encodeURIComponent(especialidad)}`;
    }
    const res = await axios.get(url, obtenerCabeceras());
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

  /**
   * Cambia el estado de disponibilidad del médico (Activo/Inactivo).
   * @param {boolean} estadoActivo - true para Activo, false para Inactivo
   */
  async cambiarEstadoDisponibilidad(estadoActivo) {
    const res = await axios.put(
      `${URL_BASE_API}/api/v1/medico/estado`,
      { esta_activo: estadoActivo },
      obtenerCabeceras()
    );
    return res.data;
  },

};

// Aliases para retrocompatibilidad
export const doctorService = {
  getTriageQueue: (soloDisp = false, esp = null) => servicioMedico.obtenerPanelGuardia(soloDisp, esp),
  getMyPatients: servicioMedico.obtenerMisPacientes,
  assignPatient: servicioMedico.asignarPaciente,
  releasePatient: servicioMedico.liberarPaciente,
  getPatientRecord: servicioMedico.obtenerExpedientePaciente,
  submitReview: servicioMedico.guardarRevisionMedica,
};
