"""
Puente de retrocompatibilidad hacia app.api.v1.administracion.
"""

from app.api.v1.administracion import (
    router,
    obtener_estadisticas_admin,
    listar_medicos,
    crear_medico,
    actualizar_medico,
    listar_pacientes_historico,
    listar_registros_auditoria
)

__all__ = [
    "router",
    "obtener_estadisticas_admin",
    "listar_medicos",
    "crear_medico",
    "actualizar_medico",
    "listar_pacientes_historico",
    "listar_registros_auditoria"
]
