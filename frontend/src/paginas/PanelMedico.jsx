/**
 * Portal del Médico de Guardia (MediSinc-IA).
 * Dashboard clínico con navegación por pestañas (Cola General vs Mis Pacientes),
 * asignación concurrente de casos, escáner QR y visor de expediente en pantalla dividida.
 */

import React, { useState, useEffect } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import {
  Stethoscope,
  Users,
  AlertOctagon,
  CheckCircle,
  Search,
  QrCode,
  LogOut,
  RefreshCw,
  Clock,
  ChevronRight,
  Shield,
  Filter,
  Sparkles,
  ArrowRight,
  UserCheck,
  History,
  AlertCircle,
  X,
  Play,
} from 'lucide-react';
import { servicioMedico } from '../servicios/servicioMedico';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';
import ModalDetallePaciente from '../componentes/medico/ModalDetallePaciente';

export const PanelMedico = () => {
  const usuarioActual = servicioAutenticacion.obtenerUsuarioActual();

  // Estados de navegación y datos
  const [pestanaActiva, setPestanaActiva] = useState('COLA_GENERAL'); // 'COLA_GENERAL' | 'MIS_PACIENTES'
  const [pacientesCola, setPacientesCola] = useState([]);
  const [misPacientes, setMisPacientes] = useState([]);
  const [incluirRevisados, setIncluirRevisados] = useState(false);

  const [metricas, setMetricas] = useState({
    en_espera: 0,
    en_consulta: 0,
    atendidos: 0,
    total_rojo: 0,
    total_hoy: 0,
  });

  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroPrioridad, setFiltroPrioridad] = useState('TODOS');
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState(null);
  const [mostrarEscaner, setMostrarEscaner] = useState(false);
  const [notificacion, setNotificacion] = useState(null);

  // Mostrar alerta temporal
  const lanzarNotificacion = (mensaje, tipo = 'info') => {
    setNotificacion({ mensaje, tipo });
    setTimeout(() => setNotificacion(null), 4000);
  };

  // Cargar datos de la cola general y mis pacientes
  const cargarDatos = async () => {
    try {
      const [resPanel, resMisPacientes] = await Promise.allSettled([
        servicioMedico.obtenerPanelGuardia(false),
        servicioMedico.obtenerMisPacientes(incluirRevisados),
      ]);

      if (resPanel.status === 'fulfilled') {
        const datos = resPanel.value;
        const lista = datos?.registros || datos?.records || [];
        const stats = datos?.metricas || datos?.metrics || {};

        setPacientesCola(lista);
        setMetricas({
          en_espera: stats.en_espera ?? stats.waiting_count ?? 0,
          en_consulta: stats.en_consulta ?? stats.in_consultation_count ?? 0,
          atendidos: stats.atendidos_hoy ?? stats.atendidos ?? stats.reviewed_count ?? 0,
          total_rojo: stats.total_rojo ?? stats.total_red ?? 0,
          total_hoy: stats.total_hoy ?? stats.total_today ?? lista.length,
        });
      }

      if (resMisPacientes.status === 'fulfilled') {
        const datosMis = resMisPacientes.value;
        setMisPacientes(datosMis?.pacientes || datosMis?.patients || []);
      }
    } catch (error) {
      console.error('Error al cargar datos del panel médico:', error);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos();
    const intervalo = setInterval(cargarDatos, 6000);
    return () => clearInterval(intervalo);
  }, [incluirRevisados]);

  // Manejo del escáner QR por cámara
  useEffect(() => {
    let scanner = null;
    if (mostrarEscaner) {
      scanner = new Html5QrcodeScanner(
        'qr-reader-container',
        { fps: 10, qrbox: { width: 250, height: 250 } },
        false
      );

      scanner.render(
        (codigoEscaneado) => {
          setBusqueda(codigoEscaneado);
          setMostrarEscaner(false);
          scanner.clear();
          lanzarNotificacion(`Código escaneado: ${codigoEscaneado}`, 'exito');
        },
        () => {}
      );
    }

    return () => {
      if (scanner) {
        try {
          scanner.clear();
        } catch {}
      }
    };
  }, [mostrarEscaner]);

  // Reclamar y atender un paciente (Asignación concurrente)
  const handleReclamarYAtender = async (paciente) => {
    try {
      const triajeId = paciente.id || paciente.codigo_acceso;
      await servicioMedico.asignarPaciente(triajeId);

      lanzarNotificacion('Paciente asignado a tu consulta activa.', 'exito');
      await cargarDatos();

      // Abrir directamente el expediente
      const expedienteCompleto = await servicioMedico.obtenerExpedientePaciente(triajeId);
      setPacienteSeleccionado(expedienteCompleto);
    } catch (error) {
      if (error.response && error.response.status === 409) {
        lanzarNotificacion(
          error.response.data?.detail || 'El paciente ya fue asignado a otro médico de guardia.',
          'error'
        );
      } else {
        lanzarNotificacion('Ocurrió un error al reclamar el paciente.', 'error');
      }
      cargarDatos();
    }
  };

  // Abrir expediente clínico en modo consulta
  const abrirExpediente = async (paciente) => {
    try {
      const id = paciente.codigo_acceso || paciente.access_code || paciente.id;
      const expedienteCompleto = await servicioMedico.obtenerExpedientePaciente(id);
      setPacienteSeleccionado(expedienteCompleto);
    } catch (error) {
      console.error('Error al abrir expediente:', error);
      setPacienteSeleccionado(paciente);
    }
  };

  // Filtrado reactivo en memoria
  const listaBase = pestanaActiva === 'COLA_GENERAL' ? pacientesCola : misPacientes;

  const pacientesFiltrados = listaBase.filter((p) => {
    const prioridad = (p.prioridad_final || p.final_priority || '').toUpperCase();
    const nombre = (p.nombre_paciente || p.patient_name || '').toLowerCase();
    const codigo = (p.codigo_acceso || p.access_code || '').toLowerCase();
    const termino = busqueda.toLowerCase().trim();

    const coincideBusqueda = !termino || nombre.includes(termino) || codigo.includes(termino);
    const coincideFiltro =
      filtroPrioridad === 'TODOS' ||
      prioridad === filtroPrioridad ||
      (filtroPrioridad === 'ROJO' && prioridad === 'RED') ||
      (filtroPrioridad === 'AMARILLO' && prioridad === 'YELLOW') ||
      (filtroPrioridad === 'VERDE' && prioridad === 'GREEN');

    return coincideBusqueda && coincideFiltro;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* ========================================================================= */}
      {/* Barra de Navegación del Portal Médico */}
      {/* ========================================================================= */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-black text-lg text-white tracking-tight flex items-center gap-2">
                Panel Médico de Guardia <span className="text-[11px] bg-teal-950 text-teal-300 px-2 py-0.5 rounded-full border border-teal-500/30">En Vivo</span>
              </h1>
              <p className="text-xs text-slate-400">
                {usuarioActual?.nombre || 'Dr. Médico de Turno'} | Servicio de Emergencias
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMostrarEscaner(true)}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-xl border border-slate-700 flex items-center gap-2 text-xs font-bold transition shadow-sm"
              title="Escanear código QR del paciente"
            >
              <QrCode className="w-4 h-4 text-teal-400" />
              <span className="hidden sm:inline">Escanear QR</span>
            </button>

            <button
              onClick={() => {
                servicioAutenticacion.cerrarSesion();
                window.location.href = '/iniciar-sesion';
              }}
              className="p-2 text-slate-400 hover:text-rose-400 rounded-xl bg-slate-800/80 hover:bg-slate-800 transition"
              title="Cerrar Sesión"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Notificación Flotante / Toast */}
      {notificacion && (
        <div
          className={`fixed top-20 right-6 z-50 px-4 py-3 rounded-2xl border shadow-xl flex items-center gap-2 text-xs font-bold animate-fade-in ${
            notificacion.tipo === 'error'
              ? 'bg-rose-950 border-rose-500 text-rose-200'
              : notificacion.tipo === 'exito'
              ? 'bg-emerald-950 border-emerald-500 text-emerald-200'
              : 'bg-slate-900 border-slate-700 text-slate-200'
          }`}
        >
          {notificacion.tipo === 'error' ? (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          ) : (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          )}
          <span>{notificacion.mensaje}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Contenido Principal */}
      {/* ========================================================================= */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 space-y-6">
        {/* Tarjetas de Métricas Cuantitativas Superiores */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-3xl shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">En Espera</span>
              <Users className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-2xl font-black text-white mt-2">{metricas.en_espera}</div>
            <p className="text-[11px] text-slate-500 mt-1">Pacientes en sala sin asignar</p>
          </div>

          <div className="bg-slate-900/80 border border-cyan-500/30 p-4 rounded-3xl shadow-lg bg-cyan-950/10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider">En Consulta</span>
              <UserCheck className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-black text-cyan-300 mt-2">{metricas.en_consulta}</div>
            <p className="text-[11px] text-cyan-300/70 mt-1">Pacientes bajo atención médica</p>
          </div>

          <div className="bg-slate-900/80 border border-rose-500/30 p-4 rounded-3xl shadow-lg bg-rose-950/10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-rose-300 uppercase tracking-wider">Emergencias Rojas</span>
              <AlertOctagon className="w-5 h-5 text-rose-400 animate-pulse" />
            </div>
            <div className="text-2xl font-black text-rose-400 mt-2">{metricas.total_rojo}</div>
            <p className="text-[11px] text-rose-300/70 mt-1">Atención inmediata requerida</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-3xl shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Atendidos Hoy</span>
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 mt-2">{metricas.atendidos}</div>
            <p className="text-[11px] text-slate-500 mt-1">Consultas cerradas</p>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* Navegación por Pestañas de Gestión */}
        {/* ========================================================================= */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPestanaActiva('COLA_GENERAL')}
              className={`px-5 py-2.5 rounded-2xl text-xs font-extrabold flex items-center gap-2 transition ${
                pestanaActiva === 'COLA_GENERAL'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Cola General de Guardia</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${pestanaActiva === 'COLA_GENERAL' ? 'bg-slate-950 text-teal-300' : 'bg-slate-800 text-slate-400'}`}>
                {pacientesCola.length}
              </span>
            </button>

            <button
              onClick={() => setPestanaActiva('MIS_PACIENTES')}
              className={`px-5 py-2.5 rounded-2xl text-xs font-extrabold flex items-center gap-2 transition ${
                pestanaActiva === 'MIS_PACIENTES'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <UserCheck className="w-4 h-4" />
              <span>Mis Pacientes Asignados</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${pestanaActiva === 'MIS_PACIENTES' ? 'bg-slate-950 text-teal-300' : 'bg-slate-800 text-slate-400'}`}>
                {misPacientes.length}
              </span>
            </button>
          </div>

          {/* Controles de la Pestaña Mis Pacientes */}
          {pestanaActiva === 'MIS_PACIENTES' && (
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer bg-slate-900 px-3.5 py-1.5 rounded-xl border border-slate-800">
              <input
                type="checkbox"
                checked={incluirRevisados}
                onChange={(e) => setIncluirRevisados(e.target.checked)}
                className="rounded border-slate-700 text-teal-500 focus:ring-0"
              />
              <History className="w-3.5 h-3.5 text-slate-400" />
              <span>Ver Historial Atendidos</span>
            </label>
          )}
        </div>

        {/* ========================================================================= */}
        {/* Barra de Filtros y Búsqueda */}
        {/* ========================================================================= */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-3xl flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por Nombre, CI o Código MS-XXXXX..."
              className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition"
            />
            {busqueda && (
              <button
                onClick={() => setBusqueda('')}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-300"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" /> Prioridad:
            </span>
            {['TODOS', 'ROJO', 'AMARILLO', 'VERDE'].map((filtro) => (
              <button
                key={filtro}
                onClick={() => setFiltroPrioridad(filtro)}
                className={`px-3 py-1.5 rounded-xl text-xs font-extrabold transition ${
                  filtroPrioridad === filtro
                    ? filtro === 'ROJO'
                      ? 'bg-rose-500 text-white'
                      : filtro === 'AMARILLO'
                      ? 'bg-amber-500 text-slate-950'
                      : filtro === 'VERDE'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-teal-500 text-slate-950'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {filtro}
              </button>
            ))}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* Tabla de Pacientes */}
        {/* ========================================================================= */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Prioridad</th>
                  <th className="py-3.5 px-4">Código / Paciente</th>
                  <th className="py-3.5 px-4">Motivo Principal</th>
                  <th className="py-3.5 px-4">Estado / Asignación</th>
                  <th className="py-3.5 px-4">Llegada</th>
                  <th className="py-3.5 px-4 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cargando ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto text-teal-400 mb-2" />
                      Cargando registros clínicos en tiempo real...
                    </td>
                  </tr>
                ) : pacientesFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      No se encontraron pacientes para el filtro seleccionado.
                    </td>
                  </tr>
                ) : (
                  pacientesFiltrados.map((paciente) => {
                    const prioridad = (paciente.prioridad_final || paciente.final_priority || 'VERDE').toUpperCase();
                    const estado = (paciente.estado || paciente.status || 'RECIBIDO').toUpperCase();
                    const esRojo = prioridad === 'ROJO' || prioridad === 'RED';
                    const esAmarillo = prioridad === 'AMARILLO' || prioridad === 'YELLOW';
                    const esVerde = prioridad === 'VERDE' || prioridad === 'GREEN';

                    const medicoAsig = paciente.medico_asignado_id || paciente.assigned_doctor_id;
                    const asignadoAMi = medicoAsig && usuarioActual?.id && (medicoAsig === usuarioActual.id || medicoAsig === usuarioActual.usuario_id);
                    const asignadoAOtro = medicoAsig && !asignadoAMi;
                    const enConsulta = estado === 'EN_CONSULTA' || estado === 'IN_CONSULTATION';
                    const revisado = estado === 'REVISADO' || estado === 'REVIEWED';

                    return (
                      <tr
                        key={paciente.id || paciente.codigo_acceso}
                        className={`hover:bg-slate-800/40 transition ${
                          esRojo ? 'bg-rose-950/5' : ''
                        }`}
                      >
                        {/* 1. Prioridad */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black border ${
                              esRojo
                                ? 'bg-rose-500/20 border-rose-500 text-rose-400'
                                : esAmarillo
                                ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                                : 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                            }`}
                          >
                            <span className="w-2 h-2 rounded-full bg-current"></span>
                            {prioridad}
                          </span>
                        </td>

                        {/* 2. Código y Paciente */}
                        <td className="py-4 px-4">
                          <div className="font-extrabold text-white text-sm">
                            {paciente.nombre_paciente || paciente.patient_name || 'Paciente'}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            {paciente.codigo_acceso || paciente.access_code} | {paciente.edad || paciente.age} años (
                            {paciente.genero || paciente.gender || 'N/E'})
                          </div>
                        </td>

                        {/* 3. Motivo Principal */}
                        <td className="py-4 px-4 max-w-xs truncate text-slate-300">
                          {paciente.sintomas_brutos || paciente.raw_symptoms || 'Sin declaración'}
                        </td>

                        {/* 4. Estado y Asignación */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          {revisado ? (
                            <span className="text-[11px] font-bold bg-slate-800 text-slate-400 px-2.5 py-1 rounded-lg border border-slate-700">
                              ATENDIDO
                            </span>
                          ) : enConsulta ? (
                            asignadoAMi ? (
                              <span className="text-[11px] font-bold bg-cyan-950 text-cyan-300 px-2.5 py-1 rounded-lg border border-cyan-500/40">
                                En tu consulta
                              </span>
                            ) : (
                              <span className="text-[11px] font-bold bg-amber-950 text-amber-300 px-2.5 py-1 rounded-lg border border-amber-500/40">
                                En consulta (Otro médico)
                              </span>
                            )
                          ) : (
                            <span className="text-[11px] font-bold bg-emerald-950 text-emerald-300 px-2.5 py-1 rounded-lg border border-emerald-500/40">
                              En espera
                            </span>
                          )}
                        </td>

                        {/* 5. Hora de Llegada */}
                        <td className="py-4 px-4 whitespace-nowrap text-slate-400 text-xs">
                          {paciente.creado_en
                            ? new Date(paciente.creado_en).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : 'Reciente'}
                        </td>

                        {/* 6. Botón de Acción */}
                        <td className="py-4 px-4 text-right whitespace-nowrap">
                          {revisado ? (
                            <button
                              onClick={() => abrirExpediente(paciente)}
                              className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition"
                            >
                              Ver Ficha
                            </button>
                          ) : enConsulta && asignadoAMi ? (
                            <button
                              onClick={() => abrirExpediente(paciente)}
                              className="px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-1.5 ml-auto shadow-md transition"
                            >
                              <Play className="w-3.5 h-3.5 fill-current" />
                              <span>Continuar</span>
                            </button>
                          ) : enConsulta && asignadoAOtro ? (
                            <button
                              onClick={() => abrirExpediente(paciente)}
                              className="px-3 py-1.5 bg-slate-800/80 text-slate-500 rounded-xl text-xs font-semibold cursor-pointer hover:text-slate-300"
                              title="Consultar expediente en modo solo lectura"
                            >
                              Inspeccionar
                            </button>
                          ) : (
                            <button
                              onClick={() => handleReclamarYAtender(paciente)}
                              className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-black rounded-xl text-xs flex items-center gap-1.5 ml-auto shadow-md shadow-teal-500/20 transition"
                            >
                              <Stethoscope className="w-3.5 h-3.5" />
                              <span>Atender</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* ========================================================================= */}
      {/* Modal de Escaneo QR por Cámara Web */}
      {/* ========================================================================= */}
      {mostrarEscaner && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white flex items-center gap-2 text-sm">
                <QrCode className="w-4 h-4 text-teal-400" /> Escanear Código QR del Paciente
              </h3>
              <button
                onClick={() => setMostrarEscaner(false)}
                className="p-1.5 text-slate-400 hover:text-white rounded-xl bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div
              id="qr-reader-container"
              className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950"
            ></div>

            <p className="text-[11px] text-slate-400 text-center">
              Apunta la cámara al código QR impreso o en pantalla del paciente.
            </p>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Modal de Detalle de Expediente Clínico (Split View) */}
      {/* ========================================================================= */}
      {pacienteSeleccionado && (
        <ModalDetallePaciente
          expediente={pacienteSeleccionado}
          alCerrar={() => setPacienteSeleccionado(null)}
          alActualizar={cargarDatos}
        />
      )}
    </div>
  );
};

export const DoctorDashboard = PanelMedico;
export default PanelMedico;
