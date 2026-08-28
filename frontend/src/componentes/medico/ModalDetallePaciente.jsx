/**
 * Modal en Pantalla Dividida (Split View) para la Evaluación y Consulta Médica.
 * Panel Izquierdo: Anamnesis original del paciente, CI descifrado en memoria y respuestas PQRST.
 * Panel Derecho: Resumen estructurado por IA, banderas rojas, examen sugerido y formulario de cierre.
 */

import React, { useState } from 'react';
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
  ArrowLeftRight,
  Clock,
  Activity,
  AlertOctagon,
  Pill,
} from 'lucide-react';
import { servicioMedico } from '../../servicios/servicioMedico';
import { servicioAutenticacion } from '../../servicios/servicioAutenticacion';

/**
 * Formatea claves o identificadores de preguntas dinámicas a títulos legibles en español.
 */
const formatearEtiquetaPregunta = (clave) => {
  const mapa = {
    q_caracteristica: 'Tipo e Irradiación del Dolor',
    q_enfermedades: 'Enfermedades Previas Diagnosticadas',
    q_medicamentos: 'Medicación Habitual / Fármacos Tomados',
    q_headache_type: 'Inicio y Síntomas de Cefalea',
    q_headache_pqrst: 'Semiología de Cefalea',
    q_chest_type: 'Semiología y Dolor Torácico',
    q_chest_pqrst: 'Semiología y Dolor Torácico',
    q_abdo_loc: 'Localización Abdominal y Vómitos',
    q_abdo_pqrst: 'Localización Abdominal y Vómitos',
    q_resp_severity: 'Compromiso Respiratorio y Disnea',
    q_fever_signs: 'Signos Acompañantes del Síndrome Febril',
    q_gen_evolution: 'Evolución y Tiempo de Inicio',
    q_gen_pqrst: 'Evolución y Tiempo de Inicio',
    q_antecedentes_enfermedades: 'Comorbilidades / Antecedentes Crónicos',
    q_enfermedades_comorbilidades: 'Comorbilidades / Antecedentes Crónicos',
    q_medicamentos_actuales: 'Medicación Actual y Tratamientos Recientes',
    q_medicamentos_tratamientos: 'Medicación Actual y Tratamientos Recientes',
    duracion: 'Tiempo de Evolución',
    intensidad: 'Intensidad del Dolor',
    motivo: 'Motivo Principal de Consulta',
  };

  return mapa[clave] || clave.replace(/_/g, ' ').replace(/^q\s*/i, '').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Renderiza el valor de una respuesta dinámica de forma limpia (evitando [object Object]).
 */
const formatearValorRespuesta = (valor) => {
  if (valor === null || valor === undefined || valor === '') return 'No especificado';
  if (Array.isArray(valor)) {
    return valor.map((v) => (typeof v === 'object' ? v.label || v.etiqueta || v.valor || JSON.stringify(v) : String(v))).join(', ');
  }
  if (typeof valor === 'object') {
    return valor.label || valor.etiqueta || valor.valor || valor.texto || JSON.stringify(valor);
  }
  return String(valor);
};

export const ModalDetallePaciente = ({ expediente, alCerrar, alActualizar }) => {
  const usuarioActual = servicioAutenticacion.obtenerUsuarioActual();

  const [notasMedico, setNotasMedico] = useState('');
  const [prioridadAjustada, setPrioridadAjustada] = useState(
    expediente?.prioridad_final || expediente?.final_priority || 'AMARILLO'
  );
  const [enviandoRevision, setEnviandoRevision] = useState(false);
  const [liberando, setLiberando] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(null);
  const [mensajeError, setMensajeError] = useState(null);

  if (!expediente) return null;

  const resultadoIa = expediente.resultado_ia || expediente.ai_result || expediente.resultados_ia || {};
  const sintomasPrincipales = resultadoIa.sintomas_principales || [];
  const senalesAlerta = resultadoIa.senales_alerta_identificadas || [];
  const preguntasFaltantes = resultadoIa.informacion_faltante_critica || [];
  const resumenNarrativo = resultadoIa.resumen_clinico_narrativo || 'Evaluación médica preliminar generada.';

  const datosEstaticos = expediente.datos_estaticos || expediente.static_data || {};
  const respuestasDinamicas = expediente.respuestas_dinamicas || expediente.dynamic_answers || {};

  const estadoActual = (expediente.estado || expediente.status || 'RECIBIDO').toUpperCase();
  const esRevisado = estadoActual === 'REVISADO' || estadoActual === 'REVIEWED';
  const esEnConsulta = estadoActual === 'EN_CONSULTA' || estadoActual === 'IN_CONSULTATION';

  const medicoAsignadoId = expediente.medico_asignado_id || expediente.assigned_doctor_id;
  const esMiPaciente = medicoAsignadoId && usuarioActual?.id && (medicoAsignadoId === usuarioActual.id || medicoAsignadoId === usuarioActual.usuario_id);

  const valorIntensidad = parseInt(datosEstaticos.intensidad || 5, 10);
  const colorIntensidad =
    valorIntensidad >= 7 ? 'text-rose-400 bg-rose-950/40 border-rose-500/30' : valorIntensidad >= 4 ? 'text-amber-400 bg-amber-950/40 border-amber-500/30' : 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30';

  // Guardar evaluación médica y cerrar consulta
  const guardarRevision = async (e) => {
    e.preventDefault();
    if (!notasMedico.trim()) {
      setMensajeError('Por favor ingrese las observaciones clínicas y diagnóstico antes de finalizar la atención.');
      return;
    }

    setEnviandoRevision(true);
    setMensajeError(null);

    try {
      const payload = {
        triaje_id: expediente.id,
        triage_id: expediente.id,
        medico_id: usuarioActual?.id || usuarioActual?.usuario_id || 'doc-uuid-12345',
        doctor_id: usuarioActual?.id || usuarioActual?.usuario_id || 'doc-uuid-12345',
        notas_medico: notasMedico,
        doctor_notes: notasMedico,
        prioridad_ajustada: prioridadAjustada,
        priority_adjusted: prioridadAjustada,
      };

      await servicioMedico.guardarRevisionMedica(payload);
      setMensajeExito('Consulta médica registrada y cerrada exitosamente.');

      setTimeout(() => {
        if (alActualizar) alActualizar();
        alCerrar();
      }, 1000);
    } catch (error) {
      console.error('Error al registrar revisión médica:', error);
      setMensajeError('Ocurrió un error al guardar la revisión médica.');
    } finally {
      setEnviandoRevision(false);
    }
  };

  // Liberar paciente a la cola general
  const handleLiberar = async () => {
    if (!window.confirm('¿Deseas liberar este paciente para que vuelva a la lista de espera general?')) {
      return;
    }

    setLiberando(true);
    setMensajeError(null);

    try {
      await servicioMedico.liberarPaciente(expediente.id);
      setMensajeExito('Paciente liberado a la cola general de guardia.');

      setTimeout(() => {
        if (alActualizar) alActualizar();
        alCerrar();
      }, 900);
    } catch (error) {
      console.error('Error liberando paciente:', error);
      setMensajeError('No se pudo liberar el paciente.');
    } finally {
      setLiberando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-6xl w-full max-h-[94vh] flex flex-col shadow-2xl overflow-hidden text-slate-100">
        {/* ========================================================================= */}
        {/* Encabezado del Modal Clínico */}
        {/* ========================================================================= */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/95">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Expediente Clínico: {expediente.nombre_paciente || expediente.patient_name || 'Paciente'}
                </h3>
                <span className="text-xs font-mono font-bold bg-slate-800 text-teal-400 px-2.5 py-0.5 rounded-md border border-slate-700">
                  {expediente.codigo_acceso || expediente.access_code}
                </span>

                {/* Badge de Estado del Ciclo de Vida */}
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                    esRevisado
                      ? 'bg-slate-800 text-slate-400 border-slate-700'
                      : esEnConsulta
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
                      : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  }`}
                >
                  {esRevisado ? 'ATENDIDO' : esEnConsulta ? 'EN CONSULTA ACTIVA' : 'EN ESPERA DE GUARDIA'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {expediente.edad || expediente.age} años | Género: {expediente.genero || expediente.gender || 'No especificado'} | Ingreso:{' '}
                {expediente.creado_en ? new Date(expediente.creado_en).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Reciente'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Botón Liberar Paciente */}
            {esEnConsulta && !esRevisado && (
              <button
                type="button"
                onClick={handleLiberar}
                disabled={liberando}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-amber-400 border border-amber-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                title="Devolver este paciente a la cola general"
              >
                {liberando ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowLeftRight className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">Liberar a Guardia</span>
              </button>
            )}

            <button
              onClick={alCerrar}
              className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/60 hover:bg-slate-800 transition"
              title="Cerrar ventana"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Notificaciones de Alerta / Éxito */}
        {mensajeExito && (
          <div className="bg-emerald-950/80 border-b border-emerald-500/40 px-6 py-2.5 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{mensajeExito}</span>
          </div>
        )}
        {mensajeError && (
          <div className="bg-rose-950/80 border-b border-rose-500/40 px-6 py-2.5 text-xs text-rose-300 flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <span>{mensajeError}</span>
          </div>
        )}

        {/* ========================================================================= */}
        {/* Contenido en Pantalla Dividida (Split View) */}
        {/* ========================================================================= */}
        <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-0">
          {/* PANEL IZQUIERDO: Anamnesis y Declaración Original (5 Columnas) */}
          <div className="lg:col-span-5 p-6 border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-950/40 space-y-5 overflow-y-auto">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <User className="w-4 h-4 text-teal-400" />
              <span>Anamnesis y Declaración Original</span>
            </div>

            {/* Carnet de Identidad Descifrado con Badge Criptográfico */}
            <div className="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-2.5">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-medium text-slate-400">Carnet de Identidad:</span>
              </div>
              <span className="text-xs font-mono font-bold text-white bg-slate-800 px-3 py-1 rounded-lg border border-slate-700">
                {expediente.ci_descifrado || expediente.decrypted_ci || 'Protegido'}
              </span>
            </div>

            {/* Motivo de Consulta Libre */}
            <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 space-y-1.5 shadow-sm">
              <span className="text-xs font-semibold text-slate-400">Motivo de Consulta (Texto Libre):</span>
              <p className="text-sm text-slate-200 italic bg-slate-950 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                "{expediente.sintomas_brutos || expediente.raw_symptoms || 'Sin declaración registrada.'}"
              </p>
            </div>

            {/* Parámetros Estáticos: Intensidad de Dolor y Duración */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-900 p-3.5 rounded-2xl border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
                  <Clock className="w-3.5 h-3.5 text-teal-400" /> Tiempo de Evolución:
                </span>
                <span className="text-xs font-bold text-white">
                  {formatearValorRespuesta(datosEstaticos.duracion || datosEstaticos.duration)}
                </span>
              </div>

              <div className={`p-3.5 rounded-2xl border ${colorIntensidad}`}>
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
                  <Activity className="w-3.5 h-3.5" /> Escala del Dolor:
                </span>
                <span className="text-xs font-black">
                  {valorIntensidad} / 10
                </span>
              </div>
            </div>

            {/* Respuestas a Preguntas Dinámicas Adaptativas (PQRST) */}
            {Object.keys(respuestasDinamicas).length > 0 && (
              <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 space-y-3 shadow-sm">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-teal-400" /> Respuestas Semiológicas (PQRST):
                </span>

                <div className="space-y-2 text-xs">
                  {Object.entries(respuestasDinamicas).map(([clave, valor]) => (
                    <div key={clave} className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 space-y-1">
                      <span className="text-[11px] font-semibold text-slate-400 block">
                        {formatearEtiquetaPregunta(clave)}
                      </span>
                      <span className="font-bold text-slate-100 block">
                        {formatearValorRespuesta(valor)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* PANEL DERECHO: Inteligencia Artificial y Cierre Médico (7 Columnas) */}
          <div className="lg:col-span-7 p-6 space-y-5 overflow-y-auto">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
                <Sparkles className="w-4 h-4" />
                <span>Resumen Clínico y Ayuda Diagnóstica IA</span>
              </div>

              {/* Badge de Prioridad de Triaje */}
              <span
                className={`text-xs font-extrabold px-3 py-1 rounded-full border shadow-sm ${
                  prioridadAjustada === 'ROJO' || prioridadAjustada === 'RED'
                    ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                    : prioridadAjustada === 'AMARILLO' || prioridadAjustada === 'YELLOW'
                    ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                    : 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                }`}
              >
                Prioridad Actual: {prioridadAjustada}
              </span>
            </div>

            {/* Resumen Clínico Narrativo */}
            <div className="bg-slate-800/40 p-4 rounded-2xl border border-slate-700/60 shadow-sm space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Síntesis Clínica Estructurada:
              </span>
              <p className="text-xs leading-relaxed text-slate-200">{resumenNarrativo}</p>
            </div>

            {/* Banderas Rojas y Señales de Alerta */}
            {senalesAlerta.length > 0 && (
              <div className="bg-rose-950/20 border border-rose-500/30 p-4 rounded-2xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-rose-400">
                  <AlertTriangle className="w-4 h-4" /> Banderas Rojas / Signos de Alerta Detectados:
                </div>
                <ul className="list-disc list-inside text-xs text-rose-200/90 space-y-1">
                  {senalesAlerta.map((alerta, i) => (
                    <li key={i}>{alerta}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Información Faltante y Examen Físico Sugerido */}
            {preguntasFaltantes.length > 0 && (
              <div className="bg-amber-950/20 border border-amber-500/30 p-4 rounded-2xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                  <HelpCircle className="w-4 h-4" /> Puntos Críticos para el Examen Físico:
                </div>
                <ul className="list-disc list-inside text-xs text-amber-200/90 space-y-1">
                  {preguntasFaltantes.map((pregunta, i) => (
                    <li key={i}>{pregunta}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* ========================================================================= */}
            {/* Formulario de Evaluación y Cierre de Consulta */}
            {/* ========================================================================= */}
            <form onSubmit={guardarRevision} className="space-y-4 pt-4 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-teal-400" />
                  <span>Diagnóstico Presuntivo y Conducta Médica</span>
                </label>

                {/* Selector Facultativo de Prioridad */}
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400">Ajuste de Prioridad:</span>
                  <select
                    value={prioridadAjustada}
                    onChange={(e) => setPrioridadAjustada(e.target.value)}
                    disabled={esRevisado}
                    className="bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1 text-xs text-white focus:outline-none focus:border-teal-500 font-bold"
                  >
                    <option value="ROJO">🔴 ROJO (Vital)</option>
                    <option value="AMARILLO">🟡 AMARILLO (Urgencia)</option>
                    <option value="VERDE">🟢 VERDE (No Urgente)</option>
                  </select>
                </div>
              </div>

              {/* Área de Texto para Notas de Evolución */}
              <textarea
                value={notasMedico}
                onChange={(e) => setNotasMedico(e.target.value)}
                placeholder={
                  esRevisado
                    ? 'Consulta concluida y sellada.'
                    : 'Describa el diagnóstico presuntivo, signos vitales tomados, fármacos indicados y conducta terapéutica...'
                }
                disabled={esRevisado || enviandoRevision}
                rows={4}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-2xl p-3.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition resize-none disabled:opacity-60"
              />

              {/* Botón de Cierre de Consulta */}
              {!esRevisado ? (
                <button
                  type="submit"
                  disabled={enviandoRevision}
                  className="w-full py-3.5 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 font-bold rounded-2xl text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-teal-500/20 disabled:opacity-60"
                >
                  {enviandoRevision ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Guardando Dictamen Médico...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirmar y Finalizar Atención Médica</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-xl text-center text-xs text-slate-400">
                  ✓ Este caso ya fue atendido y cerrado en el historial médico.
                </div>
              )}
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export const PatientDetailModal = ModalDetallePaciente;
export default ModalDetallePaciente;
