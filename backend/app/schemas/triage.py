"""
Puente de retrocompatibilidad hacia app.esquemas.triaje.
"""

from app.esquemas.triaje import (
    EsquemaEntradaPaciente,
    EsquemaSalidaEstructuradaIA,
    EsquemaRespuestaInmediataTriaje,
    EsquemaRespuestaTriaje,
    EsquemaOpcionPregunta,
    EsquemaItemPreguntaDinamica,
    EsquemaEntradaPreguntasDinamicas,
    EsquemaRespuestaPreguntasDinamicas,
    EsquemaRevisionMedicaEntrada,
    EsquemaDetalleExpedienteMedico,
    PatientInputSchema,
    AIStructuredOutput,
    ImmediateTriageResponseSchema,
    TriageResponseSchema,
    DynamicQuestionsInputSchema,
    DynamicQuestionsResponseSchema,
    DynamicQuestion,
    QuestionOption,
    MedicalReviewSchema
)

__all__ = [
    "EsquemaEntradaPaciente",
    "EsquemaSalidaEstructuradaIA",
    "EsquemaRespuestaInmediataTriaje",
    "EsquemaRespuestaTriaje",
    "EsquemaOpcionPregunta",
    "EsquemaItemPreguntaDinamica",
    "EsquemaEntradaPreguntasDinamicas",
    "EsquemaRespuestaPreguntasDinamicas",
    "EsquemaRevisionMedicaEntrada",
    "EsquemaDetalleExpedienteMedico",
    "PatientInputSchema",
    "AIStructuredOutput",
    "ImmediateTriageResponseSchema",
    "TriageResponseSchema",
    "DynamicQuestionsInputSchema",
    "DynamicQuestionsResponseSchema",
    "DynamicQuestion",
    "QuestionOption",
    "MedicalReviewSchema"
]
