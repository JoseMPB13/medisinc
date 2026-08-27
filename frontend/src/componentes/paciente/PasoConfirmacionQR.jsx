/**
 * Componente: Paso 3 del Asistente de Paciente (Confirmación con Código Alfanumérico y Código QR).
 * Renderiza el código MS-XXXXX, el canvas QR descargable y sondea el estado de atención.
 */

import React, { useEffect, useState, useRef } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import confetti from 'canvas-confetti';
import { CheckCircle2, Download, Copy, RefreshCw, Clock, ArrowRight, ShieldCheck, HeartPulse } from 'lucide-react';
import { servicioTriaje } from '../../servicios/servicioTriaje';

export const PasoConfirmacionQR = ({ resultadoTriaje, alReiniciar }) => {
  const [copiado, setCopiado] = useState(false);
  const [estadoActual, setEstadoActual] = useState(resultadoTriaje?.estado || resultadoTriaje?.status || 'RECIBIDO');
  const [datosExpediente, setDatosExpediente] = useState(resultadoTriaje);
  const qrRef = useRef(null);

  const codigoAcceso = resultadoTriaje?.codigo_acceso || resultadoTriaje?.access_code || 'MS-00000';
  const nombrePaciente = resultadoTriaje?.nombre_paciente || resultadoTriaje?.patient_name || 'Paciente';

  // Efecto de celebración al renderizar comprobante
  useEffect(() => {
    try {
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 },
        colors: ['#14b8a6', '#10b981', '#06b6d4'],
      });
    } catch {
      // Ignorar si canvas-confetti no está disponible
    }
  }, []);

  // Polling de estado en tiempo real (cada 4 segundos)
  useEffect(() => {
    let intervalo = setInterval(async () => {
      try {
        if (codigoAcceso && codigoAcceso !== 'MS-00000') {
          const res = await servicioTriaje.consultarEstadoTriaje(codigoAcceso);
          if (res) {
            const estado = res.estado || res.status;
            setEstadoActual(estado);
            setDatosExpediente(res);
          }
        }
      } catch (e) {
        console.warn('Error en polling de estado:', e);
      }
    }, 4000);

    return () => clearInterval(intervalo);
  }, [codigoAcceso]);

  const copiarAlPortapapeles = () => {
    navigator.clipboard.writeText(codigoAcceso);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  const descargarQR = () => {
    const canvas = document.getElementById('qr-canvas-paciente');
    if (canvas) {
      const url = canvas.toDataURL('image/png');
      const enlace = document.createElement('a');
      enlace.download = `MediSinc_QR_${codigoAcceso}.png`;
      enlace.href = url;
      enlace.click();
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-center text-slate-100">
      {/* Encabezado de Éxito */}
      <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex flex-col items-center">
        <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-full mb-2">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">¡Pre-Triaje Registrado Exitosamente!</h2>
        <p className="text-xs text-slate-300 mt-1 max-w-md">
          Hola <span className="font-semibold text-emerald-400">{nombrePaciente}</span>, presenta este código alfanumérico o código QR en ventanilla o al médico de guardia.
        </p>
      </div>

      {/* Contenedor del Código de Acceso Destacado */}
      <div className="bg-slate-900 border border-teal-500/30 rounded-2xl p-6 shadow-2xl space-y-5">
        <div>
          <span className="text-xs uppercase font-bold tracking-widest text-teal-400">Tu Código de Atención</span>
          <div className="mt-2 flex items-center justify-center gap-3">
            <div className="text-3xl sm:text-4xl font-extrabold tracking-widest font-mono text-white bg-slate-950 px-6 py-2 rounded-xl border border-teal-500/40 shadow-inner">
              {codigoAcceso}
            </div>
            <button
              onClick={copiarAlPortapapeles}
              className="p-3 bg-slate-800 hover:bg-slate-700 text-teal-400 rounded-xl border border-slate-700 transition"
              title="Copiar código"
            >
              {copiado ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5" />}
            </button>
          </div>
          {copiado && <p className="text-xs text-emerald-400 mt-1">¡Código copiado al portapapeles!</p>}
        </div>

        {/* Renderizado de Código QR interactivo */}
        <div className="flex flex-col items-center space-y-3 pt-2">
          <div className="p-4 bg-white rounded-2xl shadow-xl border-4 border-teal-500/30 inline-block">
            <QRCodeCanvas
              id="qr-canvas-paciente"
              value={codigoAcceso}
              size={180}
              level="H"
              includeMargin={true}
            />
          </div>

          <button
            onClick={descargarQR}
            className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1.5 bg-slate-800/80 px-3.5 py-1.5 rounded-lg border border-teal-500/20 transition"
          >
            <Download className="w-4 h-4" /> Guardar imagen del Código QR
          </button>
        </div>

        {/* Estado en Tiempo Real */}
        <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 flex items-center justify-between text-left">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-500/10 text-teal-400 rounded-lg animate-pulse">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Estado de Atención:</p>
              <p className="text-sm font-bold text-white capitalize">
                {estadoActual === 'RECEIVED' || estadoActual === 'RECIBIDO' ? 'En espera de llamado médico' : estadoActual}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg">
            <Clock className="w-3.5 h-3.5 text-teal-400" />
            <span>Turno Activo</span>
          </div>
        </div>
      </div>

      {/* Botón para iniciar un nuevo registro */}
      <div className="pt-2">
        <button
          onClick={alReiniciar}
          className="text-xs text-slate-400 hover:text-slate-200 transition underline underline-offset-4"
        >
          ¿Deseas registrar a otro paciente? Iniciar nuevo formulario
        </button>
      </div>
    </div>
  );
};

export const QRConfirmationStep = PasoConfirmacionQR;
export default PasoConfirmacionQR;
