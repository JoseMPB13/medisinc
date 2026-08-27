/**
 * Componente Informativo de Privacidad y Criptografía de Datos de Salud.
 * Explica al paciente el cifrado simétrico AES-256 de su CI y la protección médica.
 */

import React from 'react';
import { ShieldCheck, Lock, KeyRound, CheckCircle2 } from 'lucide-react';

export const AvisoPrivacidad = ({ abierto, alCerrar }) => {
  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl max-w-lg w-full p-6 shadow-2xl text-slate-100 relative">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Protección Criptográfica de Datos</h3>
            <p className="text-xs text-emerald-400">Estándar de Seguridad Hospitalaria MediSinc-IA</p>
          </div>
        </div>

        <div className="space-y-3 text-sm text-slate-300">
          <div className="flex items-start space-x-3 bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
            <Lock className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-200">Cifrado Simétrico AES-256 (Fernet)</p>
              <p className="text-xs text-slate-400">Tu Carnet de Identidad (CI) se cifra antes de almacenarse en la base de datos. Nadie, excepto el médico facultativo en consulta, puede descifrarlo.</p>
            </div>
          </div>

          <div className="flex items-start space-x-3 bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
            <KeyRound className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-200">Búsqueda Ciega HMAC-SHA256 con Pepper</p>
              <p className="text-xs text-slate-400">La indexación se realiza mediante hashes criptográficos de un solo sentido. La información médica está disociada de tu identidad civil.</p>
            </div>
          </div>

          <div className="flex items-start space-x-3 bg-slate-800/60 p-3 rounded-xl border border-slate-700/50">
            <CheckCircle2 className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-200">Trazabilidad y Auditoría Inmutable</p>
              <p className="text-xs text-slate-400">Cada consulta o visualización queda registrada de forma inviolable en los registros de auditoría del centro médico.</p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={alCerrar}
            className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium py-2.5 px-4 rounded-xl transition duration-200 shadow-lg shadow-emerald-900/30"
          >
            Entendido y Aceptar
          </button>
        </div>
      </div>
    </div>
  );
};

export const PrivacyNotice = AvisoPrivacidad;
export default AvisoPrivacidad;
