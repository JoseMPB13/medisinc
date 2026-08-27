"""
Puente de retrocompatibilidad hacia app.core.limite_peticiones.
"""

from app.core.limite_peticiones import (
    verificar_limite_peticiones,
    check_rate_limit,
    _LOCAL_RATE_LIMIT_DB,
    _BD_LOCAL_LIMITE_PETICIONES,
    MAX_REQUESTS_PER_WINDOW,
    LIMITE_PETICIONES_VENTANA,
    WINDOW_SECONDS,
    VENTANA_SEGUNDOS
)

__all__ = [
    "verificar_limite_peticiones",
    "check_rate_limit",
    "_LOCAL_RATE_LIMIT_DB",
    "_BD_LOCAL_LIMITE_PETICIONES",
    "MAX_REQUESTS_PER_WINDOW",
    "LIMITE_PETICIONES_VENTANA",
    "WINDOW_SECONDS",
    "VENTANA_SEGUNDOS"
]
