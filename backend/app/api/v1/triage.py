"""
Puente de retrocompatibilidad hacia app.api.v1.triaje.
"""

from app.api.v1.triaje import (
    router,
    procesar_triaje,
    consultar_estado_triaje,
    buscar_triaje,
    generar_preguntas_dinamicas_api
)

__all__ = [
    "router",
    "procesar_triaje",
    "consultar_estado_triaje",
    "buscar_triaje",
    "generar_preguntas_dinamicas_api"
]
