"""
Módulo Principal de la Aplicación MediSinc-IA Backend (FastAPI).
Inicializa el servidor, configura CORS y expone la API v1 de triaje y verificación.
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import encrypt_ci, hash_ci, generate_access_code
from app.schemas.triage import PatientInputSchema, TriageResponseSchema
from app.providers.ai_factory import get_ai_provider
from app.services.rules_engine import evaluate_safety_overrides

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="MediSinc-IA API",
    description="API de Pre-Triaje Clínico e Inteligencia de Salud",
    version="1.0.0"
)

# Configuración Middleware CORS para permitir solicitudes desde el Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint de bienvenida e información del servicio.
    """
    return {
        "app": "MediSinc-IA Backend",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Endpoint de diagnóstico para verificar el estado de la API y la configuración de entorno.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "ai_provider": settings.AI_PROVIDER,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post(
    "/api/v1/triage/process",
    response_model=TriageResponseSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Triage"]
)
async def process_triage(patient_input: PatientInputSchema):
    """
    Procesa la captura de un paciente:
    1. Genera código único de acceso (ej. MS-8X92K).
    2. Cifra el Carnet de Identidad con AES-256 y genera su hash HMAC-SHA256.
    3. Invoca la capa agnóstica de IA (Gemini, Groq o OpenAI).
    4. Aplica el motor de reglas duras de seguridad (Safety Overrides).
    5. Consolida y retorna el resumen de triaje al Frontend.
    """
    try:
        # 1. Cifrado y Hashing de seguridad del CI
        ci_encrypted = encrypt_ci(patient_input.ci)
        ci_hashed = hash_ci(patient_input.ci)
        access_code = generate_access_code()

        # 2. Invocación a la Capa de IA Agnóstica
        ai_provider = get_ai_provider()
        ai_output = await ai_provider.process_triage(patient_input.model_dump())

        # 3. Evaluación del Motor de Reglas Duras de Seguridad (Safety Override)
        final_priority, override_applied, override_reason = evaluate_safety_overrides(
            raw_symptoms=patient_input.raw_symptoms,
            age=patient_input.age,
            static_data=patient_input.static_data,
            ai_output=ai_output
        )

        # 4. Formatear respuesta final para el cliente
        created_at_iso = datetime.utcnow().isoformat()

        response_data = TriageResponseSchema(
            access_code=access_code,
            status="READY",
            final_priority=final_priority,
            override_applied=override_applied,
            override_reason=override_reason,
            ai_result=ai_output,
            created_at=created_at_iso
        )

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando el triaje: {str(e)}"
        )
