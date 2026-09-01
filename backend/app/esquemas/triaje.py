"""
Esquemas de Validación Pydantic v2 para el Proceso de Pre-Triaje Clínico.
Define la estructura de entrada del paciente, selección de especialidad médica,
antecedentes clínicos ampliados, preguntas dinámicas adaptativas,
el formato estricto de salida del resumen de IA y la respuesta consolidada entregada al Frontend.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EsquemaEntradaPaciente(BaseModel):
    """
    Datos de entrada capturados en el formulario público del paciente (Pasos 0 y 1).
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    nombre_paciente: str = Field(..., alias="patient_name", description="Nombre completo del paciente", json_schema_extra={"example": "Juan Pérez"})
    ci: str = Field(..., description="Carnet de Identidad del paciente", json_schema_extra={"example": "1234567 SC"})
    edad: int = Field(..., ge=0, le=120, alias="age", description="Edad del paciente en años", json_schema_extra={"example": 35})
    genero: str = Field(..., alias="gender", description="Género del paciente", json_schema_extra={"example": "Masculino"})
    sintomas_brutos: str = Field(..., alias="raw_symptoms", description="Síntoma principal en texto libre", json_schema_extra={"example": "Me duele fuerte el pecho y tengo opresión"})
    
    # Especialidad médica seleccionada y antecedentes clínicos ampliados
    especialidad_solicitada: str = Field(
        default="Medicina General",
        alias="requested_specialty",
        description="Especialidad médica seleccionada por el paciente en el Paso 0",
        json_schema_extra={"example": "Medicina General"}
    )
    alergias_medicamentosas: str = Field(
        default="Ninguna conocida",
        alias="drug_allergies",
        description="Alergias a medicamentos declaradas",
        json_schema_extra={"example": "Penicilina, AINEs"}
    )
    medicacion_actual: str = Field(
        default="Ninguna",
        alias="current_medication",
        description="Fármacos o tratamientos que consume regularmente",
        json_schema_extra={"example": "Losartán 50mg, Metformina 850mg"}
    )
    enfermedades_base: List[str] = Field(
        default_factory=list,
        alias="base_diseases",
        description="Comorbilidades o enfermedades crónicas diagnosticadas",
        json_schema_extra={"example": ["Hipertensión arterial", "Diabetes mellitus tipo 2"]}
    )
    medico_asignado_id: Optional[str] = Field(
        default=None,
        alias="assigned_doctor_id",
        description="ID del médico de turno asignado para la atención",
        json_schema_extra={"example": "doc-med-general-01"}
    )

    datos_estaticos: Dict[str, Any] = Field(
        default_factory=dict,
        alias="static_data",
        description="Datos estáticos adicionales (ej. intensidad 1-10, evolución)",
        json_schema_extra={"example": {"intensidad": 8, "duracion": "2 horas"}}
    )
    respuestas_dinamicas: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="dynamic_answers",
        description="Respuestas a preguntas adaptativas de opción múltiple",
        json_schema_extra={"example": {"ubicacion": "centro del pecho", "sudoracion": "sí"}}
    )

    @property
    def assigned_doctor_id(self) -> Optional[str]:
        return self.medico_asignado_id

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

    @property
    def requested_specialty(self) -> str:
        return self.especialidad_solicitada

    @property
    def drug_allergies(self) -> str:
        return self.alergias_medicamentosas

    @property
    def current_medication(self) -> str:
        return self.medicacion_actual

    @property
    def base_diseases(self) -> List[str]:
        return self.enfermedades_base


class EsquemaSalidaEstructuradaIA(BaseModel):
    """
    Contrato estricto del resumen clínico estructurado emitido por el modelo de Inteligencia Artificial.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sintomas_principales: List[str] = Field(
        ...,
        description="Lista de síntomas principales adaptados a terminología médica estandarizada",
        json_schema_extra={"example": ["Dolor torácico opresivo", "Diaforesis"]}
    )
    duracion_e_intensidad: str = Field(
        ...,
        description="Resumen de tiempo de evolución e intensidad del cuadro sintomático",
        json_schema_extra={"example": "Evolución de 2 horas con intensidad 8/10"}
    )
    factores_agravantes_antecedentes: List[str] = Field(
        default_factory=list,
        description="Factores gatillantes, comorbilidades, alergias o medicación mencionada",
        json_schema_extra={"example": ["Hipertensión arterial", "Alergia a Penicilina"]}
    )
    senales_alerta_identificadas: List[str] = Field(
        default_factory=list,
        description="Banderas rojas o señales de peligro vital detectadas",
        json_schema_extra={"example": ["Opresión precordial irradiada"]}
    )
    prioridad_sugerida_ia: Literal["ROJO", "AMARILLO", "VERDE", "RED", "YELLOW", "GREEN"] = Field(
        ...,
        description="Prioridad preliminar evaluada por la IA (ROJO, AMARILLO, VERDE)",
        json_schema_extra={"example": "ROJO"}
    )
    resumen_clinico_narrativo: str = Field(
        ...,
        description="Síntesis narrativa concisa (2 a 3 oraciones) para rápida lectura del médico de guardia",
        json_schema_extra={"example": "Paciente masculino de 35 años consulta por dolor torácico opresivo de 2 horas de evolución e intensidad 8/10. Presenta diaforesis. Se sugiere atención prioritaria inmediata."}
    )
    informacion_faltante_critica: List[str] = Field(
        default_factory=list,
        description="Preguntas o datos clave no especificados que el facultativo debe interrogar",
        json_schema_extra={"example": ["Irradiación a extremidad superior izquierda", "Antecedentes coronarios familiares"]}
    )

    @field_validator(
        "sintomas_principales",
        "factores_agravantes_antecedentes",
        "senales_alerta_identificadas",
        "informacion_faltante_critica",
        mode="before"
    )
    @classmethod
    def normalizar_listas(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]


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
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    codigo_acceso: str = Field(..., alias="access_code", description="Código alfanumérico único para el paciente")
    estado: str = Field(..., alias="status", description="Estado del registro (RECIBIDO, LISTO, EN_CONSULTA, REVISADO)")
    prioridad_final: Literal["ROJO", "AMARILLO", "VERDE", "RED", "YELLOW", "GREEN"] = Field(..., alias="final_priority")
    sobreescritura_aplicada: bool = Field(False, alias="override_applied")
    motivo_sobreescritura: Optional[str] = Field(None, alias="override_reason")
    resultado_ia: Optional[EsquemaSalidaEstructuradaIA] = Field(None, alias="ai_result")
    especialidad_solicitada: Optional[str] = Field("Medicina General", alias="requested_specialty")
    alergias_medicamentosas: Optional[str] = Field("Ninguna conocida", alias="drug_allergies")
    medicacion_actual: Optional[str] = Field("Ninguna", alias="current_medication")
    enfermedades_base: Optional[List[str]] = Field(default_factory=list, alias="base_diseases")
    medico_asignado_id: Optional[str] = Field(None, alias="assigned_doctor_id")
    asignado_en: Optional[str] = Field(None, alias="assigned_at")
    creado_en: str = Field(..., alias="created_at")


class EsquemaOpcionPregunta(BaseModel):
    """Opción individual para una pregunta dinámica adaptativa."""
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[str] = Field(None, alias="value")
    valor: Optional[str] = Field(None, alias="value")
    etiqueta: str = Field(..., alias="label")
    texto: Optional[str] = Field(None, alias="label")
    es_alerta_roja: Optional[bool] = Field(False, alias="is_red_flag")


class EsquemaItemPreguntaDinamica(BaseModel):
    """Pregunta adaptativa generada para clarificación sintomática."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    pregunta: str = Field(..., alias="question_text")
    tipo_pregunta: str = Field("multiple_choice", alias="question_type")
    opciones: List[Dict[str, Any]] = Field(..., alias="options")


class EsquemaEntradaPreguntasDinamicas(BaseModel):
    """Entrada para solicitar 2 a 3 preguntas adaptativas de clarificación por especialidad."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sintomas_brutos: Optional[str] = Field(None, alias="symptom")
    sintoma: Optional[str] = Field(None, alias="symptom")
    edad: int = Field(..., ge=0, le=120, alias="age")
    genero: Optional[str] = Field("No especificado", alias="gender")
    especialidad_solicitada: Optional[str] = Field("Medicina General", alias="requested_specialty")
    alergias_medicamentosas: Optional[str] = Field("Ninguna conocida", alias="drug_allergies")
    medicacion_actual: Optional[str] = Field("Ninguna", alias="current_medication")
    enfermedades_base: Optional[List[str]] = Field(default_factory=list, alias="base_diseases")


class EsquemaRespuestaPreguntasDinamicas(BaseModel):
    """Respuesta con las preguntas adaptativas generadas."""
    model_config = ConfigDict(populate_by_name=True)

    sintoma_evaluado: Optional[str] = Field("", alias="symptom_evaluated")
    preguntas: List[Dict[str, Any]] = Field(default_factory=list, alias="questions")


class EsquemaItemCatalogoEspecialidad(BaseModel):
    """Ítem individual del catálogo de especialidades médicas."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    nombre: str
    name: Optional[str] = None
    icono: str = "Stethoscope"
    icon: Optional[str] = "Stethoscope"
    descripcion: str
    description: Optional[str] = None
    medicos_activos_turno: int = 0
    active_doctors: Optional[int] = 0
    medicos_disponibles: List[Dict[str, Any]] = Field(default_factory=list)
    available_doctors: List[Dict[str, Any]] = Field(default_factory=list)
    medico_de_guardia: Optional[Dict[str, Any]] = None
    on_duty_doctor: Optional[Dict[str, Any]] = None


class EsquemaAsignacionPacienteEntrada(BaseModel):
    """
    Datos de entrada para reclamar o liberar un paciente por parte del médico de guardia.
    """
    model_config = ConfigDict(populate_by_name=True)

    triaje_id: str = Field(..., alias="triage_id", description="Identificador único del registro de triaje")
    medico_id: Optional[str] = Field(None, alias="doctor_id", description="ID del perfil del profesional médico")


class EsquemaRevisionMedicaEntrada(BaseModel):
    """Esquema de entrada para guardar la evaluación y cierre del médico."""
    model_config = ConfigDict(populate_by_name=True)

    triaje_id: str = Field(..., alias="triage_id")
    medico_id: Optional[str] = Field("doc-uuid-12345", alias="doctor_id")
    notas_medico: str = Field(..., alias="doctor_notes")
    prioridad_ajustada: Optional[str] = Field(None, alias="priority_adjusted")


class EsquemaDetalleExpedienteMedico(BaseModel):
    """Detalle completo del expediente para visualización en el portal médico."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    codigo_acceso: str = Field(..., alias="access_code")
    ci_descifrado: str = Field(..., alias="decrypted_ci")
    nombre_paciente: str = Field(..., alias="patient_name")
    edad: int = Field(..., alias="age")
    genero: str = Field(..., alias="gender")
    sintomas_brutos: str = Field(..., alias="raw_symptoms")
    especialidad_solicitada: Optional[str] = Field("Medicina General", alias="requested_specialty")
    alergias_medicamentosas: Optional[str] = Field("Ninguna conocida", alias="drug_allergies")
    medicacion_actual: Optional[str] = Field("Ninguna", alias="current_medication")
    enfermedades_base: Optional[List[str]] = Field(default_factory=list, alias="base_diseases")
    datos_estaticos: Dict[str, Any] = Field(default_factory=dict, alias="static_data")
    respuestas_dinamicas: Dict[str, Any] = Field(default_factory=dict, alias="dynamic_answers")
    estado: str = Field(..., alias="status")
    prioridad_final: Optional[str] = Field(None, alias="final_priority")
    resultado_ia: Optional[Dict[str, Any]] = Field(None, alias="ai_result")
    medico_asignado_id: Optional[str] = Field(None, alias="assigned_doctor_id")
    asignado_en: Optional[str] = Field(None, alias="assigned_at")
    creado_en: str = Field(..., alias="created_at")


# -----------------------------------------------------------------------------
# ALIASES DE RETROCOMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
PatientAssignmentSchema = EsquemaAsignacionPacienteEntrada
PatientInputSchema = EsquemaEntradaPaciente
AIStructuredOutput = EsquemaSalidaEstructuradaIA
ImmediateTriageResponseSchema = EsquemaRespuestaInmediataTriaje
TriageResponseSchema = EsquemaRespuestaTriaje
DynamicQuestionsInputSchema = EsquemaEntradaPreguntasDinamicas
DynamicQuestionsResponseSchema = EsquemaRespuestaPreguntasDinamicas
DynamicQuestion = EsquemaItemPreguntaDinamica
QuestionOption = EsquemaOpcionPregunta
MedicalReviewSchema = EsquemaRevisionMedicaEntrada
SpecialtyCatalogItemSchema = EsquemaItemCatalogoEspecialidad
