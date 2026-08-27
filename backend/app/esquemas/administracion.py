"""
Esquemas de Validación Pydantic v2 para el Portal de Administración y Auditoría.
Define los modelos de creación/edición de personal médico, métricas globales y bitácora de auditoría.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class EsquemaCrearMedico(BaseModel):
    """
    Datos requeridos para dar de alta a un profesional médico o administrador en la plataforma.
    """
    model_config = ConfigDict(populate_by_name=True)

    nombre_completo: str = Field(..., alias="full_name", description="Nombre y apellido completo del profesional", example="Dra. Andrea Gutiérrez")
    correo: EmailStr = Field(..., alias="email", description="Correo electrónico institucional", example="andrea.gutierrez@medisinc.bo")
    password: str = Field(..., description="Contraseña temporal de acceso seguro", min_length=6, example="ClaveMedica2026!")
    especialidad: str = Field(default="Medicina General", alias="specialty", description="Especialidad o área de atención", example="Triaje de Emergencias")
    rol: Literal["MEDICO", "ADMIN", "DOCTOR"] = Field(default="MEDICO", alias="role", description="Rol del usuario en el sistema")


class EsquemaActualizarMedico(BaseModel):
    """
    Datos permitidos para modificar el perfil de un profesional de salud.
    """
    model_config = ConfigDict(populate_by_name=True)

    nombre_completo: Optional[str] = Field(None, alias="full_name")
    especialidad: Optional[str] = Field(None, alias="specialty")
    rol: Optional[Literal["MEDICO", "ADMIN", "DOCTOR"]] = Field(None, alias="role")
    esta_activo: Optional[bool] = Field(None, alias="is_active")


class EsquemaRespuestaMedico(BaseModel):
    """
    Respuesta devuelta al consultar la lista o perfil de profesionales médicos.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="ID del registro de perfil")
    usuario_id: Optional[str] = Field(None, alias="user_id", description="ID de usuario en Supabase Auth")
    nombre_completo: str = Field(..., alias="full_name", description="Nombre completo")
    correo: Optional[str] = Field(None, alias="email", description="Correo electrónico")
    especialidad: Optional[str] = Field("Medicina General", alias="specialty", description="Especialidad médica")
    rol: str = Field(..., alias="role", description="Rol asignado (MEDICO o ADMIN)")
    esta_activo: bool = Field(True, alias="is_active", description="Estado de actividad en la plataforma")
    creado_en: str = Field(..., alias="created_at", description="Fecha y hora de creación ISO 8601")


class EsquemaEstadisticasAdmin(BaseModel):
    """
    Métricas cuantitativas consolidadas del centro de salud en tiempo real.
    """
    model_config = ConfigDict(populate_by_name=True)

    total_triajes: int = Field(0, alias="total_triajes", description="Total histórico de pre-triajes capturados")
    casos_rojo_urgente: int = Field(0, alias="urgent_red_cases", description="Total de casos críticos catalogados en Rojo")
    casos_revisados: int = Field(0, alias="reviewed_cases", description="Total de pacientes atendidos y dados de alta por el médico")
    medicos_activos: int = Field(0, alias="active_doctors", description="Cantidad de facultativos médicos activos")
    tiempo_promedio_atencion_min: float = Field(0.0, alias="average_attention_time_min", description="Tiempo medio de consulta en minutos")

    # Campos adicionales para vistas extendidas
    total_pacientes: Optional[int] = Field(0, description="Total de pacientes registrados")
    pacientes_hoy: Optional[int] = Field(0, description="Pacientes recibidos hoy")
    en_espera: Optional[int] = Field(0, description="Pacientes en espera de atención")
    atendidos: Optional[int] = Field(0, description="Pacientes completados")
    criticos_rojo: Optional[int] = Field(0, description="Casos urgentes")
    moderados_amarillo: Optional[int] = Field(0, description="Casos prioritarios")
    leves_verde: Optional[int] = Field(0, description="Casos no urgentes")
    total_medicos: Optional[int] = Field(0, description="Total médicos registrados")


class EsquemaRegistroAuditoria(BaseModel):
    """
    Entrada individual de la bitácora inalterable de auditoría para trazabilidad médica.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    usuario_id: Optional[str] = Field(None, alias="user_id", description="ID del usuario que ejecutó la acción")
    accion: str = Field(..., alias="action", description="Descripción de la acción efectuada")
    recurso_id: Optional[str] = Field(None, alias="resource_id", description="ID del recurso afectado")
    direccion_ip: Optional[str] = Field(None, alias="ip_address", description="Dirección IP de origen")
    fecha_hora: str = Field(..., alias="timestamp", description="Estampa de tiempo ISO 8601")


# -----------------------------------------------------------------------------
# ALIASES DE RETROCOMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
DoctorCreateSchema = EsquemaCrearMedico
DoctorUpdateSchema = EsquemaActualizarMedico
DoctorResponseSchema = EsquemaRespuestaMedico
AdminStatsSchema = EsquemaEstadisticasAdmin
AuditLogResponseSchema = EsquemaRegistroAuditoria
