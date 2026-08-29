/**
 * Portal del Administrador y Gobernanza del Centro de Salud (MediSinc-IA).
 * Proporciona métricas cuantitativas consolidadas, gestión de profesionales médicos
 * con asignación de turnos de guardia y especialidades, y visor de auditoría.
 */

import React, { useState, useEffect } from 'react';
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
  const [pestanaActiva, setPestanaActiva] = useState('resumen'); // 'resumen' | 'medicos' | 'auditoria'
  const [cargando, setCargando] = useState(true);

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
      const [statsRes, medicosRes, auditRes] = await Promise.allSettled([
        servicioAdmin.obtenerEstadisticasAdmin(),
        servicioAdmin.listarMedicos(),
        servicioAdmin.listarRegistrosAuditoria(50),
      ]);

      if (statsRes.status === 'fulfilled') setEstadisticas(statsRes.value);
      if (medicosRes.status === 'fulfilled') setMedicos(medicosRes.value || []);
      if (auditRes.status === 'fulfilled') setAuditorias(auditRes.value || []);
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

  const toggleEstadoActivo = async (medico) => {
    try {
      const nuevoEstado = !(medico.esta_activo ?? medico.is_active);
      await servicioAdmin.actualizarMedico(medico.id, {
        esta_activo: nuevoEstado,
      });
      cargarDatosAdmin();
    } catch (err) {
      alert('Error al cambiar estado del médico: ' + (err.detail || err.message));
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
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${
              pestanaActiva === 'resumen'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Métricas Clínicas</span>
          </button>

          <button
            onClick={() => setPestanaActiva('medicos')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${
              pestanaActiva === 'medicos'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Gestión de Médicos y Turnos ({medicos.length})</span>
          </button>

          <button
            onClick={() => setPestanaActiva('auditoria')}
            className={`py-3.5 text-xs font-bold border-b-2 flex items-center gap-2 transition cursor-pointer ${
              pestanaActiva === 'auditoria'
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
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl">
                <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1">
                  Total Pre-Triajes
                </span>
                <p className="text-3xl font-black text-white">
                  {estadisticas.total_triajes ?? estadisticas.total_patients ?? 0}
                </p>
              </div>

              <div className="bg-slate-900 border border-rose-500/30 p-5 rounded-3xl">
                <span className="text-xs text-rose-400 font-bold uppercase tracking-wider block mb-1">
                  Casos Rojos (Urgentes)
                </span>
                <p className="text-3xl font-black text-rose-400">
                  {estadisticas.casos_rojo_urgente ?? estadisticas.urgent_red_cases ?? 0}
                </p>
              </div>

              <div className="bg-slate-900 border border-emerald-500/30 p-5 rounded-3xl">
                <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider block mb-1">
                  Pacientes Revisados
                </span>
                <p className="text-3xl font-black text-emerald-400">
                  {estadisticas.casos_revisados ?? estadisticas.reviewed_cases ?? 0}
                </p>
              </div>

              <div className="bg-slate-900 border border-indigo-500/30 p-5 rounded-3xl">
                <span className="text-xs text-indigo-400 font-bold uppercase tracking-wider block mb-1">
                  Médicos en Guardia
                </span>
                <p className="text-3xl font-black text-indigo-400">
                  {estadisticas.medicos_activos ?? estadisticas.active_doctors ?? 0}
                </p>
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
                            <button
                              onClick={() => toggleEstadoActivo(m)}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition cursor-pointer ${
                                esActivo
                                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              }`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${esActivo ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                              <span>{esActivo ? 'Activo' : 'Inactivo'}</span>
                            </button>
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
      </main>
    </div>
  );
};

export default PanelAdministrador;
