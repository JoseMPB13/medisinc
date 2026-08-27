"""
Puente de retrocompatibilidad hacia app.esquemas.administracion.
"""

from app.esquemas.administracion import (
    EsquemaCrearMedico,
    EsquemaActualizarMedico,
    EsquemaRespuestaMedico,
    EsquemaEstadisticasAdmin,
    EsquemaRegistroAuditoria,
    DoctorCreateSchema,
    DoctorUpdateSchema,
    DoctorResponseSchema,
    AdminStatsSchema,
    AuditLogResponseSchema
)

__all__ = [
    "EsquemaCrearMedico",
    "EsquemaActualizarMedico",
    "EsquemaRespuestaMedico",
    "EsquemaEstadisticasAdmin",
    "EsquemaRegistroAuditoria",
    "DoctorCreateSchema",
    "DoctorUpdateSchema",
    "DoctorResponseSchema",
    "AdminStatsSchema",
    "AuditLogResponseSchema"
]
