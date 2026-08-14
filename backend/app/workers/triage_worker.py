"""
Worker de Procesamiento Asíncrono de Triaje (Background Task Worker).
Procesa en segundo plano el análisis del modelo de IA, aplica el motor de reglas de seguridad
y actualiza el estado en Supabase con política de reintentos.
"""

import asyncio
import logging
from typing import Dict, Any

from app.providers.ai_factory import get_ai_provider
from app.services.rules_engine import evaluate_safety_overrides
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


async def process_triage_background_task(triage_id: str, patient_payload: Dict[str, Any]):
    """
    Tarea asíncrona de segundo plano para procesar la evaluación de IA de un registro de triaje.

    Entrada:
        triage_id (str) - ID único del registro de triaje.
        patient_payload (dict) - Datos estructurados del paciente (síntomas, edad, género, etc.).
    """
    max_retries = 3
    retry_delay = 2  # segundos

    logger.info(f"[Worker] Iniciando procesamiento asíncrono para triaje ID: {triage_id}")

    for attempt in range(1, max_retries + 1):
        try:
            # 1. Invocación al Proveedor de IA (Gemini, Groq u OpenAI)
            ai_provider = get_ai_provider()
            ai_output = await ai_provider.process_triage(patient_payload)

            # 2. Evaluación del Motor de Reglas Duras de Seguridad
            final_priority, override_applied, override_reason = evaluate_safety_overrides(
                raw_symptoms=patient_payload.get("raw_symptoms", ""),
                age=patient_payload.get("age", 0),
                static_data=patient_payload.get("static_data", {}),
                ai_output=ai_output
            )

            # 3. Persistencia en Supabase: Guardar AI_RESULT y actualizar estado a 'READY'
            ai_result_dict = ai_output.model_dump()
            success = supabase_service.update_triage_with_ai_result(
                triage_id=triage_id,
                ai_result=ai_result_dict,
                final_priority=final_priority,
                override_applied=override_applied,
                override_reason=override_reason
            )

            if success:
                logger.info(f"[Worker] Triaje ID {triage_id} procesado exitosamente. Prioridad final: {final_priority} (Override: {override_applied})")
                return
            else:
                logger.warning(f"[Worker] Intento {attempt}: Error guardando resultado en Supabase para triaje ID {triage_id}")

        except Exception as e:
            logger.error(f"[Worker] Intento {attempt}/{max_retries} falló para triaje ID {triage_id}: {e}")

        if attempt < max_retries:
            await asyncio.sleep(retry_delay * attempt)

    logger.critical(f"[Worker] Se agotaron los {max_retries} intentos para procesar el triaje ID {triage_id}")
