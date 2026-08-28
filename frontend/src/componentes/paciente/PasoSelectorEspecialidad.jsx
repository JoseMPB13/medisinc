/**
 * Componente: Paso 0 - Selector Interactivo de Especialidad Médica.
 * Permite al paciente indicar la rama de atención deseada y muestra la disponibilidad de guardia en tiempo real.
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
          // Si no hay especialidad preseleccionada, asignar la primera disponible
          if (!especialidadSeleccionada && data.length > 0) {
            onSeleccionarEspecialidad(data[0].nombre);
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

  const manejarSeleccion = (nombreEspecialidad) => {
    onSeleccionarEspecialidad(nombreEspecialidad);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl animate-fade-in">
      {/* Encabezado del Paso */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-3">
          <Activity className="w-3.5 h-3.5" />
          <span>Paso 0 de 3 · Triaje Especializado</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          ¿Qué tipo de atención médica necesitas hoy?
        </h2>
        <p className="text-slate-400 text-sm mt-2 leading-relaxed">
          Selecciona la especialidad de consulta. Si no estás seguro, puedes elegir{' '}
          <strong className="text-teal-300">Medicina General</strong> y nuestro equipo clínico te orientará.
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
        /* Cuadrícula de Tarjetas de Especialidades */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {catalogo.map((esp) => {
            const IconoComponente = MAPA_ICONOS[esp.icono] || Stethoscope;
            const esSeleccionado = especialidadSeleccionada === esp.nombre;
            const tieneEspecialistaActivo = esp.medicos_activos_turno > 0;

            return (
              <div
                key={esp.id}
                onClick={() => manejarSeleccion(esp.nombre)}
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

                {/* Pie de Tarjeta: Disponibilidad de Guardia */}
                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                  {tieneEspecialistaActivo ? (
                    <span className="inline-flex items-center gap-1.5 text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                      Especialista en turno ({esp.medicos_activos_turno})
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-md">
                      <Users className="w-3 h-3 text-slate-400" />
                      Atención por Guardia General
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Alerta de Seguridad y Botón de Avance */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-teal-400 flex-shrink-0" />
          <span>
            Ante emergencias vitales (dolor de pecho, desmayos), el sistema priorizará atención médica inmediata.
          </span>
        </div>

        <button
          type="button"
          onClick={onContinuar}
          disabled={!especialidadSeleccionada || cargando}
          className="w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/20 hover:from-teal-400 hover:to-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
        >
          <span>Continuar con mis datos</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default PasoSelectorEspecialidad;
