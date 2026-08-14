import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import confetti from 'canvas-confetti';
import { CheckCircle2, Copy, Download, RefreshCw, AlertTriangle, Clock, ShieldAlert } from 'lucide-react';
import { checkTriageStatus } from '../../services/triageService';

/**
 * Componente Paso 3 del Formulario Híbrido: Confirmación, Código QR Dinámico y Polling de Triaje.
 * Renderiza el código alfanumérico único (MS-XXXXX), empaqueta el QR interactivo y consulta en tiempo real
 * la actualización del estado de evaluación clínica.
 */
function StepConfirmationQR({ resultData, formData, onReset }) {
  const accessCode = resultData?.access_code || 'MS-8X92K';
  const [copied, setCopied] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(resultData?.status || 'RECEIVED');
  const [triageDetails, setTriageDetails] = useState(resultData);
  const [polling, setPolling] = useState(true);

  // Efecto de Confeti al cargar la pantalla de éxito
  useEffect(() => {
    try {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });
    } catch (e) {
      console.log('Confetti effect ignored:', e);
    }
  }, []);

  // Polling cada 3 segundos para detectar la actualización de estado a 'READY'
  useEffect(() => {
    if (!accessCode || currentStatus === 'READY' || currentStatus === 'REVIEWED') {
      setPolling(false);
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const data = await checkTriageStatus(accessCode);
        if (data) {
          setTriageDetails(data);
          if (data.status === 'READY' || data.status === 'REVIEWED') {
            setCurrentStatus(data.status);
            setPolling(false);
          }
        }
      } catch (err) {
        console.error('Error durante el polling de triaje:', err);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [accessCode, currentStatus]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(accessCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getPriorityBadge = (prio) => {
    if (prio === 'RED') return { label: 'Prioridad Roja (Urgente)', color: 'bg-rose-500/20 text-rose-400 border-rose-500/40' };
    if (prio === 'YELLOW') return { label: 'Prioridad Amarilla (Prioritario)', color: 'bg-amber-500/20 text-amber-400 border-amber-500/40' };
    return { label: 'Prioridad Verde (Atención General)', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' };
  };

  const priorityInfo = triageDetails?.final_priority ? getPriorityBadge(triageDetails.final_priority) : null;

  return (
    <div className="space-y-6 text-center">
      {/* Icono de Éxito */}
      <div className="flex flex-col items-center">
        <div className="p-4 bg-emerald-500/10 rounded-full border border-emerald-500/20 mb-3 animate-bounce">
          <CheckCircle2 className="w-12 h-12 text-emerald-400" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-100">
          ¡Pre-Triaje Registrado Exitosamente!
        </h2>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Guarde su Código Único de Acceso o muestre el Código QR en la recepción o consultorio.
        </p>
      </div>

      {/* Tarjeta Destacada del Código Alfanumérico */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/40 border border-sky-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <span className="text-[10px] tracking-wider uppercase text-sky-400 font-bold block mb-1">
          Código Único de Atención
        </span>
        <div className="text-4xl font-mono font-extrabold text-slate-100 tracking-wider my-2 selection:bg-sky-500">
          {accessCode}
        </div>

        <button
          onClick={handleCopyCode}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-sky-300 rounded-lg border border-slate-700 transition"
        >
          <Copy className="w-3.5 h-3.5" />
          {copied ? '¡Copiado!' : 'Copiar Código'}
        </button>
      </div>

      {/* Renderizado de Código QR Dinámico */}
      <div className="bg-white p-4 rounded-2xl inline-block shadow-2xl border-4 border-sky-500/20">
        <QRCodeSVG
          value={JSON.stringify({ code: accessCode, patient: formData.patientName, ci: formData.ci })}
          size={180}
          level="H"
          includeMargin={true}
        />
        <p className="text-[10px] text-slate-700 font-mono mt-2 font-semibold">
          MediSinc-IA QR Token
        </p>
      </div>

      {/* Estado del Triaje en Tiempo Real */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-left">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-sky-400" /> Estado de Evaluación IA:
          </span>
          {polling ? (
            <span className="text-xs px-2.5 py-0.5 bg-sky-500/20 text-sky-400 rounded-full border border-sky-500/30 font-medium flex items-center gap-1">
              <RefreshCw className="w-3 h-3 animate-spin" /> Procesando...
            </span>
          ) : (
            <span className="text-xs px-2.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30 font-medium">
              ✓ Evaluado
            </span>
          )}
        </div>

        {priorityInfo && (
          <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">Prioridad Asignada:</span>
            <span className={`text-xs px-3 py-1 rounded-full border font-bold ${priorityInfo.color}`}>
              {priorityInfo.label}
            </span>
          </div>
        )}

        {triageDetails?.AI_RESULT?.override_applied && (
          <div className="mt-3 bg-rose-500/10 border border-rose-500/30 rounded-lg p-2.5 text-xs text-rose-300 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong className="block">Alerta de Seguridad Activada:</strong>
              {triageDetails.AI_RESULT.override_reason}
            </div>
          </div>
        )}
      </div>

      {/* Botón para Iniciar Nueva Atención */}
      <button
        onClick={onReset}
        className="w-full py-3 px-6 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl transition duration-200 text-sm"
      >
        Registrar Nuevo Paciente
      </button>
    </div>
  );
}

export default StepConfirmationQR;
