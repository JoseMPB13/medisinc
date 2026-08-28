/**
 * Componente: Paso 1 del Asistente de Paciente (Filiación y Síntoma Actual Agudo).
 * Captura y valida Nombre, CI (con cifrado AES-256), Edad (0-120), Género,
 * Motivo de Consulta Principal (texto libre), Tiempo de Evolución e Intensidad del Dolor (1 a 10).
 */

import React, { useState } from 'react';
import {
  User,
  CreditCard,
  Calendar,
  Activity,
  AlertCircle,
  Shield,
  ArrowLeft,
  ArrowRight,
  Clock,
  HelpCircle,
} from 'lucide-react';
import AvisoPrivacidad from './AvisoPrivacidad';

export const PasoDatosEstaticos = ({ datos, alCambiar, alSiguiente, alAtras }) => {
  const [errores, setErrores] = useState({});
  const [mostrarPrivacidad, setMostrarPrivacidad] = useState(false);

  const especialidad = datos.especialidad_solicitada || datos.requested_specialty || 'Medicina General';
  const medicoNombre = datos.medico_asignado_nombre || 'Dr. Carlos Menacho';

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
    if (!ci) nuevosErrores.ci = 'El Carnet de Identidad es requerido para tu expediente.';
    if (isNaN(edad) || edad < 0 || edad > 120) nuevosErrores.edad = 'Ingresa una edad válida (0 - 120 años).';
    if (!genero) nuevosErrores.genero = 'Selecciona tu género.';
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
      {/* Encabezado del Paso con Banner Destacado de Médico de Guardia */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider">
          <Activity className="w-3.5 h-3.5" />
          <span>Paso 1 de 3 · Formulario de Ingreso</span>
        </div>

        {/* Tarjeta Visual Destacada de Asignación Médica */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-teal-950/80 via-slate-900 to-slate-900 border border-teal-500/40 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 bg-teal-500 text-slate-950 rounded-2xl shadow-md shadow-teal-500/20 font-black">
              <User className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-teal-400 block">
                Médico de Guardia que te Atenderá:
              </span>
              <h3 className="text-base font-black text-white flex items-center gap-2">
                {medicoNombre}
                <span className="text-xs font-medium text-teal-300 bg-teal-950 px-2.5 py-0.5 rounded-full border border-teal-500/30">
                  {especialidad}
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Tu pre-triaje y expediente se vincularán directamente a la consulta del doctor.
              </p>
            </div>
          </div>

          {alAtras && (
            <button
              type="button"
              onClick={alAtras}
              className="self-start sm:self-auto text-xs font-bold text-teal-300 hover:text-white border border-teal-500/30 px-3.5 py-2 rounded-xl bg-teal-950/60 hover:bg-teal-900/60 transition flex items-center gap-1.5 cursor-pointer flex-shrink-0 shadow-sm"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Cambiar Especialidad</span>
            </button>
          )}
        </div>
      </div>

      {/* Grid 1: Nombre y CI */}
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
          {errores.nombre && (
            <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errores.nombre}
            </p>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Carnet de Identidad (CI)
            </label>
            <button
              type="button"
              onClick={() => setMostrarPrivacidad(true)}
              className="text-[11px] text-teal-400 hover:underline flex items-center gap-1"
            >
              <Shield className="w-3 h-3" /> Cifrado AES-256
            </button>
          </div>
          <div className="relative">
            <CreditCard className="w-5 h-5 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              name="ci"
              value={datos.ci || ''}
              onChange={(e) => alCambiar('ci', e.target.value)}
              placeholder="Ej. 8492011 SC"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
          {errores.ci && (
            <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errores.ci}
            </p>
          )}
        </div>
      </div>

      {/* Grid 2: Edad y Género */}
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
              value={datos.edad !== undefined ? datos.edad : datos.age || ''}
              onChange={(e) => alCambiar('edad', e.target.value)}
              placeholder="Ej. 34"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
          {errores.edad && (
            <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errores.edad}
            </p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Género
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['Femenino', 'Masculino', 'Otro'].map((opcion) => (
              <button
                key={opcion}
                type="button"
                onClick={() => alCambiar('genero', opcion)}
                className={`py-2.5 px-3 rounded-xl border text-xs font-semibold transition ${
                  (datos.genero || datos.gender) === opcion
                    ? 'bg-teal-500 text-slate-950 border-teal-400 shadow-md shadow-teal-500/20'
                    : 'bg-slate-900/80 border-slate-700 text-slate-300 hover:bg-slate-800'
                }`}
              >
                {opcion}
              </button>
            ))}
          </div>
          {errores.genero && (
            <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errores.genero}
            </p>
          )}
        </div>
      </div>

      {/* Motivo de Consulta Principal (Texto Libre) */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
          ¿Cuál es tu molestia o síntoma principal?
        </label>
        <textarea
          rows="3"
          name="sintomas_brutos"
          value={datos.sintomas_brutos || datos.raw_symptoms || ''}
          onChange={(e) => alCambiar('sintomas_brutos', e.target.value)}
          placeholder="Describe con tus propias palabras qué sientes (ej. dolor fuerte en el estómago desde anoche, náuseas y fiebre)..."
          className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition resize-none"
        />
        {errores.sintomas && (
          <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" />
            {errores.sintomas}
          </p>
        )}
      </div>

      {/* Grid 3: Tiempo de Evolución e Intensidad del Dolor */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tiempo de Evolución */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-teal-400" />
              ¿Hace cuánto tiempo comenzaron los síntomas?
            </span>
          </label>
          <select
            value={datos.datos_estaticos?.duracion || datos.static_data?.duracion || '2 a 6 horas'}
            onChange={(e) =>
              alCambiar('datos_estaticos', {
                ...datos.datos_estaticos,
                duracion: e.target.value,
              })
            }
            className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          >
            <option value="Menos de 2 horas">Menos de 2 horas (Comienzo súbito)</option>
            <option value="2 a 6 horas">Entre 2 y 6 horas</option>
            <option value="6 a 24 horas">Entre 6 y 24 horas</option>
            <option value="1 a 3 días">De 1 a 3 días</option>
            <option value="Más de 3 días">Más de 3 días (Cuadro prolongado)</option>
          </select>
        </div>

        {/* Intensidad del Dolor (Slider 1 a 10) */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Intensidad del Dolor / Malestar
            </label>
            <span className={`text-xs font-black px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-700 ${obtenerColorIntensidad(intensidadActual)}`}>
              {intensidadActual} / 10
            </span>
          </div>

          <input
            type="range"
            min="1"
            max="10"
            value={intensidadActual}
            onChange={(e) =>
              alCambiar('datos_estaticos', {
                ...datos.datos_estaticos,
                intensidad: parseInt(e.target.value, 10),
              })
            }
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-400 mt-2"
          />

          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>1 (Leve)</span>
            <span>5 (Moderado)</span>
            <span className="text-rose-400 font-bold">10 (Insupportable)</span>
          </div>
        </div>
      </div>

      {/* Botones de Navegación */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-4">
        {alAtras && (
          <button
            type="button"
            onClick={alAtras}
            className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-2 text-xs font-bold cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Atrás</span>
          </button>
        )}

        <button
          type="submit"
          className="ml-auto bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-black py-3 px-8 rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center gap-2 text-xs cursor-pointer group"
        >
          <span>Continuar a Preguntas Dinámicas</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>

      {/* Modal de Aviso de Privacidad */}
      {mostrarPrivacidad && (
        <AvisoPrivacidad alCerrar={() => setMostrarPrivacidad(false)} />
      )}
    </form>
  );
};

export default PasoDatosEstaticos;
