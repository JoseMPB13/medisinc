/**
 * Portal del Administrador y Gobernanza del Centro de Salud (MediSinc-IA).
 * Proporciona métricas cuantitativas consolidadas, gestión de profesionales médicos
 * y visor de la bitácora inalterable de auditoría (registros_auditoria).
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
} from 'lucide-react';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';
import { servicioAdmin } from '../servicios/servicioAdmin';

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
  });
  const [creandoMedico, setCreandoMedico] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(null);

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
      setMensajeExito('Médico registrado exitosamente.');
      setNuevoMedico({
        nombre_completo: '',
        correo: '',
        password: '',
        especialidad: 'Medicina General',
        rol: 'MEDICO',
      });
      cargarDatosAdmin();
    } catch (err) {
      alert('Error al registrar médico: ' + (err.detail || err.message));
    } finally {
      setCreandoMedico(false);
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
              className="p-2 text-slate-400 hover:text-rose-400 rounded-xl bg-slate-800 transition"
              title="Cerrar Sesión"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Contenedor Principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 space-y-6">
        {/* Pestañas de Navegación */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setPestanaActiva('resumen')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
              pestanaActiva === 'resumen'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/30'
                : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            Métricas Globales
          </button>
          <button
            onClick={() => setPestanaActiva('medicos')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
              pestanaActiva === 'medicos'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/30'
                : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            Personal Médico
          </button>
          <button
            onClick={() => setPestanaActiva('auditoria')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
              pestanaActiva === 'auditoria'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/30'
                : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            Bitácora de Auditoría
          </button>
        </div>

        {/* CONTENIDO DE PESTAÑA: MÉTRICAS GLOBALES */}
        {pestanaActiva === 'resumen' && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs font-semibold text-slate-400 uppercase">Total Pre-Triajes</span>
                <div className="text-3xl font-black text-white mt-2">{estadisticas.total_triajes}</div>
                <p className="text-[11px] text-slate-500 mt-1">Pacientes registrados</p>
              </div>

              <div className="bg-slate-900 border border-rose-500/30 p-5 rounded-2xl bg-rose-950/10">
                <span className="text-xs font-semibold text-rose-400 uppercase">Emergencias Críticas</span>
                <div className="text-3xl font-black text-rose-400 mt-2">{estadisticas.casos_rojo_urgente}</div>
                <p className="text-[11px] text-rose-300/70 mt-1">Casos clasificados en Rojo</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs font-semibold text-emerald-400 uppercase">Atenciones Completadas</span>
                <div className="text-3xl font-black text-emerald-400 mt-2">{estadisticas.casos_revisados}</div>
                <p className="text-[11px] text-slate-500 mt-1">Dados de alta por médico</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs font-semibold text-indigo-400 uppercase">Médicos Activos</span>
                <div className="text-3xl font-black text-white mt-2">{estadisticas.medicos_activos}</div>
                <p className="text-[11px] text-slate-500 mt-1">Personal en guardia</p>
              </div>
            </div>
          </div>
        )}

        {/* CONTENIDO DE PESTAÑA: GESTIÓN DE PERSONAL MÉDICO */}
        {pestanaActiva === 'medicos' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
            {/* Formulario de Alta */}
            <div className="lg:col-span-5 bg-slate-900 border border-slate-800 p-6 rounded-3xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-indigo-400" />
                Registrar Nuevo Profesional
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

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1 font-semibold">Especialidad</label>
                    <input
                      type="text"
                      value={nuevoMedico.especialidad}
                      onChange={(e) => setNuevoMedico({ ...nuevoMedico, especialidad: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    />
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
                  className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition shadow-lg shadow-indigo-900/30"
                >
                  {creandoMedico ? 'Guardando...' : 'Crear Cuenta Médica'}
                </button>
              </form>
            </div>

            {/* Tabla de Médicos */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-slate-800 font-bold text-xs uppercase text-slate-400">
                Personal Registrado en el Sistema
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">Nombre</th>
                      <th className="p-3">Correo</th>
                      <th className="p-3">Especialidad</th>
                      <th className="p-3">Rol</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {medicos.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-800/40">
                        <td className="p-3 font-semibold text-white">{m.nombre_completo || m.full_name}</td>
                        <td className="p-3 text-slate-300">{m.correo || m.email}</td>
                        <td className="p-3 text-slate-400">{m.especialidad || m.specialty}</td>
                        <td className="p-3">
                          <span className="bg-slate-800 px-2 py-0.5 rounded text-[10px] font-bold text-teal-400">
                            {m.rol || m.role}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* CONTENIDO DE PESTAÑA: BITÁCORA DE AUDITORÍA */}
        {pestanaActiva === 'auditoria' && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl animate-fade-in">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-xs uppercase text-slate-300">Trazabilidad Inalterable de Auditoría</span>
              </div>
              <span className="text-[11px] text-slate-500">Últimos 50 eventos</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">Acción Ejecutada</th>
                    <th className="p-3">Recurso Afectado</th>
                    <th className="p-3">IP Origen</th>
                    <th className="p-3">Fecha y Hora (UTC)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {auditorias.map((a, idx) => (
                    <tr key={a.id || idx} className="hover:bg-slate-800/40">
                      <td className="p-3 font-semibold text-emerald-400">{a.accion || a.action}</td>
                      <td className="p-3 text-slate-300">{a.recurso_id || a.resource_id || '-'}</td>
                      <td className="p-3 text-slate-400">{a.direccion_ip || a.ip_address || '127.0.0.1'}</td>
                      <td className="p-3 text-slate-500 text-[11px]">{a.fecha_hora || a.timestamp}</td>
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

export const AdminDashboard = PanelAdministrador;
export default PanelAdministrador;
