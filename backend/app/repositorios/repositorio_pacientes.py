"""
Implementación Concreta del Repositorio de Pacientes (3NF) con Supabase / Resiliencia.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.repositorios.base import IRepositorioPacientes
from app.esquemas.dominio import PacienteDTO
from app.core.seguridad import descifrar_ci

logger = logging.getLogger(__name__)


class RepositorioPacientesSupabase(IRepositorioPacientes):
    """
    Repositorio para la gestión de la tabla maestra de pacientes cumpliendo 3NF.
    """

    def __init__(self, cliente_supabase=None, almacen_fallback: Optional[Dict[str, Any]] = None):
        self._cliente = cliente_supabase
        self._fallback = almacen_fallback if almacen_fallback is not None else {}

    async def crear_o_actualizar_paciente(self, datos_paciente: Dict[str, Any]) -> PacienteDTO:
        ci_hash = datos_paciente.get("ci_hash")
        paciente_id = datos_paciente.get("id") or (
            str(uuid.uuid5(uuid.NAMESPACE_DNS, f"paciente.{ci_hash}")) if ci_hash else str(uuid.uuid4())
        )
        ahora = datetime.now(timezone.utc).isoformat()

        obj_paciente = {
            "id": paciente_id,
            "ci_hash": ci_hash,
            "ci_cifrado": datos_paciente.get("ci_cifrado"),
            "nombre_completo": datos_paciente.get("nombre_completo") or datos_paciente.get("nombre_paciente", "Paciente"),
            "edad": datos_paciente.get("edad", 0),
            "genero": datos_paciente.get("genero", "No especificado"),
            "alergias_medicamentosas": datos_paciente.get("alergias_medicamentosas", "Ninguna conocida"),
            "enfermedades_base": datos_paciente.get("enfermedades_base", []),
            "medicacion_habitual": datos_paciente.get("medicacion_habitual") or datos_paciente.get("medicacion_actual", "No toma medicación"),
            "creado_en": datos_paciente.get("creado_en", ahora),
            "actualizado_en": ahora
        }

        self._fallback[paciente_id] = obj_paciente
        if ci_hash:
            self._fallback[ci_hash] = obj_paciente

        if self._cliente:
            try:
                def _guardar():
                    try:
                        self._cliente.table("pacientes").upsert(obj_paciente).execute()
                    except Exception:
                        self._cliente.table("patients").upsert(obj_paciente).execute()

                await asyncio.to_thread(_guardar)
            except Exception as e:
                logger.warning(f"[RepositorioPacientes] Error persistiendo paciente: {e}")

        return PacienteDTO.model_validate(obj_paciente)

    async def obtener_por_id(self, paciente_id: str) -> Optional[PacienteDTO]:
        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("pacientes").select("*").eq("id", paciente_id).execute()
                    except Exception:
                        res = self._cliente.table("patients").select("*").eq("id", paciente_id).execute()
                    return res.data[0] if res.data else None

                datos = await asyncio.to_thread(_consultar)
                if datos:
                    return PacienteDTO.model_validate(datos)
            except Exception as e:
                logger.error(f"[RepositorioPacientes] Error consultando paciente {paciente_id}: {e}")

        if paciente_id in self._fallback:
            return PacienteDTO.model_validate(self._fallback[paciente_id])
        return None

    async def obtener_por_ci_hash(self, ci_hash: str) -> Optional[PacienteDTO]:
        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("pacientes").select("*").eq("ci_hash", ci_hash).execute()
                    except Exception:
                        res = self._cliente.table("patients").select("*").eq("ci_hash", ci_hash).execute()
                    return res.data[0] if res.data else None

                datos = await asyncio.to_thread(_consultar)
                if datos:
                    return PacienteDTO.model_validate(datos)
            except Exception as e:
                logger.error(f"[RepositorioPacientes] Error consultando ci_hash {ci_hash}: {e}")

        if ci_hash in self._fallback:
            return PacienteDTO.model_validate(self._fallback[ci_hash])
        return None

    async def obtener_historial_clinico(self, paciente_id: str) -> Dict[str, Any]:
        paciente = await self.obtener_por_id(paciente_id)
        ci_descifrado = "NO_DISPONIBLE"
        if paciente and paciente.ci_cifrado:
            ci_descifrado = descifrar_ci(paciente.ci_cifrado)

        consultas = []
        if self._cliente:
            try:
                def _consultar_episodios():
                    try:
                        res = self._cliente.table("registros_triaje").select("*, resultados_ia(*)").eq("paciente_id", paciente_id).order("creado_en", desc=True).execute()
                    except Exception:
                        res = self._cliente.table("triage_record").select("*, ai_result(*)").eq("patient_id", paciente_id).order("created_at", desc=True).execute()
                    return res.data or []

                consultas = await asyncio.to_thread(_consultar_episodios)
            except Exception as e:
                logger.error(f"[RepositorioPacientes] Error consultando episodios clínicos: {e}")

        return {
            "paciente_id": paciente_id,
            "paciente": paciente.model_dump() if paciente else None,
            "ci_descifrado": ci_descifrado,
            "total_atenciones": len(consultas),
            "consultas": consultas,
            "records": consultas
        }
