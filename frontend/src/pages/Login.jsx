import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/authService';
import { Stethoscope, Lock, Mail, Shield, AlertCircle, ShieldCheck } from 'lucide-react';

/**
 * Vista de Inicio de Sesión Institucional para el Personal Médico y Administradores.
 */
function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('doctor@medisinc.bo');
  const [password, setPassword] = useState('medisinc2026');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await login(email, password);
      const userRole = result?.user?.role || (email.includes('admin') ? 'ADMIN' : 'DOCTOR');

      if (userRole === 'ADMIN') {
        navigate('/admin/dashboard');
      } else {
        navigate('/doctor/dashboard');
      }
    } catch (err) {
      console.error('Error al iniciar sesión:', err);
      setError(err.message || 'Error al autenticar. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center p-4 font-sans selection:bg-sky-500">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        {/* Cabecera del Portal Médico / Admin */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="p-3.5 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-2xl shadow-lg shadow-sky-500/20 mb-3">
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-100">
            Acceso Institucional <span className="text-sky-400 font-mono">MediSinc</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Portal Clínico para Médicos de Guardia y Administradores
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Correo Electrónico Institucional
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="doctor@medisinc.bo o admin@medisinc.bo"
                className="w-full bg-slate-950 border border-slate-700/80 focus:border-sky-500 rounded-xl py-2.5 pl-10 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Contraseña
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-700/80 focus:border-sky-500 rounded-xl py-2.5 pl-10 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => { setEmail('doctor@medisinc.bo'); setPassword('medisinc2026'); }}
              className="flex-1 py-1 px-2 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-lg text-[10px] border border-slate-700 transition"
            >
              Demo: Médico
            </button>
            <button
              type="button"
              onClick={() => { setEmail('admin@medisinc.bo'); setPassword('medisinc2026'); }}
              className="flex-1 py-1 px-2 bg-slate-800 hover:bg-slate-700 text-indigo-400 rounded-lg text-[10px] border border-slate-700 transition"
            >
              Demo: Administrador
            </button>
          </div>

          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 text-[11px] text-slate-400 flex items-center gap-2">
            <Shield className="w-4 h-4 text-sky-400 shrink-0" />
            <span>Acceso protegido por JWT Tokens e Inserción atómica en AUDIT_LOG.</span>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-6 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition duration-200 flex items-center justify-center gap-2"
          >
            {loading ? 'Verificando Credenciales...' : 'Ingresar al Portal'}
          </button>
        </form>
      </div>

      <footer className="mt-8 text-center text-xs text-slate-500">
        MediSinc-IA © 2026 • Santa Cruz de la Sierra, Bolivia
      </footer>
    </div>
  );
}

export default Login;
