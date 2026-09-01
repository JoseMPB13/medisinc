"""
Módulo de Control de Abuso y Límite de Peticiones (Rate Limiting) para MediSinc-IA.
Protege las rutas públicas contra peticiones masivas mediante la IP del cliente.
Implementa almacenamiento acotado en memoria con evicción LRU (Least Recently Used)
para blindar el sistema contra fugas de memoria o ataques de denegación de servicio (DoS).
"""

import time
import logging
import asyncio
from collections import OrderedDict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
import httpx

from app.core.configuracion import configuracion, settings

logger = logging.getLogger(__name__)

# Configuración del límite: 5 peticiones por ventana de 300 segundos (5 minutos)
MAX_REQUESTS_PER_WINDOW = configuracion.RATE_LIMIT_REQUESTS
LIMITE_PETICIONES_VENTANA = configuracion.RATE_LIMIT_REQUESTS
WINDOW_SECONDS = configuracion.RATE_LIMIT_MINUTES * 60
VENTANA_SEGUNDOS = configuracion.RATE_LIMIT_MINUTES * 60


class RateLimiterMemoria:
    """
    Controlador de tasa en memoria con límite acotado de capacidad y política de evicción LRU.
    Garantiza que la estructura no crezca indefinidamente ante ráfagas de IPs rotativas.
    """

    def __init__(
        self,
        capacidad_maxima: int = 10000,
        ventana_segundos: int = 300,
        limite_maximo: int = 5
    ):
        self.capacidad_maxima = capacidad_maxima
        self.ventana_segundos = ventana_segundos
        self.limite_maximo = limite_maximo
        self._almacen: OrderedDict[str, List[float]] = OrderedDict()
        self._candado = asyncio.Lock()

    async def registrar_y_validar(
        self,
        clave_ip: str,
        limite_personalizado: Optional[int] = None
    ) -> bool:
        """
        Registra el intento de solicitud para la IP indicada y valida si está dentro del umbral.

        Retorna:
            bool: True si la petición es admitida, False si superó la cuota permitida.
        """
        limite = limite_personalizado if limite_personalizado is not None else self.limite_maximo
        ahora = time.time()

        async with self._candado:
            if clave_ip in self._almacen:
                # Marcar como recientemente usada moviéndola al final
                self._almacen.move_to_end(clave_ip)
                historial = [t for t in self._almacen[clave_ip] if ahora - t < self.ventana_segundos]
            else:
                # Si se alcanza el tope de capacidad, expulsar la entrada más antigua (LRU)
                if len(self._almacen) >= self.capacidad_maxima:
                    self._almacen.popitem(last=False)
                historial = []

            if len(historial) >= limite:
                self._almacen[clave_ip] = historial
                return False

            historial.append(ahora)
            self._almacen[clave_ip] = historial
            return True

    def limpiar(self) -> None:
        """Limpia el almacenamiento en memoria (utilizado para aislar pruebas)."""
        self._almacen.clear()

    @property
    def total_ips_registradas(self) -> int:
        """Retorna el número de IPs activas almacenadas."""
        return len(self._almacen)


# Instancia global del limitador en memoria
limiter_memoria_global = RateLimiterMemoria(
    capacidad_maxima=10000,
    ventana_segundos=VENTANA_SEGUNDOS,
    limite_maximo=LIMITE_PETICIONES_VENTANA
)

# Alias de compatibilidad
_LOCAL_RATE_LIMIT_DB = limiter_memoria_global._almacen
_BD_LOCAL_LIMITE_PETICIONES = _LOCAL_RATE_LIMIT_DB


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
            logger.error(f"[RateLimit] Error consultando Upstash Redis: {e}. Usando contador local acotado.")

    # 2. Contador en Memoria Local Acotado con LRU (Fallback Resiliente)
    admitido = await limiter_memoria_global.registrar_y_validar(ip_cliente)
    if not admitido:
        logger.warning(f"[RateLimit] IP {ip_cliente} excedió el límite local.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de solicitudes excedido. Se permite un máximo de 5 peticiones cada 5 minutos por dirección IP."
        )


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
check_rate_limit = verificar_limite_peticiones
