/**
 * Servicio de Comunicación con la API de Triaje Clínico de MediSinc-IA.
 * Conecta los formularios del paciente con los endpoints /api/v1/triaje/*.
 */

import axios from 'axios';

const URL_BASE_API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const clienteApi = axios.create({
  baseURL: URL_BASE_API,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const servicioTriaje = {
  /**
   * Envía el pre-triaje capturado del paciente para persistencia y evaluación.
   * @param {Object} datosPaciente - Datos demográficos, síntomas y respuestas dinámicas.
   * @returns {Promise<Object>} Confirmación inmediata con código de acceso y triage_id.
   */
  async enviarTriaje(datosPaciente) {
    try {
      const payload = {
        nombre_paciente: datosPaciente.nombre_paciente || datosPaciente.patient_name,
        patient_name: datosPaciente.nombre_paciente || datosPaciente.patient_name,
        ci: datosPaciente.ci,
        edad: parseInt(datosPaciente.edad || datosPaciente.age, 10),
        age: parseInt(datosPaciente.edad || datosPaciente.age, 10),
        genero: datosPaciente.genero || datosPaciente.gender,
        gender: datosPaciente.genero || datosPaciente.gender,
        sintomas_brutos: datosPaciente.sintomas_brutos || datosPaciente.raw_symptoms,
        raw_symptoms: datosPaciente.sintomas_brutos || datosPaciente.raw_symptoms,
        datos_estaticos: datosPaciente.datos_estaticos || datosPaciente.static_data || {},
        static_data: datosPaciente.datos_estaticos || datosPaciente.static_data || {},
        respuestas_dinamicas: datosPaciente.respuestas_dinamicas || datosPaciente.dynamic_answers || {},
        dynamic_answers: datosPaciente.respuestas_dinamicas || datosPaciente.dynamic_answers || {},
      };

      const respuesta = await clienteApi.post('/api/v1/triaje/procesar', payload);
      return respuesta.data;
    } catch (error) {
      console.error('[servicioTriaje] Error al procesar pre-triaje:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Genera de 2 a 3 preguntas adaptativas de opción múltiple según el síntoma principal.
   * @param {string} sintoma - Motivo de consulta en texto libre.
   * @param {number} edad - Edad del paciente.
   * @param {string} genero - Género del paciente.
   * @returns {Promise<Object>} Lista de preguntas estructuradas con opciones.
   */
  async obtenerPreguntasDinamicas(sintoma, edad = 30, genero = 'No especificado') {
    try {
      const payload = {
        sintomas_brutos: sintoma,
        symptom: sintoma,
        edad: parseInt(edad, 10) || 30,
        age: parseInt(edad, 10) || 30,
        genero: genero,
        gender: genero,
      };

      const respuesta = await clienteApi.post('/api/v1/triaje/preguntas-dinamicas', payload);
      return respuesta.data;
    } catch (error) {
      console.error('[servicioTriaje] Error al obtener preguntas dinámicas:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Consulta el estado de procesamiento del triaje mediante el código de acceso alfanumérico.
   * @param {string} identificador - Código único (ej. MS-8X92K) o ID de triaje.
   * @returns {Promise<Object>} Registro del triaje con prioridad y resultado IA.
   */
  async consultarEstadoTriaje(identificador) {
    try {
      const respuesta = await clienteApi.get(`/api/v1/triaje/estado/${identificador}`);
      return respuesta.data;
    } catch (error) {
      console.error(`[servicioTriaje] Error consultando estado de ${identificador}:`, error);
      throw error.response?.data || error;
    }
  },

  /**
   * Busca un expediente por código de acceso o por Carnet de Identidad.
   * @param {Object} params - { codigo_acceso, ci }
   * @returns {Promise<Object>} Registro encontrado.
   */
  async buscarTriaje(params = {}) {
    try {
      const respuesta = await clienteApi.get('/api/v1/triaje/buscar', { params });
      return respuesta.data;
    } catch (error) {
      console.error('[servicioTriaje] Error buscando expediente:', error);
      throw error.response?.data || error;
    }
  },
};

// Aliases de retrocompatibilidad
export const triageService = {
  submitTriage: servicioTriaje.enviarTriaje,
  getDynamicQuestions: servicioTriaje.obtenerPreguntasDinamicas,
  getTriageStatus: servicioTriaje.consultarEstadoTriaje,
  lookupTriage: servicioTriaje.buscarTriaje,
};

export default servicioTriaje;
