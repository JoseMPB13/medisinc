import React from 'react';
import { User, CreditCard, Calendar, Activity, AlertCircle, ArrowRight } from 'lucide-react';

/**
 * Componente Paso 1 del Formulario Híbrido: Captura de Datos Fijos y Síntoma Base.
 * Permite registrar nombre, CI, edad, género, síntoma principal, duración e intensidad (escala 1-10).
 */
function StepStaticData({ formData, updateFormData, onNext }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.patientName || !formData.ci || !formData.age || !formData.rawSymptoms) {
      alert('Por favor complete todos los campos obligatorios (*).');
      return;
    }
    onNext();
  };

  // Asignar color dinámico al slider de intensidad (1-10)
  const getIntensityBadge = (val) => {
    const intensity = parseInt(val, 10);
    if (intensity <= 3) return { label: 'Leve (1-3)', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
    if (intensity <= 6) return { label: 'Moderado (4-6)', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };
    return { label: 'Severo / Intenso (7-10)', color: 'bg-rose-500/20 text-rose-400 border-rose-500/30' };
  };

  const badge = getIntensityBadge(formData.intensity || 5);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border-b border-slate-800 pb-4 mb-4">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <User className="w-5 h-5 text-sky-400" /> Paso 1: Información General y Síntoma Base
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Ingrese sus datos personales y el motivo principal de su consulta.
        </p>
      </div>

      {/* Datos Personales: Nombre y CI */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Nombre Completo <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              required
              placeholder="Ej. Juan Pérez"
              value={formData.patientName || ''}
              onChange={(e) => updateFormData({ patientName: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2.5 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Carnet de Identidad (CI) <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <CreditCard className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              required
              placeholder="Ej. 1234567 SC"
              value={formData.ci || ''}
              onChange={(e) => updateFormData({ ci: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2.5 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>
      </div>

      {/* Edad y Género */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Edad (Años) <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <Calendar className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="number"
              min="0"
              max="120"
              required
              placeholder="Ej. 35"
              value={formData.age || ''}
              onChange={(e) => updateFormData({ age: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2.5 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Género <span className="text-rose-400">*</span>
          </label>
          <select
            value={formData.gender || 'Masculino'}
            onChange={(e) => updateFormData({ gender: e.target.value })}
            className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2.5 px-3 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="Masculino">Masculino</option>
            <option value="Femenino">Femenino</option>
            <option value="Otro">Otro / Prefiero no decir</option>
          </select>
        </div>
      </div>

      {/* Síntoma Principal en texto libre */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
          <AlertCircle className="w-4 h-4 text-sky-400" />
          Síntoma o Molestia Principal <span className="text-rose-400">*</span>
        </label>
        <textarea
          required
          rows={3}
          placeholder="Describa brevemente qué siente (ej. 'Tengo dolor fuerte de cabeza y mareo desde esta mañana')"
          value={formData.rawSymptoms || ''}
          onChange={(e) => updateFormData({ rawSymptoms: e.target.value })}
          className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
        />
      </div>

      {/* Duración e Intensidad del Dolor (Escala 1 al 10) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Tiempo de Evolución (Duración Aproximada)
          </label>
          <input
            type="text"
            placeholder="Ej. 2 horas, 1 día, 3 días"
            value={formData.duration || ''}
            onChange={(e) => updateFormData({ duration: e.target.value })}
            className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2 px-3 text-sm text-slate-100 focus:outline-none"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
              <Activity className="w-4 h-4 text-sky-400" />
              Intensidad del Dolor o Molestia (1 al 10)
            </label>
            <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${badge.color}`}>
              {badge.label}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            value={formData.intensity || 5}
            onChange={(e) => updateFormData({ intensity: e.target.value })}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>1 (Muy Leve)</span>
            <span>5 (Moderado)</span>
            <span>10 (Insoportable)</span>
          </div>
        </div>
      </div>

      {/* Botón de Continuar */}
      <button
        type="submit"
        className="w-full py-3.5 px-6 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition duration-200 flex items-center justify-center gap-2"
      >
        <span>Continuar a Preguntas Adaptativas</span>
        <ArrowRight className="w-4 h-4" />
      </button>
    </form>
  );
}

export default StepStaticData;
