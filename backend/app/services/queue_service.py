"""
Servicio de Cola de Tareas Asíncronas (Upstash Redis & Background Tasks).
Encola solicitudes de triaje para procesamiento diferido mediante API REST de Upstash o FastAPI BackgroundTasks.
"""

import json
import logging
from typing import Dict, Any
import httpx
from fastapi import BackgroundTasks

from app.core.config import settings
from app.workers.triage_worker import process_triage_background_task

logger = logging.getLogger(__name__)


class QueueService:
    """
    Gestor de colas de tareas con soporte para Upstash Redis REST API y FastAPI BackgroundTasks.
    """

    def __init__(self):
        self.redis_url = settings.UPSTASH_REDIS_REST_URL
        self.redis_token = settings.UPSTASH_REDIS_REST_TOKEN

    async def enqueue_triage_job(
        self,
        triage_id: str,
        patient_payload: Dict[str, Any],
        background_tasks: BackgroundTasks
    ) -> bool:
        """
        Encola la tarea de procesamiento del triaje. Si Upstash Redis está disponible, realiza un LPUSH REST.
        De lo contrario, encola la tarea en los BackgroundTasks locales de FastAPI.
        """
        job_data = {
            "triage_id": triage_id,
            "patient_payload": patient_payload
        }

        # Intentar encolar en Upstash Redis si la URL y el Token están configurados
        if self.redis_url and self.redis_token and "placeholder" not in self.redis_url:
            try:
                headers = {"Authorization": f"Bearer {self.redis_token}"}
                payload_json = json.dumps(job_data)
                # Comando LPUSH medisinc_triage_queue <payload_json>
                url = f"{self.redis_url.rstrip('/')}/lpush/medisinc_triage_queue"
                
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, headers=headers, content=payload_json, timeout=5.0)
                    if resp.status_code == 200:
                        logger.info(f"Trabajo encolado en Upstash Redis para triaje ID: {triage_id}")
                        # Ejecutar también el worker en segundo plano para procesarlo inmediatamente
                        background_tasks.add_task(process_triage_background_task, triage_id, patient_payload)
                        return True
            except Exception as e:
                logger.error(f"Error al encolar en Upstash Redis REST API: {e}")

        # Fallback predeterminado: FastAPI BackgroundTasks en segundo plano
        logger.info(f"Encolando tarea en FastAPI BackgroundTasks local para triaje ID: {triage_id}")
        background_tasks.add_task(process_triage_background_task, triage_id, patient_payload)
        return True


queue_service = QueueService()
