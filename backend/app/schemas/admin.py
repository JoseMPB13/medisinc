"""
Esquemas Pydantic para el Portal de Administración (Rol ADMIN).
Define las estructuras para gestión de personal médico, métricas globales,
historial histórico de triajes y registros de la bitácora inalterable AUDIT_LOG.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class DoctorCreateSchema(BaseModel):
    """
    Esquema para la creación de un nuevo profesional de salud en el sistema.
    """
    full_name: str = Field(..., description="Nombre y apellidos del médico", min_length=3)
    email: str = Field(..., description="Correo electrónico institucional")
    specialty: str = Field(..., description="Especialidad o matrícula médica")
    password: str = Field(..., min_length=6, description="Contraseña de acceso inicial")
    role: Literal["DOCTOR", "ADMIN"] = Field("DOCTOR", description="Rol asignado en el sistema")


class DoctorUpdateSchema(BaseModel):
    """
    Esquema para la modificación parcial de los datos de un profesional médico.
    """
    full_name: Optional[str] = Field(None, description="Nombre y apellidos")
    specialty: Optional[str] = Field(None, description="Especialidad médica")
    is_active: Optional[bool] = Field(None, description="Estado de habilitación de la cuenta")
    role: Optional[Literal["DOCTOR", "ADMIN"]] = Field(None, description="Rol del usuario")


class DoctorResponseSchema(BaseModel):
    """
    Respuesta estructurada con los datos del perfil médico.
    """
    id: str = Field(..., description="ID del perfil")
    user_id: Optional[str] = Field(None, description="ID del usuario en Auth")
    full_name: str
    email: str
    specialty: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None


class AdminStatsSchema(BaseModel):
    """
    Métricas cuantitativas globales del centro de salud en tiempo real.
    """
    total_triages: int = Field(0, description="Total de triajes recibidos")
    urgent_red_cases: int = Field(0, description="Total de casos críticos catalogados en Rojo")
    reviewed_cases: int = Field(0, description="Total de triajes atendidos y confirmados por médico")
    active_doctors: int = Field(0, description="Número de médicos habilitados en el sistema")
    average_attention_time_min: float = Field(0.0, description="Tiempo promedio de atención en minutos")


class AuditLogResponseSchema(BaseModel):
    """
    Registro individual de trazabilidad inalterable en la bitácora AUDIT_LOG.
    """
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[str] = None
