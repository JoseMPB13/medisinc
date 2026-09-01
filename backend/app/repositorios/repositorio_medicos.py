"""
Implementación Concreta del Repositorio de Personal Médico y Turnos de Guardia con Supabase.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.repositorios.base import IRepositorioMedicos
from app.esquemas.dominio import PerfilMedicoDTO

logger = logging.getLogger(__name__)

# Personal base inicial para contingencia y pruebas
_MEDICOS_INICIALES = [
    {
        "id": "doc-med-general-01",
        "usuario_id": "usr-med-01",
        "nombre_completo": "Dr. Carlos Menacho",
        "correo": "carlos.menacho@medisinc.bo",
        "especialidad": "Medicina General",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-pediatria-02",
        "usuario_id": "usr-med-02",
        "nombre_completo": "Dra. Mariana Vaca",
        "correo": "mariana.vaca@medisinc.bo",
        "especialidad": "Pediatría",
        "rol": "MEDICO",
        "turno_asignado": "TARDE_NOCHE",
        "dias_guardia": ["Lunes", "Miércoles", "Viernes", "Domingo"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-ginecologia-03",
        "usuario_id": "usr-med-03",
        "nombre_completo": "Dr. Fernando Ortiz",
        "correo": "fernando.ortiz@medisinc.bo",
        "especialidad": "Ginecología y Obstetricia",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Martes", "Jueves", "Sábado"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-trauma-04",
        "usuario_id": "usr-med-04",
        "nombre_completo": "Dr. Sergio Aguilera",
        "correo": "sergio.aguilera@medisinc.bo",
        "especialidad": "Traumatología y Urgencias",
        "rol": "MEDICO",
        "turno_asignado": "MADRUGADA",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-cardio-05",
        "usuario_id": "usr-med-05",
        "nombre_completo": "Dr. Roberto Paz",
        "correo": "roberto.paz@medisinc.bo",
        "especialidad": "Cardiología y Medicina Interna",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Lunes", "Miércoles", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-odontologia-06",
        "usuario_id": "usr-med-06",
        "nombre_completo": "Dra. Valeria Cuéllar",
        "correo": "valeria.cuellar@medisinc.bo",
        "especialidad": "Odontología",
        "rol": "MEDICO",
        "turno_asignado": "TARDE_NOCHE",
        "dias_guardia": ["Lunes", "Martes", "Jueves", "Sábado"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    },
    {
        "id": "doc-admin-01",
        "usuario_id": "usr-admin-01",
        "nombre_completo": "Lic. Claudia Justiniano",
        "correo": "claudia.justiniano@medisinc.bo",
        "especialidad": "Administración Hospitalaria",
        "rol": "ADMIN",
        "turno_asignado": "TODOS",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-01T00:00:00Z"
    }
]


class RepositorioMedicosSupabase(IRepositorioMedicos):
    """
    Repositorio para gestión de personal médico y turnos con Supabase.
    """

    def __init__(self, cliente_supabase=None, almacen_fallback: Optional[Dict[str, Any]] = None):
        self._cliente = cliente_supabase
        if almacen_fallback is not None:
            self._fallback = almacen_fallback
        else:
            self._fallback = {m["id"]: dict(m) for m in _MEDICOS_INICIALES}

    async def listar_medicos(
        self,
        rol: Optional[str] = None,
        esta_activo: Optional[bool] = None,
        busqueda: Optional[str] = None
    ) -> List[PerfilMedicoDTO]:
        medicos_raw = []

        if self._cliente:
            try:
                def _consultar():
                    try:
                        consulta = self._cliente.table("perfiles").select("*")
                    except Exception:
                        consulta = self._cliente.table("profiles").select("*")

                    if rol:
                        consulta = consulta.eq("rol", rol.upper())
                    if esta_activo is not None:
                        consulta = consulta.eq("esta_activo", esta_activo)
                    if busqueda:
                        consulta = consulta.ilike("nombre_completo", f"%{busqueda}%")

                    res = consulta.order("creado_en", desc=True).execute()
                    return res.data or []

                medicos_raw = await asyncio.to_thread(_consultar)
            except Exception as e:
                logger.error(f"[RepositorioMedicos] Error listando médicos: {e}")

        if not medicos_raw:
            for p in self._fallback.values():
                if rol and (p.get("rol") != rol.upper() and p.get("role") != rol.upper()):
                    continue
                if esta_activo is not None and (p.get("esta_activo") != esta_activo and p.get("is_active") != esta_activo):
                    continue
                if busqueda:
                    termino = busqueda.lower()
                    nombre = (p.get("nombre_completo") or p.get("full_name") or "").lower()
                    correo = (p.get("correo") or p.get("email") or "").lower()
                    if termino not in nombre and termino not in correo:
                        continue
                medicos_raw.append(p)

        return [PerfilMedicoDTO.model_validate(m) for m in medicos_raw]

    async def obtener_por_id(self, medico_id: str) -> Optional[PerfilMedicoDTO]:
        if self._cliente:
            try:
                def _consultar():
                    try:
                        res = self._cliente.table("perfiles").select("*").eq("id", medico_id).execute()
                    except Exception:
                        res = self._cliente.table("profiles").select("*").eq("id", medico_id).execute()
                    return res.data[0] if res.data else None

                datos = await asyncio.to_thread(_consultar)
                if datos:
                    return PerfilMedicoDTO.model_validate(datos)
            except Exception as e:
                logger.error(f"[RepositorioMedicos] Error consultando médico {medico_id}: {e}")

        if medico_id in self._fallback:
            return PerfilMedicoDTO.model_validate(self._fallback[medico_id])
        return None

    async def crear_medico(self, datos_medico: Dict[str, Any]) -> PerfilMedicoDTO:
        medico_id = datos_medico.get("id") or str(uuid.uuid4())
        ahora = datetime.now(timezone.utc).isoformat()
        datos_completos = {
            **datos_medico,
            "id": medico_id,
            "creado_en": datos_medico.get("creado_en", ahora),
            "actualizado_en": ahora
        }
        self._fallback[medico_id] = datos_completos

        if self._cliente:
            try:
                def _insertar():
                    try:
                        self._cliente.table("perfiles").insert(datos_completos).execute()
                    except Exception:
                        self._cliente.table("profiles").insert(datos_completos).execute()

                await asyncio.to_thread(_insertar)
            except Exception as e:
                logger.error(f"[RepositorioMedicos] Error registrando médico: {e}")

        return PerfilMedicoDTO.model_validate(datos_completos)

    async def actualizar_medico(self, medico_id: str, datos_actualizacion: Dict[str, Any]) -> PerfilMedicoDTO:
        perfil = self._fallback.get(medico_id, {})
        perfil.update(datos_actualizacion)
        perfil["actualizado_en"] = datetime.now(timezone.utc).isoformat()
        self._fallback[medico_id] = perfil

        if self._cliente:
            try:
                def _actualizar():
                    try:
                        self._cliente.table("perfiles").update(datos_actualizacion).eq("id", medico_id).execute()
                    except Exception:
                        self._cliente.table("profiles").update(datos_actualizacion).eq("id", medico_id).execute()

                await asyncio.to_thread(_actualizar)
            except Exception as e:
                logger.error(f"[RepositorioMedicos] Error actualizando médico: {e}")

        return PerfilMedicoDTO.model_validate(perfil)

    async def obtener_medicos_activos_por_especialidad(self) -> Dict[str, List[Dict[str, Any]]]:
        medicos = await self.listar_medicos(esta_activo=True)
        agrupado: Dict[str, List[Dict[str, Any]]] = {}

        for m in medicos:
            esp = m.especialidad or "Medicina General"
            if esp not in agrupado:
                agrupado[esp] = []
            agrupado[esp].append(m.model_dump())

        return agrupado
