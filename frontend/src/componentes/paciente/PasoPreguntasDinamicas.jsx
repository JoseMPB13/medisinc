/**
 * Componente: Paso 2 del Asistente de Paciente (Preguntas Dinámicas Adaptativas de IA).
 * Consulta y renderiza las preguntas orientadas a descartar banderas rojas clínicas.
 */

import React, { useState, useEffect } from 'react';
import { HelpCircle, ArrowLeft, Send, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import { servicioTriaje } from '../../servicios/servicioTriaje';

export const PasoPreguntasDinamicas = ({ datos, alCambiar, alAtras, alFinalizar, estaEnviando }) => {
  const [preguntas, setPreguntas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [respuestasSeleccionadas, setRespuestasSeleccionadas] = useState(
    datos.respuestas_dinamicas || datos.dynamic_answers || {}
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
        if (montado && res?.preguntas) {
          setPreguntas(res.preguntas);
        }
      } catch (e) {
        console.error('Error al cargar preguntas dinámicas:', e);
      } finally {
        if (montado) setCargando(false);
      }
    };

    cargarPreguntas();
    return () => {
      montado = false;
    };
  }, [datos.sintomas_brutos, datos.raw_symptoms, datos.edad, datos.age, datos.genero, datos.gender]);

  const seleccionarOpcion = (idPregunta, valor) => {
    const nuevasRespuestas = {
      ...respuestasSeleccionadas,
      [idPregunta]: valor,
    };
    setRespuestasSeleccionadas(nuevasRespuestas);
    alCambiar('respuestas_dinamicas', nuevasRespuestas);
  };

  const manejarEnvio = (e) => {
    e.preventDefault();
    alFinalizar(respuestasSeleccionadas);
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
          Analizando tus síntomas con el modelo de Inteligencia Artificial para personalizar el pre-triaje.
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
          Por favor responde estas breves preguntas para ayudar al médico a evaluar la urgencia de tu caso.
        </p>
      </div>

      {/* Lista de Preguntas Dinámicas */}
      <div className="space-y-6">
        {preguntas.map((item, index) => {
          const id = item.id || `pregunta_${index}`;
          const textoPregunta = item.pregunta || item.question_text || `Pregunta ${index + 1}`;
          const opciones = item.opciones || item.options || [];
          const respuestaActual = respuestasSeleccionadas[id];

          return (
            <div key={id} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
              <p className="text-sm font-semibold text-slate-200 mb-3 flex items-start gap-2">
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 text-xs font-bold shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span>{textoPregunta}</span>
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                {opciones.map((opc, opcIdx) => {
                  const valor = opc.valor !== undefined ? opc.valor : (opc.value !== undefined ? opc.value : opc);
                  const etiqueta = opc.etiqueta || opc.label || opc;
                  const estaSeleccionado = respuestaActual === valor;

                  return (
                    <button
                      type="button"
                      key={opcIdx}
                      onClick={() => seleccionarOpcion(id, valor)}
                      className={`text-left p-3 rounded-xl border text-xs font-medium transition flex items-center justify-between ${
                        estaSeleccionado
                          ? 'bg-teal-500/15 border-teal-500 text-teal-300 shadow-md shadow-teal-950/40'
                          : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                      }`}
                    >
                      <span>{etiqueta}</span>
                      {estaSeleccionado && <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 ml-2" />}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
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
