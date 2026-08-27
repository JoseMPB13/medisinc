/**
 * Portal del Médico de Guardia (MediSinc-IA).
 * Dashboard clínico en tiempo real con ordenamiento por gravedad (ROJO > AMARILLO > VERDE),
 * escáner de código QR por cámara web y visor de expedientes con CI descifrado.
 */

import React, { useState, useEffect } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import axios from 'axios';
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
} from 'lucide-react';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';
import ModalDetallePaciente from '../componentes/medico/ModalDetallePaciente';

const URL_BASE_API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const PanelMedico = () => {
  const [pacientes, setPacientes] = useState([]);
  const [metricas, setMetricas] = useState({
    en_espera: 0,
    atendidos: 0,
    total_rojo: 0,
    total_hoy: 0,
  });
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroPrioridad, setFiltroPrioridad] = useState('TODOS');
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState(null);
  const [mostrarEscaner, setMostrarEscaner] = useState(false);

  const usuarioActual = servicioAutenticacion.obtenerUsuarioActual();

  const cargarDatosPanel = async () => {
    try {
      const token = servicioAutenticacion.obtenerToken();
      const res = await axios.get(`${URL_BASE_API}/api/v1/medico/panel`, {
        headers: { Authorization: token ? `Bearer ${token}` : '' },
      });

      const lista = res.data?.registros || res.data?.records || [];
      const stats = res.data?.metricas || res.data?.metrics || {};

      setPacientes(lista);
      setMetricas({
        en_espera: stats.en_espera ?? stats.waiting_count ?? 0,
        atendidos: stats.atendidos ?? stats.reviewed_count ?? 0,
        total_rojo: stats.total_rojo ?? stats.total_red ?? 0,
        total_hoy: stats.total_hoy ?? stats.total_today ?? lista.length,
      });
    } catch (error) {
      console.error('Error cargando panel médico:', error);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatosPanel();
    const intervalo = setInterval(cargarDatosPanel, 6000);
    return () => clearInterval(intervalo);
  }, []);

  // Inicializar escáner QR cuando se abre el modal de cámara
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
        },
        (error) => {
          // Fallos comunes de escaneo frame a frame
        }
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

  const abrirExpediente = async (paciente) => {
    try {
      const id = paciente.codigo_acceso || paciente.access_code || paciente.id;
      const token = servicioAutenticacion.obtenerToken();
      const res = await axios.get(`${URL_BASE_API}/api/v1/medico/paciente/${id}`, {
        headers: { Authorization: token ? `Bearer ${token}` : '' },
      });
      setPacienteSeleccionado(res.data);
    } catch (e) {
      console.error('Error al abrir expediente:', e);
      setPacienteSeleccionado(paciente);
    }
  };

  // Filtrado reactivo en memoria
  const pacientesFiltrados = pacientes.filter((p) => {
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Barra de Navegación del Médico */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg text-white tracking-tight flex items-center gap-2">
                Panel Médico de Guardia <span className="text-xs bg-slate-800 text-teal-400 px-2 py-0.5 rounded-full border border-teal-500/20">En Vivo</span>
              </h1>
              <p className="text-xs text-slate-400">
                {usuarioActual?.nombre || 'Dr. Médico de Turno'} | Servicio de Emergencias
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMostrarEscaner(true)}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-teal-400 rounded-xl border border-slate-700 flex items-center gap-2 text-xs font-semibold transition shadow-sm"
            >
              <QrCode className="w-4 h-4" />
              <span className="hidden sm:inline">Escanear QR</span>
            </button>

            <button
              onClick={() => {
                servicioAutenticacion.cerrarSesion();
                window.location.href = '/iniciar-sesion';
              }}
              className="p-2 text-slate-400 hover:text-rose-400 rounded-xl bg-slate-800 hover:bg-slate-800 transition"
              title="Cerrar Sesión"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Contenido Principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 space-y-6">
        {/* Tarjetas de Métricas Cuantitativas Superiores */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase">En Espera</span>
              <Users className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-2xl font-black text-white mt-2">{metricas.en_espera}</div>
            <p className="text-[11px] text-slate-500 mt-1">Pacientes en sala</p>
          </div>

          <div className="bg-slate-900/80 border border-rose-500/30 p-4 rounded-2xl shadow-lg bg-rose-950/10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-300 uppercase">Emergencias Rojas</span>
              <AlertOctagon className="w-5 h-5 text-rose-400 animate-pulse" />
            </div>
            <div className="text-2xl font-black text-rose-400 mt-2">{metricas.total_rojo}</div>
            <p className="text-[11px] text-rose-300/70 mt-1">Atención inmediata requerida</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase">Atendidos Hoy</span>
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 mt-2">{metricas.atendidos}</div>
            <p className="text-[11px] text-slate-500 mt-1">Casos revisados y cerrados</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase">Total Recibidos</span>
              <Clock className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-2xl font-black text-white mt-2">{metricas.total_hoy}</div>
            <p className="text-[11px] text-slate-500 mt-1">Volumen de la guardia</p>
          </div>
        </div>

        {/* Barra de Búsqueda y Filtros de Prioridad */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-lg flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Buscar por paciente o código (MS-XXXXX)..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            {['TODOS', 'ROJO', 'AMARILLO', 'VERDE'].map((f) => (
              <button
                key={f}
                onClick={() => setFiltroPrioridad(f)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                  filtroPrioridad === f
                    ? f === 'ROJO'
                      ? 'bg-rose-500 text-white'
                      : f === 'AMARILLO'
                      ? 'bg-amber-500 text-slate-950'
                      : f === 'VERDE'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-teal-500 text-slate-950'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Tabla de Pacientes Ordenada por Severidad Clínica */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Prioridad</th>
                  <th className="py-3.5 px-4">Código</th>
                  <th className="py-3.5 px-4">Paciente</th>
                  <th className="py-3.5 px-4">Edad / Género</th>
                  <th className="py-3.5 px-4">Motivo de Consulta</th>
                  <th className="py-3.5 px-4">Estado</th>
                  <th className="py-3.5 px-4 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cargando ? (
                  <tr>
                    <td colSpan="7" className="py-12 text-center text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-teal-400" />
                      Cargando lista de triaje...
                    </td>
                  </tr>
                ) : pacientesFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-12 text-center text-slate-500">
                      No hay pacientes en espera para el filtro seleccionado.
                    </td>
                  </tr>
                ) : (
                  pacientesFiltrados.map((p) => {
                    const prioridad = (p.prioridad_final || p.final_priority || 'VERDE').toUpperCase();
                    const esRojo = prioridad === 'ROJO' || prioridad === 'RED';
                    const esAmarillo = prioridad === 'AMARILLO' || prioridad === 'YELLOW';
                    const estado = p.estado || p.status || 'RECIBIDO';
                    const estaRevisado = estado === 'REVISADO' || estado === 'REVIEWED';

                    return (
                      <tr
                        key={p.id || p.codigo_acceso}
                        className={`hover:bg-slate-800/40 transition ${
                          esRojo ? 'bg-rose-950/10' : ''
                        }`}
                      >
                        {/* Badge de Prioridad */}
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2.5 py-1 rounded-full font-extrabold text-[10px] border flex items-center gap-1 w-fit ${
                              esRojo
                                ? 'bg-rose-500/20 border-rose-500 text-rose-300 animate-pulse'
                                : esAmarillo
                                ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                                : 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                            {prioridad}
                          </span>
                        </td>

                        {/* Código de Acceso */}
                        <td className="py-3.5 px-4 font-mono font-bold text-teal-400">
                          {p.codigo_acceso || p.access_code}
                        </td>

                        {/* Nombre del Paciente */}
                        <td className="py-3.5 px-4 font-semibold text-white">
                          {p.nombre_paciente || p.patient_name}
                        </td>

                        {/* Demografía */}
                        <td className="py-3.5 px-4 text-slate-300">
                          {p.edad || p.age} años | {p.genero || p.gender}
                        </td>

                        {/* Resumen o Síntoma */}
                        <td className="py-3.5 px-4 max-w-xs truncate text-slate-300">
                          {p.sintomas_brutos || p.raw_symptoms}
                        </td>

                        {/* Estado */}
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              estaRevisado
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {estado}
                          </span>
                        </td>

                        {/* Botón de Acción */}
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => abrirExpediente(p)}
                            className="px-3.5 py-1.5 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white font-semibold rounded-xl text-xs shadow-md shadow-teal-900/20 transition flex items-center gap-1 ml-auto"
                          >
                            <span>Evaluar</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
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

      {/* Modal de Escáner QR por Cámara */}
      {mostrarEscaner && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-teal-500/40 rounded-3xl p-6 max-w-md w-full text-center space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center justify-center gap-2">
              <QrCode className="w-5 h-5 text-teal-400" />
              Escanear Código QR del Paciente
            </h3>
            <div id="qr-reader-container" className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-950"></div>
            <button
              onClick={() => setMostrarEscaner(false)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2.5 rounded-xl text-xs transition"
            >
              Cerrar Cámara
            </button>
          </div>
        </div>
      )}

      {/* Modal de Expediente Clínico Dividido (Split View) */}
      {pacienteSeleccionado && (
        <ModalDetallePaciente
          expediente={pacienteSeleccionado}
          alCerrar={() => setPacienteSeleccionado(null)}
          alActualizar={cargarDatosPanel}
        />
      )}
    </div>
  );
};

export const DoctorDashboard = PanelMedico;
export default PanelMedico;
