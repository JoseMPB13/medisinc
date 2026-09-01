"""
Implementación Concreta del Repositorio de Bitácora de Auditoría con Supabase.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.repositorios.base import IRepositorioAuditoria
from app.esquemas.dominio import EventoAuditoriaDTO

logger = logging.getLogger(__name__)


class RepositorioAuditoriaSupabase(IRepositorioAuditoria):
    """
    Repositorio para el registro inmutable y consulta de auditoría de eventos.
    """

    def __init__(self, cliente_supabase=None, almacen_fallback: Optional[List[Dict[str, Any]]] = None):
        self._cliente = cliente_supabase
        self._fallback = almacen_fallback if almacen_fallback is not None else []

    async def registrar_evento(
        self,
        usuario_id: str,
        accion: str,
        recurso_id: Optional[str] = None,
        direccion_ip: str = "127.0.0.1"
    ) -> EventoAuditoriaDTO:
        evento_id = str(uuid.uuid4())
        fecha_hora = datetime.now(timezone.utc).isoformat()

        evento = {
            "id": evento_id,
            "usuario_id": usuario_id or "SISTEMA",
            "user_id": usuario_id or "SISTEMA",
            "accion": accion,
            "action": accion,
            "recurso_id": recurso_id,
            "resource_id": recurso_id,
            "direccion_ip": direccion_ip,
            "ip_address": direccion_ip,
            "fecha_hora": fecha_hora,
            "timestamp": fecha_hora
        }

        self._fallback.append(evento)

        if self._cliente:
            try:
                def _insertar():
                    try:
                        self._cliente.table("registros_auditoria").insert(evento).execute()
                    except Exception:
                        self._cliente.table("audit_log").insert(evento).execute()

                await asyncio.to_thread(_insertar)
            except Exception as e:
                logger.warning(f"[RepositorioAuditoria] Error insertando evento de auditoría: {e}")

        return EventoAuditoriaDTO.model_validate(evento)

    async def listar_eventos(
        self,
        limite: int = 50,
        accion: Optional[str] = None
    ) -> List[EventoAuditoriaDTO]:
        eventos_raw = []

        if self._cliente:
            try:
                def _consultar():
                    try:
                        consulta = self._cliente.table("registros_auditoria").select("*")
                    except Exception:
                        consulta = self._cliente.table("audit_log").select("*")

                    if accion:
                        consulta = consulta.eq("accion", accion)

                    res = consulta.order("fecha_hora", desc=True).limit(limite).execute()
                    return res.data or []

                eventos_raw = await asyncio.to_thread(_consultar)
            except Exception as e:
                logger.error(f"[RepositorioAuditoria] Error consultando auditoría: {e}")

        if not eventos_raw:
            fuente = list(reversed(self._fallback))
            if accion:
                fuente = [e for e in fuente if e.get("accion") == accion or e.get("action") == accion]
            eventos_raw = fuente[:limite]

        return [EventoAuditoriaDTO.model_validate(e) for e in eventos_raw]
