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
   * Consulta el catálogo de especialidades médicas con conteo de médicos activos en turno.
   * @returns {Promise<Array>} Lista de especialidades estructuradas.
   */
  async obtenerEspecialidades() {
    try {
      const respuesta = await clienteApi.get('/api/v1/triaje/especialidades');
      return respuesta.data;
    } catch (error) {
      console.warn('[servicioTriaje] Error consultando especialidades, usando catálogo de contingencia:', error);
      return [
        { id: 'medicina_general', nombre: 'Medicina General', icono: 'Stethoscope', descripcion: 'Atención primaria integral y evaluación clínica general.', medicos_activos_turno: 1 },
        { id: 'pediatria', nombre: 'Pediatría', icono: 'Baby', descripcion: 'Atención médica para lactantes, niños y adolescentes.', medicos_activos_turno: 1 },
        { id: 'ginecologia', nombre: 'Ginecología y Obstetricia', icono: 'HeartHandshake', descripcion: 'Salud femenina, control prenatal y urgencias ginecológicas.', medicos_activos_turno: 0 },
        { id: 'traumatologia', nombre: 'Traumatología y Urgencias', icono: 'Bone', descripcion: 'Lesiones óseas, musculares, contusiones y traumatismos.', medicos_activos_turno: 0 },
        { id: 'cardiologia', nombre: 'Cardiología y Medicina Interna', icono: 'HeartPulse', descripcion: 'Dolor torácico, hipertensión y patologías de adultos.', medicos_activos_turno: 0 },
        { id: 'odontologia', nombre: 'Odontología', icono: 'Smile', descripcion: 'Dolor dental agudo, infecciones y urgencias bucales.', medicos_activos_turno: 0 },
      ];
    }
  },

  /**
   * Envía el pre-triaje capturado del paciente para persistencia y evaluación.
   * @param {Object} datosPaciente - Datos demográficos, especialidad, antecedentes, síntomas y respuestas dinámicas.
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
        especialidad_solicitada: datosPaciente.especialidad_solicitada || datosPaciente.requested_specialty || 'Medicina General',
        requested_specialty: datosPaciente.especialidad_solicitada || datosPaciente.requested_specialty || 'Medicina General',
        alergias_medicamentosas: datosPaciente.alergias_medicamentosas || datosPaciente.drug_allergies || 'Ninguna conocida',
        drug_allergies: datosPaciente.alergias_medicamentosas || datosPaciente.drug_allergies || 'Ninguna conocida',
        medicacion_actual: datosPaciente.medicacion_actual || datosPaciente.current_medication || 'Ninguna',
        current_medication: datosPaciente.medicacion_actual || datosPaciente.current_medication || 'Ninguna',
        enfermedades_base: datosPaciente.enfermedades_base || datosPaciente.base_diseases || [],
        base_diseases: datosPaciente.enfermedades_base || datosPaciente.base_diseases || [],
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
   * Genera de 2 a 3 preguntas adaptativas de opción múltiple según el síntoma principal y la especialidad.
   * @param {Object|string} payloadOpciones - Payload de parámetros o motivo de consulta.
   * @param {number} [edad=30] - Edad del paciente (si se usa formato posicional).
   * @param {string} [genero='No especificado'] - Género del paciente.
   * @returns {Promise<Object>} Lista de preguntas estructuradas con opciones.
   */
  async obtenerPreguntasDinamicas(payloadOpciones, edad = 30, genero = 'No especificado') {
    try {
      let payload = {};

      if (typeof payloadOpciones === 'object' && payloadOpciones !== null) {
        payload = {
          sintomas_brutos: payloadOpciones.sintomas_brutos || payloadOpciones.symptom || '',
          symptom: payloadOpciones.sintomas_brutos || payloadOpciones.symptom || '',
          edad: parseInt(payloadOpciones.edad || payloadOpciones.age, 10) || 30,
          age: parseInt(payloadOpciones.edad || payloadOpciones.age, 10) || 30,
          genero: payloadOpciones.genero || payloadOpciones.gender || 'No especificado',
          gender: payloadOpciones.genero || payloadOpciones.gender || 'No especificado',
          especialidad_solicitada: payloadOpciones.especialidad_solicitada || payloadOpciones.requested_specialty || 'Medicina General',
          requested_specialty: payloadOpciones.especialidad_solicitada || payloadOpciones.requested_specialty || 'Medicina General',
          alergias_medicamentosas: payloadOpciones.alergias_medicamentosas || payloadOpciones.drug_allergies || 'Ninguna conocida',
          drug_allergies: payloadOpciones.alergias_medicamentosas || payloadOpciones.drug_allergies || 'Ninguna conocida',
          medicacion_actual: payloadOpciones.medicacion_actual || payloadOpciones.current_medication || 'Ninguna',
          current_medication: payloadOpciones.medicacion_actual || payloadOpciones.current_medication || 'Ninguna',
          enfermedades_base: payloadOpciones.enfermedades_base || payloadOpciones.base_diseases || [],
          base_diseases: payloadOpciones.enfermedades_base || payloadOpciones.base_diseases || [],
        };
      } else {
        payload = {
          sintomas_brutos: payloadOpciones,
          symptom: payloadOpciones,
          edad: parseInt(edad, 10) || 30,
          age: parseInt(edad, 10) || 30,
          genero: genero,
          gender: genero,
          especialidad_solicitada: 'Medicina General',
          requested_specialty: 'Medicina General',
          alergias_medicamentosas: 'Ninguna conocida',
          drug_allergies: 'Ninguna conocida',
          medicacion_actual: 'Ninguna',
          current_medication: 'Ninguna',
          enfermedades_base: [],
          base_diseases: [],
        };
      }

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
      console.error('[servicioTriaje] Error en búsqueda de expediente:', error);
      throw error.response?.data || error;
    }
  },
};

// Aliases para retrocompatibilidad con código existente
export const triageService = {
  getSpecialties: servicioTriaje.obtenerEspecialidades,
  submitTriage: servicioTriaje.enviarTriaje,
  getDynamicQuestions: servicioTriaje.obtenerPreguntasDinamicas,
  getTriageStatus: servicioTriaje.consultarEstadoTriaje,
  lookupTriage: servicioTriaje.buscarTriaje,
};
