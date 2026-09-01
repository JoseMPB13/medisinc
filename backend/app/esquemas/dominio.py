"""
Modelos y DTOs Fuertemente Tipados de Dominio para Persistencia y Arquitectura Limpia.
Utiliza Pydantic v2 con ConfigDict(from_attributes=True) para garantizar tipado estricto.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class PacienteDTO(BaseModel):
    """DTO para la entidad Maestra de Paciente (3NF)."""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    ci_hash: Optional[str] = None
    ci_cifrado: Optional[str] = None
    nombre_completo: str
    edad: int
    genero: str
    alergias_medicamentosas: str = "Ninguna conocida"
    enfermedades_base: List[str] = Field(default_factory=list)
    medicacion_habitual: str = "No toma medicación"
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None


class ResultadoIADTO(BaseModel):
    """DTO para el diagnóstico y estructuración clínica procesada por IA."""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: Optional[str] = None
    triaje_id: Optional[str] = None
    prioridad_sugerida: str
    justificacion_clinica: str
    resumen_semiologico: str
    red_flags_detectadas: List[str] = Field(default_factory=list)
    especialidad_sugerida: str = "Medicina General"
    posibles_diagnosticos: List[str] = Field(default_factory=list)
    recomendaciones_inmediatas: List[str] = Field(default_factory=list)
    preguntas_complementarias_respuestas: Dict[str, Any] = Field(default_factory=dict)
    nivel_confianza: float = 0.95
    override_aplicado: bool = False
    motivo_override: Optional[str] = None
    creado_en: Optional[str] = None


class RegistroTriajeDTO(BaseModel):
    """DTO para el episodio clínico de pre-triaje."""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    codigo_acceso: str
    paciente_id: Optional[str] = None
    nombre_paciente: Optional[str] = None
    edad: Optional[int] = None
    genero: Optional[str] = None
    ci_cifrado: Optional[str] = None
    ci_descifrado: Optional[str] = None
    ci_hash: Optional[str] = None
    especialidad_id: Optional[str] = None
    especialidad_solicitada: str = "Medicina General"
    medico_asignado_id: Optional[str] = None
    asignado_en: Optional[str] = None
    sintomas_brutos: str
    alergias_medicamentosas: str = "Ninguna conocida"
    medicacion_actual: str = "Ninguna"
    enfermedades_base: List[str] = Field(default_factory=list)
    datos_estaticos: Dict[str, Any] = Field(default_factory=dict)
    respuestas_dinamicas: Dict[str, Any] = Field(default_factory=dict)
    estado: str = "RECIBIDO"
    prioridad_final: Optional[str] = None
    notas_medico: Optional[str] = None
    prioridad_ajustada: Optional[str] = None
    resultados_ia: Optional[ResultadoIADTO] = None
    tiempo_estimado_segundos_restantes: Optional[int] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None


class PerfilMedicoDTO(BaseModel):
    """DTO para el personal médico y administrativo."""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    usuario_id: Optional[str] = None
    nombre_completo: str
    correo: str
    especialidad: str = "Medicina General"
    rol: str = "MEDICO"
    turno_asignado: str = "TODOS"
    dias_guardia: List[str] = Field(default_factory=list)
    esta_activo: bool = True
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None


class EventoAuditoriaDTO(BaseModel):
    """DTO para la bitácora inalterable de auditoría."""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    usuario_id: str = "SISTEMA"
    accion: str
    recurso_id: Optional[str] = None
    direccion_ip: str = "127.0.0.1"
    fecha_hora: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
