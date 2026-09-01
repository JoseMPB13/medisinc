"""
Esquemas de Validación Pydantic v2 para el Portal de Administración y Auditoría.
Define los modelos de creación/edición de personal médico, asignación de turnos de guardia,
métricas globales y bitácora de auditoría.
Soporte bilingüe dual completo para blindar el consumo del frontend.
"""

from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict



class EsquemaCrearMedico(BaseModel):
    """
    Datos requeridos para dar de alta a un profesional médico o administrador en la plataforma.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    nombre_completo: str = Field(..., alias="full_name", description="Nombre y apellido completo del profesional")
    correo: EmailStr = Field(..., alias="email", description="Correo electrónico institucional")
    password: str = Field(..., description="Contraseña temporal de acceso seguro", min_length=6)
    especialidad: str = Field(default="Medicina General", alias="specialty", description="Especialidad o área de atención")
    rol: Literal["MEDICO", "ADMIN", "DOCTOR"] = Field(default="MEDICO", alias="role", description="Rol del usuario en el sistema")
    turno_asignado: Optional[Literal["MANANA", "TARDE_NOCHE", "MADRUGADA", "TODOS"]] = Field(
        default="MANANA", alias="assigned_shift", description="Turno de guardia: MANANA (07:00-15:00), TARDE_NOCHE (15:00-23:00), MADRUGADA (23:00-07:00), TODOS"
    )
    dias_guardia: Optional[List[str]] = Field(
        default_factory=lambda: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        alias="duty_days"
    )


class EsquemaActualizarMedico(BaseModel):
    """
    Datos permitidos para modificar el perfil de un profesional de salud y su turno de guardia.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    nombre_completo: Optional[str] = Field(None, alias="full_name")
    especialidad: Optional[str] = Field(None, alias="specialty")
    rol: Optional[Literal["MEDICO", "ADMIN", "DOCTOR"]] = Field(None, alias="role")
    turno_asignado: Optional[Literal["MANANA", "TARDE_NOCHE", "MADRUGADA", "TODOS"]] = Field(None, alias="assigned_shift")
    dias_guardia: Optional[List[str]] = Field(None, alias="duty_days")
    esta_activo: Optional[bool] = Field(None, alias="is_active")


class EsquemaRespuestaMedico(BaseModel):
    """
    Respuesta devuelta al consultar la lista o perfil de profesionales médicos.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(..., description="ID del registro de perfil")
    usuario_id: Optional[str] = Field(None, alias="user_id", description="ID de usuario en Supabase Auth")
    nombre_completo: str = Field(..., alias="full_name", description="Nombre completo")
    correo: Optional[str] = Field(None, alias="email", description="Correo electrónico")
    especialidad: Optional[str] = Field("Medicina General", alias="specialty", description="Especialidad médica")
    rol: str = Field(..., alias="role", description="Rol asignado (MEDICO o ADMIN)")
    turno_asignado: str = Field(default="TODOS", alias="assigned_shift", description="Turno de guardia asignado")
    dias_guardia: Optional[List[str]] = Field(default_factory=list, alias="duty_days", description="Días de guardia")
    esta_activo: bool = Field(True, alias="is_active", description="Estado de actividad en la plataforma")
    creado_en: str = Field(..., alias="created_at", description="Fecha y hora de creación ISO 8601")


class EsquemaEstadisticasAdmin(BaseModel):
    """
    Métricas cuantitativas consolidadas del centro de salud en tiempo real.
    Soporta propiedades bilingües duales simultáneas para frontend.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Claves en español
    total_triajes: int = Field(0, description="Total histórico de pre-triajes capturados")
    casos_rojo_urgente: int = Field(0, description="Total de casos críticos catalogados en Rojo")
    casos_revisados: int = Field(0, description="Total de pacientes atendidos y dados de alta por el médico")
    medicos_activos: int = Field(0, description="Cantidad de facultativos médicos activos")
    tiempo_promedio_atencion_min: float = Field(0.0, description="Tiempo medio de consulta en minutos")

    # Claves en inglés simultáneas
    total_patients: Optional[int] = Field(0, description="Total de pacientes registrados")
    urgent_red_cases: Optional[int] = Field(0, description="Casos rojos urgentes")
    reviewed_cases: Optional[int] = Field(0, description="Casos revisados")
    active_doctors: Optional[int] = Field(0, description="Médicos activos")
    average_attention_time_min: Optional[float] = Field(0.0, description="Tiempo medio de atención")

    # Campos complementarios para vistas extendidas
    total_pacientes: Optional[int] = Field(0, description="Total de pacientes registrados")
    pacientes_hoy: Optional[int] = Field(0, description="Pacientes recibidos hoy")
    en_espera: Optional[int] = Field(0, description="Pacientes en espera de atención")
    atendidos: Optional[int] = Field(0, description="Pacientes completados")
    criticos_rojo: Optional[int] = Field(0, description="Casos urgentes")
    moderados_amarillo: Optional[int] = Field(0, description="Casos prioritarios")
    leves_verde: Optional[int] = Field(0, description="Casos no urgentes")
    total_medicos: Optional[int] = Field(0, description="Total médicos registrados")

    # Diccionarios de soporte dual para pruebas y clientes legacy
    metricas: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Diccionario estructurado de métricas en español")
    stats: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Diccionario estructurado de métricas en inglés")


class EsquemaRegistroAuditoria(BaseModel):
    """
    Entrada individual de la bitácora inalterable de auditoría para trazabilidad médica.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[str] = None
    usuario_id: Optional[str] = Field(None, alias="user_id", description="ID del usuario que ejecutó la acción")
    user_id: Optional[str] = Field(None, description="ID del usuario (alias inglés)")
    accion: str = Field(..., alias="action", description="Descripción de la acción efectuada")
    action: Optional[str] = Field(None, description="Descripción de la acción (alias inglés)")
    recurso_id: Optional[str] = Field(None, alias="resource_id", description="ID del recurso afectado")
    resource_id: Optional[str] = Field(None, description="ID del recurso (alias inglés)")
    direccion_ip: Optional[str] = Field(None, alias="ip_address", description="Dirección IP de origen")
    ip_address: Optional[str] = Field(None, description="Dirección IP (alias inglés)")
    fecha_hora: str = Field(..., alias="timestamp", description="Estampa de tiempo ISO 8601")
    timestamp: Optional[str] = Field(None, description="Estampa de tiempo (alias inglés)")


# -----------------------------------------------------------------------------
# ALIASES DE RETROCOMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
DoctorCreateSchema = EsquemaCrearMedico
DoctorUpdateSchema = EsquemaActualizarMedico
DoctorResponseSchema = EsquemaRespuestaMedico
AdminStatsSchema = EsquemaEstadisticasAdmin
AuditLogResponseSchema = EsquemaRegistroAuditoria
