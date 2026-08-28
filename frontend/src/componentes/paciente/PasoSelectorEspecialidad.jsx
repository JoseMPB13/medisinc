/**
 * Componente: Paso 0 - Selector Interactivo de Especialidad Médica con Médico de Turno.
 * Permite al paciente elegir la rama de atención y muestra al médico de guardia que lo atenderá.
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
        if (montado) {
          setCatalogo(data);
          // Si no hay especialidad preseleccionada, asignar la primera
          if (!especialidadSeleccionada && data.length > 0) {
            const primerItem = data[0];
            const medicoTurno = primerItem.medico_de_guardia || (primerItem.medicos_disponibles && primerItem.medicos_disponibles[0]);
            onSeleccionarEspecialidad(
              primerItem.nombre,
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

  const manejarSeleccion = (esp) => {
    const medicoTurno = esp.medico_de_guardia || (esp.medicos_disponibles && esp.medicos_disponibles[0]);
    const medicoId = medicoTurno?.id || 'doc-med-general-01';
    const medicoNombre = medicoTurno?.nombre_completo || medicoTurno?.name || 'Dr. Carlos Menacho';

    onSeleccionarEspecialidad(esp.nombre, medicoId, medicoNombre);
  };

  const itemSeleccionado = catalogo.find((e) => e.nombre === especialidadSeleccionada);
  const medicoTurnoActual = itemSeleccionado?.medico_de_guardia || {
    nombre_completo: medicoAsignadoNombre || 'Dr. Carlos Menacho',
    especialidad: especialidadSeleccionada || 'Medicina General'
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl animate-fade-in">
      {/* Encabezado del Paso */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-3">
          <Activity className="w-3.5 h-3.5" />
          <span>Paso 0 de 3 · Selección de Especialidad y Médico</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          ¿Qué tipo de atención médica necesitas hoy?
        </h2>
        <p className="text-slate-400 text-sm mt-2 leading-relaxed">
          Selecciona la especialidad de consulta. Un médico de guardia evaluará tu pre-triaje de forma personalizada.
        </p>
      </div>

      {/* Estado de Carga */}
      {cargando ? (
        <div className="py-16 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 text-teal-400 animate-spin" />
          <p className="text-sm font-medium">Consultando especialistas de guardia...</p>
        </div>
      ) : errorCarga ? (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-400" />
          <span>{errorCarga} Mostrando opciones básicas de contingencia.</span>
        </div>
      ) : (
        <>
          {/* Cuadrícula de Tarjetas de Especialidades */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {catalogo.map((esp) => {
              const IconoComponente = MAPA_ICONOS[esp.icono] || Stethoscope;
              const esSeleccionado = especialidadSeleccionada === esp.nombre;
              const tieneEspecialistaActivo = esp.medicos_activos_turno > 0;
              const medicoTurno = esp.medico_de_guardia;

              return (
                <div
                  key={esp.id}
                  onClick={() => manejarSeleccion(esp)}
                  className={`group relative p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                    esSeleccionado
                      ? 'bg-gradient-to-b from-teal-950/60 to-slate-900/90 border-teal-400/80 shadow-lg shadow-teal-500/10 ring-2 ring-teal-500/30 scale-[1.01]'
                      : 'bg-slate-950/60 border-slate-800/90 hover:border-slate-700 hover:bg-slate-800/40'
                  }`}
                >
                  <div>
                    {/* Cabecera de la tarjeta: Icono + Check */}
                    <div className="flex items-center justify-between mb-3.5">
                      <div
                        className={`p-3 rounded-xl transition-colors ${
                          esSeleccionado
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'bg-slate-800 text-teal-400 group-hover:bg-slate-700 group-hover:text-teal-300'
                        }`}
                      >
                        <IconoComponente className="w-6 h-6" />
                      </div>

                      {esSeleccionado ? (
                        <div className="flex items-center gap-1 text-teal-400 font-semibold text-xs bg-teal-500/10 px-2.5 py-1 rounded-full border border-teal-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                          <span>Elegida</span>
                        </div>
                      ) : null}
                    </div>

                    {/* Nombre y Descripción */}
                    <h3
                      className={`font-bold text-base transition-colors ${
                        esSeleccionado ? 'text-teal-300' : 'text-slate-100 group-hover:text-white'
                      }`}
                    >
                      {esp.nombre}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                      {esp.descripcion}
                    </p>
                  </div>

                  {/* Pie de Tarjeta: Disponibilidad y Médico de Turno */}
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                    {tieneEspecialistaActivo ? (
                      <span className="inline-flex items-center gap-1.5 text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        Especialista en turno
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-amber-300 font-medium bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                        Guardia General
                      </span>
                    )}

                    <span className="text-slate-400 font-mono text-[10px]">
                      {tieneEspecialistaActivo ? `${esp.medicos_activos_turno} médico(s)` : 'Cobertura Activa'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Tarjeta Destacada del Médico Asignado */}
          {especialidadSeleccionada && (
            <div className="p-4 rounded-2xl bg-teal-950/40 border border-teal-500/30 shadow-md mb-8 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-teal-500/20 border border-teal-500/40 text-teal-300">
                  <UserCheck className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-teal-400 block">
                    Médico de Guardia Asignado para tu Atención:
                  </span>
                  <p className="text-sm font-bold text-white">
                    {medicoTurnoActual?.nombre_completo || medicoTurnoActual?.name || 'Dr. Carlos Menacho'}{' '}
                    <span className="text-xs font-normal text-slate-400">
                      — {itemSeleccionado?.nombre || 'Medicina General'}
                    </span>
                  </p>
                </div>
              </div>

              <span className="hidden sm:inline-flex items-center gap-1 text-xs text-emerald-300 font-semibold bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
                <ShieldCheck className="w-3.5 h-3.5" /> En Turno Activo
              </span>
            </div>
          )}
        </>
      )}

      {/* Botón de Continuar */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-800">
        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-teal-400" />
          <span>Atención confidencial cifrada con estándar médico.</span>
        </div>

        <button
          type="button"
          onClick={onContinuar}
          disabled={!especialidadSeleccionada || cargando}
          className="bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-black py-3 px-7 rounded-2xl shadow-lg shadow-teal-500/20 transition-all flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed group cursor-pointer"
        >
          <span>Continuar a Mis Datos</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};

export default PasoSelectorEspecialidad;
