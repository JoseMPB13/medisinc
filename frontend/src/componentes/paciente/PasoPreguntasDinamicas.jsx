/**
 * Componente: Paso 2 del Asistente de Paciente (Preguntas Dinámicas de IA y Antecedentes Clínicos).
 * Presenta:
 * 1. Preguntas adaptativas semiológicas (PQRST) generadas por IA para descarte vital.
 * 2. Antecedentes clínicos estructurados en chips multiselección:
 *    - Alergias a Medicamentos (Ninguna, Penicilina, AINEs, Sulfas, Otros).
 *    - Enfermedades de Base (Ninguna, Hipertensión, Diabetes, Asma/EPOC, Cardiopatía, Gastritis).
 *    - Medicación Habitual (No toma medicación, Antihipertensivos, Insulina, Analgésicos, Otros).
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
  Pill,
  FileHeart,
  AlertTriangle,
  Check,
} from 'lucide-react';
import { servicioTriaje } from '../../servicios/servicioTriaje';

// Preguntas de contingencia inmediata para garantizar que la vista nunca quede vacía
const PREGUNTAS_FALLBACK_DEFAULT = [
  {
    id: 'q_caracteristica_dolor',
    pregunta: '¿Cómo describirías la molestia o dolor principal?',
    tipo_pregunta: 'single_choice',
    opciones: [
      { etiqueta: 'Opresivo o punzada fuerte de inicio repentino', valor: 'agudo_opresivo' },
      { etiqueta: 'Dolor cólico o ardor que va y viene', valor: 'colico_ardor' },
      { etiqueta: 'Pesadez o malestar sordo continuo', valor: 'sordo_continuo' },
    ],
  },
  {
    id: 'q_signos_acompanantes',
    pregunta: '¿Presentas alguno de estos signos de alarma en este momento?',
    tipo_pregunta: 'multiple_choice',
    opciones: [
      { etiqueta: 'Dificultad para respirar o falta de aire al reposar', valor: 'disnea' },
      { etiqueta: 'Fiebre alta, escalofríos o sudoración fría', valor: 'fiebre_chuy' },
      { etiqueta: 'Vómitos continuos o incapacidad de tomar líquidos', valor: 'vomitos_incoercibles' },
      { etiqueta: 'Ninguno de los anteriores', valor: 'ninguno' },
    ],
  },
];

const OPCIONES_ALERGIAS = ['Ninguna', 'Penicilina', 'AINEs / Ibuprofeno', 'Sulfas', 'Otros'];
const OPCIONES_ENFERMEDADES = [
  'Ninguna',
  'Hipertensión Arterial',
  'Diabetes Mellitus',
  'Asma / EPOC',
  'Cardiopatía',
  'Gastritis / Úlcera',
];
const OPCIONES_MEDICACION = [
  'No toma medicación',
  'Antihipertensivos',
  'Hipoglucemiantes / Insulina',
  'Analgésicos / AINEs',
  'Otros',
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
  const [otraAlergiaTexto, setOtraAlergiaTexto] = useState('');
  const [otraMedicacionTexto, setOtraMedicacionTexto] = useState('');

  const especialidad = datos.especialidad_solicitada || datos.requested_specialty || 'Medicina General';
  const alergiasActuales = datos.alergias_medicamentosas || datos.drug_allergies || 'Ninguna';
  const enfermedadesActuales = datos.enfermedades_base || datos.base_diseases || [];
  const medicacionActual = datos.medicacion_actual || datos.current_medication || 'No toma medicación';

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
          alergias_medicamentosas: alergiasActuales,
          medicacion_actual: medicacionActual,
          enfermedades_base: enfermedadesActuales,
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
  ]);

  // Manejo de respuestas a preguntas de IA
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

    const nuevoEstado = {
      ...respuestasSeleccionadas,
      [idPregunta]: nuevoValor,
    };

    setRespuestasSeleccionadas(nuevoEstado);
    alCambiar('respuestas_dinamicas', nuevoEstado);
  };

  // Manejo de Alergias
  const seleccionarAlergiaChip = (opcion) => {
    if (opcion === 'Ninguna') {
      alCambiar('alergias_medicamentosas', 'Ninguna conocida');
      setOtraAlergiaTexto('');
    } else if (opcion === 'Otros') {
      alCambiar('alergias_medicamentosas', otraAlergiaTexto || 'Otra alergia');
    } else {
      alCambiar('alergias_medicamentosas', opcion);
    }
  };

  // Manejo de Enfermedades de Base
  const toggleEnfermedadChip = (opcion) => {
    let nuevasEnfermedades = [...enfermedadesActuales];
    if (opcion === 'Ninguna') {
      nuevasEnfermedades = [];
    } else {
      nuevasEnfermedades = nuevasEnfermedades.filter((e) => e !== 'Ninguna');
      if (nuevasEnfermedades.includes(opcion)) {
        nuevasEnfermedades = nuevasEnfermedades.filter((e) => e !== opcion);
      } else {
        nuevasEnfermedades.push(opcion);
      }
    }
    alCambiar('enfermedades_base', nuevasEnfermedades);
  };

  // Manejo de Medicación Actual
  const seleccionarMedicacionChip = (opcion) => {
    if (opcion === 'No toma medicación') {
      alCambiar('medicacion_actual', 'No toma medicación');
      setOtraMedicacionTexto('');
    } else if (opcion === 'Otros') {
      alCambiar('medicacion_actual', otraMedicacionTexto || 'Otros medicamentos');
    } else {
      alCambiar('medicacion_actual', opcion);
    }
  };

  const manejarEnvio = (e) => {
    e.preventDefault();
    const respuestasFinales = {
      ...respuestasSeleccionadas,
      notas_adicionales: notasAdicionales.trim(),
    };
    alFinalizar(respuestasFinales);
  };

  return (
    <form onSubmit={manejarEnvio} className="space-y-6 animate-fade-in text-slate-100">
      {/* Encabezado del Paso */}
      <div className="border-b border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Paso 2 de 3 · Evaluación Dinámica y Antecedentes</span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Preguntas Complementarias y Antecedentes
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Responde las preguntas para descartar riesgos vitales en{' '}
            <span className="text-teal-300 font-semibold">{especialidad}</span>.
          </p>
        </div>

        {alAtras && (
          <button
            type="button"
            onClick={alAtras}
            className="self-start sm:self-auto text-xs text-slate-400 hover:text-teal-400 border border-slate-700/80 px-3 py-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 transition flex items-center gap-1.5 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Volver a mis datos</span>
          </button>
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 1: PREGUNTAS DINÁMICAS DE IA (SEMIOLOGÍA PQRST) */}
      {/* ========================================================================= */}
      <div className="space-y-5">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
          <HeartPulse className="w-4 h-4" />
          <span>Semiología del Cuadro Actual</span>
        </div>

        {cargando ? (
          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-teal-400" />
            <p className="text-xs font-medium">Analizando síntomas con Inteligencia Médica...</p>
          </div>
        ) : (
          preguntas.map((item, index) => {
            const idPregunta = item.id || `pregunta_${index}`;
            const tipo = item.tipo_pregunta || item.tipo || 'single_choice';
            const opciones = item.opciones || item.options || [];
            const respuestaActual = respuestasSeleccionadas[idPregunta];

            return (
              <div
                key={idPregunta}
                className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md"
              >
                <div className="flex items-start gap-2.5">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-teal-500/20 text-teal-300 font-black text-xs flex items-center justify-center border border-teal-500/30">
                    {index + 1}
                  </span>
                  <h3 className="font-bold text-sm text-slate-100 leading-snug">
                    {item.pregunta || item.texto_pregunta}
                  </h3>
                </div>

                {/* Opciones de Respuesta */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                  {opciones.map((opc, opcIdx) => {
                    const valor = typeof opc === 'object' ? opc.valor || opc.value : opc;
                    const etiqueta =
                      typeof opc === 'object'
                        ? opc.etiqueta || opc.label || opc.texto || valor
                        : opc;

                    const estaSeleccionado =
                      tipo === 'multiple_choice'
                        ? Array.isArray(respuestaActual) && respuestaActual.includes(valor)
                        : respuestaActual === valor;

                    return (
                      <button
                        key={opcIdx}
                        type="button"
                        onClick={() => seleccionarOpcion(idPregunta, valor, tipo)}
                        className={`p-3.5 rounded-xl border text-left text-xs font-medium transition flex items-center justify-between gap-2 cursor-pointer ${
                          estaSeleccionado
                            ? 'bg-teal-500/15 border-teal-400 text-teal-200 ring-1 ring-teal-500/30'
                            : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <span>{etiqueta}</span>
                        {estaSeleccionado && (
                          <CheckCircle2 className="w-4 h-4 text-teal-400 flex-shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 2: ANTECEDENTES CLÍNICOS EN CHIPS MULTISELECCIÓN */}
      {/* ========================================================================= */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
          <FileHeart className="w-4 h-4" />
          <span>Antecedentes Médicos y Factores de Riesgo</span>
        </div>

        {/* 1. Alergias a Medicamentos */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              ¿Tienes alguna alergia conocida a medicamentos?
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {OPCIONES_ALERGIAS.map((opc) => {
              const seleccionado =
                opc === 'Ninguna'
                  ? alergiasActuales === 'Ninguna' || alergiasActuales === 'Ninguna conocida'
                  : opc === 'Otros'
                  ? alergiasActuales !== 'Ninguna' &&
                    alergiasActuales !== 'Ninguna conocida' &&
                    !['Penicilina', 'AINEs / Ibuprofeno', 'Sulfas'].includes(alergiasActuales)
                  : alergiasActuales === opc;

              return (
                <button
                  key={opc}
                  type="button"
                  onClick={() => seleccionarAlergiaChip(opc)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition flex items-center gap-1.5 cursor-pointer ${
                    seleccionado
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {seleccionado && <Check className="w-3.5 h-3.5 text-amber-400" />}
                  <span>{opc}</span>
                </button>
              );
            })}
          </div>

          {alergiasActuales !== 'Ninguna' &&
            alergiasActuales !== 'Ninguna conocida' &&
            !['Penicilina', 'AINEs / Ibuprofeno', 'Sulfas'].includes(alergiasActuales) && (
              <input
                type="text"
                value={otraAlergiaTexto}
                onChange={(e) => {
                  setOtraAlergiaTexto(e.target.value);
                  alCambiar('alergias_medicamentosas', e.target.value || 'Otra alergia');
                }}
                placeholder="Escribe a qué medicamento eres alérgico(a)..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 mt-2"
              />
            )}
        </div>

        {/* 2. Enfermedades de Base / Comorbilidades */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
          <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
            <HeartPulse className="w-4 h-4 text-teal-400" />
            ¿Padeces alguna enfermedad previa diagnosticada?
          </span>

          <div className="flex flex-wrap gap-2">
            {OPCIONES_ENFERMEDADES.map((opc) => {
              const seleccionado =
                opc === 'Ninguna'
                  ? enfermedadesActuales.length === 0
                  : enfermedadesActuales.includes(opc);

              return (
                <button
                  key={opc}
                  type="button"
                  onClick={() => toggleEnfermedadChip(opc)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition flex items-center gap-1.5 cursor-pointer ${
                    seleccionado
                      ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {seleccionado && <Check className="w-3.5 h-3.5 text-teal-400" />}
                  <span>{opc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Medicación Habitual */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
          <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
            <Pill className="w-4 h-4 text-teal-400" />
            ¿Tomas medicamentos habitualmente o para este malestar?
          </span>

          <div className="flex flex-wrap gap-2">
            {OPCIONES_MEDICACION.map((opc) => {
              const seleccionado =
                opc === 'No toma medicación'
                  ? medicacionActual === 'No toma medicación' || medicacionActual === 'Ninguna'
                  : opc === 'Otros'
                  ? medicacionActual !== 'No toma medicación' &&
                    medicacionActual !== 'Ninguna' &&
                    !['Antihipertensivos', 'Hipoglucemiantes / Insulina', 'Analgésicos / AINEs'].includes(medicacionActual)
                  : medicacionActual === opc;

              return (
                <button
                  key={opc}
                  type="button"
                  onClick={() => seleccionarMedicacionChip(opc)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition flex items-center gap-1.5 cursor-pointer ${
                    seleccionado
                      ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {seleccionado && <Check className="w-3.5 h-3.5 text-teal-400" />}
                  <span>{opc}</span>
                </button>
              );
            })}
          </div>

          {medicacionActual !== 'No toma medicación' &&
            medicacionActual !== 'Ninguna' &&
            !['Antihipertensivos', 'Hipoglucemiantes / Insulina', 'Analgésicos / AINEs'].includes(medicacionActual) && (
              <input
                type="text"
                value={otraMedicacionTexto}
                onChange={(e) => {
                  setOtraMedicacionTexto(e.target.value);
                  alCambiar('medicacion_actual', e.target.value || 'Otros medicamentos');
                }}
                placeholder="Escribe qué medicamentos o pastillas tomas..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 mt-2"
              />
            )}
        </div>
      </div>

      {/* Campo Opcional de Notas o Comentarios Adicionales */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Información Adicional (Opcional)
        </label>
        <textarea
          rows="2"
          value={notasAdicionales}
          onChange={(e) => setNotasAdicionales(e.target.value)}
          placeholder="Si tienes algún otro síntoma o detalle para el médico, puedes escribirlo aquí..."
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition resize-none"
        />
      </div>

      {/* Botones de Navegación Final */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-4">
        {alAtras && (
          <button
            type="button"
            onClick={alAtras}
            disabled={estaEnviando}
            className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-2 text-xs font-bold disabled:opacity-50 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Atrás</span>
          </button>
        )}

        <button
          type="submit"
          disabled={estaEnviando}
          className="ml-auto bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-black py-3 px-8 rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center gap-2 text-xs disabled:opacity-50 cursor-pointer"
        >
          {estaEnviando ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
              <span>Generando Comprobante QR...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4 text-slate-950" />
              <span>Finalizar Pre-Triaje y Obtener QR</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export default PasoPreguntasDinamicas;
