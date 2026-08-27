"""
Puente de retrocompatibilidad hacia app.api.v1.triaje.
"""

from app.api.v1.triaje import (
    router,
    generar_preguntas_dinamicas_api
)

__all__ = [
    "router",
    "generar_preguntas_dinamicas_api"
]
