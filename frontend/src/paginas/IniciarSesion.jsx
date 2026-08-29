/**
 * Página de Autenticación para Personal Médico y Administradores (MediSinc-IA).
 * Permite el acceso seguro con correo y contraseña, redireccionando según el rol.
 */

import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Stethoscope, Lock, Mail, ArrowRight, ShieldCheck, HeartPulse, AlertCircle, Loader2 } from 'lucide-react';
import { servicioAutenticacion } from '../servicios/servicioAutenticacion';

export const IniciarSesion = () => {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();
  const location = useLocation();
  const destino = location.state?.from?.pathname || '/medico';

  const manejarEnvio = async (e) => {
    e.preventDefault();
    setCargando(true);
    setError(null);

    try {
      const usuario = await servicioAutenticacion.iniciarSesion(correo, password);
      const rol = usuario.rol || usuario.role;

      if (rol === 'ADMIN') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/medico', { replace: true });
      }
    } catch (err) {
      console.error('Error de autenticación:', err);
      setError('Credenciales inválidas. Por favor verifica tu correo y contraseña.');
    } finally {
      setCargando(false);
    }
  };

  const rellenarCredencialesDemo = (tipo) => {
    setPassword('123456');
    if (tipo === 'admin') {
      setCorreo('admin@medisinc.bo');
    } else if (tipo === 'pediatria') {
      setCorreo('mariana.vaca@medisinc.bo');
    } else if (tipo === 'ginecologia') {
      setCorreo('sofia.justiniano@medisinc.bo');
    } else {
      setCorreo('carlos.menacho@medisinc.bo');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-slate-100 selection:bg-teal-500">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <Link to="/" className="inline-flex items-center gap-2 p-3 bg-teal-500/10 border border-teal-500/30 rounded-2xl text-teal-400">
          <HeartPulse className="w-8 h-8" />
        </Link>
        <h2 className="text-2xl font-black text-white tracking-tight">
          Portal Clínico MediSinc·IA
        </h2>
        <p className="text-xs text-slate-400">
          Acceso para médicos de guardia y administradores autorizados
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900/90 border border-slate-800 py-8 px-6 sm:px-10 rounded-3xl shadow-2xl backdrop-blur-xl">
          {error && (
            <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={manejarEnvio} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Correo Electrónico Institucional
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="email"
                  required
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  placeholder="usuario@medisinc.bo"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Contraseña de Seguridad
                </label>
                <span className="text-[10px] text-teal-400 font-mono">Clave demo: 123456</span>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="123456"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={cargando}
              className="w-full bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-teal-900/30 transition duration-200 flex items-center justify-center gap-2 text-xs disabled:opacity-50 mt-2"
            >
              {cargando ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Validando Credenciales...</span>
                </>
              ) : (
                <>
                  <span>Ingresar al Sistema</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Accesos Rápidos de Demostración con perfiles de la DB */}
          <div className="mt-6 pt-6 border-t border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider block mb-2">
              Cuentas de Demostración (Contraseña: 123456):
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => rellenarCredencialesDemo('general')}
                className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-800 text-teal-400 rounded-lg text-[11px] font-semibold border border-slate-700 transition text-left truncate"
                title="Dr. Carlos Menacho (Medicina General)"
              >
                🩺 Dr. Menacho (Med. General)
              </button>
              <button
                type="button"
                onClick={() => rellenarCredencialesDemo('pediatria')}
                className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-800 text-emerald-400 rounded-lg text-[11px] font-semibold border border-slate-700 transition text-left truncate"
                title="Dra. Mariana Vaca (Pediatría)"
              >
                👶 Dra. Vaca (Pediatría)
              </button>
              <button
                type="button"
                onClick={() => rellenarCredencialesDemo('ginecologia')}
                className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-800 text-pink-400 rounded-lg text-[11px] font-semibold border border-slate-700 transition text-left truncate"
                title="Dra. Sofía Justiniano (Ginecología)"
              >
                🌸 Dra. Justiniano (Ginecología)
              </button>
              <button
                type="button"
                onClick={() => rellenarCredencialesDemo('admin')}
                className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-800 text-indigo-400 rounded-lg text-[11px] font-semibold border border-slate-700 transition text-left truncate"
                title="Dr. Fernando Morales (Administrador)"
              >
                🛡️ Dr. Morales (Admin)
              </button>
            </div>
          </div>

          <div className="mt-4 text-center">
            <Link to="/" className="text-xs text-slate-400 hover:text-slate-200 transition">
              ← Volver al formulario de paciente
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export const Login = IniciarSesion;
export default IniciarSesion;
