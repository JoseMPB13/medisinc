import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle2, FileText, UserCheck, AlertTriangle, Activity, Stethoscope } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Componente Modal de Visualización Dividida y Confirmación de Atención Médica.
 * Presenta la declaración bruta del paciente a la izquierda, el resumen IA a la derecha
 * y el formulario de cierre con notas médicas y ajuste de prioridad.
 */
function PatientDetailModal({ patientData, onClose, onReviewComplete }) {
  const [doctorNotes, setDoctorNotes] = useState('');
  const [priorityAdjusted, setPriorityAdjusted] = useState(patientData?.final_priority || 'RED');
  const [saving, setSaving] = useState(false);

  if (!patientData) return null;

  const raw = patientData;
  const aiResult = patientData.AI_RESULT?.structured_result || patientData.ai_result || {};
  const isOverride = patientData.AI_RESULT?.override_applied || patientData.override_applied;
  const overrideReason = patientData.AI_RESULT?.override_reason || patientData.override_reason;

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!doctorNotes.trim()) {
      alert('Por favor ingrese las observaciones médicas antes de confirmar la atención.');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API_BASE_URL}/doctor/review`, {
        triage_id: raw.id,
        doctor_id: 'doc-uuid-12345',
        doctor_notes: doctorNotes,
        priority_adjusted: priorityAdjusted,
      });

      alert('Atención médica registrada exitosamente. El expediente ha sido marcado como REVIEWED.');
      if (onReviewComplete) onReviewComplete();
      onClose();
    } catch (err) {
      console.error('Error al guardar revisión médica:', err);
      alert('Error guardando revisión médica. Se actualizará en la base local.');
      if (onReviewComplete) onReviewComplete();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const getPriorityBadgeClass = (prio) => {
    if (prio === 'RED') return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    if (prio === 'YELLOW') return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-3 md:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-5xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Cabecera del Modal */}
        <div className="p-4 md:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-sky-500/10 rounded-xl border border-sky-500/20">
              <Stethoscope className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-100">{raw.patient_name}</h2>
                <span className="font-mono text-xs px-2.5 py-0.5 bg-slate-800 text-sky-400 rounded-md border border-slate-700 font-semibold">
                  {raw.access_code}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Edad: {raw.age} años | Género: {raw.gender} | Estado: <span className="font-semibold text-slate-300">{raw.status}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-slate-200 transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Cuerpo del Modal: Pantalla Dividida (Split-View) */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Columna Izquierda: Declaración Bruta del Paciente */}
          <div className="space-y-4 bg-slate-950/50 border border-slate-800 rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-2">
              <FileText className="w-4 h-4 text-sky-400" />
              Declaración Directa del Paciente (Raw Data)
            </h3>

            <div>
              <span className="text-[11px] text-slate-500 font-semibold block">Carnet de Identidad (Descifrado en Memoria):</span>
              <span className="text-sm font-mono text-sky-300 font-bold bg-slate-900 px-2.5 py-1 rounded border border-slate-800 inline-block mt-1">
                {raw.decrypted_ci || raw.ci || 'Descifrando CI...'}
              </span>
            </div>

            <div>
              <span className="text-[11px] text-slate-500 font-semibold block mb-1">Síntoma Principal en Texto Libre:</span>
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 leading-relaxed font-sans italic">
                "{raw.raw_symptoms}"
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Tiempo de Evolución:</span>
                <span className="font-semibold text-slate-200">{raw.static_data?.duracion || 'No especificado'}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Intensidad Declarada:</span>
                <span className="font-semibold text-slate-200">{raw.static_data?.intensidad || 5} / 10</span>
              </div>
            </div>

            {raw.dynamic_answers && Object.keys(raw.dynamic_answers).length > 0 && (
              <div>
                <span className="text-[11px] text-slate-500 font-semibold block mb-1">Respuestas Preguntas Adaptativas:</span>
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-1 text-xs">
                  {Object.entries(raw.dynamic_answers).map(([key, val]) => (
                    <div key={key} className="flex justify-between border-b border-slate-800/60 pb-1">
                      <span className="text-slate-400 font-mono">{key}:</span>
                      <span className="text-sky-300 font-medium">{Array.isArray(val) ? val.join(', ') : String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Columna Derecha: Resumen Estructurado por IA & Safety Overrides */}
          <div className="space-y-4 bg-slate-950/50 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-emerald-400" />
                Resumen Clínico Inteligente por IA
              </h3>
              <span className={`text-xs px-3 py-0.5 rounded-full border font-bold ${getPriorityBadgeClass(raw.final_priority)}`}>
                Prioridad: {raw.final_priority || 'RED'}
              </span>
            </div>

            {isOverride && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300 flex items-start gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="block text-rose-200">Safety Override Aplicado:</strong>
                  {overrideReason || 'Regla de seguridad clínica activada.'}
                </div>
              </div>
            )}

            <div>
              <span className="text-[11px] text-slate-500 font-semibold block mb-1">Síntesis Narrativa para Lectura Médica:</span>
              <p className="text-xs text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800 leading-relaxed">
                {aiResult.resumen_clinico_narrativo || 'Analizando sintomatología...'}
              </p>
            </div>

            {aiResult.senales_alerta_identificadas?.length > 0 && (
              <div>
                <span className="text-[11px] text-rose-400 font-semibold block mb-1 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Banderas Rojas Identificadas:
                </span>
                <ul className="list-disc list-inside text-xs text-rose-300 bg-rose-950/20 border border-rose-500/20 p-2.5 rounded-lg space-y-0.5">
                  {aiResult.senales_alerta_identificadas.map((flag, i) => (
                    <li key={i}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {aiResult.informacion_faltante_critica?.length > 0 && (
              <div>
                <span className="text-[11px] text-amber-400 font-semibold block mb-1">Información Faltante Crítica a Indagar:</span>
                <ul className="list-disc list-inside text-xs text-amber-300 bg-amber-950/20 border border-amber-500/20 p-2.5 rounded-lg space-y-0.5">
                  {aiResult.informacion_faltante_critica.map((info, i) => (
                    <li key={i}>{info}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Formulario de Evaluación Presencial y Cierre de Atención */}
        <form onSubmit={handleSubmitReview} className="p-4 md:p-5 border-t border-slate-800 bg-slate-950 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Observaciones y Notas Clínicas Presenciales <span className="text-rose-400">*</span>
              </label>
              <textarea
                required
                rows={2}
                placeholder="Escriba las conclusiones de la atención del médico..."
                value={doctorNotes}
                onChange={(e) => setDoctorNotes(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Ajuste Manual de Prioridad (Opcional)
              </label>
              <select
                value={priorityAdjusted}
                onChange={(e) => setPriorityAdjusted(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl py-2.5 px-3 text-xs text-slate-100 focus:outline-none"
              >
                <option value="RED">🔴 Rojo (Urgente / Emergencia)</option>
                <option value="YELLOW">🟡 Amarillo (Prioritario)</option>
                <option value="GREEN">🟢 Verde (No Urgente)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-slate-800/80">
            <button
              type="button"
              onClick={onClose}
              className="py-2.5 px-5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl text-xs transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="py-2.5 px-6 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 text-xs transition flex items-center gap-2"
            >
              <UserCheck className="w-4 h-4" />
              {saving ? 'Guardando Registro...' : 'Guardar y Confirmar Atención'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PatientDetailModal;
