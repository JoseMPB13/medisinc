/**
 * Modal en Pantalla Dividida (Split View) para la Evaluación y Consulta Médica.
 * Panel Izquierdo: Anamnesis original del paciente, CI descifrado en memoria,
 * especialidad solicitada, alerta de alergias y antecedentes patológicos.
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
  Check,
  FileHeart,
  BriefcaseMedical,
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

  return (
    mapa[clave] ||
    clave
      .replace(/_/g, ' ')
      .replace(/^q\s*/i, '')
      .replace(/\b\w/g, (l) => l.toUpperCase())
  );
};

/**
 * Renderiza el valor de una respuesta dinámica de forma limpia (evitando [object Object]).
 */
const formatearValorRespuesta = (valor) => {
  if (valor === null || valor === undefined || valor === '') return 'No especificado';
  if (Array.isArray(valor)) {
    return valor
      .map((v) =>
        typeof v === 'object' ? v.label || v.etiqueta || v.valor || JSON.stringify(v) : String(v)
      )
      .join(', ');
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

  const resultadoIa =
    expediente.resultado_ia || expediente.ai_result || expediente.resultados_ia || {};
  const sintomasPrincipales = resultadoIa.sintomas_principales || [];
  const senalesAlerta = resultadoIa.senales_alerta_identificadas || [];
  const preguntasFaltantes = resultadoIa.informacion_faltante_critica || [];
  const factoresAgravantes = resultadoIa.factores_agravantes_antecedentes || [];
  const resumenNarrativo =
    resultadoIa.resumen_clinico_narrativo || 'Evaluación médica preliminar generada.';

  const datosEstaticos = expediente.datos_estaticos || expediente.static_data || {};
  const respuestasDinamicas = expediente.respuestas_dinamicas || expediente.dynamic_answers || {};

  const especialidad =
    expediente.especialidad_solicitada || expediente.requested_specialty || 'Medicina General';
  const alergias =
    expediente.alergias_medicamentosas || expediente.drug_allergies || 'Ninguna conocida';
  const medicacion = expediente.medicacion_actual || expediente.current_medication || 'Ninguna';
  const enfermedadesBase =
    expediente.enfermedades_base || expediente.base_diseases || [];

  const tieneAlergiasRiesgo =
    alergias &&
    alergias !== 'Ninguna' &&
    alergias !== 'Ninguna conocida' &&
    alergias.trim() !== '';

  const estadoActual = (expediente.estado || expediente.status || 'RECIBIDO').toUpperCase();
  const esRevisado = estadoActual === 'REVISADO' || estadoActual === 'REVIEWED';
  const esEnConsulta = estadoActual === 'EN_CONSULTA' || estadoActual === 'IN_CONSULTATION';

  const medicoAsignadoId = expediente.medico_asignado_id || expediente.assigned_doctor_id;
  const esMiPaciente =
    medicoAsignadoId &&
    usuarioActual?.id &&
    (medicoAsignadoId === usuarioActual.id || medicoAsignadoId === usuarioActual.usuario_id);

  const valorIntensidad = parseInt(datosEstaticos.intensidad || 5, 10);
  const colorIntensidad =
    valorIntensidad >= 7
      ? 'text-rose-400 bg-rose-950/40 border-rose-500/30'
      : valorIntensidad >= 4
      ? 'text-amber-400 bg-amber-950/40 border-amber-500/30'
      : 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30';

  // Guardar evaluación médica y cerrar consulta
  const guardarRevision = async (e) => {
    e.preventDefault();
    if (!notasMedico.trim()) {
      setMensajeError(
        'Por favor ingrese las observaciones clínicas y diagnóstico antes de finalizar la atención.'
      );
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

                {/* Badge de Especialidad */}
                <span className="inline-flex items-center gap-1 text-xs font-semibold bg-teal-950 text-teal-300 border border-teal-500/30 px-2.5 py-0.5 rounded-lg">
                  <BriefcaseMedical className="w-3.5 h-3.5" />
                  {especialidad}
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
                {expediente.edad || expediente.age} años | Género:{' '}
                {expediente.genero || expediente.gender || 'No especificado'} | Ingreso:{' '}
                {expediente.creado_en
                  ? new Date(expediente.creado_en).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : 'Reciente'}
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
                {liberando ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ArrowLeftRight className="w-3.5 h-3.5" />
                )}
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
          {/* PANEL IZQUIERDO: Anamnesis, Antecedentes y Declaración Original (5 Columnas) */}
          <div className="lg:col-span-5 p-6 border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-950/40 space-y-5 overflow-y-auto">
            {/* Banner de Advertencia de Alergias */}
            {tieneAlergiasRiesgo && (
              <div className="p-4 rounded-2xl bg-amber-950/60 border border-amber-500/60 shadow-lg text-amber-200 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5 animate-bounce" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                    ¡Alerta de Alergia a Medicamentos!
                  </h4>
                  <p className="text-xs mt-1 font-semibold text-white">
                    {alergias}
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <User className="w-4 h-4 text-teal-400" />
              <span>Anamnesis y Declaración del Paciente</span>
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
                <span className="text-xs font-black">{valorIntensidad} / 10</span>
              </div>
            </div>

            {/* Antecedentes Clínicos: Medicación y Comorbilidades */}
            <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 space-y-3 shadow-sm">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-300">
                <FileHeart className="w-4 h-4 text-teal-400" />
                <span>Antecedentes Clínicos</span>
              </div>

              <div>
                <span className="text-[11px] text-slate-400 font-semibold block mb-0.5">
                  Medicación Actual:
                </span>
                <p className="text-xs text-slate-200 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
                  {medicacion || 'Ninguna reportada'}
                </p>
              </div>

              <div>
                <span className="text-[11px] text-slate-400 font-semibold block mb-1">
                  Comorbilidades / Enfermedades de Base:
                </span>
                {enfermedadesBase.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {enfermedadesBase.map((enf, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-slate-800 text-teal-300 border border-slate-700 text-xs font-medium"
                      >
                        <Check className="w-3 h-3 text-teal-400" />
                        {enf}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">Sin antecedentes diagnosticados</p>
                )}
              </div>
            </div>

            {/* Respuestas a Preguntas Dinámicas PQRST */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <HelpCircle className="w-4 h-4 text-teal-400" />
                <span>Respuestas Dinámicas (Semiología PQRST)</span>
              </div>

              {Object.keys(respuestasDinamicas).length === 0 ? (
                <p className="text-xs text-slate-500 italic bg-slate-900 p-3.5 rounded-2xl border border-slate-800">
                  No se registraron respuestas complementarias.
                </p>
              ) : (
                <div className="space-y-2">
                  {Object.entries(respuestasDinamicas).map(([clave, valor]) => {
                    if (clave === 'notas_adicionales') return null;
                    return (
                      <div
                        key={clave}
                        className="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 text-xs space-y-1"
                      >
                        <span className="font-semibold text-teal-300 block">
                          {formatearEtiquetaPregunta(clave)}:
                        </span>
                        <span className="text-slate-200 block font-medium">
                          {formatearValorRespuesta(valor)}
                        </span>
                      </div>
                    );
                  })}

                  {respuestasDinamicas.notas_adicionales && (
                    <div className="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 text-xs space-y-1">
                      <span className="font-semibold text-slate-400 block">
                        Detalles / Comentarios Adicionales del Paciente:
                      </span>
                      <p className="text-slate-200 italic">
                        "{respuestasDinamicas.notas_adicionales}"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* PANEL DERECHO: Resumen Clínico por IA y Formulario de Cierre (7 Columnas) */}
          <div className="lg:col-span-7 p-6 space-y-5 overflow-y-auto bg-slate-900/50">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
                <Sparkles className="w-4 h-4" />
                <span>Síntesis Clínica Asistida por IA</span>
              </div>

              {expediente.sobreescritura_aplicada && (
                <span className="text-[11px] font-bold text-rose-400 bg-rose-950/60 border border-rose-500/40 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <AlertOctagon className="w-3.5 h-3.5" /> Safety Override Manchester
                </span>
              )}
            </div>

            {/* Resumen Narrativo */}
            <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Resumen Ejecutivo para el Médico:
              </span>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {resumenNarrativo}
              </p>
            </div>

            {/* Tarjeta de Banderas Rojas y Signos de Alarma */}
            {senalesAlerta.length > 0 && (
              <div className="bg-rose-950/20 border border-rose-500/30 p-4 rounded-2xl space-y-2">
                <span className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400" /> Banderas Rojas y Signos de Alerta:
                </span>
                <ul className="space-y-1 text-xs text-rose-200">
                  {senalesAlerta.map((alerta, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-400 font-bold">•</span>
                      <span>{alerta}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Datos Clínicos Estructurados (Síntomas y Factores Agravantes) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-teal-400 uppercase tracking-wider">
                  Síntomas Normalizados:
                </span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {sintomasPrincipales.length > 0 ? (
                    sintomasPrincipales.map((s, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                        <span>{s}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500 italic">No identificados</li>
                  )}
                </ul>
              </div>

              <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                  Factores y Antecedentes:
                </span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {factoresAgravantes.length > 0 ? (
                    factoresAgravantes.map((f, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                        <span>{f}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500 italic">Sin agravantes registrados</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Formulario de Cierre de Consulta Médica */}
            <form
              onSubmit={guardarRevision}
              className="bg-slate-950/90 p-5 rounded-2xl border border-slate-800 space-y-4 pt-4 shadow-xl"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-teal-400" /> Cierre y Conducta Médica
                </span>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400">Nivel Triaje:</span>
                  <select
                    value={prioridadAjustada}
                    onChange={(e) => setPrioridadAjustada(e.target.value)}
                    disabled={esRevisado}
                    className="bg-slate-900 border border-slate-700 text-xs rounded-xl px-2.5 py-1 text-white focus:outline-none focus:border-teal-500 font-bold"
                  >
                    <option value="ROJO">🔴 ROJO (Nivel I - Emergencia)</option>
                    <option value="AMARILLO">🟡 AMARILLO (Nivel II - Urgente)</option>
                    <option value="VERDE">🟢 VERDE (Nivel III - General)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Diagnóstico Presuntivo, Conducta y Prescripción Médica:
                </label>
                <textarea
                  rows="3"
                  value={notasMedico}
                  onChange={(e) => setNotasMedico(e.target.value)}
                  disabled={esRevisado}
                  placeholder={
                    esRevisado
                      ? 'Consulta médica cerrada.'
                      : 'Escriba las observaciones del examen físico, indicación farmacológica o derivación...'
                  }
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition resize-none disabled:opacity-60"
                />
              </div>

              {!esRevisado && (
                <button
                  type="submit"
                  disabled={enviandoRevision}
                  className="w-full bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-extrabold py-3 px-6 rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center justify-center gap-2 text-xs disabled:opacity-50"
                >
                  {enviandoRevision ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                      <span>Guardando en Expediente Clínico...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 text-slate-950" />
                      <span>Finalizar Atención y Cerrar Consulta</span>
                    </>
                  )}
                </button>
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
