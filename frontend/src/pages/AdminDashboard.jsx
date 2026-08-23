import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Users,
  UserPlus,
  FileText,
  Activity,
  LogOut,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Eye,
  Shield,
  Edit2,
  Lock,
  UserCheck,
  UserX,
  Stethoscope,
  Filter,
  ArrowUpDown,
  History,
  Terminal,
  Database
} from 'lucide-react';
import { getCurrentUser, logout } from '../services/authService';
import adminService from '../services/adminService';
import PatientDetailModal from '../components/doctor/PatientDetailModal';

/**
 * Portal del Administrador de MediSinc-IA (/admin/dashboard).
 * Proporciona:
 * 1. Métricas globales cuantitativas de atención en tiempo real.
 * 2. CRUD completo del personal médico y roles (DOCTOR / ADMIN).
 * 3. Historial clínico global de pacientes actuales y anteriores.
 * 4. Visor de la bitácora inalterable de auditoría (AUDIT_LOG).
 */
function AdminDashboard() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();

  const [activeTab, setActiveTab] = useState('doctors'); // 'doctors' | 'history' | 'audit'
  const [loading, setLoading] = useState(true);

  // Estados de Métricas
  const [stats, setStats] = useState({
    total_triages: 0,
    urgent_red_cases: 0,
    reviewed_cases: 0,
    active_doctors: 0,
    average_attention_time_min: 0.0
  });

  // Estados de Personal Médico (CRUD)
  const [doctors, setDoctors] = useState([]);
  const [doctorSearch, setDoctorSearch] = useState('');
  const [showCreateDocModal, setShowCreateDocModal] = useState(false);
  const [editingDoctor, setEditingDoctor] = useState(null);
  const [newDoctorData, setNewDoctorData] = useState({
    full_name: '',
    email: '',
    specialty: '',
    password: '',
    role: 'DOCTOR'
  });

  // Estados de Historial de Pacientes
  const [patientHistory, setPatientHistory] = useState([]);
  const [historySearch, setHistorySearch] = useState('');
  const [historyStatusFilter, setHistoryStatusFilter] = useState('');
  const [historyPriorityFilter, setHistoryPriorityFilter] = useState('');
  const [selectedPatientForDetail, setSelectedPatientForDetail] = useState(null);

  // Estados de Bitácora AUDIT_LOG
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditActionFilter, setAuditActionFilter] = useState('');

  const loadAllAdminData = async () => {
    setLoading(true);
    try {
      // 1. Cargar Estadísticas
      const statsData = await adminService.getStats();
      setStats(statsData || {});

      // 2. Cargar Doctores
      const docsData = await adminService.getDoctors();
      setDoctors(docsData || []);

      // 3. Cargar Historial
      const historyData = await adminService.getPatientHistory();
      setPatientHistory(historyData.records || []);

      // 4. Cargar Logs de Auditoría
      const logsData = await adminService.getAuditLogs();
      setAuditLogs(logsData || []);
    } catch (err) {
      console.error('Error cargando datos del portal de administración:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllAdminData();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Manejadores CRUD Doctores
  const handleCreateDoctor = async (e) => {
    e.preventDefault();
    try {
      await adminService.createDoctor(newDoctorData);
      alert('✓ Profesional médico registrado exitosamente en el sistema.');
      setShowCreateDocModal(false);
      setNewDoctorData({
        full_name: '',
        email: '',
        specialty: '',
        password: '',
        role: 'DOCTOR'
      });
      loadAllAdminData();
    } catch (err) {
      console.error('Error creando doctor:', err);
      alert('Error creando médico. Verifique que los campos sean válidos.');
    }
  };

  const handleToggleDoctorStatus = async (doctor) => {
    try {
      const newStatus = !doctor.is_active;
      await adminService.updateDoctor(doctor.id, { is_active: newStatus });
      alert(`✓ Estado del profesional actualizado a: ${newStatus ? 'ACTIVO' : 'INACTIVO'}`);
      loadAllAdminData();
    } catch (err) {
      console.error('Error actualizando estado del doctor:', err);
      alert('Error actualizando estado del profesional.');
    }
  };

  const handleUpdateDoctor = async (e) => {
    e.preventDefault();
    if (!editingDoctor) return;
    try {
      await adminService.updateDoctor(editingDoctor.id, {
        full_name: editingDoctor.full_name,
        specialty: editingDoctor.specialty,
        role: editingDoctor.role
      });
      alert('✓ Perfil del médico actualizado correctamente.');
      setEditingDoctor(null);
      loadAllAdminData();
    } catch (err) {
      console.error('Error actualizando doctor:', err);
      alert('Error actualizando perfil.');
    }
  };

  // Filtrado en vivo de personal médico
  const filteredDoctors = doctors.filter((doc) => {
    const term = doctorSearch.toLowerCase();
    return (
      doc.full_name?.toLowerCase().includes(term) ||
      doc.email?.toLowerCase().includes(term) ||
      doc.specialty?.toLowerCase().includes(term)
    );
  });

  // Filtrado en vivo de historial clínico
  const filteredHistory = patientHistory.filter((rec) => {
    const term = historySearch.toLowerCase();
    const matchesSearch =
      rec.patient_name?.toLowerCase().includes(term) ||
      rec.access_code?.toLowerCase().includes(term) ||
      rec.raw_symptoms?.toLowerCase().includes(term);
    const matchesStatus = !historyStatusFilter || rec.status === historyStatusFilter;
    const matchesPriority = !historyPriorityFilter || rec.final_priority === historyPriorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Filtrado en vivo de auditoría
  const filteredAuditLogs = auditLogs.filter((log) => {
    return !auditActionFilter || log.action === auditActionFilter;
  });

  const getPriorityStyle = (prio) => {
    if (prio === 'RED') return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    if (prio === 'YELLOW') return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500">
      {/* Barra de Navegación Superior */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-100">Portal de Administración</h1>
                <span className="text-xs px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-md border border-indigo-500/30 font-semibold">
                  MEDISINC ADMIN
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {currentUser?.full_name || 'Administrador Central'} ({currentUser?.email || 'admin@medisinc.bo'})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAllAdminData}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={handleLogout}
              className="py-2 px-3 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </header>

      {/* Contenedor Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 space-y-6">
        {/* Tarjetas de Métricas Estadísticas Globales */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-slate-100">{stats.total_triages}</span>
              <p className="text-[11px] text-slate-400">Total Triajes</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="p-3 bg-rose-500/10 rounded-xl text-rose-400">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-rose-400">{stats.urgent_red_cases}</span>
              <p className="text-[11px] text-slate-400">Casos Críticos (Rojo)</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-emerald-400">{stats.reviewed_cases}</span>
              <p className="text-[11px] text-slate-400">Atendidos</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="p-3 bg-sky-500/10 rounded-xl text-sky-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-sky-400">{stats.active_doctors}</span>
              <p className="text-[11px] text-slate-400">Médicos Habilitados</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3 col-span-2 md:col-span-1">
            <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-purple-300">{stats.average_attention_time_min}m</span>
              <p className="text-[11px] text-slate-400">Tiempo Promedio</p>
            </div>
          </div>
        </div>

        {/* Selector de Pestañas de Navegación */}
        <div className="flex border-b border-slate-800 gap-2">
          <button
            onClick={() => setActiveTab('doctors')}
            className={`py-3 px-5 text-xs font-bold rounded-t-xl transition flex items-center gap-2 border-b-2 ${
              activeTab === 'doctors'
                ? 'bg-slate-900 border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Gestión del Personal Médico (CRUD)</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`py-3 px-5 text-xs font-bold rounded-t-xl transition flex items-center gap-2 border-b-2 ${
              activeTab === 'history'
                ? 'bg-slate-900 border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Historial Clínico Integral ({patientHistory.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`py-3 px-5 text-xs font-bold rounded-t-xl transition flex items-center gap-2 border-b-2 ${
              activeTab === 'audit'
                ? 'bg-slate-900 border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Bitácora de Auditoría AUDIT_LOG ({auditLogs.length})</span>
          </button>
        </div>

        {/* PESTAÑA 1: GESTIÓN DE PERSONAL MÉDICO (CRUD) */}
        {activeTab === 'doctors' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                  Listado y Control de Cuentas Médicas
                </h2>
                <p className="text-xs text-slate-400">
                  Administra los roles de acceso institucional, credenciales y estados activos del personal.
                </p>
              </div>

              <div className="flex items-center gap-3 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Buscar médico..."
                    value={doctorSearch}
                    onChange={(e) => setDoctorSearch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl py-2 pl-9 pr-3 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <button
                  onClick={() => setShowCreateDocModal(true)}
                  className="py-2.5 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-bold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-indigo-500/20 transition shrink-0"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Nuevo Médico</span>
                </button>
              </div>
            </div>

            {/* Tabla de Doctores */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-3">Profesional</th>
                    <th className="py-3 px-3">Correo Institucional</th>
                    <th className="py-3 px-3">Especialidad / Matrícula</th>
                    <th className="py-3 px-3">Rol</th>
                    <th className="py-3 px-3">Estado</th>
                    <th className="py-3 px-3 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredDoctors.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-3 font-semibold text-slate-100 flex items-center gap-2">
                        <div className="p-1.5 bg-indigo-500/10 text-indigo-400 rounded-lg">
                          <Stethoscope className="w-3.5 h-3.5" />
                        </div>
                        <span>{doc.full_name}</span>
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-300">{doc.email}</td>
                      <td className="py-3 px-3 text-slate-300">{doc.specialty || 'No especificada'}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full font-bold text-[10px] border ${
                            doc.role === 'ADMIN'
                              ? 'bg-purple-500/20 text-purple-300 border-purple-500/30'
                              : 'bg-sky-500/20 text-sky-300 border-sky-500/30'
                          }`}
                        >
                          {doc.role}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                            doc.is_active
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {doc.is_active ? '● Activo' : '○ Inactivo'}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right space-x-2">
                        <button
                          onClick={() => setEditingDoctor(doc)}
                          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                          title="Editar Médico"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleToggleDoctorStatus(doc)}
                          className={`p-1.5 rounded-lg transition ${
                            doc.is_active
                              ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400'
                              : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400'
                          }`}
                          title={doc.is_active ? 'Desactivar Cuenta' : 'Activar Cuenta'}
                        >
                          {doc.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* PESTAÑA 2: HISTORIAL GLOBAL DE PACIENTES */}
        {activeTab === 'history' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                  Historial Clínico Integral de Triajes
                </h2>
                <p className="text-xs text-slate-400">
                  Visualiza pacientes actuales, pendientes y finalizados con búsqueda rápida y filtros.
                </p>
              </div>

              {/* Filtros de Historial */}
              <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-48">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Nombre o Código..."
                    value={historySearch}
                    onChange={(e) => setHistorySearch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl py-2 pl-9 pr-3 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <select
                  value={historyStatusFilter}
                  onChange={(e) => setHistoryStatusFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-700/80 rounded-xl py-2 px-3 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="">Estado: Todos</option>
                  <option value="RECEIVED">RECEIVED (Recibido)</option>
                  <option value="READY">READY (Evaluado IA)</option>
                  <option value="REVIEWED">REVIEWED (Atendido)</option>
                </select>

                <select
                  value={historyPriorityFilter}
                  onChange={(e) => setHistoryPriorityFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-700/80 rounded-xl py-2 px-3 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="">Prioridad: Todas</option>
                  <option value="RED">🔴 Rojo (Urgente)</option>
                  <option value="YELLOW">🟡 Amarillo (Prioritario)</option>
                  <option value="GREEN">🟢 Verde (No urgente)</option>
                </select>
              </div>
            </div>

            {/* Tabla de Historial Clínico */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-3">Código</th>
                    <th className="py-3 px-3">Paciente</th>
                    <th className="py-3 px-3">Edad/Género</th>
                    <th className="py-3 px-3">Síntoma Declarado</th>
                    <th className="py-3 px-3">Nivel Prioridad</th>
                    <th className="py-3 px-3">Estado</th>
                    <th className="py-3 px-3">Fecha y Hora</th>
                    <th className="py-3 px-3 text-right">Expediente</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredHistory.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-3 font-mono font-bold text-sky-400">{rec.access_code}</td>
                      <td className="py-3 px-3 font-semibold text-slate-100">{rec.patient_name}</td>
                      <td className="py-3 px-3 text-slate-400">
                        {rec.age} años • {rec.gender}
                      </td>
                      <td className="py-3 px-3 text-slate-300 max-w-xs truncate italic">"{rec.raw_symptoms}"</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] border ${getPriorityStyle(rec.final_priority)}`}>
                          {rec.final_priority || 'RED'}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-semibold text-[11px] ${
                            rec.status === 'REVIEWED' ? 'text-emerald-400' : 'text-amber-400'
                          }`}
                        >
                          {rec.status === 'REVIEWED' ? '✓ Atendido' : '● Pendiente'}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-400">
                        {rec.created_at ? new Date(rec.created_at).toLocaleString() : 'Reciente'}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => setSelectedPatientForDetail(rec)}
                          className="py-1.5 px-3 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 rounded-lg text-xs font-semibold flex items-center gap-1 ml-auto transition"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Ver</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* PESTAÑA 3: BITÁCORA INALTERABLE DE AUDITORÍA (AUDIT_LOG) */}
        {activeTab === 'audit' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-purple-400" /> Registro Inalterable de Seguridad (AUDIT_LOG)
                </h2>
                <p className="text-xs text-slate-400">
                  Trazabilidad cronológica de consultas de expedientes, accesos de médicos y modificaciones.
                </p>
              </div>

              <select
                value={auditActionFilter}
                onChange={(e) => setAuditActionFilter(e.target.value)}
                className="bg-slate-950 border border-slate-700/80 rounded-xl py-2 px-3 text-xs text-slate-200 focus:outline-none"
              >
                <option value="">Filtrar Acción: Todas</option>
                <option value="VIEW_PATIENT_DETAIL">VIEW_PATIENT_DETAIL</option>
                <option value="CONFIRM_MEDICAL_REVIEW">CONFIRM_MEDICAL_REVIEW</option>
                <option value="CREATE_DOCTOR">CREATE_DOCTOR</option>
                <option value="UPDATE_DOCTOR">UPDATE_DOCTOR</option>
                <option value="SYSTEM_STARTUP">SYSTEM_STARTUP</option>
              </select>
            </div>

            {/* Tabla de Logs */}
            <div className="overflow-x-auto font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Timestamp (UTC)</th>
                    <th className="py-2.5 px-3">Acción Registrada</th>
                    <th className="py-2.5 px-3">Recurso Afectado (ID)</th>
                    <th className="py-2.5 px-3">Dirección IP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredAuditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 text-purple-400">
                        {log.timestamp ? new Date(log.timestamp).toISOString() : 'Reciente'}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            log.action?.includes('REVIEW')
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : log.action?.includes('VIEW')
                              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                              : 'bg-purple-500/10 text-purple-300 border border-purple-500/20'
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 truncate max-w-xs">{log.resource_id || 'Global'}</td>
                      <td className="py-2.5 px-3 text-slate-400">{log.ip_address || '127.0.0.1'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* MODAL: REGISTRAR NUEVO MÉDICO */}
      {showCreateDocModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-indigo-400" /> Registrar Nuevo Profesional Médico
              </h3>
              <button onClick={() => setShowCreateDocModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDoctor} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Nombre Completo *</label>
                <input
                  type="text"
                  required
                  placeholder="Dr. Fernando Morales"
                  value={newDoctorData.full_name}
                  onChange={(e) => setNewDoctorData({ ...newDoctorData, full_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Correo Institucional (@medisinc.bo) *</label>
                <input
                  type="email"
                  required
                  placeholder="f.morales@medisinc.bo"
                  value={newDoctorData.email}
                  onChange={(e) => setNewDoctorData({ ...newDoctorData, email: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Especialidad o Matrícula Profesional *</label>
                <input
                  type="text"
                  required
                  placeholder="Emergencias y Cuidados Críticos"
                  value={newDoctorData.specialty}
                  onChange={(e) => setNewDoctorData({ ...newDoctorData, specialty: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Contraseña Inicial *</label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={newDoctorData.password}
                    onChange={(e) => setNewDoctorData({ ...newDoctorData, password: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Rol en el Sistema</label>
                  <select
                    value={newDoctorData.role}
                    onChange={(e) => setNewDoctorData({ ...newDoctorData, role: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none"
                  >
                    <option value="DOCTOR">DOCTOR (Médico)</option>
                    <option value="ADMIN">ADMIN (Director)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateDocModal(false)}
                  className="py-2 px-4 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="py-2 px-5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-md"
                >
                  Registrar Médico
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDITAR PERFIL DE MÉDICO */}
      {editingDoctor && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-indigo-400" /> Editar Perfil Médico
              </h3>
              <button onClick={() => setEditingDoctor(null)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateDoctor} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Nombre Completo</label>
                <input
                  type="text"
                  value={editingDoctor.full_name}
                  onChange={(e) => setEditingDoctor({ ...editingDoctor, full_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Especialidad</label>
                <input
                  type="text"
                  value={editingDoctor.specialty}
                  onChange={(e) => setEditingDoctor({ ...editingDoctor, specialty: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Rol</label>
                <select
                  value={editingDoctor.role}
                  onChange={(e) => setEditingDoctor({ ...editingDoctor, role: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none"
                >
                  <option value="DOCTOR">DOCTOR</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingDoctor(null)}
                  className="py-2 px-4 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="py-2 px-5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-md"
                >
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL DE EXPEDIENTE CLÍNICO PARA VISUALIZACIÓN DESDE HISTORIAL */}
      {selectedPatientForDetail && (
        <PatientDetailModal
          patientData={selectedPatientForDetail}
          onClose={() => setSelectedPatientForDetail(null)}
          onReviewComplete={loadAllAdminData}
        />
      )}
    </div>
  );
}

export default AdminDashboard;
