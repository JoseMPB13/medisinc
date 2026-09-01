/**
 * Componente: Paso 0 - Selector Interactivo de Especialidad Médica con Médico de Turno.
 * Al hacer clic en cualquier especialidad, selecciona la rama y el médico de guardia
 * y pasa de forma automática e inmediata al formulario de datos del paciente (Paso 1).
 */

import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  Baby,
  HeartHandshake,
  Bone,
  HeartPulse,
  Smile,
  Activity,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Users,
  AlertCircle,
  Loader2,
  UserCheck,
  Sparkles,
} from 'lucide-react';
import { servicioTriaje } from '../../servicios/servicioTriaje';

const MAPA_ICONOS = {
  Stethoscope: Stethoscope,
  Baby: Baby,
  HeartHandshake: HeartHandshake,
  Bone: Bone,
  HeartPulse: HeartPulse,
  Smile: Smile,
  Activity: Activity,
};

export const PasoSelectorEspecialidad = ({
  especialidadSeleccionada,
  medicoAsignadoId,
  medicoAsignadoNombre,
  onSeleccionarEspecialidad,
  onContinuar,
}) => {
  const [catalogo, setCatalogo] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(null);

  useEffect(() => {
    let montado = true;
    const cargarEspecialidades = async () => {
      try {
        setCargando(true);
        const data = await servicioTriaje.obtenerEspecialidades();
        if (montado && Array.isArray(data) && data.length > 0) {
          setCatalogo(data);
          // Si no hay especialidad preseleccionada, preconfigurar con la primera
          if (!especialidadSeleccionada) {
            const primerItem = data[0];
            const nombreEsp = primerItem.nombre || primerItem.name || 'Medicina General';
            const medicoTurno = primerItem.medico_de_guardia || primerItem.on_duty_doctor || (primerItem.medicos_disponibles && primerItem.medicos_disponibles[0]);
            onSeleccionarEspecialidad(
              nombreEsp,
              medicoTurno?.id || 'doc-med-general-01',
              medicoTurno?.nombre_completo || medicoTurno?.name || 'Dr. Carlos Menacho'
            );
          }
        }
      } catch (err) {
        if (montado) {
          console.error('Error al cargar especialidades:', err);
          setErrorCarga('No se pudo cargar el catálogo de especialidades.');
        }
      } finally {
        if (montado) setCargando(false);
      }
    };

    cargarEspecialidades();
    return () => {
      montado = false;
    };
  }, []);

  // Al hacer clic en una especialidad: selecciona y avanza inmediatamente al formulario
  const manejarClickEspecialidad = (esp) => {
    const nombreEsp = esp.nombre || esp.name || 'Medicina General';
    const medicoTurno =
      esp.medico_de_guardia ||
      esp.on_duty_doctor ||
      (esp.medicos_disponibles && esp.medicos_disponibles[0]) ||
      (esp.available_doctors && esp.available_doctors[0]);

    const medicoId = medicoTurno?.id || 'doc-med-general-01';
    const medicoNombre = medicoTurno?.nombre_completo || medicoTurno?.name || 'Dr. Carlos Menacho';

    onSeleccionarEspecialidad(nombreEsp, medicoId, medicoNombre);
    if (onContinuar) {
      onContinuar();
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl animate-fade-in">
      {/* Encabezado del Paso */}
      <div className="mb-8 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-bold uppercase tracking-wider mb-3">
          <Activity className="w-3.5 h-3.5" />
          <span>Paso 0 de 3 · Elige tu Especialidad</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
          ¿Qué tipo de atención médica necesitas hoy?
        </h2>
        <p className="text-slate-400 text-sm mt-2 leading-relaxed">
          Haz clic en la especialidad para asignarte con el médico de turno y pasar al formulario de ingreso.
        </p>
      </div>

      {/* Estado de Carga */}
      {cargando ? (
        <div className="py-16 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 text-teal-400 animate-spin" />
          <p className="text-sm font-medium">Consultando especialistas de guardia activos...</p>
        </div>
      ) : errorCarga ? (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-400" />
          <span>{errorCarga} Mostrando opciones de contingencia.</span>
        </div>
      ) : (
        /* Cuadrícula de Tarjetas de Especialidades */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {catalogo.map((esp) => {
            const nombreEsp = esp.nombre || esp.name || 'Medicina General';
            const iconoEsp = esp.icono || esp.icon || 'Stethoscope';
            const descripcionEsp = esp.descripcion || esp.description || 'Atención médica integral';
            const medicosActivos = esp.medicos_activos_turno ?? esp.active_doctors ?? 0;
            const tieneEspecialistaActivo = medicosActivos > 0;

            const medicoTurno =
              esp.medico_de_guardia ||
              esp.on_duty_doctor ||
              (esp.medicos_disponibles && esp.medicos_disponibles[0]) ||
              (esp.available_doctors && esp.available_doctors[0]);

            const nombreMedico = medicoTurno?.nombre_completo || medicoTurno?.name || 'Dr. Carlos Menacho';
            const esSeleccionado = especialidadSeleccionada === nombreEsp;
            const IconoComponente = MAPA_ICONOS[iconoEsp] || Stethoscope;

            return (
              <div
                key={esp.id || nombreEsp}
                onClick={() => tieneEspecialistaActivo && manejarClickEspecialidad(esp)}
                className={`group relative p-5 rounded-2xl border transition-all duration-200 flex flex-col justify-between 
                  ${tieneEspecialistaActivo ? 'cursor-pointer hover:scale-[1.02] active:scale-[0.99]' : 'cursor-not-allowed opacity-60 grayscale'}
                  ${
                  esSeleccionado
                    ? 'bg-gradient-to-b from-teal-950/70 to-slate-900/90 border-teal-400 shadow-xl shadow-teal-500/10 ring-2 ring-teal-500/40'
                    : tieneEspecialistaActivo 
                      ? 'bg-slate-950/60 border-slate-800 hover:border-teal-500/50 hover:bg-slate-800/40'
                      : 'bg-slate-900/40 border-slate-800/50'
                }`}
              >
                <div>
                  {/* Cabecera de la tarjeta: Icono + Badge */}
                  <div className="flex items-center justify-between mb-3.5">
                    <div
                      className={`p-3 rounded-xl transition-colors ${
                        esSeleccionado
                          ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                          : tieneEspecialistaActivo
                            ? 'bg-slate-800 text-teal-400 group-hover:bg-teal-500/20 group-hover:text-teal-300'
                            : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      <IconoComponente className="w-6 h-6" />
                    </div>

                    {tieneEspecialistaActivo && (
                      <div className="flex items-center gap-1 text-teal-400 font-bold text-xs bg-teal-500/10 px-2.5 py-1 rounded-full border border-teal-500/30 group-hover:bg-teal-500 group-hover:text-slate-950 transition-colors">
                        <span>Elegir</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </div>
                    )}
                  </div>

                  {/* Nombre y Descripción */}
                  <h3 className="font-extrabold text-base text-white group-hover:text-teal-300 transition-colors">
                    {nombreEsp}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-2">
                    {descripcionEsp}
                  </p>
                </div>

                {/* Pie de Tarjeta: Médico de Turno */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 font-medium">Médico de Guardia:</span>
                    {tieneEspecialistaActivo ? (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        En Turno
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] text-rose-300 font-semibold bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                        Inactivo
                      </span>
                    )}
                  </div>
                  <p className={`font-bold text-xs truncate ${tieneEspecialistaActivo ? 'text-teal-300' : 'text-slate-500'}`}>
                    {tieneEspecialistaActivo ? nombreMedico : 'Sin Especialista Activo'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pie Informativo */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs text-slate-400">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-teal-400" />
          <span>Atención confidencial cifrada con estándar médico internacional.</span>
        </div>
      </div>
    </div>
  );
};

export default PasoSelectorEspecialidad;
