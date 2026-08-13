"""
Esquemas de Validación Pydantic para el Proceso de Pre-Triaje Clínico.
Define la estructura de entrada del paciente, el formato de salida estricto de la IA
y la respuesta consolidada entregada al Frontend.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class PatientInputSchema(BaseModel):
    """
    Datos de entrada capturados en el formulario público del paciente.
    """
    patient_name: str = Field(..., description="Nombre completo del paciente", example="Juan Pérez")
    ci: str = Field(..., description="Carnet de Identidad del paciente", example="1234567 SC")
    age: int = Field(..., ge=0, le=120, description="Edad del paciente en años", example=35)
    gender: str = Field(..., description="Género del paciente", example="Masculino")
    raw_symptoms: str = Field(..., description="Síntoma principal expresado en texto libre", example="Me duele fuerte el pecho y tengo opresión")
    static_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Datos estáticos adicionales (ej. intensidad 1-10, evolución)",
        example={"intensidad": 8, "duracion": "2 horas"}
    )
    dynamic_answers: Optional[Dict[str, Any]] = Field(
        default={},
        description="Respuestas a las preguntas dinámicas adaptativas de opción múltiple",
        example={"ubicacion": "centro del pecho", "sudoracion": "sí"}
    )


class AIStructuredOutput(BaseModel):
    """
    Contrato estricto del resumen clínico estructurado generado por la IA.
    """
    sintomas_principales: List[str] = Field(
        ...,
        description="Lista de síntomas principales adaptados a terminología médica",
        example=["Dolor torácico opresivo", "Diaforesis"]
    )
    duracion_e_intensidad: str = Field(
        ...,
        description="Resumen de tiempo de evolución e intensidad del dolor",
        example="Evolución de 2 horas con intensidad 8/10"
    )
    factores_agravantes_antecedentes: List[str] = Field(
        default_factory=list,
        description="Factores gatillantes o antecedentes de salud mencionados",
        example=["Hipertensión arterial"]
    )
    senales_alerta_identificadas: List[str] = Field(
        default_factory=list,
        description="Banderas rojas o señales de peligro detectadas",
        example=["Opresión precordial irradiada"]
    )
    prioridad_sugerida_ia: Literal["RED", "YELLOW", "GREEN"] = Field(
        ...,
        description="Prioridad preliminar evaluada por la IA (RED, YELLOW, GREEN)",
        example="RED"
    )
    resumen_clinico_narrativo: str = Field(
        ...,
        description="Síntesis narrativa concisa (2 a 3 oraciones) para rápida lectura del médico",
        example="Paciente masculino de 35 años consulta por dolor torácico opresivo de 2 horas de evolución e intensidad 8/10. Presenta sudoración profusa. Se sugiere atención prioritaria."
    )
    informacion_faltante_critica: List[str] = Field(
        default_factory=list,
        description="Preguntas o datos clave no especificadas que el médico debe indagar",
        example=["Irradiación a brazo izquierdo", "Antecedentes cardíacos familiares"]
    )


class TriageResponseSchema(BaseModel):
    """
    Respuesta final devuelta al cliente tras procesar la captura, IA y reglas de seguridad.
    """
    access_code: str = Field(..., description="Código alfanumérico único para el paciente (ej. MS-8X92K)")
    status: str = Field(..., description="Estado del registro (RECEIVED, READY, REVIEWED)")
    final_priority: Literal["RED", "YELLOW", "GREEN"] = Field(..., description="Nivel de prioridad final asignado")
    override_applied: bool = Field(..., description="Indica si se aplicó un Safety Override por motor de reglas")
    override_reason: Optional[str] = Field(None, description="Razón de la sobreescritura si fue aplicada")
    ai_result: AIStructuredOutput = Field(..., description="Resultado detallado del análisis por IA")
    created_at: str = Field(..., description="Fecha y hora de creación ISO 8601")
