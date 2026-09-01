"""
Servicio de Cola de Tareas Asíncronas (Upstash Redis y Background Tasks).
Encola solicitudes de triaje para procesamiento diferido mediante API REST de Upstash o FastAPI BackgroundTasks.
"""

import json
import logging
from typing import Dict, Any
import httpx
from fastapi import BackgroundTasks

from app.core.configuracion import configuracion
from app.workers.triage_worker import process_triage_background_task

logger = logging.getLogger(__name__)


class ServicioCola:
    """
    Gestor de colas de tareas con soporte para Upstash Redis REST API y FastAPI BackgroundTasks.
    """

    def __init__(self):
        self.redis_url = configuracion.UPSTASH_REDIS_REST_URL
        self.redis_token = configuracion.UPSTASH_REDIS_REST_TOKEN

    async def encolar_tarea_triaje(
        self,
        triaje_id: str,
        datos_paciente: Dict[str, Any],
        tareas_segundo_plano: BackgroundTasks
    ) -> bool:
        """
        Encola la tarea de procesamiento del triaje. Si Upstash Redis está disponible, realiza un LPUSH REST.
        De lo contrario, encola la tarea en los BackgroundTasks locales de FastAPI.
        """
        datos_trabajo = {
            "triage_id": triaje_id,
            "patient_payload": datos_paciente
        }

        # Intentar encolar en Upstash Redis si la URL y el Token están configurados
        if self.redis_url and self.redis_token and "placeholder" not in self.redis_url:
            try:
                headers = {"Authorization": f"Bearer {self.redis_token}"}
                payload_json = json.dumps(datos_trabajo)
                url = f"{self.redis_url.rstrip('/')}/lpush/medisinc_triage_queue"
                
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, headers=headers, content=payload_json, timeout=5.0)
                    if resp.status_code == 200:
                        logger.info(f"Trabajo encolado en Upstash Redis para triaje ID: {triaje_id}")
                        tareas_segundo_plano.add_task(process_triage_background_task, triaje_id, datos_paciente)
                        return True
            except Exception as e:
                logger.error(f"Error al encolar en Upstash Redis REST API: {e}")

        # Fallback predeterminado: FastAPI BackgroundTasks en segundo plano
        logger.info(f"Encolando tarea en FastAPI BackgroundTasks local para triaje ID: {triaje_id}")
        tareas_segundo_plano.add_task(process_triage_background_task, triaje_id, datos_paciente)
        return True

    # Alias para compatibilidad con código existente
    async def enqueue_triage_job(self, triage_id: str, patient_payload: Dict[str, Any], background_tasks: BackgroundTasks) -> bool:
        return await self.encolar_tarea_triaje(triaje_id=triage_id, datos_paciente=patient_payload, tareas_segundo_plano=background_tasks)


servicio_cola = ServicioCola()
queue_service = servicio_cola
QueueService = ServicioCola
