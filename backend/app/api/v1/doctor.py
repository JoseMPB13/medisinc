"""
Puente de retrocompatibilidad hacia app.api.v1.medico.
"""

from app.api.v1.medico import (
    router,
    obtener_panel_medico,
    obtener_detalle_paciente,
    registrar_revision_medica
)

__all__ = [
    "router",
    "obtener_panel_medico",
    "obtener_detalle_paciente",
    "registrar_revision_medica"
]
