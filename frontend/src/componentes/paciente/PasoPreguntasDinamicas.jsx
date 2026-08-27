/**
 * Componente: Paso 2 del Asistente de Paciente (Preguntas Complementarias de IA).
 * Consulta y renderiza de 2 a 3 preguntas clínicas adaptativas orientadas a:
 * 1. Banderas rojas y características específicas del padecimiento actual.
 * 2. Enfermedades de base y comorbilidades (diabetes, hipertensión, etc.).
 * 3. Medicamentos actuales o tratamientos recientes.
 */

import React, { useState, useEffect } from 'react';
import { HelpCircle, ArrowLeft, Send, CheckCircle2, Loader2, Sparkles, AlertCircle, FileText, Pill, HeartPulse } from 'lucide-react';
import { servicioTriaje } from '../../servicios/servicioTriaje';

// Preguntas de contingencia inmediata para garantizar que la vista nunca quede vacía
const PREGUNTAS_FALLBACK_DEFAULT = [
  {
    id: 'q_evolucion_sintoma',
    pregunta: '¿Con qué rapidez aparecieron las molestias o síntomas?',
    tipo_pregunta: 'single_choice',
    opciones: [
      { etiqueta: 'Aparición repentina y muy intensa en las últimas horas', valor: 'inicio_agudo_intenso' },
      { etiqueta: 'Malestar progresivo a lo largo de 1 a 3 días', valor: 'inicio_subagudo' },
      { etiqueta: 'Molestia persistente desde hace más de una semana', valor: 'inicio_cronico' }
    ]
  },
  {
    id: 'q_antecedentes_enfermedades',
    pregunta: '¿Padece alguna enfermedad o condición médica previa relevante?',
    tipo_pregunta: 'multiple_choice',
    opciones: [
      { etiqueta: 'Hipertensión arterial (presión alta)', valor: 'hipertension' },
      { etiqueta: 'Diabetes mellitus (azúcar en sangre)', valor: 'diabetes' },
      { etiqueta: 'Problemas del corazón o infarto previo', valor: 'cardiopatia' },
      { etiqueta: 'Asma, bronquitis crónica o EPOC', valor: 'asma_epoc' },
      { etiqueta: 'Enfermedad renal o hepática', valor: 'renal_hepatica' },
      { etiqueta: 'Ninguna enfermedad diagnosticada', valor: 'ninguna' }
    ]
  },
  {
    id: 'q_medicamentos_actuales',
    pregunta: '¿Toma medicamentos habitualmente o ha tomado algo para este malestar?',
    tipo_pregunta: 'multiple_choice',
    opciones: [
      { etiqueta: 'Medicamentos para la presión arterial o el corazón', valor: 'antihipertensivos' },
      { etiqueta: 'Anticoagulantes o aspirina diariamente', valor: 'anticoagulantes' },
      { etiqueta: 'Insulina o pastillas para la diabetes', valor: 'antidiabeticos' },
      { etiqueta: 'Tomé analgésicos o antibióticos en las últimas horas', valor: 'analgesicos_recientes' },
      { etiqueta: 'No tomo ningún medicamento de forma regular', valor: 'ninguno' }
    ]
  }
];

export const PasoPreguntasDinamicas = ({ datos, alCambiar, alAtras, alFinalizar, estaEnviando }) => {
  const [preguntas, setPreguntas] = useState(PREGUNTAS_FALLBACK_DEFAULT);
  const [cargando, setCargando] = useState(true);
  const [respuestasSeleccionadas, setRespuestasSeleccionadas] = useState(
    datos.respuestas_dinamicas || datos.dynamic_answers || {}
  );
  const [notasAdicionales, setNotasAdicionales] = useState(
    datos.respuestas_dinamicas?.notas_adicionales || ''
  );

  useEffect(() => {
    let montado = true;
    const cargarPreguntas = async () => {
      setCargando(true);
      try {
        const sintoma = datos.sintomas_brutos || datos.raw_symptoms || 'Malestar general';
        const edad = datos.edad || datos.age || 30;
        const genero = datos.genero || datos.gender || 'No especificado';

        const res = await servicioTriaje.obtenerPreguntasDinamicas(sintoma, edad, genero);
        const listaPreguntas = res?.preguntas || res?.questions || res?.data?.preguntas || res?.data?.questions;

        if (montado && Array.isArray(listaPreguntas) && listaPreguntas.length > 0) {
          setPreguntas(listaPreguntas);
        } else if (montado) {
          setPreguntas(PREGUNTAS_FALLBACK_DEFAULT);
        }
      } catch (e) {
        console.error('Error al cargar preguntas dinámicas de IA:', e);
        if (montado) {
          setPreguntas(PREGUNTAS_FALLBACK_DEFAULT);
        }
      } finally {
        if (montado) setCargando(false);
      }
    };

    cargarPreguntas();
    return () => {
      montado = false;
    };
  }, [datos.sintomas_brutos, datos.raw_symptoms, datos.edad, datos.age, datos.genero, datos.gender]);

  const seleccionarOpcion = (idPregunta, valor, tipoPregunta = 'single_choice') => {
    let nuevoValor;

    if (tipoPregunta === 'multiple_choice') {
      const valoresPrevios = Array.isArray(respuestasSeleccionadas[idPregunta])
        ? respuestasSeleccionadas[idPregunta]
        : (respuestasSeleccionadas[idPregunta] ? [respuestasSeleccionadas[idPregunta]] : []);

      if (valor === 'ninguno' || valor === 'ninguna') {
        nuevoValor = ['ninguno'];
      } else {
        const sinNinguno = valoresPrevios.filter((v) => v !== 'ninguno' && v !== 'ninguna');
        if (sinNinguno.includes(valor)) {
          nuevoValor = sinNinguno.filter((v) => v !== valor);
        } else {
          nuevoValor = [...sinNinguno, valor];
        }
      }
    } else {
      nuevoValor = valor;
    }

    const nuevasRespuestas = {
      ...respuestasSeleccionadas,
      [idPregunta]: nuevoValor,
      ...(notasAdicionales ? { notas_adicionales: notasAdicionales } : {})
    };

    setRespuestasSeleccionadas(nuevasRespuestas);
    alCambiar('respuestas_dinamicas', nuevasRespuestas);
  };

  const manejarCambioNotas = (e) => {
    const texto = e.target.value;
    setNotasAdicionales(texto);
    const nuevasRespuestas = {
      ...respuestasSeleccionadas,
      notas_adicionales: texto,
    };
    alCambiar('respuestas_dinamicas', nuevasRespuestas);
  };

  const manejarEnvio = (e) => {
    e.preventDefault();
    const respuestasFinales = {
      ...respuestasSeleccionadas,
      ...(notasAdicionales ? { notas_adicionales: notasAdicionales } : {})
    };
    alFinalizar(respuestasFinales);
  };

  if (cargando) {
    return (
      <div className="py-16 text-center space-y-4 animate-fade-in text-slate-100">
        <div className="relative w-16 h-16 mx-auto">
          <div className="absolute inset-0 rounded-full border-4 border-teal-500/20 border-t-teal-400 animate-spin"></div>
          <Sparkles className="w-6 h-6 text-teal-400 absolute inset-0 m-auto animate-pulse" />
        </div>
        <h3 className="text-lg font-bold text-white">Generando preguntas clínicas adaptativas...</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          La Inteligencia Artificial está estructurando preguntas sobre tus síntomas, enfermedades previas y medicamentos.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={manejarEnvio} className="space-y-6 animate-fade-in text-slate-100">
      {/* Encabezado del Paso */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-teal-400" />
            Paso 2: Preguntas Complementarias
          </h2>
          <span className="text-xs font-semibold px-2.5 py-1 bg-teal-500/10 border border-teal-500/30 text-teal-400 rounded-full flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> IA Adaptativa
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Por favor responde estas breves preguntas sobre tu padecimiento, antecedentes médicos y medicamentos para que el médico evalúe tu caso con máxima precisión.
        </p>
      </div>

      {/* Lista de Preguntas Dinámicas */}
      <div className="space-y-6">
        {preguntas.map((item, index) => {
          const id = item.id || `pregunta_${index}`;
          const textoPregunta = item.pregunta || item.question_text || `Pregunta ${index + 1}`;
          const tipo = item.tipo_pregunta || item.question_type || 'single_choice';
          const opciones = item.opciones || item.options || [];
          const respuestaActual = respuestasSeleccionadas[id];

          return (
            <div key={id} className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-lg">
              <div className="flex items-start gap-2 mb-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-500/20 text-teal-400 text-xs font-bold shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-100">{textoPregunta}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {tipo === 'multiple_choice' ? 'Puedes seleccionar una o más opciones' : 'Selecciona la opción que mejor describe tu situación'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                {opciones.map((opc, opcIdx) => {
                  const valor = opc.valor !== undefined ? opc.valor : (opc.value !== undefined ? opc.value : opc);
                  const etiqueta = opc.etiqueta || opc.label || opc;

                  let estaSeleccionado = false;
                  if (Array.isArray(respuestaActual)) {
                    estaSeleccionado = respuestaActual.includes(valor);
                  } else {
                    estaSeleccionado = respuestaActual === valor;
                  }

                  return (
                    <button
                      type="button"
                      key={opcIdx}
                      onClick={() => seleccionarOpcion(id, valor, tipo)}
                      className={`text-left p-3.5 rounded-xl border text-xs font-medium transition flex items-center justify-between ${
                        estaSeleccionado
                          ? 'bg-teal-500/20 border-teal-400 text-teal-200 shadow-md shadow-teal-950/40 ring-1 ring-teal-400/50'
                          : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                      }`}
                    >
                      <span className="leading-relaxed">{etiqueta}</span>
                      {estaSeleccionado ? (
                        <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 ml-2" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0 ml-2" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Campo Opcional: Aclaraciones de medicamentos y antecedentes */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 shadow-lg space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Pill className="w-4 h-4 text-teal-400" />
            <span>Otras enfermedades, medicamentos o alergias no mencionadas (opcional):</span>
          </label>
          <textarea
            rows={2}
            value={notasAdicionales}
            onChange={manejarCambioNotas}
            placeholder="Ej: Soy alérgico a la penicilina, tomo Losartán 50mg cada mañana..."
            className="w-full bg-slate-950/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
          />
        </div>
      </div>

      {/* Botones de Navegación */}
      <div className="pt-4 flex items-center justify-between border-t border-slate-800">
        <button
          type="button"
          onClick={alAtras}
          disabled={estaEnviando}
          className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2.5 px-5 rounded-xl transition flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al Paso 1</span>
        </button>

        <button
          type="submit"
          disabled={estaEnviando}
          className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold py-3 px-8 rounded-xl shadow-lg shadow-emerald-900/30 transition duration-200 flex items-center gap-2 text-sm disabled:opacity-50"
        >
          {estaEnviando ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Procesando Pre-Triaje...</span>
            </>
          ) : (
            <>
              <span>Generar Código y QR</span>
              <Send className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export const DynamicQuestionsStep = PasoPreguntasDinamicas;
export default PasoPreguntasDinamicas;
