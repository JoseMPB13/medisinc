import axios from 'axios';

/**
 * Cliente Axios configurado para consumir los endpoints de MediSinc-IA Backend.
 * Utiliza VITE_API_BASE_URL con fallback a localhost:8000/api/v1.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Solicita de 2 a 3 preguntas adaptativas según el síntoma principal y edad del paciente.
 * 
 * @param {string} symptom - Síntoma manifestado por el paciente.
 * @param {number} age - Edad del paciente.
 * @returns {Promise<Object>} Listado de preguntas dinámicas devuelto por la API.
 */
export const getDynamicQuestions = async (symptom, age) => {
  try {
    const response = await apiClient.post('/triage/dynamic-questions', {
      symptom,
      age: parseInt(age, 10) || 0,
    });
    return response.data;
  } catch (error) {
    console.error('Error obteniendo preguntas dinámicas:', error);
    throw error;
  }
};

/**
 * Envía los datos del pre-triaje completo para registro y procesamiento asíncrono.
 * 
 * @param {Object} patientData - Datos personales, síntoma, respuestas dinámicas e intensidad.
 * @returns {Promise<Object>} Respuesta inmediata con el código de acceso (ej. MS-LMXGP).
 */
export const submitTriage = async (patientData) => {
  try {
    const payload = {
      patient_name: patientData.patientName,
      ci: patientData.ci,
      age: parseInt(patientData.age, 10) || 0,
      gender: patientData.gender,
      raw_symptoms: patientData.rawSymptoms,
      static_data: {
        intensidad: parseInt(patientData.intensity, 10) || 5,
        duracion: patientData.duration || 'No especificado',
      },
      dynamic_answers: patientData.dynamicAnswers || {},
    };

    const response = await apiClient.post('/triage/process', payload);
    return response.data;
  } catch (error) {
    console.error('Error enviando pre-triaje:', error);
    throw error;
  }
};

/**
 * Consulta el estado actual de un registro de triaje (polling RECEIVED -> READY -> REVIEWED).
 * 
 * @param {string} identifier - Código de acceso alfanumérico o ID de triaje.
 * @returns {Promise<Object>} Registro completo con el estado y resumen estructurado por IA.
 */
export const checkTriageStatus = async (identifier) => {
  try {
    const response = await apiClient.get(`/triage/status/${identifier}`);
    return response.data;
  } catch (error) {
    console.error(`Error consultando estado para ${identifier}:`, error);
    throw error;
  }
};

export default {
  getDynamicQuestions,
  submitTriage,
  checkTriageStatus,
};
