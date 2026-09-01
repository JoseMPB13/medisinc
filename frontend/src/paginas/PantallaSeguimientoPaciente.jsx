import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Activity, Clock, ShieldCheck, RefreshCw, Smartphone, ArrowLeft } from 'lucide-react';
import { servicioTriaje } from '../servicios/servicioTriaje';

export const PantallaSeguimientoPaciente = () => {
  const { codigo } = useParams();
  const navigate = useNavigate();
  const [datosExpediente, setDatosExpediente] = useState(null);
  const [estadoActual, setEstadoActual] = useState('Cargando...');
  const [segundosRestantes, setSegundosRestantes] = useState(15 * 60);
  
  useEffect(() => {
    let intervalo = setInterval(async () => {
      try {
        if (codigo) {
          const res = await servicioTriaje.consultarEstadoTriaje(codigo);
          if (res) {
            setEstadoActual(res.estado || res.status);
            setDatosExpediente(res);
            if (res.tiempo_estimado_segundos_restantes !== undefined) {
              setSegundosRestantes(res.tiempo_estimado_segundos_restantes);
            }
          }
        }
      } catch (e) {
        console.warn('Error en polling de estado:', e);
      }
    }, 4000);

    // Ejecución inicial
    servicioTriaje.consultarEstadoTriaje(codigo).then(res => {
      if (res) {
        setEstadoActual(res.estado || res.status);
        setDatosExpediente(res);
        if (res.tiempo_estimado_segundos_restantes !== undefined) {
          setSegundosRestantes(res.tiempo_estimado_segundos_restantes);
        }
      }
    }).catch(() => setEstadoActual('Error al cargar'));

    return () => clearInterval(intervalo);
  }, [codigo]);

  // Temporizador visual local de 1 segundo
  useEffect(() => {
    const timerLocal = setInterval(() => {
      setSegundosRestantes((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timerLocal);
  }, []);

  const formatoTiempo = (segundos) => {
    if (segundos <= 0) return 'Es tu turno';
    const m = Math.floor(segundos / 60);
    const s = segundos % 60;
    return `${m} min ${s < 10 ? '0' : ''}${s} seg`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-6 selection:bg-teal-500 selection:text-white">
      <div className="max-w-md w-full bg-slate-900 border border-teal-500/30 rounded-3xl p-8 shadow-2xl mt-10">
        <div className="flex flex-col items-center mb-6">
          <div className="p-4 bg-teal-500/10 rounded-full border border-teal-500/30 mb-4 animate-pulse">
            <Smartphone className="w-10 h-10 text-teal-400" />
          </div>
          <h1 className="text-xl font-bold text-center text-white">Seguimiento en Vivo</h1>
          <p className="text-sm text-slate-400">Código de Turno: <span className="font-mono text-teal-300 font-bold">{codigo}</span></p>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
          <div className="text-xs uppercase font-bold tracking-widest text-teal-400">Estado de Atención</div>
          <div className="text-2xl font-black text-white capitalize">
            {estadoActual === 'RECEIVED' || estadoActual === 'RECIBIDO' ? 'En espera de llamado' : estadoActual}
          </div>
          
          <div className="flex items-center justify-center gap-2 text-sm text-slate-400 mt-4">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span className="font-mono font-medium">Tiempo estimado: {formatoTiempo(segundosRestantes)}</span>
          </div>
        </div>

        <div className="mt-8 space-y-4">
          <button 
            onClick={() => navigate('/')}
            className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 p-3 rounded-xl flex items-center justify-center gap-2 transition font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al Inicio (Pre-Triaje)
          </button>
          
          <div className="pt-4 border-t border-slate-800 flex items-center justify-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-teal-500" />
            <span>Información actualizada en tiempo real</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PantallaSeguimientoPaciente;
