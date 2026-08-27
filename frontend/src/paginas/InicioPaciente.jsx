/**
 * Página Principal del Asistente de Paciente (MediSinc-IA).
 * Implementa el flujo Wizard de 3 pasos para la captura y estructuración del pre-triaje.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Stethoscope, Shield, HeartPulse, Activity, Check } from 'lucide-react';
import PasoDatosEstaticos from '../componentes/paciente/PasoDatosEstaticos';
import PasoPreguntasDinamicas from '../componentes/paciente/PasoPreguntasDinamicas';
import PasoConfirmacionQR from '../componentes/paciente/PasoConfirmacionQR';
import { servicioTriaje } from '../servicios/servicioTriaje';

export const InicioPaciente = () => {
  const [pasoActual, setPasoActual] = useState(1);
  const [datosFormulario, setDatosFormulario] = useState({
    nombre_paciente: '',
    ci: '',
    edad: '',
    genero: '',
    sintomas_brutos: '',
    datos_estaticos: {
      duracion: '2 a 6 horas',
      intensidad: 5,
    },
    respuestas_dinamicas: {},
  });
  const [resultadoTriaje, setResultadoTriaje] = useState(null);
  const [estaEnviando, setEstaEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState(null);

  const actualizarCampo = (campo, valor) => {
    setDatosFormulario((prev) => ({
      ...prev,
      [campo]: valor,
    }));
  };

  const enviarPreTriajeFinal = async (respuestasDinamicas) => {
    setEstaEnviando(true);
    setErrorEnvio(null);
    try {
      const payloadCompleto = {
        ...datosFormulario,
        respuestas_dinamicas: respuestasDinamicas,
      };

      const res = await servicioTriaje.enviarTriaje(payloadCompleto);
      setResultadoTriaje(res);
      setPasoActual(3);
    } catch (err) {
      console.error('Error al enviar pre-triaje:', err);
      setErrorEnvio(err.detail || 'Ocurrió un error al procesar tu solicitud. Intenta nuevamente.');
    } finally {
      setEstaEnviando(false);
    }
  };

  const reiniciarFormulario = () => {
    setDatosFormulario({
      nombre_paciente: '',
      ci: '',
      edad: '',
      genero: '',
      sintomas_brutos: '',
      datos_estaticos: {
        duracion: '2 a 6 horas',
        intensidad: 5,
      },
      respuestas_dinamicas: {},
    });
    setResultadoTriaje(null);
    setPasoActual(1);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-teal-500 selection:text-white">
      {/* Barra de Navegación */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-teal-500 to-emerald-400 rounded-xl shadow-lg shadow-teal-500/20 text-slate-950">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg text-white tracking-tight flex items-center gap-1.5">
                MediSinc<span className="text-teal-400 font-normal">·IA</span>
              </h1>
              <p className="text-[10px] text-teal-400 font-semibold tracking-wider uppercase">
                Pre-Triaje Clínico Inteligente
              </p>
            </div>
          </div>

          <Link
            to="/iniciar-sesion"
            className="text-xs font-semibold text-slate-300 hover:text-teal-400 bg-slate-800/80 hover:bg-slate-800 px-3.5 py-1.5 rounded-xl border border-slate-700/80 transition flex items-center gap-1.5"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Acceso Personal Médico</span>
          </Link>
        </div>
      </header>

      {/* Contenido Principal con Wizard */}
      <main className="max-w-3xl mx-auto px-4 py-8 w-full flex-1">
        {/* Indicador Visual de Pasos */}
        <div className="mb-8">
          <div className="flex items-center justify-between relative max-w-md mx-auto">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-slate-800 w-full -z-0"></div>
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-teal-500 transition-all duration-300 -z-0"
              style={{ width: pasoActual === 1 ? '0%' : pasoActual === 2 ? '50%' : '100%' }}
            ></div>

            {/* Paso 1 */}
            <div className="flex flex-col items-center relative z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition shadow-md ${
                  pasoActual > 1
                    ? 'bg-teal-500 text-slate-950 shadow-teal-500/30'
                    : pasoActual === 1
                    ? 'bg-teal-500 text-slate-950 ring-4 ring-teal-500/20'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {pasoActual > 1 ? <Check className="w-4 h-4" /> : '1'}
              </div>
              <span className="text-[11px] font-semibold text-slate-300 mt-1.5">Datos</span>
            </div>

            {/* Paso 2 */}
            <div className="flex flex-col items-center relative z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition shadow-md ${
                  pasoActual > 2
                    ? 'bg-teal-500 text-slate-950 shadow-teal-500/30'
                    : pasoActual === 2
                    ? 'bg-teal-500 text-slate-950 ring-4 ring-teal-500/20'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {pasoActual > 2 ? <Check className="w-4 h-4" /> : '2'}
              </div>
              <span className="text-[11px] font-semibold text-slate-300 mt-1.5">Preguntas IA</span>
            </div>

            {/* Paso 3 */}
            <div className="flex flex-col items-center relative z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition shadow-md ${
                  pasoActual === 3
                    ? 'bg-teal-500 text-slate-950 ring-4 ring-teal-500/20 shadow-teal-500/30'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                3
              </div>
              <span className="text-[11px] font-semibold text-slate-300 mt-1.5">Código QR</span>
            </div>
          </div>
        </div>

        {/* Mensaje de Error en Envío */}
        {errorEnvio && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-xs text-rose-300">
            {errorEnvio}
          </div>
        )}

        {/* Tarjeta Contenedora del Paso Activo */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
          {pasoActual === 1 && (
            <PasoDatosEstaticos
              datos={datosFormulario}
              alCambiar={actualizarCampo}
              alSiguiente={() => setPasoActual(2)}
            />
          )}

          {pasoActual === 2 && (
            <PasoPreguntasDinamicas
              datos={datosFormulario}
              alCambiar={actualizarCampo}
              alAtras={() => setPasoActual(1)}
              alFinalizar={enviarPreTriajeFinal}
              estaEnviando={estaEnviando}
            />
          )}

          {pasoActual === 3 && (
            <PasoConfirmacionQR
              resultadoTriaje={resultadoTriaje}
              alReiniciar={reiniciarFormulario}
            />
          )}
        </div>
      </main>

      {/* Pie de Página con Sellos de Seguridad */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-5xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>© 2026 MediSinc-IA. Centro de Salud Santa Cruz de la Sierra, Bolivia.</p>
          <div className="flex items-center gap-4 text-slate-400">
            <span className="flex items-center gap-1"><Shield className="w-3.5 h-3.5 text-teal-400" /> Cifrado AES-256</span>
            <span className="flex items-center gap-1"><Activity className="w-3.5 h-3.5 text-emerald-400" /> Motor Clínico v2.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const PatientHome = InicioPaciente;
export default InicioPaciente;
