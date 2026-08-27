"""
Módulo de Control de Abuso y Límite de Peticiones (Rate Limiting) para MediSinc-IA.
Protege las rutas públicas contra peticiones masivas mediante la IP del cliente
con Upstash Redis o contador en memoria local como fallback resiliente.
"""

import time
import logging
from typing import Dict, List
from fastapi import Request, HTTPException, status
import httpx

from app.core.configuracion import configuracion, settings

logger = logging.getLogger(__name__)

# Base de datos en memoria local para el contador por IP: {ip: [timestamps]}
_LOCAL_RATE_LIMIT_DB: Dict[str, list] = {}
_BD_LOCAL_LIMITE_PETICIONES = _LOCAL_RATE_LIMIT_DB

# Configuración del límite: 5 peticiones por ventana de 300 segundos (5 minutos)
MAX_REQUESTS_PER_WINDOW = configuracion.RATE_LIMIT_REQUESTS
LIMITE_PETICIONES_VENTANA = configuracion.RATE_LIMIT_REQUESTS
WINDOW_SECONDS = configuracion.RATE_LIMIT_MINUTES * 60
VENTANA_SEGUNDOS = configuracion.RATE_LIMIT_MINUTES * 60


async def verificar_limite_peticiones(request: Request):
    """
    Middleware / Dependencia de FastAPI para verificar si la IP del cliente ha superado el límite permitido.

    Entrada:
        request (Request): Objeto de la petición entrante.
    Lanza:
        HTTPException(429): Si se superan las 5 peticiones en una ventana de 5 minutos.
    """
    ip_cliente = request.client.host if request.client else "127.0.0.1"
    encabezado_reenvio = request.headers.get("X-Forwarded-For")
    if encabezado_reenvio:
        ip_cliente = encabezado_reenvio.split(",")[0].strip()

    ahora = time.time()

    # 1. Verificación en Upstash Redis REST API si está configurado
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN and "placeholder" not in settings.UPSTASH_REDIS_REST_URL:
        try:
            clave_redis = f"limite_peticiones:{ip_cliente}"
            encabezados = {"Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"}

            async with httpx.AsyncClient() as cliente_http:
                url_incr = f"{settings.UPSTASH_REDIS_REST_URL.rstrip('/')}/incr/{clave_redis}"
                resp_incr = await cliente_http.post(url_incr, headers=encabezados, timeout=3.0)

                if resp_incr.status_code == 200:
                    conteo_actual = resp_incr.json().get("result", 1)
                    if conteo_actual == 1:
                        url_expire = f"{settings.UPSTASH_REDIS_REST_URL.rstrip('/')}/expire/{clave_redis}/{VENTANA_SEGUNDOS}"
                        await cliente_http.post(url_expire, headers=encabezados, timeout=3.0)

                    if conteo_actual > LIMITE_PETICIONES_VENTANA:
                        logger.warning(f"[RateLimit] IP {ip_cliente} excedió el límite en Redis ({conteo_actual}/{LIMITE_PETICIONES_VENTANA})")
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
    marcas_tiempo = _LOCAL_RATE_LIMIT_DB.get(ip_cliente, [])
    # Filtrar marcas de tiempo que estén dentro de la ventana de 5 minutos
    marcas_validas = [t for t in marcas_tiempo if ahora - t < VENTANA_SEGUNDOS]

    if len(marcas_validas) >= LIMITE_PETICIONES_VENTANA:
        logger.warning(f"[RateLimit] IP {ip_cliente} excedió el límite local ({len(marcas_validas)}/{LIMITE_PETICIONES_VENTANA})")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de solicitudes excedido. Se permite un máximo de 5 peticiones cada 5 minutos por dirección IP."
        )

    marcas_validas.append(ahora)
    _LOCAL_RATE_LIMIT_DB[ip_cliente] = marcas_validas


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
check_rate_limit = verificar_limite_peticiones
