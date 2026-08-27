"""
Esquemas de Validación Pydantic v2 para el Proceso de Pre-Triaje Clínico.
Define la estructura de entrada del paciente, preguntas dinámicas adaptativas,
el formato estricto de salida del resumen de IA y la respuesta consolidada entregada al Frontend.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class EsquemaEntradaPaciente(BaseModel):
    """
    Datos de entrada capturados en el formulario público del paciente.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    nombre_paciente: str = Field(..., alias="patient_name", description="Nombre completo del paciente", example="Juan Pérez")
    ci: str = Field(..., description="Carnet de Identidad del paciente", example="1234567 SC")
    edad: int = Field(..., ge=0, le=120, alias="age", description="Edad del paciente en años", example=35)
    genero: str = Field(..., alias="gender", description="Género del paciente", example="Masculino")
    sintomas_brutos: str = Field(..., alias="raw_symptoms", description="Síntoma principal en texto libre", example="Me duele fuerte el pecho y tengo opresión")
    datos_estaticos: Dict[str, Any] = Field(
        default_factory=dict,
        alias="static_data",
        description="Datos estáticos adicionales (ej. intensidad 1-10, evolución)",
        example={"intensidad": 8, "duracion": "2 horas"}
    )
    respuestas_dinamicas: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="dynamic_answers",
        description="Respuestas a preguntas adaptativas de opción múltiple",
        example={"ubicacion": "centro del pecho", "sudoracion": "sí"}
    )

    @property
    def patient_name(self) -> str:
        return self.nombre_paciente

    @property
    def age(self) -> int:
        return self.edad

    @property
    def gender(self) -> str:
        return self.genero

    @property
    def raw_symptoms(self) -> str:
        return self.sintomas_brutos

    @property
    def static_data(self) -> Dict[str, Any]:
        return self.datos_estaticos

    @property
    def dynamic_answers(self) -> Optional[Dict[str, Any]]:
        return self.respuestas_dinamicas


class EsquemaSalidaEstructuradaIA(BaseModel):
    """
    Contrato estricto del resumen clínico estructurado emitido por el modelo de Inteligencia Artificial.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sintomas_principales: List[str] = Field(
        ...,
        description="Lista de síntomas principales adaptados a terminología médica estandarizada",
        example=["Dolor torácico opresivo", "Diaforesis"]
    )
    duracion_e_intensidad: str = Field(
        ...,
        description="Resumen de tiempo de evolución e intensidad del cuadro sintomático",
        example="Evolución de 2 horas con intensidad 8/10"
    )
    factores_agravantes_antecedentes: List[str] = Field(
        default_factory=list,
        description="Factores gatillantes, comorbilidades o antecedentes mencionados",
        example=["Hipertensión arterial"]
    )
    senales_alerta_identificadas: List[str] = Field(
        default_factory=list,
        description="Banderas rojas o señales de peligro vital detectadas",
        example=["Opresión precordial irradiada"]
    )
    prioridad_sugerida_ia: Literal["ROJO", "AMARILLO", "VERDE", "RED", "YELLOW", "GREEN"] = Field(
        ...,
        description="Prioridad preliminar evaluada por la IA (ROJO, AMARILLO, VERDE)",
        example="ROJO"
    )
    resumen_clinico_narrativo: str = Field(
        ...,
        description="Síntesis narrativa concisa (2 a 3 oraciones) para rápida lectura del médico de guardia",
        example="Paciente masculino de 35 años consulta por dolor torácico opresivo de 2 horas de evolución e intensidad 8/10. Presenta diaforesis. Se sugiere atención prioritaria inmediata."
    )
    informacion_faltante_critica: List[str] = Field(
        default_factory=list,
        description="Preguntas o datos clave no especificados que el facultativo debe interrogar",
        example=["Irradiación a extremidad superior izquierda", "Antecedentes coronarios familiares"]
    )


class EsquemaRespuestaInmediataTriaje(BaseModel):
    """
    Respuesta de confirmación devuelta al paciente inmediatamente tras persistir su pre-triaje.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    triaje_id: str = Field(..., alias="triage_id", description="Identificador único del registro de triaje")
    codigo_acceso: str = Field(..., alias="access_code", description="Código alfanumérico generado (ej. MS-8X92K)")
    estado: str = Field("RECEIVED", alias="status", description="Estado inicial del registro ('RECIBIDO' o 'RECEIVED')")
    nombre_paciente: str = Field(..., alias="patient_name", description="Nombre del paciente")
    mensaje: str = Field("Pre-triaje registrado exitosamente. Tu resumen clínico se encuentra en procesamiento.", alias="message")
    creado_en: str = Field(..., alias="created_at", description="Fecha y hora de creación ISO 8601")

    # Campos bilingües serializables directamente
    triage_id: Optional[str] = None
    access_code: Optional[str] = None
    status: Optional[str] = None
    patient_name: Optional[str] = None
    created_at: Optional[str] = None

    def model_post_init(self, __context):
        if not self.triage_id:
            self.triage_id = self.triaje_id
        if not self.access_code:
            self.access_code = self.codigo_acceso
        if not self.status:
            self.status = self.estado
        if not self.patient_name:
            self.patient_name = self.nombre_paciente
        if not self.created_at:
            self.created_at = self.creado_en


class EsquemaRespuestaTriaje(BaseModel):
    """
    Respuesta consolidada completa con resultado de IA y Safety Overrides.
    """
    model_config = ConfigDict(populate_by_name=True)

    codigo_acceso: str = Field(..., alias="access_code", description="Código alfanumérico único para el paciente")
    estado: str = Field(..., alias="status", description="Estado del registro (RECIBIDO, LISTO, REVISADO)")
    prioridad_final: Literal["ROJO", "AMARILLO", "VERDE", "RED", "YELLOW", "GREEN"] = Field(..., alias="final_priority")
    sobreescritura_aplicada: bool = Field(False, alias="override_applied")
    motivo_sobreescritura: Optional[str] = Field(None, alias="override_reason")
    resultado_ia: Optional[EsquemaSalidaEstructuradaIA] = Field(None, alias="ai_result")
    creado_en: str = Field(..., alias="created_at")


class EsquemaOpcionPregunta(BaseModel):
    """Opción individual para una pregunta dinámica adaptativa."""
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[str] = Field(None, alias="value")
    valor: Optional[str] = Field(None, alias="value")
    etiqueta: str = Field(..., alias="label")
    texto: Optional[str] = Field(None, alias="label")


class EsquemaItemPreguntaDinamica(BaseModel):
    """Pregunta adaptativa generada para clarificación sintomática."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    pregunta: str = Field(..., alias="question_text")
    tipo_pregunta: str = Field("multiple_choice", alias="question_type")
    opciones: List[Dict[str, Any]] = Field(..., alias="options")


class EsquemaEntradaPreguntasDinamicas(BaseModel):
    """Entrada para solicitar 2 a 3 preguntas adaptativas de clarificación."""
    model_config = ConfigDict(populate_by_name=True)

    sintomas_brutos: Optional[str] = Field(None, alias="symptom")
    sintoma: Optional[str] = Field(None, alias="symptom")
    edad: int = Field(..., ge=0, le=120, alias="age")
    genero: Optional[str] = Field("No especificado", alias="gender")


class EsquemaRespuestaPreguntasDinamicas(BaseModel):
    """Respuesta con las preguntas adaptativas generadas."""
    model_config = ConfigDict(populate_by_name=True)

    sintoma_evaluado: Optional[str] = Field("", alias="symptom_evaluated")
    preguntas: List[Dict[str, Any]] = Field(..., alias="questions")


class EsquemaRevisionMedicaEntrada(BaseModel):
    """Esquema de entrada para guardar la evaluación y cierre del médico."""
    model_config = ConfigDict(populate_by_name=True)

    triaje_id: str = Field(..., alias="triage_id")
    medico_id: Optional[str] = Field("doc-uuid-12345", alias="doctor_id")
    notas_medico: str = Field(..., alias="doctor_notes")
    prioridad_ajustada: Optional[str] = Field(None, alias="priority_adjusted")


class EsquemaDetalleExpedienteMedico(BaseModel):
    """Detalle completo del expediente para visualización en el portal médico."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    codigo_acceso: str = Field(..., alias="access_code")
    ci_descifrado: str = Field(..., alias="decrypted_ci")
    nombre_paciente: str = Field(..., alias="patient_name")
    edad: int = Field(..., alias="age")
    genero: str = Field(..., alias="gender")
    sintomas_brutos: str = Field(..., alias="raw_symptoms")
    datos_estaticos: Dict[str, Any] = Field(default_factory=dict, alias="static_data")
    respuestas_dinamicas: Dict[str, Any] = Field(default_factory=dict, alias="dynamic_answers")
    estado: str = Field(..., alias="status")
    prioridad_final: Optional[str] = Field(None, alias="final_priority")
    resultado_ia: Optional[Dict[str, Any]] = Field(None, alias="ai_result")
    creado_en: str = Field(..., alias="created_at")


# -----------------------------------------------------------------------------
# ALIASES DE RETROCOMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
PatientInputSchema = EsquemaEntradaPaciente
AIStructuredOutput = EsquemaSalidaEstructuradaIA
ImmediateTriageResponseSchema = EsquemaRespuestaInmediataTriaje
TriageResponseSchema = EsquemaRespuestaTriaje
DynamicQuestionsInputSchema = EsquemaEntradaPreguntasDinamicas
DynamicQuestionsResponseSchema = EsquemaRespuestaPreguntasDinamicas
DynamicQuestion = EsquemaItemPreguntaDinamica
QuestionOption = EsquemaOpcionPregunta
MedicalReviewSchema = EsquemaRevisionMedicaEntrada
