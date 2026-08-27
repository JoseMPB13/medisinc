"""
Módulo de Esquemas Pydantic v2 en Español para MediSinc-IA.
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
    QuestionOption
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
    "QuestionOption"
]
