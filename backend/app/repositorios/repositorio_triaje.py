"""
Implementación Concreta del Repositorio de Triaje con Supabase / Resiliencia Asíncrona.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.repositorios.base import IRepositorioTriaje
from app.esquemas.dominio import RegistroTriajeDTO, ResultadoIADTO

logger = logging.getLogger(__name__)


class RepositorioTriajeSupabase(IRepositorioTriaje):
    """
    Repositorio para la gestión de episodios de triaje utilizando Supabase
    y delegación no bloqueante con asyncio.to_thread.
    """

    def __init__(self, cliente_supabase=None, almacen_fallback: Optional[Dict[str, Any]] = None):
        self._cliente = cliente_supabase
        self._fallback = almacen_fallback if almacen_fallback is not None else {}

    async def guardar_triaje(self, datos_triaje: Dict[str, Any]) -> RegistroTriajeDTO:
        triaje_id = datos_triaje.get("id")
        self._fallback[triaje_id] = dict(datos_triaje)

        if self._cliente:
            try:
                def _insertar():
                    try:
                        self._cliente.table("registros_triaje").insert(datos_triaje).execute()
                    except Exception:
                        self._cliente.table("triage_record").insert(datos_triaje).execute()

                await asyncio.to_thread(_insertar)
            except Exception as e:
                logger.warning(f"[RepositorioTriaje] Error insertando en Supabase: {e}")

        return RegistroTriajeDTO.model_validate(datos_triaje)

    async def obtener_por_id(self, triaje_id: str) -> Optional[RegistroTriajeDTO]:
        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("registros_triaje").select("*, resultados_ia(*)").eq("id", triaje_id).execute()
                    except Exception:
                        res = self._cliente.table("triage_record").select("*, ai_result(*)").eq("id", triaje_id).execute()
                    return res.data[0] if res.data else None

                datos = await asyncio.to_thread(_consultar)
                if datos:
                    return RegistroTriajeDTO.model_validate(datos)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error consultando triaje {triaje_id}: {e}")

        if triaje_id in self._fallback:
            return RegistroTriajeDTO.model_validate(self._fallback[triaje_id])
        return None

    async def obtener_por_codigo(self, codigo_acceso: str) -> Optional[RegistroTriajeDTO]:
        cod_upper = codigo_acceso.upper().strip()
        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("registros_triaje").select("*, resultados_ia(*)").eq("codigo_acceso", cod_upper).execute()
                    except Exception:
                        res = self._cliente.table("triage_record").select("*, ai_result(*)").eq("access_code", cod_upper).execute()
                    return res.data[0] if res.data else None

                datos = await asyncio.to_thread(_consultar)
                if datos:
                    return RegistroTriajeDTO.model_validate(datos)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error consultando código {codigo_acceso}: {e}")

        for reg in self._fallback.values():
            if (reg.get("codigo_acceso") or "").upper() == cod_upper or (reg.get("access_code") or "").upper() == cod_upper:
                return RegistroTriajeDTO.model_validate(reg)
            if reg.get("id") == codigo_acceso:
                return RegistroTriajeDTO.model_validate(reg)
        return None

    async def obtener_cola_guardia(
        self,
        solo_disponibles: bool = False,
        especialidad: Optional[str] = None
    ) -> List[RegistroTriajeDTO]:
        registros_crudos = []

        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("registros_triaje").select("*, resultados_ia(*)").order("creado_en", desc=True).execute()
                    except Exception:
                        res = self._cliente.table("triage_record").select("*, ai_result(*)").order("created_at", desc=True).execute()
                    return res.data or []

                registros_crudos = await asyncio.to_thread(_consultar)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error obteniendo cola: {e}")

        if not registros_crudos:
            registros_crudos = list(self._fallback.values())

        # Deduplicar y filtrar
        vistos = set()
        resultado = []
        peso_prioridad = {"ROJO": 1, "RED": 1, "AMARILLO": 2, "YELLOW": 2, "VERDE": 3, "GREEN": 3}

        for reg in registros_crudos:
            r_id = reg.get("id")
            if not r_id or r_id in vistos:
                continue
            vistos.add(r_id)

            # Filtro de disponibilidad
            if solo_disponibles and (reg.get("medico_asignado_id") or reg.get("assigned_doctor_id")):
                continue

            # Filtro de especialidad
            if especialidad:
                esp_reg = reg.get("especialidad_solicitada") or reg.get("requested_specialty")
                if esp_reg and esp_reg.lower() != especialidad.lower():
                    continue

            resultado.append(RegistroTriajeDTO.model_validate(reg))

        # Ordenar por gravedad clínica (Rojo -> Amarillo -> Verde)
        resultado.sort(key=lambda x: (
            0 if x.estado in ["EN_CONSULTA", "IN_CONSULTATION"] else 1,
            peso_prioridad.get(str(x.prioridad_final or "").upper(), 4)
        ))

        return resultado

    async def actualizar_resultado_ia(
        self,
        triaje_id: str,
        resultado_ia: Dict[str, Any],
        prioridad_final: str,
        override_aplicado: bool = False,
        motivo_override: Optional[str] = None
    ) -> bool:
        if triaje_id in self._fallback:
            self._fallback[triaje_id]["resultados_ia"] = resultado_ia
            self._fallback[triaje_id]["resultado_ia"] = resultado_ia
            self._fallback[triaje_id]["prioridad_final"] = prioridad_final
            self._fallback[triaje_id]["final_priority"] = prioridad_final
            self._fallback[triaje_id]["estado"] = "LISTO"
            self._fallback[triaje_id]["status"] = "READY"

        if self._cliente:
            try:
                def _actualizar():
                    try:
                        self._cliente.table("resultados_ia").upsert({
                            "triaje_id": triaje_id,
                            **resultado_ia,
                            "override_aplicado": override_aplicado,
                            "motivo_override": motivo_override
                        }).execute()
                        self._cliente.table("registros_triaje").update({
                            "prioridad_final": prioridad_final,
                            "estado": "LISTO"
                        }).eq("id", triaje_id).execute()
                    except Exception:
                        self._cliente.table("ai_result").upsert({
                            "triage_id": triaje_id,
                            **resultado_ia
                        }).execute()
                        self._cliente.table("triage_record").update({
                            "final_priority": prioridad_final,
                            "status": "READY"
                        }).eq("id", triaje_id).execute()

                await asyncio.to_thread(_actualizar)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error actualizando resultado IA: {e}")

        return True

    async def asignar_medico(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        ahora = datetime.now(timezone.utc).isoformat()

        if triaje_id in self._fallback:
            self._fallback[triaje_id]["medico_asignado_id"] = medico_id
            self._fallback[triaje_id]["assigned_doctor_id"] = medico_id
            self._fallback[triaje_id]["estado"] = "EN_CONSULTA"
            self._fallback[triaje_id]["status"] = "IN_CONSULTATION"
            self._fallback[triaje_id]["asignado_en"] = ahora

        if self._cliente:
            try:
                def _asignar():
                    try:
                        self._cliente.table("registros_triaje").update({
                            "medico_asignado_id": medico_id,
                            "estado": "EN_CONSULTA",
                            "asignado_en": ahora
                        }).eq("id", triaje_id).execute()
                    except Exception:
                        self._cliente.table("triage_record").update({
                            "assigned_doctor_id": medico_id,
                            "status": "IN_CONSULTATION"
                        }).eq("id", triaje_id).execute()

                await asyncio.to_thread(_asignar)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error asignando médico: {e}")

        triaje = await self.obtener_por_id(triaje_id)
        if not triaje:
            raise ValueError(f"No se encontró el triaje con ID '{triaje_id}'")
        return triaje

    async def liberar_paciente(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        if triaje_id in self._fallback:
            self._fallback[triaje_id]["medico_asignado_id"] = None
            self._fallback[triaje_id]["assigned_doctor_id"] = None
            self._fallback[triaje_id]["estado"] = "LISTO"
            self._fallback[triaje_id]["status"] = "READY"
            self._fallback[triaje_id]["asignado_en"] = None

        if self._cliente:
            try:
                def _liberar():
                    try:
                        self._cliente.table("registros_triaje").update({
                            "medico_asignado_id": None,
                            "estado": "LISTO",
                            "asignado_en": None
                        }).eq("id", triaje_id).execute()
                    except Exception:
                        self._cliente.table("triage_record").update({
                            "assigned_doctor_id": None,
                            "status": "READY"
                        }).eq("id", triaje_id).execute()

                await asyncio.to_thread(_liberar)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error liberando paciente: {e}")

        triaje = await self.obtener_por_id(triaje_id)
        if not triaje:
            raise ValueError(f"No se encontró el triaje con ID '{triaje_id}'")
        return triaje

    async def cerrar_revision_medica(
        self,
        triaje_id: str,
        medico_id: str,
        notas_medico: str,
        prioridad_ajustada: Optional[str] = None
    ) -> RegistroTriajeDTO:
        ahora = datetime.now(timezone.utc).isoformat()

        if triaje_id in self._fallback:
            self._fallback[triaje_id]["estado"] = "REVISADO"
            self._fallback[triaje_id]["status"] = "REVIEWED"
            self._fallback[triaje_id]["notas_medico"] = notas_medico
            self._fallback[triaje_id]["doctor_notes"] = notas_medico
            if prioridad_ajustada:
                self._fallback[triaje_id]["prioridad_ajustada"] = prioridad_ajustada
                self._fallback[triaje_id]["prioridad_final"] = prioridad_ajustada

        if self._cliente:
            try:
                def _cerrar():
                    datos_up = {
                        "estado": "REVISADO",
                        "notas_medico": notas_medico,
                        "actualizado_en": ahora
                    }
                    if prioridad_ajustada:
                        datos_up["prioridad_ajustada"] = prioridad_ajustada
                        datos_up["prioridad_final"] = prioridad_ajustada

                    try:
                        self._cliente.table("registros_triaje").update(datos_up).eq("id", triaje_id).execute()
                    except Exception:
                        self._cliente.table("triage_record").update({
                            "status": "REVIEWED",
                            "doctor_notes": notas_medico
                        }).eq("id", triaje_id).execute()

                await asyncio.to_thread(_cerrar)
            except Exception as e:
                logger.error(f"[RepositorioTriaje] Error cerrando revisión: {e}")

        triaje = await self.obtener_por_id(triaje_id)
        if not triaje:
            raise ValueError(f"No se encontró el triaje con ID '{triaje_id}'")
        return triaje
