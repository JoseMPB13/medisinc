import React from 'react';
import { ShieldCheck, Lock, CheckCircle2 } from 'lucide-react';

/**
 * Componente Modal / Banner de Aviso de Privacidad y Confidencialidad de Datos Médicos.
 * Garantiza el consentimiento informado del paciente antes de capturar información de salud.
 */
function PrivacyNotice({ onAccept }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 md:p-8 max-w-lg w-full shadow-2xl animate-fade-in">
        <div className="flex items-center gap-3 mb-4 text-sky-400">
          <div className="p-3 bg-sky-500/10 rounded-xl border border-sky-500/20">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">Protección de Datos Sanitarios</h2>
            <p className="text-xs text-sky-400 font-medium">Santa Cruz de la Sierra - Bolivia</p>
          </div>
        </div>

        <div className="space-y-3 text-slate-300 text-sm mb-6 leading-relaxed">
          <p className="flex items-start gap-2">
            <Lock className="w-4 h-4 text-sky-400 mt-1 shrink-0" />
            <span>
              Su <strong>Carnet de Identidad (CI)</strong> será almacenado mediante <strong>cifrado militar AES-256</strong> y un hash unidireccional seguro. Ningún tercero no autorizado podrá visualizar su documento.
            </span>
          </p>
          <p className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-1 shrink-0" />
            <span>
              La información declarada tiene como único propósito acelerar su atención clínica previa a la consulta con el profesional de salud.
            </span>
          </p>
        </div>

        <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 mb-6 text-xs text-slate-400">
          Al presionar "Aceptar y Continuar", usted declara ingresar datos verídicos para el proceso asistido de pre-triaje.
        </div>

        <button
          onClick={onAccept}
          className="w-full py-3 px-6 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition duration-200 flex items-center justify-center gap-2"
        >
          Aceptar y Continuar
        </button>
      </div>
    </div>
  );
}

export default PrivacyNotice;
