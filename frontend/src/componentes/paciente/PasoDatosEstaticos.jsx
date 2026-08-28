/**
 * Componente: Paso 1 del Asistente de Paciente (Captura de Datos Generales y Antecedentes Clínicos).
 * Valida Nombre, CI, Edad (0-120), Género, Síntoma libre, Duración, Intensidad del Dolor (1-10),
 * y captura estructurada de Alergias Medicamentosas, Medicación Actual y Enfermedades de Base.
 */

import React, { useState } from 'react';
import {
  User,
  CreditCard,
  Calendar,
  Activity,
  AlertCircle,
  HeartPulse,
  Shield,
  Pill,
  AlertTriangle,
  FileHeart,
  ArrowLeft,
  ArrowRight,
  Check,
} from 'lucide-react';
import AvisoPrivacidad from './AvisoPrivacidad';

const OPCIONES_ALERGIAS_COMUNES = ['Ninguna', 'Penicilina', 'AINEs / Ibuprofeno', 'Sulfas', 'Otra'];
const OPCIONES_ENFERMEDADES_COMUNES = [
  'Ninguna',
  'Hipertensión',
  'Diabetes',
  'Asma / EPOC',
  'Cardiopatía',
  'Gastritis / Úlcera',
];

export const PasoDatosEstaticos = ({ datos, alCambiar, alSiguiente, alAtras }) => {
  const [errores, setErrores] = useState({});
  const [mostrarPrivacidad, setMostrarPrivacidad] = useState(false);
  const [otraAlergiaTexto, setOtraAlergiaTexto] = useState('');

  const especialidad = datos.especialidad_solicitada || datos.requested_specialty || 'Medicina General';
  const alergiasActuales = datos.alergias_medicamentosas || datos.drug_allergies || 'Ninguna';
  const enfermedadesActuales = datos.enfermedades_base || datos.base_diseases || [];
  const medicacionActual = datos.medicacion_actual || datos.current_medication || '';

  // Obtener color dinámico para el slider de intensidad de dolor (1-10)
  const obtenerColorIntensidad = (valor) => {
    const num = parseInt(valor, 10);
    if (num <= 3) return 'from-emerald-500 to-teal-500 text-emerald-400';
    if (num <= 6) return 'from-amber-500 to-yellow-500 text-amber-400';
    return 'from-rose-600 to-red-500 text-rose-400';
  };

  const seleccionarAlergiaChip = (opcion) => {
    if (opcion === 'Ninguna') {
      alCambiar('alergias_medicamentosas', 'Ninguna conocida');
      setOtraAlergiaTexto('');
    } else if (opcion === 'Otra') {
      alCambiar('alergias_medicamentosas', otraAlergiaTexto || 'Otra alergia');
    } else {
      alCambiar('alergias_medicamentosas', opcion);
    }
  };

  const toggleEnfermedadChip = (opcion) => {
    let nuevasEnfermedades = [...enfermedadesActuales];
    if (opcion === 'Ninguna') {
      nuevasEnfermedades = [];
    } else {
      // Remover "Ninguna" si se selecciona una comorbilidad
      nuevasEnfermedades = nuevasEnfermedades.filter((e) => e !== 'Ninguna');
      if (nuevasEnfermedades.includes(opcion)) {
        nuevasEnfermedades = nuevasEnfermedades.filter((e) => e !== opcion);
      } else {
        nuevasEnfermedades.push(opcion);
      }
    }
    alCambiar('enfermedades_base', nuevasEnfermedades);
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
      {/* Encabezado del Paso con Badge de Especialidad */}
      <div className="border-b border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1.5">
            <Activity className="w-3.5 h-3.5" />
            <span>Paso 1 de 3 · Datos y Antecedentes</span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Datos Generales y Motivo de Consulta
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Especialidad seleccionada:{' '}
            <span className="text-teal-300 font-semibold">{especialidad}</span>
          </p>
        </div>

        {alAtras && (
          <button
            type="button"
            onClick={alAtras}
            className="self-start sm:self-auto text-xs text-slate-400 hover:text-teal-400 border border-slate-700/80 px-3 py-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 transition flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Cambiar especialidad</span>
          </button>
        )}
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
              value={datos.edad !== undefined ? datos.edad : (datos.age !== undefined ? datos.age : '')}
              onChange={(e) => alCambiar('edad', e.target.value)}
              placeholder="Ej. 28"
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
          {errores.genero && (
            <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errores.genero}
            </p>
          )}
        </div>
      </div>

      {/* Motivo de Consulta en Texto Libre */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
          ¿Cuál es tu molestia o síntoma principal?
        </label>
        <p className="text-xs text-slate-400 mb-2">
          Escribe libremente con tus propias palabras (ej. <i>"Me duele la tutuma y tengo chucho de frío"</i>, <i>"Tengo dolor agudo en el pecho"</i>).
        </p>
        <textarea
          rows="3"
          name="sintomas_brutos"
          value={datos.sintomas_brutos || datos.raw_symptoms || ''}
          onChange={(e) => alCambiar('sintomas_brutos', e.target.value)}
          placeholder="Describe detalladamente tus molestias o dolencias actuales..."
          className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition resize-none"
        />
        {errores.sintomas && (
          <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" />
            {errores.sintomas}
          </p>
        )}
      </div>

      {/* Grid 3: Duración e Intensidad del Dolor */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Tiempo de Evolución
          </label>
          <select
            value={datos.datos_estaticos?.duracion || datos.static_data?.duracion || '2 a 6 horas'}
            onChange={(e) =>
              alCambiar('datos_estaticos', { ...(datos.datos_estaticos || {}), duracion: e.target.value })
            }
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
            onChange={(e) =>
              alCambiar('datos_estaticos', {
                ...(datos.datos_estaticos || {}),
                intensidad: parseInt(e.target.value, 10),
              })
            }
            className="w-full accent-teal-400 cursor-pointer h-2 bg-slate-700 rounded-lg appearance-none"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-semibold">
            <span>1 (Leve)</span>
            <span>5 (Moderado)</span>
            <span>10 (Insoportable)</span>
          </div>
        </div>
      </div>

      {/* =========================================================================
          NUEVA SECCIÓN: ANTECEDENTES MÉDICOS Y ALERGIAS FARMACOLÓGICAS
         ========================================================================= */}
      <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-5">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <FileHeart className="w-5 h-5 text-teal-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Antecedentes Médicos y Alergias
          </h3>
        </div>

        {/* 1. Alergias a Medicamentos */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <label className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              ¿Tienes alergia a algún medicamento?
            </label>
          </div>
          <div className="flex flex-wrap gap-2 mb-2">
            {OPCIONES_ALERGIAS_COMUNES.map((opc) => {
              const esActivo =
                opc === 'Ninguna'
                  ? alergiasActuales === 'Ninguna' || alergiasActuales === 'Ninguna conocida'
                  : alergiasActuales.includes(opc);
              return (
                <button
                  type="button"
                  key={opc}
                  onClick={() => seleccionarAlergiaChip(opc)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
                    esActivo
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-sm'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {opc}
                </button>
              );
            })}
          </div>
          {alergiasActuales !== 'Ninguna' && alergiasActuales !== 'Ninguna conocida' && (
            <input
              type="text"
              value={datos.alergias_medicamentosas || ''}
              onChange={(e) => alCambiar('alergias_medicamentosas', e.target.value)}
              placeholder="Especifica el medicamento alérgico (ej. Penicilina, Diclofenaco)..."
              className="w-full bg-slate-900 border border-amber-500/40 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          )}
        </div>

        {/* 2. Medicación Habitual */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Pill className="w-4 h-4 text-teal-400" />
            <label className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Medicación Actual
            </label>
          </div>
          <input
            type="text"
            value={medicacionActual}
            onChange={(e) => alCambiar('medicacion_actual', e.target.value)}
            placeholder="¿Tomas medicamentos a diario o tomaste algo para este malestar? (Ej. Losartán 50mg, Paracetamol)..."
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
        </div>

        {/* 3. Enfermedades de Base */}
        <div>
          <label className="block text-xs font-semibold text-slate-200 uppercase tracking-wider mb-2">
            Enfermedades o Condiciones Crónicas Diagnosticadas
          </label>
          <div className="flex flex-wrap gap-2">
            {OPCIONES_ENFERMEDADES_COMUNES.map((enf) => {
              const esActivo =
                enf === 'Ninguna'
                  ? enfermedadesActuales.length === 0
                  : enfermedadesActuales.includes(enf);
              return (
                <button
                  type="button"
                  key={enf}
                  onClick={() => toggleEnfermedadChip(enf)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border flex items-center gap-1.5 ${
                    esActivo
                      ? 'bg-teal-500/20 text-teal-300 border-teal-500/50 shadow-sm'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {esActivo && <Check className="w-3 h-3 text-teal-400" />}
                  <span>{enf}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Botones de Navegación */}
      <div className="pt-4 flex items-center justify-between gap-4">
        {alAtras ? (
          <button
            type="button"
            onClick={alAtras}
            className="px-5 py-3 rounded-xl border border-slate-700 bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition flex items-center gap-2 text-sm font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Atrás</span>
          </button>
        ) : (
          <div></div>
        )}

        <button
          type="submit"
          className="bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 font-bold py-3 px-8 rounded-xl shadow-lg shadow-teal-900/30 transition flex items-center justify-center gap-2 text-sm"
        >
          <span>Siguiente: Preguntas Adaptativas</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Modal de Privacidad */}
      <AvisoPrivacidad abierto={mostrarPrivacidad} alCerrar={() => setMostrarPrivacidad(false)} />
    </form>
  );
};

export const StaticDataStep = PasoDatosEstaticos;
export default PasoDatosEstaticos;
