/**
 * Componente: Paso 2 del Asistente de Paciente (Preguntas Complementarias de IA).
 * Consulta y renderiza de 2 a 3 preguntas clínicas adaptativas orientadas a:
 * 1. Banderas rojas y semiología PQRST adaptada a la especialidad médica.
 * 2. Enfermedades de base y comorbilidades (diabetes, hipertensión, etc.).
 * 3. Medicamentos actuales, tratamientos recientes y alergias.
 */

import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  ArrowLeft,
  Send,
  CheckCircle2,
  Loader2,
  Sparkles,
  AlertCircle,
  FileText,
  HeartPulse,
} from 'lucide-react';
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
      { etiqueta: 'Molestia persistente desde hace más de una semana', valor: 'inicio_cronico' },
    ],
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
      { etiqueta: 'Ninguna enfermedad diagnosticada', valor: 'ninguna' },
    ],
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
      { etiqueta: 'No tomo ningún medicamento de forma regular', valor: 'ninguno' },
    ],
  },
];

export const PasoPreguntasDinamicas = ({
  datos,
  alCambiar,
  alAtras,
  alFinalizar,
  estaEnviando,
}) => {
  const [preguntas, setPreguntas] = useState(PREGUNTAS_FALLBACK_DEFAULT);
  const [cargando, setCargando] = useState(true);
  const [respuestasSeleccionadas, setRespuestasSeleccionadas] = useState(
    datos.respuestas_dinamicas || datos.dynamic_answers || {}
  );
  const [notasAdicionales, setNotasAdicionales] = useState(
    datos.respuestas_dinamicas?.notas_adicionales || ''
  );

  const especialidad = datos.especialidad_solicitada || datos.requested_specialty || 'Medicina General';

  useEffect(() => {
    let montado = true;
    const cargarPreguntas = async () => {
      setCargando(true);
      try {
        const payload = {
          sintomas_brutos: datos.sintomas_brutos || datos.raw_symptoms || 'Malestar general',
          edad: datos.edad || datos.age || 30,
          genero: datos.genero || datos.gender || 'No especificado',
          especialidad_solicitada: especialidad,
          alergias_medicamentosas: datos.alergias_medicamentosas || datos.drug_allergies || 'Ninguna conocida',
          medicacion_actual: datos.medicacion_actual || datos.current_medication || 'Ninguna',
          enfermedades_base: datos.enfermedades_base || datos.base_diseases || [],
        };

        const res = await servicioTriaje.obtenerPreguntasDinamicas(payload);
        const listaPreguntas =
          res?.preguntas || res?.questions || res?.data?.preguntas || res?.data?.questions;

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
  }, [
    datos.sintomas_brutos,
    datos.raw_symptoms,
    datos.edad,
    datos.age,
    datos.genero,
    datos.gender,
    especialidad,
    datos.alergias_medicamentosas,
    datos.medicacion_actual,
  ]);

  const seleccionarOpcion = (idPregunta, valor, tipoPregunta = 'single_choice') => {
    let nuevoValor;

    if (tipoPregunta === 'multiple_choice') {
      const valoresPrevios = Array.isArray(respuestasSeleccionadas[idPregunta])
        ? respuestasSeleccionadas[idPregunta]
        : respuestasSeleccionadas[idPregunta]
        ? [respuestasSeleccionadas[idPregunta]]
        : [];

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
      ...(notasAdicionales ? { notas_adicionales: notasAdicionales } : {}),
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
      ...(notasAdicionales ? { notas_adicionales: notasAdicionales } : {}),
    };
    alFinalizar(respuestasFinales);
  };

  return (
    <form onSubmit={manejarEnvio} className="space-y-6 animate-fade-in text-slate-100">
      {/* Encabezado del Paso con Indicador de IA */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Paso 2 de 3 · Preguntas Adaptativas</span>
          </div>

          <span className="text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700">
            Rama: <strong className="text-teal-300 font-semibold">{especialidad}</strong>
          </span>
        </div>

        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <HelpCircle className="w-6 h-6 text-teal-400" />
          Preguntas de Clarificación Clínica
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          La Inteligencia Artificial ha seleccionado estas preguntas personalizadas para ayudar al médico de guardia a comprender mejor tu cuadro antes de entrar a consulta.
        </p>
      </div>

      {/* Lista de Preguntas o Estado de Carga */}
      {cargando ? (
        <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-3 bg-slate-900/50 rounded-2xl border border-slate-800">
          <Loader2 className="w-8 h-8 text-teal-400 animate-spin" />
          <p className="text-sm font-medium">Analizando síntomas con IA clínica...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {preguntas.map((p, idx) => {
            const idPregunta = p.id || `pregunta_${idx}`;
            const textoPregunta = p.pregunta || p.question_text;
            const tipoPregunta = p.tipo_pregunta || p.question_type || 'single_choice';
            const opciones = p.opciones || p.options || [];
            const respuestaActual = respuestasSeleccionadas[idPregunta];

            return (
              <div
                key={idPregunta}
                className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition"
              >
                <h3 className="text-sm font-semibold text-white mb-1 flex items-start gap-2">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs font-bold mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{textoPregunta}</span>
                </h3>

                <p className="text-[11px] text-slate-400 ml-8 mb-3">
                  {tipoPregunta === 'multiple_choice'
                    ? 'Selecciona una o más opciones que correspondan:'
                    : 'Selecciona la opción más precisa:'}
                </p>

                {/* Opciones de la Pregunta */}
                <div className="grid grid-cols-1 gap-2.5 ml-8">
                  {opciones.map((opc, opcIdx) => {
                    const etiqueta = opc.etiqueta || opc.label || opc;
                    const valor = opc.valor || opc.value || etiqueta;

                    let esSeleccionado = false;
                    if (tipoPregunta === 'multiple_choice') {
                      esSeleccionado =
                        Array.isArray(respuestaActual) && respuestaActual.includes(valor);
                    } else {
                      esSeleccionado = respuestaActual === valor;
                    }

                    return (
                      <button
                        type="button"
                        key={opcIdx}
                        onClick={() => seleccionarOpcion(idPregunta, valor, tipoPregunta)}
                        className={`text-left p-3.5 rounded-xl border text-xs font-medium transition flex items-center justify-between ${
                          esSeleccionado
                            ? 'bg-teal-500/20 border-teal-400 text-teal-200 shadow-sm'
                            : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <span className="pr-3 leading-relaxed">{etiqueta}</span>
                        {esSeleccionado && (
                          <CheckCircle2 className="w-4 h-4 text-teal-400 flex-shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Caja de Comentarios Adicionales */}
          <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-teal-400" />
              <span>¿Deseas agregar algún otro detalle importante? (Opcional)</span>
            </label>
            <textarea
              rows="2"
              value={notasAdicionales}
              onChange={manejarCambioNotas}
              placeholder="Cualquier información adicional que consideres relevante para el médico..."
              className="w-full bg-slate-950/60 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>
        </div>
      )}

      {/* Botones de Navegación */}
      <div className="pt-4 flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={alAtras}
          disabled={estaEnviando}
          className="px-5 py-3 rounded-xl border border-slate-700 bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition flex items-center gap-2 text-sm font-semibold disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Atrás</span>
        </button>

        <button
          type="submit"
          disabled={estaEnviando || cargando}
          className="bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-extrabold py-3 px-8 rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center justify-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {estaEnviando ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
              <span>Generando Código y QR...</span>
            </>
          ) : (
            <>
              <span>Finalizar y Obtener Código QR</span>
              <Send className="w-4 h-4 text-slate-950" />
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export const DynamicQuestionsStep = PasoPreguntasDinamicas;
export default PasoPreguntasDinamicas;
