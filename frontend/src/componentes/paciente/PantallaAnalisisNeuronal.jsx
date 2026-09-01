import React, { useState, useEffect } from 'react';
import { BrainCircuit, Activity, HeartPulse, Network } from 'lucide-react';

const MENSAJES = [
  "Analizando constantes vitales...",
  "Cruzando datos clínicos...",
  "Evaluando factores de riesgo...",
  "Clasificando nivel de urgencia..."
];

export const PantallaAnalisisNeuronal = () => {
  const [indiceMensaje, setIndiceMensaje] = useState(0);

  useEffect(() => {
    // Cambiar de mensaje cada 800ms
    const intervalo = setInterval(() => {
      setIndiceMensaje((prev) => {
        if (prev < MENSAJES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 800); 

    return () => clearInterval(intervalo);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-8 text-center animate-fade-in">
      <div className="relative">
        {/* Efecto de resplandor */}
        <div className="absolute inset-0 bg-teal-500 blur-2xl opacity-20 rounded-full animate-pulse"></div>
        {/* Contenedor del ícono principal */}
        <div className="relative z-10 w-28 h-28 bg-slate-900 border border-teal-500/50 rounded-full flex items-center justify-center shadow-[0_0_40px_rgba(20,184,166,0.3)]">
          {/* Alternando íconos basados en el mensaje actual para más dinamismo */}
          {indiceMensaje === 0 && <HeartPulse className="w-14 h-14 text-teal-400 animate-pulse" />}
          {indiceMensaje === 1 && <Network className="w-14 h-14 text-teal-400 animate-pulse" />}
          {indiceMensaje === 2 && <Activity className="w-14 h-14 text-teal-400 animate-pulse" />}
          {indiceMensaje === 3 && <BrainCircuit className="w-14 h-14 text-teal-400 animate-pulse" />}
        </div>
        
        {/* Partículas rotatorias simuladas (anillos CSS) */}
        <div className="absolute inset-[-10px] border-2 border-dashed border-teal-500/30 rounded-full animate-[spin_4s_linear_infinite]" />
        <div className="absolute inset-[-20px] border border-teal-500/10 rounded-full animate-[spin_3s_linear_infinite_reverse]" />
      </div>
      
      <div className="space-y-3">
        <h3 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400">
          Análisis de IA en Curso
        </h3>
        <p className="text-base font-semibold text-slate-300 h-6">
          {MENSAJES[indiceMensaje]}
        </p>
      </div>
      
      {/* Indicadores de progreso (barritas) */}
      <div className="flex gap-2 mt-6">
        {MENSAJES.map((_, i) => (
          <div 
            key={i} 
            className={`h-1.5 rounded-full transition-all duration-500 ${
              i <= indiceMensaje ? 'w-10 bg-teal-400 shadow-[0_0_10px_rgba(45,212,191,0.8)]' : 'w-4 bg-slate-800'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default PantallaAnalisisNeuronal;
