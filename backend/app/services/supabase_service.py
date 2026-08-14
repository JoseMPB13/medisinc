"""
Servicio de Persistencia con Supabase (PostgreSQL).
Proporciona métodos para interactuar con la base de datos de MediSinc-IA
utilizando el Service Role Key con el SDK oficial de Supabase.
"""

import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Memoria en almacenamiento local (Fallback si Supabase no tiene credenciales válidas en desarrollo)
_IN_MEMORY_TRIAGE_DB: Dict[str, Dict[str, Any]] = {}
_IN_MEMORY_AI_DB: Dict[str, Dict[str, Any]] = {}


class SupabaseService:
    """
    Cliente encapsulado de Supabase para operaciones de lectura/escritura en la BD.
    """

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.client: Optional[Client] = None

        if self.url and "placeholder" not in self.url and self.key and "placeholder" not in self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Cliente Supabase inicializado correctamente")
            except Exception as e:
                logger.error(f"Error al conectar con Supabase SDK: {e}")
                self.client = None
        else:
            logger.warning("Supabase URL/Key sin configurar o en modo placeholder. Se utilizará almacenamiento local de contingencia.")
            self.client = None

    def create_triage_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un nuevo registro de triaje con estado inicial 'RECEIVED'.

        Entrada: data (dict) - Campos de TRIAGE_RECORD.
        Salida: dict - Registro creado en la base de datos.
        """
        record_payload = {
            "access_code": data.get("access_code"),
            "ci_hash": data.get("ci_hash"),
            "ci_encrypted": data.get("ci_encrypted"),
            "patient_name": data.get("patient_name"),
            "age": data.get("age"),
            "gender": data.get("gender"),
            "raw_symptoms": data.get("raw_symptoms"),
            "static_data": data.get("static_data", {}),
            "dynamic_answers": data.get("dynamic_answers", {}),
            "status": "RECEIVED",
            "final_priority": data.get("final_priority")
        }

        if self.client:
            try:
                response = self.client.table("TRIAGE_RECORD").insert(record_payload).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                logger.error(f"Error al insertar registro en Supabase TRIAGE_RECORD: {e}")

        # Fallback local de desarrollo
        triage_id = data.get("id") or f"local-id-{data.get('access_code')}"
        record_payload["id"] = triage_id
        record_payload["created_at"] = "2026-08-13T20:00:00Z"
        _IN_MEMORY_TRIAGE_DB[triage_id] = record_payload
        _IN_MEMORY_TRIAGE_DB[data.get("access_code")] = record_payload
        return record_payload

    def update_triage_with_ai_result(
        self,
        triage_id: str,
        ai_result: Dict[str, Any],
        final_priority: str,
        override_applied: bool,
        override_reason: Optional[str]
    ) -> bool:
        """
        Guarda la salida del resumen de IA en AI_RESULT y actualiza el estado de TRIAGE_RECORD a 'READY'.
        """
        ai_payload = {
            "triage_id": triage_id,
            "provider": settings.AI_PROVIDER,
            "model": "auto-selected-model",
            "structured_result": ai_result,
            "override_applied": override_applied,
            "override_reason": override_reason
        }

        if self.client:
            try:
                # 1. Insertar en AI_RESULT
                self.client.table("AI_RESULT").insert(ai_payload).execute()
                # 2. Actualizar estado y prioridad en TRIAGE_RECORD
                self.client.table("TRIAGE_RECORD").update({
                    "status": "READY",
                    "final_priority": final_priority
                }).eq("id", triage_id).execute()
                return True
            except Exception as e:
                logger.error(f"Error al actualizar AI_RESULT en Supabase: {e}")

        # Fallback local
        _IN_MEMORY_AI_DB[triage_id] = ai_payload
        if triage_id in _IN_MEMORY_TRIAGE_DB:
            _IN_MEMORY_TRIAGE_DB[triage_id]["status"] = "READY"
            _IN_MEMORY_TRIAGE_DB[triage_id]["final_priority"] = final_priority
            _IN_MEMORY_TRIAGE_DB[triage_id]["ai_result"] = ai_payload
        return True

    def get_triage_by_code_or_hash(
        self,
        access_code: Optional[str] = None,
        ci_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un registro de triaje por código alfanumérico (ej. MS-8X92K) o por hash del CI.
        """
        if self.client:
            try:
                query = self.client.table("TRIAGE_RECORD").select("*, AI_RESULT(*)")
                if access_code:
                    query = query.eq("access_code", access_code)
                elif ci_hash:
                    query = query.eq("ci_hash", ci_hash)
                else:
                    return None

                response = query.execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            except Exception as e:
                logger.error(f"Error al consultar triaje en Supabase: {e}")

        # Fallback local
        if access_code and access_code in _IN_MEMORY_TRIAGE_DB:
            rec = _IN_MEMORY_TRIAGE_DB[access_code]
            rec["AI_RESULT"] = _IN_MEMORY_AI_DB.get(rec.get("id"))
            return rec
        return None


# Instancia global del servicio Supabase
supabase_service = SupabaseService()
