"""
Router de Endpoints de Triaje Clínico API v1.
Maneja la recepción inmediata de datos del paciente, encolamiento asíncrono,
consulta de estado y búsqueda para médicos por código de acceso o CI hash.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.core.security import encrypt_ci, hash_ci, generate_access_code
from app.schemas.triage import PatientInputSchema, AIStructuredOutput, TriageResponseSchema
from app.services.supabase_service import supabase_service
from app.services.queue_service import queue_service

router = APIRouter(prefix="/triage", tags=["Triaje Clínico"])


class ImmediateTriageResponseSchema(BaseModel):
    """
    Respuesta de confirmación inmediata devuelta al paciente tras guardar su registro inicial.
    """
    triage_id: str = Field(..., description="ID único del registro de triaje")
    access_code: str = Field(..., description="Código corto alfanumérico generado (ej. MS-8X92K)")
    status: str = Field("RECEIVED", description="Estado inicial del registro ('RECEIVED')")
    patient_name: str
    message: str = Field("Pre-triaje capturado exitosamente. Procesando análisis sintomático...", description="Mensaje informativo para el usuario")
    created_at: str


@router.post(
    "/process",
    response_model=ImmediateTriageResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def process_triage(
    patient_input: PatientInputSchema,
    background_tasks: BackgroundTasks
):
    """
    Endpoint Público de Ingreso de Paciente (Paso 3 del Formulario):
    1. Genera código único de acceso (ej. MS-8X92K).
    2. Cifra el CI (AES-256) y genera hash HMAC-SHA256.
    3. Registra en Supabase con estado 'RECEIVED'.
    4. Encola la tarea asíncrona en Redis / BackgroundTasks para procesamiento por IA.
    5. Responde INMEDIATAMENTE al paciente para renderizado del Código QR sin demoras de red.
    """
    try:
        # 1. Cifrado y Hashing de seguridad del CI
        ci_encrypted = encrypt_ci(patient_input.ci)
        ci_hashed = hash_ci(patient_input.ci)
        access_code = generate_access_code()

        # Payload para persistencia inicial
        input_dict = patient_input.model_dump()
        triage_id = f"tr-{access_code.lower()}"

        record_data = {
            "id": triage_id,
            "access_code": access_code,
            "ci_hash": ci_hashed,
            "ci_encrypted": ci_encrypted,
            "patient_name": patient_input.patient_name,
            "age": patient_input.age,
            "gender": patient_input.gender,
            "raw_symptoms": patient_input.raw_symptoms,
            "static_data": patient_input.static_data,
            "dynamic_answers": patient_input.dynamic_answers,
            "status": "RECEIVED",
            "final_priority": None
        }

        # 2. Guardar registro inicial en Supabase
        db_record = supabase_service.create_triage_record(record_data)
        saved_id = db_record.get("id", triage_id)

        # 3. Encolar tarea asíncrona para evaluación de IA y Motor de Reglas
        await queue_service.enqueue_triage_job(
            triage_id=saved_id,
            patient_payload=input_dict,
            background_tasks=background_tasks
        )

        # 4. Respuesta Inmediata al paciente
        return ImmediateTriageResponseSchema(
            triage_id=saved_id,
            access_code=access_code,
            status="RECEIVED",
            patient_name=patient_input.patient_name,
            message="Pre-triaje registrado exitosamente. Tu resumen clínico se encuentra en procesamiento.",
            created_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el pre-triaje: {str(e)}"
        )


@router.get(
    "/status/{identifier}",
    tags=["Triaje Clínico"]
)
async def get_triage_status(identifier: str):
    """
    Consulta el estado y resultado de un registro de triaje mediante su access_code (ej. MS-8X92K) o ID.
    Permite al paciente o médico verificar cuando el estado cambia de 'RECEIVED' a 'READY'.
    """
    record = supabase_service.get_triage_by_code_or_hash(access_code=identifier)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún registro con el código de acceso '{identifier}'"
        )
    return record


@router.get(
    "/lookup",
    tags=["Portal Médico"]
)
async def lookup_triage_for_doctor(
    access_code: Optional[str] = Query(None, description="Código de acceso (MS-8X92K)"),
    ci: Optional[str] = Query(None, description="Carnet de Identidad del paciente")
):
    """
    Búsqueda de registros para médicos autenticados por Código de Acceso o por Carnet de Identidad.
    """
    if not access_code and not ci:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar un código de acceso ('access_code') o un Carnet de Identidad ('ci')"
        )

    ci_hashed = hash_ci(ci) if ci else None
    record = supabase_service.get_triage_by_code_or_hash(access_code=access_code, ci_hash=ci_hashed)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró ningún registro para el criterio de búsqueda ingresado"
        )
    return record
