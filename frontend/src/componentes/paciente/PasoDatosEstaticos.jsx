/**
 * Componente: Paso 1 del Asistente de Paciente (Captura de Datos Demográficos y Clínicos).
 * Valida Nombre, CI, Edad (0-120), Género, Síntoma libre, Duración e Intensidad de Dolor (1-10).
 */

import React, { useState } from 'react';
import { User, CreditCard, Calendar, Activity, AlertCircle, HeartPulse, Shield, Info } from 'lucide-react';
import AvisoPrivacidad from './AvisoPrivacidad';

export const PasoDatosEstaticos = ({ datos, alCambiar, alSiguiente }) => {
  const [errores, setErrores] = useState({});
  const [mostrarPrivacidad, setMostrarPrivacidad] = useState(false);

  // Obtener color dinámico para el slider de intensidad de dolor (1-10)
  const obtenerColorIntensidad = (valor) => {
    const num = parseInt(valor, 10);
    if (num <= 3) return 'from-emerald-500 to-teal-500 text-emerald-400';
    if (num <= 6) return 'from-amber-500 to-yellow-500 text-amber-400';
    return 'from-rose-600 to-red-500 text-rose-400';
  };

  const validarFormulario = () => {
    const nuevosErrores = {};
    const nombre = (datos.nombre_paciente || datos.patient_name || '').trim();
    const ci = (datos.ci || '').trim();
    const edad = parseInt(datos.edad || datos.age, 10);
    const genero = datos.genero || datos.gender;
    const sintomas = (datos.sintomas_brutos || datos.raw_symptoms || '').trim();

    if (!nombre) nuevosErrores.nombre = 'El nombre completo es obligatorio.';
    if (!ci) nuevosErrores.ci = 'El Carnet de Identidad es requerido para el expediente.';
    if (isNaN(edad) || edad < 0 || edad > 120) nuevosErrores.edad = 'Ingresa una edad válida (0 - 120 años).';
    if (!genero) nuevosErrores.genero = 'Selecciona el género.';
    if (!sintomas || sintomas.length < 5) nuevosErrores.sintomas = 'Describe tu síntoma principal (mínimo 5 caracteres).';

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const manejarContinuar = (e) => {
    e.preventDefault();
    if (validarFormulario()) {
      alSiguiente();
    }
  };

  const intensidadActual = datos.datos_estaticos?.intensidad || datos.static_data?.intensidad || 5;

  return (
    <form onSubmit={manejarContinuar} className="space-y-6 animate-fade-in text-slate-100">
      {/* Encabezado del Paso */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Activity className="w-6 h-6 text-teal-400" />
          Paso 1: Datos Generales y Motivo de Consulta
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Ingresa tus datos personales y describe cómo te sientes hoy para iniciar la evaluación clínica.
        </p>
      </div>

      {/* Grid: Nombre y CI */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Nombre Completo
          </label>
          <div className="relative">
            <User className="w-5 h-5 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              name="nombre_paciente"
              value={datos.nombre_paciente || datos.patient_name || ''}
              onChange={(e) => alCambiar('nombre_paciente', e.target.value)}
              placeholder="Ej. María René Suárez"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
          {errores.nombre && <p className="text-xs text-rose-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{errores.nombre}</p>}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Carnet de Identidad (CI)
            </label>
            <button
              type="button"
              onClick={() => setMostrarPrivacidad(true)}
              className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1"
            >
              <Shield className="w-3.5 h-3.5" /> Cifrado AES-256
            </button>
          </div>
          <div className="relative">
            <CreditCard className="w-5 h-5 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              name="ci"
              value={datos.ci || ''}
              onChange={(e) => alCambiar('ci', e.target.value)}
              placeholder="Ej. 1234567 SC"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
          {errores.ci && <p className="text-xs text-rose-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{errores.ci}</p>}
        </div>
      </div>

      {/* Grid: Edad y Género */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Edad (Años)
          </label>
          <div className="relative">
            <Calendar className="w-5 h-5 absolute left-3 top-3 text-slate-500" />
            <input
              type="number"
              min="0"
              max="120"
              name="edad"
              value={datos.edad !== undefined ? datos.edad : (datos.age !== undefined ? datos.age : '')}
              onChange={(e) => alCambiar('edad', e.target.value)}
              placeholder="Ej. 28"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
          {errores.edad && <p className="text-xs text-rose-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{errores.edad}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Género
          </label>
          <select
            name="genero"
            value={datos.genero || datos.gender || ''}
            onChange={(e) => alCambiar('genero', e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
          >
            <option value="">Selecciona tu género</option>
            <option value="Femenino">Femenino</option>
            <option value="Masculino">Masculino</option>
            <option value="Otro">Otro / Prefiero no decir</option>
          </select>
          {errores.genero && <p className="text-xs text-rose-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{errores.genero}</p>}
        </div>
      </div>

      {/* Motivo de Consulta en Texto Libre */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
          ¿Cuál es tu molestia o síntoma principal?
        </label>
        <p className="text-xs text-slate-400 mb-2">
          Escribe libremente con tus propias palabras (ej. <i>"Me duele la tutuma y tengo chucho de frío"</i>, <i>"Tengo dolor fuerte en el pecho"</i>).
        </p>
        <textarea
          rows="3"
          name="sintomas_brutos"
          value={datos.sintomas_brutos || datos.raw_symptoms || ''}
          onChange={(e) => alCambiar('sintomas_brutos', e.target.value)}
          placeholder="Describe detalladamente tus molestias o dolencias..."
          className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition resize-none"
        />
        {errores.sintomas && <p className="text-xs text-rose-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{errores.sintomas}</p>}
      </div>

      {/* Grid: Duración e Intensidad */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Tiempo de Evolución
          </label>
          <select
            value={datos.datos_estaticos?.duracion || datos.static_data?.duracion || '2 a 6 horas'}
            onChange={(e) => alCambiar('datos_estaticos', { ...(datos.datos_estaticos || {}), duracion: e.target.value })}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
          >
            <option value="Menos de 2 horas">Menos de 2 horas (Muy reciente)</option>
            <option value="2 a 6 horas">2 a 6 horas</option>
            <option value="1 a 3 días">1 a 3 días</option>
            <option value="Más de 1 semana">Más de 1 semana (Crónico)</option>
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Intensidad del Dolor
            </label>
            <span className={`text-sm font-bold ${obtenerColorIntensidad(intensidadActual)}`}>
              {intensidadActual} / 10
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            value={intensidadActual}
            onChange={(e) => alCambiar('datos_estaticos', { ...(datos.datos_estaticos || {}), intensidad: parseInt(e.target.value, 10) })}
            className="w-full accent-teal-400 cursor-pointer h-2 bg-slate-700 rounded-lg appearance-none"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-semibold">
            <span>1 (Leve)</span>
            <span>5 (Moderado)</span>
            <span>10 (Insoportable)</span>
          </div>
        </div>
      </div>

      {/* Botón de Acción */}
      <div className="pt-4 flex justify-end">
        <button
          type="submit"
          className="w-full md:w-auto bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white font-semibold py-3 px-8 rounded-xl shadow-lg shadow-teal-900/30 transition duration-200 flex items-center justify-center gap-2"
        >
          <span>Siguiente: Preguntas Adaptativas</span>
          <HeartPulse className="w-5 h-5" />
        </button>
      </div>

      {/* Modal de Privacidad */}
      <AvisoPrivacidad abierto={mostrarPrivacidad} alCerrar={() => setMostrarPrivacidad(false)} />
    </form>
  );
};

export const StaticDataStep = PasoDatosEstaticos;
export default PasoDatosEstaticos;
