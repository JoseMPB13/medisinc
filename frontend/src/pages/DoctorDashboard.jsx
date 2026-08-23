import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { getCurrentUser, logout } from '../services/authService';
import PatientDetailModal from '../components/doctor/PatientDetailModal';
import {
  Stethoscope,
  LogOut,
  QrCode,
  Search,
  Users,
  AlertOctagon,
  CheckCircle2,
  Clock,
  RefreshCw,
  Eye,
  Camera,
  X,
  Loader2,
  Activity
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Vista de Dashboard para el Profesional Médico (/doctor/dashboard).
 * Presenta métricas rápidas, lista de espera ordenada automáticamente por nivel de urgencia,
 * buscador tripartito por QR, Código o CI, carga bajo demanda y modal de detalle clínico.
 */
function DoctorDashboard() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();

  const [metrics, setMetrics] = useState({ waiting_count: 0, reviewed_count: 0, total_red: 0, total_today: 0 });
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingPatientDetail, setLoadingPatientDetail] = useState(false);

  // Estados del Buscador Tripartito
  const [searchCode, setSearchCode] = useState('');
  const [searchCI, setSearchCI] = useState('');
  const [showQRScanner, setShowQRScanner] = useState(false);

  // Estado del Modal de Detalle
  const [selectedPatient, setSelectedPatient] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const resp = await axios.get(`${API_BASE_URL}/doctor/dashboard`);
      if (resp.data) {
        setMetrics(resp.data.metrics || {});
        setRecords(resp.data.records || []);
      }
    } catch (err) {
      console.error('Error cargando dashboard médico:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000); // Auto-refresh cada 10s
    return () => clearInterval(interval);
  }, []);

  // Carga bajo demanda del detalle del paciente con CI descifrado en memoria y auditoría
  const handleOpenPatientDetail = async (identifier) => {
    if (!identifier) return;
    setLoadingPatientDetail(true);
    try {
      const resp = await axios.get(`${API_BASE_URL}/doctor/patient/${identifier}`);
      if (resp.data) {
        setSelectedPatient(resp.data);
      }
    } catch (err) {
      console.error(`Error obteniendo detalle de paciente (${identifier}):`, err);
      alert(`No se pudo cargar el expediente para '${identifier}'. Verifique que el registro exista.`);
    } finally {
      setLoadingPatientDetail(false);
    }
  };

  // Inicializar escáner de Cámara QR html5-qrcode
  useEffect(() => {
    let scanner = null;
    if (showQRScanner) {
      scanner = new Html5QrcodeScanner(
        'qr-reader',
        { fps: 10, qrbox: { width: 250, height: 250 } },
        false
      );

      scanner.render(
        (decodedText) => {
          console.log('Código QR Escaneado:', decodedText);
          let codeToLookup = decodedText;
          try {
            const parsed = JSON.parse(decodedText);
            if (parsed.code) codeToLookup = parsed.code;
          } catch (e) {}

          setShowQRScanner(false);
          scanner.clear();
          handleOpenPatientDetail(codeToLookup);
        },
        (error) => {
          // Ignorar errores menores de cuadro a cuadro
        }
      );
    }

    return () => {
      if (scanner) {
        try {
          scanner.clear();
        } catch (e) {}
      }
    };
  }, [showQRScanner]);

  const handleSearchByCode = (e) => {
    if (e) e.preventDefault();
    if (!searchCode.trim()) return;
    handleOpenPatientDetail(searchCode.trim().toUpperCase());
  };

  const handleSearchByCI = async (e) => {
    e.preventDefault();
    if (!searchCI.trim()) return;
    handleOpenPatientDetail(searchCI.trim());
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getPriorityStyle = (prio) => {
    if (prio === 'RED') return { border: 'border-l-4 border-l-rose-500 bg-slate-900/90', badge: 'bg-rose-500/20 text-rose-400 border-rose-500/30' };
    if (prio === 'YELLOW') return { border: 'border-l-4 border-l-amber-500 bg-slate-900/90', badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };
    return { border: 'border-l-4 border-l-emerald-500 bg-slate-900/90', badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500">
      {/* Indicador de Carga Global para Apertura de Expediente */}
      {loadingPatientDetail && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center space-y-3">
          <div className="p-4 bg-sky-500/10 rounded-2xl border border-sky-500/20 animate-pulse">
            <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
          </div>
          <p className="text-sm font-semibold text-slate-200">
            Descifrando Carnet de Identidad y cargando expediente clínico...
          </p>
        </div>
      )}

      {/* Cabecera del Dashboard */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-tr from-sky-500 to-blue-600 rounded-xl shadow-md">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Panel Médico de Triaje <span className="text-xs px-2 py-0.5 bg-sky-500/20 text-sky-400 rounded-md border border-sky-500/30 font-mono">Santa Cruz</span>
              </h1>
              <p className="text-xs text-slate-400">
                {currentUser?.full_name || 'Dr. Médico de Guardia'} ({currentUser?.role || 'DOCTOR'})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchDashboardData}
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

      {/* Contenido Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 space-y-6">
        {/* Panel de Métricas Rápidas */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
            <div className="p-3 bg-sky-500/10 rounded-xl border border-sky-500/20 text-sky-400">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-extrabold text-slate-100">{metrics.waiting_count}</span>
              <p className="text-xs text-slate-400 font-medium">En Espera</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
            <div className="p-3 bg-rose-500/10 rounded-xl border border-rose-500/20 text-rose-400">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-extrabold text-rose-400">{metrics.total_red}</span>
              <p className="text-xs text-slate-400 font-medium">Casos Rojos (Urgentes)</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-extrabold text-emerald-400">{metrics.reviewed_count}</span>
              <p className="text-xs text-slate-400 font-medium">Atendidos Hoy</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
            <div className="p-3 bg-slate-800 rounded-xl text-slate-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-extrabold text-slate-100">{metrics.total_today}</span>
              <p className="text-xs text-slate-400 font-medium">Total de Ingresos</p>
            </div>
          </div>
        </div>

        {/* Buscador Tripartito (Lector QR por cámara, Código Alfanumérico e Input CI) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3">
            Buscador Tripartito de Expedientes Médicos
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Vía 1: Botón Lector Código QR por Cámara */}
            <button
              onClick={() => setShowQRScanner(true)}
              className="py-3 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold rounded-xl text-xs transition flex items-center justify-center gap-2 shadow-md shadow-sky-500/20"
            >
              <Camera className="w-4 h-4" />
              <span>Escanear Código QR por Cámara</span>
            </button>

            {/* Vía 2: Buscador por Código Alfanumérico MS-8X92K */}
            <form onSubmit={handleSearchByCode} className="flex gap-2">
              <input
                type="text"
                placeholder="Código MS-XXXXX"
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-sky-500 font-mono uppercase"
              />
              <button
                type="submit"
                className="px-3 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-xl border border-slate-700 text-xs transition"
              >
                <Search className="w-4 h-4" />
              </button>
            </form>

            {/* Vía 3: Buscador por Carnet de Identidad (CI) */}
            <form onSubmit={handleSearchByCI} className="flex gap-2">
              <input
                type="text"
                placeholder="Carnet de Identidad (CI)"
                value={searchCI}
                onChange={(e) => setSearchCI(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
              <button
                type="submit"
                className="px-3 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-xl border border-slate-700 text-xs transition font-medium"
              >
                Buscar CI
              </button>
            </form>
          </div>
        </div>

        {/* Modal de Escáner QR por Cámara */}
        {showQRScanner && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-md w-full relative">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <QrCode className="w-5 h-5 text-sky-400" /> Escáner de Código QR
                </h3>
                <button
                  onClick={() => setShowQRScanner(false)}
                  className="p-1 hover:bg-slate-800 rounded-lg text-slate-400"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div id="qr-reader" className="w-full overflow-hidden rounded-xl bg-slate-950 border border-slate-800"></div>
              <p className="text-xs text-slate-400 text-center mt-3">
                Apunta la cámara del dispositivo al código QR impreso o en la pantalla del paciente.
              </p>
            </div>
          </div>
        )}

        {/* Lista de Espera en Tiempo Real Ordenada por Prioridad (Rojos arriba) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" /> Lista de Espera de Pacientes (Ordenada por Urgencia)
            </h2>
            <span className="text-xs text-slate-400">Total: {records.length} registros</span>
          </div>

          {records.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No hay pacientes registrados en la lista de espera por el momento.
            </div>
          ) : (
            <div className="space-y-3">
              {records.map((rec) => {
                const style = getPriorityStyle(rec.final_priority);
                const isReviewed = rec.status === 'REVIEWED';

                return (
                  <div
                    key={rec.id}
                    className={`border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition hover:border-slate-700 ${style.border}`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-100">{rec.patient_name}</span>
                        <span className="font-mono text-xs text-sky-400 font-semibold px-2 py-0.5 bg-slate-950 rounded border border-slate-800">
                          {rec.access_code}
                        </span>
                        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${style.badge}`}>
                          {rec.final_priority || 'RED'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-1">
                        <strong>Síntoma:</strong> "{rec.raw_symptoms}" | <strong>Edad:</strong> {rec.age} años | <strong>Llegada:</strong> {rec.created_at ? new Date(rec.created_at).toLocaleTimeString() : 'Reciente'}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 self-end md:self-auto">
                      <span className={`text-xs font-semibold ${isReviewed ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {isReviewed ? '✓ Atendido' : '● Pendiente'}
                      </span>
                      <button
                        onClick={() => handleOpenPatientDetail(rec.access_code || rec.id)}
                        className="py-2 px-3 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Ver Expediente</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Modal de Expediente Clínico en Pantalla Dividida y Cierre */}
      {selectedPatient && (
        <PatientDetailModal
          patientData={selectedPatient}
          onClose={() => setSelectedPatient(null)}
          onReviewComplete={fetchDashboardData}
        />
      )}
    </div>
  );
}

export default DoctorDashboard;
