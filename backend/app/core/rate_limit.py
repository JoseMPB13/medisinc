"""
Módulo de Control de Abuso y Rate Limiting para MediSinc-IA Backend.
Protege las rutas públicas contra peticiones masivas utilizando la IP del cliente
con Upstash Redis o contador en memoria local como fallback.
"""

import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Memoria local para contar peticiones por IP en entorno de desarrollo: {ip: [timestamps]}
_LOCAL_RATE_LIMIT_DB: Dict[str, list] = {}

# Configuración del límite: Máximo 5 peticiones por ventana de 300 segundos (5 minutos)
MAX_REQUESTS_PER_WINDOW = 5
WINDOW_SECONDS = 300


async def check_rate_limit(request: Request):
    """
    Middleware / Dependencia de FastAPI para verificar si la IP del cliente ha superado el límite.

    Entrada: request (Request) - Objeto de la petición entrante.
    Lanza: HTTPException(429) si se superan las 5 peticiones por cada 5 minutos.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    header_forwarded = request.headers.get("X-Forwarded-For")
    if header_forwarded:
        client_ip = header_forwarded.split(",")[0].strip()

    now = time.time()

    # 1. Verificar si Upstash Redis REST API está disponible
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN and "placeholder" not in settings.UPSTASH_REDIS_REST_URL:
        try:
            redis_key = f"rate_limit:{client_ip}"
            headers = {"Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"}

            async with httpx.AsyncClient() as client:
                # Incrementar contador
                incr_url = f"{settings.UPSTASH_REDIS_REST_URL.rstrip('/')}/incr/{redis_key}"
                resp_incr = await client.post(incr_url, headers=headers, timeout=3.0)
                
                if resp_incr.status_code == 200:
                    current_count = resp_incr.json().get("result", 1)
                    if current_count == 1:
                        # Establecer TTL de 300 segundos en el primer incremento
                        expire_url = f"{settings.UPSTASH_REDIS_REST_URL.rstrip('/')}/expire/{redis_key}/{WINDOW_SECONDS}"
                        await client.post(expire_url, headers=headers, timeout=3.0)

                    if current_count > MAX_REQUESTS_PER_WINDOW:
                        logger.warning(f"[RateLimit] IP {client_ip} excedió el límite en Upstash Redis ({current_count}/{MAX_REQUESTS_PER_WINDOW})")
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Límite de solicitudes excedido. Se permite un máximo de 5 peticiones cada 5 minutos por dirección IP."
                        )
                    return
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[RateLimit] Error consultando Upstash Redis: {e}. Usando contador local.")

    # 2. Contador en Memoria Local (Fallback)
    timestamps = _LOCAL_RATE_LIMIT_DB.get(client_ip, [])
    # Filtrar timestamps que estén dentro de la ventana de 5 minutos
    valid_timestamps = [t for t in timestamps if now - t < WINDOW_SECONDS]

    if len(valid_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning(f"[RateLimit] IP {client_ip} excedió el límite local ({len(valid_timestamps)}/{MAX_REQUESTS_PER_WINDOW})")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de solicitudes excedido. Se permite un máximo de 5 peticiones cada 5 minutos por dirección IP."
        )

    valid_timestamps.append(now)
    _LOCAL_RATE_LIMIT_DB[client_ip] = valid_timestamps
