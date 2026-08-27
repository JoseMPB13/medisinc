/**
 * Modal en Pantalla Dividida (Split View) para la Evaluación Médica de Guardia.
 * Panel Izquierdo: Datos literales del paciente y CI descifrado en memoria.
 * Panel Derecho: Resumen estructurado de IA, señales de alerta, notas médicas y cierre.
 */

import React, { useState } from 'react';
import axios from 'axios';
import {
  X,
  Shield,
  AlertTriangle,
  FileText,
  User,
  HeartPulse,
  Send,
  Loader2,
  HelpCircle,
  Stethoscope,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { servicioAutenticacion } from '../../servicios/servicioAutenticacion';

const URL_BASE_API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ModalDetallePaciente = ({ expediente, alCerrar, alActualizar }) => {
  const [notasMedico, setNotasMedico] = useState('');
  const [prioridadAjustada, setPrioridadAjustada] = useState(
    expediente?.prioridad_final || expediente?.final_priority || 'AMARILLO'
  );
  const [enviandoRevision, setEnviandoRevision] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(false);

  if (!expediente) return null;

  const resultadoIa = expediente.resultado_ia || expediente.ai_result || expediente.resultados_ia || {};
  const sintomasPrincipales = resultadoIa.sintomas_principales || [];
  const senalesAlerta = resultadoIa.senales_alerta_identificadas || [];
  const preguntasFaltantes = resultadoIa.informacion_faltante_critica || [];
  const resumenNarrativo = resultadoIa.resumen_clinico_narrativo || 'Sin resumen narrativo generado.';

  const datosEstaticos = expediente.datos_estaticos || expediente.static_data || {};
  const respuestasDinamicas = expediente.respuestas_dinamicas || expediente.dynamic_answers || {};

  const guardarRevision = async (e) => {
    e.preventDefault();
    if (!notasMedico.trim()) {
      alert('Por favor ingrese las observaciones o diagnóstico médico antes de cerrar.');
      return;
    }

    setEnviandoRevision(true);
    try {
      const usuario = servicioAutenticacion.obtenerUsuarioActual();
      const token = servicioAutenticacion.obtenerToken();

      const payload = {
        triaje_id: expediente.id,
        triage_id: expediente.id,
        medico_id: usuario?.id || 'doc-uuid-12345',
        doctor_id: usuario?.id || 'doc-uuid-12345',
        notas_medico: notasMedico,
        doctor_notes: notasMedico,
        prioridad_ajustada: prioridadAjustada,
        priority_adjusted: prioridadAjustada,
      };

      await axios.post(`${URL_BASE_API}/api/v1/medico/revisar`, payload, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      });

      setMensajeExito(true);
      setTimeout(() => {
        if (alActualizar) alActualizar();
        alCerrar();
      }, 1200);
    } catch (error) {
      console.error('Error al registrar revisión médica:', error);
      alert('Ocurrió un error al guardar la revisión médica.');
    } finally {
      setEnviandoRevision(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-6xl w-full max-h-[94vh] flex flex-col shadow-2xl overflow-hidden text-slate-100">
        {/* Barra Superior del Modal */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">
                  Expediente Clínico: {expediente.nombre_paciente || expediente.patient_name}
                </h3>
                <span className="text-xs font-mono font-bold bg-slate-800 text-teal-400 px-2.5 py-0.5 rounded-md border border-slate-700">
                  {expediente.codigo_acceso || expediente.access_code}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {expediente.edad || expediente.age} años | Género: {expediente.genero || expediente.gender}
              </p>
            </div>
          </div>

          <button
            onClick={alCerrar}
            className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/60 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido en Pantalla Dividida (Split View) */}
        <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-0">
          {/* PANEL IZQUIERDO: Datos Crudos del Paciente (5 Cols) */}
          <div className="lg:col-span-5 p-6 border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-950/40 space-y-5 overflow-y-auto">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <User className="w-4 h-4 text-teal-400" />
              <span>Declaración Original del Paciente</span>
            </div>

            {/* Carnet de Identidad Descifrado */}
            <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-slate-400">Carnet de Identidad (CI):</span>
              </div>
              <span className="text-xs font-mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
                {expediente.ci_descifrado || expediente.decrypted_ci || 'Descifrado en Memoria'}
              </span>
            </div>

            {/* Motivo de Consulta Libre */}
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-1.5">
              <span className="text-xs font-semibold text-slate-400">Motivo de Consulta (Texto Libre):</span>
              <p className="text-sm text-slate-200 italic bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                "{expediente.sintomas_brutos || expediente.raw_symptoms}"
              </p>
            </div>

            {/* Datos Estáticos de Evolución e Intensidad */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-900 p-3 rounded-xl border border-slate-800">
                <span className="text-[11px] text-slate-400 block">Evolución:</span>
                <span className="text-xs font-bold text-white">{datosEstaticos.duracion || 'No especificada'}</span>
              </div>
              <div className="bg-slate-900 p-3 rounded-xl border border-slate-800">
                <span className="text-[11px] text-slate-400 block">Intensidad Dolor:</span>
                <span className="text-xs font-bold text-teal-400">{datosEstaticos.intensidad || 5} / 10</span>
              </div>
            </div>

            {/* Respuestas a Preguntas Dinámicas */}
            {Object.keys(respuestasDinamicas).length > 0 && (
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-teal-400" /> Respuestas a Preguntas Dinámicas:
                </span>
                <div className="space-y-1.5 text-xs text-slate-300">
                  {Object.entries(respuestasDinamicas).map(([clave, valor]) => (
                    <div key={clave} className="bg-slate-950/70 p-2 rounded border border-slate-800 flex justify-between">
                      <span className="text-slate-400">{clave}:</span>
                      <span className="font-semibold text-white">{String(valor)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* PANEL DERECHO: Inteligencia Artificial y Cierre Médico (7 Cols) */}
          <div className="lg:col-span-7 p-6 space-y-5 overflow-y-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
                <Sparkles className="w-4 h-4" />
                <span>Resumen Clínico Asistido por IA</span>
              </div>

              <span
                className={`text-xs font-bold px-3 py-1 rounded-full border ${
                  prioridadAjustada === 'ROJO' || prioridadAjustada === 'RED'
                    ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                    : prioridadAjustada === 'AMARILLO' || prioridadAjustada === 'YELLOW'
                    ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                    : 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                }`}
              >
                Prioridad: {prioridadAjustada}
              </span>
            </div>

            {/* Resumen Narrativo */}
            <div className="bg-slate-800/40 p-4 rounded-2xl border border-slate-700/60">
              <p className="text-xs leading-relaxed text-slate-200">{resumenNarrativo}</p>
            </div>

            {/* Banderas Rojas y Señales de Alerta */}
            {senalesAlerta.length > 0 && (
              <div className="bg-rose-950/20 border border-rose-500/30 p-3.5 rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-rose-400">
                  <AlertTriangle className="w-4 h-4" /> Banderas Rojas / Señales de Alerta:
                </div>
                <ul className="list-disc list-inside text-xs text-rose-200/90 space-y-0.5">
                  {senalesAlerta.map((alerta, i) => (
                    <li key={i}>{alerta}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Información Faltante Crítica */}
            {preguntasFaltantes.length > 0 && (
              <div className="bg-amber-950/20 border border-amber-500/30 p-3.5 rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                  <HelpCircle className="w-4 h-4" /> Datos Clínicos a Interrogar en Consulta:
                </div>
                <ul className="list-disc list-inside text-xs text-amber-200/90 space-y-0.5">
                  {preguntasFaltantes.map((pregunta, i) => (
                    <li key={i}>{pregunta}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Formulario de Revisión y Cierre Facultativo */}
            <form onSubmit={guardarRevision} className="space-y-4 pt-2 border-t border-slate-800">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Ajuste Facultativo de Prioridad
                  </label>
                  <select
                    value={prioridadAjustada}
                    onChange={(e) => setPrioridadAjustada(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="ROJO">🔴 ROJO (Atención Inmediata / Vital)</option>
                    <option value="AMARILLO">🟡 AMARILLO (Prioritario / Urgencia)</option>
                    <option value="VERDE">🟢 VERDE (Consulta No Urgente)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Notas de Evolución Médica / Diagnóstico Presuntivo
                </label>
                <textarea
                  rows="3"
                  value={notasMedico}
                  onChange={(e) => setNotasMedico(e.target.value)}
                  placeholder="Ingrese el diagnóstico presuntivo, conducta médica, medicamentos o derivación..."
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 resize-none"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={alCerrar}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition"
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  disabled={enviandoRevision}
                  className="px-6 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-teal-900/30 transition flex items-center gap-2 disabled:opacity-50"
                >
                  {enviandoRevision ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Cerrando Caso...</span>
                    </>
                  ) : mensajeExito ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                      <span>¡Atención Registrada!</span>
                    </>
                  ) : (
                    <>
                      <span>Cerrar y Dar de Alta</span>
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export const PatientDetailModal = ModalDetallePaciente;
export default ModalDetallePaciente;
