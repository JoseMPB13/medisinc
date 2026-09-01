/**
 * Portal del Administrador y Gobernanza del Centro de Salud (MediSinc-IA).
 * Proporciona métricas cuantitativas consolidadas, gestión de profesionales médicos
 * con asignación de turnos de guardia y especialidades, y visor de auditoría.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck,
  UserPlus,
  Users,
  Activity,
  AlertTriangle,
  Clock,
  LogOut,
  RefreshCw,
  Search,
  FileText,
  Lock,
  CheckCircle2,
  Stethoscope,
  Edit2,
  Check,
  X,
  Power,
  Sun,
  Sunset,
  Moon,
  ShieldAlert,
  User,
  Star,
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';
import { servicioAdmin } from '../servicios/servicioAdmin';

const ESPECIALIDADES_DISPONIBLES = [
  'Medicina General',
  'Pediatría',
  'Ginecología y Obstetricia',
  'Traumatología y Urgencias',
  'Cardiología y Medicina Interna',
  'Odontología',
];

const TURNOS_DISPONIBLES = [
  { valor: 'MANANA', etiqueta: 'Mañana (07:00 - 15:00)', icono: Sun, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  { valor: 'TARDE_NOCHE', etiqueta: 'Tarde/Noche (15:00 - 23:00)', icono: Sunset, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
  { valor: 'MADRUGADA', etiqueta: 'Madrugada (23:00 - 07:00)', icono: Moon, color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
  { valor: 'TODOS', etiqueta: 'Guardia Completa / 24h', icono: Clock, color: 'text-teal-400 bg-teal-500/10 border-teal-500/30' },
];

export const PanelAdministrador = () => {
  const [estadisticas, setEstadisticas] = useState({
    total_triajes: 0,
    casos_rojo_urgente: 0,
    casos_revisados: 0,
    medicos_activos: 0,
    tiempo_promedio_atencion_min: 0.0,
  });
  const [medicos, setMedicos] = useState([]);
  const [auditorias, setAuditorias] = useState([]);
  const [pacientesHistorico, setPacientesHistorico] = useState([]);
  const [pestanaActiva, setPestanaActiva] = useState('resumen'); // 'resumen' | 'medicos' | 'auditoria' | 'calendario'
  const [cargando, setCargando] = useState(true);

  // Estados para Calendario
  const [fechaCalendario, setFechaCalendario] = useState(new Date());
  const [diaSeleccionado, setDiaSeleccionado] = useState(new Date().getDate());

  // Construir citas en base a pacientes/triajes reales
  const citasReales = useMemo(() => {
    if (!pacientesHistorico || pacientesHistorico.length === 0) return {};
    const citas = {};
    const currentYear = fechaCalendario.getFullYear();
    const currentMonth = fechaCalendario.getMonth();

    pacientesHistorico.forEach(p => {
      const date = new Date(p.creado_en || new Date());
      if (date.getFullYear() === currentYear && date.getMonth() === currentMonth) {
        const day = date.getDate();
        if (!citas[day]) citas[day] = [];

        let nomMedico = 'Sin Asignar';
        let espMedico = p.especialidad_solicitada || 'Medicina General';
        if (p.medico_asignado_id) {
          const med = medicos.find(m => m.id === p.medico_asignado_id);
          if (med) nomMedico = med.nombre_completo || med.full_name;
        }

        const horaStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        citas[day].push({
          id: p.id,
          medico: nomMedico,
          medico_id: p.medico_asignado_id,
          especialidad: espMedico,
          hora: horaStr,
          paciente: p.nombre_paciente || p.patient_name || 'Paciente',
          estado: (p.estado || 'PENDIENTE').toUpperCase(),
          fecha_original: p.creado_en
        });
      }
    });

    // Ordenar citas del día por hora
    Object.keys(citas).forEach(day => {
      citas[day].sort((a, b) => a.hora.localeCompare(b.hora));
    });

    return citas;
  }, [pacientesHistorico, fechaCalendario, medicos]);

  const [citaEditando, setCitaEditando] = useState(null);
  const [datosEdicionCita, setDatosEdicionCita] = useState({});

  const guardarCambiosCita = async (e) => {
    e.preventDefault();
    if (!citaEditando) return;
    try {
      await servicioAdmin.actualizarCita(citaEditando.id, {
        medico_asignado_id: datosEdicionCita.medico_asignado_id,
        fecha_cita: datosEdicionCita.fecha_cita
      });
      setMensajeExito('Cita re-agendada correctamente.');
      setCitaEditando(null);
      cargarDatosAdmin();
    } catch (err) {
      alert('Error al actualizar cita: ' + (err.detail || err.message));
    }
  };

  // Formulario nuevo médico
  const [nuevoMedico, setNuevoMedico] = useState({
    nombre_completo: '',
    correo: '',
    password: '',
    especialidad: 'Medicina General',
    rol: 'MEDICO',
    turno_asignado: 'MANANA',
  });
  const [creandoMedico, setCreandoMedico] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(null);

  // Edición rápida de médico
  const [medicoEnEdicion, setMedicoEnEdicion] = useState(null);
  const [guardandoEdicion, setGuardandoEdicion] = useState(false);

  const usuarioActual = servicioAutenticacion.obtenerUsuarioActual();

  const cargarDatosAdmin = async () => {
    try {
      const [statsRes, medicosRes, auditRes, pacientesRes] = await Promise.allSettled([
        servicioAdmin.obtenerEstadisticasAdmin(),
        servicioAdmin.listarMedicos(),
        servicioAdmin.listarRegistrosAuditoria(50),
        servicioAdmin.listarPacientesHistorico(),
      ]);

      if (statsRes.status === 'fulfilled') setEstadisticas(statsRes.value);
      if (medicosRes.status === 'fulfilled') setMedicos(medicosRes.value || []);
      if (auditRes.status === 'fulfilled') setAuditorias(auditRes.value || []);
      if (pacientesRes.status === 'fulfilled') setPacientesHistorico(pacientesRes.value.datos || pacientesRes.value || []);
    } catch (e) {
      console.error('Error cargando portal de administración:', e);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatosAdmin();
  }, []);

  const registrarMedico = async (e) => {
    e.preventDefault();
    setCreandoMedico(true);
    setMensajeExito(null);
    try {
      await servicioAdmin.crearMedico(nuevoMedico);
      setMensajeExito('Médico registrado exitosamente con turno asignado.');
      setNuevoMedico({
        nombre_completo: '',
        correo: '',
        password: '',
        especialidad: 'Medicina General',
        rol: 'MEDICO',
        turno_asignado: 'MANANA',
      });
      cargarDatosAdmin();
    } catch (err) {
      alert('Error al registrar médico: ' + (err.detail || err.message));
    } finally {
      setCreandoMedico(false);
    }
  };

  const guardarCambiosMedico = async (medicoId) => {
    if (!medicoEnEdicion) return;
    setGuardandoEdicion(true);
    try {
      await servicioAdmin.actualizarMedico(medicoId, medicoEnEdicion);
      setMedicoEnEdicion(null);
      setMensajeExito('Datos de guardia y especialidad actualizados.');
      cargarDatosAdmin();
    } catch (err) {
      alert('Error al actualizar médico: ' + (err.detail || err.message));
    } finally {
      setGuardandoEdicion(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Barra de Navegación */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg text-white tracking-tight flex items-center gap-2">
                Portal de Administración y Gobernanza
              </h1>
              <p className="text-xs text-slate-400">
                {usuarioActual?.nombre || 'Administrador Central'} | MediSinc-IA
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                servicioAutenticacion.cerrarSesion();
                window.location.href = '/iniciar-sesion';
              }}
              className="text-xs text-rose-400 hover:text-rose-300 border border-rose-500/30 bg-rose-500/10 px-3.5 py-1.5 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </header>

      {/* Menú de Pestañas */}
      <div className="border-b border-slate-800 bg-slate-900/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex space-x-4">
          <button
            onClick={() => setPestanaActiva('resumen')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${pestanaActiva === 'resumen'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
          >
            <Activity className="w-4 h-4" />
            <span>Métricas Clínicas</span>
          </button>

          <button
            onClick={() => setPestanaActiva('medicos')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${pestanaActiva === 'medicos'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
          >
            <Users className="w-4 h-4" />
            <span>Gestión de Médicos y Turnos ({medicos.length})</span>
          </button>

          <button
            onClick={() => setPestanaActiva('calendario')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${pestanaActiva === 'calendario'
              ? 'border-teal-500 text-teal-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
          >
            <CalendarIcon className="w-4 h-4" />
            <span>Agenda Médica</span>
          </button>

          <button
            onClick={() => setPestanaActiva('auditoria')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${pestanaActiva === 'auditoria'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
          >
            <FileText className="w-4 h-4" />
            <span>Bitácora de Auditoría</span>
          </button>
        </div>
      </div>

      {/* Contenedor Principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1">
        {/* CONTENIDO DE PESTAÑA: RESUMEN / MÉTRICAS */}
        {pestanaActiva === 'resumen' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
            {/* 1. Columna Izquierda (Métricas y Ocupación) */}
            <div className="lg:col-span-5 flex flex-col gap-6">

              {/* Tarjeta 1: Métricas Principales */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl">
                <h3 className="text-sm font-bold text-white mb-5 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-400" />
                  Métricas Principales
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1">Pre-Triajes</span>
                    <p className="text-2xl font-black text-white">{estadisticas.total_triajes ?? 0}</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-2xl border border-amber-500/20">
                    <span className="text-xs text-amber-400 font-bold uppercase tracking-wider block mb-1">En Espera</span>
                    <p className="text-2xl font-black text-amber-400">{estadisticas.en_espera ?? 0}</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-2xl border border-rose-500/20">
                    <span className="text-xs text-rose-400 font-bold uppercase tracking-wider block mb-1">Urgentes</span>
                    <p className="text-2xl font-black text-rose-400">{estadisticas.casos_rojo_urgente ?? 0}</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-2xl border border-emerald-500/20">
                    <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider block mb-1">Revisados</span>
                    <p className="text-2xl font-black text-emerald-400">{estadisticas.casos_revisados ?? 0}</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-2xl border border-cyan-500/20">
                    <span className="text-xs text-cyan-400 font-bold uppercase tracking-wider block mb-1">Tiempo. Promedio</span>
                    <p className="text-2xl font-black text-cyan-400">{estadisticas.tiempo_promedio_atencion_min ?? 0}min</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-2xl border border-indigo-500/20">
                    <span className="text-xs text-indigo-400 font-bold uppercase tracking-wider block mb-1">Médicos</span>
                    <p className="text-2xl font-black text-indigo-400">{estadisticas.medicos_activos ?? 0}</p>
                  </div>
                </div>
              </div>

              {/* Tarjeta 2: Ocupación de Personal Médico */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl">
                <h3 className="text-sm font-bold text-white mb-5 flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-400" />
                  Ocupación de Personal Médico
                </h3>
                {(() => {
                  const activos = estadisticas.medicos_activos ?? 0;
                  const total = estadisticas.total_medicos ?? activos;
                  const inactivos = Math.max(0, total - activos);
                  const pActivos = total > 0 ? Math.round((activos / total) * 100) : 0;
                  const pInactivos = total > 0 ? Math.round((inactivos / total) * 100) : 0;

                  return (
                    <div className="space-y-4">
                      <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex shadow-inner">
                        <div style={{ width: `${pActivos}%` }} className="h-full bg-indigo-500"></div>
                        <div style={{ width: `${pInactivos}%` }} className="h-full bg-slate-600"></div>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded bg-indigo-500"></div>
                          <span className="text-slate-300">En Guardia ({pActivos}%)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded bg-slate-600"></div>
                          <span className="text-slate-500">Inactivos ({pInactivos}%)</span>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>

            </div>

            {/* 2. Columna Central (Distribución y Médicos en Guardia) */}
            <div className="lg:col-span-4 flex flex-col gap-6">

              {/* Tarjeta 1: Gráfico Donut de Triage */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex flex-col h-[320px]">
                <h3 className="text-sm font-bold text-white mb-2 flex items-center justify-between">
                  <span>Gravedad de Pacientes</span>
                  <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full">Hoy</span>
                </h3>

                {(() => {
                  const rojo = estadisticas.criticos_rojo ?? 0;
                  const amarillo = estadisticas.moderados_amarillo ?? 0;
                  const verde = estadisticas.leves_verde ?? 0;
                  const total = rojo + amarillo + verde || 1;

                  const pRojo = Math.round((rojo / total) * 100);
                  const pAmarillo = Math.round((amarillo / total) * 100);
                  const pVerde = Math.round((verde / total) * 100);

                  const degRojo = (pRojo / 100) * 360;
                  const degAmarillo = degRojo + ((pAmarillo / 100) * 360);

                  return (
                    <div className="flex items-center flex-1">
                      <div className="flex-1 flex flex-col gap-3 text-xs">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                          <span className="text-slate-300 font-bold">{rojo} Rojos</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                          <span className="text-slate-300 font-bold">{amarillo} Amarillos</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                          <span className="text-slate-300 font-bold">{verde} Verdes</span>
                        </div>
                      </div>

                      <div className="relative w-28 h-28 shrink-0 flex items-center justify-center rounded-full ml-4"
                        style={{
                          background: `conic-gradient(from 0deg, #f43f5e 0deg ${degRojo}deg, #f59e0b ${degRojo}deg ${degAmarillo}deg, #10b981 ${degAmarillo}deg 360deg)`
                        }}>
                        <div className="w-20 h-20 bg-slate-900 rounded-full flex flex-col items-center justify-center shadow-inner">
                          <span className="text-xl font-black text-white">{total === 1 && rojo === 0 && amarillo === 0 && verde === 0 ? 0 : total}</span>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Tarjeta 2: Médicos en Guardia (Lista) */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex-1">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Stethoscope className="w-5 h-5 text-indigo-400" />
                  Médicos en Guardia
                </h3>
                <div className="space-y-3 overflow-y-auto max-h-60 pr-2 custom-scrollbar">
                  {medicos.filter(m => m.esta_activo).length === 0 ? (
                    <div className="text-xs text-slate-500 text-center py-4">No hay médicos activos</div>
                  ) : (
                    medicos.filter(m => m.esta_activo).map(medico => (
                      <div key={medico.id} className="flex items-center justify-between p-3 bg-slate-950 rounded-2xl border border-slate-800/50">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs uppercase shrink-0">
                            {(medico.nombre_completo || medico.full_name || 'MD').substring(0, 2)}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-200 line-clamp-1">{medico.nombre_completo || medico.full_name}</p>
                            <p className="text-xs text-slate-500 line-clamp-1">{medico.especialidad || medico.specialty}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg text-[10px] font-bold shrink-0">
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
                          Activo
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>

            {/* 3. Columna Derecha (Perfil y Auditoría Reciente) */}
            <div className="lg:col-span-3 flex flex-col gap-6">

              {/* Tarjeta 1: Perfil Admin */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex flex-col items-center text-center">
                <div className="w-20 h-20 bg-slate-800 rounded-full border-4 border-slate-950 shadow-xl mb-4 flex items-center justify-center text-slate-400 overflow-hidden">
                  <User className="w-10 h-10" />
                </div>
                <h3 className="font-bold text-white">{usuarioActual?.nombre || 'Admin Central'}</h3>
                <p className="text-xs text-slate-500 mb-4">{usuarioActual?.rol || 'Administrador'}</p>
                <div className="flex items-center justify-between w-full border-t border-slate-800 pt-4 px-2">
                  <div className="text-center">
                    <Star className="w-4 h-4 text-indigo-400 mx-auto mb-1" />
                    <span className="text-xs font-bold text-slate-300">Nivel 1</span>
                  </div>
                  <div className="text-center">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                    <span className="text-xs font-bold text-slate-300">Acceso Total</span>
                  </div>
                </div>
              </div>

              {/* Tarjeta 2: Actividad Reciente */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex-1 flex flex-col">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center justify-between">
                  Actividad Reciente
                  <button onClick={() => setPestanaActiva('auditoria')} className="text-[10px] bg-teal-500/20 text-teal-400 px-2 py-1 rounded-lg hover:bg-teal-500/30 transition">
                    Ver Más
                  </button>
                </h3>
                <div className="space-y-4 flex-1">
                  {auditorias.slice(0, 4).map(log => (
                    <div key={log.id} className="flex gap-3">
                      <div className="mt-1 shrink-0">
                        <FileText className="w-4 h-4 text-slate-500" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold text-slate-300 truncate" title={log.accion.replace(/_/g, ' ')}>
                          {log.accion.replace(/_/g, ' ')}
                        </p>
                        <p className="text-[10px] text-slate-500 truncate" title={log.recurso_id || log.usuario_id}>
                          {log.recurso_id || log.usuario_id}
                        </p>
                        <p className="text-[10px] text-slate-600 mt-0.5">
                          {new Date(log.fecha_hora).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                  {auditorias.length === 0 && (
                    <div className="text-xs text-slate-500 text-center py-4">No hay actividad reciente</div>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* CONTENIDO DE PESTAÑA: GESTIÓN DE PERSONAL MÉDICO Y TURNOS */}
        {pestanaActiva === 'medicos' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
            {/* Formulario de Alta */}
            <div className="lg:col-span-4 bg-slate-900 border border-slate-800 p-6 rounded-3xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-indigo-400" />
                Registrar Profesional y Asignar Turno
              </h3>

              {mensajeExito && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" /> {mensajeExito}
                </div>
              )}

              <form onSubmit={registrarMedico} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 mb-1 font-semibold">Nombre Completo</label>
                  <input
                    type="text"
                    required
                    value={nuevoMedico.nombre_completo}
                    onChange={(e) => setNuevoMedico({ ...nuevoMedico, nombre_completo: e.target.value })}
                    placeholder="Ej. Dra. Valeria Justiniano"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1 font-semibold">Correo Electrónico</label>
                  <input
                    type="email"
                    required
                    value={nuevoMedico.correo}
                    onChange={(e) => setNuevoMedico({ ...nuevoMedico, correo: e.target.value })}
                    placeholder="valeria.justiniano@medisinc.bo"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1 font-semibold">Contraseña Temporal</label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={nuevoMedico.password}
                    onChange={(e) => setNuevoMedico({ ...nuevoMedico, password: e.target.value })}
                    placeholder="••••••••"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1 font-semibold">Especialidad Asignada</label>
                  <select
                    value={nuevoMedico.especialidad}
                    onChange={(e) => setNuevoMedico({ ...nuevoMedico, especialidad: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    {ESPECIALIDADES_DISPONIBLES.map((esp) => (
                      <option key={esp} value={esp}>
                        {esp}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1 font-semibold">Turno de Guardia</label>
                    <select
                      value={nuevoMedico.turno_asignado}
                      onChange={(e) => setNuevoMedico({ ...nuevoMedico, turno_asignado: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="MANANA">Mañana (07-15h)</option>
                      <option value="TARDE_NOCHE">Tarde/Noche (15-23h)</option>
                      <option value="MADRUGADA">Madrugada (23-07h)</option>
                      <option value="TODOS">Guardia Completa 24h</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1 font-semibold">Rol Asignado</label>
                    <select
                      value={nuevoMedico.rol}
                      onChange={(e) => setNuevoMedico({ ...nuevoMedico, rol: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="MEDICO">MEDICO</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={creandoMedico}
                  className="w-full mt-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition shadow-lg shadow-indigo-900/30 cursor-pointer"
                >
                  {creandoMedico ? 'Guardando...' : 'Crear Cuenta Médica'}
                </button>
              </form>
            </div>

            {/* Tabla de Médicos con Edición de Turnos y Especialidad */}
            <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <span className="font-bold text-xs uppercase text-slate-400">
                  Róster de Facultativos y Turnos de Guardia
                </span>
                <button
                  onClick={cargarDatosAdmin}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Actualizar</span>
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">Profesional</th>
                      <th className="p-3">Especialidad</th>
                      <th className="p-3">Turno de Guardia</th>
                      <th className="p-3">Estado</th>
                      <th className="p-3 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {medicos.map((m) => {
                      const estaEditando = medicoEnEdicion?.id === m.id;
                      const turnoInfo = TURNOS_DISPONIBLES.find(
                        (t) => t.valor === (m.turno_asignado || m.assigned_shift || 'TODOS')
                      ) || TURNOS_DISPONIBLES[3];

                      const esActivo = m.esta_activo !== false && m.is_active !== false;

                      return (
                        <tr key={m.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-3">
                            <p className="font-bold text-white">{m.nombre_completo || m.full_name}</p>
                            <p className="text-[11px] text-slate-400">{m.correo || m.email}</p>
                          </td>

                          <td className="p-3">
                            {estaEditando ? (
                              <select
                                value={medicoEnEdicion.especialidad}
                                onChange={(e) =>
                                  setMedicoEnEdicion({ ...medicoEnEdicion, especialidad: e.target.value })
                                }
                                className="bg-slate-950 border border-indigo-500 rounded-lg p-1.5 text-xs text-white"
                              >
                                {ESPECIALIDADES_DISPONIBLES.map((esp) => (
                                  <option key={esp} value={esp}>
                                    {esp}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <span className="font-medium text-slate-200">
                                {m.especialidad || m.specialty || 'Medicina General'}
                              </span>
                            )}
                          </td>

                          <td className="p-3">
                            {estaEditando ? (
                              <select
                                value={medicoEnEdicion.turno_asignado}
                                onChange={(e) =>
                                  setMedicoEnEdicion({ ...medicoEnEdicion, turno_asignado: e.target.value })
                                }
                                className="bg-slate-950 border border-indigo-500 rounded-lg p-1.5 text-xs text-white"
                              >
                                <option value="MANANA">Mañana (07-15h)</option>
                                <option value="TARDE_NOCHE">Tarde/Noche (15-23h)</option>
                                <option value="MADRUGADA">Madrugada (23-07h)</option>
                                <option value="TODOS">Guardia Completa 24h</option>
                              </select>
                            ) : (
                              <span
                                className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${turnoInfo.color}`}
                              >
                                <span>{turnoInfo.etiqueta}</span>
                              </span>
                            )}
                          </td>

                          <td className="p-3">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition ${esActivo
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                }`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${esActivo ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                              <span>{esActivo ? 'Activo' : 'Inactivo'}</span>
                            </span>
                          </td>

                          <td className="p-3 text-right">
                            {estaEditando ? (
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  onClick={() => guardarCambiosMedico(m.id)}
                                  disabled={guardandoEdicion}
                                  className="p-1.5 bg-emerald-500 text-slate-950 rounded-lg hover:bg-emerald-400 transition cursor-pointer"
                                  title="Guardar cambios"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => setMedicoEnEdicion(null)}
                                  className="p-1.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition cursor-pointer"
                                  title="Cancelar"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() =>
                                  setMedicoEnEdicion({
                                    id: m.id,
                                    nombre_completo: m.nombre_completo || m.full_name,
                                    especialidad: m.especialidad || m.specialty || 'Medicina General',
                                    turno_asignado: m.turno_asignado || m.assigned_shift || 'TODOS',
                                    rol: m.rol || m.role || 'MEDICO',
                                    esta_activo: esActivo,
                                  })
                                }
                                className="p-1.5 bg-slate-800 text-slate-300 hover:text-white rounded-lg hover:bg-slate-700 transition cursor-pointer"
                                title="Editar turno y especialidad"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* CONTENIDO DE PESTAÑA: BITÁCORA DE AUDITORÍA */}
        {pestanaActiva === 'auditoria' && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-4 border-b border-slate-800 font-bold text-xs uppercase text-slate-400">
              Registros Inalterables de Auditoría Médica
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">Fecha y Hora</th>
                    <th className="p-3">Acción Registrada</th>
                    <th className="p-3">Usuario / Médico</th>
                    <th className="p-3">IP Origen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {auditorias.map((a, idx) => (
                    <tr key={a.id || idx} className="hover:bg-slate-800/40">
                      <td className="p-3 text-slate-400">{new Date(a.fecha_hora || a.timestamp).toLocaleString()}</td>
                      <td className="p-3 font-semibold text-teal-400">{a.accion || a.action}</td>
                      <td className="p-3 text-slate-300 font-mono">{a.usuario_id || a.user_id}</td>
                      <td className="p-3 text-slate-400 font-mono">{a.direccion_ip || a.ip_address}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* CONTENIDO DE PESTAÑA: CALENDARIO / AGENDA */}
        {pestanaActiva === 'calendario' && (
          <div className="animate-fade-in space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
              <div className="flex flex-col lg:flex-row gap-8">

                {/* Calendario UI */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <CalendarIcon className="w-6 h-6 text-teal-400" />
                      {fechaCalendario.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }).replace(/^\w/, c => c.toUpperCase())}
                    </h2>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setFechaCalendario(new Date(fechaCalendario.getFullYear(), fechaCalendario.getMonth() - 1, 1))}
                        className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        <ChevronLeft className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => {
                          setFechaCalendario(new Date());
                          setDiaSeleccionado(new Date().getDate());
                        }}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 transition"
                      >
                        Hoy
                      </button>
                      <button
                        onClick={() => setFechaCalendario(new Date(fechaCalendario.getFullYear(), fechaCalendario.getMonth() + 1, 1))}
                        className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold text-slate-500 mb-2">
                    <div>Dom</div><div>Lun</div><div>Mar</div><div>Mié</div><div>Jue</div><div>Vie</div><div>Sáb</div>
                  </div>

                  <div className="grid grid-cols-7 gap-2">
                    {(() => {
                      const year = fechaCalendario.getFullYear();
                      const month = fechaCalendario.getMonth();
                      const daysInMonth = new Date(year, month + 1, 0).getDate();
                      const firstDayIndex = new Date(year, month, 1).getDay();

                      const blanks = Array.from({ length: firstDayIndex }).map((_, i) => (
                        <div key={`blank-${i}`} className="p-3 bg-slate-950/20 rounded-2xl border border-transparent"></div>
                      ));

                      const days = Array.from({ length: daysInMonth }).map((_, i) => {
                        const dayNumber = i + 1;
                        const hasAppointments = citasReales[dayNumber] && citasReales[dayNumber].length > 0;
                        const isSelected = diaSeleccionado === dayNumber;
                        const isToday = dayNumber === new Date().getDate() && month === new Date().getMonth() && year === new Date().getFullYear();

                        return (
                          <button
                            key={dayNumber}
                            onClick={() => setDiaSeleccionado(dayNumber)}
                            className={`p-3 rounded-2xl border transition relative flex flex-col items-center justify-center min-h-[4rem] cursor-pointer ${isSelected
                              ? 'bg-teal-500 text-slate-950 border-teal-400 font-bold shadow-lg shadow-teal-500/20'
                              : isToday
                                ? 'bg-slate-800 text-white border-teal-500/50 font-bold'
                                : 'bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800'
                              }`}
                          >
                            <span>{dayNumber}</span>
                            {hasAppointments && (
                              <div className="absolute bottom-2 flex gap-1">
                                {citasReales[dayNumber].slice(0, 3).map((_, idx) => (
                                  <div key={idx} className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-slate-950' : 'bg-teal-400'}`}></div>
                                ))}
                                {citasReales[dayNumber].length > 3 && (
                                  <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-slate-950' : 'bg-amber-400'}`}></div>
                                )}
                              </div>
                            )}
                          </button>
                        );
                      });

                      return [...blanks, ...days];
                    })()}
                  </div>
                </div>

                {/* Detalle de Citas del Día */}
                <div className="lg:w-[350px] bg-slate-950 rounded-3xl p-6 border border-slate-800 flex flex-col h-[550px]">
                  <h3 className="text-sm font-bold text-white mb-4 border-b border-slate-800 pb-3">
                    Agenda del {diaSeleccionado} de {fechaCalendario.toLocaleDateString('es-ES', { month: 'long' })}
                  </h3>

                  {citaEditando ? (
                    <form onSubmit={guardarCambiosCita} className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                      <div className="bg-slate-900 p-4 rounded-2xl border border-teal-500/50">
                        <h4 className="text-xs font-bold text-teal-400 mb-3">Re-agendar Cita</h4>
                        <div className="mb-3">
                          <label className="text-[10px] text-slate-400 block mb-1">Médico Asignado</label>
                          <select
                            value={datosEdicionCita.medico_asignado_id || ''}
                            onChange={(e) => setDatosEdicionCita({ ...datosEdicionCita, medico_asignado_id: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white outline-none"
                          >
                            <option value="">-- Sin Asignar --</option>
                            {medicos.map(m => (
                              <option key={m.id} value={m.id}>
                                {m.nombre_completo || m.full_name} ({m.especialidad || m.specialty || 'Medicina General'})
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="mb-4">
                          <label className="text-[10px] text-slate-400 block mb-1">Nueva Fecha y Hora</label>
                          <input
                            type="datetime-local"
                            value={datosEdicionCita.fecha_cita || ''}
                            onChange={(e) => setDatosEdicionCita({ ...datosEdicionCita, fecha_cita: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white outline-none"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button type="submit" className="flex-1 bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold py-2 rounded-lg transition">Guardar</button>
                          <button type="button" onClick={() => setCitaEditando(null)} className="flex-1 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold py-2 rounded-lg transition">Cancelar</button>
                        </div>
                      </div>
                    </form>
                  ) : (
                    <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                      {citasReales[diaSeleccionado] && citasReales[diaSeleccionado].length > 0 ? (
                        citasReales[diaSeleccionado].map((cita) => (
                          <div
                            key={cita.id}
                            onClick={() => {
                              setCitaEditando(cita);
                              const fechaDate = new Date(cita.fecha_original);
                              const offset = fechaDate.getTimezoneOffset() * 60000;
                              const localISOTime = (new Date(fechaDate - offset)).toISOString().slice(0, -1);
                              setDatosEdicionCita({
                                medico_asignado_id: cita.medico_id || '',
                                fecha_cita: localISOTime.substring(0, 16)
                              });
                            }}
                            className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl relative overflow-hidden group hover:border-teal-500/50 transition cursor-pointer"
                          >
                            <div className={`absolute top-0 left-0 w-1 h-full ${cita.estado === 'REVISADO' ? 'bg-teal-500' : cita.estado === 'EN_CONSULTA' ? 'bg-blue-500' : 'bg-amber-500'}`}></div>
                            <div className="pl-3">
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-black text-white">{cita.hora}</span>
                                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md ${cita.estado === 'REVISADO' ? 'bg-teal-500/20 text-teal-400' : cita.estado === 'EN_CONSULTA' ? 'bg-blue-500/20 text-blue-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                  {cita.estado === 'RECIBIDO' ? 'PENDIENTE' : cita.estado}
                                </span>
                              </div>
                              <p className="text-[11px] font-bold text-slate-300 mt-2">{cita.medico}</p>
                              <p className="text-[10px] text-slate-500 mb-2">{cita.especialidad}</p>

                              <div className="flex items-center gap-1.5 text-[10px] bg-slate-950 p-1.5 rounded-lg border border-slate-800">
                                <User className="w-3 h-3 text-slate-400" />
                                <span className="text-slate-300">{cita.paciente}</span>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
                          <CalendarIcon className="w-10 h-10 mb-3 opacity-20" />
                          <p className="text-xs font-bold">Día Libre</p>
                          <p className="text-[10px] mt-1 px-4">No hay citas programadas para ninguno de los médicos en esta fecha.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PanelAdministrador;
