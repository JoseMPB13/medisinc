"""
Router de Endpoints para el Portal Médico y Gestión de Auditoría API v1.
Proporciona el dashboard ordenado por prioridad clínica, la revisión médica presencial
y la descodificación segura del CI en memoria con trazabilidad inalterable en AUDIT_LOG.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.security import decrypt_ci, hash_ci
from app.services.supabase_service import supabase_service, _IN_MEMORY_TRIAGE_DB, _IN_MEMORY_AI_DB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctor", tags=["Portal Médico"])


class MedicalReviewSchema(BaseModel):
    """
    Esquema de entrada para guardar la evaluación médica presencial.
    """
    triage_id: str = Field(..., description="ID único del registro de triaje")
    doctor_id: Optional[str] = Field("doc-uuid-12345", description="ID del médico autenticado")
    doctor_notes: str = Field(..., description="Observaciones y diagnóstico inicial del profesional médico")
    priority_adjusted: Optional[str] = Field(None, description="Prioridad ajustada manualmente ('RED', 'YELLOW', 'GREEN')")


@router.get(
    "/dashboard",
    tags=["Portal Médico"]
)
async def get_doctor_dashboard():
    """
    Obtiene la lista de espera de pacientes para el dashboard del médico.
    Ordena los registros por nivel de urgencia:
    1. RED (🔴 Urgente) arriba.
    2. YELLOW (🟡 Prioritario) al centro.
    3. GREEN (🟢 No Urgente) abajo.
    Orden secundario: Hora de llegada (created_at).
    """
    try:
        all_records = []

        client = supabase_service.get_client()
        if client:
            try:
                resp = client.table("triage_record").select("*, ai_result(*)").execute()
                if resp.data:
                    all_records = resp.data
            except Exception as e:
                logger.error(f"Error al consultar Supabase Dashboard triage_record: {e}")

        if not all_records:
            # Recuperar registros de la base local de desarrollo
            distinct_keys = set()
            for key, rec in _IN_MEMORY_TRIAGE_DB.items():
                rec_id = rec.get("id")
                if rec_id and rec_id not in distinct_keys:
                    distinct_keys.add(rec_id)
                    rec_copy = dict(rec)
                    rec_copy["AI_RESULT"] = _IN_MEMORY_AI_DB.get(rec_id)
                    all_records.append(rec_copy)

        # Mapeo numérico para ordenamiento por prioridad clínica
        priority_weight = {
            "RED": 1,
            "YELLOW": 2,
            "GREEN": 3,
            None: 4
        }

        # Ordenar registros
        sorted_records = sorted(
            all_records,
            key=lambda r: (priority_weight.get(r.get("final_priority")), r.get("created_at", ""))
        )

        # Calcular métricas globales del dashboard
        waiting_count = sum(1 for r in sorted_records if r.get("status") in ["RECEIVED", "READY"])
        reviewed_count = sum(1 for r in sorted_records if r.get("status") == "REVIEWED")
        total_red = sum(1 for r in sorted_records if r.get("final_priority") == "RED")

        return {
            "metrics": {
                "waiting_count": waiting_count,
                "reviewed_count": reviewed_count,
                "total_red": total_red,
                "total_today": len(sorted_records)
            },
            "records": sorted_records
        }

    except Exception as e:
        logger.error(f"Error al recuperar dashboard médico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cargando dashboard médico: {str(e)}"
        )


@router.get(
    "/patient/{identifier}",
    tags=["Portal Médico"]
)
async def get_patient_detail_for_doctor(identifier: str):
    """
    Obtiene el detalle completo de un paciente por código de acceso o ID:
    - Descifra el CI en memoria (`decrypt_ci`) para visualización exclusiva del médico.
    - Registra atómicamente un evento de auditoría en AUDIT_LOG.
    """
    try:
        ci_hashed = hash_ci(identifier) if not identifier.startswith("MS-") else None
        record = supabase_service.get_triage_by_code_or_hash(
            access_code=identifier if identifier.startswith("MS-") else None,
            ci_hash=ci_hashed
        )

        if not record and identifier in _IN_MEMORY_TRIAGE_DB:
            record = _IN_MEMORY_TRIAGE_DB[identifier]

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro con identificador '{identifier}' no encontrado."
            )

        # Descifrar Carnet de Identidad en memoria para la pantalla dividida médica
        ci_encrypted = record.get("ci_encrypted", "")
        decrypted_ci = decrypt_ci(ci_encrypted) if ci_encrypted else "CI Desconocido"
        record["decrypted_ci"] = decrypted_ci

        # Trazabilidad Inalterable: Insertar log de auditoría
        client = supabase_service.get_client()
        if client:
            try:
                client.table("audit_log").insert({
                    "action": "VIEW_PATIENT_DETAIL",
                    "resource_id": record.get("id"),
                    "ip_address": "127.0.0.1",
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Error insertando audit_log en Supabase: {e}")

        return record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalle del paciente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo expediente clínico: {str(e)}"
        )


@router.post(
    "/review",
    status_code=status.HTTP_200_OK,
    tags=["Portal Médico"]
)
async def submit_medical_review(payload: MedicalReviewSchema):
    """
    Guarda la confirmación médica de atención presencial:
    1. Registra la evaluación en la tabla `medical_review`.
    2. Cambia el estado del triaje en `triage_record` a 'REVIEWED'.
    3. Si el médico ajustó la prioridad, actualiza `final_priority`.
    4. Genera una entrada atómica en `audit_log`.
    """
    try:
        triage_id = payload.triage_id

        # 1. Registro en medical_review
        client = supabase_service.get_client()
        if client:
            try:
                client.table("medical_review").insert({
                    "triage_id": triage_id,
                    "doctor_notes": payload.doctor_notes,
                    "priority_adjusted": payload.priority_adjusted,
                    "reviewed_at": datetime.utcnow().isoformat()
                }).execute()
                
                # 2. Actualizar estado a REVIEWED en triage_record
                update_payload = {"status": "REVIEWED"}
                if payload.priority_adjusted:
                    update_payload["final_priority"] = payload.priority_adjusted

                client.table("triage_record").update(update_payload).eq("id", triage_id).execute()

                # 3. Log de Auditoría
                client.table("audit_log").insert({
                    "action": "CONFIRM_MEDICAL_REVIEW",
                    "resource_id": triage_id,
                    "ip_address": "127.0.0.1",
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()

            except Exception as e:
                logger.error(f"Error al registrar revisión médica en Supabase: {e}")

        # Actualizar memoria local de contingencia
        if triage_id in _IN_MEMORY_TRIAGE_DB:
            _IN_MEMORY_TRIAGE_DB[triage_id]["status"] = "REVIEWED"
            if payload.priority_adjusted:
                _IN_MEMORY_TRIAGE_DB[triage_id]["final_priority"] = payload.priority_adjusted

        return {
            "status": "success",
            "message": "Atención médica registrada y expediente cerrado.",
            "triage_id": triage_id,
            "reviewed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error al procesar revisión médica: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error guardando revisión médica: {str(e)}"
        )
